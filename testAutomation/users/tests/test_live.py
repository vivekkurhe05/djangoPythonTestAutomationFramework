import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core import signing
from django.test import tag
from rolepermissions.roles import assign_role, clear_roles
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select

from core.tests.utils import LiveTestMixin, sreenshotOnFail
from subscriptions.models import Order
from subscriptions.tests.factories import AssessmentPackageFactory, \
    AssessmentPurchaseFactory, OrderFactory, SubscriptionFactory
from surveys.tests.factories import SurveyFactory, \
    SurveyQuestionFactory, SurveySectionFactory
from users.models import Invitation, User
from .factories import UserFactory
from unittest import skip
import random
import string
from PageObjects.locators import Locators
from parameterized import parameterized


@tag("live11")
@sreenshotOnFail()
class LoginTests(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        self.browser.get(self.live_server_url)

    def test_login_as_registered_user(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'admin')
        self.login(self.user.email, self.password)
        # obj = User.objects.get(email=self.user.email)

        page_title = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("pageTitle")
        )
        self.assertEqual("Dashboard", page_title.text)
        self.assertIn("home", self.browser.current_url)
        logout = self.browser.find_element_by_link_text("Logout")
        logout.click()
        time.sleep(2)
        self.assertEqual(self.live_server_url + '/', self.browser.current_url)

    @skip("sncfds")
    def test_login_as_unregistered_user(self):
        self.login("randomusername", "randompassword")
        expected_message = "Please enter a correct Email address and password. " \
                           "Note that both fields may be case-sensitive."
        self.assertIn("login", self.browser.current_url)
        error_text = self.browser.find_element_by_id("error_notification").text
        self.assertEqual(expected_message, error_text)

    @skip("sncfds")
    def test_login_as_registered_user_with_incorrect_password(self):
        self.login(self.user.email, "randompassword")
        expected_message = "Please enter a correct Email address and password. " \
                           "Note that both fields may be case-sensitive."
        self.assertIn("login", self.browser.current_url)
        error_text = self.browser.find_element_by_id("error_notification").text
        self.assertEqual(expected_message, error_text)

    @skip("sncfds")
    def test_forgot_password_for_organisation(self):
        self.user = UserFactory.create(password=self.password)
        login_link = self.browser_wait.until(
            lambda browser: self.browser.find_elements_by_link_text("Login")[1]
        )
        self.browser.execute_script("return arguments[0].scrollIntoView();", login_link)
        login_link.click()

        self.browser_wait.until(
            EC.url_contains("login")
        )
        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Forgot password?").click()
        self.assertIn("password/reset", self.browser.current_url)

        enter_email = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("id_email")
        )
        enter_email.send_keys(self.user.email)

        self.browser_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )

        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "button[type='submit']")
        )
        submit_button.click()

        success_text = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_tag_name("h5").text
        )
        self.assertEqual(success_text, "Instructions sent successfully")

    @skip("sncfds")
    def test_user_logout_and_click_back_button(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'admin')
        self.login(self.user.email, self.password)
        self.assertIn("home", self.browser.current_url)
        logout = self.browser.find_element_by_link_text("Logout")
        logout.click()
        self.browser.implicitly_wait(30)
        self.browser.back()
        self.assertNotEquals(self.browser.current_url, "home")

    @skip("sncfds")
    def test_login_with_correct_username_and_empty_password(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'admin')
        self.login(self.user.email, '')
        self.assertIn('login', self.browser.current_url)

    @parameterized.expand([
        ("", ""),
        ("vivek@gmail.web", "admin"),
        ("abcs", "agdjewsduc"),
        ("", "admin"),
        ("", "incorrectpassword"),
        ("incorrectusername", "")
    ])
    @skip("sdhfkdsh")
    def test_login(self, username, password):
        self.login(username, password)
        self.assertNotEqual('home', self.browser.title)


