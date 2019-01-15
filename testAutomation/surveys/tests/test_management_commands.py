'''
from unittest.mock import mock_open, patch

from django.core.management import call_command
from django.test import TestCase

from .factories import SurveyFactory, SurveyQuestionFactory
from ..management.commands import import_survey
from ..models import Survey, SurveyQuestion


class TestExportUsers(TestCase):
    def csv_ise(self, *args):
        """Turn a list of strings into a line from a CSV."""
        return ','.join(args) + '\r\n'

    def run_command(self, data):
        method_to_patch = 'surveys.management.commands.import_survey.open_csv_file'
        with patch(method_to_patch) as open_csv_file:
            open_csv_file.return_value = bytearray(data, encoding='utf-8')
            call_command('import_survey', 'survey', 'questions.csv', verbosity=0)

    def test_open_csv_file(self):
        expected = 'the file content'
        filemname = 'questions.csv'
        mocked = mock_open(read_data=expected)
        with patch('builtins.open', mocked, create=True):
            contents = import_survey.open_csv_file(filemname)

        mocked.assert_called_once_with(filemname, 'rb')
        self.assertEqual(contents, expected)

    def test_extension(self):
        filename = import_survey.ensure_extension('questions', 'csv')
        self.assertEqual(filename, 'questions.csv')

    def test_from_scratch(self):
        """Import a new survey and create its questions."""
        csv = self.csv_ise('Name', 'Code', 'Upload', 'Reference')
        csv += self.csv_ise('What is your name?', '4.3.2.1', 'Policy', 'www.example.com')

        self.run_command(data=csv)
        survey = Survey.objects.get()
        question = SurveyQuestion.objects.get()

        self.assertEqual(survey.name, 'survey')
        self.assertEqual(question.name, 'What is your name?')
        self.assertEqual(question.section_code, '4.3')
        self.assertEqual(question.section, 1)  # since it was the first section found
        self.assertEqual(question.level, 2)
        self.assertEqual(question.question_number, 1)
        self.assertEqual(question.upload_type, 'policy')
        self.assertEqual(question.reference, 'www.example.com')

    def test_overwrite(self):
        """Import over the top of an existing survey."""
        old_survey = SurveyFactory.create(name='survey')
        SurveyQuestionFactory.create(survey=old_survey, name='Old question?')

        csv = self.csv_ise('Name', 'Code', 'Upload', 'Reference')
        csv += self.csv_ise('What is your name?', '4.3.2.1', 'Policy', 'www.example.com')

        self.run_command(data=csv)

        Survey.objects.get()  # Will explode if a new survey has been created
        question = SurveyQuestion.objects.get()
        self.assertEqual(question.name, 'What is your name?')

    def test_broken_columns(self):
        """Throw a nice error message when the CSV has the wrong columns."""
        csv = self.csv_ise('Name', 'Code', 'Unrelated')

        message = '^The CSV must have Name, Code, Upload and Reference columns\.$'
        with self.assertRaisesRegexp(ValueError, message):
            self.run_command(data=csv)

    def test_required_name(self):
        """Throw a nice error message when an entry is missing a name."""
        csv = self.csv_ise('Name', 'Code', 'Upload', 'Reference')
        csv += self.csv_ise('Question?', '', '', '')

        message = '^The entry at line 2 must have both Name and Code\. \(Question\?\)$'
        with self.assertRaisesRegexp(ValueError, message):
            self.run_command(data=csv)

    def test_required_code(self):
        """Throw a nice error message when an entry is missing a code."""
        csv = self.csv_ise('Name', 'Code', 'Upload', 'Reference')
        csv += self.csv_ise('', '4.3.2.1', '', '')

        message = '^The entry at line 2 must have both Name and Code\. \(4\.3\.2\.1\)$'
        with self.assertRaisesRegexp(ValueError, message):
            self.run_command(data=csv)

    def test_required_code_and_name_missing(self):
        """Throw a nice error message when an entry is missing a code and name."""
        csv = self.csv_ise('Name', 'Code', 'Upload', 'Reference')
        csv += self.csv_ise('', '', '', '')

        message = '^The entry at line 2 must have both Name and Code\. \(\)$'
        with self.assertRaisesRegexp(ValueError, message):
            self.run_command(data=csv)

    def test_broken_code(self):
        """Throw a nice error message when a code has the wrong format."""
        csv = self.csv_ise('Name', 'Code', 'Upload', 'Reference')
        csv += self.csv_ise('Question?', '3.2.1', '', '')

        message = (
            '^A code must consist of four digits \(e\.g\. 4\.3\.2\.1\) '
            '- the code at line 2 is 3\.2\.1$'
        )
        with self.assertRaisesRegexp(ValueError, message):
            self.run_command(data=csv)

    def test_broken_upload(self):
        """Throw a nice error message when the upload type has an invalid value."""
        csv = self.csv_ise('Name', 'Code', 'Upload', 'Reference')
        csv += self.csv_ise('Question?', '4.3.2.1', 'Nonsense', '')

        message = (
            '^The entry at line 2, with code 4\.3\.2\.1, must have Policy, '
            'Procedure, or nothing in the Upload column\.$'
        )
        with self.assertRaisesRegexp(ValueError, message):
            self.run_command(data=csv)
'''
