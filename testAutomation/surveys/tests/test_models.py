from django.core.urlresolvers import reverse
from django.core.validators import ValidationError
from django.test import TestCase

from documents.tests.factories import DocumentFactory
from users.models import Invitation as InvitationModel
from users.tests.factories import InvitationFactory, OrganisationFactory

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
from ..models import Survey, SurveyAnswer, SurveyResponse


class TestSurvey(TestCase):
    def test_str(self):
        survey = SurveyFactory.build()
        self.assertEqual(str(survey), survey.name)


class TestSurveySections(TestCase):
    def setUp(self):
        self.survey = SurveyFactory.create()
        self.area = SurveyAreaFactory.create(number=4)

        self.section4_1 = SurveySectionFactory.create(
            number=1,
            area=self.area,
        )
        self.section4_2 = SurveySectionFactory.create(
            number=2,
            area=self.area,
        )
        self.section4_3 = SurveySectionFactory.create(
            number=3,
            area=self.area,
        )

        self.q1 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section4_1
        )
        self.q2 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=2,
            section=self.section4_1
        )
        self.q3 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=3,
            section=self.section4_2
        )
        self.q4 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=4,
            section=self.section4_3
        )

    def test_get_sections(self):
        sections = self.survey.get_sections()
        self.assertSequenceEqual(
            sections,
            [
                self.q1.section,
                self.q3.section,
                self.q4.section,
            ]
        )


class TestSurveyQuestion(TestCase):
    def setUp(self):
        self.question = SurveyQuestionFactory.create(
            section__area__number=4,
            section__number=1,
            level=2,
            question_number=3,
        )

    def test_get_code(self):
        self.assertEqual(self.question.get_code(), '4.1.2.3')

    def test_str(self):
        self.assertEqual(str(self.question), self.question.name)


class TestSurveyQuestionOption(TestCase):
    def test_str(self):
        option = SurveyQuestionOptionFactory.build()
        self.assertEqual(str(option), option.name)


