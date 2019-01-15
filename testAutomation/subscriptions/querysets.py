from datetime import date

from django.db import models


class SubscriptionQueryset(models.QuerySet):
    def latest_for_organisation(self, organisation):
        subscriptions = self.filter(order__organisation=organisation)
        subscriptions = subscriptions.exclude(order__status='canceled')
        return subscriptions.order_by('-start_date').first()

    def active_for_organisation(self, organisation):
        from subscriptions.models import Order
        today = date.today()
        subscriptions = self.filter(
            order__organisation=organisation,
            order__status=Order.STATUS_APPROVED,
            start_date__lte=today,
            end_date__gte=today,
        )
        return subscriptions.order_by('-start_date').first()


class AssessmentPurchaseQueryset(models.QuerySet):
    def unused(self):
        return self.annotate(
            number_used=models.Count('invitations'),
        ).filter(
            number_used__lt=models.F('number_included'),
        )

    def get_pending_approval(self, organisation):
        from subscriptions.models import Order
        return self.filter(
            order__organisation=organisation,
            order__status__in=[Order.STATUS_NEW, Order.STATUS_IN_PROGRESS]
        ).aggregate(
            total_count=models.Sum('number_included')
        )['total_count']
