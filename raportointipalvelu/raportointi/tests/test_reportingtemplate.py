import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.migrations.testing.setup import (
    load_testing_data, add_testing_responses_service_ticket,
    add_testing_responses_kayttooikeus_yllapitaja_ok, add_reportingtemplate_data)
from raportointi.models import Kysymysryhma
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class ReportingBaseGetTests(TestCase):
    """GET tests for reporting-base.
    Requires Ylläpitäjä permissions.
    """
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_reportingtemplate_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_reportingbase_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="reportingtemplate_kysymysryhma").pk
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/reporting-base/{kysymysryhmaid}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_reportingbase_data(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="reportingtemplate_kysymysryhma").pk
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/reporting-base/{kysymysryhmaid}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        self.assertEqual(data["kysymysryhmaid"], kysymysryhmaid)
        self.assertEqual(data["nimi_fi"], "reportingtemplate_kysymysryhma")
        self.assertEqual(len(data["questions"]), 1)

        self.assertEqual(len(data["questions"][0]["matriisikysymykset"]), 2)
        self.assertEqual(data["questions"][0]["matriisikysymykset"][0]["kysymys_fi"], "reportingtemplate question1")
        self.assertEqual(data["questions"][0]["matriisikysymykset"][1]["kysymys_fi"], "reportingtemplate question2")


