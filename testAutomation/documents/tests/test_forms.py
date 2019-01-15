from django.test import TestCase

from ..forms import AddDocumentForm, EditDocumentForm


class TestAddDocumentForm(TestCase):
    form = AddDocumentForm

    def test_required(self):
        required_fields = {
            'name',
            'file'
        }

        form = self.form(data={})
        self.assertFalse(form.is_valid())
        self.assertLessEqual(required_fields, form.errors.keys())


class TestEditDocumentForm(TestCase):
    form = EditDocumentForm

    def test_required(self):
        required_fields = {
            'name'
        }

        form = self.form(data={})
        self.assertFalse(form.is_valid())
        self.assertLessEqual(required_fields, form.errors.keys())
