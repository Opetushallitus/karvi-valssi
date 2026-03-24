import json
import responses

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_service_ticket, add_testing_responses_email_service,
    add_testing_responses_service_ticket_fail_500)
from kyselyt.constants import VASTAAJATUNNUS_MAX_LENGTH, EMAIL_STATUS_SENT, EMAIL_STATUS_FAILED
from kyselyt.models import Message, OphAuthentication
from kyselyt.tests.constants import get_test_access_token, VIESTINTAPALVELU_API_URL


@override_settings(RATELIMIT_ENABLE=False)
class LahetaApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_post_laheta_and_post_viestit_after_with_id_ok(self):
        add_testing_responses_service_ticket(responses)
        add_testing_responses_email_service(responses)
        msgs = [{"email": "a002@a.aa", "template": 2, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue("msg_id" in resp.json()[0])
        msgs = Message.objects.filter(email="a002@a.aa")
        self.assertEqual(len(msgs), 1)
        self.assertTrue(len(msgs[0].msg_status) > 0)
        self.assertEqual(msgs[0].email_service_msg_id_str, "tunniste-1")

        msg_id = resp.json()[0]["msg_id"]
        data = {"msg_ids": [msg_id]}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0].get("msg_status"), EMAIL_STATUS_SENT)

    @responses.activate
    def test_post_laheta_containing_unnecessary_data(self):
        add_testing_responses_service_ticket(responses)
        add_testing_responses_email_service(responses)
        msgs = [{"email": "a002@a.aa", "template": 2, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01",
                 "unused-data": 3}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @responses.activate
    def test_post_laheta_message_empty_ok(self):
        add_testing_responses_service_ticket(responses)
        add_testing_responses_email_service(responses)
        msgs = [{"email": "a002@a.aa", "template": 2, "vastaajatunnus": "a",
                 "message": "", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @responses.activate
    def test_post_laheta_tgt_appear_to_db_after_request(self):
        add_testing_responses_service_ticket(responses)
        add_testing_responses_email_service(responses)
        self.assertEqual(OphAuthentication.objects.count(), 0)
        msgs = [{"email": "a002@a.aa", "template": 2, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(OphAuthentication.objects.count(), 1)
        self.assertEqual(OphAuthentication.objects.first().tgt, "http://ok")

    @responses.activate
    def test_post_laheta_tgt_clear_after_validity(self):
        add_testing_responses_email_service(responses)
        add_testing_responses_service_ticket_fail_500(responses)
        OphAuthentication.objects.get_or_create(id=1, defaults={"tgt": "aaa"})
        self.assertEqual(OphAuthentication.objects.first().tgt, "aaa")
        msgs = [{"email": "a002@a.aa", "template": 2, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(OphAuthentication.objects.first().tgt, "")

    def test_post_laheta_email_missing_fail(self):
        msgs = [{"template": 2, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("email" in str(resp.json()))

    def test_post_laheta_template_missing_fail(self):
        msgs = [{"email": "a003@a.aa", "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("template" in str(resp.json()))

    def test_post_laheta_vastaajatunnus_missing_fail(self):
        msgs = [{"email": "a004@a.aa", "template": 2,
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("vastaajatunnus" in str(resp.json()))

    def test_post_laheta_vastaajatunnus_too_long_fail(self):
        vast_tunnus = "a" * (VASTAAJATUNNUS_MAX_LENGTH + 1)
        msgs = [{"email": "a005@a.aa", "template": 3, "vastaajatunnus": vast_tunnus,
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("vastaajatunnus" in str(resp.json()))

    def test_post_laheta_filename_fi_missing_fail(self):
        msgs = [{"email": "a002@a.aa", "template": 1, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("filename_fi" in str(resp.json()))

    def test_post_laheta_filename_sv_missing_fail(self):
        msgs = [{"email": "a002@a.aa", "template": 1, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("filename_sv" in str(resp.json()))

    def test_post_laheta_pdf_file_fi_missing_fail(self):
        msgs = [{"email": "a002@a.aa", "template": 1, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf",
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("pdf_file_fi" in str(resp.json()))

    def test_post_laheta_pdf_file_sv_missing_fail(self):
        msgs = [{"email": "a002@a.aa", "template": 1, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf"}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("pdf_file_sv" in str(resp.json()))

    def test_post_laheta_message_missing_fail(self):
        msgs = [{"email": "a002@a.aa", "template": 2, "vastaajatunnus": "a", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("message" in str(resp.json()))

    def test_post_laheta_enddate_missing_fail(self):
        msgs = [{"email": "a002@a.aa", "template": 2, "vastaajatunnus": "a", "message": "additional msg"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("end_date" in str(resp.json()))

    @responses.activate
    def test_post_laheta_ok_email_with_invalid_ending(self):
        add_testing_responses_service_ticket(responses)
        add_testing_responses_email_service(responses)
        msgs = [{"email": "f001@a.invalid", "template": 1, "vastaajatunnus": "a",
                 "message": "additional msg", "end_date": "2023-01-01"}]
        data = {"messages": json.dumps(msgs),
                "filename_fi": "a.pdf", "pdf_file_fi": ContentFile("no-content", "empty.pdf"),
                "filename_sv": "a.pdf", "pdf_file_sv": ContentFile("no-content", "empty.pdf")}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", data, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json()[0].get("msg_status"), EMAIL_STATUS_FAILED)
        msg_id = resp.json()[0].get("msg_id")
        msg = Message.objects.get(msg_id=msg_id)
        self.assertEqual(msg.msg_status, EMAIL_STATUS_FAILED)

        data = {"msg_ids": [msg_id]}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()[0].get("msg_status"), EMAIL_STATUS_FAILED)

    def test_get_laheta_fail(self):
        resp = self.client.get(f"{VIESTINTAPALVELU_API_URL}/laheta/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_laheta_fail(self):
        resp = self.client.put(f"{VIESTINTAPALVELU_API_URL}/laheta/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(RATELIMIT_ENABLE=False)
class LahetaApiAccessTokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_post_laheta_access_token_missing(self):
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_laheta_access_token_faulty(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer faulty-key")
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/laheta/", {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
