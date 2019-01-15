from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.views import View
from django.views.generic.base import ContextMixin
from rolepermissions.roles import assign_role

from documents.tests.factories import DocumentFactory
from surveys.tests.factories import (
    SurveyAnswerFactory,
    SurveyFactory,
    SurveyQuestionFactory,
    SurveyResponseFactory,
)
from users.tests.factories import InvitationFactory, UserFactory
from .utils import AnonymouseTestMixin, RequestTestCase
from .. import mixins, views
from ..utils import Sidebar


class BlankView(mixins.AppMixin, ContextMixin, View):
    pass


class TestAppMixin(RequestTestCase):
    view_class = BlankView

    def setUp(self):
        super().setUp()
        self.view = self.view_class()
        self.user = UserFactory.create()

    def test_get_sidebar_sidebar_item_none(self):
        self.view.sidebar_item = None

        message = "You must specify 'sidebar_item' or override 'get_sidebar'."
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            self.view.get_sidebar(self.user)

    def test_get_sidebar_sidebar_section_none(self):
        self.view.sidebar_section = None

        message = "You must specify 'sidebar_section' or override 'get_sidebar'."
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            self.view.get_sidebar(self.user)

    def test_get_page_title_none(self):
        self.view.page_title = None

        message = "You must specify 'page_title' or override 'get_page_title'."
        with self.assertRaisesRegex(ImproperlyConfigured, message):
            self.view.get_page_title()

    def test_get_sidebar_active(self):
        assign_role(self.user, 'admin')
        self.view.sidebar_item = 'dashboard'
        sidebar = self.view.get_sidebar(self.user)
        self.assertEqual(sidebar['main']['dashboard']['class'], 'active')

    def test_get_sidebar_user(self):
        assign_role(self.user, 'user')
        self.view.sidebar_item = 'dashboard'
        sidebar = self.view.get_sidebar(self.user)
        self.assertFalse('invites' in sidebar['main'])
        self.assertFalse('users' in sidebar['settings'])

    def test_get_sidebar_manager(self):
        assign_role(self.user, 'manager')
        self.view.sidebar_item = 'dashboard'
        sidebar = self.view.get_sidebar(self.user)
        self.assertTrue('invites' in sidebar['main'])
        self.assertFalse('users' in sidebar['settings'])

    def test_get_sidebar_admin(self):
        assign_role(self.user, 'admin')
        self.view.sidebar_item = 'dashboard'
        sidebar = self.view.get_sidebar(self.user)
        self.assertTrue('invites' in sidebar['main'])
        self.assertTrue('users' in sidebar['settings'])

    def test_get_sidebar_anonymous(self):
        self.view.sidebar_item = 'dashboard'
        sidebar = self.view.get_sidebar(AnonymousUser())
        self.assertEqual(sidebar, {})

    def test_get_context_data(self):
        assign_role(self.user, 'admin')
        self.view.request = self.create_request(user=self.user)

        self.view.sidebar_item = 'dashboard'
        self.view.page_title = 'Dashboard'

        sidebar = Sidebar().set_sidebar_item_active('main', 'dashboard')

        context = self.view.get_context_data()
        expected = {
            'view': self.view,
            'page_title': 'Dashboard',
            'sidebar_main': sidebar['main'],
            'sidebar_settings': sidebar['settings'],
        }
        self.assertEqual(context, expected)


