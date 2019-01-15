from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile

from core.tests.utils import AnonymouseTestMixin, RequestTestCase
from users.tests.factories import UserFactory
from .factories import DocumentFactory
from .. import views
from ..models import Document


class TestDocumentHome(AnonymouseTestMixin, RequestTestCase):
    view = views.DocumentHome

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()

    def test_get(self):
        view = self.view.as_view()
        request = self.create_request('get', user=self.user)
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_anonymous(self):
        view = self.view.as_view()
        request = self.create_request('get', auth=False)
        response = view(request)
        self.assertRedirectToLogin(response)

    def test_post(self):
        view = self.view.as_view()
        test_file = SimpleUploadedFile('test_file.txt', b'This is sample text')

        data = {
            'name': 'sample document',
            'expiry': date(2020, 1, 14),
            'file': test_file
        }

        request = self.create_request('post', user=self.user, data=data)
        response = view(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn('Document uploaded successfully', request._messages.store[0])

        document = Document.objects.get()
        self.assertEqual(document.name, data['name'])
        self.assertEqual(document.file.read(), b'This is sample text')
        # Remove the file from the file system
        document.file.delete()

    def test_post_error(self):
        view = self.view.as_view()

        data = {
            'name': '',
            'expiry': date(2020, 1, 14),
            'file': ''
        }

        request = self.create_request('post', user=self.user, data=data)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn('Failed to upload document', request._messages.store[0])


class TestDocumentEdit(AnonymouseTestMixin, RequestTestCase):
    view = views.DocumentEdit

    def setUp(self):
        super().setUp()
        self.view = self.view.as_view()
        self.user = UserFactory.create()
        self.document = DocumentFactory.create()

    def test_get_anonymous(self):
        request = self.create_request(auth=False)
        response = self.view(request, pk=self.document.id)
        self.assertRedirectToLogin(response)

    def test_get(self):
        request = self.create_request('get', user=self.user)
        response = self.view(request, pk=self.document.id)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        data = {
            'name': 'test user',
            'expiry': date(2020, 1, 14),
        }

        request = self.create_request('post', user=self.user, data=data)
        response = self.view(request, pk=self.document.id)
        self.assertEqual(response.status_code, 302)

        self.assertIn(
            'Document updated successfully',
            request._messages.store[0],
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.name, data['name'])

    def test_post_invalid_data(self):
        data = {
            'name': 'test user',
            'expiry': 'invalid_expiry_date'
        }

        request = self.create_request('post', user=self.user, data=data)
        response = self.view(request, pk=self.document.id)
        self.assertEqual(response.status_code, 200)

        self.assertIn(
            'Failed to update document',
            request._messages.store[0],
        )