@tag("live")
class RegisterTests(LiveTestMixin, StaticLiveServerTestCase):

    fixtures = [
        'organisationtypes.json',
        'default_countries.json',
    ]

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        self.browser.get(self.live_server_url)
        self.data = {'name': 'Pavan',
                     'emailAddress': 'pavan.mansukhani@theredpandas.com',
                     'password': 'admin',
                     'mobile': '8879237340',
                     'location': 'Mumbai',
                     'role': 'dev',
                     'legalName': 'Red Panda',
                     'optionalName': 'The RedPanda',
                     'parentOrg': 'RedPanda',
                     'iatiUid': '123456789',
                     'regNumber': '123456',
                     'orgIdentifier': 'redpanda',
                     'address1': '6th floor, Cerebrum',
                     'address2': 'Kalyani Nagar',
                     'city': 'Pune',
                     'province': 'Pune',
                     'country': 'India',
                     'postalCode': '400007',
                     'poBox': '112233',
                     'offPhone': '1231231234',
                     'landmark': 'Near D-Mart',
                     'website': 'https://theredpandas.com',
                     'socialMedia': 'https://theredpandas.com',
                     'otherSocialMedia': 'https://theredpandas.com'}

        self.data2 = {
            'name': '',
            'emailAddress': '',
            'password': '',
            'mobile': '',
            'location': '',
            'role': '',
            'legalName': 'Red Panda',
            'optionalName': 'The RedPanda',
            'parentOrg': 'RedPanda',
            'iatiUid': '123456789',
            'regNumber': '123456',
            'orgIdentifier': 'redpanda',
            'address1': '6th floor, Cerebrum',
            'address2': 'Kalyani Nagar',
            'city': 'Pune',
            'province': 'Pune',
            'country': 'India',
            'postalCode': '400007',
            'poBox': '112233',
            'offPhone': '1231231234',
            'landmark': 'Near D-Mart',
            'website': 'https://theredpandas.com',
            'socialMedia': 'https://theredpandas.com',
            'otherSocialMedia': 'https://theredpandas.com'
        }

        self.data3 = {
            'name': 'Pavan',
            'emailAddress': 'pavan.mansukhani@theredpandas.com',
            'password': 'admin',
            'mobile': '8879237340',
            'location': 'Mumbai',
            'role': 'dev',
            'legalName': '',
            'optionalName': '',
            'parentOrg': '',
            'iatiUid': '',
            'regNumber': '',
            'orgIdentifier': '',
            'address1': '',
            'address2': '',
            'city': '',
            'province': '',
            'country': '',
            'postalCode': '',
            'poBox': '',
            'offPhone': '',
            'landmark': '',
            'website': '',
            'socialMedia': '',
            'otherSocialMedia': ''
        }

    def test_register_as_an_organization(self):
        self.assertIn(self.title, self.browser.title)

        register_link = self.browser.find_element_by_link_text("Register")

        self.browser.execute_script(
            "return arguments[0].scrollIntoView();", register_link
        )
        register_link = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_link_text("Register")
        )
        with self.wait_for_page_load():
            register_link.click()

        self.browser_wait.until(EC.url_contains("register"))
        self.assertIn("register", self.browser.current_url)

        data = self.data
        self.fill_register_form(data, "pavan@theredpandas.com", data.get("legalName"))

        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "input[type='submit']")
        )
        submit_button.click()

        alert_elem = self.browser.find_element_by_class_name("heading")

        self.assertEquals(
            alert_elem.text,
            "Thank you for signing up"
        )

        self.browser_wait.until(
            EC.presence_of_element_located((By.LINK_TEXT, "Login here"))
        )
        login_here = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_link_text("Login here")
        )
        login_here.click()
        self.browser_wait.until(EC.url_contains("login"))

        self.assertIn("login", self.browser.current_url)

    @skip("temporarily")
    def test_register_organization_full_flow_with_login(self):
        self.assertIn(self.title, self.browser.title)

        register_link = self.browser.find_element_by_link_text("Register")
        self.browser.execute_script(
            "return arguments[0].scrollIntoView();", register_link
        )
        with self.wait_for_page_load():
            register_link.click()

        self.browser_wait.until(EC.url_contains("register"))
        self.assertIn("register", self.browser.current_url)
        data = self.data
        user_email_address = data.get("emailAddress")
        user_password = data.get("password")
        print('User Email Adress -> ', user_email_address)
        print('User Password -> ', user_password)

        self.fill_register_form(data, data.get("emailAddress"), data.get("legalName"))
        print('\nRegistration form filled')

        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "input[type='submit']")
        )
        submit_button.click()
        time.sleep(10)
        print('\nSubmit button clicked')

        alert_elem = self.browser.find_element_by_class_name("heading")

        self.assertEquals(
            alert_elem.text,
            "Thank you for signing up"
        )
        print('Thank you for signing up message printed')

        self.browser_wait.until(
            EC.presence_of_element_located((By.LINK_TEXT, "Login here"))
        )
        login_here = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_link_text("Login here")
        )
        login_here.click()
        print('\nLogin here clicked')
        self.browser_wait.until(EC.url_matches("login"))
        print('URL matches')

        self.assertIn("login", self.browser.current_url)
        print(self.browser.current_url)

        # validate email address
        db_user = User.objects.get(email=user_email_address)
        print('db_user -> ', db_user)
        print('\nOrganization', db_user.organisation)
        db_user.is_active = True
        db_user.save()
        print('db.user is saved')

        self.login(user_email_address, user_password)
        print('login function called successfully')
        self.browser.implicitly_wait(30)
        self.logout()
        self.browser.implicitly_wait(30)
        print('click on logout')
        self.browser.get(self.live_server_url)

    @skip("temporarily")
    def test_register_organization_with_already_registered_user(self):
        self.assertIn(self.title, self.browser.title)
        db_user = self.user

        register_link = self.browser.find_element_by_link_text("Register")
        self.browser.execute_script(
            "return arguments[0].scrollIntoView();", register_link
        )
        register_link.click()

        self.browser_wait.until(EC.url_contains("register"))
        self.assertIn("register", self.browser.current_url)
        data = self.data
        self.fill_register_form(data, db_user.email, data.get("legalName"))

        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "input[type='submit']")
        )
        submit_button.click()
        time.sleep(10)
        alert_element = self.browser.find_element_by_id("alert")
        alert = alert_element.find_element_by_class_name("px-2")

        self.assertEquals(alert.text, "Registration Failed, please correct the form")
        error_text = self.browser.find_element_by_id("error_1_id_email").text

        self.assertEquals(error_text, "User with this Email address already exists.")

    @skip("temporarily")
    def test_register_organization_with_already_registered_organisation(self):
        self.assertIn(self.title, self.browser.title)
        db_user = self.user
        org = db_user.organisation

        register_link = self.browser.find_element_by_link_text("Register")
        self.browser.execute_script(
            "return arguments[0].scrollIntoView();", register_link
        )
        register_link.click()

        self.browser_wait.until(EC.url_contains("register"))

        self.assertIn("register", self.browser.current_url)
        data = self.data

        self.fill_register_form(data, data.get("emailAddress"), org.legal_name)

        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "input[type='submit']")
        )
        submit_button.click()
        time.sleep(10)
        alert_element = self.browser.find_element_by_id("alert")
        alert = alert_element.find_element_by_class_name("px-2")

        self.assertEquals(alert.text, "Registration Failed, please correct the form")
        error_text = self.browser.find_element_by_id("error_1_id_legal_name").text
        self.assertEquals(error_text,
                          "Organisation with this Organization / "
                          "Legal entity already exists.")

    @skip("temporarily")
    def test_register_organization_with_already_registered_user_and_registered_organization(self):
        self.assertIn(self.title, self.browser.title)
        db_user = self.user
        org = db_user.organisation
        register_link = self.browser.find_element_by_link_text("Register")
        self.browser.execute_script(
            "return arguments[0].scrollIntoView();", register_link
        )
        register_link.click()
        self.browser_wait.until(EC.url_contains("register"))
        data = self.data
        self.fill_register_form(data, db_user.email, org.legal_name)

        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "input[type='submit']")
        )
        submit_button.click()
        time.sleep(10)
        alert_element = self.browser.find_element_by_id("alert")
        alert = alert_element.find_element_by_class_name("px-2")

        self.assertEquals(alert.text, "Registration Failed, please correct the form")
        error_text_1 = self.browser.find_element_by_id("error_1_id_email").text
        error_text_2 = self.browser.find_element_by_id("error_1_id_legal_name").text
        self.assertEquals(error_text_1, "User with this Email address already exists.")
        self.assertEquals(error_text_2,
                          "Organisation with this Organization / "
                          "Legal entity already exists.")

    @skip("temporarily")
    def test_register_organization_with_empty_user_details(self):
        self.assertIn(self.title, self.browser.title)
        register_link = self.browser.find_element_by_link_text("Register")
        self.browser.execute_script(
            "return arguments[0].scrollIntoView();", register_link
        )
        register_link.click()
        self.browser_wait.until(EC.url_contains("register"))
        data2 = self.data2
        self.fill_register_form(data2, data2.get('emailAddress'), data2.get('legalName'))
        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "input[type='submit']")
        )
        submit_button.click()
        time.sleep(1)
        self.assertEqual(self.browser.current_url, self.live_server_url+'/register/')

    @skip("temporarily")
    def test_register_with_empty_organization_details(self):
        self.assertIn(self.title, self.browser.title)
        register_link = self.browser.find_element_by_link_text("Register")
        self.browser.execute_script(
            "return arguments[0].scrollIntoView()", register_link
        )
        register_link.click()
        self.browser_wait.until(EC.url_contains("register"))
        data3 = self.data3
        self.fill_register_form(data3, data3.get('emailAddress'), data3.get('legalName'))
        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "input[type='submit']"
            )
        )
        submit_button.click()
        self.browser.implicitly_wait(30)
        self.assertEqual(self.browser.current_url, self.live_server_url + '/register/')


