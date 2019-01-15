import os
from urllib.parse import urlparse

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.utils import timezone
from rolepermissions.roles import assign_role
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from core.tests.utils import LiveTestMixin, sreenshotOnFail
from documents.models import Document
from documents.tests.factories import DocumentFactory
from subscriptions.models import Order
from subscriptions.tests.factories import AssessmentPackageFactory, \
    AssessmentPurchaseFactory, OrderFactory, SubscriptionFactory
from surveys.models import SurveyAnswerDocument
from surveys.tests.factories import SurveyAnswerFactory, SurveyFactory, \
    SurveyQuestionFactory, SurveyResponseFactory, SurveySectionFactory
from users.tests.factories import InvitationFactory, UserFactory
from unittest import skip
import time
from unittest import skip


UPLOAD_FILE_PATH = os.path.join(os.path.dirname(__file__), 'test_file.txt')


@tag("live")
@sreenshotOnFail()
class AssessmentTests(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'manager')

        self.survey = SurveyFactory.create()

        self.section4_1 = SurveySectionFactory.create(
            number=1,
        )

        self.section4_2 = SurveySectionFactory.create(
            number=2,
        )

        self.section4_3 = SurveySectionFactory.create(
            number=3,
        )

        self.q1 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section4_1
        )

        self.q2 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=2,
            section=self.section4_1
        )
        self.q3 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=2,
            section=self.section4_1
        )

        self.q4 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=3,
            section=self.section4_2
        )
        self.q5 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=4,
            section=self.section4_3
        )

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

        self.login(self.user.email, self.password)
        self.assertIn(self.title, self.browser.title)

    def tearDown(self):
        self.logout()

    @skip("temporarily")
    def test_invite_registered_grantee_from_assessments_shared_tier_gold(self):
        self.grantee = UserFactory.create(password=self.password)
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Invite grantee"),
        )

        self.select_drop_down_for_invitation("grantee")

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[2].click()

        self.set_survey_due_date("id_due_date")

        submit = self.browser.find_element_by_css_selector("button[type='submit']")
        self.click_and_wait_for_page_load(submit)
        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)

    @skip("temporarily")
    def test_invite_unregistered_grantee_from_assessments_shared_tier_bronze(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Invite grantee"),
        )

        # invite grantee by email
        cannot_find_link = "Can't find the organization?"
        invite_org_link = self.browser.find_element_by_link_text(cannot_find_link)
        invite_org_link.click()

        new_grantee_email_field = self.browser.find_element_by_id("id_grantee_email")
        new_user_email = "pavan.mansukhani@theredpandas.com"
        new_grantee_email_field.send_keys(new_user_email)

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']",
        )
        tiers[0].click()

        self.set_survey_due_date("id_due_date")

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_css_selector("button[type='submit']"),
        )
        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)

    @skip("temporarily")
    def test_invite_unregistered_grantee_from_assessments_shared_tier_silver(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Invite grantee"),
        )

        # invite grantee by email
        cannot_find_link = "Can't find the organization?"
        invite_org_link = self.browser.find_element_by_link_text(cannot_find_link)
        invite_org_link.click()

        new_grantee_email_field = self.browser.find_element_by_id("id_grantee_email")
        new_user_email = "pavan.mansukhani@theredpandas.com"
        new_grantee_email_field.send_keys(new_user_email)

        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[1].click()

        self.set_survey_due_date("id_due_date")

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_css_selector("button[type='submit']"),
        )
        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)

    @skip("temporarily")
    def test_invite_unregistered_grantee_from_assessments_shared_tier_gold(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Invite grantee"),
        )

        # invite grantee by email
        cannot_find_link = "Can't find the organization?"
        invite_org_link = self.browser.find_element_by_link_text(cannot_find_link)
        invite_org_link.click()

        new_user_email = "pavan.mansukhani@theredpandas.com"
        new_grantee_email_field = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("id_grantee_email")
        )
        new_grantee_email_field.send_keys(new_user_email)
        # select survey
        self.select_drop_down_for_invitation("survey")

        # select tier
        # 0-Bronze,1-Silver,2-Gold,3-Platinum
        tiers = self.browser.find_elements_by_css_selector(
            "label[class='ui-check w-sm']")
        tiers[2].click()

        self.set_survey_due_date("id_due_date")

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_css_selector("button[type='submit']"),
        )
        alert_elem = self.browser.find_element_by_id("alert")
        success_msg = "Invitation sent successfully"
        self.assertIn(alert_elem.find_element_by_class_name("px-2").text, success_msg)

    def test_start_assessment_from_dashboard_with_bronze_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Get started…"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )

        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])
        # next
        next_section = self.browser.find_element_by_link_text("Next")
        self.click_and_wait_for_page_load(next_section)

        # View Summary
        self.browser_wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "View summary"))
        )

        save = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_link_text("View summary")
        )
        self.click_and_wait_for_page_load(save)

        self.assertEquals(
            self.browser_wait.until(
                lambda browser: self.browser.find_element_by_class_name("badge").text
            ), "Bronze"
        )

        self.browser_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".number._700"))
        )

        completion_percentage = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(".number._700")
        )

        self.assertEquals(completion_percentage.text, "100%")

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Dashboard"),
        )

        self.assertEquals(
            self.browser_wait.until(
                lambda browser: self.browser.find_element_by_class_name(
                    "text-capitalize").text
            ), "Bronze"
        )

    @skip("temporarily")
    def test_start_assessment_from_assessments_shared_with_bronze_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        self.assertEqual(
            self.browser_wait.until(
                lambda browser: self.browser.find_element_by_class_name(
                    "badge").text
            ), "Bronze"
        )

        completion_percentage = self.browser.find_element_by_css_selector(".number._700")
        self.assertEqual(completion_percentage.text, "100%")

        tier = self.browser.find_element_by_class_name("text-capitalize")
        self.assertEqual(tier.text, "Bronze")

    @skip("temporarily")
    def test_start_assessment_from_assessments_shared_with_gold_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        change = self.browser_wait.until(
            EC.element_to_be_clickable((By.CLASS_NAME, "d-print-none"))
        )
        change.click()

        change_container = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("select2-id_level-container")
        )
        change_container.click()
        # 0-Bronze, 1-Silver, 2-Gold, 3-Platinum
        tiers = self.browser.find_elements_by_css_selector("li[id^='select2-id_level']")
        self.click_and_wait_for_page_load(tiers[2])

        tier_badge = self.browser_wait.until(
            EC.visibility_of(
                self.browser.find_element_by_class_name("badge")
            )
        )
        self.assertEqual(tier_badge.text, "Gold")

        next_section = self.browser.find_element_by_link_text("Next")
        self.click_and_wait_for_page_load(next_section)

        gold_level = self.browser.find_element_by_id("level_3")
        question_area3 = gold_level.find_element_by_class_name("js-answer-value")
        qs4 = question_area3.find_elements_by_css_selector("label[class='ui-check']")

        self.click_and_wait_for_page_load(qs4[2])
        explanation_text = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "textarea[id*='explanation']")
        )
        explanation_input = "Test: Not Applicable for Gold Survey."
        with self.wait_for_page_load():
            explanation_text.send_keys(explanation_input)
            self.blur()

        # View Summary
        save = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_link_text("View summary")
        )
        self.click_and_wait_for_page_load(save)

        tier = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_class_name("badge")
        )

        self.assertEquals(tier.text, "Gold")
        completion_percentage = self.browser_wait.until(
            EC.visibility_of(
                self.browser.find_element_by_class_name("number")
            )
        )

        self.assertEquals(completion_percentage.text, "25")

    @skip("temporarily")
    def test_start_edit_assessment_from_assessments_shared_with_platinum_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        self.browser.find_element_by_class_name("d-print-none").click()

        self.browser_wait.until(
            EC.element_to_be_clickable((By.ID, "select2-id_level-container"))
        )
        self.browser.find_element_by_id("select2-id_level-container").click()

        # 0-Bronze, 1-Silver, 2-Gold, 3-Platinum
        tiers = self.browser.find_elements_by_css_selector("li[id^='select2-id_level']")
        self.click_and_wait_for_page_load(tiers[3])

        badge = self.browser_wait.until(
            lambda browser: browser.find_element_by_class_name("badge")
        )
        self.assertEqual(badge.text, "Platinum")

        self.browser_wait.until(EC.presence_of_element_located((By.ID, "level_1")))

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = self.browser_wait.until(
            lambda browser: bronze_level.find_element_by_class_name("js-answer-value")
        )
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        silver_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_2")
        )
        silver_level.find_element_by_class_name("js-answer-value")
        questions_area2 = self.browser_wait.until(
            lambda browser: silver_level.find_elements_by_class_name("js-answer-value")
        )
        qs2 = questions_area2[0].find_elements_by_css_selector("label[class='ui-check']")
        qs3 = questions_area2[1].find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs2[0])
        self.click_and_wait_for_page_load(qs3[2])
        explanation_text = self.browser_wait.until(
            lambda browser: self.browser.find_elements_by_css_selector(
                "textarea[id*='explanation']")
        )
        with self.wait_for_page_load():
            explanation_text[-1].send_keys("Test: Not Applicable for Silver Survey.")
            self.blur()

        # next_form
        next_section = self.browser.find_element_by_link_text("Next")
        self.click_and_wait_for_page_load(next_section)

        self.browser_wait.until(
            EC.presence_of_element_located((By.ID, "level_3"))
        )

        gold_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_3")
        )
        question_area3 = self.browser_wait.until(
            lambda browser: gold_level.find_element_by_class_name("js-answer-value")
        )
        qs4 = question_area3.find_elements_by_css_selector("label[class='ui-check']")

        self.click_and_wait_for_page_load(qs4[2])
        explanation_text = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "textarea[id*='explanation']")
        )
        with self.wait_for_page_load():
            explanation_text.send_keys("Test: Not Applicable for Gold Survey.")
            self.blur()

        # next_form
        next_section = self.browser.find_element_by_link_text("Next")
        self.click_and_wait_for_page_load(next_section)
        self.browser_wait.until(
            EC.presence_of_element_located((By.ID, "level_4"))
        )

        question_area4 = self.browser_wait.until(
            lambda browser:
            browser.find_element_by_id("level_4").find_element_by_class_name(
                "js-answer-value"
            )
        )
        qs5 = question_area4.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs5[2])
        explanation_text = self.browser.find_element_by_css_selector(
            "textarea[id*='explanation']")
        with self.wait_for_page_load():
            explanation_text.send_keys("Test: Not Applicable for Platinum Survey.")
            self.blur()

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        tier = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_class_name("badge")
        )
        self.assertEquals(tier.text, "Platinum")

        self.assertEquals(
            self.browser_wait.until(
                lambda browser: browser.find_element_by_css_selector(".number._700").text
            ), "100%"
        )

    @skip("temporarily")
    def test_check_assessment_compliance_report_with_bronze_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser.find_element_by_id("level_1")
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)
        self.browser_wait.until(EC.presence_of_element_located((By.CLASS_NAME, "badge")))

        self.assertEqual(
            self.browser_wait.until(
                lambda browser: browser.find_element_by_class_name("badge").text
            ), "Bronze"
        )
        completion_percentage = self.browser.find_element_by_css_selector(".number._700")
        percentage = "100%"
        self.assertEqual(completion_percentage.text, "%s" % percentage)

        compliance_elem = self.browser_wait.until(
            lambda browser: browser.find_element_by_link_text("Compliance")
        )
        self.click_and_wait_for_page_load(compliance_elem)

        text_present = "compliant with the Bronze tier"
        compliant_msg = (percentage + " " + text_present)
        box_elements = self.browser_wait.until(
            lambda browser: self.browser.find_elements_by_class_name("d-print-row")
        )
        self.assertIn(compliant_msg, box_elements[-1].text)

    @skip("temporarily")
    def test_check_assessment_completion_report_with_bronze_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        self.browser_wait.until(EC.url_contains("progress"))

        self.assertEqual(
            self.browser_wait.until(
                lambda browser: browser.find_element_by_class_name("badge").text
            ), "Bronze"
        )

        completion_percentage = self.browser.find_element_by_css_selector(
            ".number._700"
        )
        percentage = "100%"
        self.assertEqual(completion_percentage.text, "%s" % percentage)

        completion = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_link_text("Completion")
        )
        self.click_and_wait_for_page_load(completion)

        self.browser_wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "box-body"))
        )

        completion_msg = ("completed " + percentage + " of the Bronze tier")
        box_elements = self.browser.find_elements_by_class_name("box-body")
        self.assertIn(completion_msg, box_elements[1].text)

    @skip("temporarily")
    def test_attach_document_for_assessment_survey_with_bronze_tier(self):

        self.q1.upload_type = 'policy'
        self.q1.save()
        self.document = DocumentFactory.create(
            organisation=self.user.organisation,
        )

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        qs1[0].click()

        self.browser.find_element_by_css_selector(
            "span[id*='attach_document']"
        ).click()

        attach_doc = self.browser_wait.until(
            lambda browser: browser.find_element_by_css_selector(
                "li[id*='attach_document-result']"
            )
        )
        attach_doc.click()

        doc_explanation_text = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "textarea[id*='attach_explanation']")
        )
        doc_explanation_input = "Test for Survey."
        doc_explanation_text.send_keys(doc_explanation_input)

        attach = self.browser.find_element_by_css_selector(
            "button[value='attach_document']"
        )
        self.click_and_wait_for_page_load(attach)

        self.browser_wait.until(
            EC.visibility_of(self.browser.find_element_by_tag_name("button"))
        )

        # View Summary
        save = self.browser_wait.until(
            lambda browser: browser.find_element_by_link_text("View summary")
        )
        self.click_and_wait_for_page_load(save)

        self.browser_wait.until(EC.presence_of_element_located((By.CLASS_NAME, "badge")))

        self.assertEqual(
            self.browser_wait.until(
                lambda browser: browser.find_element_by_class_name("badge").text
            ), "Bronze"
        )
        percentage = "100%"
        self.browser_wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".number._700"))
        )

        completion_percentage_text = self.browser_wait.until(
            lambda browser: browser.find_element_by_css_selector(".number._700").text
        )
        self.assertEqual(completion_percentage_text, "%s" % percentage)

    @skip("temporarily")
    def test_user_cannot_submit_incomplete_assessment(self):
        self.section_2_question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section4_2
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        # # next
        # next_section = self.browser.find_element_by_link_text("Next")
        # next_section.click()

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        self.assertEqual(
            self.browser_wait.until(
                lambda browser: self.browser.find_element_by_class_name(
                    "badge",
                ).text
            ), "Bronze"
        )

        completion_percentage = self.browser.find_element_by_css_selector(".number._700")
        self.assertEqual(completion_percentage.text, "50%")

        submit = self.browser.find_element_by_class_name(
            "btn.is-sec-action.ml-1.d-print-none"
        )
        self.assertFalse(submit.is_enabled())

    @skip("temporarily")
    def test_user_info_when_there_are_no_questions_left_for_section(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        # next_section
        next_section = self.browser.find_element_by_link_text("Next")
        self.click_and_wait_for_page_load(next_section)

        info_msg = "There are no bronze tier questions for this section."
        bronze_level_section_2 = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("level_1")
        )

        self.assertEqual(info_msg, bronze_level_section_2.text)

    @skip("temporarily")
    def test_inform_user_to_select_document_for_assessment_survey(self):
        new_question = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section4_1,
            upload_type='policy'
        )

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        selector = '[data-question="%s"] label[class="ui-check"]' % new_question.pk
        qs1 = question_area.find_elements_by_css_selector(selector)
        self.click_and_wait_for_page_load(qs1[0])

        info_msg = (
            "You need to attach at least one document, "
            "if you do not have a document available please select in progress "
            "and come back to this question later"
        )

        validation_error_field = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_class_name("invalid-feedback")
        )
        self.assertEqual(info_msg, validation_error_field.text)

    @skip("temporarily")
    def test_submit_complete_assessment_with_bronze_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        # # next
        # next_section = self.browser.find_element_by_link_text("Next")
        # next_section.click()

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        self.assertEqual(
            self.browser_wait.until(
                lambda browser: self.browser.find_element_by_class_name(
                    "badge").text
            ), "Bronze"
        )

        completion_percentage = self.browser.find_element_by_css_selector(".number._700")
        self.assertEqual(completion_percentage.text, "100%")

        submit = self.browser.find_element_by_class_name(
            "btn.is-sec-action.ml-1.d-print-none"
        )
        self.assertTrue(submit.is_enabled())
        self.click_and_wait_for_page_load(submit)

        info_text_elem = self.browser_wait.until(
            lambda browser: browser.find_element_by_class_name("highlighted-sec")
        )
        submit_text = "Submitting will make this assessment and " \
                      "all of the documents associated with it available to " \
                      "any organizations that you have shared it with " \
                      "as well as any organizations you share it with " \
                      "in the future."
        self.assertEqual(info_text_elem.text, submit_text)

        submit_dialog = self.browser.find_element_by_class_name(
            "btn.btn.is-sec-action.p-x-md"
        )
        self.click_and_wait_for_page_load(submit_dialog)

    @skip("temporarily")
    def test_export_completed_assessment_with_bronze_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        # # next
        # next_section = self.browser.find_element_by_link_text("Next")
        # next_section.click()
        #
        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        self.assertEqual(
            self.browser_wait.until(
                lambda browser: self.browser.find_element_by_class_name(
                    "badge").text
            ), "Bronze"
        )

        completion_percentage = self.browser.find_element_by_css_selector(".number._700")
        self.assertEqual(completion_percentage.text, "100%")

        download = self.browser.find_element_by_link_text("Download this assessment")
        self.assertTrue(download.is_enabled())
        # download.click()

    @skip("temporarily")
    def test_verify_max_allowed_text_length_for_survey_explanation_with_bronze_tier(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[-1])
        explanation_text = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "textarea[id*='explanation']")
        )
        placeholder_text = explanation_text.get_attribute("placeholder")
        self.assertIn("150", placeholder_text)

    @skip("temporarily")
    def test_fill_assessment_survey_by_upload_new_document_with_bronze_tier(self):
        self.q1.upload_type = 'policy'
        self.q1.save()

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        self.browser.find_element_by_link_text("Upload new document").click()

        upload_file = self.browser.find_element_by_css_selector(
            "input[id*='upload_file']"
        )
        upload_file.send_keys(UPLOAD_FILE_PATH)

        upload_file_name = self.browser.find_element_by_css_selector(
            "input[id*='upload_name']"
        )

        self.browser.execute_script("return arguments[0].scrollIntoView();",
                                    upload_file_name)

        file_name = "Test file"
        upload_file_name.send_keys(file_name)

        upload_file_explanation = self.browser.find_element_by_css_selector(
            "textarea[id*='upload_explanation']"
        )
        upload_file_explanation.send_keys("Upload test file for testing..")

        upload_button = self.browser.find_element_by_css_selector(
            "button[value='upload_document']"
        )
        self.click_and_wait_for_page_load(upload_button)

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        db_doc = SurveyAnswerDocument.objects.get()
        self.assertEqual(db_doc.document.name, file_name)
        db_doc.document.file.delete()


