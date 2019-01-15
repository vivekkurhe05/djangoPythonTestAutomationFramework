from datetime import date, timedelta

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rolepermissions.roles import assign_role

from surveys.tests.factories import SurveyResponseFactory

from .factories import InvitationFactory, OrganisationFactory, UserFactory
from ..models import get_invitation_status, Invitation, OrganisationType


class TestOrganisationType(TestCase):
    def test_str(self):
        org_type = OrganisationType.objects.first()
        self.assertEqual(str(org_type), org_type.name)


class TestOrganisation(TestCase):
    def test_str(self):
        organisation = OrganisationFactory.create()
        self.assertEqual(str(organisation), organisation.legal_name)


class TestInvitation(TestCase):
    def test_str(self):
        invitation = InvitationFactory.create()
        expected = '{} {}'.format(invitation.grantor, invitation.grantee)
        self.assertEqual(str(invitation), expected)

    def test_get_invitation_status(self):
        invitation = InvitationFactory.build()
        expected = invitation.get_status_display()
        self.assertEqual(get_invitation_status(invitation.status), expected)

    def test_highlight_invitation_due_date(self):
        invitation = InvitationFactory.create(due_date=date.today())
        expected = invitation.highlight_due_date()
        self.assertEqual(expected, True)

    def test_do_not_highlight_invitation_due_date(self):
        due_date = date.today() + timedelta(days=3)
        invitation = InvitationFactory.create(due_date=due_date)
        expected = invitation.highlight_due_date()
        self.assertEqual(expected, False)

    def test_do_not_highlight_invitation_due_date_submitted(self):
        due_date = date.today() + timedelta(days=-5)
        invitation = InvitationFactory.create(due_date=due_date, status=3)
        expected = invitation.highlight_due_date()
        self.assertEqual(expected, False)

    def test_send_invites(self):
        user = UserFactory.create()
        manager = UserFactory.create(organisation=user.organisation)
        assign_role(manager, 'manager')
        admin = UserFactory.create(organisation=user.organisation)
        assign_role(admin, 'admin')

        invitation = InvitationFactory.create(grantee=user.organisation)

        invitation.send_invites()
        self.assertEqual(len(mail.outbox), 2)
        subject = 'Invitation to submit assessment'
        self.assertEqual(mail.outbox[0].subject, subject)

        to_addresses = [address for email in mail.outbox for address in email.to]
        self.assertEqual(len(to_addresses), 2)
        self.assertIn(admin.email, to_addresses)
        self.assertIn(manager.email, to_addresses)

    def test_send_invites_unregistered(self):
        invitation = InvitationFactory.create(
            grantee_email='grantee@new-organisation.com',
        )

        invitation.send_invites_unregistered()
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        subject = 'Invitation to submit assessment'
        self.assertEqual(email.to[0], invitation.grantee_email)
        self.assertEqual(email.subject, subject)


class InvitationQueryset(TestCase):
    manager = Invitation.objects

    def test_with_submitted_response_id(self):
        response = SurveyResponseFactory.create(
            submitted=timezone.now(),
        )
        invitation = InvitationFactory.create(
            survey=response.survey,
            grantee=response.organisation,
        )
        invitations = self.manager.with_submitted_response_id()
        self.assertSequenceEqual(invitations, [invitation])
        self.assertEqual(invitations[0].response_id, response.id)

    def test_with_submitted_response_id_not_submitted(self):
        response = SurveyResponseFactory.create(
            submitted=None,
        )
        invitation = InvitationFactory.create(
            survey=response.survey,
            grantee=response.organisation,
        )
        invitations = self.manager.with_submitted_response_id()
        self.assertSequenceEqual(invitations, [invitation])
        self.assertIsNone(invitations[0].response_id)

    def test_with_submitted_response_id_other_organisation(self):
        response = SurveyResponseFactory.create(
            submitted=timezone.now(),
        )
        invitation = InvitationFactory.create(
            survey=response.survey,
        )
        invitations = self.manager.with_submitted_response_id()
        self.assertSequenceEqual(invitations, [invitation])
        self.assertIsNone(invitations[0].response_id)

    def test_with_submitted_response_id_other_survey(self):
        response = SurveyResponseFactory.create(
            submitted=timezone.now(),
        )
        invitation = InvitationFactory.create(
            grantee=response.organisation,
        )
        invitations = self.manager.with_submitted_response_id()
        self.assertSequenceEqual(invitations, [invitation])
        self.assertIsNone(invitations[0].response_id)
