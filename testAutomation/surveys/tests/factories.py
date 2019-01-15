import factory

from users.tests.factories import OrganisationFactory
from .. import models


class SurveyFactory(factory.DjangoModelFactory):
    name = factory.Sequence('Survey {}'.format)

    class Meta:
        model = models.Survey


class SurveyAreaFactory(factory.DjangoModelFactory):
    name = factory.Sequence('Survey Area {}'.format)
    number = factory.Sequence(int)

    class Meta:
        model = models.SurveyArea
        django_get_or_create = ('number',)


class SurveySectionFactory(factory.DjangoModelFactory):
    name = factory.Sequence('Survey Section {}'.format)
    number = factory.Sequence(int)
    area = factory.SubFactory(SurveyAreaFactory)

    class Meta:
        model = models.SurveySection


class SurveyQuestionFactory(factory.DjangoModelFactory):
    survey = factory.SubFactory(SurveyFactory)
    name = factory.Sequence('SurveyQuestion {}?'.format)
    section = factory.SubFactory(SurveySectionFactory)
    level = 1
    question_number = 1

    class Meta:
        model = models.SurveyQuestion


class SurveyQuestionOptionFactory(factory.DjangoModelFactory):
    question = factory.SubFactory(SurveyQuestionFactory)
    name = factory.Sequence('SurveyQuestionOption {}'.format)

    class Meta:
        model = models.SurveyQuestionOption


class SurveyResponseFactory(factory.DjangoModelFactory):
    survey = factory.SubFactory(SurveyFactory)
    organisation = factory.SubFactory(OrganisationFactory)
    level = 1

    class Meta:
        model = models.SurveyResponse


class SurveyAnswerFactory(factory.DjangoModelFactory):
    response = factory.SubFactory(SurveyResponseFactory)
    question = factory.SubFactory(SurveyQuestionFactory)
    value = 'yes'

    class Meta:
        model = models.SurveyAnswer


class SurveyAnswerDocumentFactory(factory.DjangoModelFactory):
    answer = factory.SubFactory(SurveyAnswerFactory)
    document = factory.SubFactory(
        'documents.tests.factories.DocumentFactory',
        organisation=factory.SelfAttribute('..answer.response.organisation'),
    )

    class Meta:
        model = models.SurveyAnswerDocument
