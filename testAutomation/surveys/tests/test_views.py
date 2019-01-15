from datetime import date

from unittest.mock import patch

from django.core import mail
from django.core.urlresolvers import reverse
from django.http import Http404
from django.utils import timezone
from django.views import View
from rolepermissions.roles import assign_role

from core.tests.utils import AnonymouseTestMixin, RequestTestCase
from documents.models import Document
from subscriptions.models import Order
from subscriptions.tests.factories import (
    AssessmentPurchaseFactory,
    SubscriptionFactory
)
from users.models import Invitation
from users.tests.factories import InvitationFactory, OrganisationFactory, UserFactory
from .factories import (
    SurveyAnswerDocumentFactory,
    SurveyAnswerFactory,
    SurveyAreaFactory,
    SurveyFactory,
    SurveyQuestionFactory,
    SurveyQuestionOptionFactory,
    SurveyResponseFactory,
    SurveySectionFactory,
)
from .. import views
from ..models import SurveyAnswer, SurveyAnswerDocument, SurveyResponse


class BlankView(views.SurveyViewMixin, View):
    pass


class TestSurveyViewMixin(AnonymouseTestMixin, RequestTestCase):
    view_class = BlankView

    def setUp(self):
        super().setUp()
        self.view = self.view_class()
        self.user = UserFactory.create()
        self.request = self.create_request(user=self.user)

    def test_dispatch_grantee(self):
        response = SurveyResponseFactory.create(pk=1, organisation=self.user.organisation)
        SurveyQuestionFactory.create(survey=response.survey)
        self.view.dispatch(self.request, pk=1)
        self.assertEqual(self.view.survey_response, response)

    def test_dispatch_404(self):
        SurveyResponseFactory.create(pk=1)
        with self.assertRaises(Http404):
            self.view.dispatch(self.request, pk=1)


class TestSurveyStartView(AnonymouseTestMixin, RequestTestCase):
    view = views.SurveyStartView

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()

    def test_get(self):
        question = SurveyQuestionFactory.create(survey=self.survey)
        view = self.view.as_view()

        request = self.create_request()
        response = view(request, pk=self.survey.pk)
        self.assertEqual(response.status_code, 302)

        # Ensure a new SurveyResponse was initialised correctly.
        survey_response = SurveyResponse.objects.get(
            organisation=request.user.organisation,
            survey=self.survey,
        )
        expected_url = reverse(
            'survey-section',
            kwargs={'pk': survey_response.pk, 'section': question.section.pk},
        )
        self.assertEqual(response.url, expected_url)

    def test_get_exists(self):
        question = SurveyQuestionFactory.create(survey=self.survey)

        view = self.view.as_view()
        request = self.create_request()

        SurveyResponseFactory.create(
            organisation=request.user.organisation,
            survey=self.survey,
        )

        response = view(request, pk=self.survey.pk)
        self.assertEqual(response.status_code, 302)

        # Ensure no new SurveyResponse was created.
        survey_response = SurveyResponse.objects.get(
            organisation=request.user.organisation,
            survey=self.survey,
        )
        expected_url = reverse(
            'survey-section',
            kwargs={'pk': survey_response.pk, 'section': question.section.pk},
        )
        self.assertEqual(response.url, expected_url)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request, pk=self.survey.pk)
        self.assertRedirectToLogin(response)

    def test_survey_does_not_exist(self):
        view = self.view.as_view()
        request = self.create_request()
        with self.assertRaises(Http404):
            view(request, pk=100, level=1)

    def test_no_section(self):
        view = self.view.as_view()
        request = self.create_request()
        with self.assertRaises(Http404):
            view(request, pk=self.survey.pk)


class TestSurveySectionView(AnonymouseTestMixin, RequestTestCase):
    view = views.SurveySectionView

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.survey_response = SurveyResponseFactory.create(
            organisation=self.user.organisation,
            survey=self.survey,
            level=1,
        )
        self.area = SurveyAreaFactory.create(number=4)
        self.section = SurveySectionFactory.create(
            number=1,
            area=self.area,
        )
        self.question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section
        )

    def test_get(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        response = view(request, pk=self.survey_response.pk, section=self.section.pk)
        self.assertEqual(response.status_code, 200)

    def test_get_first(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        response = view(request, pk=self.survey_response.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['section'], self.section)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request, pk=self.survey_response.pk, section=self.section.pk)
        self.assertRedirectToLogin(response)

    def test_get_other(self):
        view = self.view.as_view()
        request = self.create_request()
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            level=1,
        )
        self.assertNotEqual(request.user.organisation, survey_response.organisation)
        with self.assertRaises(Http404):
            view(request, pk=survey_response.pk, section=self.section.pk)

    def test_get_404(self):
        """
        SurveyViewMixin provides a 404 response if the user doesn't have a
        SurveyResponse.
        """
        view = self.view.as_view()
        request = self.create_request()
        with self.assertRaises(Http404):
            view(
                request,
                pk=self.survey_response.pk + 1,
                section=SurveySectionFactory.create(
                    number=2,
                    area=self.area,
                )
            )

    def test_get_context_data(self):
        section_2 = SurveySectionFactory.create(number=2, area=self.area)
        SurveyQuestionFactory.create(survey=self.survey, level=1, section=section_2)
        section_3 = SurveySectionFactory.create(number=3, area=self.area)
        SurveyQuestionFactory.create(survey=self.survey, level=1, section=section_3)

        view = self.view()
        view.survey = self.survey
        view.level = 1
        view.section = section_2
        view.object = self.survey_response
        view.questions = self.survey.questions.all()
        view.request = self.create_request()
        context = view.get_context_data()

        summary_url = reverse('survey-progress', kwargs={
            'pk': self.survey_response.pk,
        })
        previous_url = reverse('survey-section', kwargs={
            'pk': self.survey_response.pk,
            'section': self.section.pk,
        })
        next_url = reverse('survey-section', kwargs={
            'pk': self.survey_response.pk,
            'section': section_3.pk,
        })

        self.assertEqual(context['survey'], self.survey)
        self.assertEqual(context['level_display'], 'Bronze')
        self.assertEqual(context['section'], section_2)
        self.assertEqual(context['previous_url'], previous_url)
        self.assertEqual(context['summary_url'], summary_url)
        self.assertEqual(context['next_url'], next_url)

    def test_progress_cached(self):
        view = self.view()
        view.object = self.survey_response
        expected = self.survey_response.get_progress()

        with self.assertNumQueries(3):
            self.assertEqual(view.progress, expected)
        with self.assertNumQueries(0):
            self.assertEqual(view.progress, expected)

    def test_post(self):
        view = self.view.as_view()
        data = {
            'level': 2,
        }

        self.assertNotEqual(
            self.survey_response.level,
            data['level'],
        )

        request = self.create_request('post', user=self.user, data=data)
        response = view(
            request,
            pk=self.survey_response.pk,
            section=self.question.section.pk,
        )
        self.assertEqual(response.status_code, 302)

        self.survey_response.refresh_from_db()
        self.assertEqual(
            self.survey_response.level,
            data['level'],
        )

    def test_get_success_url(self):
        view = self.view()
        view.survey = self.survey
        view.section = self.section
        view.object = self.survey_response

        expected_url = reverse('survey-section', kwargs={
            'pk': self.survey_response.pk,
            'section': self.section.pk,
        })
        self.assertEqual(view.get_success_url(), expected_url)

    def test_get_summary_url(self):
        view = self.view()
        view.survey = self.survey
        view.section = self.section
        view.object = self.survey_response
        view.request = self.create_request(user=self.user)

        expected = reverse('survey-progress', kwargs={
            'pk': self.survey_response.pk,
        })
        self.assertEqual(view.get_summary_url(), expected)

    def test_get_summary_url_complete(self):
        SurveyAnswerFactory.create(
            response=self.survey_response,
            question=self.question,
        )
        view = self.view()
        view.survey = self.survey
        view.section = self.section
        view.object = self.survey_response
        view.request = self.create_request(user=self.user)

        expected = reverse('survey-compliance', kwargs={
            'pk': self.survey_response.pk,
        })
        self.assertEqual(view.get_summary_url(), expected)

    def test_get_levels(self):
        view = self.view()
        view.object = view.survey_response = self.survey_response
        view.questions = [self.question]
        view.answers_lookup = {}

        levels = list(view.get_levels())

        self.assertEqual(len(levels), 4)

        for level in levels:
            level['forms'] = list(level.pop('forms'))

        expected = [
            {
                'hide': False,
                'level': 1,
                'label': 'Bronze',
                'forms': [levels[0]['forms'][0]],
            },
            {
                'hide': True,
                'level': 2,
                'label': 'Silver',
                'forms': [],
            },
            {
                'hide': True,
                'level': 3,
                'label': 'Gold',
                'forms': [],
            },
            {
                'hide': True,
                'level': 4,
                'label': 'Platinum',
                'forms': [],
            },
        ]
        self.assertSequenceEqual(levels, expected)

    def test_get_answer_form(self):
        view = self.view()
        view.object = view.survey_response = self.survey_response
        view.questions = [self.question]
        answer = SurveyAnswerFactory.create()
        view.answers_lookup = {self.question.pk: answer}

        form = view.get_answer_form(self.question)
        self.assertEqual(form.instance, answer)

    def test_get_answer_form_kwargs(self):
        view = self.view()
        view.survey_response = self.survey_response

        kwargs = view.get_answer_form_kwargs(self.question)
        expected = {
            'prefix': 'level_{}_{}'.format(self.question.level, self.question.pk),
            'question': self.question,
            'response': self.survey_response,
        }
        self.assertEqual(kwargs, expected)

    def test_get_section(self):
        view = self.view()
        view.survey = self.survey
        view.object = self.survey_response
        view.request = self.create_request(user=self.user)
        view.kwargs = {'section': self.section.pk}

        section = view.get_section()
        self.assertEqual(section, self.section)

        SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section__area__number=1
        )
        section = view.get_section()
        self.assertEqual(section, self.section)

    def test_get_section_first(self):
        view = self.view()
        view.survey = self.survey
        view.object = self.survey_response
        view.request = self.create_request(user=self.user)
        view.kwargs = {}

        section = view.get_section()
        self.assertEqual(section, self.section)

        question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section__area__number=1
        )
        section = view.get_section()
        self.assertEqual(section, question.section)

    def test_get_section_none(self):
        view = self.view()
        response = SurveyResponseFactory.create(
            organisation=self.user.organisation,
        )
        view.object = response
        view.survey = response.survey
        view.request = self.create_request(user=self.user)
        view.kwargs = {}

        with self.assertRaises(Http404):
            view.get_section()


