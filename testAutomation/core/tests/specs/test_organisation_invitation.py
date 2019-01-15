import pytest
from selenium.webdriver.support.select import Select

from core.tests.specs import config

GFGP_ASSESSMENT_SYSTEM = "GFGP Assessment System"


@pytest.mark.skip
def test_invite_registered_organisation_for_bronze_survey(driver,
                                                          login_user_with, logout):
    db_user = config.REGISTER_DATA
    user_email_address = db_user.get("emailAddress")
    user_password = db_user.get("password")

    login_user_with(user_email_address, user_password)
    assert GFGP_ASSESSMENT_SYSTEM in driver.title
    assert "login" in driver.current_url

    driver.find_element_by_link_text("Invitations").click()
    driver.find_element_by_link_text("New invitation").click()

    # select from list
    select_grantee = Select(driver.find_element_by_id("id_grantee"))
    print(select_grantee.options[-1].text)
    select_grantee.options[-1].click()
    # select survey
    select_survey = Select(driver.find_element_by_id("id_survey"))
    print(select_survey.options[-1].text)
    select_survey.options[-1].click()
    # select tier - todo
    # 0-Bronze,1-Silver,2-Gold,3-Platinum
    driver.find_elements_by_css_selector("label[class='ui-check w-sm']")[0].click()

    driver.find_element_by_css_selector("button[type='submit']").click()
    alert_elem = driver.find_element_by_id("alert")
    success_msg = "Invitation sent successfully"
    assert alert_elem.find_element_by_class_name("px-2").text == success_msg

    logout()


@pytest.mark.skip
def test_invite_organisation_to_register_for_survey(driver,
                                                    login_user_with, logout):
    db_user = config.REGISTER_DATA
    user_email_address = db_user.get("emailAddress")
    user_password = db_user.get("password")

    login_user_with(user_email_address, user_password)
    assert GFGP_ASSESSMENT_SYSTEM in driver.title
    assert "login" in driver.current_url

    driver.find_element_by_link_text("Invitations").click()
    driver.find_element_by_link_text("New invitation").click()

    invite_org_link = driver.find_element_by_link_text("Can't find the organization?")
    invite_org_link.click()
    driver.find_element_by_link_text("Cancel").click()
    invite_org_link.click()

    new_grantee_email_field = driver.find_element_by_id("id_grantee_email")
    new_grantee_email_field.send_keys("pavan.mansukhani@theredpandas.com")

    # select survey
    select_survey = Select(driver.find_element_by_id("id_survey"))
    print(select_survey.options[-1].text)
    select_survey.options[-1].click()
    # select tier
    # 0-Bronze,1-Silver,2-Gold,3-Platinum
    driver.find_elements_by_css_selector("label[class='ui-check w-sm']")[0].click()

    driver.find_element_by_css_selector("button[type='submit']").click()
    alert_elem = driver.find_element_by_id("alert")

    failure_msg = "Invitation failed, Email already exists"
    assert alert_elem.find_element_by_class_name("px-2").text == failure_msg


@pytest.mark.skip
def test_invite_registered_user_email_to_register_for_survey(driver,
                                                             login_user_with, logout):
    db_user = config.REGISTER_DATA
    user_email_address = db_user.get("emailAddress")
    user_password = db_user.get("password")

    login_user_with(user_email_address, user_password)
    assert GFGP_ASSESSMENT_SYSTEM in driver.title
    assert "login" in driver.current_url

    driver.find_element_by_link_text("Invitations").click()
    driver.find_element_by_link_text("New invitation").click()

    invite_org_link = driver.find_element_by_link_text("Can't find the organization?")
    invite_org_link.click()
    driver.find_element_by_link_text("Cancel").click()
    invite_org_link.click()

    new_grantee_email_field = driver.find_element_by_id("id_grantee_email")
    new_grantee_email_field.send_keys("pavanmansukhani@gmail.com")

    # select survey
    select_survey = Select(driver.find_element_by_id("id_survey"))
    print(select_survey.options[-1].text)
    select_survey.options[-1].click()
    # select tier
    # 0-Bronze,1-Silver,2-Gold,3-Platinum
    driver.find_elements_by_css_selector("label[class='ui-check w-sm']")[0].click()

    driver.find_element_by_css_selector("button[type='submit']").click()
    alert_elem = driver.find_element_by_id("alert")

    success_msg = "Invitation sent successfully"
    alert = alert_elem.find_element_by_class_name("px-2")
    assert alert.text == success_msg
