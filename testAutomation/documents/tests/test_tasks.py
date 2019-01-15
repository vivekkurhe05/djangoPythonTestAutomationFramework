from datetime import date, timedelta

from django.core import mail
from django.test import override_settings, TestCase

from rolepermissions.roles import assign_role

from users.tests.factories import OrganisationFactory, UserFactory

from .factories import DocumentFactory
from ..tasks import check_document_expiry


class TestDocumentCeleryTasks(TestCase):

    def setUp(self):
        super().setUp()
        self.organisation = OrganisationFactory.create()
        self.user = UserFactory.create(organisation=self.organisation)
        assign_role(self.user, 'admin')

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_send_email_today(self):
        self.document = DocumentFactory.create(
            expiry=date.today(),
            organisation=self.organisation
        )

        check_document_expiry()

        self.assertEqual(len(mail.outbox), 1)
        subject = 'Action required - Document expiry notice.'
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertIn("today", mail.outbox[0].body,)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_send_email_later(self):
        self.document = DocumentFactory.create(
            expiry=date.today() + timedelta(days=14),
            organisation=self.organisation
        )
        check_document_expiry()

        self.assertEqual(len(mail.outbox), 1)
        subject = 'Action required - Document expiry notice.'
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(self.user.email, mail.outbox[0].to)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_send_email_none(self):
        DocumentFactory.create(
            expiry=date.today() + timedelta(days=1),
            organisation=self.organisation
        )
        DocumentFactory.create(
            expiry=date.today() + timedelta(days=2),
            organisation=self.organisation
        )
        DocumentFactory.create(
            expiry=date.today() + timedelta(days=13),
            organisation=self.organisation
        )
        DocumentFactory.create(
            expiry=date.today() + timedelta(days=15),
            organisation=self.organisation
        )
        DocumentFactory.create(
            expiry=date.today() + timedelta(days=20),
            organisation=self.organisation
        )

        check_document_expiry()
        self.assertEqual(len(mail.outbox), 0)