class TestSurveyAnswerView(AnonymouseTestMixin, RequestTestCase):
    view = views.SurveyAnswerView

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.survey_response = SurveyResponseFactory.create(
            organisation=self.user.organisation,
            survey=self.survey,
            level=1,
        )
        self.question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
        )
        self.options = SurveyQuestionOptionFactory.create_batch(
            3,
            question=self.question,
        )

    def create_answer(self):
        answer = SurveyAnswerFactory.create(
            response=self.survey_response,
            question=self.question,
        )
        answer.options.add(*self.options[2:])
        return answer

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request_ajax(auth=False)
        response = view(request, pk=self.survey_response.pk, question=self.question.pk)
        self.assertRedirectToLogin(response)

    def test_get_not_ajax(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        with self.assertRaises(Http404):
            view(request, pk=self.survey_response.pk, question=self.question.pk)

    def test_get_create(self):
        view = self.view.as_view()
        request = self.create_request_ajax(user=self.user)
        response = view(request, pk=self.survey_response.pk, question=self.question.pk)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context_data['form'].instance.pk)

    def test_get_update(self):
        answer = self.create_answer()
        view = self.view.as_view()
        request = self.create_request_ajax(user=self.user)
        response = view(request, pk=self.survey_response.pk, question=self.question.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['form'].instance, answer)

    def test_post_create(self):
        view = self.view.as_view()
        options = self.options[:2]
        prefix = 'level_1_%s-' % self.question.pk
        data = {
            '%svalue' % prefix: SurveyAnswer.ANSWER_YES,
            '%soptions' % prefix: [o.pk for o in options],
        }

        request = self.create_request('post', user=self.user, data=data)
        response = view(request, pk=self.survey_response.pk, question=self.question.pk)
        self.assertEqual(response.status_code, 302)

        self.survey_response.refresh_from_db()
        answer = self.survey_response.answers.get()
        self.assertEqual(answer.value, SurveyAnswer.ANSWER_YES)
        self.assertSequenceEqual(answer.options.all(), options)

        self.assertEqual(
            request._messages.store[0],
            'Answer saved',
        )

        expected_url = reverse('survey-answer', kwargs={
            'pk': self.survey_response.pk,
            'question': self.question.pk,
        })
        self.assertEqual(response.url, expected_url)

    def test_post_update(self):
        answer = self.create_answer()
        view = self.view.as_view()
        options = self.options[:2]
        prefix = 'level_1_%s-' % self.question.pk
        data = {
            '%svalue' % prefix: SurveyAnswer.ANSWER_NO,
            '%soptions' % prefix: [o.pk for o in options],
            '%sexplanation' % prefix: 'Any',
        }

        request = self.create_request('post', user=self.user, data=data)
        response = view(request, pk=self.survey_response.pk, question=self.question.pk)
        self.assertEqual(response.status_code, 302)

        answer.refresh_from_db()
        self.assertEqual(answer.value, SurveyAnswer.ANSWER_NO)
        self.assertSequenceEqual(answer.options.all(), options)

        self.assertEqual(
            request._messages.store[0],
            'Answer saved',
        )

        expected_url = reverse('survey-answer', kwargs={
            'pk': self.survey_response.pk,
            'question': self.question.pk,
        })
        self.assertEqual(response.url, expected_url)

    def test_post_error(self):
        view = self.view.as_view()
        prefix = 'level_1_%s-' % self.question.pk
        data = {
            '%svalue' % prefix: SurveyAnswer.ANSWER_PROGRESS,
        }

        request = self.create_request('post', user=self.user, data=data)
        response = view(request, pk=self.survey_response.pk, question=self.question.pk)
        self.assertEqual(response.status_code, 200)
        errors = response.context_data['form'].errors
        self.assertIn('explanation', errors)
        self.assertIn('due_date', errors)

        self.assertEqual(
            request._messages.store[0],
            'Answer not saved, please correct the form',
        )


