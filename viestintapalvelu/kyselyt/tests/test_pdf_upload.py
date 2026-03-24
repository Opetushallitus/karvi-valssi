import responses

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_service_ticket, add_testing_responses_email_service)
from kyselyt.models import Message
from kyselyt.tests.constants import get_test_access_token, VIESTINTAPALVELU_API_URL


@override_settings(RATELIMIT_ENABLE=False)
class PdfUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_post_pdfsend_ok(self):
        add_testing_responses_service_ticket(responses)
        add_testing_responses_email_service(responses)
        data = {"filename": "a.pdf", "email": "a@a.aa", "end_date": "2023-01-01",
                "pdf_file": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(
            f"{VIESTINTAPALVELU_API_URL}/pdfsend/", data=data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        msg = Message.objects.filter(email="a@a.aa").first()
        self.assertTrue(len(msg.msg_status) > 0)
        self.assertEqual(msg.email_service_msg_id_str, "tunniste-1")

    def test_post_pdfsend_filename_missing(self):
        data = {"email": "a@a.aa", "end_date": "2023-01-01", "pdf_file": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(
            f"{VIESTINTAPALVELU_API_URL}/pdfsend/", data=data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("filename" in str(resp.json()) and "required" in str(resp.json()))

    def test_post_pdfsend_email_missing(self):
        data = {"filename": "a.pdf", "end_date": "2023-01-01", "pdf_file": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(
            f"{VIESTINTAPALVELU_API_URL}/pdfsend/", data=data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("email" in str(resp.json()) and "required" in str(resp.json()))

    def test_post_pdfsend_pdf_field_missing(self):
        data = {"filename": "a.pdf", "email": "a@a.aa", "end_date": "2023-01-01"}
        resp = self.client.post(
            f"{VIESTINTAPALVELU_API_URL}/pdfsend/", data=data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("pdf_file" in str(resp.json()) and "No file was submitted" in str(resp.json()))

    def test_post_pdfsend_enddate_missing(self):
        data = {"filename": "a.pdf", "email": "a@a.aa", "pdf_file": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(
            f"{VIESTINTAPALVELU_API_URL}/pdfsend/", data=data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("end_date" in str(resp.json()) and "required" in str(resp.json()))

    def test_post_pdfsend_file_missing(self):
        data = {"filename": "a.pdf", "email": "a@a.aa", "pdf_file": ""}
        resp = self.client.post(
            f"{VIESTINTAPALVELU_API_URL}/pdfsend/", data=data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("pdf_file" in str(resp.json()) and "not a file" in str(resp.json()))

    def test_post_pdfsend_faulty_email(self):
        data = {"filename": "a.pdf", "email": "a@a", "end_date": "2023-01-01",
                "pdf_file": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(
            f"{VIESTINTAPALVELU_API_URL}/pdfsend/", data=data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Enter a valid email address" in str(resp.json()))
