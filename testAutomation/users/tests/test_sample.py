from core.tests.utils import LiveTestMixin
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from .my_factories import UserFactory
from rolepermissions.roles import assign_role, clear_roles
from django.test import tag
import time


@tag("live111")
class LoginTest(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        self.browser.get(self.live_server_url)

    def tearDown(self):
        clear_roles(self.user)

    def test_login_as_registered_user(self):
        assign_role(self.user, 'admin')
        self.login(self.user.email, self.password)
