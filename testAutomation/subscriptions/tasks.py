from __future__ import absolute_import, unicode_literals

from datetime import date

from celery import shared_task

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.template.defaultfilters import date as datefilter

from incuna_mail import send

from rolepermissions.checkers import has_role

from subscriptions.models import Order, Subscription


def _send_notification(subscriptions, expiry_days):
    site = Site.objects.get_current()
    if expiry_days == 30:
        subject = 'Action required: Your GGC subscription will expire in 1 month'
    elif expiry_days == 7:
        subject = 'Action required: Your GGC subscription will expire in 1 week'
    else:
        subject = 'Action required: Your GGC subscription has expired'

    for subscription in subscriptions:
        organisation = subscription.order.organisation
        users = subscription.order.organisation.user_set.all()
        end_date = subscription.end_date
        for user in users:
            if has_role(user, ['admin']):
                if expiry_days == 0:
                    renewal_message = "has expired"
                else:
                    renewal_message = "is due for renewal on {}".format(
                        datefilter(end_date)
                    )
                context = {
                    'site': site,
                    'site_domain': site.domain,
                    'site_name': site.name,
                    'email': user.email,
                    'organisation_name': organisation.legal_name,
                    'renewal_message': renewal_message,
                    'user_name': user.name
                }
                send(
                    to=user.email,
                    subject=subject,
                    template_name='subscriptions/emails/order_renewal.txt',
                    context=context,
                    sender=settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
                )


def _to_be_expired(expiry_days=0):
    expiry_date = date.today() + relativedelta(days=expiry_days)
    subscriptions = Subscription.objects.filter(
        end_date=expiry_date,
        order__status=Order.STATUS_APPROVED
    ).prefetch_related('order__organisation__user_set')
    _send_notification(subscriptions, expiry_days)


@shared_task
def check_subscription_expiry():
    _to_be_expired(expiry_days=30)
    _to_be_expired(expiry_days=7)
    _to_be_expired(expiry_days=0)
