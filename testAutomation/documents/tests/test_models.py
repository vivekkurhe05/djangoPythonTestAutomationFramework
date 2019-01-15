from django.test import TestCase

from .factories import (
    DocumentFactory
)


class TestDocument(TestCase):
    def test_str(self):
        document = DocumentFactory.build()
        self.assertEqual(str(document), document.name)