@tag("live")
@sreenshotOnFail()
class DocumentLibraryTests(LiveTestMixin, StaticLiveServerTestCase):

    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        assign_role(self.user, 'manager')

        self.browser.get(self.live_server_url)
        self.login(self.user.email, self.password)

    def tearDown(self):
        self.logout()

    @skip("temporarily")
    def test_upload_new_document_for_assessment_survey_with_bronze_tier(self):
        self.survey = SurveyFactory.create()
        self.section1_1 = SurveySectionFactory.create(
            number=1,
        )
        self.q1 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section1_1
        )
        self.q1.upload_type = 'policy'
        self.q1.save()

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        start_assessment = self.browser_wait.until(
            lambda browser: browser.find_element_by_link_text("Start assessment")
        )
        self.click_and_wait_for_page_load(start_assessment)

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        self.browser.find_element_by_link_text("Upload new document").click()

        upload_file = self.browser.find_element_by_css_selector(
            "input[id*='upload_file']"
        )
        upload_file.send_keys(UPLOAD_FILE_PATH)

        upload_file_name = self.browser.find_element_by_css_selector(
            "input[id*='upload_name']"
        )

        self.browser.execute_script(
            "return arguments[0].scrollIntoView();",
            upload_file_name,
        )

        file_name = "Test file"
        upload_file_name.send_keys(file_name)

        upload_file_explanation = self.browser.find_element_by_css_selector(
            "textarea[id*='upload_explanation']"
        )
        upload_file_explanation.send_keys("Upload test file for testing..")

        upload_button = self.browser.find_element_by_css_selector(
            "button[value='upload_document']"
        )
        self.click_and_wait_for_page_load(upload_button)

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        db_doc = SurveyAnswerDocument.objects.get()
        self.assertEqual(db_doc.document.name, file_name)
        db_doc.document.file.delete()

    @skip("temporarily")
    def test_attach_document_from_previously_saved_in_library(self):
        self.survey = SurveyFactory.create()

        self.section1_1 = SurveySectionFactory.create(
            number=1,
        )

        self.q1 = SurveyQuestionFactory.create(
            survey=self.survey,
            level=1,
            section=self.section1_1
        )

        self.q1.upload_type = 'policy'
        self.q1.save()
        library_document_name = "library_document"
        DocumentFactory.create(
            name=library_document_name,
            organisation=self.user.organisation,
        )

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Assessments"),
        )
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Start assessment"),
        )

        bronze_level = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_id("level_1")
        )
        question_area = bronze_level.find_element_by_class_name("js-answer-value")
        qs1 = question_area.find_elements_by_css_selector("label[class='ui-check']")
        self.click_and_wait_for_page_load(qs1[0])

        with self.wait_for_page_load():
            self.browser.find_element_by_css_selector(
                "span[id*='attach_document']"
            ).click()

        attach_doc = self.browser_wait.until(
            lambda browser: browser.find_element_by_css_selector(
                "li[id*='attach_document-result']"
            )
        )
        attach_doc.click()

        doc_explanation_text = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(
                "textarea[id*='attach_explanation']")
        )
        doc_explanation_input = "Test for Survey."
        doc_explanation_text.send_keys(doc_explanation_input)

        attach = self.browser.find_element_by_css_selector(
            "button[value='attach_document']"
        )
        self.click_and_wait_for_page_load(attach)

        self.browser_wait.until(
            EC.visibility_of(self.browser.find_element_by_tag_name("button"))
        )

        # View Summary
        save = self.browser.find_element_by_link_text("View summary")
        self.click_and_wait_for_page_load(save)

        db_survey = SurveyAnswerDocument.objects.get()
        self.assertEqual(db_survey.document.name, library_document_name)

    @skip("temporarily")
    def test_uploading_a_document_in_library(self):
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Document library"),
        )
        file_name = "Test file"

        document_name = self.browser.find_element_by_id("id_name")
        document_name.send_keys(file_name)

        document_expiry = self.browser.find_element_by_id("id_expiry")
        document_expiry.send_keys(self.get_next_date())

        upload_file = self.browser.find_element_by_id("id_file")
        upload_file.send_keys(UPLOAD_FILE_PATH)

        self.click_and_wait_for_page_load(self.browser.find_element_by_id("submit"))

        success_msg = "Document uploaded successfully"
        alert = self.browser.find_element_by_id("alert")
        self.assertEqual(alert.text, success_msg)

        db_doc = Document.objects.get()
        self.assertEqual(db_doc.name, file_name)
        self.assertEqual(db_doc.file.read(), b'This is sample text')
        db_doc.file.delete()

    @skip("temporarily")
    def test_user_can_download_document_from_library(self):
        document = DocumentFactory.create(
            organisation=self.user.organisation,
            name="Test file",
        )
        print(document.name)
        print(document.organisation)
        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Document library"),
        )

        url = self.browser.find_element_by_class_name("btn.white").get_attribute('href')
        # Compare the path only to avoid issues comparing S3 session params
        self.assertEqual(urlparse(url).path, urlparse(document.file.url).path)

        document.file.delete()

    @skip("temporarily")
    def test_user_can_edit_the_name_of_uploaded_in_library(self):
        DocumentFactory.create(
            organisation=self.user.organisation,
            name="Test file",
        )

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Document library"),
        )

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_css_selector(".text-right .btn.white"),
        )

        new_file_name = "New test file name"
        edit_document_name = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("id_name")
        )
        edit_document_name.clear()
        edit_document_name.send_keys(new_file_name)

        self.browser_wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )

        submit = self.browser_wait.until(
            lambda browser: browser.find_element_by_css_selector("button[type='submit']")
        )
        self.click_and_wait_for_page_load(submit)
        success_msg = "Document updated successfully"

        alert = self.browser_wait.until(
            lambda browser: browser.find_element_by_id("alert")
        )
        self.assertEqual(alert.text, success_msg)

        db_doc = Document.objects.get()
        self.assertEqual(db_doc.name, new_file_name)
        db_doc.file.delete()


