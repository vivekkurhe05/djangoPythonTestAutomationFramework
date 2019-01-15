from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponseRedirect
from django.views.generic import DetailView, FormView, ListView, TemplateView
from rolepermissions.checkers import has_role

from core.mixins import AppMixin

from .forms import OrderForm
from .models import AssessmentPackage, AssessmentPurchase, Order


class SubscriptionMixin(LoginRequiredMixin, AppMixin):
    sidebar_section = 'settings'
    sidebar_item = 'subscription'
    page_title = 'Subscription & billing'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        packages = AssessmentPackage.objects.filter(
            is_active=True
        ).order_by('number_included')
        context.update(
            packages=packages,
            subscription_defaults=settings.SITE_SUBSCRIPTION,
            subscription_default_email=settings.DEFAULT_SUBSCRIPTION_FROM_EMAIL,
        )
        return context


class SubscriptionListView(SubscriptionMixin, UserPassesTestMixin, TemplateView):
    template_name = 'subscription.html'

    def test_func(self):
        return has_role(self.request.user, ['admin'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisation = self.request.user.organisation
        pending_assessment_purchase = AssessmentPurchase.objects.get_pending_approval(
            organisation
        )
        context.update(
            pending_assessment_purchase=pending_assessment_purchase,
            latest_subscription=organisation.latest_subscription,
            show_order_history=Order.objects.filter(organisation=organisation).exists()
        )
        return context


class OrderView(SubscriptionMixin, UserPassesTestMixin, FormView):
    template_name = 'order.html'
    form_class = OrderForm
    success_url = reverse_lazy('subscription')
    form_initial_data = None

    def test_func(self):
        return has_role(self.request.user, ['admin'])

    def get_initial(self):
        initial = super().get_initial()
        try:
            package_id = int(self.request.GET.get('id', 0))
        except ValueError:
            package_id = 0
        organisation = self.request.user.organisation
        current_subscription = organisation.latest_subscription
        package = AssessmentPackage.objects.filter(id=package_id).first()
        initial['subscription'] = current_subscription is None or (
            current_subscription.get_is_renewal_due()
        )
        initial['package'] = package
        self.form_initial_data = initial
        return initial

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        current_subscription = request.user.organisation.latest_subscription
        if current_subscription and (
            not current_subscription.order.get_is_approved()
        ):
            messages.warning(self.request, (
                '''
                You have an order in progress, please complete the order
                by paying the invoice. Please contact us if you have any
                questions or you need to make any amends to the order
                '''
            ), extra_tags='show-icon')
            return HttpResponseRedirect(reverse('subscription'))
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_subscription = self.request.user.organisation.latest_subscription
        total_amount = 0.0
        if self.form_initial_data['subscription']:
            total_amount += context['subscription_defaults']['price']
        if self.form_initial_data['package']:
            total_amount += float(self.form_initial_data['package'].price)
        has_active_subscription = current_subscription and (
            not current_subscription.get_is_expired()
        )
        context.update(
            valid_until=datetime.now() + relativedelta(years=1),
            has_active_subscription=has_active_subscription,
            total_amount=total_amount
        )
        return context

    def form_invalid(self, form, **kwargs):
        messages.warning(
            self.request, 'Order failed - {}'.format(form.error_message),
            extra_tags='show-icon'
        )
        return super().form_invalid(form)

    def form_valid(self, form, **kwargs):
        response = super().form_valid(form)
        instance = form.save()
        instance.send_order_confirmation()
        messages.success(
            self.request, 'You have successfully submitted the order',
            extra_tags='show-icon'
        )
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'organisation': self.request.user.organisation})
        return kwargs


class OrderHistoryView(SubscriptionMixin, UserPassesTestMixin, ListView):
    template_name = 'order_history.html'
    paginate_by = 20
    page_limit = 5
    context_object_name = "orders"

    def test_func(self):
        return has_role(self.request.user, ['admin'])

    def get_queryset(self):
        organisation = self.request.user.organisation
        return Order.objects.filter(
            organisation=organisation
        )


class OrderDetailsView(SubscriptionMixin, UserPassesTestMixin, DetailView):
    template_name = 'order_details.html'
    model = Order

    def test_func(self):
        return has_role(self.request.user, ['admin'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = context['object']
        order_items, order_total = order.get_order_details()
        context.update(
            order_total=order_total
        )
        return context
