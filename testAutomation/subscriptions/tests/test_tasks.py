from datetime import date, timedelta

from django.conf import settings
from django.core import mail
from django.test import override_settings, TestCase

from rolepermissions.roles import assign_role

from users.tests.factories import OrganisationFactory, UserFactory

from .factories import OrderFactory, SubscriptionFactory
from ..models import Order
from ..tasks import check_subscription_expiry


class TestSubscriptionCeleryTasks(TestCase):

    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory.create()
        self.user = UserFactory.create(organisation=self.organisation)
        self.order = OrderFactory.create(
            organisation=self.organisation,
            status=Order.STATUS_APPROVED
        )
        assign_role(self.user, 'admin')

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_send_renewal_email_today(self):
        SubscriptionFactory.create(
            end_date=date.today(),
            order=self.order
        )
        check_subscription_expiry()

        self.assertEqual(len(mail.outbox), 1)
        subject = 'Action required: Your GGC subscription has expired'
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertIn("has expired", mail.outbox[0].body)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
        )

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_send_renewal_email_one_week(self):
        SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=7),
            order=self.order
        )
        check_subscription_expiry()

        self.assertEqual(len(mail.outbox), 1)
        subject = 'Action required: Your GGC subscription will expire in 1 week'
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
        )

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_send_renewal_email_one_month(self):
        SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=30),
            order=self.order
        )

        check_subscription_expiry()

        self.assertEqual(len(mail.outbox), 1)
        subject = 'Action required: Your GGC subscription will expire in 1 month'
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
        )

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_send_renewal_email_none(self):
        order1 = OrderFactory.create(
            organisation=self.organisation,
            status=Order.STATUS_APPROVED
        )
        SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=1),
            order=order1
        )
        order2 = OrderFactory.create(
            organisation=self.organisation,
            status=Order.STATUS_APPROVED
        )
        SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=15),
            order=order2
        )
        order3 = OrderFactory.create(
            organisation=self.organisation,
            status=Order.STATUS_APPROVED
        )
        SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=200),
            order=order3
        )
        order4 = OrderFactory.create(
            organisation=self.organisation,
            status=Order.STATUS_APPROVED
        )
        SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=300),
            order=order4
        )

        check_subscription_expiry()
        self.assertEqual(len(mail.outbox), 0)
