import responses
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.migrations.testing.setup import (
    add_testing_responses_service_ticket, add_testing_responses_kayttooikeus_toteuttaja_ok, add_viewreport_data,
    add_testing_responses_kayttooikeus_paakayttaja_ok, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok)
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES
from raportointi.utils import datenow_delta


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class ClosedSurveysGetTests(TestCase):
    """GET tests for viewing closed kyselys"""
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_viewreport_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_closed_kyselys_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/closed-surveys/koulutustoimija=0.1.2/?role=toteuttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        self.assertEqual(data[0]["nimi_fi"], "reportview_kysymysryhma")
        self.assertEqual(data[0]["kyselykertas"][0]["nimi"], "viewreport_kyselykerta_2")
        self.assertEqual(data[0]["kyselykertas"][0]["kysely"]["nimi_fi"], "viewreport")
        self.assertEqual(data[0]["kyselykertas"][0]["show_summary"], True)
        self.assertTrue(data[0]["available_kyselykertas"][0]["nimi_fi"].startswith("reportview_kysymysryhma"))
        self.assertEqual(data[0]["available_kyselykertas"][0]["kyselykerta_alkupvm"],
                         datenow_delta(-100).strftime("%Y-%m-%d"))
        self.assertEqual(data[0]["koulutustoimija_oid"], "0.1.2")

    @responses.activate
    def test_get_closed_kyselys_paakayttaja_data(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/closed-surveys/koulutustoimija=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()

        self.assertEqual(data[0]["nimi_fi"], "reportview_kysymysryhma")
        self.assertTrue(data[0]["available_kyselykertas"][0]["nimi_fi"].startswith("reportview_kysymysryhma"))
        self.assertEqual(data[0]["available_kyselykertas"][0]["kyselykerta_alkupvm"],
                         datenow_delta(-100).strftime("%Y-%m-%d"))
        self.assertEqual(data[0]["koulutustoimija_oid"], "0.1.2")
        self.assertEqual(data[0]["available_kyselykertas"][0]["show_summary"], False)
        self.assertEqual(data[0]["available_kyselykertas"][-1]["show_summary"], True)

    @responses.activate
    def test_get_closed_kyselys_paakayttaja_data_impersonate_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses)

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/closed-surveys/koulutustoimija=0.1.2/?role=paakayttaja",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_closed_kyselys_paakayttaja_data_impersonate_org_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/closed-surveys/koulutustoimija=0.1.2/?role=paakayttaja",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
