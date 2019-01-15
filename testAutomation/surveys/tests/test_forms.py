from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from documents.tests.factories import DocumentFactory

from .factories import (
    SurveyAnswerDocumentFactory,
    SurveyQuestionFactory,
    SurveyResponseFactory,
)
from ..forms import SurveyAnswerForm
from ..models import SurveyAnswer, SurveyAnswerDocument


class TestSurveyAnswerForm(TestCase):
    def setUp(self):
        self.question = SurveyQuestionFactory.create()
        self.survey_response = SurveyResponseFactory.create(
            survey=self.question.survey,
        )

    def test_clean_value_yes(self):
        data = {
            'value': SurveyAnswer.ANSWER_YES,
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_value_progress_missing(self):
        data = {
            'value': SurveyAnswer.ANSWER_PROGRESS,
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('explanation', form.errors)
        self.assertIn('due_date', form.errors)

    def test_clean_value_progress(self):
        data = {
            'value': SurveyAnswer.ANSWER_PROGRESS,
            'explanation': 'The explanation',
            'due_date': '03/03/2031',
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_value_no_missing(self):
        data = {
            'value': SurveyAnswer.ANSWER_NO,
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('explanation', form.errors)
        self.assertNotIn('due_date', form.errors)

    def test_clean_value_no(self):
        data = {
            'value': SurveyAnswer.ANSWER_NO,
            'explanation': 'The explanation',
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertTrue(form.is_valid())

    def test_clean_due_date_past(self):
        data = {
            'value': SurveyAnswer.ANSWER_PROGRESS,
            'explanation': 'The explanation',
            'due_date': '03/03/2001',
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('due_date', form.errors)

    def test_fields(self):
        form = SurveyAnswerForm(self.question, self.survey_response)

        expected = ['value', 'options', 'explanation', 'due_date', 'operation']
        self.assertCountEqual(form.fields.keys(), expected)

    def test_helper(self):
        form = SurveyAnswerForm(self.question, self.survey_response)

        self.assertTrue(hasattr(form, 'helper'))
        self.assertFalse(hasattr(form, 'attach_helper'))
        self.assertFalse(hasattr(form, 'upload_helper'))


class TestSurveyAnswerFormAtachDocument(TestCase):
    def setUp(self):
        self.test_file = SimpleUploadedFile('test_file.txt', b'This is sample text')
        self.question = SurveyQuestionFactory.create(upload_type='progress')
        self.survey_response = SurveyResponseFactory.create(
            survey=self.question.survey,
        )
        self.document = DocumentFactory.create(
            organisation=self.survey_response.organisation,
        )

    def test_fields(self):
        form = SurveyAnswerForm(self.question, self.survey_response)

        expected = [
            'value',
            'options',
            'explanation',
            'due_date',
            'operation',
            'attach_document',
            'attach_explanation',
            'upload_name',
            'upload_expiry',
            'upload_file',
            'upload_explanation',
        ]
        self.assertCountEqual(form.fields.keys(), expected)

    def test_helper(self):
        form = SurveyAnswerForm(self.question, self.survey_response)

        self.assertTrue(hasattr(form, 'helper'))
        self.assertTrue(hasattr(form, 'attach_helper'))
        self.assertTrue(hasattr(form, 'upload_helper'))

    def test_clean_attach_document(self):
        data = {
            'operation': 'attach_document',
            'value': SurveyAnswer.ANSWER_YES,
            'attach_document': self.document.pk,
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertEqual(self.document.organisation, self.survey_response.organisation)
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_attach_document_other(self):
        document = DocumentFactory.create()
        data = {
            'operation': 'attach_document',
            'value': SurveyAnswer.ANSWER_YES,
            'attach_document': document.pk,
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertNotEqual(document.organisation, self.survey_response.organisation)
        self.assertFalse(form.is_valid())
        self.assertIn('attach_document', form.errors)

    def test_clean_attach_document_required(self):
        data = {
            'operation': 'attach_document',
            'value': SurveyAnswer.ANSWER_YES,
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('attach_document', form.errors)

    def test_clean_upload_document(self):
        data = {
            'operation': 'upload_document',
            'value': SurveyAnswer.ANSWER_YES,
            'upload_name': 'Any',
        }
        files = {
            'upload_file': self.test_file,
        }

        form = SurveyAnswerForm(
            self.question,
            self.survey_response,
            data=data,
            files=files,
        )

        self.assertEqual(self.document.organisation, self.survey_response.organisation)
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_upload_document_required(self):
        data = {
            'operation': 'upload_document',
            'value': SurveyAnswer.ANSWER_YES,
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('upload_name', form.errors)
        self.assertIn('upload_file', form.errors)

    def test_clean_value_yes_required(self):
        data = {
            'value': SurveyAnswer.ANSWER_YES,
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertFalse(form.is_valid())
        self.assertIn('value', form.errors)

    def test_clean_value_progress_not_required(self):
        data = {
            'value': SurveyAnswer.ANSWER_PROGRESS,
            'explanation': 'Any',
            'due_date': '03/03/2031',
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertTrue(form.is_valid())

    def test_clean_value_no_not_required(self):
        data = {
            'value': SurveyAnswer.ANSWER_NO,
            'explanation': 'Any',
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        self.assertTrue(form.is_valid())

    def test_clean_value_yes_document_exists(self):
        document = SurveyAnswerDocumentFactory.create(
            answer__question=self.question,
            answer__response=self.survey_response,
        )
        data = {
            'value': SurveyAnswer.ANSWER_YES,
        }
        form = SurveyAnswerForm(
            self.question,
            self.survey_response,
            instance=document.answer,
            data=data,
        )

        self.assertTrue(form.is_valid())

    def test_save_attach_document(self):
        data = {
            'operation': 'attach_document',
            'value': SurveyAnswer.ANSWER_YES,
            'attach_document': self.document.pk,
            'attach_explanation': 'The explanation',
        }
        form = SurveyAnswerForm(self.question, self.survey_response, data=data)

        answer = form.save()

        answer_docuemnt = SurveyAnswerDocument.objects.get()
        self.assertEqual(answer_docuemnt.answer, answer)
        self.assertEqual(answer_docuemnt.document, self.document)
        self.assertEqual(answer_docuemnt.explanation, data['attach_explanation'])

    def test_save_upload_document(self):
        data = {
            'operation': 'upload_document',
            'value': SurveyAnswer.ANSWER_YES,
            'upload_name': 'The name',
            'upload_explanation': 'The explanation',
        }
        files = {
            'upload_file': self.test_file,
        }
        form = SurveyAnswerForm(
            self.question,
            self.survey_response,
            data=data,
            files=files,
        )

        answer = form.save()

        answer_docuemnt = SurveyAnswerDocument.objects.get()
        self.assertEqual(answer_docuemnt.answer, answer)
        self.assertEqual(answer_docuemnt.explanation, data['upload_explanation'])
        self.assertEqual(answer_docuemnt.document.name, data['upload_name'])
        self.assertEqual(answer_docuemnt.document.file.read(), b'This is sample text')
        # Remove the file from the file system
        answer_docuemnt.document.file.delete()
