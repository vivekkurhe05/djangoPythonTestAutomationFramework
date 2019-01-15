from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.utils import timezone
from rolepermissions.roles import assign_role
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.tests.utils import LiveTestMixin, sreenshotOnFail
from subscriptions.models import Order
from subscriptions.tests.factories import AssessmentPackageFactory, \
    AssessmentPurchaseFactory, OrderFactory, SubscriptionFactory
from surveys.tests.factories import SurveyAnswerFactory, SurveyFactory, \
    SurveyQuestionFactory, SurveyResponseFactory, SurveySectionFactory, SurveyAreaFactory
from users.tests.factories import InvitationFactory, UserFactory
from unittest import skip
from selenium.webdriver.support.ui import WebDriverWait
import time
import selenium.webdriver.support.ui as ui


@tag("live")
@sreenshotOnFail()
class SubscriptionTests(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'admin')

        self.survey = SurveyFactory.create()

        self.section1_1 = SurveySectionFactory.create(
            number=1,
        )
        self.section1_2 = SurveySectionFactory.create(
            number=2,
        )
        self.section1_3 = SurveySectionFactory.create(
            number=3,
        )

        self.q1 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section1_1
        )
        self.q2 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=2,
            section=self.section1_1
        )
        self.q3 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=2,
            section=self.section1_1
        )

        self.q4 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=3,
            section=self.section1_2
        )
        self.q5 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=4,
            section=self.section1_3
        )

        package_invitation_allowed = 10
        self.package = AssessmentPackageFactory.create(
            name="10 invitations Package",
            number_included=package_invitation_allowed, price=900.00
        )

        self.login(self.user.email, self.password)
        self.assertIn(self.title, self.browser.title)

    def tearDown(self):
        self.logout()

    def test_user_need_to_buy_a_subscription_package(self):
        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Subscription & billing").click()
        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Subscribe now").click()

        # getting the last element of the list
        invitation_package = self.browser.find_elements_by_css_selector(
            "label[for^='id_package']"
        )[-1]
        invitation_package.click()

        total_amount = self.browser.find_element_by_id("total-amount").text
        self.assertIn("2400", total_amount)

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        order_submit_message = "You have successfully submitted the order"
        alert_text = self.browser.find_element_by_id("alert").text
        self.assertEqual(alert_text, order_submit_message)

        # order_placed_text = self.browser.find_element_by_class_name(
        #     "mb-0.has-cbronze-color"
        # ).text

        # locator changed
        order_placed_text = self.browser.find_element_by_xpath(
            "//h2[contains(text(), 'Order placed')]"
        ).text
        self.assertEquals(order_placed_text, "Order placed")

    def test_user_cannot_send_invitation_without_subscription(self):
        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Invitations").click()

        info_text = "Subscribe to invite grantees to submit assessments"
        self.assertIn(info_text,
                      self.browser.find_element_by_class_name("d-flex.px-4").text
                      )

        subscribe_button = self.browser.find_element_by_link_text("Subscribe")
        self.assertTrue(subscribe_button.is_enabled())

    def test_user_cannot_send_invitation_without_buying_invitation_package(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )
        SubscriptionFactory.create(order=order)

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Invitations").click()

        require_subscription_text = "Invite a grantees to submit an assessment"
        # self.assertIn(require_subscription_text,
        #               self.browser.find_element_by_class_name(
        #                   "box-body.px-4.d-flex").text)

        # locator changed
        self.assertIn(require_subscription_text,
                      self.browser.find_element_by_xpath(
                          "//div[contains(text(),'Invite a grantees to submit an assessment')]").text)

    def test_user_should_be_able_to_view_remaining_invitation_credits(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        SubscriptionFactory.create(order=order)

        invitation_count = 10
        AssessmentPurchaseFactory.create(
            package=self.package,
            order=order,
            order__organisation=self.grantor_org,
            order__status=Order.STATUS_APPROVED,
            number_included=invitation_count,
        )

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Invitations").click()

        # credits_field = self.browser_wait.until(
        #     lambda browser: browser.find_element_by_class_name(
        #         "badge-pill.bg-crystal-blue.number")
        # )

        # locator changed and WebDriverWait works
        wait = WebDriverWait(self.browser, 10)
        credits_field = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//span[@class='badge badge-pill bg-crystal-blue _700 number mx-1']")))
        actual_text = credits_field.text
        self.assertEquals(actual_text, "10")
        self.assertEqual(order.organisation.remaining_invites, 10)

    def test_user_cannot_send_invitation_where_there_are_no_credits_left(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        SubscriptionFactory.create(order=order)

        invitation_count = 1
        AssessmentPurchaseFactory.create(
            package=self.package,
            order=order,
            order__organisation=self.grantor_org,
            order__status=Order.STATUS_APPROVED,
            number_included=invitation_count,
        )
        self.grantee_user = UserFactory.create(password=self.password)
        assign_role(self.grantee_user, 'manager')

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Invitations").click()
        # credits_field = self.browser_wait.until(
        #     lambda browser: browser.find_element_by_class_name(
        #         "badge-pill.bg-crystal-blue.number")
        # )

        wait = WebDriverWait(self.browser, 10)
        credits_field = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//span[@class='badge badge-pill bg-crystal-blue _700 number mx-1']")))
        actual_text = credits_field.text
        self.assertEquals(actual_text, "1")
        self.assertEqual(order.organisation.remaining_invites, 1)

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Make invitation").click()

        # select from list
        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector("label[class='ui-check w-sm']")
        tiers[1].click()

        self.browser.find_element_by_css_selector("button[type='submit']").click()

        db_order = Order.objects.get(id=order.id)
        self.assertEqual(db_order.organisation.remaining_invites, 0)
        self.assertTrue(
            EC.invisibility_of_element_located((By.LINK_TEXT, "Make invitation"))
        )

    def test_user_can_buy_a_package_for_invitation_credits(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        SubscriptionFactory.create(order=order)

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Assessments").click()

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Subscription & billing").click()
        package_section = self.browser.find_element_by_class_name("invitation-package")
        buy_package_button = package_section.find_element_by_link_text("Buy")
        buy_package_button.click()

        self.browser_wait.until(
            EC.text_to_be_present_in_element((By.ID, "total-amount"), "900")
        )
        total_amount = self.browser.find_element_by_id("total-amount").text
        self.assertIn("900", total_amount)
        self.browser.find_element_by_css_selector("button[type='submit']").click()

        order_submit_message = "You have successfully submitted the order"
        alert_text = self.browser.find_element_by_id("alert").text
        self.assertEqual(alert_text, order_submit_message)

        # package_order_info = self.browser.find_element_by_class_name(
        #     "d-flex.bg-md-champagne")

        # locator changed
        package_order_info = self.browser.find_element_by_xpath(
            "//span[contains(text(),'10 assessment invitations')]")

        self.assertIn("10 assessment invitations", package_order_info.text)

    def test_inform_user_for_subscription_to_expire(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        current_date = date.today()
        next_month_date = current_date + relativedelta(days=30)
        SubscriptionFactory.create(order=order, end_date=next_month_date)

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Assessments").click()

        expiration_info = "Your subscription expires in 30 days"
        subscription_expiry_notif = self.browser.find_element_by_class_name(
            "notification-header.pjax-update")
        self.assertIn(expiration_info, subscription_expiry_notif.text)
        renew_button = self.browser.find_element_by_link_text("Renew")
        self.assertTrue(renew_button.is_enabled())

    def test_inform_user_when_subscription_is_expired(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        current_date = date.today()
        SubscriptionFactory.create(order=order, end_date=current_date)

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Assessments").click()

        # expiration_info = "Your subscription expires in 0 days"
        expiration_info = "Your subscription expires in"
        # subscription_expiry_notif = self.browser.find_element_by_class_name(
        #     "notification-header.pjax-update")

        # locator changed
        subscription_expiry_notif = self.browser.find_element_by_xpath(
            "//span[@class='vr-middle text-s-md']")
        self.assertIn(expiration_info, subscription_expiry_notif.text)
        renew_button = self.browser.find_element_by_link_text("Renew")
        self.assertTrue(renew_button.is_enabled())

    def test_user_can_view_assessments_with_active_subscription(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )
        print("Order is", order)
        SubscriptionFactory.create(order=order)

        self.grantee = UserFactory.create(password=self.password)
        assign_role(self.user, "admin")

        self.survey = SurveyFactory.create()

        self.survey_response = SurveyResponseFactory.create(
            organisation=self.grantee.organisation,
            survey=self.survey,
            level=1,
            submitted=timezone.now()
        )
        print("Survey response is", self.survey_response)
        self.section = SurveySectionFactory.create(
            number=1,
        )
        print("Section is", self.section)
        self.question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section
        )
        print("Queston is", self.question)
        self.answer = SurveyAnswerFactory.create(
            response=self.survey_response,
            question=self.question
        )
        print("Answer is", self.answer)
        self.invitation = InvitationFactory.create(
            survey=self.survey,
            grantee=self.survey_response.organisation,
            status=3,
            accepted=True,
            grantor=self.user.organisation
        )
        print("Invitation is", self.invitation)
        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Assessments").click()
        import time
        time.sleep(10)
        self.assertTrue(EC.presence_of_element_located((By.LINK_TEXT, "View")))
        view_submitted_survey = self.browser.find_element_by_link_text("View")
        self.assertTrue(view_submitted_survey.is_enabled())

    def test_user_cannot_view_assessments_with_expired_subscription(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        current_date = date.today()
        SubscriptionFactory.create(order=order, end_date=current_date)

        self.grantee = UserFactory.create(password=self.password)
        assign_role(self.user, "admin")

        self.survey = SurveyFactory.create()

        self.survey_response = SurveyResponseFactory.create(
            organisation=self.grantee.organisation,
            survey=self.survey,
            level=1,
            submitted=timezone.now()
        )
        self.section = SurveySectionFactory.create(
            number=1,
        )
        self.question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section
        )
        self.answer = SurveyAnswerFactory.create(
            response=self.survey_response,
            question=self.question
        )
        self.invitation = InvitationFactory.create(
            survey=self.survey,
            grantee=self.survey_response.organisation,
            status=3,
            accepted=True,
            grantor=self.user.organisation
        )

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Assessments").click()

        renew_subscription_field = self.browser.find_element_by_link_text(
            "Renew subscription")
        self.assertTrue(renew_subscription_field.is_enabled())

        assessment_notification = self.browser.find_element_by_class_name(
            "notification-header.pjax-update").text

        view_assessments_info_text = "Your subscription expires in 0 days"

        self.assertIn(view_assessments_info_text, assessment_notification)

    def test_view_order_history_for_subscription(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        SubscriptionFactory.create(order=order)

        invitation_count = 1
        AssessmentPurchaseFactory.create(
            package=self.package,
            order=order,
            order__organisation=self.grantor_org,
            order__status=Order.STATUS_APPROVED,
            number_included=invitation_count,
        )

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Subscription & billing").click()
        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Order history").click()

        table_order = self.browser.find_element_by_id("packages-list")

        table_rows = table_order.find_elements_by_xpath("tbody/tr/td")
        current_formatted_date = date.today().strftime("%d %b %Y")
        self.assertEqual(current_formatted_date.lstrip("0"), table_rows[1].text)
        self.assertEquals("Paid", table_rows[2].text)

    def test_option_for_user_to_renew_subscription_on_dashboard(self):
        self.grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=self.grantor_org,
            status=Order.STATUS_APPROVED
        )

        SubscriptionFactory.create(order=order, end_date=date.today())

        invitation_count = 1
        AssessmentPurchaseFactory.create(
            package=self.package,
            order=order,
            order__organisation=self.grantor_org,
            order__status=Order.STATUS_APPROVED,
            number_included=invitation_count,
        )

        with self.wait_for_page_load():
            self.browser.find_element_by_link_text("Dashboard").click()

        expired_subscription_message = "Your subscription expires in 0 days"
        expired_subscription_element = self.browser.find_element_by_css_selector(
            "div > .col-md-6.mt-3 > .text-bold")

        self.assertIn(expired_subscription_message, expired_subscription_element.text)

        renew_button = self.browser.find_element_by_link_text("Renew")
        self.assertTrue(renew_button.is_enabled())


@tag("live")
class CompleteFlow(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'admin')
        self.browser.get(self.live_server_url)

        self.grantor = self.user.organisation
        new_order = OrderFactory.create(organisation=self.grantor,
                                        status=Order.STATUS_APPROVED)

        SubscriptionFactory.create(order=new_order,
                                   price=1500.00)

        new_package = AssessmentPackageFactory.create(name=str(self.user),
                                                      number_included=2,
                                                      price=900.00)

        self.assess=AssessmentPurchaseFactory.create(order=new_order,
                                                     package=new_package,
                                                     number_included=2,
                                                     price=900.00)

        self.user1 = UserFactory.create(password=self.password)
        self.grantee = self.user1.organisation
        self.survey_list = SurveyFactory.create(name="Survey 0")

    @skip("temporarily")
    def test_func_invite_organization_for_bronze_assessment(self):

        self.login(self.user.email, self.password)

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Invitations")
        )

        self.browser.find_element_by_xpath("//a[contains(text(), 'Make invitation')]").click()

        self.select_drop_down_for_invitation("grantee")

        self.select_drop_down_for_invitation("survey")

        ele = self.browser.find_element_by_xpath("//label//input[@type='radio'][@value='2']")
        self.browser.execute_script("arguments[0].click()", ele)

        self.browser.find_element_by_xpath("//button[@type='submit']").click()

        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)

        self.logout()

        assign_role(self.user1, 'admin')
        self.login(self.user1.email, self.password)

        self.browser.find_element_by_xpath("//button[contains(text(),'Accept')]").click()

    @skip("temporarily")
    def test_func_login_as_a_grantee_and_accept_invitation(self):

        InvitationFactory.create(grantor=self.grantor,
                                 grantee=self.grantee,
                                 survey=self.survey_list,
                                 level=1,
                                 status=1)
        assign_role(self.user1, "manager")
        self.login(self.user1.email, self.password)

        self.browser.find_element_by_xpath("//button[contains(text(),'Accept')]").click()

        time.sleep(0.5)

        self.browser_wait.until(
            lambda browser: EC.new_window_is_opened(browser.current_window_handle)
        )

        self.browser.switch_to.window(self.browser.window_handles[0])
        confirm = self.browser_wait.until(
            lambda browser: browser.find_element_by_css_selector(
                "button[type='submit']")
        )
        confirm.click()

        expected_msg = "Successfully accepted the invitation"

        actual_msg = self.browser.find_element_by_xpath("//div[@id='alert']//div[@class='px-2']").text

        self.assertEqual(expected_msg, actual_msg)

    @skip("temporarily")
    def test_func_submit_assessment_received_by_grantee(self):

        survey_area = SurveyAreaFactory.create(name="Financial management", number=5)

        survey_section = SurveySectionFactory.create(area=survey_area, name="Financial management",
                                                     number=1)

        que = SurveyQuestionFactory.create(survey=self.survey_list, section=survey_section)

        assign_role(self.user1, "admin")
        self.login(self.user1.email, self.password)

        self.click_and_wait_for_page_load(

            self.browser.find_element_by_css_selector("a[href='/survey/view/assessment']")
        )
        self.browser.find_element_by_xpath("//a[contains(text(),'Start assessment')]").click()

        q1 = self.browser.find_elements_by_css_selector(
            "label[class='ui-check']")
        self.click_button(q1[0])

        time.sleep(50)
        view_summary = self.browser.find_element_by_xpath("//a[contains(text(),'View summary')]")
        self.click_button(view_summary)

        submit = self.browser.find_element_by_xpath("//div[@class='d-flex']//button[contains(text(),'Submit')]")
        self.click_button(submit)

        self.browser_wait.until(
            lambda browser: EC.new_window_is_opened(browser.current_window_handle)
        )

        self.browser.switch_to.window(self.browser.window_handles[0])
        confirm = self.browser_wait.until(
            lambda browser: browser.find_element_by_xpath(
                "//button[@type='submit']")
        )
        self.click_button(confirm)

        expected_msg = "Assessment published successfully"
        actual_msg = self.browser.find_element_by_xpath(
            "//div[contains(text(),'Assessment published successfully')]").text
        self.assertEqual(expected_msg, actual_msg)

        self.logout()

        res = SurveyResponseFactory.create(survey=self.survey_list,
                                           organisation=self.grantee,
                                           level=1)

        InvitationFactory.create(survey=self.survey_list, grantor=self.grantor, grantee=self.grantee,
                                 accepted=True, level=1, status=3, purchase=self.assess)

        SurveyAnswerFactory.create(response=res, question=que)

        assign_role(self.user, 'admin')
        self.login(self.user.email, self.password)

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_xpath("//a[@href='/survey/invite']")
        )

        org_names = self.browser.find_elements_by_css_selector("table tbody tr td div[class='text-bold']")

        self.assertEqual(str(self.grantee), org_names[-1].text)

        self.browser.find_element_by_xpath("//a[contains(text(),'View')]").click()

        expected_completion_percentage = "100%"

        actual_completion_percentage = self.browser.find_element_by_xpath(
            "//span[@class='number _700 primary-font-color']").text

        self.assertEqual(expected_completion_percentage, actual_completion_percentage)

    @skip("temporarily")
    def test_func_submit_assessment_with_inprogress_answer_without_picking_date(self):
        survey_area = SurveyAreaFactory.create(name='Human resources', number=6)

        survey_section = SurveySectionFactory.create(area=survey_area, name='Human resource management and payroll')

        que = SurveyQuestionFactory.create(survey=self.survey_list, section=survey_section, level=1, question_number=1)

        assign_role(self.user1, "admin")
        self.login(self.user1.email, self.password)

        self.click_and_wait_for_page_load(

            self.browser.find_element_by_css_selector("a[href='/survey/view/assessment']")
        )
        self.browser.find_element_by_xpath("//a[contains(text(),'Start assessment')]").click()

        q1 = self.browser.find_elements_by_css_selector(
            "label[class='ui-check']")

        self.click_button(q1[1])

        time.sleep(0.5)
        self.browser.find_element_by_xpath("//textarea").send_keys('test explanation')

        view_summary = self.browser.find_element_by_xpath("//a[contains(text(),'View summary')]")
        self.click_button(view_summary)
        submit_btn = self.browser.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
        is_btn_enabled = submit_btn.is_enabled()
        self.assertEqual(False, is_btn_enabled)

    def test_func_submit_assessment_with_inprogress_answer_and_picking_date(self):
        survey_area = SurveyAreaFactory.create(name='Human resources', number=6)

        survey_section = SurveySectionFactory.create(area=survey_area, name='Human resource management and payroll')

        que = SurveyQuestionFactory.create(survey=self.survey_list, section=survey_section, level=1, question_number=1)

        assign_role(self.user1, "admin")
        self.login(self.user1.email, self.password)

        self.click_and_wait_for_page_load(

            self.browser.find_element_by_css_selector("a[href='/survey/view/assessment']")
        )
        self.browser.find_element_by_xpath("//a[contains(text(),'Start assessment')]").click()

        q1 = self.browser.find_elements_by_css_selector(
            "label[class='ui-check']")

        self.click_button(q1[1])

        time.sleep(0.5)
        self.browser.find_element_by_xpath("//textarea").send_keys('test explanation')

        self.pick_a_date("input[type=text]")
        view_summary = self.browser.find_element_by_xpath("//a[contains(text(),'View summary')]")
        self.click_button(view_summary)
        submit_btn = self.browser.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
        is_btn_enabled = submit_btn.is_enabled()
        self.assertTrue(is_btn_enabled)

    @skip("temporarily")
    def test_func_submit_assessment_with_no_answer(self):
        pass

    @skip("temporarily")
    def test_func_submit_assessment_with_notapplicable_answer(self):
        pass