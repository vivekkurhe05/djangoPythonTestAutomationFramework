from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout

from django import forms

from .models import AssessmentPackage, AssessmentPurchase, Order, Subscription


class OrderForm(forms.ModelForm):
    subscription = forms.BooleanField(initial=False, required=False)
    package = forms.ModelChoiceField(
        queryset=AssessmentPackage.objects.filter(is_active=True),
        empty_label="None",
        widget=forms.RadioSelect(),
        required=False
    )

    class Meta:
        model = Order
        fields = []

    def __init__(self, organisation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.organisation = organisation
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Div(
                    Field(
                        'subscription', template='crispy/order/subscription_section.html'
                    ),
                ),
                Div(
                    Field(
                        'package', template='crispy/order/packages_section.html'
                    ),
                )
            )
        )

    def clean(self):
        cleaned_data = super(OrderForm, self).clean()
        subscription_selected = cleaned_data['subscription']
        package = cleaned_data.get('package', None)
        self.error_message = "Please correct the form"
        current_subscription = Subscription.objects.latest_for_organisation(
            self.organisation
        )
        self.current_subscription = current_subscription
        if current_subscription and not current_subscription.get_is_renewal_due():
            '''
            If user has active subscription which is not due for renewal
            User cannot place an order without any package selected
            and User cannot place an order with subscription selected
            '''
            if not package:
                self.error_message = "Please select a valid Assessment Package"
                self.add_error('package', self.error_message)

            if subscription_selected:
                self.error_message = "You already have an active subscription"
                self.add_error('subscription', self.error_message)

        if not subscription_selected and not current_subscription:
            self.error_message = "Please select subscription to place the order"
            self.add_error('subscription', self.error_message)
        return cleaned_data

    def save(self, commit=False):
        cleaned_data = super(OrderForm, self).clean()
        subscription_selected = cleaned_data['subscription']
        package = cleaned_data.get('package', None)

        self.instance.organisation = self.organisation
        self.instance.save()

        if subscription_selected:
            subscription = Subscription(order=self.instance)
            subscription.full_clean()
            subscription.save()

        if package:
            assessment_purchase = AssessmentPurchase(order=self.instance, package=package)
            assessment_purchase.clean()
            assessment_purchase.save()
        return self.instance
