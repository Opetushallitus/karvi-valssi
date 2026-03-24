
import weasyprint

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.tests.constants import BASE_URL


@override_settings(RATELIMIT_ENABLE=False)
class ViewsetTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_admin_page(self):
        resp = self.client.get(f"/{BASE_URL}admin/", follow=True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class PdfCreationTests(TestCase):
    def test_pdf_creation(self):
        pdf_file = None
        try:
            pdf_file = weasyprint.HTML(string="<html>something</html>").write_pdf()
        except Exception:
            pass
        self.assertIsNotNone(pdf_file)
