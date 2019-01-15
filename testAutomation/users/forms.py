import os

from captcha.fields import ReCaptchaField
from crispy_forms.bootstrap import FormActions, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, HTML, Layout
from django import forms
from django.conf import settings
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm as PasswordChangeFormBase,
    UserCreationForm
)
from django.contrib.auth.forms import PasswordResetForm as PasswordResetFormBase
from django.utils.translation import ugettext_lazy as _

from .models import Organisation, User


class BootstrapClearableFileInput(forms.ClearableFileInput):
    template_name = 'widgets/clearable_file_input.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        file_name = value and os.path.basename(value.name)
        context['widget'].update(file_name=file_name)
        return context


class OrganisationForm(forms.ModelForm):
    class Meta:
        fields = (
            'legal_name',
            'acronym',
            'known_as',
            'types',
            'parent_organisation',
            'registration_number',
            'supporting_file',
            'iati_uid',

            'address_1',
            'address_2',
            'city',
            'province',
            'country',
            'zip',
            'po_box',
            'phone_number',
            'landmark',
            'size',
            'annual_expenditure',
            'website',
            'social_media',
            'other_social_media',
            'biography',
        )
        model = Organisation
        widgets = {
            'supporting_file': BootstrapClearableFileInput
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['legal_name'].widget.attrs.pop('autofocus', None)
        self.fields['country'].empty_label = None

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Field(
                    'legal_name',
                    placeholder=_('Awarding or receiving the grant'),
                    wrapper_class='col-md-6',
                ),
                Field(
                    'acronym',
                    wrapper_class='col-md-6',
                ),

                Field(
                    'known_as',
                    placeholder=_('Otherwise known as...'),
                    wrapper_class='col-md-6',
                ),
                Field(
                    'parent_organisation',
                    placeholder=_('Parent / umbrella organization'),
                    wrapper_class='col-md-6',
                ),

                Field(
                    'types',
                    data_placeholder=_('Type of organization'),
                    data_plugin='select2',
                    data_option='{}',
                    style="width:100%",
                    wrapper_class='col-md-6',
                ),
                Field('iati_uid', wrapper_class='col-md-6'),

                Field(
                    'registration_number',
                    placeholder=_('Registration number'),
                    wrapper_class='col-md-6',
                ),
                Field(
                    'supporting_file',
                    placeholder=_('Evidence of registration'),
                    template='bootstrap4/layout/field_file.html',
                    wrapper_class='col-md-6',
                ),
                css_class='form-row',
            ),
            Div(
                HTML('<h6 class="col-md-12 mt-3">Address</h6>'),
                Field(
                    'address_1', placeholder=_('Address 1'),
                    wrapper_class='col-md-12',
                ),
                Field(
                    'address_2', placeholder=_('Address 2'),
                    wrapper_class='col-md-12',
                ),
                Field('city', placeholder=_('City / Town'), wrapper_class='col-md-6'),
                Field(
                    'province',
                    placeholder=_('County, Province, District, State'),
                    wrapper_class='col-md-6',
                ),
                Field(
                    'country',
                    placeholder=_('Country'),
                    data_plugin='select2',
                    data_option='{}',
                    style="width:100%",
                    wrapper_class='col-md-6',
                ),
                Field('zip', placeholder=_('If relevant'), wrapper_class='col-md-6'),
                Field('po_box', wrapper_class='col-md-6'),
                Field(
                    'phone_number',
                    placeholder=_('Phone number'),
                    wrapper_class='col-md-6',
                ),
                css_class='form-row',
            ),
            Div(
                HTML('<h6 class="col-md-12 mt-3">Other details</h6>'),
                Field(
                    'size',
                    data_plugin='select2',
                    data_option='{}',
                    style="width:100%",
                    data_minimum_results_for_search='Infinity',
                    wrapper_class='col-md-6',
                ),
                Field(
                    'annual_expenditure',
                    data_plugin='select2',
                    data_option='{}',
                    style="width:100%",
                    data_minimum_results_for_search='Infinity',
                    wrapper_class='col-md-6',
                ),
                Field(
                    'landmark',
                    placeholder=_('To help visitors find your physical location'),
                    wrapper_class='col-md-6'
                ),

                Field(
                    'website',
                    placeholder=_('http://examplesite.com'),
                    wrapper_class='col-md-6'
                ),
                Field(
                    'social_media',
                    placeholder=_('Blog, Facebook, Twitter'),
                    wrapper_class='col-md-6'
                ),
                Field(
                    'other_social_media',
                    placeholder=_('Blog, Facebook, Twitter'),
                    wrapper_class='col-md-6'
                ),
                Field(
                    'biography',
                    placeholder=_('Describe your organization'),
                    wrapper_class='col-md-12'
                ),
                css_class='form-row',
            )
        )


