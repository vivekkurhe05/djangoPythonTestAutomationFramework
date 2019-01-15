import pytest

from core.tests.specs import config

GFGP_ASSESSMENT_SYSTEM = "GFGP Assessment System"


@pytest.mark.skip
def test_invite_grantee_from_assessments_shared_with_bronze_survey(driver,
                                                                   login_user_with,
                                                                   logout):
    db_user = config.REGISTER_DATA
    user_email_address = db_user.get("emailAddress")
    user_password = db_user.get("password")

    login_user_with(user_email_address, user_password)
    assert GFGP_ASSESSMENT_SYSTEM in driver.title
    assert "login" in driver.current_url