@sreenshotOnFail()
@tag("live")
class InvitationTests(LiveTestMixin, StaticLiveServerTestCase):
    fixtures = [
        'organisationtypes.json',
        'default_countries.json',
    ]

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'admin')

        self.grantee_user = UserFactory.create(password=self.password)
        assign_role(self.grantee_user, 'manager')

        self.survey = SurveyFactory.create()
        print("\nSurvey list is", self.survey)
        self.section4_1 = SurveySectionFactory.create(
            number=1,
        )
        print("Section 4.1 question is", self.section4_1)
        self.section4_2 = SurveySectionFactory.create(
            number=2,
        )
        print("Section 4.2 question is", self.section4_2)
        self.section4_3 = SurveySectionFactory.create(
            number=3,
        )
        print("Section 4.3 question is", self.section4_3)
        self.q1 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section4_1
        )
        print("self.q1 is", self.q1)

        self.q2 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=2,
            section=self.section4_1
        )
        print("self.q2 is", self.q2)
        self.q3 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=3,
            section=self.section4_2
        )
        print("self.q3 is", self.q3)
        self.q4 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=4,
            section=self.section4_3
        )
        print("self.q4 is", self.q4)

        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        SubscriptionFactory.create(order=order)
        package = AssessmentPackageFactory.create(
            number_included=1,
            price=900.00
        )

        AssessmentPurchaseFactory.create(
            package=package,
            order=order,
            order__organisation=self.grantor_org,
            order__status=Order.STATUS_APPROVED,
            number_included=10,
        )

        self.data = {'name': 'Pavan',
                     'emailAddress': 'pavan.mansukhani@theredpandas.com',
                     'password': 'admin',
                     'mobile': '8879237340',
                     'location': 'Mumbai',
                     'role': 'dev',
                     'legalName': 'Red Panda',
                     'optionalName': 'The RedPanda',
                     'parentOrg': 'RedPanda',
                     'iatiUid': '123456789',
                     'regNumber': '123456',
                     'orgIdentifier': 'redpanda',
                     'address1': '6th floor, Cerebrum',
                     'address2': 'Kalyani Nagar',
                     'city': 'Pune',
                     'province': 'Pune',
                     'country': 'India',
                     'postalCode': '400007',
                     'poBox': '112233',
                     'offPhone': '1231231234',
                     'landmark': 'Near D-Mart',
                     'website': 'https://theredpandas.com',
                     'socialMedia': 'https://theredpandas.com',
                     'otherSocialMedia': 'https://theredpandas.com'}

        self.browser.get(self.live_server_url)

    def test_invite_registered_organisation_for_bronze_survey(self):
        self.login(self.user.email, self.password)

        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()

        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")
        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[0].click()

        submit = self.browser.find_element_by_css_selector("button[type='submit']")
        submit.click()

        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)

        self.logout()

    def test_invite_registered_organisation_for_silver_survey(self):
        self.login(self.user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()
        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[1].click()

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)
        self.logout()

    def test_invite_registered_organisation_for_gold_survey(self):
        self.login(self.user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()
        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[2].click()

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)
        self.logout()

    def test_invite_registered_organisation_for_platinum_survey(self):
        self.login(self.user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()
        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[3].click()

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)
        self.logout()

    def test_re_invite_registered_organisation_for_silver_survey(self):
        self.login(self.user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()
        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[1].click()

        self.browser.find_element_by_css_selector("button[type='submit']").click()
        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)

        resend_btn = self.browser.find_element_by_css_selector("button.btn")
        resend_btn.click()

        resend_success_msg = "Your invite has been resent"
        alert_elem = self.browser.find_element_by_id("alert")
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text,
                      resend_success_msg)
        self.logout()

    def test_invite_and_accept_registered_organisation_for_gold_survey(self):
        self.login(self.user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()

        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[2].click()
        #
        self.browser_wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
        )

        submit = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "button[type='submit']")
        )
        submit.click()
        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)
        self.logout()
        self.login(self.grantee_user.email, self.password)
        # survey_tier = self.browser.find_element_by_class_name("badge bg-level-3")
        # locator changed
        survey_tier = self.browser.find_element_by_xpath("//span[contains(text(), 'Gold')]")
        self.assertEquals(survey_tier.text, "Gold")
        accept = self.browser_wait.until(
            lambda browser: browser.find_element_by_class_name("accept-invite-btn")
        )
        accept.click()

        self.browser_wait.until(
            lambda browser: EC.new_window_is_opened(browser.current_window_handle)
        )

        self.browser.switch_to.window(self.browser.window_handles[0])
        confirm = self.browser_wait.until(
            lambda browser: browser.find_element_by_css_selector(
                "button[type='submit']")
        )
        confirm.click()

        alert_elem = self.browser.find_element_by_id("alert")
        self.assertEquals(alert_elem.text, "Successfully accepted the invitation")

    def test_invite_new_user_for_bronze_survey(self):
        self.login(self.user.email, self.password)

        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()

        self.browser.find_element_by_link_text("Make invitation").click()

        # invite_org_link = self.browser.find_element_by_link_text(cannot_find_link)
        # submit = self.browser_wait.until(
        #     lambda browser: self.browser.find_element_by_css_selector(
        #         "button[type='submit']")
        # )

        # invite_org_link.click()

        # invite grantee by email
        cannot_find_link = "Can't find the organization?"
        invite_org_link = self.browser.find_element_by_link_text(cannot_find_link)
        self.browser.execute_script("arguments[0].click();", invite_org_link)

        new_grantee_email_field = self.browser.find_element_by_id("id_grantee_email")
        new_user_email = self.data.get("emailAddress")
        print('new_user_email ===> ', new_user_email)
        new_grantee_email_field.send_keys(new_user_email)

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[0].click()

        self.set_survey_due_date("id_due_date")

        submit = self.browser.find_element_by_css_selector("button[type='submit']")
        submit.click()
        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)
        self.logout()
        # Register the new user with the invite link
        invitation = Invitation.objects.get(grantee_email=new_user_email,
                                            grantee=None, accepted=False)

        print('invitation =====>>>> ', invitation.grantee_email)
        token = signing.dumps(invitation.id)
        print(token)
        self.browser.get(self.live_server_url + "/register/?token=" + token)
        # self.browser.get(self.live_server_url + "/register/")
        self.fill_register_form(self.data, new_user_email, self.data.get("legalName"))

        submit_button = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "input[type='submit']")
        )
        submit_button.click()

        alert_element = self.browser.find_element_by_id("alert")
        self.assertEquals(alert_element.text, "Thanks for signing up. Please login")

        self.login(new_user_email, self.data.get("password"))
        time.sleep(4)
        self.assertEquals("1", self.browser.find_element_by_class_name("badge").text)

    def test_user_cannot_re_send_invitation_to_organisation_for_same_survey(self):
        self.login(self.user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()
        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[0].click()

        self.set_survey_due_date("id_due_date")

        self.browser.find_element_by_css_selector("button[type='submit']").click()
        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)

        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[0].click()
        self.browser.find_element_by_css_selector("button[type='submit']").click()

        alert_elem = self.browser.find_element_by_id("alert")
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text,
                      "Invitation failed, please correct the form")

        error_msg = self.browser.find_element_by_id("error_1_id_grantee").text
        self.assertIn(
            "An invitation already exists for the organization "
            "with the given assessment", error_msg
        )
        self.logout()

    def test_user_cannot_send_invitation_to_its_own_organisation_email_address(self):
        user_email_address = self.user.email
        self.login(user_email_address, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()
        self.browser.find_element_by_link_text("Make invitation").click()

        # invite grantee by email
        cannot_find_link = "Can't find the organization?"
        invite_org_link = self.browser.find_element_by_link_text(cannot_find_link)
        self.browser.execute_script("arguments[0].click();", invite_org_link)
        # invite_org_link.click()

        new_grantee_email_field = self.browser.find_element_by_id("id_grantee_email")

        new_grantee_email_field.send_keys(user_email_address)

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[0].click()

        self.set_survey_due_date("id_due_date")

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        alert_elem = self.browser.find_element_by_id("alert")
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text,
                      "Invitation failed, please correct the form")

        error_msg = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id(
                "error_1_id_grantee_email"
            ).text
        )
        self.assertIn(
            "Email already registered, please select their organisation", error_msg
        )
        self.logout()

    def test_user_cannot_search_own_organisation_name_for_sending_invitation(self):
        user = self.user
        legal_name = user.organisation.legal_name
        self.login(user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()
        self.browser.find_element_by_link_text("Make invitation").click()

        # check if legal_name exists in grantee drop down
        select_grantee = Select(self.browser.find_element_by_tag_name("select"))
        time.sleep(3)
        for grantee_option in select_grantee.options:
            self.assertNotIn(legal_name, grantee_option.text)

        self.logout()

    def test_user_with_role_user_cannot_send_invitation(self):
        user = UserFactory.create(password=self.password)

        clear_roles(user)
        assign_role(user, "user")

        self.login(user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.assertNotIn("Invitations",
                         self.browser.find_element_by_id("sidenav-list").text)

        self.logout()

    def test_user_with_role_user_cannot_accept_invitation(self):
        admin_user = self.user
        assign_role(admin_user, "admin")

        user = UserFactory.create(password=self.password)
        clear_roles(user)
        assign_role(user, "user")

        self.login(admin_user.email, self.password)
        self.assertIn(self.title, self.browser.title)

        self.browser.find_element_by_link_text("Invitations").click()
        self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[0].click()

        self.set_survey_due_date("id_due_date")

        self.browser.find_element_by_css_selector("button[type='submit']").click()
        self.logout()

        self.login(user.email, self.password)
        self.assertNotIn("Accept",
                         self.browser.find_elements_by_class_name("box-body")[1].text)

        self.assertNotIn("Invitations",
                         self.browser.find_element_by_id("sidenav-list").text)

        self.logout()


@tag("live")
@sreenshotOnFail()
class DashboardTests(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        self.browser.get(self.live_server_url)

    def tearDown(self):
        self.logout()

    def test_as_a_user_role_cannot_view_menu_items_from_dashboard(self):
        assign_role(self.user, 'user')
        self.login(self.user.email, self.password)

        page_title = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("pageTitle")
        )
        self.assertEqual("Dashboard", page_title.text)
        self.assertIn("home", self.browser.current_url)

        user_menu = self.browser.find_element_by_id("sidenav-list").text

        self.assertNotIn("Invitations", user_menu)

    def test_as_a_manager_role_cannot_view_menu_items_from_dashboard(self):
        assign_role(self.user, 'manager')
        self.login(self.user.email, self.password)

        page_title = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("pageTitle")
        )
        self.assertEqual("Dashboard", page_title.text)
        self.assertIn("home", self.browser.current_url)

        manager_menu = self.browser.find_element_by_id("sidenav-list").text

        self.assertIn("Invitations", manager_menu)
        self.assertNotIn("Organization & users", manager_menu)


@tag("live")
class ProfileTests(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, "user")
        self.browser.get(self.live_server_url)
        self.login(self.user.email, self.password)

        self.updated_user_name = "Test User.."
        self.updated_job_role = "Testing.."
        self.updated_mobile = "1234567890"
        self.updated_email = "test@theredpandas.com"

    def tearDown(self):
        self.logout()

    def test_as_a_user_i_can_edit_profile_details(self):
        self.assertIn("home", self.browser.current_url)

        self.browser.find_element_by_link_text("My profile").click()
        page_title = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("pageTitle")
        )
        self.assertEqual("My profile", page_title.text)

        user_name = self.browser.find_element_by_id("id_name")
        user_name.clear()
        user_name.send_keys(self.updated_user_name)

        job_role = self.browser.find_element_by_id("id_job_role")
        job_role.clear()
        job_role.send_keys(self.updated_job_role)

        user_mobile = self.browser.find_element_by_id("id_user_mobile")
        user_mobile.clear()
        user_mobile.send_keys(self.updated_mobile)

        submit = self.browser.find_element_by_css_selector("button[type='submit']")
        submit.click()

        db_user = User.objects.get(email=self.user.email)

        self.assertEqual(db_user.name, self.updated_user_name)
        self.assertEqual(db_user.job_role, self.updated_job_role)
        self.assertEqual(db_user.user_mobile, self.updated_mobile)

    def test_as_a_user_i_can_update_my_email_address(self):
        self.assertIn("home", self.browser.current_url)

        self.browser.find_element_by_link_text("My profile").click()
        page_title = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("pageTitle")
        )
        self.assertEqual("My profile", page_title.text)

        user_id = self.user.id

        user_name = self.browser.find_element_by_id("id_name")
        user_name.clear()
        user_name.send_keys(self.updated_user_name)

        user_email = self.browser.find_element_by_id("id_email")
        user_email.clear()
        user_email.send_keys(self.updated_email)

        job_role = self.browser.find_element_by_id("id_job_role")
        job_role.clear()
        job_role.send_keys(self.updated_job_role)

        user_mobile = self.browser.find_element_by_id("id_user_mobile")
        user_mobile.clear()
        user_mobile.send_keys(self.updated_mobile)

        submit = self.browser.find_element_by_css_selector("button[type='submit']")
        submit.click()

        db_user = User.objects.get(id=user_id)

        self.assertEqual(db_user.name, self.updated_user_name)
        self.assertEqual(db_user.job_role, self.updated_job_role)
        self.assertEqual(db_user.user_mobile, self.updated_mobile)
        self.assertEqual(db_user.email, self.updated_email)

    def test_prompt_user_when_update_email_with_already_registered_email_address(self):
        updated_email = "pavan@theredpandas.com"
        UserFactory.create(email="pavan@theredpandas.com", password=self.password)

        self.assertIn("home", self.browser.current_url)

        self.browser.find_element_by_link_text("My profile").click()
        page_title = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("pageTitle")
        )
        self.assertEqual("My profile", page_title.text)

        user_name = self.browser.find_element_by_id("id_name")
        user_name.clear()
        user_name.send_keys(self.updated_user_name)

        user_email = self.browser.find_element_by_id("id_email")
        user_email.clear()
        user_email.send_keys(updated_email)

        job_role = self.browser.find_element_by_id("id_job_role")
        job_role.clear()
        job_role.send_keys(self.updated_job_role)

        submit = self.browser.find_element_by_css_selector("button[type='submit']")
        submit.click()

        submit_alert_text = "Edit profile failed, please correct the form"

        alert = self.browser.find_element_by_id("alert")
        self.assertEqual(alert.text, submit_alert_text)

        email_error = self.browser.find_element_by_id("error_1_id_email")

        validation_text = "User with this Email address already exists."
        self.assertEqual(email_error.text, validation_text)

    def test_as_a_user_i_can_change_my_password(self):
        self.assertIn("home", self.browser.current_url)

        self.browser.find_element_by_link_text("My profile").click()
        page_title = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("pageTitle")
        )
        self.assertEqual("My profile", page_title.text)

        change_password = self.browser.find_element_by_link_text("Change password")
        change_password.click()

        old_pass_field = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("id_old_password")
        )
        old_pass_field.send_keys(self.password)

        new_pass_field = self.browser.find_element_by_id("id_new_password1")
        new_pass_field.send_keys("newpassword")

        new_confirm_pass_field = self.browser.find_element_by_id("id_new_password2")
        new_confirm_pass_field.send_keys("newpassword")

        submit = self.browser.find_element_by_css_selector("input[type='submit']")
        submit.click()

        success_pass_change = "Password has been updated successfully"

        alert = self.browser.find_element_by_id("alert")
        self.assertEqual(alert.text, success_pass_change)

    def test_as_a_user_i_have_to_input_my_correct_old_pass_for_change_password(self):
        self.assertIn("home", self.browser.current_url)

        self.browser.find_element_by_link_text("My profile").click()
        page_title = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("pageTitle")
        )
        self.assertEqual("My profile", page_title.text)

        change_password = self.browser.find_element_by_link_text("Change password")
        change_password.click()

        old_pass_field = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("id_old_password")
        )
        old_pass_field.send_keys("anypassword")

        new_pass_field = self.browser.find_element_by_id("id_new_password1")
        new_pass_field.send_keys("newpassword")

        new_confirm_pass_field = self.browser.find_element_by_id("id_new_password2")
        new_confirm_pass_field.send_keys("newpassword")

        submit = self.browser.find_element_by_css_selector("input[type='submit']")
        submit.click()

        error_change_pass_form = "Please correct the form errors"

        alert = self.browser.find_element_by_id("alert")
        self.assertEqual(alert.text, error_change_pass_form)

        old_pass_error = "Your old password was entered incorrectly. " \
                         "Please enter it again."

        error_info_field = self.browser.find_element_by_id("error_1_id_old_password")
        self.assertEqual(error_info_field.text, old_pass_error)


