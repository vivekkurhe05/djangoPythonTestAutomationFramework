import os

from countries.models import Country
from django.core import mail, signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import override_settings
from rolepermissions.checkers import has_role
from rolepermissions.roles import assign_role

from core.tests.utils import AnonymouseTestMixin, RequestTestCase
from .factories import InvitationFactory, UserFactory
from .. import views
from ..models import Organisation, OrganisationType, User


@override_settings(DISABLE_RECAPTCHA=False)
class TestRegisterView(RequestTestCase):
    view = views.RegisterView

    def setUp(self):
        country = Country.objects.get(code='KE')
        org_type = OrganisationType.objects.first()
        self.data = {
            'name': 'test user',
            'email': 'test.user@example.com',
            'password1': 'Password1',
            'password2': 'Password1',
            'user_mobile': '+918899889988',
            'job_role': 'Admin',
            'legal_name': 'Sample Organization',
            'known_as': 'Computer',
            'parent_organisation': 'Parent Organisation',
            'registration_number': 'ABPN223344D',
            'types': [org_type.pk],
            'address_1': 'Sample address 1',
            'address_2': 'Sample address 2',
            'city': 'Pune',
            'province': 'Pune',
            'zip': '411441',
            'country': country.pk,
            'phone_number': '+918899889988',
            'website': 'http://sample.org/',
            'token': '',
            'g-recaptcha-response': 'PASSED',
            'terms_of_service': True,
            'privacy_policy': True,
        }

        os.environ['RECAPTCHA_TESTING'] = 'True'

    def tearDown(self):
        del os.environ['RECAPTCHA_TESTING']

    def test_get(self):
        """Assert the register view can be displayed."""
        view = self.view.as_view()
        request = self.create_request('get', auth=False)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        """Assert a user can register."""

        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        expected_url = reverse('registration-confirm')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        user = User.objects.get()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(user.name, self.data['name'])
        self.assertEqual(user.email, self.data['email'])

    def test_post_file(self):
        file_contents = b'This is sample text'
        test_file = SimpleUploadedFile('test_file.txt', file_contents)

        self.data['supporting_file'] = test_file

        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        self.assertEqual(response.status_code, 302)
        organisation = Organisation.objects.get()
        self.assertTrue(organisation.supporting_file)
        self.assertEqual(organisation.supporting_file.read(), file_contents)
        organisation.supporting_file.delete()

    def test_post_with_invite(self):
        invitation = InvitationFactory.create(
            grantee=None,
            grantee_email=self.data['email'],
        )
        self.data['token'] = signing.dumps(invitation.id)

        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            'Thanks for signing up. Please login',
            request._messages.store[0],
        )
        self.assertEqual(len(mail.outbox), 0)

        user = User.objects.get()

        invitation.refresh_from_db()

        self.assertEqual(invitation.grantee, user.organisation)
        self.assertTrue(user.is_active)
        self.assertTrue(user.email_verified)
        self.assertFalse(invitation.accepted)

    def test_post_with_invite_other_email(self):
        invitation = InvitationFactory.create(
            grantee=None,
            grantee_email='other.user@example.com'
        )
        self.data['token'] = signing.dumps(invitation.id)

        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        expected_url = reverse('registration-confirm')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

        user = User.objects.get()

        invitation.refresh_from_db()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(user.name, self.data['name'])
        self.assertEqual(user.email, self.data['email'])

        self.assertEqual(invitation.grantee, user.organisation)
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertFalse(invitation.accepted)

    def test_post_with_invite_no_token(self):
        invitation = InvitationFactory.create(
            grantee=None,
            grantee_email=self.data['email']
        )

        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        self.assertEqual(response.status_code, 302)

        user = User.objects.get()

        invitation.refresh_from_db()

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(user.name, self.data['name'])
        self.assertEqual(user.email, self.data['email'])

        self.assertEqual(invitation.grantee, user.organisation)
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertFalse(invitation.accepted)

    def test_post_with_invite_bad_token(self):
        self.data['token'] = 'any'
        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Registration Failed, Invalid token',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.exists())

    def test_post_with_invite_does_not_exist(self):
        self.data['token'] = signing.dumps(1)
        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Registration Failed, Invalid token',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.exists())

    def test_post_with_invite_accepted(self):
        invitation = InvitationFactory.create(
            grantee=None,
            grantee_email=self.data['email'],
            accepted=True,
        )
        self.data['token'] = signing.dumps(invitation.id)

        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Registration Failed, Invalid token',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.exists())

    def test_post_with_invite_with_grantee(self):
        invitation = InvitationFactory.create(
            grantee_email=self.data['email'],
        )
        self.data['token'] = signing.dumps(invitation.id)

        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Registration Failed, Invalid token',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.exists())

    def test_invalid(self):
        view = self.view.as_view()
        request = self.create_request('post', auth=False, data={})
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Registration Failed, please correct the form',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.exists())

    def test_post_recaptcha_invalid(self):
        self.data['g-recaptcha-response'] = 'FAILED'
        view = self.view.as_view()
        request = self.create_request('post', auth=False, data=self.data)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Registration Failed, please correct the form',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.exists())


