from incuna_test_utils.testcases.urls import URLTestCase

from .. import views


class TestSurveyURLs(URLTestCase):
    def test_survey_start(self):
        self.assert_url_matches_view(
            view=views.SurveyStartView,
            expected_url='/survey/start/42',
            url_name='survey-start',
            url_kwargs={'pk': 42},
        )

    def test_survey_section(self):
        self.assert_url_matches_view(
            view=views.SurveySectionView,
            expected_url='/survey/1/2',
            url_name='survey-section',
            url_kwargs={'pk': 1, 'section': 2},
        )

    def test_survey_section_start(self):
        self.assert_url_matches_view(
            view=views.SurveySectionView,
            expected_url='/survey/1/start',
            url_name='survey-section-start',
            url_kwargs={'pk': 1},
        )

    def test_survey_progress(self):
        self.assert_url_matches_view(
            view=views.SurveyProgresssReport,
            expected_url='/survey/1/progress',
            url_name='survey-progress',
            url_kwargs={'pk': 1},
        )

    def test_survey_report(self):
        self.assert_url_matches_view(
            view=views.SurveyFullReport,
            expected_url='/survey/1/report',
            url_name='survey-report',
            url_kwargs={'pk': 1},
        )

    def test_survey_submit(self):
        self.assert_url_matches_view(
            view=views.SubmitSurveyResponse,
            expected_url='/survey/1/submit',
            url_name='survey-submit',
            url_kwargs={'pk': 1},
        )

    def test_survey_invite(self):
        self.assert_url_matches_view(
            view=views.InviteListView,
            expected_url='/survey/invite',
            url_name='survey-invite',
        )