@tag("live")
class OrganisationUsersTests(LiveTestMixin, StaticLiveServerTestCase):
    fixtures = [
        'organisationtypes.json',
        'default_countries.json',
    ]

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, "admin")
        self.browser.get(self.live_server_url)
        self.login(self.user.email, self.password)

    def tearDown(self):
        self.logout()

    def test_add_user_for_organisation_with_manager_role(self):
        self.new_user_data = {'name': 'Pavan',
                              'emailAddress': 'pavan.mansukhani@theredpandas.com',
                              'mobile': '8879237340',
                              'role': 'dev'}

        self.browser.find_element_by_link_text("Organization & users").click()
        self.browser.find_element_by_link_text("Add user").click()

        name_field = self.browser.find_element_by_id("id_name")
        name_field.send_keys(self.new_user_data['name'])

        email_field = self.browser.find_element_by_id("id_email")
        email_field.send_keys(self.new_user_data['emailAddress'])

        mobile_field = self.browser.find_element_by_id("id_user_mobile")
        mobile_field.send_keys(self.new_user_data['mobile'])

        role_field = self.browser.find_element_by_id("id_job_role")
        role_field.send_keys(self.new_user_data['role'])

        select_user_container = self.browser.find_element_by_id(
            "select2-id_user_type-container"
        )
        select_user_container.click()
        select_manager = self.browser.find_element_by_css_selector("li[id*='manager']")
        select_manager.click()

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        alert_text = self.browser.find_element_by_id("alert").text
        success_msg = "User added successfully"

        self.assertEqual(alert_text, success_msg)

    def test_edit_organisation_details_as_admin(self):
        legal_name = "New legal name"
        new_address = "Cerebrum IT park"
        new_city = "Pune"
        self.browser.find_element_by_link_text("Organization & users").click()
        self.browser.find_element_by_link_text("Edit").click()

        legal_name_field = self.browser.find_element_by_id("id_legal_name")
        legal_name_field.clear()
        legal_name_field.send_keys(legal_name)

        address_field = self.browser.find_element_by_id("id_address_1")
        address_field.clear()
        address_field.send_keys(new_address)

        city_field = self.browser.find_element_by_id("id_city")
        city_field.clear()
        city_field.send_keys(new_city)

        self.select_drop_down_element_multiple("id_types", "Other")
        self.select_drop_down_element("id_country", "id_country", 5)

        save = self.browser.find_elements_by_tag_name("button")[-1]
        save.click()

        alert_text = self.browser.find_element_by_id("alert").text
        success_msg = "Organization updated successfully"

        self.assertEqual(alert_text, success_msg)
        db_user = User.objects.get(id=self.user.id)
        db_org = db_user.organisation

        self.assertEqual(db_org.legal_name, legal_name)
        self.assertEqual(db_org.address_1, new_address)
        self.assertEqual(db_org.city, new_city)

    def test_add_already_registered_email_address_as_new_user(self):
        self.new_user_data = {'name': 'Pavan',
                              'emailAddress': 'pavan.mansukhani@theredpandas.com',
                              'mobile': '8879237340',
                              'role': 'dev'}
        UserFactory.create(email=self.new_user_data['emailAddress'],
                           password=self.password)

        self.browser.find_element_by_link_text("Organization & users").click()
        self.browser.find_element_by_link_text("Add user").click()

        name_field = self.browser.find_element_by_id("id_name")
        name_field.send_keys(self.new_user_data['name'])

        email_field = self.browser.find_element_by_id("id_email")
        email_field.send_keys(self.new_user_data['emailAddress'])

        mobile_field = self.browser.find_element_by_id("id_user_mobile")
        mobile_field.send_keys(self.new_user_data['mobile'])

        role_field = self.browser.find_element_by_id("id_job_role")
        role_field.send_keys(self.new_user_data['role'])

        select_user_container = self.browser.find_element_by_id(
            "select2-id_user_type-container"
        )
        select_user_container.click()
        select_manager = self.browser.find_element_by_css_selector("li[id*='manager']")
        select_manager.click()

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        alert_text = self.browser.find_element_by_id("alert").text

        error_msg = "Add user failed, please correct the form"
        self.assertEqual(alert_text, error_msg)

        error_text = "User with this Email address already exists."
        email_error_text = self.browser.find_element_by_id("error_1_id_email").text
        self.assertEqual(error_text, email_error_text)

    def test_modify_user_details_for_organisation_as_an_admin(self):
        new_name = "new user name"
        new_mobile_number = "1234567890"
        new_role = "test"

        self.new_user = UserFactory.create(email="abcd@abcd.com",
                                           password=self.password,
                                           organisation=self.user.organisation)
        assign_role(self.new_user, "user")

        self.browser.find_element_by_link_text("Organization & users").click()
        self.browser.find_elements_by_link_text("Edit")[-1].click()

        name_field = self.browser.find_element_by_id("id_name")
        name_field.clear()
        name_field.send_keys(new_name)

        role_field = self.browser.find_element_by_id("id_job_role")
        role_field.send_keys(new_role)

        mobile_field = self.browser.find_element_by_id("id_user_mobile")
        mobile_field.clear()
        mobile_field.send_keys(new_mobile_number)

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        alert_text = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("alert").text
        )
        success_msg = "User updated successfully"

        self.assertEqual(alert_text, success_msg)

        db_new_user = User.objects.get(id=self.new_user.id)

        self.assertEqual(db_new_user.name, new_name)
        self.assertEqual(db_new_user.user_mobile, new_mobile_number)

    def test_delete_user_details_for_organisation_as_an_admin(self):
        self.new_user = UserFactory.create(email="abcd@abcd.com",
                                           password=self.password,
                                           organisation=self.user.organisation)
        assign_role(self.new_user, "user")

        self.browser.find_element_by_link_text("Organization & users").click()
        self.browser.find_elements_by_link_text("Edit")[-1].click()

        self.browser.find_element_by_css_selector("button[type='button']").click()

        self.browser_wait.until(
            lambda browser: EC.new_window_is_opened(browser.current_window_handle)
        )

        self.browser.switch_to.window(self.browser.window_handles[0])

        self.browser_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        submit = self.browser_wait.until(
            lambda browser: browser.find_elements_by_css_selector(
                "button[type='submit']"
            )[-1]
        )
        time.sleep(0.5)
        submit.click()

        self.browser.switch_to_default_content()

        alert_text = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("alert").text
        )
        success_msg = "User successfully deleted"

        self.assertEqual(alert_text, success_msg)


