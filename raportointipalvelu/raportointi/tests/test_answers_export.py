import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.migrations.testing.setup import (
    add_viewreport_data, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_paakayttaja_ok)
from raportointi.models import Kysymysryhma, Kysely
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class AnswersExportTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_viewreport_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_answers_export_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        kysely = Kysely.objects.get(nimi_fi="viewreport1")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/answers-export/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija={kysely.koulutustoimija.oid}/"
            f"alkupvm={kysely.voimassa_alkupvm}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_answers_export_base64_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        kysely = Kysely.objects.get(nimi_fi="viewreport1")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/answers-export/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija={kysely.koulutustoimija.oid}/"
            f"alkupvm={kysely.voimassa_alkupvm}/?base64=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(type(resp.content), bytes)
        self.assertTrue(resp.content.startswith(b"77u/VmFz"))
        self.assertTrue(resp.content.endswith(b"=="))

    @responses.activate
    def test_get_answers_export_no_permission_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/answers-export/kysymysryhmaid=1/koulutustoimija=1/alkupvm=1/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @responses.activate
    def test_get_answers_export_kysely_not_found(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/answers-export/kysymysryhmaid=1/koulutustoimija=1/alkupvm=2000-01-01/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER018" in str(resp.json()))

    @responses.activate
    def test_get_answers_export_lomaketyyppi_not_allowed(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="lomaketyyppi_not_found")
        kysely = Kysely.objects.get(nimi_fi="lomaketyyppi_not_found")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/answers-export/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija={kysely.koulutustoimija.oid}/"
            f"alkupvm={kysely.voimassa_alkupvm}/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER027" in str(resp.json()))