class TestSurveyResponse(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()
        cls.area = SurveyAreaFactory.create(number=4)
        cls.q1 = SurveyQuestionFactory.create(
            survey=cls.survey,
            level=1,
            section=SurveySectionFactory.create(number=1, area=cls.area)
        )
        cls.q2 = SurveyQuestionFactory.create(
            survey=cls.survey,
            level=2,
            section=SurveySectionFactory.create(number=2, area=cls.area)
        )
        cls.q3 = SurveyQuestionFactory.create(
            survey=cls.survey,
            level=3,
            section=SurveySectionFactory.create(number=3, area=cls.area)
        )

    def test_get_summary_url(self):
        response = SurveyResponseFactory.create()
        expected = reverse('survey-progress', kwargs={'pk': response.pk})
        self.assertEqual(response.get_summary_url(), expected)

    def test_get_summary_url_complete(self):
        response = SurveyResponseFactory.create()
        expected = reverse('survey-compliance', kwargs={'pk': response.pk})
        self.assertEqual(response.get_summary_url(is_complete=True), expected)


class TestSurveyResponseProgress(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()
        cls.area = SurveyAreaFactory.create(number=4)
        cls.section4_1 = SurveySectionFactory.create(number=1, area=cls.area)
        cls.section4_2 = SurveySectionFactory.create(number=2, area=cls.area)
        cls.section4_3 = SurveySectionFactory.create(number=3, area=cls.area)

        cls.q1 = SurveyQuestionFactory.create(
            survey=cls.survey,
            level=1,
            section=cls.section4_1
        )
        cls.q2 = SurveyQuestionFactory.create(
            survey=cls.survey,
            level=2,
            section=cls.section4_2
        )
        cls.q3 = SurveyQuestionFactory.create(
            survey=cls.survey,
            level=3,
            section=cls.section4_3
        )

        # section 4_2 question with no answer
        SurveyQuestionFactory.create(
            survey=cls.survey,
            level=2,
            section=cls.section4_2,
            question_number=2,
        )
        # section 4_3 question with no answer
        SurveyQuestionFactory.create(
            survey=cls.survey,
            level=2,
            section=cls.section4_3,
            question_number=2,
        )

        cls.survey_response = SurveyResponseFactory(
            survey=cls.survey,
            level=2
        )

        # section 4_1 answer
        SurveyAnswerFactory.create(
            response=cls.survey_response,
            question=cls.q1,
            value=SurveyAnswer.ANSWER_YES,
        )
        # section 4_2 answer
        SurveyAnswerFactory.create(
            response=cls.survey_response,
            question=cls.q2,
            value=SurveyAnswer.ANSWER_NO,
        )

        # section 4_2 question with answer
        SurveyAnswerFactory.create(
            response=cls.survey_response,
            value=SurveyAnswer.ANSWER_NO,
            question__survey=cls.survey,
            question__level=2,
            question__section=cls.section4_2,
            question__question_number=3,
        )

        # Not included progress because q3 is level 3
        SurveyAnswerFactory.create(
            response=cls.survey_response,
            question=cls.q3,
            value=SurveyAnswer.ANSWER_YES,
        )

        cls.expected_progress_total = {
            'total': 5,
            'count': 3,
            'ratio': 3 / 5,
            'percentage': 60,
            'slug': 'in-progress',
            'is_complete': False,
            'label': 'In progress',
        }

        org_grantor = OrganisationFactory.create(legal_name='Grantor Org')
        cls.invitation = InvitationFactory.create(
            grantor=org_grantor,
            grantee=cls.survey_response.organisation,
            accepted=True,
            survey=cls.survey
        )

    def test_get_progress_info_new(self):
        expected = {
            'total': 10,
            'count': 0,
            'slug': 'not-started',
            'is_complete': False,
            'label': 'Not yet started',
            'ratio': 0,
            'percentage': 0,
        }
        self.assertEqual(SurveyResponse.get_progress_info(0, 10), expected)

    def test_get_progress_info_progress(self):
        expected = {
            'total': 10,
            'count': 5,
            'slug': 'in-progress',
            'is_complete': False,
            'label': 'In progress',
            'ratio': 0.5,
            'percentage': 50,
        }
        self.assertEqual(SurveyResponse.get_progress_info(5, 10), expected)

    def test_get_progress_info_complete(self):
        expected = {
            'total': 10,
            'count': 10,
            'slug': 'complete',
            'is_complete': True,
            'label': 'Complete',
            'ratio': 1.0,
            'percentage': 100,
        }
        self.assertEqual(SurveyResponse.get_progress_info(10, 10), expected)

    def test_get_progress_info_zero(self):
        expected = {
            'total': 1,
            'count': 0,
            'slug': 'not-started',
            'is_complete': False,
            'label': 'Not yet started',
            'ratio': 0,
            'percentage': 0,
        }
        self.assertEqual(SurveyResponse.get_progress_info(0, 1), expected)

    def test_get_progress_info_no_question(self):
        expected = {
            'total': 0,
            'count': 0,
            'slug': 'no-question',
            'is_complete': True,
            'label': 'No questions for this tier',
            'ratio': 0,
            'percentage': 0,
        }
        self.assertEqual(SurveyResponse.get_progress_info(0, 0), expected)

    def test_get_progress_info_110(self):
        expected = {
            'total': 10,
            'count': 10,
            'slug': 'complete',
            'is_complete': True,
            'label': 'Complete',
            'ratio': 1.0,
            'percentage': 100,
        }
        self.assertEqual(SurveyResponse.get_progress_info(11, 10), expected)

    def test_get_progress(self):
        expected = {
            'sections': [
                {
                    'section': self.section4_1,
                    'total': 1,
                    'count': 1,
                    'slug': 'complete',
                    'is_complete': True,
                    'label': 'Complete',
                    'ratio': 1.0,
                    'percentage': 100,
                },
                {
                    'section': self.section4_2,
                    'total': 3,
                    'count': 2,
                    'slug': 'in-progress',
                    'is_complete': False,
                    'label': 'In progress',
                    'ratio': 2 / 3,
                    'percentage': 67,
                },
                {
                    'section': self.section4_3,
                    'total': 1,
                    'count': 0,
                    'slug': 'not-started',
                    'is_complete': False,
                    'label': 'Not yet started',
                    'ratio': 0.0,
                    'percentage': 0,
                },
            ],
        }
        expected.update(self.expected_progress_total)
        expected['compliance'] = {
            'total': 5,
            'count': 1,
            'ratio': 1 / 5,
            'percentage': 20,
            'slug': 'in-progress',
            'is_complete': False,
            'label': 'In progress',
        }

        """
        SELECT DISTINCT
          FROM "surveys_surveysection"
         INNER
          JOIN "surveys_surveyquestion"
            ON ("surveys_surveysection"."id" =  "surveys_surveyquestion"."section_id")
         INNER
          JOIN "surveys_surveyarea"
            ON ("surveys_surveysection"."area_id" =  "surveys_surveyarea"."id")
         WHERE (
                   "surveys_surveyquestion"."level" <= 4
           AND "surveys_surveyquestion"."survey_id" =  4582
               )
         ORDER BY "surveys_surveyarea"."number" ASC, "surveys_surveysection"."number" ASC
        SELECT
            SUM(
                CASE WHEN "surveys_surveyquestion"."section_id" = 7001 THEN 1 ELSE 0 END
            ) AS "7001",
            SUM(
                CASE WHEN "surveys_surveyquestion"."section_id" = 7000 THEN 1 ELSE 0 END
            ) AS "7000",
            SUM(
                CASE WHEN "surveys_surveyquestion"."section_id" = 7002 THEN 1 ELSE 0 END
            ) AS "7002"
          FROM "surveys_surveyquestion"
         WHERE "surveys_surveyquestion"."survey_id" =  4582
        SELECT
            SUM(
                CASE WHEN "surveys_surveyquestion"."section_id" = 7001 THEN 1 ELSE 0 END
            ) AS "7001",
            SUM(
                CASE WHEN "surveys_surveyquestion"."section_id" = 7000 THEN 1 ELSE 0 END
            ) AS "7000",
            SUM(
                CASE WHEN "surveys_surveyquestion"."section_id" = 7002 THEN 1 ELSE 0 END
            ) AS "7002"
          FROM "surveys_surveyanswer"
         INNER
          JOIN "surveys_surveyquestion"
            ON ("surveys_surveyanswer"."question_id" =  "surveys_surveyquestion"."id")
         WHERE "surveys_surveyanswer"."response_id" =  8071

        """
        with self.assertNumQueries(3):
            self.assertEqual(self.survey_response.get_progress(), expected)

    def test_get_total_progress(self):
        with self.assertNumQueries(3):
            survey_response = list(Survey.objects.with_latest_response_progress(
                self.survey_response.organisation,
                []  # empty list of sent Invitations
            ))[0].survey_response
            progress = survey_response.progress

        self.assertEqual(progress, self.expected_progress_total)

    def test_survey_response_invites(self):
        with self.assertNumQueries(4):
            invitations = InvitationModel.objects.filter(
                grantee=self.survey_response.organisation,
                accepted=True
            )
            survey_response = list(Survey.objects.with_latest_response_progress(
                self.survey_response.organisation,
                invitations
            ))[0]
        self.assertEqual(len(survey_response.invites), 1)

    def test_get_compliance(self):
        expected = {
            'progress': self.expected_progress_total,
            'compliance': {
                'levels': {
                    1: {
                        'slug': 'complete',
                        'is_complete': True,
                        'label': 'Bronze',
                        'level': 1,
                        'count': 1,
                        'total': 1,
                        'percentage': 100,
                        'ratio': 1.0,
                    },
                    2: {
                        'slug': 'in-progress',
                        'is_complete': False,
                        'label': 'Silver',
                        'level': 2,
                        'count': 1,
                        'total': 5,
                        'percentage': 20,
                        'ratio': 1 / 5,
                    },
                    3: {
                        'slug': 'in-progress',
                        'is_complete': False,
                        'label': 'Gold',
                        'level': 3,
                        'count': 2,
                        'total': 6,
                        'percentage': 33,
                        'ratio': 2 / 6,
                    },
                    4: {
                        'slug': 'in-progress',
                        'is_complete': False,
                        'label': 'Platinum',
                        'level': 4,
                        'count': 2,
                        'total': 6,
                        'percentage': 33,
                        'ratio': 2 / 6,
                    },
                },
                'sections': [
                    {
                        'levels': [
                            {
                                'count': 1,
                                'label': 'Bronze',
                                'level': 1,
                                'percentage': 100,
                                'total': 1,
                                'ratio': 1.0,
                                'slug': 'complete',
                                'is_complete': True,
                            },
                            {
                                'count': 1,
                                'label': 'Silver',
                                'level': 2,
                                'percentage': 100,
                                'total': 1,
                                'ratio': 1.0,
                                'slug': 'complete',
                                'is_complete': True,
                            },
                            {
                                'count': 1,
                                'label': 'Gold',
                                'level': 3,
                                'percentage': 100,
                                'total': 1,
                                'ratio': 1.0,
                                'slug': 'complete',
                                'is_complete': True,
                            },
                            {
                                'count': 1,
                                'label': 'Platinum',
                                'level': 4,
                                'percentage': 100,
                                'total': 1,
                                'ratio': 1.0,
                                'slug': 'complete',
                                'is_complete': True,
                            },
                        ],
                        'section': self.section4_1
                    },
                    {
                        'levels': [
                            {
                                'count': 0,
                                'label': 'Bronze',
                                'level': 1,
                                'percentage': 0,
                                'total': 0,
                                'ratio': 0,
                                'slug': 'no-question',
                                'is_complete': True,
                            },
                            {
                                'count': 0,
                                'label': 'Silver',
                                'level': 2,
                                'percentage': 0,
                                'total': 3,
                                'ratio': 0.0,
                                'slug': 'not-started',
                                'is_complete': False,
                            },
                            {
                                'count': 0,
                                'label': 'Gold',
                                'level': 3,
                                'percentage': 0,
                                'total': 3,
                                'ratio': 0.0,
                                'slug': 'not-started',
                                'is_complete': False,
                            },
                            {
                                'count': 0,
                                'label': 'Platinum',
                                'level': 4,
                                'percentage': 0,
                                'total': 3,
                                'ratio': 0.0,
                                'slug': 'not-started',
                                'is_complete': False,
                            },
                        ],
                        'section': self.section4_2,
                    },
                    {
                        'levels': [
                            {
                                'count': 0,
                                'label': 'Bronze',
                                'level': 1,
                                'percentage': 0,
                                'total': 0,
                                'ratio': 0,
                                'slug': 'no-question',
                                'is_complete': True,
                            },
                            {
                                'count': 0,
                                'label': 'Silver',
                                'level': 2,
                                'percentage': 0,
                                'total': 1,
                                'ratio': 0.0,
                                'slug': 'not-started',
                                'is_complete': False,
                            },
                            {
                                'count': 1,
                                'label': 'Gold',
                                'level': 3,
                                'percentage': 50,
                                'total': 2,
                                'ratio': 1 / 2,
                                'slug': 'in-progress',
                                'is_complete': False,
                            },
                            {
                                'count': 1,
                                'label': 'Platinum',
                                'level': 4,
                                'percentage': 50,
                                'total': 2,
                                'ratio': 1 / 2,
                                'slug': 'in-progress',
                                'is_complete': False,
                            },
                        ],
                        'section': self.section4_3,
                    },
                ],
            }
        }
        with self.assertNumQueries(3):
            compliance = self.survey_response.get_compliance()
        self.assertEqual(compliance, expected)

    def test_get_level_compliance(self):
        expected = {
            'compliance': {
                'count': 1,
                'label': 'In progress',
                'percentage': 20,
                'ratio': 0.2,
                'sections': [
                    {
                        'count': 1,
                        'label': 'Complete',
                        'percentage': 100,
                        'ratio': 1.0,
                        'section': self.section4_1,
                        'slug': 'complete',
                        'is_complete': True,
                        'total': 1,
                    },
                    {
                        'count': 0,
                        'label': 'Not yet started',
                        'percentage': 0,
                        'ratio': 0.0,
                        'section': self.section4_2,
                        'slug': 'not-started',
                        'is_complete': False,
                        'total': 3,
                    },
                    {
                        'count': 0,
                        'label': 'Not yet started',
                        'percentage': 0,
                        'ratio': 0.0,
                        'section': self.section4_3,
                        'slug': 'not-started',
                        'is_complete': False,
                        'total': 1,
                    }
                ],
                'slug': 'in-progress',
                'is_complete': False,
                'total': 5,
            },
            'progress': {
                'count': 3,
                'label': 'In progress',
                'percentage': 60,
                'ratio': 0.6,
                'slug': 'in-progress',
                'is_complete': False,
                'total': 5,
            }
        }
        with self.assertNumQueries(3):
            stats = self.survey_response.get_level_compliance()
        self.assertEqual(stats, expected)


class TestSurveyAnswer(TestCase):
    def test_str(self):
        answer = SurveyAnswerFactory.build()
        self.assertEqual(str(answer), answer.get_value_display())


class TestSurveyAnswerDocument(TestCase):
    def test_str(self):
        answer_docuemnt = SurveyAnswerDocumentFactory.create()
        expected = '{} - {} - {}'.format(
            answer_docuemnt.created.strftime('%Y-%m-%d %H:%M:%S'),
            answer_docuemnt.answer_id,
            answer_docuemnt.document_id,
        )
        self.assertEqual(str(answer_docuemnt), expected)

    def test_clean(self):
        "Clean should not error if organisations match"
        answer_docuemnt = SurveyAnswerDocumentFactory.create()
        self.assertEqual(
            answer_docuemnt.answer.response.organisation,
            answer_docuemnt.document.organisation,
        )
        answer_docuemnt.clean()

    def test_clean_different_organisation(self):
        document = DocumentFactory.create()
        answer_docuemnt = SurveyAnswerDocumentFactory.create(document=document)

        self.assertNotEqual(
            answer_docuemnt.answer.response.organisation,
            answer_docuemnt.document.organisation,
        )
        message = 'The document and survey answer organisations must match'
        with self.assertRaisesRegex(ValidationError, message):
            answer_docuemnt.clean()
