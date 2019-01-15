import datetime
from functools import wraps
from io import BytesIO

from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from incuna_test_utils.testcases.request import BaseRequestTestCase
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import ui
from selenium.webdriver.support import expected_conditions as EC

from users.tests.factories import UserFactory

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import os
import platform


def save_screenshot(browser, name):
    filename = 'tests/screenshot-%s.png' % name
    contents = BytesIO(browser.get_screenshot_as_png())
    path = default_storage.save(filename, contents)

    print('Screenshot saved for %s' % name)
    try:
        fullpath = default_storage.path(path)
    except NotImplementedError:
        pass
    else:
        print('  Path: %s' % fullpath)
    try:
        url = default_storage.url(path)
    except NotImplementedError:
        pass
    else:
        print('  URL: %s' % url)


def sreenshotOnFail(browser_attr='browser'):
    """
    Take a screenshot whenever a test fails.

    Wrap every method on a class that starts test_ with a wrapper that takes a
    screenshot if the method raises and Exception. The browser_attr is used to
    tell the decorator how to obtain the web browser (driver)

    Usage:
        @sreenshotOnFail()
        class TestDemo(unittest.TestCase):
            def setUp(self):
                self.browser = webdriver.Firefox()

            def test_demo2(self):
                self.driver.get("https://stackoverflow.com")
                self.assertEqual(True, False)
    """
    def decorator(cls):
        def wrap(fn):
            @wraps(fn)
            def wrapper(self, *args, **kwargs):
                """Call the wrapped function and take a screenshot if it fails."""
                try:
                    return fn(self, *args, **kwargs)
                except Exception:
                    # This will only be reached if the test fails
                    name = '%s.%s' % (self.__class__.__name__, fn.__name__)
                    browser = getattr(self, browser_attr)
                    save_screenshot(browser, name)
                    raise
            return wrapper

        for attr, fn in cls.__dict__.items():
            if attr[:5] == 'test_' and callable(fn):
                setattr(cls, attr, wrap(fn))

        return cls
    return decorator


class AnonymouseTestMixin:
    def setUp(self):
        super().setUp()
        self.login_redirect_url = reverse('login') + '?next=/'

    def assertRedirectToLogin(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.login_redirect_url)


class RequestTestCase(BaseRequestTestCase):
    user_factory = UserFactory

    def create_request_ajax(self, *args, **kwargs):
        return self.create_request(
            *args,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            **kwargs
        )


class WaitForPageLoad:
    """
    Wait for the page to reload.

    Waits for pjax to finish OR the html element to change.
    """
    def __init__(self, browser, timeout):
        self.browser = browser
        self.timeout = timeout

    def __enter__(self):
        "Store the current html element and add a flag to track when pjax is running"
        self.old_page = self.browser.find_element_by_tag_name('html')
        self.browser.execute_script(
            """
            document.ajaxing = true;
            $(document).one('pjaxEnd', function() {document.ajaxing = false;});
            $(document).one('ajaxComplete', function() {document.ajaxing = false;});
            """
        )

    def __exit__(self, *args):
        "Wait for html element to change or ajaxing to stop"
        oldId = self.old_page.id
        wait = ui.WebDriverWait(self.browser, self.timeout)

        try:
            wait.until(lambda browser: (
                (browser.find_element_by_tag_name('html').id != oldId) or
                not browser.execute_script('return document.ajaxing')
            ))
        except Exception as e:
            pass


