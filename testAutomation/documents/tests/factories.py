import factory

from .. import models


class DocumentFactory(factory.DjangoModelFactory):
    name = factory.Sequence('Document {}'.format)
    file = factory.django.FileField()
    organisation = factory.SubFactory('users.tests.factories.OrganisationFactory')

    class Meta:
        model = models.Document