class TestOrganizationView(AnonymouseTestMixin, RequestTestCase):
    view = views.OrganizationView

    def setUp(self):
        super().setUp()
        self.view = self.view.as_view()
        self.user = UserFactory.create()

    def test_get_anonymous(self):
        request = self.create_request(auth=False)
        response = self.view(request)
        self.assertRedirectToLogin(response)

    def test_get_admin(self):
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_manager(self):
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_user(self):
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)


class TestAddUserView(AnonymouseTestMixin, RequestTestCase):
    view = views.AddUserView

    def setUp(self):
        super().setUp()
        self.view = self.view.as_view()
        self.user = UserFactory.create()

    def test_get_anonymous(self):
        request = self.create_request(auth=False)
        response = self.view(request)
        self.assertRedirectToLogin(response)

    def test_get_admin(self):
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_manager(self):
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_user(self):
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)

    def test_post(self):
        assign_role(self.user, 'admin')

        data = {
            'name': 'test user',
            'email': 'test.user@example.com',
            'user_mobile': '+918899889988',
            'job_role': 'Manager',
            'user_type': 'manager',
        }

        request = self.create_request('post', user=self.user, data=data)
        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            'User added successfully',
            request._messages.store[0],
        )

        self.assertEqual(len(mail.outbox), 1)
        subject = 'Welcome to the Global Grant Community'
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(data['email'], mail.outbox[0].to)

        user = User.objects.get(email=data['email'])

        self.assertEqual(user.name, data['name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.user_mobile, data['user_mobile'])
        self.assertEqual(user.job_role, data['job_role'])
        self.assertEqual(user.organisation, self.user.organisation)
        self.assertEqual(user.is_active, True)
        self.assertEqual(user.email_verified, True)
        self.assertEqual(has_role(user, data['user_type']), True)

    def test_post_invalid_data(self):
        assign_role(self.user, 'admin')

        data = {
            'name': 'test user',
            'email': 'test.user@example.com',
            'user_mobile': 'Invalid Mobile',
            'job_role': 'Manager',
            'user_type': 'manager',
        }

        request = self.create_request('post', user=self.user, data=data)
        response = self.view(request)
        user = User.objects.filter(email=data['email'])

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Add user failed, please correct the form',
            request._messages.store[0],
        )
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(user.exists())


class TestEditUserView(AnonymouseTestMixin, RequestTestCase):
    view = views.EditUserView

    def setUp(self):
        super().setUp()
        self.view = self.view.as_view()
        self.user = UserFactory.create()

    def test_get_permission_admin(self):
        assign_role(self.user, 'admin')

    def test_get_anonymous(self):
        request = self.create_request(auth=False)
        response = self.view(request, pk=self.user.id)
        self.assertRedirectToLogin(response)

    def test_get_admin(self):
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        with self.assertRaises(Http404):
            self.view(request, pk=self.user.id)

    def test_get_manager(self):
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = self.view(request, pk=self.user.id)
        self.assertEqual(response.status_code, 302)

    def test_get_user(self):
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        response = self.view(request, pk=self.user.id)
        self.assertEqual(response.status_code, 302)

    def test_post(self):
        assign_role(self.user, 'admin')

        data = {
            'name': 'test user',
            'email': 'test.user@example.com',
            'user_mobile': '+918899889988',
            'job_role': 'Manager',
            'user_type': 'manager',
        }

        request = self.create_request('post', user=self.user, data=data)
        with self.assertRaises(Http404):
            self.view(request, pk=self.user.id)

    def test_post_admin(self):
        assign_role(self.user, 'admin')

        data = {
            'name': 'test user',
            'email': 'test.user@example.com',
            'user_mobile': '+918899889988',
            'job_role': 'Manager',
            'user_type': 'manager',
        }

        request = self.create_request('post', user=self.user, data=data)

        test_user = UserFactory.create(organisation=self.user.organisation)
        assign_role(test_user, 'manager')
        response = self.view(request, pk=test_user.id)
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            'User updated successfully',
            request._messages.store[0],
        )

        user = User.objects.get(email=data['email'])

        self.assertEqual(user.name, data['name'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.user_mobile, data['user_mobile'])
        self.assertEqual(user.job_role, data['job_role'])
        self.assertEqual(user.organisation, test_user.organisation)
        self.assertEqual(has_role(user, data['user_type']), True)

    def test_post_invalid_data(self):
        assign_role(self.user, 'admin')

        data = {
            'name': 'test user',
            'email': 'test.user@example.com',
            'user_mobile': 'Invalid Mobile',
            'job_role': 'Manager',
            'user_type': 'manager',
        }

        request = self.create_request('post', user=self.user, data=data)

        test_user = UserFactory.create(organisation=self.user.organisation)
        response = self.view(request, pk=test_user.id)

        user = User.objects.filter(email=data['email'])

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'User update failed, please correct the form',
            request._messages.store[0],
        )
        self.assertFalse(user.exists())

    def test_post_other_organisation(self):
        data = {
            'name': 'test user',
            'email': 'test.user@example.com',
            'user_mobile': '+918899889988',
            'job_role': 'Manager',
            'user_type': 'manager',
        }
        assign_role(self.user, 'admin')
        request = self.create_request('post', user=self.user, data=data)
        test_user = UserFactory.create()
        assign_role(test_user, 'user')
        self.assertNotEqual(self.user.organisation, test_user.organisation)
        with self.assertRaises(Http404):
            self.view(request, pk=test_user.id)


