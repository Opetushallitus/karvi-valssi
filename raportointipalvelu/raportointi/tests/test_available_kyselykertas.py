import responses

from datetime import datetime

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.migrations.testing.setup import (
    add_testing_responses_kayttooikeus_paakayttaja_ok, add_test_user, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_test_results, add_testing_responses_kayttooikeus_toteuttaja_ok,
)
from raportointi.models import Kysymysryhma, Kyselykerta
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class AvailableKyselykertasTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_results()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_available_kyselykertas_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)

        kysymysryhma1 = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        kyselykerta = Kyselykerta.objects.get(kyselyid__kysely__kysymysryhmaid__kysymysryhmaid=kysymysryhma1.pk)

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/available-kyselykertas/"
            f"kysymysryhmaid={kysymysryhma1.pk}/koulutustoimija=0.1.2/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(
            resp.json()[0]["kyselykerta_alkupvm"], datetime.strftime(kyselykerta.voimassa_alkupvm, "%Y-%m-%d")
        )
        self.assertEqual(resp.json()[0]["display_report"], False)
        self.assertEqual(resp.json()[0]["show_summary"], True)
        self.assertEqual(resp.json()[0]["show_result"], True)
        self.assertTrue(resp.json()[0]["nimi_fi"].startswith("summary_testikysymysryhma1"))
        self.assertTrue(resp.json()[0]["nimi_sv"].startswith("summary_testikysymysryhma1"))

    @responses.activate
    def test_get_available_kyselykertas_no_permission_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)

        kysymysryhma1 = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/available-kyselykertas/"
            f"kysymysryhmaid={kysymysryhma1.pk}/koulutustoimija=0.1.2/"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class AvailableKyselykertasRangeTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_results()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_available_kyselykertas_range_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)

        kysymysryhma1 = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/available-kyselykertas/pvm1=2025-01-01/pvm2=2040-01-01/"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 2)
        self.assertEqual(resp.json()[0]["kysymysryhmaid"], kysymysryhma1.pk)
        self.assertEqual(resp.json()[0]["name"]["fi"], "summary_testikysymysryhma1")
        self.assertEqual(resp.json()[0]["show_summary"], True)
        self.assertEqual(resp.json()[0]["show_result"], True)
        self.assertEqual(resp.json()[0]["laatutekija"], "prosessi")

        self.assertEqual(resp.json()[1]["name"]["fi"], "summary_testikysymysryhma3")
        self.assertEqual(resp.json()[1]["show_summary"], False)
        self.assertEqual(resp.json()[1]["show_result"], False)
        self.assertEqual(resp.json()[1]["laatutekija"], "prosessi")

    @responses.activate
    def test_get_available_kyselykertas_range_no_permission_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/available-kyselykertas/pvm1=2025-01-01/pvm2=2040-01-01/"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))
