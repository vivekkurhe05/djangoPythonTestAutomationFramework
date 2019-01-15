import factory

from users.tests.factories import OrganisationFactory
from .. import models


class AssessmentPackageFactory(factory.DjangoModelFactory):
    name = factory.Sequence('AssessmentPackage {}'.format)

    class Meta:
        model = models.AssessmentPackage


class OrderFactory(factory.DjangoModelFactory):
    organisation = factory.SubFactory(OrganisationFactory)

    class Meta:
        model = models.Order


class SubscriptionFactory(factory.DjangoModelFactory):
    order = factory.SubFactory(OrderFactory)

    class Meta:
        model = models.Subscription


class AssessmentPurchaseFactory(factory.DjangoModelFactory):
    order = factory.SubFactory(OrderFactory)

    class Meta:
        model = models.AssessmentPurchase
