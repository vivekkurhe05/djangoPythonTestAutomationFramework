from datetime import date, timedelta

from django.test import override_settings, tag, TestCase
from rolepermissions.roles import assign_role

from documents.tasks import check_document_expiry
from documents.tests.factories import DocumentFactory

from subscriptions.models import Order
from subscriptions.tasks import check_subscription_expiry
from subscriptions.tests.factories import (
    AssessmentPackageFactory,
    AssessmentPurchaseFactory,
    OrderFactory,
    SubscriptionFactory
)

from .factories import InvitationFactory, UserFactory
from ..forms import PasswordResetForm


@tag('email')
@override_settings(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend')
class TestEmails(TestCase):
    """
    Save the email copy to files so the copy can be checked.

    Emails will be saved to the folde `tmp` in the project root (as set by
    `EMAIL_FILE_PATH`)
    """

    def setUp(self):
        # The user must have a valid password for the password_reset email.
        self.user = UserFactory.create(password='zecret')
        self.order = OrderFactory.create(
            organisation=self.user.organisation,
            status=Order.STATUS_APPROVED
        )

    def test_validation_email(self):
        self.user.send_validation_email()

    def test_send_welcome_invite(self):
        assign_role(self.user, 'user')
        self.user.send_welcome_invite()

    def test_send_invites(self):
        manager = UserFactory.create()
        assign_role(manager, 'manager')

        invitation = InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=manager.organisation,
        )

        invitation.send_invites()

    def test_send_invites_unregistered(self):
        invitation = InvitationFactory.build(
            grantor=self.user.organisation,
            grantee_email='grantee@new-organisation.com',
        )

        invitation.send_invites_unregistered()

    def test_password_reset(self):
        data = {
            'email': self.user.email
        }
        form = PasswordResetForm(data=data)
        self.assertTrue(form.is_valid())
        form.save()

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_expired_documents_today(self):
        assign_role(self.user, 'manager')
        self.document = DocumentFactory.create(
            expiry=date.today(),
            organisation=self.user.organisation
        )
        check_document_expiry()
        self.document.file.delete()

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_expired_documents_later(self):
        assign_role(self.user, 'manager')
        self.document = DocumentFactory.create(
            expiry=date.today() + timedelta(days=14),
            organisation=self.user.organisation
        )
        check_document_expiry()
        self.document.file.delete()

    def test_order_confirmation_subscription(self):
        assign_role(self.user, 'admin')
        self.subscription = SubscriptionFactory.create(order=self.order)
        self.order.send_order_confirmation()

    def test_order_confirmation_package(self):
        assign_role(self.user, 'admin')
        package = AssessmentPackageFactory.create(
            number_included=1,
            price=900.00
        )
        AssessmentPurchaseFactory.create(
            package=package,
            order=self.order,
            number_included=1,
            price=900.00
        )
        self.order.send_order_confirmation()

    def test_order_completion_subscription(self):
        assign_role(self.user, 'admin')
        self.subscription = SubscriptionFactory.create(
            order__organisation=self.user.organisation,
            order__status=Order.STATUS_APPROVED
        )
        self.subscription.order.send_order_completion()

    def test_order_canceled_subscription(self):
        assign_role(self.user, 'admin')
        self.subscription = SubscriptionFactory.create(
            order__organisation=self.user.organisation,
            order__status=Order.STATUS_CANCELED
        )
        self.subscription.order.send_order_cancelation()

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_subscription_renewal_today(self):
        assign_role(self.user, 'admin')
        self.subscription = SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=0),
            order=self.order
        )
        check_subscription_expiry()

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_subscription_renewal_one_week(self):
        assign_role(self.user, 'admin')
        self.subscription = SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=7),
            order=self.order
        )
        check_subscription_expiry()

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_subscription_renewal_one_month(self):
        assign_role(self.user, 'admin')
        self.subscription = SubscriptionFactory.create(
            end_date=date.today() + timedelta(days=30),
            order=self.order
        )
        check_subscription_expiry()
