from django.test import TestCase

from users.tests.factories import UserFactory

from .factories import (
    SurveyAnswerFactory,
    SurveyAreaFactory,
    SurveyFactory,
    SurveyQuestionFactory,
    SurveyResponseFactory,
    SurveySectionFactory,
)
from ..models import (
    Survey,
    SurveyAnswer,
    SurveyQuestion,
    SurveyResponse,
)


class TestSurveyQueryset(TestCase):
    manager = Survey.objects

    def test_available(self):
        """Only surveys with questions are available"""
        survey = SurveyFactory.create()
        SurveyQuestionFactory.create(survey=survey)
        SurveyFactory.create()

        expected = {survey}
        self.assertSequenceEqual(set(self.manager.available()), expected)


class TestSurveyQuestionQueryset(TestCase):
    manager = SurveyQuestion.objects

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()
        cls.q_other_survey = SurveyQuestionFactory.create()
        area = SurveyAreaFactory.create(number=11)
        cls.section_1 = SurveySectionFactory.create(number=1, area=area)
        cls.section_2 = SurveySectionFactory.create(number=2, area=area)
        cls.section_3 = SurveySectionFactory.create(number=1, area__number=12)
        cls.q1 = SurveyQuestionFactory.create(
            survey=cls.survey,
            section=cls.section_1,
            level=1,
            question_number=1,
        )
        cls.q2 = SurveyQuestionFactory.create(
            survey=cls.survey,
            section=cls.section_2,
            level=1,
            question_number=1,
        )
        cls.q3 = SurveyQuestionFactory.create(
            survey=cls.survey,
            section=cls.section_1,
            level=2,
            question_number=1,
        )
        cls.q4 = SurveyQuestionFactory.create(
            survey=cls.survey,
            section=cls.section_2,
            level=2,
            question_number=1,
        )
        cls.q5 = SurveyQuestionFactory.create(
            survey=cls.survey,
            section=cls.section_2,
            level=2,
            question_number=2,
        )
        cls.q6 = SurveyQuestionFactory.create(
            survey=cls.survey,
            section=cls.section_3,
            level=1,
            question_number=1,
        )

    def test_for_survey(self):
        expected = {self.q1, self.q2, self.q3, self.q4, self.q5, self.q6}
        self.assertSequenceEqual(
            set(self.manager.for_survey(self.survey)),
            expected
        )

    def test_for_level_one(self):
        expected = {self.q1, self.q2, self.q6}
        self.assertSequenceEqual(
            set(self.manager.for_level(self.survey, level=1)),
            expected
        )

    def test_for_level_two(self):
        expected = {self.q1, self.q2, self.q3, self.q4, self.q5, self.q6}
        self.assertSequenceEqual(
            set(self.manager.for_level(self.survey, level=2)),
            expected
        )

    def test_for_section(self):
        expected = {self.q2, self.q4, self.q5}
        self.assertSequenceEqual(
            set(self.manager.for_section(self.survey, section=self.section_2)),
            expected
        )

    def test_next_section_first(self):
        self.assertEqual(
            self.manager.next_section(self.survey, current_section=None),
            self.section_1.pk
        )

    def test_next_section(self):
        self.assertEqual(
            self.manager.next_section(
                self.survey,
                current_section=self.section_1
            ),
            self.section_2.pk
        )

    def test_next_section_by_area(self):
        self.assertEqual(
            self.manager.next_section(
                self.survey,
                current_section=self.section_2
            ),
            self.section_3.pk
        )

    def test_next_section_last(self):
        self.assertEqual(
            self.manager.next_section(
                self.survey,
                current_section=self.section_3
            ),
            None
        )

    def test_previous_section_first(self):
        self.assertEqual(
            self.manager.previous_section(self.survey, current_section=self.section_1),
            None
        )

    def test_previous_section(self):
        self.assertEqual(
            self.manager.previous_section(
                self.survey,
                current_section=self.section_2
            ),
            self.section_1.pk
        )

    def test_previous_section_by_area(self):
        self.assertEqual(
            self.manager.previous_section(
                self.survey,
                current_section=self.section_3
            ),
            self.section_2.pk
        )


class TestSurveyResponseQueryset(TestCase):
    manager = SurveyResponse.objects

    @classmethod
    def setUpTestData(cls):
        cls.survey = SurveyFactory.create()
        SurveyQuestionFactory.create(survey=cls.survey)

    def test_for_user(self):
        user = UserFactory.create()
        sr1 = SurveyResponseFactory.create(
            survey=self.survey,
            organisation=user.organisation,
        )

        SurveyResponseFactory.create(survey=self.survey)

        # Serveys with no questions should be excluded
        SurveyResponseFactory.create(organisation=user.organisation)

        self.assertSequenceEqual(self.manager.for_user(user), [sr1])


class TestSurveyAnswerQueryset(TestCase):
    manager = SurveyAnswer.objects

    @classmethod
    def setUpTestData(cls):
        cls.answer1 = SurveyAnswerFactory.create(
            value=SurveyAnswer.ANSWER_YES,
        )
        cls.answer2 = SurveyAnswerFactory.create(
            value=SurveyAnswer.ANSWER_YES,
            response=cls.answer1.response,
        )
        cls.answer3 = SurveyAnswerFactory.create(
            value=SurveyAnswer.ANSWER_NO,
            response=cls.answer1.response,
        )

    def test_results(self):
        results = self.manager.results()
        expected = {
            'total': 3,
            'yes': 2,
            'no': 1,
            'in-progress': 0,
            'not-applicable': 0,
        }
        self.assertEqual(results, expected)

    def test_by_question(self):

        by_question = self.manager.by_question()
        expected = {
            self.answer1.question_id: self.answer1,
            self.answer2.question_id: self.answer2,
            self.answer3.question_id: self.answer3,
        }
        self.assertEqual(by_question, expected)
