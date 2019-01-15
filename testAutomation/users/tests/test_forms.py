from django.test import TestCase

from ..forms import AddUserForm, RegisterForm, SignInForm


class TestRegisterForm(TestCase):
    form = RegisterForm

    def test_required(self):
        required_fields = {
            'name',
            'email',
            'password1',
            'password2',
            'job_role'
        }

        form = self.form(data={})
        self.assertFalse(form.is_valid())
        self.assertLessEqual(required_fields, form.errors.keys())


class TestSignInForm(TestCase):
    form = SignInForm

    def test_required(self):
        required_fields = {
            'username',
            'password'
        }
        form = self.form(data={})
        self.assertFalse(form.is_valid())
        self.assertLessEqual(required_fields, form.errors.keys())


class TestAddUserForm(TestCase):
    form = AddUserForm

    def test_required(self):
        required_fields = {
            'name',
            'email',
            'user_type',
            'job_role'
        }
        form = self.form(data={})
        self.assertFalse(form.is_valid())
        self.assertLessEqual(required_fields, form.errors.keys())