class TestDeleteUserView(AnonymouseTestMixin, RequestTestCase):
    view = views.DeleteUserView

    def setUp(self):
        super().setUp()
        self.view = self.view.as_view()
        self.user = UserFactory.create()

    def test_get_not_authorised(self):
        request = self.create_request_ajax(user=self.user)
        response = self.view(request, pk=self.user.id)
        self.assertRedirectToLogin(response)

    def test_get_anonymous(self):
        request = self.create_request_ajax(auth=False)
        response = self.view(request, pk=self.user.id)
        self.assertRedirectToLogin(response)

    def test_get_not_ajax(self):
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        with self.assertRaises(Http404):
            self.view(request, pk=self.user.id)

    def test_get(self):
        assign_role(self.user, 'admin')
        request = self.create_request_ajax(user=self.user)

        with self.assertRaises(Http404):
            self.view(request, pk=self.user.id)

    def test_post_logged_in_user(self):
        assign_role(self.user, 'admin')
        request = self.create_request_ajax('post', user=self.user)

        with self.assertRaises(Http404):
            self.view(request, pk=self.user.id)

    def test_post_admin(self):
        assign_role(self.user, 'admin')
        request = self.create_request_ajax('post', user=self.user)
        test_user = UserFactory.create(organisation=self.user.organisation)
        assign_role(test_user, 'admin')
        response = self.view(request, pk=test_user.id)
        expected_url = reverse('organization')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        self.assertIn(
            'User successfully deleted',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.filter(id=test_user.id).exists())

    def test_post_manager(self):
        assign_role(self.user, 'admin')
        request = self.create_request_ajax('post', user=self.user)
        test_user = UserFactory.create(organisation=self.user.organisation)
        assign_role(test_user, 'manager')
        response = self.view(request, pk=test_user.id)
        expected_url = reverse('organization')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        self.assertIn(
            'User successfully deleted',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.filter(id=test_user.id).exists())

    def test_post_user(self):
        assign_role(self.user, 'admin')
        request = self.create_request_ajax('post', user=self.user)
        test_user = UserFactory.create(organisation=self.user.organisation)
        assign_role(test_user, 'user')
        response = self.view(request, pk=test_user.id)
        expected_url = reverse('organization')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        self.assertIn(
            'User successfully deleted',
            request._messages.store[0],
        )
        self.assertFalse(User.objects.filter(id=test_user.id).exists())

    def test_post_other_organisation(self):
        assign_role(self.user, 'admin')
        request = self.create_request_ajax('post', user=self.user)
        test_user = UserFactory.create()
        assign_role(test_user, 'user')
        self.assertNotEqual(self.user.organisation, test_user.organisation)
        with self.assertRaises(Http404):
            self.view(request, pk=test_user.id)