@tag("live")
class LandingPageTests(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.browser.get(self.live_server_url)

    @skip("temporarily")
    def test_user_can_access_static_pages_without_login(self):
        # Before
        # about_us = self.browser.find_element_by_class_name("btn.banner-btn-aboutus")

        # After
        about_us = self.browser.find_element_by_xpath("//button[@class='btn banner-btn-aboutus is-harvest-gold']")
        about_us.click()
        self.browser_wait.until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(),'Back')]"))
        )

        self.assertIn("aboutus", self.browser.current_url)

        self.browser.find_element_by_link_text("Privacy Policy").click()
        self.browser_wait.until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(text(),'Back')]"))
        )
        self.assertIn("privacy", self.browser.current_url)


@tag("live")
class HelpAndFAQ(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'manager')
        self.browser.get(self.live_server_url)
        self.login(self.user.email, self.password)

    def tearDown(self):
        self.logout()

    def test_total_number_of_help_and_faq_questions(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_xpath(Locators.side_nav_help_and_faq)
        )
        self.assertIn('/faq/', self.browser.current_url)
        actual_total_question = len(self.browser.find_elements_by_xpath(Locators.actual_total_questions))
        self.assertEqual(20, actual_total_question)

    def test_help_and_faq_questions(self):
        expected_questions = [
                              'How do I contact the Global Grant Community?',
                              'What happens when I submit my assessment ?',
                              'What happens if I change my tier?',
                              'Can I complete the assessment at any tier?',
                              'I’ve spotted an error in the content.',
                              'I do not understand the question',
                              'How do I answer a question?',
                              'How can I make a change to my submitted assessment?',
                              'I want to see an earlier version of my assessment?',
                              'I’ve accidentally selected an answer how do I unselect it?',
                              'I can’t submit my assessment',
                              'What happens when I accept an invitation?',
                              'Do I have to complete a new assessment everytime I get a new invitation?',
                              'Why can’t I view invitations?',
                              'How do I save my assessment?',
                              'How can I view another organization’s assessment report?',
                              'I have a poor internet connection will I lose my assessment data?',
                              'How long will it take me to complete the assessment?',
                              'What browsers does the system Support?',
                              'How safe are my data and what about the new General Data Protection Regulation (GDPR)?'
                              ]
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_xpath(Locators.side_nav_help_and_faq)
        )
        self.assertIn('/faq/', self.browser.current_url)

        actual_questions_list = []
        items = self.browser.find_elements_by_xpath(Locators.actual_total_questions)
        for f in items:
            actual_questions = f.text
            actual_questions_list.append(actual_questions)
        self.assertEqual(str(expected_questions), str(actual_questions_list))

    def test_help_and_faq_answers(self):
        expected_answers_list = [
                            'You can contact us at gfgpcommunityportal@aasciences.ac.ke',
                            'We are currently exploring options to enable member to member communication within the system with plans to acquire future funding for a fully fledged online community.',
                            'When you submit your assessment all organizations, whos invitations you have accepted, will be able to see your assessment.',
                            'Changing your target tier will allow you to see your compliance and assessment completeness at a different target level. This change will be shown in your reports and will be visible to the organization(s) you are sharing your assessment with.',
                            'Yes. You can expand all tiers in the assessment and complete the questions within them. Please note they will not show in your report results unless you change your target tier.',
                            'Whilst every effort has been taken to ensure the copy is correct, mistakes can happen. We appreciate all editorial comments, please submit them to us via email (see FAQ ‘how to contact the global grant community’)',
                            'Your opinions are important to us. If a question does not make sense and you do not know how to interpret it please let us know. (see FAQ ‘how to contact the global grant community’)',
                            'Currently you can select from three response choices.',
                            'This means that to the best of your knowledge you do comply with the question being asked.',
                            'This means that you are in the progress of compliance but there are some outstanding actions that will be ready soon. You can explain these in the box provided.',
                            'This means your organization does not comply with this statement or that the statement is not applicable to your organisation. You can explain why your organization does not comply in the box provided.',
                            'In the BETA version of the portal you are working on a live version of your assessment. Any changes you make to your assessment will be visible to the organizations your assessment is shared with. You could contact the organization you are submitting your assessment to and advise them that you will be making changes.',
                            'Currently there is no history or versions of assessments available.',
                            'Select the \'clear\' button on the question to reset your response.',
                            'In BETA you are unable to select the submit button more than once. When you accept more than one invitation you automatically share your assessment data with those new organisations.',
                            'If you’ve not completed an assessment previously you will be able to complete an assessment and submit it to the inviting organization.',
                            'If you have already completed an assessment and have selected the submit button your assessment will be visible to any organizations that invite you to complete an assessment.',
                            'No. The system is designed to have one assessment per organization. Every time another organization wishes to view your assessment report you will be asked whether you wish to give your permission to the requesting organization.',
                            'Different users have different permissions. Please speak to the administrator for your organisation to update your permissions to enable you to to make and accept invitations.',
                            'Your assessment responses are automatically saved.',
                            'If you have invited an organization to complete an assessment you will need to wait for them to accept your invitation and ‘submit’ their assessment before you can view their report. If their report is already in the system, they will have to give their approval for you to view their report.',
                            'All responses are saved automatically as you answer them so if you do lose your connection your data should be up to date when you next connect.',
                            'A poor internet connection can be frustrating. We are doing everything we can to limit this, soon you will be able to print your assessment to complete offline while you wait for a good connection. We recommend waiting until you have a good internet connection to upload your documents.',
                            'We have preliminary data which indicates it takes less than 1 hour to complete all the assessment questions at the Bronze tier. Our prediction is that to complete the assessment at the Silver tier should take a total of 2.5h, Gold 4.5 and Platinum 5h.',
                            'These estimates do not include the time required to source, upload and cross reference your process, procedure or policy documents.',
                            'To streamline the process, we recommend you have all your documents on file and ready to upload when requested.',
                            'Remember, you will only have to do this once!',
                            'Internet explorer 11 and Microsoft Edge',
                            'Firefox, Safari, Chrome - The latest releases',
                            'Last 3 major iOS releases (iPhone and iPad)',
                            'Last 3 major Android releases',
                            'The portal and all your data will be hosted on the Amazon Web Services servers located in Eire.',
                            'We are working hard to ensure we shall be compliant with the requirements of GDPR when the production version goes live in Mid’18.',
                            'African Academy of Sciences has not been assessed for compliance to GDPR. The beta portal has been developed to test and refine the production / launch version of the portal. The security and privacy of your data has been a core requirement throughout the development process'
                           ]

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_xpath(Locators.side_nav_help_and_faq)
        )
        self.assertIn('/faq/', self.browser.current_url)

        actual_answers_list = []

        que_list = self.browser.find_elements_by_xpath(Locators.actual_total_questions)
        ans_list = self.browser.find_elements_by_xpath(Locators.actual_total_answers)

        for que in que_list:
            que.click()
            time.sleep(0.5)
            for ans in ans_list:
                an = ans.text
                actual_answers_list.append(an)
                actual_answers_list[:] = [item for item in actual_answers_list if item != '']
        self.assertEqual(str(expected_answers_list), str(actual_answers_list))