@override_settings(RATELIMIT_ENABLE=False)
class ReportingTemplatePostTests(TestCase):
    """POST tests for reporting-base.
    Requires Ylläpitäjä permissions.
    """
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_post_reportingtemplate_ok(self):
        """Check for CREATED response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="reportingtemplate_yllapitaja_kysymysryhma").pk
        post_data = {
            "kysymysryhmaid": kysymysryhmaid,
            "title_fi": "main title fi",
            "title_sv": "main title sv",
            "description_fi": "main description fi",
            "description_sv": "main description sv",
            "template_helptexts": [
                {
                    "question_id": 1,
                    "title_fi": "title fi",
                    "title_sv": "title sv",
                    "description_fi": "description fi",
                    "description_sv": "description sv"
                },
                {
                    "question_id": 2,
                    "title_fi": "title fi",
                    "title_sv": "title sv",
                    "description_fi": "description fi",
                    "description_sv": "description sv"
                }
            ]
        }

        resp = self.client.post(RAPORTOINTIPALVELU_API_URL + "/reporting-template/", data=post_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @responses.activate
    def test_post_reportingtemplate_data(self):
        """Check reportingtemplate returned data is correct after post request"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="reportingtemplate_yllapitaja_kysymysryhma").pk
        post_data = {
            "kysymysryhmaid": kysymysryhmaid,
            "title_fi": "main title fi",
            "title_sv": "main title sv",
            "description_fi": "main description fi",
            "description_sv": "main description sv",
            "template_helptexts": [
                {
                    "question_id": 1,
                    "title_fi": "helptext title fi",
                    "title_sv": "helptext title sv",
                    "description_fi": "helptext description fi",
                    "description_sv": "helptext description sv"
                },
                {
                    "question_id": 2,
                    "title_fi": "helptext title fi",
                    "title_sv": "helptext title sv",
                    "description_fi": "helptext description fi",
                    "description_sv": "helptext description sv"
                }
            ]
        }

        resp = self.client.post(RAPORTOINTIPALVELU_API_URL + "/reporting-template/", data=post_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        data = resp.json()
        self.assertEqual(data["kysymysryhmaid"], kysymysryhmaid)
        self.assertEqual(data["title_fi"], "main title fi")
        self.assertEqual(data["title_sv"], "main title sv")
        self.assertEqual(data["description_fi"], "main description fi")
        self.assertEqual(data["description_sv"], "main description sv")

        template_helptexts = data["template_helptexts"]
        self.assertEqual(len(template_helptexts), 2)
        self.assertEqual(template_helptexts[0]["question_id"], 1)
        self.assertEqual(template_helptexts[0]["title_fi"], "helptext title fi")
        self.assertEqual(template_helptexts[0]["title_sv"], "helptext title sv")
        self.assertEqual(template_helptexts[0]["description_fi"], "helptext description fi")
        self.assertEqual(template_helptexts[0]["description_sv"], "helptext description sv")


@override_settings(RATELIMIT_ENABLE=False)
class ReportingTemplatePutTests(TestCase):
    """POST tests for reporting-base.
    Requires Ylläpitäjä permissions.
    """
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_put_reportingtemplate_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="reportingtemplate_yllapitaja_kysymysryhma").pk
        post_data = {
            "kysymysryhmaid": kysymysryhmaid,
            "title_fi": "main title fi",
            "title_sv": "main title sv",
            "description_fi": "main description fi",
            "description_sv": "main description sv",
            "template_helptexts": [
                {
                    "id": 1,
                    "question_id": 1,
                    "title_fi": "helptext title fi",
                    "title_sv": "helptext title sv",
                    "description_fi": "helptext description fi",
                    "description_sv": "helptext description sv"
                },
                {
                    "id": 2,
                    "question_id": 2,
                    "title_fi": "helptext title fi",
                    "title_sv": "helptext title sv",
                    "description_fi": "helptext description fi",
                    "description_sv": "helptext description sv"
                }
            ]
        }

        post_resp = self.client.post(RAPORTOINTIPALVELU_API_URL + "/reporting-template/", data=post_data, format="json")
        self.assertEqual(post_resp.status_code, status.HTTP_201_CREATED)

        put_data = {
            "kysymysryhmaid": kysymysryhmaid,
            "title_fi": "main title fi put",
            "title_sv": "main title sv put",
            "description_fi": "main description fi put",
            "description_sv": "main description sv put",
            "template_helptexts": [
                {
                    "id": 1,
                    "question_id": 1,
                    "title_fi": "helptext title fi put",
                    "title_sv": "helptext title sv put",
                    "description_fi": "helptext description fi put",
                    "description_sv": "helptext description sv put"
                },
                {
                    "id": 2,
                    "question_id": 2,
                    "title_fi": "helptext title fi put",
                    "title_sv": "helptext title sv put",
                    "description_fi": "helptext description fi put",
                    "description_sv": "helptext description sv put"
                }
            ]
        }

        put_resp = self.client.put(RAPORTOINTIPALVELU_API_URL + f"/reporting-template/{post_resp.json()['id']}/",
                                   data=put_data,
                                   format="json")

        data = put_resp.json()

        self.assertEqual(data["title_fi"], "main title fi put")
        self.assertEqual(data["title_sv"], "main title sv put")
        self.assertEqual(data["description_fi"], "main description fi put")
        self.assertEqual(data["description_sv"], "main description sv put")

        template_helptexts = data["template_helptexts"]
        self.assertEqual(len(template_helptexts), 2)
        self.assertEqual(template_helptexts[0]["id"], 1)
        self.assertEqual(template_helptexts[0]["question_id"], 1)
        self.assertEqual(template_helptexts[0]["title_fi"], "helptext title fi put")
        self.assertEqual(template_helptexts[0]["title_sv"], "helptext title sv put")
        self.assertEqual(template_helptexts[0]["description_fi"], "helptext description fi put")
        self.assertEqual(template_helptexts[0]["description_sv"], "helptext description sv put")


@override_settings(RATELIMIT_ENABLE=False)
class WrongMethodTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_put_reportingbase_fail(self):
        resp = self.client.put(RAPORTOINTIPALVELU_API_URL + "/reporting-base/4/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_reportingbase_fail(self):
        resp = self.client.delete(RAPORTOINTIPALVELU_API_URL + "/reporting-base/4/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_reportingbase_fail(self):
        resp = self.client.post(RAPORTOINTIPALVELU_API_URL + "/reporting-base/4/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_reportingtemplate_fail(self):
        resp = self.client.put(RAPORTOINTIPALVELU_API_URL + "/reporting-template/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