class TestEditOrganizationView(AnonymouseTestMixin, RequestTestCase):
    view = views.EditOrganizationView

    def setUp(self):
        super().setUp()
        country = Country.objects.get(code='KE')
        org_type = OrganisationType.objects.first()
        self.data = {
            'legal_name': 'Sample Organization',
            'known_as': 'Computer',
            'parent_organisation': 'Parent Organisation',
            'registration_number': 'ABPN223344D',
            'types': [org_type.pk],
            'address_1': 'Sample address 1',
            'address_2': 'Sample address 2',
            'city': 'Pune',
            'province': 'Pune',
            'zip': '411441',
            'country': country.pk,
            'phone_number': '+918899889988',
            'website': 'http://sample.org/',
        }
        self.view = self.view.as_view()
        self.user = UserFactory.create()

    def test_get_anonymous(self):
        request = self.create_request(auth=False)
        response = self.view(request, pk=self.user.id)
        self.assertRedirectToLogin(response)

    def test_get_admin(self):
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = self.view(request, pk=self.user.id)
        self.assertEqual(response.status_code, 200)

    def test_get_manager(self):
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = self.view(request, pk=self.user.id)
        self.assertEqual(response.status_code, 302)

    def test_get_user(self):
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        response = self.view(request, pk=self.user.id)
        self.assertEqual(response.status_code, 302)

    def test_post(self):
        assign_role(self.user, 'admin')
        request = self.create_request('post', user=self.user, data=self.data)
        response = self.view(request, pk=self.user.id)
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            'Organization updated successfully',
            request._messages.store[0],
        )

    def test_post_file(self):
        assign_role(self.user, 'admin')

        file_contents = b'This is sample text'
        test_file = SimpleUploadedFile('test_file.txt', file_contents)

        self.data['supporting_file'] = test_file

        request = self.create_request('post', user=self.user, data=self.data)
        response = self.view(request, pk=self.user.id)

        self.assertEqual(response.status_code, 302)
        organisation = Organisation.objects.get()
        self.assertTrue(organisation.supporting_file)
        self.assertEqual(organisation.supporting_file.read(), file_contents)
        organisation.supporting_file.delete()

    def test_post_invalid_data(self):
        assign_role(self.user, 'admin')
        self.data['phone_number'] = 'invalid_phone_number'
        request = self.create_request('post', user=self.user, data=self.data)
        response = self.view(request, pk=self.user.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'Organization update failed, please correct the form',
            request._messages.store[0],
        )


class TestOrganizationDetailView(AnonymouseTestMixin, RequestTestCase):
    view = views.OrganizationDetailView

    def setUp(self):
        super().setUp()
        self.view = self.view.as_view()
        self.user = UserFactory.create()

    def test_get_anonymous(self):
        request = self.create_request(auth=False)
        response = self.view(request, pk=self.user.organisation.id)
        self.assertRedirectToLogin(response)

    def test_get_user(self):
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        response = self.view(request, pk=self.user.organisation.id)
        self.assertEqual(response.status_code, 200)

    def test_get_invalid_id(self):
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        with self.assertRaises(Http404):
            self.view(request, pk=self.user.id)

    def test_get_queries(self):
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        """
        SELECT FROM "users_organisation"
         WHERE "users_organisation"."id" = 2988
        SELECT "auth_group"."id", "auth_group"."name"
          FROM "auth_group"
         INNER
          JOIN "users_user_groups"
            ON ("auth_group"."id" = "users_user_groups"."group_id")
         WHERE (
            "users_user_groups"."user_id" = 2332
            AND "auth_group"."name" IN ('manager', 'admin', 'user')
           )
         ORDER BY "auth_group"."name" ASC
        SELECT COUNT(*) AS "__count"
          FROM "users_organisation"
        SELECT
            "users_organisationtype"."id",
            "users_organisationtype"."name",
            COUNT("users_organisation_types"."organisation_id") AS "value"
          FROM "users_organisationtype"
          LEFT OUTER
          JOIN "users_organisation_types"
            ON ("users_organisationtype"."id" =
                "users_organisation_types"."organisationtype_id")
         GROUP BY "users_organisationtype"."id"
         ORDER BY "users_organisationtype"."sort_order" ASC
        SELECT FROM "page_page"
         WHERE (
           "page_page"."active" = true
           AND "page_page"."_cached_url" IN ('/')
           )
         ORDER BY "_url_length" DESC LIMIT 1
        SELECT FROM "users_organisationtype"
         INNER
          JOIN "users_organisation_types"
            ON ("users_organisationtype"."id" =
                "users_organisation_types"."organisationtype_id")
         WHERE "users_organisation_types"."organisation_id" = 2988
         ORDER BY "users_organisationtype"."sort_order" ASC
        SELECT FROM "surveys_surveyresponse"
         INNER
          JOIN "surveys_survey"
            ON ("surveys_surveyresponse"."survey_id" = "surveys_survey"."id")
         WHERE "surveys_surveyresponse"."organisation_id" = 2988
         ORDER BY "surveys_surveyresponse"."created" ASC
        SELECT "subscriptions_subscription"."id", "subscriptions_subscription"."order_id",
          "subscriptions_subscription"."start_date",
          "subscriptions_subscription"."end_date", "subscriptions_subscription"."price",
          "subscriptions_subscription"."created"
          FROM "subscriptions_subscription" INNER JOIN "subscriptions_order" ON (
            "subscriptions_subscription"."order_id" = "subscriptions_order"."id")
          WHERE ("subscriptions_order"."organisation_id" = 248648
          AND NOT ("subscriptions_order"."status" = 'canceled'))
          ORDER BY "subscriptions_subscription"."start_date" DESC LIMIT 1
        """
        with self.assertNumQueries(8):
            response = self.view(request, pk=self.user.organisation.id)
            response.render()
        self.assertEqual(response.status_code, 200)