class TestSurveyAnswerDocumentDelete(AnonymouseTestMixin, RequestTestCase):
    view = views.SurveyAnswerDocumentDelete

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.answer_document = SurveyAnswerDocumentFactory.create(
            answer__response__organisation=self.user.organisation,
            answer__value=SurveyAnswer.ANSWER_YES,
        )
        # Other document must be attached to answer for removal to be allowed.
        SurveyAnswerDocumentFactory.create(
            answer=self.answer_document.answer,
        )

    def test_get(self):
        view = self.view.as_view()
        request = self.create_request_ajax(user=self.user)
        response = view(request, pk=self.answer_document.pk)
        self.assertEqual(response.status_code, 200)

        expected_url = reverse('survey-document-delete', kwargs={
            'pk': self.answer_document.pk,
        })
        self.assertContains(response, expected_url)

    def test_get_last(self):
        "No delete form displayed for last document if the answer value is YES"
        answer_document = SurveyAnswerDocumentFactory.create(
            answer__response__organisation=self.user.organisation,
            answer__value=SurveyAnswer.ANSWER_YES,
        )
        view = self.view.as_view()
        request = self.create_request_ajax(user=self.user)
        response = view(request, pk=answer_document.pk)
        self.assertEqual(response.status_code, 200)

        expected_url = reverse('survey-document-delete', kwargs={
            'pk': self.answer_document.pk,
        })
        self.assertNotContains(response, expected_url)

    def test_get_last_in_progress(self):
        "Delete form displayed for last document if the answer value is In Progress"
        answer_document = SurveyAnswerDocumentFactory.create(
            answer__response__organisation=self.user.organisation,
            answer__value=SurveyAnswer.ANSWER_PROGRESS,
        )

        view = self.view.as_view()
        request = self.create_request_ajax(user=self.user)
        response = view(request, pk=answer_document.pk)
        self.assertEqual(response.status_code, 200)

        expected_url = reverse('survey-document-delete', kwargs={
            'pk': answer_document.pk,
        })
        self.assertContains(response, expected_url)

    def test_get_not_owner(self):
        answer_document = SurveyAnswerDocumentFactory.create()
        view = self.view.as_view()

        request = self.create_request_ajax()
        with self.assertRaises(Http404):
            view(request, pk=answer_document.pk)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request, pk=self.answer_document.pk)
        self.assertRedirectToLogin(response)

    def test_get_not_ajax(self):
        view = self.view.as_view()

        request = self.create_request(user=self.user)
        with self.assertRaises(Http404):
            view(request, pk=self.answer_document.pk)

    def test_post_not_ajax(self):
        "Non AJAX post should delete the object and redirect to the survey section"
        answer = self.answer_document.answer
        view = self.view.as_view()
        request = self.create_request('post', user=self.user, data={})
        response = view(request, pk=self.answer_document.pk)

        expected_url = reverse('survey-section', kwargs={
            'pk': answer.response.pk,
            'section': answer.question.section.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

        self.assertEqual(
            request._messages.store[0],
            'Document successfully removed',
        )

        deleted = SurveyAnswerDocument.objects.filter(pk=self.answer_document.pk)
        self.assertFalse(deleted.exists())

    def test_post(self):
        "AJAX post should delete the object and redirect to the survey answer"
        answer = self.answer_document.answer
        document = self.answer_document.document
        view = self.view.as_view()
        request = self.create_request_ajax('post', user=self.user, data={})
        response = view(request, pk=self.answer_document.pk)

        expected_url = reverse('survey-answer', kwargs={
            'pk': answer.response.pk,
            'question': answer.question.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        deleted = SurveyAnswerDocument.objects.filter(pk=self.answer_document.pk)
        self.assertFalse(deleted.exists())
        self.assertEqual(Document.objects.get(pk=document.pk), document)

    def test_post_last(self):
        "Can not delete the last document if the answer value is Yes"
        answer_document = SurveyAnswerDocumentFactory.create(
            answer__response__organisation=self.user.organisation,
            answer__value=SurveyAnswer.ANSWER_YES,
        )
        view = self.view.as_view()
        request = self.create_request_ajax('post', user=self.user, data={})
        response = view(request, pk=answer_document.pk)

        self.assertEqual(response.status_code, 302)

        expected_message = (
            'You must have at least one document attached, please select '
            'in progress before you remove the document'
        )
        self.assertEqual(request._messages.store[0], expected_message)

        not_deleted = SurveyAnswerDocument.objects.filter(pk=answer_document.pk)
        self.assertTrue(not_deleted.exists())

    def test_post_last_in_progress(self):
        "Can delete the last document if the answer value is In Progress"
        answer_document = SurveyAnswerDocumentFactory.create(
            answer__response__organisation=self.user.organisation,
            answer__value=SurveyAnswer.ANSWER_PROGRESS,
        )
        view = self.view.as_view()
        request = self.create_request_ajax('post', user=self.user, data={})
        response = view(request, pk=answer_document.pk)

        self.assertEqual(response.status_code, 302)
        deleted = SurveyAnswerDocument.objects.filter(pk=answer_document.pk)
        self.assertFalse(deleted.exists())


class TestSurveyAnswerDeleteView(AnonymouseTestMixin, RequestTestCase):
    view = views.SurveyAnswerDeleteView

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.survey_response = SurveyResponseFactory.create(
            organisation=self.user.organisation,
            survey=self.survey,
            level=1,
        )
        self.question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
        )
        self.options = SurveyQuestionOptionFactory.create_batch(
            3,
            question=self.question,
        )
        self.answer = SurveyAnswerFactory.create(
            response=self.survey_response,
            question=self.question,
        )
        self.answer.options.add(*self.options[2:])

    def test_get(self):
        view = self.view.as_view()
        request = self.create_request_ajax(user=self.user)
        response = view(request, pk=self.answer.pk)
        self.assertEqual(response.status_code, 200)

        expected_url = reverse('survey-answer-delete', kwargs={
            'pk': self.answer.pk,
        })
        self.assertContains(response, expected_url)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request, pk=self.answer.pk)
        self.assertRedirectToLogin(response)

    def test_get_not_ajax(self):
        view = self.view.as_view()

        request = self.create_request(user=self.user)
        with self.assertRaises(Http404):
            view(request, pk=self.answer.pk)

    def test_post(self):
        "AJAX post should delete the object and redirect to the survey answer"
        view = self.view.as_view()
        request = self.create_request_ajax('post', user=self.user, data={})
        response = view(request, pk=self.answer.pk)

        expected_url = reverse('survey-answer', kwargs={
            'pk': self.survey_response.pk,
            'question': self.question.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)
        deleted = SurveyAnswer.objects.filter(pk=self.answer.pk)
        self.assertFalse(deleted.exists())


class TestSurveyProgresssReport(AnonymouseTestMixin, RequestTestCase):
    view = views.SurveyProgresssReport

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.survey_response = SurveyResponseFactory.create(
            organisation=self.user.organisation,
            survey=self.survey,
            level=1,
        )
        self.area = SurveyAreaFactory.create(number=4)
        self.section = SurveySectionFactory.create(
            number=1,
            area=self.area,
        )
        self.question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section
        )

    def test_get(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        response = view(request, pk=self.survey_response.pk)
        self.assertEqual(response.status_code, 200)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request, pk=self.survey_response.pk)
        self.assertRedirectToLogin(response)

    def test_get_other(self):
        view = self.view.as_view()
        request = self.create_request()
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            level=1,
        )
        self.assertNotEqual(request.user.organisation, survey_response.organisation)
        with self.assertRaises(Http404):
            view(request, pk=survey_response.pk)

    def test_get_context_data(self):
        view = self.view()
        view.survey = self.survey
        view.level = 1
        view.object = self.survey_response
        view.request = self.create_request()
        context = view.get_context_data()

        expected = self.survey_response.get_progress()
        self.assertEqual(context['progress'], expected)

    def test_post(self):
        view = self.view.as_view()
        data = {'level': 2}

        self.assertNotEqual(self.survey_response.level, data['level'])

        request = self.create_request('post', user=self.user, data=data)
        response = view(request, pk=self.survey_response.pk)

        expected_url = reverse('survey-progress', kwargs={'pk': self.survey_response.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

        self.survey_response.refresh_from_db()
        self.assertEqual(self.survey_response.level, data['level'])


class TestSurveyComplianceReport(AnonymouseTestMixin, RequestTestCase):
    view = views.SurveyComplianceReport

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.survey_response = SurveyResponseFactory.create(
            organisation=self.user.organisation,
            survey=self.survey,
            level=1,
        )
        self.area = SurveyAreaFactory.create(number=4)
        self.section = SurveySectionFactory.create(
            number=1,
            area=self.area,
        )
        self.question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section
        )

    def test_get(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        response = view(request, pk=self.survey_response.pk)
        self.assertEqual(response.status_code, 200)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request, pk=self.survey_response.pk)
        self.assertRedirectToLogin(response)

    def test_get_other(self):
        view = self.view.as_view()
        request = self.create_request()
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            level=1,
        )
        self.assertNotEqual(request.user.organisation, survey_response.organisation)
        with self.assertRaises(Http404):
            view(request, pk=survey_response.pk)

    def test_get_context_data(self):
        view = self.view()
        view.survey = self.survey
        view.level = 1
        view.object = self.survey_response
        view.request = self.create_request()
        context = view.get_context_data()

        expected = self.survey_response.get_compliance()
        compliance = expected['compliance']

        self.assertEqual(context['progress'], expected['progress'])
        self.assertEqual(context['compliance'], compliance)
        self.assertEqual(context['target_level_progress'], compliance['levels'][1])

    def test_post(self):
        survey_response = self.survey_response
        view = self.view.as_view()
        data = {'level': 2}

        self.assertNotEqual(survey_response.level, data['level'])

        request = self.create_request('post', user=self.user, data=data)
        response = view(request, pk=survey_response.pk)

        expected_url = reverse('survey-compliance', kwargs={'pk': survey_response.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

        survey_response.refresh_from_db()
        self.assertEqual(survey_response.level, data['level'])


class TestSurveyFullReport(AnonymouseTestMixin, RequestTestCase):
    view = views.SurveyFullReport

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.survey_response = SurveyResponseFactory.create(
            organisation=self.user.organisation,
            survey=self.survey,
            level=1,
        )
        self.area = SurveyAreaFactory.create(number=4)
        self.section = SurveySectionFactory.create(
            number=1,
            area=self.area,
        )
        self.question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section
        )
        self.options = SurveyQuestionOptionFactory.create_batch(
            3,
            question=self.question,
        )
        self.answer = SurveyAnswerFactory.create(
            response=self.survey_response,
            question=self.question,
        )
        self.answer.options.add(*self.options[1:])
        self.documents = SurveyAnswerDocumentFactory.create_batch(
            3,
            answer=self.answer,
        )

    def create_grantor(self):
        self.grantor_user = UserFactory.create()
        self.invitation = InvitationFactory.create(
            survey=self.survey,
            grantee=self.survey_response.organisation,
            accepted=True,
            grantor=self.grantor_user.organisation
        )
        self.survey_response.submitted = timezone.now()
        self.survey_response.save()

    def test_get_survey_queryset_grantee(self):
        view = self.view()
        self.assertTrue(view.get_survey_queryset(self.user).exists())

    def test_get_survey_queryset_grantee_other(self):
        view = self.view()
        user = UserFactory.create()
        self.assertFalse(view.get_survey_queryset(user).exists())

    def test_get_survey_queryset_grator(self):
        view = self.view()
        self.create_grantor()
        self.assertTrue(view.get_survey_queryset(self.grantor_user).exists())

    def test_get_survey_queryset_grator_response_not_submitted(self):
        view = self.view()

        grantor_user = UserFactory.create()
        InvitationFactory.create(
            survey=self.survey,
            grantee=self.survey_response.organisation,
            accepted=True,
            grantor=grantor_user.organisation
        )

        self.assertFalse(view.get_survey_queryset(grantor_user).exists())

    def test_get_survey_queryset_grator_invitation_not_accepted(self):
        view = self.view()

        grantor_user = UserFactory.create()
        InvitationFactory.create(
            survey=self.survey,
            grantee=self.survey_response.organisation,
            accepted=False,
            grantor=grantor_user.organisation
        )
        self.survey_response.submitted = timezone.now()
        self.survey_response.save()

        self.assertFalse(view.get_survey_queryset(grantor_user).exists())

    def test_get_survey_queryset_grator_other_survey(self):
        view = self.view()

        grantor_user = UserFactory.create()
        InvitationFactory.create(
            grantee=self.survey_response.organisation,
            accepted=True,
            grantor=grantor_user.organisation
        )
        self.survey_response.submitted = timezone.now()
        self.survey_response.save()

        self.assertFalse(view.get_survey_queryset(grantor_user).exists())

    def test_get_survey_queryset_grator_other_grantee(self):
        view = self.view()

        grantor_user = UserFactory.create()
        InvitationFactory.create(
            survey=self.survey,
            accepted=False,
            grantor=grantor_user.organisation
        )
        self.survey_response.submitted = timezone.now()
        self.survey_response.save()

        self.assertFalse(view.get_survey_queryset(grantor_user).exists())

    def test_is_owner(self):
        self.create_grantor()
        view = self.view()
        view.request = self.create_request(user=self.user)
        view.survey_response = self.survey_response
        self.assertTrue(view.is_owner())

    def test_is_owner_grantor(self):
        self.create_grantor()
        view = self.view()
        view.request = self.create_request(user=self.grantor_user)
        view.survey_response = self.survey_response
        self.assertFalse(view.is_owner())

    def test_get_template_names_grantee(self):
        self.create_grantor()
        view = self.view()
        view.request = self.create_request(user=self.user)
        view.survey_response = self.survey_response
        self.assertEqual(view.get_template_names(), [view.grantee_template_name])

    def test_get_template_names_grantor(self):
        self.create_grantor()
        view = self.view()
        view.request = self.create_request(user=self.grantor_user)
        view.survey_response = self.survey_response
        self.assertEqual(view.get_template_names(), [view.grantor_template_name])

    def test_get(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        response = view(request, pk=self.survey_response.pk)
        self.assertEqual(response.status_code, 200)

    def test_get_grantor_without_active_subscription(self):
        self.create_grantor()
        view = self.view.as_view()
        assign_role(self.grantor_user, 'admin')
        request = self.create_request(user=self.grantor_user)
        response = view(request, pk=self.survey_response.pk)
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('subscription')
        self.assertEqual(response.url, expected_url)
        expected_message = (
            "No active subscription. Your organization needs "
            "an active subscription to view the report"
        )
        self.assertEqual(request._messages.store[0], expected_message)

    def test_get_grantor_with_active_subscription(self):
        self.create_grantor()
        assign_role(self.grantor_user, 'admin')
        SubscriptionFactory.create(
            order__organisation=self.grantor_user.organisation,
            order__status=Order.STATUS_APPROVED
        )
        view = self.view.as_view()
        request = self.create_request(user=self.grantor_user)
        response = view(request, pk=self.survey_response.pk)
        self.assertEqual(response.status_code, 200)

    def test_get_grantor_manager_without_active_subscription(self):
        self.create_grantor()
        view = self.view.as_view()
        assign_role(self.grantor_user, 'manager')
        request = self.create_request(user=self.grantor_user)
        response = view(request, pk=self.survey_response.pk)
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('home')
        self.assertEqual(response.url, expected_url)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request, pk=self.survey_response.pk)
        self.assertRedirectToLogin(response)

    def test_get_other(self):
        view = self.view.as_view()
        request = self.create_request()
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            level=1,
        )
        self.assertNotEqual(request.user.organisation, survey_response.organisation)
        with self.assertRaises(Http404):
            view(request, pk=survey_response.pk)

    def test_get_context_data(self):
        # This question should not be included.
        other = SurveyQuestionFactory.create(
            survey=self.survey,
            level=2,
            section=self.section
        )
        SurveyAnswerFactory.create(
            response=self.survey_response,
            question=other,
        )
        view = self.view()
        view.survey = self.survey
        view.level = 1
        view.object = self.survey_response
        view.request = self.create_request()
        context = view.get_context_data()

        expected = self.survey_response.get_level_compliance()
        compliance = expected['compliance']
        compliance['sections'][0]['questions'] = [self.question]

        self.assertEqual(context['progress'], expected['progress'])
        self.assertEqual(context['compliance'], compliance)
        self.assertEqual(len(context['compliance']['sections']), 1)
        step = context['compliance']['sections'][0]
        self.assertSequenceEqual(step['questions'], [self.question])
        question = step['questions'][0]
        self.assertEqual(question.answer, self.answer)

    def test_get_num_queries(self):
        other = SurveyAnswerFactory.create(
            response=self.survey_response,
        )
        options = SurveyQuestionOptionFactory.create_batch(
            3,
            question=other.question,
        )
        other.options.add(*options[:2])
        SurveyAnswerDocumentFactory.create_batch(
            3,
            answer=other,
        )

        view = self.view.as_view()
        request = self.create_request(user=self.user)

        """
        SELECT DISTINCT
          FROM "surveys_surveyresponse"
         INNER
          JOIN "surveys_survey"
            ON ("surveys_surveyresponse"."survey_id" =  "surveys_survey"."id")
         INNER
          JOIN "surveys_surveyquestion"
            ON ("surveys_survey"."id" =  "surveys_surveyquestion"."survey_id")
         WHERE (
                   "surveys_surveyquestion"."id" IS NOT NULL
               AND "surveys_surveyresponse"."organisation_id" =  831
           AND "surveys_surveyresponse"."id" =  438
               )
        SELECT "auth_group"."id", "auth_group"."name"
          FROM "auth_group"
         INNER
          JOIN "users_user_groups"
           ON ("auth_group"."id" = "users_user_groups"."group_id")
         WHERE (
                    "users_user_groups"."user_id" = 5047
                AND "auth_group"."name" IN ('user', 'manager', 'admin')
                )
          ORDER BY "auth_group"."name" ASC

        SELECT DISTINCT
          FROM "surveys_surveysection"
         INNER
          JOIN "surveys_surveyquestion"
            ON ("surveys_surveysection"."id" =  "surveys_surveyquestion"."section_id")
         INNER
          JOIN "surveys_surveyarea"
            ON ("surveys_surveysection"."area_id" =  "surveys_surveyarea"."id")
         WHERE "surveys_surveyquestion"."survey_id" =  388
         ORDER BY "surveys_surveyarea"."number" ASC, "surveys_surveysection"."number" ASC
        SELECT COUNT("surveys_surveyquestion"."id") AS "total",
            SUM(
                CASE WHEN "surveys_surveyquestion"."section_id" =  622 THEN 1 ELSE 0 END
            ) AS "622"
          FROM "surveys_surveyquestion"
         WHERE (
                   "surveys_surveyquestion"."survey_id" =  388
           AND "surveys_surveyquestion"."level" <=  1
               )
        SELECT COUNT("surveys_surveyanswer"."id") AS "total",
            SUM(
                   CASE WHEN (
                       "surveys_surveyanswer"."value" =  'yes'
               AND "surveys_surveyquestion"."section_id" =  622
               ) THEN 1 ELSE 0 END
            ) AS "622",
            SUM(
                CASE WHEN "surveys_surveyanswer"."value" =  'yes' THEN 1 ELSE 0 END
            ) AS "compliance_total"
          FROM "surveys_surveyanswer"
         INNER
          JOIN "surveys_surveyquestion"
            ON ("surveys_surveyanswer"."question_id" =  "surveys_surveyquestion"."id")
         WHERE (
                   "surveys_surveyanswer"."response_id" =  438
           AND "surveys_surveyquestion"."level" <=  1
               )
        SELECT
          FROM "surveys_surveyanswer"
         INNER
          JOIN "surveys_surveyquestion"
            ON ("surveys_surveyanswer"."question_id" =  "surveys_surveyquestion"."id")
         WHERE (
                   "surveys_surveyquestion"."level" <=  1
           AND "surveys_surveyanswer"."response_id" =  438
               )
        SELECT
          FROM "surveys_surveyquestionoption"
         INNER
          JOIN "surveys_surveyanswer_options"
            ON
         WHERE "surveys_surveyanswer_options"."surveyanswer_id" IN (272, 273)
         ORDER BY "surveys_surveyquestionoption"."sort_order" ASC
        SELECT
          FROM "surveys_surveyanswerdocument"
         INNER
          JOIN "documents_document"
            ON ("surveys_surveyanswerdocument"."document_id" =  "documents_document"."id")
         WHERE "surveys_surveyanswerdocument"."answer_id" IN (272, 273)
        SELECT
          FROM "surveys_surveyquestion"
         INNER
          JOIN "surveys_surveysection"
            ON ("surveys_surveyquestion"."section_id" =  "surveys_surveysection"."id")
         INNER
          JOIN "surveys_surveyarea"
            ON ("surveys_surveysection"."area_id" =  "surveys_surveyarea"."id")
         WHERE (
                   "surveys_surveyquestion"."survey_id" =  388
           AND "surveys_surveyquestion"."level" <=  1
               )
         ORDER BY
        SELECT
          FROM "surveys_surveyquestionoption"
         WHERE "surveys_surveyquestionoption"."question_id" IN (704)
         ORDER BY "surveys_surveyquestionoption"."sort_order" ASC
        SELECT
          FROM "page_page"
         WHERE (
                   "page_page"."active" =  true
           AND "page_page"."_cached_url" IN ('/')
               )
         ORDER BY "_url_length" DESC LIMIT 1
        SELECT
            FROM "subscriptions_subscription"
        INNER JOIN "subscriptions_order"
        ON ("subscriptions_subscription"."order_id" = "subscriptions_order"."id")
        WHERE ("subscriptions_order"."organisation_id" = 167911
        AND NOT ("subscriptions_order"."status" = 'canceled'))
        ORDER BY "subscriptions_subscription"."start_date" DESC LIMIT 1
        """
        with self.assertNumQueries(12):
            response = view(request, pk=self.survey_response.pk)
            response.render()
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        survey_response = self.survey_response
        view = self.view.as_view()
        data = {'level': 2}

        self.assertNotEqual(survey_response.level, data['level'])

        request = self.create_request('post', user=self.user, data=data)
        response = view(request, pk=survey_response.pk)

        expected_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, expected_url)

        survey_response.refresh_from_db()
        self.assertEqual(survey_response.level, data['level'])

    def test_post_grantor(self):
        self.create_grantor()
        survey_response = self.survey_response
        view = self.view.as_view()
        data = {'level': 2}
        request = self.create_request('post', user=self.grantor_user, data=data)
        response = view(request, pk=survey_response.pk)
        self.assertEqual(response.status_code, 405)