@tag("live")
class ReportsTests(LiveTestMixin, StaticLiveServerTestCase):
    def setUp(self):
        self.user = UserFactory.create(password=self.password)
        self.browser.get(self.live_server_url)

    def tearDown(self):
        self.logout()

    def test_view_submitted_assessment_report_by_grantee(self):
        self.grantee = UserFactory.create(password=self.password)
        assign_role(self.grantee, "admin")
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

        grantor_org = self.user.organisation
        order = OrderFactory.create(
            organisation=grantor_org,
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
            order__organisation=grantor_org,
            order__status=Order.STATUS_APPROVED,
            number_included=1,
        )

        self.login(self.user.email, self.password)

        self.click_and_wait_for_page_load(
            self.browser.find_element_by_link_text("Invitations"),
        )
        self.assertTrue(EC.presence_of_element_located((By.LINK_TEXT, "View")))
        view_submitted_survey = self.browser.find_element_by_link_text("View")
        self.click_and_wait_for_page_load(view_submitted_survey)

        self.assertTrue(
            self.browser_wait.until(
                lambda browser:
                browser.find_element_by_link_text("Print report").is_enabled()
            )
        )
        completion_percentage = self.browser_wait.until(
            lambda browser: self.browser.find_element_by_css_selector(".number._700")
        )
        report_header = self.browser.find_element_by_tag_name("h2").text
        self.assertEquals(completion_percentage.text, "100%")
        self.assertIn("Full report", report_header)
