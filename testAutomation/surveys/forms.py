import json
from datetime import date

from crispy_forms.bootstrap import FormActions, StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Button, Div, Field, HTML, Layout
from django import forms
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from documents.models import Document
from subscriptions.models import AssessmentPurchase, Order
from users.models import Invitation, Organisation, User
from .models import (
    LEVEL_CHOICES,
    Survey,
    SurveyAnswer,
    SurveyAnswerDocument,
    SurveyResponse,
)


BOOL_CHOICES = ((True, 'Yes'), (False, 'No'))


class SurveyLevelForm(forms.ModelForm):
    level_helper = FormHelper()
    level_helper.form_tag = False
    level_helper.form_show_labels = False
    level_helper.layout = Layout(
        Div(
            Field(
                'level', template='surveys/crispy/survey_level_field.html',
                data_plugin='select2', data_option='{}',
                data_minimum_results_for_search='Infinity', style="width:100%"
            ),
            id='div_id_level'
        ),
    )

    class Meta:
        model = SurveyResponse
        fields = ['level']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['level'].choices = LEVEL_CHOICES


class SurveyAnswerForm(forms.ModelForm):
    operation = forms.CharField(required=False, widget=forms.HiddenInput())

    # Make fields required based on SurveyAnswer.value
    required_if_value = {
        'explanation': [
            SurveyAnswer.ANSWER_PROGRESS,
            SurveyAnswer.ANSWER_NO,
            SurveyAnswer.ANSWER_NA
        ],
        'due_date': [SurveyAnswer.ANSWER_PROGRESS],
    }

    # Make fields required based on `operation`
    required_if_operation = {
        'attach_document': ('attach_document',),
        'upload_document': ('upload_name', 'upload_file'),
    }

    class Meta:
        model = SurveyAnswer
        fields = ['value', 'options', 'explanation', 'due_date']
        widgets = {
            'options': forms.CheckboxSelectMultiple,
            'value': forms.RadioSelect(),
            'explanation': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, question, response, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.instance.question = question
        self.instance.response = response

        value_field = self.fields['value']
        value_field.label = ''
        value_field.choices = SurveyAnswer.ANSWER_CHOICES

        options_field = self.fields['options']
        options_field.label = ''
        options_field.queryset = question.options.all()

        self.fields['due_date'].label = 'Completion date'

        # Data for jQuery to make the fields required based on selection
        data_required_on_change = {
            '#div_id_%s' % self.add_prefix(field_name): values
            for field_name, values in self.required_if_value.items()
        }

        value_field_div = Div(
            Field(
                'value',
                template='surveys/crispy/survey_radioselect.html',
                data_required_on_change=json.dumps(data_required_on_change),
            ),
            css_class='js-answer-value d-flex flex-xs-sm-down-wrap',
        )

        if self.instance.pk:
            url = reverse('survey-answer-delete', kwargs={'pk': self.instance.pk})
            value_field_div.append(
                Div(
                    Button(
                        'clear',
                        'Clear',
                        css_class='btn btn-fw white mb-3',
                        onclick="app.loadModal('{}', 'Clear answer')".format(url),
                    ),
                )
            )

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Div(
                Field('options'),
                css_class='js-answer-options mb-4',
            ),
            value_field_div,
            Div(
                Div(
                    Field('explanation', placeholder=_('Recommended maximum 150 words')),
                    css_class="flex-sm p-1",
                ),
                Div(
                    Field(
                        'due_date',
                        data_plugin='datepicker',
                        data_option=json.dumps({
                            'autoclose': True,
                            'format': 'dd/mm/yyyy',
                            'startDate': '+1d',
                        }),
                        placeholder=_('Pick a date'),
                    ),
                    css_class="p-1 conditional"
                ),
                css_class="d-flex flex-column flex-sm-row"
            ),
            Field('operation', css_class='js-operation'),
        )

        if question.upload_type:
            get_question_document_field = SurveyAnswerDocument._meta.get_field
            get_document_field = Document._meta.get_field
            documents = Document.objects.filter(organisation_id=response.organisation_id)
            self.fields.update(
                attach_document=get_question_document_field('document').formfield(
                    queryset=documents,
                    required=False,
                ),
                attach_explanation=get_question_document_field('explanation').formfield(
                    required=False,
                    widget=forms.Textarea(attrs={'rows': 4}),
                ),
                upload_name=get_document_field('name').formfield(required=False),
                upload_expiry=get_document_field('expiry').formfield(required=False),
                upload_file=get_document_field('file').formfield(required=False),
                upload_explanation=get_question_document_field('explanation').formfield(
                    required=False,
                    widget=forms.Textarea(attrs={'rows': 4}),
                ),
            )

            self.attach_helper = FormHelper()
            self.attach_helper.form_tag = False
            self.attach_helper.disable_csrf = True
            self.attach_helper.layout = Layout(
                Div(
                    Div(
                        Div(
                            Field(
                                'attach_document',
                                data_plugin='select2',
                                data_option='{}',
                                data_placeholder='Choose...',
                                style="width:100%",
                            ),
                            css_class='font-weight-normal js-attach-document-select'
                        ),
                        Div(
                            Field(
                                'attach_explanation',
                                placeholder=_(
                                    'Document name, page number, and paragraph '
                                    'reference for the reviewer '
                                    '(Recommended maximum 150 words)'
                                ),
                            ),
                            css_class="form-group",
                        ),
                        css_class='form-group width-100',
                    ),
                    Div(
                        StrictButton(
                            'Attach',
                            type='button',
                            css_class='js-operation-button is-primary w-100 max-w-240',
                            value='attach_document',
                        ),
                        css_class='text-right mt-4'
                    ),
                    css_class='align-items-start',
                )
            )
            self.upload_helper = FormHelper()
            self.upload_helper.form_tag = False
            self.upload_helper.disable_csrf = True
            self.upload_helper.layout = Layout(
                Div(
                    Div(
                        Field(
                            'upload_name',
                            placeholder='Type here...',
                            css_class='mb-3 max-w-600',
                        ),
                        Field(
                            'upload_expiry',
                            css_class='max-w-240',
                            placeholder='dd/mm/yyyy',
                            data_plugin='datepicker',
                            data_option=json.dumps({
                                'autoclose': True,
                                'startDate': '+1d',
                                'format': 'dd/mm/yyyy',
                            }),
                        ),
                        css_class='flex-sm mr-sm-3 w-sm-down-full'
                    ),
                    Div(
                        Field(
                            'upload_file',
                            template='select_file.html'
                        ),
                        css_class='w-sm-down-full'
                    ),
                    css_class='d-flex align-items-start flex-column flex-sm-row'
                ),
                Div(
                    Field(
                        'upload_explanation',
                        placeholder=_(
                            'Document name, page number, and paragraph '
                            'reference for the reviewer (Recommended maximum 150 words)'
                        ),
                    ),
                    Div(
                        StrictButton(
                            'Upload & attach',
                            type='button',
                            css_class='js-operation-button is-primary w-100 max-w-240',
                            value='upload_document',
                        ),
                        css_class='text-right mt-4'
                    ),
                ),
            )

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < date.today():
            raise forms.ValidationError("This should be in the future.")
        return due_date

    def clean(self):
        required_msg = forms.Field.default_error_messages['required']
        cleaned_data = super().clean()
        value = cleaned_data.get('value')
        for field_name, values in self.required_if_value.items():
            required = value in values
            if required and not cleaned_data.get(field_name):
                self.add_error(field_name, required_msg)

        operation = cleaned_data.get('operation')
        for field_name in self.required_if_operation.get(operation, ()):
            if not cleaned_data.get(field_name):
                self.add_error(field_name, required_msg)

        upload_type = self.instance.question.upload_type
        if not self.errors and upload_type and value == SurveyAnswer.ANSWER_YES:
            # Only make this check if there are not other errors, as they may
            # have errors relating to the upload.
            if not operation and len(self.instance.documents.all()) == 0:
                # This is not and attach or upload operation and there are no
                # existing attachments
                self.add_error(
                    'value',
                    _(
                        'You need to attach at least one document, '
                        'if you do not have a document available please select '
                        'in progress and come back to this question later'
                    ),
                )

        return cleaned_data

    def _save_m2m(self):
        super()._save_m2m()
        answer = self.instance
        cleaned_data = self.cleaned_data
        operation = cleaned_data.get('operation')

        document = None
        explanation = ''

        if operation == 'upload_document':
            explanation = cleaned_data.get('upload_explanation')
            document = Document.objects.create(
                organisation=answer.response.organisation,
                name=cleaned_data.get('upload_name'),
                file=cleaned_data.get('upload_file'),
                expiry=cleaned_data.get('upload_expiry'),
            )

        if operation == 'attach_document':
            document = cleaned_data.get('attach_document')
            explanation = cleaned_data.get('attach_explanation')

        if document:
            SurveyAnswerDocument.objects.create(
                answer=answer,
                document=document,
                explanation=explanation,
            )