class TestDirectoryView(AnonymouseTestMixin, RequestTestCase):
    view = views.DirectoryView

    def setUp(self):
        super().setUp()
        self.view = self.view.as_view()
        self.user = UserFactory.create()

    def test_get_anonymous(self):
        request = self.create_request(auth=False)
        response = self.view(request)
        self.assertRedirectToLogin(response)

    def test_get_user(self):
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_queries(self):
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        """
        SELECT "auth_group"."id", "auth_group"."name"
          FROM "auth_group"
         INNER
          JOIN "users_user_groups"
            ON ("auth_group"."id" = "users_user_groups"."group_id")
         WHERE (
                   "users_user_groups"."user_id" = 2367
           AND "auth_group"."name" IN ('admin', 'user', 'manager')
               )
         ORDER BY "auth_group"."name" ASC
        SELECT COUNT(*) AS "__count"
          FROM "users_organisation"
        SELECT
            "users_organisationtype"."id",
            "users_organisationtype"."name",
            COUNT("users_organisation_types"."organisation_id") AS "value"
          FROM "users_organisationtype"
          LEFT OUTER
          JOIN "users_organisation_types"
            ON ("users_organisationtype"."id"
                = "users_organisation_types"."organisationtype_id")
         GROUP BY "users_organisationtype"."id"
         ORDER BY "users_organisationtype"."sort_order" ASC
        SELECT FROM "page_page"
         WHERE (
                   "page_page"."active" = true
           AND "page_page"."_cached_url" IN ('/')
               )
         ORDER BY "_url_length" DESC LIMIT 1
        SELECT FROM "users_organisation"
        SELECT FROM "users_organisationtype"
         INNER
          JOIN "users_organisation_types"
            ON ("users_organisationtype"."id"
            = "users_organisation_types"."organisationtype_id")
         WHERE "users_organisation_types"."organisation_id" IN (3019)
         ORDER BY "users_organisationtype"."sort_order" ASC
        SELECT "subscriptions_subscription"."id", "subscriptions_subscription"."order_id",
          "subscriptions_subscription"."start_date",
          "subscriptions_subscription"."end_date", "subscriptions_subscription"."price",
          "subscriptions_subscription"."created"
          FROM "subscriptions_subscription" INNER JOIN "subscriptions_order" ON (
            "subscriptions_subscription"."order_id" = "subscriptions_order"."id")
          WHERE ("subscriptions_order"."organisation_id" = 248648
          AND NOT ("subscriptions_order"."status" = 'canceled'))
          ORDER BY "subscriptions_subscription"."start_date" DESC LIMIT 1
        """
        with self.assertNumQueries(7):
            response = self.view(request, pk=self.user.organisation.id)
            response.render()
        self.assertEqual(response.status_code, 200)