class OrganisationRegisterForm(OrganisationForm):
    terms_of_service = forms.BooleanField()
    privacy_policy = forms.BooleanField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not settings.DISABLE_RECAPTCHA:
            self.fields['captcha'] = ReCaptchaField(label='')
            self.helper.layout.append(
                Div(
                    Field(
                        'captcha',
                        template='crispy/captcha.html',
                        wrapper_class='col-md-12 d-flex justify-content-center',
                    ),
                    css_class='form-row',
                ),
            )

        self.helper.layout.append(
            Div(
                Div(
                    Div(
                        Field(
                            'terms_of_service',
                            template='registration/crispy/checkbox_field.html',
                            css_class="full left-0"
                        ),
                        HTML('''<div class='my-2'>&</div>'''),
                        Field(
                            'privacy_policy',
                            template='registration/crispy/checkbox_field.html',
                            link='privacy',
                            css_class="full left-0"
                        ),
                        css_class='text-center',
                    ),
                    css_class='mt-2 mb-4 text-sm',
                ),
            ),
        )


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.pop('autofocus', None)

        for fieldname in ['password1', 'password2']:
            self.fields[fieldname].help_text = None

    class Meta:
        fields = (
            'name',
            'email',
            'password1',
            'password2',
            'user_mobile',
            'job_role'
        )
        model = User

    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(
        Div(
            HTML('''<h6 class='text-bold col-md-12 p-3 text-center'>User Details</h6>'''),
            Field('name', placeholder=_('Name'), wrapper_class='col-md-6'),
            Field('email', placeholder=_('Email address'), wrapper_class='col-md-6'),
            Field('password1', placeholder=_('Password'), wrapper_class='col-md-6'),
            Field(
                'password2', placeholder=_('Confirm password'), wrapper_class='col-md-6'
            ),
            Field(
                'user_mobile', placeholder=_('Mobile number'), wrapper_class='col-md-6'
            ),
            Field('job_role', placeholder=_('Job role'), wrapper_class='col-md-6'),
            css_class='form-row',
        )
    )


class SignInForm(AuthenticationForm):
    class Meta:
        fields = (
            'username',
            'password'
        )
        model = User

    def __init__(self, *args, **kwargs):
        super(SignInForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.pop('autofocus', None)

    helper = FormHelper()
    helper.form_show_labels = False
    helper.layout = Layout(
        Div(
            Div(
                Field('username', placeholder=_('Email *')),
                Field('password', placeholder=_('Password *')),
            ),
            FormActions(
                StrictButton(_('Login'), type='submit', css_class='is-primary',),
                css_class="form-group"
            ),
            css_class="mx-auto w-xxl w-auto-xs pt-5 px-3 text-center"
        )
    )


class PasswordResetForm(PasswordResetFormBase):
    class Meta:
        fields = (
            'email'
        )
        model = User

    helper = FormHelper()
    helper.form_show_labels = False
    helper.layout = Layout(
        Field('email', placeholder=_('Email *')),
        FormActions(
            StrictButton(
                _('Send'), type='submit', css_class='is-primary btn-block p-x-md',
            ),
            css_class="form-group"
        ),
    )


class AddUserForm(forms.ModelForm):

    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('user', 'User'),
    )
    user_type = forms.ChoiceField(choices=USER_TYPE_CHOICES)

    def __init__(self, *args, **kwargs):
        super(AddUserForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.pop('autofocus', None)

    class Meta:
        fields = (
            'name',
            'email',
            'user_mobile',
            'job_role'
        )
        model = User

    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(
        Div(
            Field('name', placeholder=_('Name'), wrapper_class='col-md-6'),
            Field('email', placeholder=_('Email address'), wrapper_class='col-md-6'),
            Field(
                'user_mobile',
                placeholder=_('Mobile number'),
                wrapper_class='col-md-6',
            ),
            Field('job_role', placeholder=_('Job role'), wrapper_class='col-md-6'),
            Field(
                'user_type',
                data_plugin='select2',
                data_option='{}',
                data_minimum_results_for_search='Infinity',
                style="width:100%",
                wrapper_class='col-md-6',
            ),
            css_class='row',
        )
    )


class ProfileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.pop('autofocus', None)

    class Meta:
        fields = (
            'name',
            'email',
            'user_mobile',
            'job_role'
        )
        model = User

    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(
        Div(
            Field('name', placeholder=_('Name'), wrapper_class='col-md-6'),
            Field('email', placeholder=_('Email address'), wrapper_class='col-md-6'),
            Div(
                HTML('''
                    <a href="{% url 'change-password' %}" class='btn white'>
                        Change password
                    </a>
                '''),
                css_class='col-md-6 d-flex align-items-center my-4'
            ),
            Field(
                'user_mobile', placeholder=_('Mobile number'), wrapper_class='col-md-6'
            ),
            Field('job_role', placeholder=_('Job role'), wrapper_class='col-md-6'),
            css_class='form-row',
        )
    )


class PasswordChangeForm(PasswordChangeFormBase):
    def __init__(self, *args, **kwargs):
        super(PasswordChangeForm, self).__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.pop('autofocus', None)
