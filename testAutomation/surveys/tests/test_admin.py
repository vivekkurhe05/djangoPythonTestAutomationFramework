from unittest.mock import MagicMock, patch

from core.tests.utils import RequestTestCase

from .factories import SurveyAnswerFactory, SurveyQuestionFactory

from ..admin import (
    SurveyAdmin,
    SurveyAnswerAdmin,
    SurveyQuestionAdmin,
)
from ..models import Survey, SurveyAnswer, SurveyQuestion


class TestSurveyAdmin(RequestTestCase):

    @patch('django.contrib.admin.options.ModelAdmin.changeform_view')
    def test_changeform_view_original_object_id(self, changeform_view):
        admin = SurveyAdmin(Survey, None)
        object_id = '1'
        admin.changeform_view(MagicMock(), object_id)
        self.assertEqual(admin.original_object_id, object_id)

    def test_save_model(self):
        question = SurveyQuestionFactory.create()
        survey = question.survey
        original_id = survey.pk

        admin = SurveyAdmin(Survey, None)
        admin.original_object_id = original_id

        survey.id = None
        survey.name = '{} Copy'.format(survey.name)

        request = self.create_request('post', data={'_saveasnew': True})
        admin.save_model(request, survey, MagicMock(), False)

        self.assertIsNotNone(survey.id)
        self.assertNotEqual(survey.id, original_id)

        original = Survey.objects.get(pk=original_id)
        copy = Survey.objects.get(pk=survey.id)

        original_question = original.questions.get()
        copy_question = copy.questions.get()

        self.assertNotEqual(copy_question, original_question)

        self.assertEqual(copy_question.name, original_question.name)
        self.assertEqual(copy_question.section, original_question.section)
        copy_section_code = copy_question.section.get_code()
        original_section_code = original_question.section.get_code()
        self.assertEqual(copy_section_code, original_section_code)
        self.assertEqual(copy_question.level, original_question.level)
        self.assertEqual(copy_question.question_number, original_question.question_number)
        self.assertEqual(copy_question.upload_type, original_question.upload_type)
        self.assertEqual(copy_question.reference, original_question.reference)


class TestSurveyQuestionAdmin(RequestTestCase):
    def test_get_queryset(self):
        SurveyQuestionFactory.create()
        admin = SurveyQuestionAdmin(SurveyQuestion, None)

        with self.assertNumQueries(1):
            obj = admin.get_queryset(None)[0]
            admin.area(obj)

    def test_area(self):
        question = SurveyQuestionFactory.create()
        admin = SurveyQuestionAdmin(SurveyQuestion, None)
        self.assertEqual(admin.area(question), question.section.area)


class TestSurveyAnswerAdmin(RequestTestCase):
    def test_get_queryset(self):
        SurveyAnswerFactory.create()
        admin = SurveyAnswerAdmin(SurveyAnswer, None)

        with self.assertNumQueries(1):
            obj = admin.get_queryset(None)[0]
            admin.survey(obj)
            admin.organisation(obj)

    def test_survey(self):
        answer = SurveyAnswerFactory.create()
        admin = SurveyAnswerAdmin(SurveyAnswer, None)
        self.assertEqual(admin.survey(answer), answer.response.survey)

    def test_organisation(self):
        answer = SurveyAnswerFactory.create()
        admin = SurveyAnswerAdmin(SurveyAnswer, None)
        self.assertEqual(admin.organisation(answer), answer.response.organisation)
