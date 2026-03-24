import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.migrations.testing.setup import (
    add_lomake_usage_data, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_paakayttaja_ok, add_testing_responses_kayttooikeus_toteuttaja_ok,
)
from raportointi.constants import DATE_INPUT_FORMAT
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES
from raportointi.utils import datenow_delta


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class LomakeUsageExportTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_lomake_usage_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_lomake_usage_export_loppupvm_included_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        pvm1 = datenow_delta(-15).strftime(DATE_INPUT_FORMAT)
        pvm2 = datenow_delta(-5).strftime(DATE_INPUT_FORMAT)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/lomake-usage-export/pvm1={pvm1}/pvm2={pvm2}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_lomake_usage_export_alkupvm_included_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        pvm1 = datenow_delta(-5).strftime(DATE_INPUT_FORMAT)
        pvm2 = datenow_delta(5).strftime(DATE_INPUT_FORMAT)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/lomake-usage-export/pvm1={pvm1}/pvm2={pvm2}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_lomake_usage_export_middle_included_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        pvm1 = datenow_delta(-15).strftime(DATE_INPUT_FORMAT)
        pvm2 = datenow_delta(5).strftime(DATE_INPUT_FORMAT)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/lomake-usage-export/pvm1={pvm1}/pvm2={pvm2}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_lomake_usage_export_not_found_fail(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        pvm1 = datenow_delta(0).strftime(DATE_INPUT_FORMAT)
        pvm2 = datenow_delta(5).strftime(DATE_INPUT_FORMAT)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/lomake-usage-export/pvm1={pvm1}/pvm2={pvm2}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER024" in str(resp.json()))

    @responses.activate
    def test_get_lomake_usage_export_paakayttaja_no_permission_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        pvm1 = datenow_delta(-15).strftime(DATE_INPUT_FORMAT)
        pvm2 = datenow_delta(-5).strftime(DATE_INPUT_FORMAT)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/lomake-usage-export/pvm1={pvm1}/pvm2={pvm2}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))

    @responses.activate
    def test_get_lomake_usage_export_toteuttaja_no_permission_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        pvm1 = datenow_delta(-15).strftime(DATE_INPUT_FORMAT)
        pvm2 = datenow_delta(-5).strftime(DATE_INPUT_FORMAT)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/lomake-usage-export/pvm1={pvm1}/pvm2={pvm2}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))

    @responses.activate
    def test_get_lomake_usage_export_faulty_date_fail(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/lomake-usage-export/pvm1=2025-13-01/pvm2=2025-01-02/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER032" in str(resp.json()))

    @responses.activate
    def test_get_lomake_usage_export_faulty_dates_order_fail(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/lomake-usage-export/pvm1=2025-01-02/pvm2=2025-01-01/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER033" in str(resp.json()))
