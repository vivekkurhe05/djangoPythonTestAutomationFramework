from django.contrib.auth.views import login
from incuna_test_utils.testcases.urls import URLTestCase

from .. import views


class TestUsers(URLTestCase):
    def test_register(self):
        self.assert_url_matches_view(
            view=views.RegisterView,
            expected_url='/register/',
            url_name='register',
        )

    def test_login(self):
        self.assert_url_matches_view(
            view=login,
            expected_url='/login/',
            url_name='login',
        )
