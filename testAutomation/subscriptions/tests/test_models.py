from datetime import date

from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from django.test import TestCase

from users.tests.factories import OrganisationFactory

from .factories import (
    AssessmentPackageFactory,
    AssessmentPurchaseFactory,
    OrderFactory,
    SubscriptionFactory,
)
from ..models import Order


class TestAssessmentPackage(TestCase):
    def test_str(self):
        assessment_package = AssessmentPackageFactory.build()
        self.assertEqual(str(assessment_package), assessment_package.name)


class TestAssessmentPurchase(TestCase):
    def test_str(self):
        assessment_purchase = AssessmentPurchaseFactory.create()
        expected_str = '{:07d} - {:%x %X}'.format(
            assessment_purchase.pk,
            assessment_purchase.created
        )
        self.assertEqual(expected_str, str(assessment_purchase))

    def test_clean_package_none(self):
        assessment_purchase = AssessmentPurchaseFactory.create()
        self.assertEqual(assessment_purchase.package, None)
        assessment_purchase.clean()

    def test_clean_number_included_from_package(self):
        assessment_package = AssessmentPackageFactory.create(
            number_included=1,
            price=900.00
        )
        assessment_purchase = AssessmentPurchaseFactory.create(package=assessment_package)
        self.assertEqual(assessment_purchase.package, assessment_package)
        assessment_purchase.clean()
        self.assertEqual(
            assessment_purchase.number_included,
            assessment_package.number_included
        )

    def test_clean_price_from_package(self):
        assessment_package = AssessmentPackageFactory.create(
            number_included=1,
            price=900.00
        )
        assessment_purchase = AssessmentPurchaseFactory.create(package=assessment_package)
        self.assertEqual(assessment_purchase.package, assessment_package)
        assessment_purchase.clean()
        self.assertEqual(
            assessment_purchase.price,
            assessment_package.price
        )


class TestOrder(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.organisation = OrganisationFactory.create()

    def test_str(self):
        order = OrderFactory.create()
        expected_str = '{:07d} - {:%x %X}'.format(order.pk, order.created)
        self.assertEqual(expected_str, str(order))

    def test_get_is_awaiting_payment(self):
        order = OrderFactory.create(status="new")
        self.assertEqual(True, order.get_is_awaiting_payment())

    def test_get_is_awaiting_payment_false(self):
        order = OrderFactory.create(status="approve")
        self.assertEqual(False, order.get_is_awaiting_payment())

    def test_get_status_display(self):
        order = OrderFactory.create(status="approved")
        self.assertEqual("Paid", order.get_status_display())

    def test_get_status_display_canceled(self):
        order = OrderFactory.create(status="canceled")
        self.assertEqual("Canceled", order.get_status_display())

    def test_get_formatted_id(self):
        order = OrderFactory.create()
        expected_str = '{:07d}'.format(order.pk)
        self.assertEqual(expected_str, order.get_formatted_id())

    def test_get_is_approved(self):
        order = OrderFactory.build(status="approved")
        self.assertTrue(order.get_is_approved())

    def test_get_is_approved_false(self):
        order = OrderFactory.build(status="new")
        self.assertFalse(order.get_is_approved())

    @patch('subscriptions.models.Order.send_order_completion')
    def test_send_order_completion_called(self, send_order_completion):
        order = OrderFactory.create(
            organisation=self.organisation,
            status=Order.STATUS_NEW
        )
        order.status = Order.STATUS_APPROVED
        order.save()
        send_order_completion.assert_called_with()

    @patch('subscriptions.models.Order.send_order_completion')
    def test_send_order_completion_called_with_approved(self, send_order_completion):
        order = OrderFactory.build(
            organisation=self.organisation
        )
        order.status = Order.STATUS_APPROVED
        order.save()
        send_order_completion.assert_called_with()

    @patch('subscriptions.models.Order.send_order_completion')
    def test_send_order_completion_not_called_when_no_change(self, send_order_completion):
        order = OrderFactory.build(
            organisation=self.organisation,
            status=Order.STATUS_APPROVED
        )
        order.status = Order.STATUS_APPROVED
        order.save()
        self.assertFalse(send_order_completion.called)

    @patch('subscriptions.models.Order.send_order_cancelation')
    def test_send_order_cancelation_called(self, send_order_cancelation):
        order = OrderFactory.create(
            organisation=self.organisation,
            status=Order.STATUS_NEW
        )
        order.status = Order.STATUS_CANCELED
        order.save()
        send_order_cancelation.assert_called_with()

    @patch('subscriptions.models.Order.send_order_cancelation')
    def test_send_order_cancelation_called_with_canceled(self, send_order_cancelation):
        order = OrderFactory.build(
            organisation=self.organisation
        )
        order.status = Order.STATUS_CANCELED
        order.save()
        send_order_cancelation.assert_called_with()

    @patch('subscriptions.models.Order.send_order_cancelation')
    def test_send_order_cancelation_not_called_no_change(self, send_order_cancelation):
        order = OrderFactory.build(
            organisation=self.organisation,
            status=Order.STATUS_CANCELED
        )
        order.status = Order.STATUS_CANCELED
        order.save()
        self.assertFalse(send_order_cancelation.called)


class TestSubscriptionTestCase(TestCase):

    def test_get_remaining(self):
        end_date = date.today() + relativedelta(years=1)
        subscription = SubscriptionFactory.create(end_date=end_date)
        expected = end_date - date.today()
        self.assertEqual(subscription.get_remaining().days, expected.days)

    def test_get_is_renewal_due(self):
        order = OrderFactory.create(status="approved")
        end_date = date.today() + relativedelta(days=10)
        subscription = SubscriptionFactory.create(order=order, end_date=end_date)
        self.assertTrue(subscription.get_is_renewal_due())

    def test_get_is_renewal_due_false(self):
        order = OrderFactory.create(status="approved")
        end_date = date.today() + relativedelta(days=100)
        subscription = SubscriptionFactory.create(order=order, end_date=end_date)
        self.assertFalse(subscription.get_is_renewal_due())

    def test_get_is_expired(self):
        order = OrderFactory.create(status="approved")
        end_date = date.today()
        subscription = SubscriptionFactory.create(order=order, end_date=end_date)
        self.assertTrue(subscription.get_is_expired())

    def test_get_is_expired_false(self):
        order = OrderFactory.create(status="approved")
        end_date = date.today() + relativedelta(days=100)
        subscription = SubscriptionFactory.create(order=order, end_date=end_date)
        self.assertFalse(subscription.get_is_expired())
