from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import models
from django.utils import timezone

from incuna_mail import send
from rolepermissions.checkers import has_role

from users.models import Organisation, User

from .querysets import AssessmentPurchaseQueryset, SubscriptionQueryset


def get_end_date():
    return date.today() + relativedelta(years=1)


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in-progress'
    STATUS_APPROVED = 'approved'
    STATUS_CANCELED = 'canceled'

    ORDER_STATUS_CHOICES = (
        (STATUS_NEW, 'New'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_APPROVED, 'Paid'),
        (STATUS_CANCELED, 'Canceled'),
    )
    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    notes = models.TextField(blank=True)
    status = models.CharField(
        choices=ORDER_STATUS_CHOICES,
        max_length=100,
        default='new'
    )
    created = models.DateTimeField(default=timezone.now, editable=False)
    paid_date = models.DateTimeField(editable=False, null=True)
    _init_order_status = None

    class Meta:
        ordering = ['-created']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._init_order_status = self.status

    def __str__(self):
        return '{:07d} - {:%x %X}'.format(self.pk, self.created)

    def get_is_awaiting_payment(self):
        return self.status in (Order.STATUS_NEW, Order.STATUS_IN_PROGRESS)

    def get_is_approved(self):
        return self.status == Order.STATUS_APPROVED

    def get_order_details(self):
        items = []
        total_order_price = float(0)
        try:
            if self.subscription:
                items.append({
                    'name': 'Annual Subscription',
                    'price': self.subscription.price
                })
                total_order_price += float(self.subscription.price)
        except Subscription.DoesNotExist:
            pass

        try:
            if self.assessment_purchase:
                purchase_name = 'Assessment Purchase: {} invites'.format(
                    self.assessment_purchase.number_included
                )
                items.append({
                    'name': purchase_name,
                    'price': self.assessment_purchase.price
                })
                total_order_price += float(self.assessment_purchase.price)
        except AssessmentPurchase.DoesNotExist:
            pass

        return items, total_order_price

    def send_order_confirmation(self):
        order_number = '{:07d}'.format(self.pk)
        subject = 'GCC Order confirmation {}'.format(order_number)
        template_name = 'subscriptions/emails/order_confirmation.txt'
        self._send_order_email(subject, template_name)

    def send_order_cancelation(self):
        order_number = '{:07d}'.format(self.pk)
        subject = 'GCC Order cancelation {}'.format(order_number)
        template_name = 'subscriptions/emails/order_cancelation.txt'
        self._send_order_email(subject, template_name)

    def send_order_completion(self):
        order_number = '{:07d}'.format(self.pk)
        subject = 'GCC Order completion {}'.format(order_number)
        template_name = 'subscriptions/emails/order_completion.txt'
        self._send_order_email(subject, template_name)

    def _send_order_email(self, subject, template_name):
        users = User.objects.filter(organisation=self.organisation)
        site = Site.objects.get_current()
        order_number = '{:07d}'.format(self.pk)
        organisation_name = self.organisation.legal_name
        order_items, order_total = self.get_order_details()
        for user in users:
            if has_role(user, ['admin']):
                context = {
                    'site': site,
                    'site_domain': site.domain,
                    'site_name': site.name,
                    'organisation_name': organisation_name,
                    'order_items': order_items,
                    'order_total': '{0:.2f}'.format(order_total),
                    'order_number': order_number,
                    'user_name': user.name
                }

                send(
                    to=user.email,
                    subject=subject,
                    template_name=template_name,
                    context=context,
                    sender=settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
                )

    def get_formatted_id(self):
        return '{:07d}'.format(self.pk)

    def save(self, *args, **kwargs):
        if self._init_order_status != self.status:
            if self.status == Order.STATUS_APPROVED:
                self.paid_date = timezone.now()
                self.send_order_completion()
            elif self.status == Order.STATUS_CANCELED:
                self.send_order_cancelation()
        super().save(*args, **kwargs)


class Subscription(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='subscription'
    )
    start_date = models.DateField(default=date.today)
    end_date = models.DateField(default=get_end_date)
    price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=settings.SITE_SUBSCRIPTION['price']
    )
    created = models.DateTimeField(default=timezone.now, editable=False)

    objects = SubscriptionQueryset.as_manager()

    def get_remaining(self):
        return self.end_date - date.today()

    def get_is_renewal_due(self):
        approved = self.order.get_is_approved()
        reminder_days = self.get_remaining()
        renewal_days = settings.SITE_SUBSCRIPTION['renewal_reminder_days']
        return approved and reminder_days.days <= renewal_days

    def get_is_expired(self):
        approved = self.order.get_is_approved()
        reminder_days = self.get_remaining()
        return approved and reminder_days.days <= 0


class AssessmentPackage(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    number_included = models.IntegerField(unique=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now, editable=False)

    def __str__(self):
        return self.name


class AssessmentPurchase(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.PROTECT,
        related_name='assessment_purchase'
    )
    package = models.ForeignKey(
        AssessmentPackage,
        on_delete=models.PROTECT,
        related_name='purchases',
        null=True
    )
    number_included = models.IntegerField(null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, null=True)
    created = models.DateTimeField(default=timezone.now, editable=False)

    objects = AssessmentPurchaseQueryset.as_manager()

    def clean(self):
        if self.package:
            if self.number_included is None:
                self.number_included = self.package.number_included
            if self.price is None:
                self.price = self.package.price

    def __str__(self):
        return '{:07d} - {:%x %X}'.format(self.pk, self.created)