class LiveTestMixin:
    title = "GFGP Assessment System"
    password = 'secret'
    time_to_wait_in_secs = 15

    def wait_for_page_load(self, timeout=time_to_wait_in_secs):
        """
        Wait for page load to complete while some code is run.

        Usage:
            with self.wait_for_page_load():
                self.browser.find_element_by_link_text("Dashboard").click()
        """
        return WaitForPageLoad(self.browser, timeout)

    def click_and_wait_for_page_load(self, element, timeout=time_to_wait_in_secs):
        "Helper method to click element and then wait for the page to re load"
        with self.wait_for_page_load(timeout):
            element.click()

    def blur(self):
        self.browser.execute_script(
            'if (document.activeElement) {document.activeElement.blur();}',
        )

    @classmethod
    def setUpClass(cls):
        cls.get_browser(cls, 'chrome')
        cls.browser_wait = ui.WebDriverWait(cls.browser, cls.time_to_wait_in_secs)
        cls.browser.implicitly_wait(cls.time_to_wait_in_secs)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def get_browser(self, browser_name):
        if platform.system() == 'Linux':
            if browser_name.casefold() == 'chrome':
                options = webdriver.ChromeOptions()
                options.add_argument("--start-maximized")
                self.browser = webdriver.Chrome(executable_path=os.getcwd() + "/drivers_linux/chromedriver", chrome_options=options)
            elif browser_name.casefold() == 'firefox':
                self.browser = webdriver.Firefox(executable_path=os.getcwd() + "/drivers_linux/geckodriver")
            elif browser_name.casefold() == 'headless':
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--start-maximized")
                self.browser = webdriver.Chrome(
                    executable_path=os.getcwd() + "/drivers_linux/chromedriver",
                    chrome_options=chrome_options)

    def login(self, username, password):
        self.browser.get(self.live_server_url)
        self.assertIn(self.title, self.browser.title)

        login_link = self.browser_wait.until(
            lambda browser: self.browser.find_elements_by_link_text("Login")[1]
        )
        self.browser.execute_script("return arguments[0].scrollIntoView();", login_link)
        login_link.click()
        # self.browser_wait.until(EC.url_changes)
        self.browser_wait.until(
            EC.url_contains("login")
        )

        self.assertIn("login", self.browser.current_url)

        user_field = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("id_username")
        )
        user_field.send_keys(username)
        user_password = self.browser.find_element_by_id("id_password")
        user_password.send_keys(password)
        login_button = self.browser.find_element_by_css_selector("button[type='submit']")
        login_button.click()

    def logout(self):
        self.browser_wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Logout"))
        ).click()

    def select_drop_down_for_invitation(self, elem):
        org_type_select = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id(
                "select2-id_%s-container" % elem
            )
        )
        org_type_select.click()
        self.browser.find_elements_by_css_selector("li[id*='%s']" % elem)[-1].click()

    def select_drop_down_element(self, elem_id, drop_down_id, drop_down_index):
        org_type_select = self.browser.find_element_by_id(
            "select2-%s-container" % elem_id,
        )
        org_type_select.click()
        drop_down = self.browser.find_elements_by_css_selector(
            "[id^='select2-%s-result']" % drop_down_id)[drop_down_index]
        drop_down.click()

    def select_drop_down_element_multiple(self, elem_id, text):
        select = self.browser.find_element_by_id(elem_id)
        select2 = select.find_element_by_xpath('following-sibling::*[1]')
        select2.click()

        input = self.browser.find_element_by_css_selector('input[type=search]')
        input.send_keys(text)
        input.send_keys(Keys.RETURN)

    def fill_register_form(self, data, email, legal_name):
        self.populate_element_by_id("id_name", data.get("name"))
        self.populate_element_by_id("id_email", email)
        self.populate_element_by_id("id_password1", data.get("password"))
        self.populate_element_by_id("id_password2", data.get("password"))
        self.populate_element_by_id("id_user_mobile", data.get("mobile"))
        self.populate_element_by_id("id_job_role", data.get("role"))
        self.populate_element_by_id("id_legal_name", legal_name)
        self.populate_element_by_id("id_acronym", data.get("optionalName"))
        self.populate_element_by_id("id_known_as", data.get("optionalName"))
        self.populate_element_by_id("id_parent_organisation", data.get("parentOrg"))

        self.select_drop_down_element_multiple('id_types', 'Other')
        self.populate_element_by_id("id_iati_uid", data.get("iatiUid"))
        self.populate_element_by_id("id_registration_number", data.get("regNumber"))
        self.populate_element_by_id("id_address_1", data.get("address1"))
        self.populate_element_by_id("id_address_2", data.get("address2"))
        self.populate_element_by_id("id_city", data.get("city"))
        self.populate_element_by_id("id_province", data.get("province"))

        self.select_drop_down_element("id_country", "id_country", 2)
        self.populate_element_by_id("id_zip", data.get("postalCode"))
        self.populate_element_by_id("id_po_box", data.get("poBox"))
        self.populate_element_by_id("id_phone_number", data.get("offPhone"))
        self.populate_element_by_id("id_landmark", data.get("landmark"))
        self.populate_element_by_id("id_website", data.get("website"))
        self.populate_element_by_id("id_social_media", data.get("socialMedia"))
        self.populate_element_by_id("id_other_social_media", data.get("otherSocialMedia"))

        self.browser.find_element_by_id("id_terms_of_service").click()
        self.browser.find_element_by_id("id_privacy_policy").click()

    def populate_element_by_id(self, elem_id, text_to_write):
        self.browser.find_element_by_id(elem_id).send_keys(text_to_write)

    def set_survey_due_date(self, id_due_date):
        next_day_date = self.get_next_date()
        due_date = self.browser.find_element_by_id(id_due_date)
        due_date.send_keys(next_day_date)

    def get_next_date(self):
        now = datetime.date.today()
        tomorrow_date_time = now + + datetime.timedelta(days=1)
        next_day_date = tomorrow_date_time.strftime("%d/%m/%Y")
        return next_day_date

    def implicit_wait(self, time_in_secs=30):
        self.browser.implicitly_wait(time_in_secs)

    def click_button(self, ele):
        self.browser.execute_script("arguments[0].click();", ele)

    def pick_a_date(self, id_due_date):
        next_day_date = self.get_next_date()
        due_date = self.browser.find_element_by_css_selector(id_due_date)
        due_date.send_keys(next_day_date)
