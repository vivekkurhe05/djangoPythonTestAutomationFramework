import json

from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Div, Field, Layout
from django import forms

from .models import Document


class AddDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = (
            'name',
            'expiry',
            'file'
        )

    helper = FormHelper()

    helper.layout = Layout(
        Div(
            Div(
                Field('name', placeholder='Type here...', css_class='mb-3 max-w-600'),
                Field(
                    'expiry', css_class='max-w-240', placeholder='dd/mm/yyyy',
                    data_plugin='datepicker',
                    data_option=json.dumps({
                        'autoclose': True,
                        'startDate': '+1d',
                        'format': 'dd/mm/yyyy'
                    })
                ),
                css_class='flex-sm mr-sm-3 w-sm-down-full'
            ),
            Div(
                Field(
                    'file',
                    template='select_file.html'
                ),
                Div(
                    StrictButton(
                        'Upload',
                        type='submit',
                        css_class='is-primary w-100 max-w-240',
                        id='submit'
                    ),
                    css_class='text-center mt-4'
                ),
                css_class='w-sm-down-full'
            ),
            css_class='d-flex align-items-start flex-column flex-sm-row'
        )
    )


class EditDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = (
            'name',
            'expiry',
        )

    helper = FormHelper()
    helper.form_tag = False
    helper.layout = Layout(
        Field('name', placeholder='Type here...', css_class='mb-3'),
        Field(
            'expiry', css_class='', placeholder='dd/mm/yyyy',
            data_plugin='datepicker',
            data_option=json.dumps({
                'autoclose': True,
                'startDate': '+1d',
                'format': 'dd/mm/yyyy'
            })
        ),
    )