class SubmitForm(forms.ModelForm):
    class Meta:
        model = SurveyResponse
        fields = []

    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(
        FormActions(
            StrictButton(
                _('Submit'),
                type='submit',
                css_class='btn is-sec-action p-x-md',
            ),
            HTML(
                """
                <button type="button" class="btn white p-x-md" data-dismiss="modal">
                    Cancel
                </button>
                """,
            ),
        )
    )

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.submitted = timezone.now()
        if commit:
            instance.save()
        return instance


class InvitationForm(forms.ModelForm):
    is_organisation_invite = forms.BooleanField(initial=True, required=False)

    class Meta:
        model = Invitation
        fields = (
            'grantee_email',
            'grantee',
            'survey',
            'level',
            'due_date',
        )

    def __init__(self, grantor, *args, **kwargs):
        self.grantor = grantor
        super().__init__(*args, **kwargs)
        self.instance.grantor = grantor
        self.fields['survey'].queryset = Survey.objects.filter(is_active=True)
        self.fields['grantee'].required = False
        self.fields['grantee_email'].required = False
        grantees = Organisation.objects.all().exclude(id=grantor.id)
        self.fields['grantee'].queryset = grantees

    def clean(self):
        cleaned_data = super(InvitationForm, self).clean()
        is_organisation_invite = cleaned_data.get('is_organisation_invite')
        if is_organisation_invite:
            cleaned_data['grantee_email'] = None
            add_error_field = 'grantee'
        else:
            cleaned_data['grantee'] = None
            add_error_field = 'grantee_email'

        if not self.grantor.active_subscription:
            message = (
                "No active subscription. Your organization needs "
                "an active subscription to make an invitations"
            )
            msg = forms.ValidationError(message)
            self.add_error(add_error_field, msg)
        elif self.grantor.remaining_invites == 0:
            message = (
                "No invitations available. Your organization needs "
                "to purchase more invitations."
            )
            msg = forms.ValidationError(message)
            self.add_error(add_error_field, msg)
        elif not cleaned_data[add_error_field]:
            msg = forms.ValidationError("This field is required.")
            self.add_error(add_error_field, msg)
        elif is_organisation_invite:
            invites_list = Invitation.objects.filter(
                grantor=self.instance.grantor,
                grantee=cleaned_data['grantee'],
                survey=cleaned_data['survey']
            )
            if(invites_list.count() > 0):
                error = '''An invitation already exists for the
                organization with the given assessment'''
                msg = forms.ValidationError(error)
                self.add_error(add_error_field, msg)
        else:
            user_list = User.objects.filter(
                email__iexact=cleaned_data['grantee_email']
            )
            if(user_list.count() > 0):
                error = "Email already registered, please select their organisation"
                msg = forms.ValidationError(error)
                self.add_error('grantee_email', msg)
        return cleaned_data

    def save(self, commit=True):
        purchase = AssessmentPurchase.objects.filter(
            order__organisation=self.grantor,
            order__status=Order.STATUS_APPROVED
        ).unused().order_by('created').first()
        self.instance.purchase = purchase
        return super().save(commit=commit)

    helper = FormHelper()
    helper.form_tag = False
    helper.form_show_labels = False

    helper.layout = Layout(
        Div(
            HTML(
                '''<h6 class="heading">1. Find an organization to invite</h6>'''
            ),
            Div(
                Div(
                    HTML('''<label>
                        Invite organization by email:</label>'''),
                    Div(
                        Field(
                            'grantee_email',
                            placeholder='Enter the organization\'s email address'
                        ),
                        css_class='max-w-600 font-weight-normal'
                    ),
                    css_class='form-group my-3',
                ),
                HTML('''<label class="link text-u-l">
                <a href="#" onClick="app.toggleInviteForm('grantee_invite_form')"
                class="invite_form_toggle">
                    Cancel
                </a>
                </label>'''),
            ),
            css_class='mb-5 grantee_invite_form'
        ),
        Div(
            HTML(
                '''<h6 class="heading">1. Find an organization to invite</h6>'''
            ),
            Div(
                Div(
                    HTML(
                        '''<label>Choose an organization:</label>'''
                    ),
                    Div(
                        Field(
                            'grantee', data_plugin='select2', data_option='{}',
                            data_placeholder='Choose...', style="width:100%"
                        ),
                        css_class='max-w-600 font-weight-normal'
                    ),
                    css_class='form-group my-3',
                ),
                HTML('''<label class="link text-u-l">
                    <a href="#" onClick="app.toggleInviteForm('org_invite_form')"
                    class="invite_form_toggle">
                    Can't find the organization?</a>
                    </label>'''),
            ),
            css_class='mb-5 org_invite_form'
        ),
        Div(
            HTML('''<h6 class="heading">2. Choose an assessment:</h6>'''),
            Div(
                HTML('''<label>Assessment type:</label>'''),
                Div(
                    Field(
                        'survey', data_plugin='select2', data_option='{}',
                        data_placeholder='Choose...', style="width:100%"
                    ),
                    css_class='max-w-600 font-weight-normal'
                ),
                Div(
                    Field('level', template="crispy/custom_inline_radio.html"),
                    css_class="mt-3"
                ),
                css_class='form-group my-3',
            ),

            HTML('''<label>The organization will be asked to submit
                this tier as a minimum.</label>'''),
            css_class="mb-5"
        ),
        Div(
            HTML('''<h6 class="heading">3. Set a completion deadline:</h6>'''),
            Div(
                HTML('''<label>Due date: (Optional)</label>'''),
            ),
            Field(
                'due_date', css_class='max-w-240', placeholder='dd/mm/yyyy',
                data_plugin='datepicker',
                data_option=json.dumps({
                    'autoclose': True,
                    'startDate': '+1d',
                    'format': 'dd/mm/yyyy'
                })
            ),
            css_class="mb-5"
        ),
        Div(
            HTML('''<h6 class="heading">4. Notify the organization</h6>'''),
            Div(
                StrictButton(
                    ('Send invitation'), type='submit', css_class='is-primary'
                ),
                HTML('''{% if user.organisation.remaining_invites  %}
                    <span class="mx-2">You have<span
                    class="badge badge-pill bg-crystal-blue _700 number mx-1">
                    {{user.organisation.remaining_invites}}</span>invitations
                    (<a href="#" class="link text-u-l text-nowrap">buy more</a>)
                    </span> {% endif %}
                '''),
                css_class='form-group my-3'
            ),
            HTML(
                '''<label>You'll be notified when the assessment is
                ready to view.</label>'''
            ),
            Div(
                Field(
                    'is_organisation_invite'
                ), css_class="d-none"
            ),
            css_class="mb-5"
        )
    )