class TestSurveyReportSubmit(RequestTestCase):
    view = views.SurveyFullReport

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        cls.survey = SurveyFactory.create()
        cls.question = SurveyQuestionFactory.create(survey=cls.survey)
        cls.survey_response = SurveyResponseFactory.create(
            organisation=cls.user.organisation,
            survey=cls.survey,
        )
        cls.submit_url = reverse('survey-submit', kwargs={'pk': cls.survey_response.pk})

    def test_not_complete(self):
        request = self.create_request(user=self.user)
        view = self.view.as_view()
        response = view(request, pk=self.survey_response.pk)
        self.assertNotContains(response, self.submit_url)

    def test_complete(self):
        SurveyAnswerFactory.create(
            response=self.survey_response,
            question=self.question,
        )
        request = self.create_request(user=self.user)
        view = self.view.as_view()
        response = view(request, pk=self.survey_response.pk)
        self.assertContains(response, self.submit_url)

    def test_report_submited(self):
        SurveyAnswerFactory.create(
            response=self.survey_response,
            question=self.question,
        )
        self.survey_response.submitted = timezone.now()
        self.survey_response.save()

        request = self.create_request(user=self.user)
        view = self.view.as_view()
        response = view(request, pk=self.survey_response.pk)
        self.assertNotContains(response, self.submit_url)


