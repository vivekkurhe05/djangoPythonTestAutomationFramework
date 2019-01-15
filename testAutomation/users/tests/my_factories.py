import factory
from ..models import User, Organisation


class OrganisationFactory(factory.DjangoModelFactory):
    legal_name = factory.Sequence('Test organisation {}'.format)

    class Meta:
        model = Organisation


class UserFactory(factory.django.DjangoModelFactory):

    # To check checkbox in backend database use following is_active = True
    is_active = True
    name = factory.sequence(lambda n: 'user-{0}'.format(n))
    email = factory.sequence(lambda n: 'user-{0}@example.com'.format(n))
    password = factory.PostGenerationMethodCall('set_password', None)
    organisation = factory.SubFactory(OrganisationFactory)

    class Meta:
        model = User
