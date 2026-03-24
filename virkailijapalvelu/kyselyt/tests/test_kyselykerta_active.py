import responses
from datetime import datetime

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_kayttooikeus_ok, add_testing_responses_kayttooikeus_organisaatiot_empty,
    add_testing_responses_service_ticket, add_testing_responses_kayttooikeus_multi_ok,
    add_testing_responses_kayttooikeus_yllapitaja_ok, add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok)
from kyselyt.models import Kyselykerta, Kysymysryhma, Vastaajatunnus
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token


@override_settings(RATELIMIT_ENABLE=False)
class KyselykertaActiveApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_kyselykerta_active_koulutustoimija_ok(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma={kysymysryhmaid}/organisaatio=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta5")
        self.assertEqual(resp.json()[0]["kyselykertaid"], kyselykerta.kyselykertaid)
        self.assertEqual(resp.json()[0]["kyselyid"], kyselykerta.kyselyid.kyselyid)
        self.assertEqual(
            resp.json()[0]["voimassa_alkupvm"], datetime.strftime(kyselykerta.voimassa_alkupvm, "%Y-%m-%d"))
        self.assertEqual(
            resp.json()[0]["voimassa_loppupvm"], datetime.strftime(kyselykerta.voimassa_loppupvm, "%Y-%m-%d"))
        self.assertEqual(resp.json()[0]["last_kyselysend"]["message"], "test-msg")
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus="a1")
        self.assertEqual(resp.json()[0]["last_kyselysend"]["vastaajatunnus"]["voimassa_alkupvm"],
                         datetime.strftime(vastaajatunnus.voimassa_alkupvm, "%Y-%m-%d"))
        self.assertEqual(resp.json()[0]["last_kyselysend"]["vastaajatunnus"]["voimassa_loppupvm"],
                         datetime.strftime(vastaajatunnus.voimassa_loppupvm, "%Y-%m-%d"))

    @responses.activate
    def test_get_kyselykerta_active_toimipaikka_ok(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma={kysymysryhmaid}/organisaatio=0.1.3/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_kyselykerta_active_toimipaikka_impersonate_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma={kysymysryhmaid}/organisaatio=0.1.3/",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_kyselykerta_active_toimipaikka_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma={kysymysryhmaid}/organisaatio=0.1.3/",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_kyselykerta_active_kyselysend_not_found_ok(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma3").kysymysryhmaid
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma={kysymysryhmaid}/organisaatio=0.1.3/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()[0]["last_kyselysend"], None)

    def test_get_kyselykerta_active_kysymysryhmaid_missing_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @responses.activate
    def test_get_kyselykerta_active_kyselykerta_not_found_ok(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma2").kysymysryhmaid
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma={kysymysryhmaid}/organisaatio=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json(), [])

    def test_get_kyselykerta_active_kysymysryhmaid_string_type_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma=a/organisaatio=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_kyselykerta_active_kysymysryhmaid_float_type_fail(self):
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma=1.1/organisaatio=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @responses.activate
    def test_get_kyselykerta_active_organisaatio_missing_fail(self):
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma={kysymysryhmaid}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_kyselykerta_active_organisaatio_wrong_format_fail(self):
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma=999/organisaatio=a/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @responses.activate
    def test_get_kyselykerta_active_vakajarjestaja_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma={kysymysryhmaid}/organisaatio=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_kyselykerta_active_fail(self):
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma=1/organisaatio=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kyselykerta_active_fail(self):
        resp = self.client.put(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/kysymysryhma=1/organisaatio=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(RATELIMIT_ENABLE=False)
class KyselykertaActiveMultiApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_post_kyselykerta_active_multi_ok(self):
        add_testing_responses_kayttooikeus_multi_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid1 = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma11_1").kysymysryhmaid
        kysymysryhmaid2 = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma11_2").kysymysryhmaid
        data = [{"kysymysryhmaid": kysymysryhmaid1, "organisaatio": "0.1.2"},
                {"kysymysryhmaid": kysymysryhmaid2, "organisaatio": "0.1.3.2"},
                {"kysymysryhmaid": 999, "organisaatio": "0.1.2"}]
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/multi/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 3)

        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta11_1")
        self.assertEqual(resp.json()[0]["kysymysryhmaid"], kysymysryhmaid1)
        self.assertEqual(resp.json()[0]["kyselykertaid"], kyselykerta.kyselykertaid)
        self.assertEqual(resp.json()[0]["kyselyid"], kyselykerta.kyselyid.kyselyid)
        self.assertEqual(
            resp.json()[0]["voimassa_alkupvm"], datetime.strftime(kyselykerta.voimassa_alkupvm, "%Y-%m-%d"))
        self.assertEqual(
            resp.json()[0]["voimassa_loppupvm"], datetime.strftime(kyselykerta.voimassa_loppupvm, "%Y-%m-%d"))
        self.assertEqual(resp.json()[0]["last_kyselysend"]["message"], "test-msg")
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus="a1")
        self.assertEqual(resp.json()[0]["last_kyselysend"]["vastaajatunnus"]["voimassa_alkupvm"],
                         datetime.strftime(vastaajatunnus.voimassa_alkupvm, "%Y-%m-%d"))
        self.assertEqual(resp.json()[0]["last_kyselysend"]["vastaajatunnus"]["voimassa_loppupvm"],
                         datetime.strftime(vastaajatunnus.voimassa_loppupvm, "%Y-%m-%d"))

        kyselykerta2 = Kyselykerta.objects.get(nimi="testikyselykerta11_2")
        self.assertEqual(resp.json()[1]["kysymysryhmaid"], kysymysryhmaid2)
        self.assertEqual(resp.json()[1]["kyselykertaid"], kyselykerta2.kyselykertaid)
        self.assertEqual(resp.json()[1]["last_kyselysend"], None)

        self.assertEqual(resp.json()[2], {})  # empty dict if kysymysryhma not found

    @responses.activate
    def test_post_kyselykerta_active_multi_empty_list_ok(self):
        add_testing_responses_kayttooikeus_multi_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/multi/", [], format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    @responses.activate
    def test_post_kyselykerta_active_multi_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid1 = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma11_1").kysymysryhmaid
        data = [{"kysymysryhmaid": kysymysryhmaid1, "organisaatio": "0.1.2"}]
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/multi/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_kyselykerta_active_multi_kysymysryhmaid_missing_fail(self):
        data = [{"organisaatio": "0.1.2"}]
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/multi/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_kyselykerta_active_multi_organisaatio_missing_fail(self):
        data = [{"kysymysryhmaid": 1}]
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/multi/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_kyselykerta_active_multi_kysymysryhmaid_wrong_type_fail(self):
        data = [{"kysymysryhmaid": "a", "organisaatio": "0.1.2"}]
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/multi/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("valid integer is required" in str(resp.json()))

    def test_get_kyselykerta_active_multi_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/multi/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kyselykerta_active_multi_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/active/multi/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