class TestSubmitSurveyResponse(AnonymouseTestMixin, RequestTestCase):
    view = views.SubmitSurveyResponse

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        cls.survey = SurveyFactory.create()
        SurveyQuestionFactory.create(survey=cls.survey)

    def setUp(self):
        super().setUp()
        self.survey_response = SurveyResponseFactory.create(
            organisation=self.user.organisation,
            survey=self.survey,
            level=1,
            submitted=None,
        )

    def test_get(self):
        view = self.view.as_view()

        request = self.create_request_ajax(user=self.user)
        response = view(request, pk=self.survey_response.pk)
        self.assertEqual(response.status_code, 200)

    def test_get_other(self):
        view = self.view.as_view()

        request = self.create_request_ajax()
        with self.assertRaises(Http404):
            view(request, pk=self.survey_response.pk)

    def test_get_submitted(self):
        self.survey_response.submitted = timezone.now()
        self.survey_response.save()

        view = self.view.as_view()
        request = self.create_request_ajax(user=self.user)
        with self.assertRaises(Http404):
            view(request, pk=self.survey_response.pk)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request, pk=1)
        self.assertRedirectToLogin(response)

    def test_get_not_ajax(self):
        view = self.view.as_view()

        request = self.create_request(user=self.user)
        with self.assertRaises(Http404):
            view(request, pk=self.survey_response.pk)

    def test_post(self):
        now = timezone.now()

        view = self.view.as_view()

        data = {}
        request = self.create_request('post', user=self.user, data=data)

        self.assertIsNone(self.survey_response.submitted)

        with patch('django.utils.timezone.now') as now_mock:
            now_mock.return_value = now
            response = view(request, pk=self.survey_response.pk)

        report_url = reverse('survey-report', kwargs={'pk': self.survey_response.pk})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, report_url)

        self.assertEqual(
            request._messages.store[0],
            'Assessment published successfully',
        )

        self.survey_response.refresh_from_db()
        self.assertEqual(self.survey_response.submitted, now)

    def test_post_with_invitation(self):
        invitation = InvitationFactory.create(
            survey=self.survey,
            grantee=self.user.organisation,
        )
        self.assertNotEqual(invitation.status, invitation.INVITATION_SUBMITTED)
        view = self.view.as_view()
        request = self.create_request('post', user=self.user, data={})
        response = view(request, pk=self.survey_response.pk)

        invitation.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(invitation.status, invitation.INVITATION_SUBMITTED)

    def test_get_object(self):
        view = self.view()
        view.survey_response = self.survey_response

        object = view.get_object()
        self.assertEqual(object, self.survey_response)