@tag("live")
class DirectoryTests(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        self.browser.get(self.live_server_url)
        self.implicit_wait()

    def test_func_search_organization_with_different_user_types(self):

        self.data = {'user': 'user', 'admin': 'admin', 'manager': 'manager'}
        for i in self.data:
            assign_role(self.user, self.data.get(i))
            self.login(self.user.email, self.password)
            self.click_and_wait_for_page_load(
                self.browser.find_element_by_xpath(Locators.side_nav_directory)
            )
            self.assertIn('directory', self.browser.current_url)
            self.browser.find_element_by_xpath(Locators.search_text_box).send_keys(str(self.user.organisation))
            expected_search_text = str(self.user.organisation)
            actual_search_text = self.browser.find_element_by_xpath(Locators.actual_search_text).text
            self.assertEqual(expected_search_text, actual_search_text)
            self.logout()

    def test_func_search_organization_with_different_user_types_without_case_checking(self):

        self.data = {'user': 'user', 'admin': 'admin', 'manager': 'manager'}
        for i in self.data:
            assign_role(self.user, self.data.get(i))
            self.login(self.user.email, self.password)
            self.click_and_wait_for_page_load(
                self.browser.find_element_by_xpath(Locators.side_nav_directory)
            )
            self.assertIn('directory', self.browser.current_url)
            org_name = str(self.user.organisation)
            self.browser.find_element_by_xpath(Locators.search_text_box). \
                send_keys(''.join(random.choice((x, y)) for x, y in zip(org_name.upper(), org_name.lower())))
            expected_search_text = str(self.user.organisation)
            actual_search_text = self.browser.find_element_by_xpath(Locators.actual_search_text).text
            self.assertEqual(expected_search_text, actual_search_text)
            self.logout()

    def test_func_search_organization_with_invalid_name(self):

        digits = ''.join(random.sample(string.digits, 8))
        chars = ''.join(random.sample(string.ascii_letters, 15))
        self.data = {'user': 'user', 'admin': 'admin', 'manager': 'manager'}
        for i in self.data:
            assign_role(self.user, self.data.get(i))
            self.login(self.user.email, self.password)
            self.click_and_wait_for_page_load(
                self.browser.find_element_by_xpath(Locators.side_nav_directory)
            )
            self.assertIn('directory', self.browser.current_url)
            self.browser.find_element_by_xpath(Locators.search_text_box).send_keys(digits + chars)
            expected_search_text = "No Results"
            actual_search_text = self.browser.find_element_by_xpath(Locators.no_result).text
            self.assertEqual(expected_search_text, actual_search_text)
            self.logout()

    def test_func_count_registered_organization(self):

        assign_role(self.user, 'admin')
        self.login(self.user.email, self.password)
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_xpath(Locators.side_nav_directory)
        )

        total_org = self.browser.find_elements_by_xpath(Locators.total_org_list)
        total_org_registered_count = len(total_org)
        actual_organization = \
            self.browser.find_element_by_xpath(Locators.actual_organization).text

        self.assertEqual(total_org_registered_count, int(actual_organization))
