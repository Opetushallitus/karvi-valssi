import responses
from datetime import datetime, timedelta

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.constants import DATE_INPUT_FORMAT
from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_service_ticket, add_testing_responses_kayttooikeus_paakayttaja_ok,
    add_testing_responses_kayttooikeus_yllapitaja_ok, add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok)
from kyselyt.models import Kysely, Kysymysryhma, Vastaajatunnus, Kyselykerta
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token


@override_settings(RATELIMIT_ENABLE=False)
class KyselykertaExtendEnddateApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_patch_kyselykerta_extend_enddate_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma10").pk
        kysely = Kysely.objects.get(nimi_fi="testikysely10")
        alkupvm = datetime.strftime(kysely.voimassa_alkupvm, DATE_INPUT_FORMAT)
        new_voimassa_loppupvm = kysely.voimassa_loppupvm + timedelta(days=5)
        data = {"voimassa_loppupvm": datetime.strftime(new_voimassa_loppupvm, DATE_INPUT_FORMAT)}
        resp = self.client.patch(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid={kysymysryhmaid}/"
            f"koulutustoimija={kysely.koulutustoimija.oid}/alkupvm={alkupvm}/",
            data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("updates_kysely"), 1)
        self.assertEqual(resp.json().get("updates_kyselykerta"), 2)
        self.assertEqual(resp.json().get("updates_vastaajatunnus"), 2)

        # check voimassa_loppupvms are updated in db
        self.assertEqual(Kysely.objects.get(nimi_fi="testikysely10").voimassa_loppupvm, new_voimassa_loppupvm)
        self.assertEqual(Kyselykerta.objects.get(nimi="testikyselykerta10").voimassa_loppupvm, new_voimassa_loppupvm)
        self.assertEqual(Kyselykerta.objects.get(nimi="testikyselykerta10_2").voimassa_loppupvm, new_voimassa_loppupvm)
        self.assertEqual(Vastaajatunnus.objects.get(tunnus="AAA101").voimassa_loppupvm, new_voimassa_loppupvm)
        self.assertEqual(Vastaajatunnus.objects.get(tunnus="AAA102").voimassa_loppupvm, new_voimassa_loppupvm)

    @responses.activate
    def test_patch_kyselykerta_extend_enddate_impersonate_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma10").pk
        kysely = Kysely.objects.get(nimi_fi="testikysely10")
        alkupvm = datetime.strftime(kysely.voimassa_alkupvm, DATE_INPUT_FORMAT)
        new_voimassa_loppupvm = kysely.voimassa_loppupvm + timedelta(days=5)
        data = {"voimassa_loppupvm": datetime.strftime(new_voimassa_loppupvm, DATE_INPUT_FORMAT)}
        resp = self.client.patch(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid={kysymysryhmaid}/"
            f"koulutustoimija={kysely.koulutustoimija.oid}/alkupvm={alkupvm}/",
            data, format="json", HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("updates_kysely"), 1)
        self.assertEqual(resp.json().get("updates_kyselykerta"), 2)
        self.assertEqual(resp.json().get("updates_vastaajatunnus"), 2)

    @responses.activate
    def test_patch_kyselykerta_extend_enddate_kysymysryhma_not_found(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        data = {"voimassa_loppupvm": "2099-01-01"}
        resp = self.client.patch(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid=999/"
            f"koulutustoimija=9999/alkupvm=123/",
            data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER016" in str(resp.json()))

    @responses.activate
    def test_patch_kyselykerta_extend_enddate_kysely_not_found(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma10").pk
        kysely = Kysely.objects.get(nimi_fi="testikysely10")
        data = {"voimassa_loppupvm": "2099-01-01"}
        resp = self.client.patch(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid={kysymysryhmaid}/"
            f"koulutustoimija={kysely.koulutustoimija.oid}/alkupvm=2000-01-01/",
            data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER021" in str(resp.json()))

    @responses.activate
    def test_patch_kyselykerta_extend_enddate_enddate_in_the_past(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma10_3").pk
        kysely = Kysely.objects.get(nimi_fi="testikysely10_3")
        alkupvm = datetime.strftime(kysely.voimassa_alkupvm, DATE_INPUT_FORMAT)
        resp = self.client.patch(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid={kysymysryhmaid}/"
            f"koulutustoimija={kysely.koulutustoimija.oid}/alkupvm={alkupvm}/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER021" in str(resp.json()))

    @responses.activate
    def test_patch_kyselykerta_extend_enddate_enddate_before_previous_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma10").pk
        kysely = Kysely.objects.get(nimi_fi="testikysely10")
        alkupvm = datetime.strftime(kysely.voimassa_alkupvm, DATE_INPUT_FORMAT)
        new_voimassa_loppupvm = kysely.voimassa_loppupvm - timedelta(days=5)
        data = {"voimassa_loppupvm": datetime.strftime(new_voimassa_loppupvm, DATE_INPUT_FORMAT)}
        resp = self.client.patch(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid={kysymysryhmaid}/"
            f"koulutustoimija={kysely.koulutustoimija.oid}/alkupvm={alkupvm}/",
            data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("VA007" in str(resp.json()))

    def test_get_kyselykerta_extend_enddate_wrong_method_fail(self):
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid=999/"
            f"koulutustoimija=999/alkupvm=999/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_kyselykerta_extend_enddate_wrong_method_fail(self):
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid=999/"
            f"koulutustoimija=999/alkupvm=999/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kyselykerta_extend_enddate_wrong_method_fail(self):
        resp = self.client.put(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselykerta/extend-enddate/kysymysryhmaid=999/"
            f"koulutustoimija=999/alkupvm=999/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