class TestInviteListView(AnonymouseTestMixin, RequestTestCase):
    view = views.InviteListView

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()
        SurveyQuestionFactory.create(survey=cls.survey)

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()

    def test_get_admin(self):
        view = self.view.as_view()
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_manager(self):
        view = self.view.as_view()
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_user(self):
        view = self.view.as_view()
        assign_role(self.user, 'user')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_get_not_authorised(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertRedirectToLogin(response)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request)
        self.assertRedirectToLogin(response)

    def test_report_url_without_subscription(self):
        "Response should not contain the report url"
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )
        InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=survey_response.organisation,
            survey=self.survey,
            accepted=True,
        )
        view = self.view.as_view()
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        report_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertNotContains(response, report_url)

    def test_report_url_with_active_subscription(self):
        "Response should contain the report url"
        SubscriptionFactory.create(
            order__organisation=self.user.organisation,
            order__status=Order.STATUS_APPROVED
        )
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )
        InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=survey_response.organisation,
            survey=self.survey,
            accepted=True,
        )
        view = self.view.as_view()
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        report_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertContains(response, report_url)

    def test_report_url_not_accepted(self):
        "Response should not contain the report url if the invitation is not accepted"
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )
        InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=survey_response.organisation,
            survey=self.survey,
            accepted=False,
        )
        view = self.view.as_view()
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        report_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertNotContains(response, report_url)

    def test_report_url_not_submited(self):
        "Response should not contain the report url if the response is not submitted"
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=None,
        )
        InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=survey_response.organisation,
            survey=self.survey,
            accepted=True,
        )
        view = self.view.as_view()
        assign_role(self.user, 'manager')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        report_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertNotContains(response, report_url)

    def test_get_pending_invites_count(self):
        view = self.view()
        assign_role(self.user, 'admin')
        # Included
        InvitationFactory.create(
            grantee=self.user.organisation,
            accepted=False,
        )
        # Not pending
        InvitationFactory.create(
            grantee=self.user.organisation,
            accepted=True,
        )
        # Different grantee
        InvitationFactory.create(
            accepted=True,
        )

        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        self.assertEqual(context['pending_invites_count'], 1)

    def test_get_received_invites(self):
        view = self.view()
        assign_role(self.user, 'admin')
        invite = InvitationFactory.create(
            grantee=self.user.organisation,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        invites = context['received_invites']
        self.assertSequenceEqual(invites, [invite])

    def test_get_sent_invites(self):
        view = self.view()
        assign_role(self.user, 'admin')
        invite = InvitationFactory.create(
            grantor=self.user.organisation,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        invites = context['sent_invites']
        self.assertSequenceEqual(invites, [invite])

    def test_get_sent_invites_response_id(self):
        view = self.view()
        assign_role(self.user, 'admin')
        response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )
        invite = InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=response.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        invites = context['sent_invites']
        self.assertSequenceEqual(invites, [invite])
        self.assertEqual(invites[0].response_id, response.pk)

    def test_sent_invites_pagination(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create_batch(
            12,
            grantor=self.user.organisation,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        is_paginated = context['is_paginated']
        page_range = context['page_range']
        self.assertEqual(is_paginated, True)
        self.assertEqual(page_range, range(1, 3))
        self.assertEqual(context['page_obj'].number, 1)

    def test_sent_invites_pagination_not_found(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create(
            grantor=self.user.organisation,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 3}
        view.object_list = view.get_queryset()
        with self.assertRaises(Http404):
            view.get_context_data()

    def test_sent_invites_no_pagination(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create(
            grantor=self.user.organisation,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        is_paginated = context['is_paginated']
        self.assertEqual(is_paginated, False)


class TestCreateInviteView(AnonymouseTestMixin, RequestTestCase):
    view = views.CreateInviteView

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()
        SurveyQuestionFactory.create(survey=cls.survey)

    def test_get_not_authorised(self):
        user = UserFactory.create()
        view = self.view.as_view()
        request = self.create_request(user=user)
        response = view(request)
        self.assertRedirectToLogin(response)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request)
        self.assertRedirectToLogin(response)

    def test_get_admin_without_active_subscription(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        response = view(request)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('subscription')
        self.assertEqual(response.url, expected_url)
        expected_message = (
            "No active subscription. Your organization needs "
            "an active subscription to make an invitations"
        )
        self.assertEqual(request._messages.store[0], expected_message)

    def test_get_admin_with_active_subscription_no_invites(self):
        view = self.view.as_view()
        organisation = OrganisationFactory.create()
        user = UserFactory.create(organisation=organisation)
        SubscriptionFactory.create(
            order__organisation=organisation,
            order__status=Order.STATUS_APPROVED
        )
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('subscription')
        self.assertEqual(response.url, expected_url)
        expected_message = (
            "No invitations available. Your organization needs "
            "to purchase more invitations."
        )
        self.assertEqual(request._messages.store[0], expected_message)

    def test_get_admin_with_active_subscription_with_invites(self):
        view = self.view.as_view()
        organisation = OrganisationFactory.create()
        user = UserFactory.create(organisation=organisation)
        SubscriptionFactory.create(
            order__organisation=organisation,
            order__status=Order.STATUS_APPROVED
        )
        AssessmentPurchaseFactory.create(
            order__organisation=organisation,
            order__status=Order.STATUS_APPROVED,
            number_included=10,
            price=900.00,
        )
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_manager_without_active_subscription(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'manager')
        request = self.create_request(user=user)
        response = view(request)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('home')
        self.assertEqual(response.url, expected_url)
        expected_message = (
            "No active subscription. Your organization needs "
            "an active subscription to make an invitations"
        )
        self.assertEqual(request._messages.store[0], expected_message)

    def test_get_manager_with_active_subscription_no_invites(self):
        view = self.view.as_view()
        organisation = OrganisationFactory.create()
        user = UserFactory.create(organisation=organisation)
        SubscriptionFactory.create(
            order__organisation=organisation,
            order__status=Order.STATUS_APPROVED
        )
        assign_role(user, 'manager')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('home')
        self.assertEqual(response.url, expected_url)
        expected_message = (
            "No invitations available. Your organization needs "
            "to purchase more invitations."
        )
        self.assertEqual(request._messages.store[0], expected_message)

    def test_get_user(self):
        view = self.view.as_view()
        user = UserFactory.create()
        assign_role(user, 'user')
        request = self.create_request(user=user)
        response = view(request)
        self.assertEqual(response.status_code, 302)

    def test_post_with_email_without_active_subscription(self):
        user = UserFactory.create()
        assign_role(user, 'admin')
        grantee_admin = UserFactory.create()
        assign_role(grantee_admin, 'admin')

        data = {
            'grantee_email': 'abc@mail.com',
            'grantee': '',
            'survey': self.survey.pk,
            'level': 1,
            'is_organisation_invite': False
        }
        view = self.view.as_view()
        request = self.create_request('post', user=user, data=data)
        response = view(request)
        errors = response.context_data['form'].errors
        expected_message = (
            "No active subscription. Your organization needs "
            "an active subscription to make an invitations"
        )
        self.assertIn('grantee_email', errors)
        self.assertEqual(expected_message, errors['grantee_email'][0])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request._messages.store[0],
            'Invitation failed, please correct the form',
        )

    def test_post_with_email_with_active_subscription_no_invites(self):
        user = UserFactory.create()
        assign_role(user, 'admin')
        grantor = user.organisation
        grantee_admin = UserFactory.create()
        assign_role(grantee_admin, 'admin')
        SubscriptionFactory.create(
            order__organisation=grantor,
            order__status=Order.STATUS_APPROVED
        )
        data = {
            'grantee_email': 'abc@mail.com',
            'grantee': '',
            'survey': self.survey.pk,
            'level': 1,
            'is_organisation_invite': False
        }
        view = self.view.as_view()
        request = self.create_request('post', user=user, data=data)
        response = view(request)
        errors = response.context_data['form'].errors
        expected_message = (
            "No invitations available. Your organization needs "
            "to purchase more invitations."
        )
        self.assertIn('grantee_email', errors)
        self.assertEqual(expected_message, errors['grantee_email'][0])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request._messages.store[0],
            'Invitation failed, please correct the form',
        )

    def test_post_with_email_with_active_subscription_with_invites(self):
        """User can only create invites with active subscription and with purchase"""
        user = UserFactory.create()
        assign_role(user, 'admin')
        grantor = user.organisation
        grantee_admin = UserFactory.create()
        assign_role(grantee_admin, 'admin')

        SubscriptionFactory.create(
            order__organisation=grantor,
            order__status=Order.STATUS_APPROVED
        )
        AssessmentPurchaseFactory.create(
            order__organisation=grantor,
            order__status=Order.STATUS_APPROVED,
            number_included=10,
            price=900.00,
        )

        data = {
            'grantee_email': 'abc@mail.com',
            'grantee': '',
            'survey': self.survey.pk,
            'level': 1,
            'is_organisation_invite': False
        }
        view = self.view.as_view()
        request = self.create_request('post', user=user, data=data)
        response = view(request)
        self.assertEqual(response.status_code, 302)

        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)
        invitation = Invitation.objects.get(grantee_email=data['grantee_email'])

        self.assertIsNone(invitation.grantee)
        self.assertEqual(invitation.grantor, grantor)
        self.assertEqual(invitation.survey, self.survey)
        self.assertEqual(invitation.level, 1)

    def test_post_with_organisation_without_active_subscription(self):
        user = UserFactory.create()
        assign_role(user, 'admin')

        grantee_admin = UserFactory.create()
        assign_role(grantee_admin, 'admin')
        user.organisation
        grantee = grantee_admin.organisation

        data = {
            'grantee_email': '',
            'grantee': grantee.pk,
            'survey': self.survey.pk,
            'level': 1,
            'is_organisation_invite': True
        }
        view = self.view.as_view()
        request = self.create_request('post', user=user, data=data)
        response = view(request)
        errors = response.context_data['form'].errors
        expected_message = (
            "No active subscription. Your organization needs "
            "an active subscription to make an invitations"
        )
        self.assertIn('grantee', errors)
        self.assertEqual(expected_message, errors['grantee'][0])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request._messages.store[0],
            'Invitation failed, please correct the form',
        )

    def test_post_with_organisation_with_active_subscription_no_invites(self):
        user = UserFactory.create()
        assign_role(user, 'admin')

        grantee_admin = UserFactory.create()
        assign_role(grantee_admin, 'admin')

        grantor = user.organisation
        grantee = grantee_admin.organisation
        SubscriptionFactory.create(
            order__organisation=grantor,
            order__status=Order.STATUS_APPROVED
        )
        data = {
            'grantee_email': '',
            'grantee': grantee.pk,
            'survey': self.survey.pk,
            'level': 1,
            'is_organisation_invite': True
        }
        view = self.view.as_view()
        request = self.create_request('post', user=user, data=data)
        response = view(request)
        errors = response.context_data['form'].errors
        expected_message = (
            "No invitations available. Your organization needs "
            "to purchase more invitations."
        )
        self.assertIn('grantee', errors)
        self.assertEqual(expected_message, errors['grantee'][0])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request._messages.store[0],
            'Invitation failed, please correct the form',
        )

    def test_post_with_organisation_with_active_subscription_with_invites(self):
        """User can only create invites with active subscription and with purchase"""
        user = UserFactory.create()
        assign_role(user, 'admin')

        grantee_admin = UserFactory.create()
        assign_role(grantee_admin, 'admin')

        grantor = user.organisation
        grantee = grantee_admin.organisation
        SubscriptionFactory.create(
            order__organisation=grantor,
            order__status=Order.STATUS_APPROVED
        )
        AssessmentPurchaseFactory.create(
            order__organisation=grantor,
            order__status=Order.STATUS_APPROVED,
            number_included=10,
            price=900.00,
        )
        data = {
            'grantee_email': '',
            'grantee': grantee.pk,
            'survey': self.survey.pk,
            'level': 1,
            'is_organisation_invite': True
        }
        view = self.view.as_view()
        request = self.create_request('post', user=user, data=data)
        response = view(request)
        self.assertEqual(response.status_code, 302)

        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)

        invitation = Invitation.objects.get(grantee=grantee)
        self.assertEqual(invitation.grantor, grantor)
        self.assertEqual(invitation.survey, self.survey)
        self.assertEqual(invitation.level, 1)

        self.assertEqual(len(mail.outbox), 1)
        subject = 'Invitation to submit assessment'
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(grantee_admin.email, mail.outbox[0].to)

    def test_post_with_organisation_due_date(self):
        user = UserFactory.create()
        assign_role(user, 'admin')

        grantee_admin = UserFactory.create()
        assign_role(grantee_admin, 'admin')

        grantor = user.organisation
        grantee = grantee_admin.organisation
        SubscriptionFactory.create(
            order__organisation=grantor,
            order__status=Order.STATUS_APPROVED
        )
        AssessmentPurchaseFactory.create(
            order__organisation=grantor,
            order__status=Order.STATUS_APPROVED,
            number_included=10,
            price=900.00,
        )

        data = {
            'grantee_email': '',
            'grantee': grantee.pk,
            'survey': self.survey.pk,
            'level': 1,
            'is_organisation_invite': True,
            'due_date': date(2020, 1, 14)
        }
        view = self.view.as_view()
        request = self.create_request('post', user=user, data=data)
        response = view(request)
        self.assertEqual(response.status_code, 302)

        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)

        invitation = Invitation.objects.get(grantee=grantee)
        self.assertEqual(invitation.grantor, grantor)
        self.assertEqual(invitation.survey, self.survey)
        self.assertEqual(invitation.level, 1)
        self.assertEqual(invitation.due_date,  date(2020, 1, 14))

        self.assertEqual(len(mail.outbox), 1)
        subject = 'Invitation to submit assessment'
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertIn(grantee_admin.email, mail.outbox[0].to)

    def test_post_error(self):
        user = UserFactory.create()
        assign_role(user, 'admin')

        grantee_admin = UserFactory.create()
        assign_role(grantee_admin, 'admin')

        grantee = grantee_admin.organisation
        data = {
            'grantee': grantee.pk,
            'survey': self.survey.pk,
            'grantee_email': '',
        }

        view = self.view.as_view()
        request = self.create_request('post', user=user, data=data)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            request._messages.store[0],
            'Invitation failed, please correct the form',
        )


