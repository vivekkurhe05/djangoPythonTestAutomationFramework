from datetime import date

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.http import Http404
from rolepermissions.roles import assign_role

from core.tests.utils import AnonymouseTestMixin, RequestTestCase
from users.tests.factories import OrganisationFactory, UserFactory

from .factories import AssessmentPackageFactory, OrderFactory, SubscriptionFactory
from .. import views
from ..models import AssessmentPurchase, Order


class TestSubscriptionListView(AnonymouseTestMixin, RequestTestCase):
    view = views.SubscriptionListView

    @classmethod
    def setUpTestData(cls):
        cls.package1 = AssessmentPackageFactory.create(
            number_included=1,
            price=900.00
        )
        cls.package2 = AssessmentPackageFactory.create(
            number_included=10,
            price=10000.00
        )
        cls.package3 = AssessmentPackageFactory.create(
            number_included=100,
            price=40000.00
        )
        cls.packages = [cls.package1, cls.package2, cls.package3]

    def test_get_admin(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_manager(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'manager')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_user(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'user')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_packages(self):
        view = self.view()
        user = UserFactory.create()
        assign_role(user, 'admin')
        inactive_pacakge = AssessmentPackageFactory.create(
            is_active=False,
            number_included=20,
            price=30000.00
        )
        view.request = self.create_request(user=user)
        context = view.get_context_data()
        packages = context['packages']
        self.assertEqual(len(packages), 3)
        self.assertNotIn(inactive_pacakge, packages)

    def test_subscription_price(self):
        view = self.view()
        user = UserFactory.create()
        assign_role(user, 'admin')
        view.request = self.create_request(user=user)
        context = view.get_context_data()
        subscription = context['subscription_defaults']
        expected_price = settings.SITE_SUBSCRIPTION['price']
        self.assertEqual(subscription['price'], expected_price)


class TestOrderView(AnonymouseTestMixin, RequestTestCase):
    view = views.OrderView

    @classmethod
    def setUpTestData(cls):
        cls.organisation = OrganisationFactory.create()
        cls.user = UserFactory.create(organisation=cls.organisation)
        assign_role(cls.user, 'admin')

        cls.package1 = AssessmentPackageFactory.create(
            number_included=1,
            price=900.00
        )
        cls.package2 = AssessmentPackageFactory.create(
            number_included=10,
            price=10000.00
        )
        cls.package3 = AssessmentPackageFactory.create(
            number_included=100,
            price=40000.00
        )
        cls.packages = [cls.package1, cls.package2, cls.package3]

    def test_get_admin(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_manager(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'manager')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_user(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'user')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_already_active_subscription(self):
        """ Cannot order again if subcription is not active """
        view = self.view.as_view()
        order = OrderFactory.create(
            organisation=self.user.organisation,
            status=Order.STATUS_NEW
        )
        SubscriptionFactory.create(order=order)
        request = self.create_request(user=self.user)
        response = view(request)
        expected_url = reverse('subscription')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

    def test_post_no_subscription(self):
        """User cannot order if subscription not checked"""
        view = self.view.as_view()
        data = {
            'subscription': False,
        }
        request = self.create_request('post', user=self.user, data=data)
        view(request)
        expected_message = 'Order failed - Please select subscription to place the order'
        self.assertEqual(request._messages.store[0], expected_message)

    def test_post_first_subscription(self):
        """User can order only for subscription"""
        view = self.view.as_view()
        data = {
            'subscription': True,
        }
        request = self.create_request('post', user=self.user, data=data)
        response = view(request)

        expected_url = reverse('subscription')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        order = Order.objects.get()
        self.assertEqual(order.organisation, self.user.organisation)
        self.assertIsNotNone(order.subscription)
        with self.assertRaises(AssessmentPurchase.DoesNotExist):
            order.assessment_purchase

        self.assertEqual(len(mail.outbox), 1)
        order_number = '{:07d}'.format(order.pk)
        subject = 'GCC Order confirmation {}'.format(order_number)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
        )

    def test_post_first_subscription_with_package(self):
        """User can order subscription both subscription and package"""
        view = self.view.as_view()
        data = {
            'subscription': True,
            'package': self.package1.pk
        }
        request = self.create_request('post', user=self.user, data=data)
        response = view(request)

        expected_url = reverse('subscription')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        order = Order.objects.get()
        self.assertEqual(order.organisation, self.user.organisation)
        self.assertIsNotNone(order.subscription)
        self.assertEqual(order.assessment_purchase.package, self.package1)

        self.assertEqual(len(mail.outbox), 1)
        order_number = '{:07d}'.format(order.pk)
        subject = 'GCC Order confirmation {}'.format(order_number)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
        )

    def test_post_active_subscription_another_subscription(self):
        """User cannot order for subscription if already has active subscription"""
        view = self.view.as_view()
        subscription_order = OrderFactory.create(
            organisation=self.user.organisation,
            status=Order.STATUS_APPROVED
        )
        SubscriptionFactory.create(order=subscription_order)
        data = {
            'subscription': True
        }
        request = self.create_request('post', user=self.user, data=data)
        view(request)

        expected_message = 'Order failed - You already have an active subscription'

        self.assertEqual(request._messages.store[0], expected_message)
        self.assertEqual(Order.objects.count(), 1)

    def test_post_active_subscription_purchase_package(self):
        """User can purchase package with an active subscription"""
        view = self.view.as_view()
        subscription_order = OrderFactory.create(
            organisation=self.user.organisation,
            status=Order.STATUS_APPROVED
        )
        SubscriptionFactory.create(order=subscription_order)
        data = {
            'package': self.package1.pk
        }
        request = self.create_request('post', user=self.user, data=data)
        response = view(request)

        expected_url = reverse('subscription')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        order = Order.objects.all()[0]
        self.assertNotEqual(subscription_order, order)
        self.assertEqual(order.organisation, self.user.organisation)
        self.assertEqual(order.assessment_purchase.package, self.package1)

        self.assertEqual(len(mail.outbox), 1)
        order_number = '{:07d}'.format(order.pk)
        subject = 'GCC Order confirmation {}'.format(order_number)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
        )

    def test_post_form_invalid(self):
        """User get error when no package with active subscription"""
        view = self.view.as_view()
        data = {
            'subcription': 'test',
            'package': None
        }
        request = self.create_request('post', user=self.user, data=data)
        view(request)

        expected_message = 'Order failed - Please select subscription to place the order'
        self.assertEqual(request._messages.store[0], expected_message)
        self.assertFalse(Order.objects.exists())

    def test_post_active_subscription_no_package_none(self):
        """User get error when no package with active subscription"""
        view = self.view.as_view()
        order = OrderFactory.create(
            organisation=self.user.organisation,
            status=Order.STATUS_APPROVED
        )
        SubscriptionFactory.create(order=order)
        data = {
            'package': None
        }
        request = self.create_request('post', user=self.user, data=data)
        view(request)
        expected_message = 'Order failed - Please select a valid Assessment Package'

        self.assertEqual(request._messages.store[0], expected_message)
        self.assertEqual(Order.objects.count(), 1)

    def test_post_subscription_renewal_only_subscription(self):
        """User can order subscription when the subsciption renewal is due"""
        view = self.view.as_view()
        order = OrderFactory.create(
            organisation=self.user.organisation,
            status=Order.STATUS_APPROVED
        )
        end_date = date.today() + relativedelta(days=10)
        SubscriptionFactory.create(order=order, end_date=end_date)
        data = {
            'subscription': True,
            'package': ""
        }
        request = self.create_request('post', user=self.user, data=data)
        response = view(request)
        expected_url = reverse('subscription')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        order = Order.objects.all()[0]

        self.assertEqual(order.organisation, self.user.organisation)
        self.assertIsNotNone(order.subscription)
        self.assertEqual(len(mail.outbox), 1)

        order_number = '{:07d}'.format(order.pk)
        subject = 'GCC Order confirmation {}'.format(order_number)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
        )

    def test_post_subscription_renewal_with_package(self):
        """User can order subscription with package when the subsciption renewal is due"""
        view = self.view.as_view()
        order = OrderFactory.create(
            organisation=self.user.organisation,
            status=Order.STATUS_APPROVED
        )
        end_date = date.today() + relativedelta(days=10)
        SubscriptionFactory.create(order=order, end_date=end_date)
        data = {
            'subscription': True,
            'package': self.package1.pk
        }
        request = self.create_request('post', user=self.user, data=data)
        response = view(request)
        expected_url = reverse('subscription')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        order = Order.objects.all()[0]

        self.assertEqual(order.organisation, self.user.organisation)
        self.assertIsNotNone(order.subscription)
        self.assertEqual(order.assessment_purchase.package, self.package1)
        self.assertEqual(len(mail.outbox), 1)

        order_number = '{:07d}'.format(order.pk)
        subject = 'GCC Order confirmation {}'.format(order_number)
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(
            mail.outbox[0].from_email,
            settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL
        )


class TestOrderHistoryView(AnonymouseTestMixin, RequestTestCase):
    view = views.OrderHistoryView

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        assign_role(cls.user, 'admin')

    def test_get_admin(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_manager(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'manager')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_user(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'user')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)


class TestOrderDetailsView(AnonymouseTestMixin, RequestTestCase):
    view = views.OrderDetailsView

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        assign_role(cls.user, 'admin')

        cls.order = OrderFactory.create(
            organisation=cls.user.organisation,
            status=Order.STATUS_APPROVED
        )

    def test_get_admin(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        response = view(request, pk=self.order.pk)
        self.assertEqual(response.status_code, 200)

    def test_get_manager(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'manager')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_user(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'user')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_invalid_id(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        with self.assertRaises(Http404):
            view(request, pk=9999)
