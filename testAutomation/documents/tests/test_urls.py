from incuna_test_utils.testcases.urls import URLTestCase

from .. import views


class TestDocuments(URLTestCase):
    def test_document_home(self):
        self.assert_url_matches_view(
            view=views.DocumentHome,
            expected_url='/document/',
            url_name='document-home',
        )