class TestHome(AnonymouseTestMixin, RequestTestCase):
    view = views.Home

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.survey = SurveyFactory.create()
        cls.question = SurveyQuestionFactory.create(survey=cls.survey, level=1)

    def test_get_user(self):
        request = self.create_request('get', user=self.user)
        view = self.view.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request('get', auth=False)
        response = view(request)
        self.assertRedirectToLogin(response)

    def test_survey_start_url(self):
        request = self.create_request('get', user=self.user)
        view = self.view.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

        expected_url = reverse('survey-start', kwargs={'pk': self.survey.pk})
        self.assertContains(response, expected_url)

    def test_survey_continue_url(self):
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            organisation=self.user.organisation,
        )

        request = self.create_request('get', user=self.user)
        view = self.view.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

        unexpected_url = reverse('survey-start', kwargs={'pk': self.survey.pk})
        expected_url = reverse('survey-progress', kwargs={'pk': survey_response.pk})
        self.assertContains(response, expected_url)
        self.assertNotContains(response, unexpected_url)

    def test_survey_complete_url(self):
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            organisation=self.user.organisation,
        )
        SurveyAnswerFactory.create(
            response=survey_response,
            question=self.question,
        )

        request = self.create_request('get', user=self.user)
        view = self.view.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

        unexpected_url = reverse('survey-start', kwargs={'pk': self.survey.pk})
        expected_url = reverse('survey-compliance', kwargs={'pk': survey_response.pk})
        self.assertContains(response, expected_url)
        self.assertNotContains(response, unexpected_url)

    def test_invite_url(self):
        assign_role(self.user, 'admin')
        request = self.create_request('get', user=self.user)
        view = self.view.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

        expected_url = reverse('survey-invite')
        self.assertContains(response, expected_url)

    def test_accept_invite_url(self):
        invite = InvitationFactory.create(grantee=self.user.organisation)
        assign_role(self.user, 'admin')
        request = self.create_request('get', user=self.user)
        view = self.view.as_view()
        response = view(request)
        self.assertEqual(response.status_code, 200)

        expected_url = reverse('invite-accept', kwargs={'pk': invite.pk})
        self.assertContains(response, expected_url)


class TestHomeContext(RequestTestCase):
    view = views.Home

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()
        cls.question = SurveyQuestionFactory.create(survey=cls.survey, level=1)
        cls.empty_survey = SurveyFactory.create()
        cls.grantee = UserFactory.create()
        cls.grantor = UserFactory.create()
        cls.other = UserFactory.create()

    def create_response(self, **kwargs):
        defaults = {'level': 1, 'survey': self.survey}
        defaults.update(kwargs)
        return SurveyResponseFactory.create(**defaults)

    def create_response_with_answer(self, **kwargs):
        response = self.create_response(**kwargs)
        SurveyAnswerFactory.create(
            response=response,
            question=self.question,
        )
        return response

    def get_context_data(self, user):
        view = self.view()
        view.request = self.create_request(user=user)
        return view.get_context_data()

    def test_get_survey_not_started(self):
        surveys = list(self.get_context_data(self.grantee)['surveys'])
        self.assertSequenceEqual(surveys, [self.survey, self.empty_survey])

        self.assertIsNone(surveys[0].survey_response)

    def test_get_survey_started(self):
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            organisation=self.grantee.organisation,
        )
        surveys = list(self.get_context_data(self.grantee)['surveys'])
        self.assertSequenceEqual(surveys, [self.survey, self.empty_survey])

        self.assertEqual(surveys[0].survey_response, survey_response)
        progress = surveys[0].survey_response.progress
        expected_progress = {
            'slug': 'not-started',
            'is_complete': False,
            'label': 'Not yet started',
            'total': 1,
            'count': 0,
            'percentage': 0,
            'ratio': 0.0,
        }
        self.assertEqual(progress, expected_progress)

    def test_get_invites(self):
        invite = InvitationFactory.create(
            grantee=self.grantee.organisation,
            accepted=False,
        )

        invites = self.get_context_data(self.grantee)['invites']
        self.assertSequenceEqual(invites, [invite])

    def test_get_invites_accepted(self):
        InvitationFactory.create(
            grantee=self.grantee.organisation,
            accepted=True,
        )
        invites = self.get_context_data(self.grantee)['invites']
        self.assertFalse(invites.exists())

    def test_get_invites_other_organisation(self):
        InvitationFactory.create(
            accepted=False,
        )
        invites = self.get_context_data(self.grantee)['invites']
        self.assertFalse(invites.exists())

    def test_get_documents_count(self):
        DocumentFactory.create_batch(2, organisation=self.grantee.organisation)
        documents_count = self.get_context_data(self.grantee)['documents_count']
        self.assertEqual(documents_count, 2)

    def test_get_documents_count_zero(self):
        documents_count = self.get_context_data(self.grantee)['documents_count']
        self.assertEqual(documents_count, 0)


class TestLanding(RequestTestCase):
    view = views.Landing

    def test_get_user(self):
        user = UserFactory()
        request = self.create_request('get', user=user)
        view = self.view.as_view()
        response = view(request)
        expected_url = reverse('home')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url + '/', expected_url)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request('get', auth=False)
        response = view(request)
        self.assertEqual(response.status_code, 200)
