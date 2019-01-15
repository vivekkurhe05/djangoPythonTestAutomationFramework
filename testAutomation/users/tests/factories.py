import factory

from ..models import Invitation, Organisation, User


class OrganisationFactory(factory.DjangoModelFactory):
    legal_name = factory.Sequence('Test organisation {}'.format)

    class Meta:
        model = Organisation


class UserFactory(factory.DjangoModelFactory):
    is_active = True
    email = factory.Sequence('user-{}@example.com'.format)
    name = factory.Sequence('User {}'.format)
    password = factory.PostGenerationMethodCall('set_password', None)
    organisation = factory.SubFactory(OrganisationFactory)

    class Meta:
        model = User


class InvitationFactory(factory.DjangoModelFactory):
    survey = factory.SubFactory('surveys.tests.factories.SurveyFactory')
    grantor = factory.SubFactory(OrganisationFactory)
    grantee = factory.SubFactory(OrganisationFactory)
    level = 1
    status = 1

    class Meta:
        model = Invitation