class TestInviteAcceptView(AnonymouseTestMixin, RequestTestCase):
    view = views.InviteAcceptView

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()
        cls.invite = InvitationFactory.create(accepted=False, survey=cls.survey)
        SurveyQuestionFactory.create(survey=cls.invite.survey)

    def test_get_not_authorised(self):
        user = UserFactory.create(organisation=self.invite.grantee)
        view = self.view.as_view()
        request = self.create_request_ajax(user=user)
        response = view(request, pk=self.invite.pk)
        self.assertRedirectToLogin(response)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request_ajax(auth=False)
        response = view(request, pk=self.invite.pk)
        self.assertRedirectToLogin(response)

    def test_get_not_ajax(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        with self.assertRaises(Http404):
            view(request, pk=self.invite.pk)

    def test_get_admin(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'admin')
        request = self.create_request_ajax(user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 200)

        self.invite.refresh_from_db()
        self.assertFalse(self.invite.accepted)

    def test_get_manager(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'manager')
        request = self.create_request_ajax(user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 200)

        self.invite.refresh_from_db()
        self.assertFalse(self.invite.accepted)

    def test_get_user(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'user')
        request = self.create_request_ajax(user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)

        self.invite.refresh_from_db()
        self.assertFalse(self.invite.accepted)

    def test_post_admin(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'admin')
        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)

        self.invite.refresh_from_db()
        self.assertTrue(self.invite.accepted)

    def test_post_manager(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'manager')
        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)

        self.invite.refresh_from_db()
        self.assertTrue(self.invite.accepted)

    def test_post_user(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'user')
        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)

        self.invite.refresh_from_db()
        self.assertFalse(self.invite.accepted)

    def test_post_pending_submission(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'admin')
        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)

        self.invite.refresh_from_db()
        self.assertTrue(self.invite.accepted)
        self.assertEqual(self.invite.status, self.invite.INVITATION_PENDING)

    def test_post_submitted(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'admin')

        SurveyResponseFactory.create(
            organisation=user.organisation,
            survey=self.survey,
            submitted=timezone.now(),
        )

        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)

        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, self.invite.INVITATION_SUBMITTED)

    def test_post_submitted_other(self):
        "Other organisation's submitted responses should not change the status"
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'admin')

        SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )

        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)

        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, self.invite.INVITATION_PENDING)


class TestResendInviteView(AnonymouseTestMixin, RequestTestCase):
    view = views.ResendInviteView

    @classmethod
    def setUpTestData(cls):
        cls.invite = InvitationFactory.create(accepted=True)
        SurveyQuestionFactory.create(survey=cls.invite.survey)

    def test_get_not_authorised(self):
        user = UserFactory.create(organisation=self.invite.grantee)
        view = self.view.as_view()
        request = self.create_request_ajax(user=user)
        response = view(request, pk=self.invite.pk)
        self.assertRedirectToLogin(response)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request_ajax(auth=False)
        response = view(request, pk=self.invite.pk)
        self.assertRedirectToLogin(response)

    def test_get_not_ajax(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'admin')
        request = self.create_request(user=user)
        response = view(request, pk=self.invite.pk)
        self.assertEqual(response.status_code, 405)

    def test_post_admin(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'admin')
        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)
        last_sent = self.invite.last_sent

        self.assertEqual(len(mail.outbox), 1)
        self.invite.refresh_from_db()
        self.assertTrue(self.invite.last_sent > last_sent)

    def test_post_manager(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'manager')
        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse('survey-invite')
        self.assertEqual(response.url, expected_url)

    def test_post_user(self):
        view = self.view.as_view()
        user = UserFactory.create(organisation=self.invite.grantee)
        assign_role(user, 'user')
        request = self.create_request_ajax('post', user=user)
        response = view(request, pk=self.invite.pk)

        self.assertEqual(response.status_code, 302)
        expected_url = '/login/?next=/'
        self.assertEqual(response.url, expected_url)


class TestViewAssessmentList(AnonymouseTestMixin, RequestTestCase):
    view = views.ViewAssessmentList

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.survey = SurveyFactory.create()

    def test_get_not_authorised(self):
        view = self.view.as_view()
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertRedirectToLogin(response)

    def test_get(self):
        view = self.view.as_view()
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_grantor_report_url_accepted_without_active_subscription(self):
        "Response should not contain the report url"
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )
        InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=survey_response.organisation,
            survey=self.survey,
            accepted=True,
        )
        view = self.view.as_view()
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        report_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertNotContains(response, report_url)

    def test_grantor_report_url_accepted_with_active_subscription(self):
        "Response should contain the report url"
        SubscriptionFactory.create(
            order__organisation=self.user.organisation,
            order__status=Order.STATUS_APPROVED
        )
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )
        InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=survey_response.organisation,
            survey=self.survey,
            accepted=True,
        )
        view = self.view.as_view()
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        report_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertContains(response, report_url)

    def test_grantor_report_url_not_accepted(self):
        "Response should not contain the report url if the invitation is not accepted"
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )
        InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=survey_response.organisation,
            survey=self.survey,
            accepted=False,
        )
        view = self.view.as_view()
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        report_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertNotContains(response, report_url)

    def test_grantor_report_url_not_submited(self):
        "Response should not contain the report url if the response is not submitted"
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=None,
        )
        InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=survey_response.organisation,
            survey=self.survey,
            accepted=True,
        )
        view = self.view.as_view()
        assign_role(self.user, 'admin')
        request = self.create_request(user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)
        report_url = reverse('survey-report', kwargs={'pk': survey_response.pk})
        self.assertNotContains(response, report_url)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request(auth=False)
        response = view(request)
        self.assertRedirectToLogin(response)

    def test_get_no_shared_with_me(self):
        view = self.view()
        assign_role(self.user, 'admin')
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        invites = context['shared_with_me']
        self.assertEqual(len(invites), 0)

    def test_get_shared_with_me_not_accepted(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create(
            grantor=self.user.organisation,
            survey=self.survey
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        invites = context['shared_with_me']
        self.assertEqual(len(invites), 0)

    def test_get_shared_with_me_accepted(self):
        view = self.view()
        assign_role(self.user, 'admin')
        invite = InvitationFactory.create(
            grantor=self.user.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        invites = context['shared_with_me']
        self.assertSequenceEqual(invites, [invite])

    def test_get_no_shared_with_me_response_id(self):
        view = self.view()
        assign_role(self.user, 'admin')
        response = SurveyResponseFactory.create(
            survey=self.survey,
            submitted=timezone.now(),
        )
        invite = InvitationFactory.create(
            grantor=self.user.organisation,
            grantee=response.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        invites = context['shared_with_me']
        self.assertSequenceEqual(invites, [invite])
        self.assertEqual(invites[0].response_id, response.pk)

    def test_get_survey_inactive(self):
        SurveyFactory.create(is_active=False)
        view = self.view()
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        surveys = list(context['surveys'])
        self.assertSequenceEqual(surveys, [self.survey])

    def test_get_no_survey(self):
        self.survey.delete()

        view = self.view()
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        surveys = list(context['surveys'])
        self.assertSequenceEqual(surveys, [])

    def test_get_survey_without_survey_response(self):
        view = self.view()
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        surveys = list(context['surveys'])
        self.assertSequenceEqual(surveys, [self.survey])
        self.assertIsNone(surveys[0].survey_response)

    def test_get_survey_with_survey_response(self):
        view = self.view()

        SurveyQuestionFactory.create(survey=self.survey)
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            organisation=self.user.organisation,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        survey = list(context['surveys'])[0]
        self.assertEqual(survey.survey_response, survey_response)

    def test_get_survey_with_invite_accepted(self):
        view = self.view()

        invitation = InvitationFactory.create(
            survey=self.survey,
            grantee=self.user.organisation,
            accepted=True,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        survey = list(context['surveys'])[0]
        self.assertEqual(survey.invites, [invitation])

    def test_get_survey_with_invite_not_accepted(self):
        view = self.view()

        InvitationFactory.create(
            survey=self.survey,
            grantee=self.user.organisation,
            accepted=False,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        survey = list(context['surveys'])[0]
        self.assertEqual(survey.invites, [])

    def test_get_survey_with_invite_other(self):
        view = self.view()

        InvitationFactory.create(
            survey=self.survey,
            accepted=True,
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        survey = list(context['surveys'])[0]
        self.assertEqual(survey.invites, [])

    def test_get_survey_with_multiple_survey_response(self):
        view = self.view()

        SurveyQuestionFactory.create(survey=self.survey)
        survey_response = SurveyResponseFactory.create(
            survey=self.survey,
            organisation=self.user.organisation,
        )
        other = SurveyResponseFactory.create(
            survey=self.survey,
            organisation=self.user.organisation,
        )

        # Update modified date
        survey_response.save()
        self.assertTrue(survey_response.modified > other.modified)

        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        surveys = list(context['surveys'])
        self.assertEqual(surveys[0].survey_response, survey_response)

    def test_shared_with_me_pagination(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create_batch(
            14,
            grantor=self.user.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        is_paginated = context['is_paginated']
        page_range = context['page_range']
        self.assertEqual(is_paginated, True)
        self.assertEqual(page_range, range(1, 3))
        self.assertEqual(context['page_obj'].number, 1)

    def test_shared_with_me_no_pagination(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create(
            grantor=self.user.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        is_paginated = context['is_paginated']
        self.assertEqual(is_paginated, False)

    def test_shared_with_me_pagination_not_found(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create(
            grantor=self.user.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 3}
        view.object_list = view.get_queryset()
        with self.assertRaises(Http404):
            view.get_context_data()

    def test_shared_with_pagination_limit_factor_2(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create(
            grantor=self.user.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 1}
        view.page_limit = 10
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        is_paginated = context['is_paginated']
        self.assertEqual(is_paginated, False)

    def test_shared_with_pagination_greater_than_right(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create_batch(
            140,
            grantor=self.user.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 11}
        view.page_limit = 10
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        is_paginated = context['is_paginated']
        self.assertEqual(is_paginated, True)

    def test_shared_with_pagination_between_left_right(self):
        view = self.view()
        assign_role(self.user, 'admin')
        InvitationFactory.create_batch(
            300,
            grantor=self.user.organisation,
            survey=self.survey,
            accepted=True
        )
        view.request = self.create_request(user=self.user)
        view.kwargs = {'page': 11}
        view.page_limit = 10
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        is_paginated = context['is_paginated']
        self.assertEqual(is_paginated, True)
