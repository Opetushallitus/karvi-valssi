import responses

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.constants import DATE_INPUT_FORMAT
from raportointi.migrations.testing.setup import (
    load_testing_data, add_test_user, add_test_kayttajat,
    add_testing_responses_service_ticket, add_testing_responses_kayttooikeus_toteuttaja_ok,
    add_testing_responses_kayttooikeus_organisaatiot_empty, add_testing_responses_kayttooikeus_paakayttaja_ok,
    add_testing_responses_service_ticket_fail_500, add_testing_responses_kayttooikeus_paakayttaja_only_ok,
    add_testing_responses_kayttooikeus_yllapitaja_ok, add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok,
    add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok)
from raportointi.models import Kysely, Kyselykerta, Vastaajatunnus, Vastaaja
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES
from raportointi.utils import datenow_delta


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class DataCollectionToteuttajaGetTests(TestCase):
    """Get tests for the data-collection toteuttaja"""
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_datacollection_toteuttaja_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=toteuttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_datacollection_toteuttaja_impersonate_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)
        resp = self.client.get(
            RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=toteuttaja",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_datacollection_toteuttaja_impersonate_org_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(
            RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=toteuttaja",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_datacollection_service_ticket_fail(self):
        """Check for 403 forbidden response
        Opintopolku service ticket API call failed, auth will fail with forbidden response.
        """
        add_testing_responses_service_ticket_fail_500(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @responses.activate
    def test_get_datacollection_no_kayttooikeus(self):
        """Check for 403 response
        No organisaatio or kayttooikeudet returned from Opintopolku, auth will fail with forbidden response.
        """
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @responses.activate
    def test_get_datacollection_toteuttaja_permissions(self):
        """Check correct kysely's are returned with toteuttaja permissions"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=toteuttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        if any(kysely["nimi_fi"] == "organisaatiokysely" for kysely in resp.json()):
            self.assertTrue(False)
        if not any(kysely["nimi_fi"] == "toimipaikkakysely" for kysely in resp.json()):
            self.assertTrue(False)

    @responses.activate
    def test_get_datacollection_statistics(self):
        """Check added statistics"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        # Setup latest vastaaja
        kysely1 = Kysely.objects.get(nimi_fi="testikysely1")
        kyselykerta1 = Kyselykerta.objects.get(
            kyselyid=kysely1, nimi="testikyselykerta1")
        vastaajatunnus1_1 = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus1_1")
        latest_vastaaja = Vastaaja.objects.get(
            kyselykertaid=kyselykerta1.kyselykertaid,
            vastaajatunnus=vastaajatunnus1_1.vastaajatunnusid)

        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=toteuttaja")
        # Statistics with data
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        kysely_data = resp.json()[2]
        self.assertEqual(kysely_data["nimi_fi"], "testikysely1")
        self.assertEqual(kysely_data["indicators"]["main_indicator"]["key"], "pedagoginen_prosessi")
        self.assertEqual(kysely_data["indicators"]["secondary_indicators"][0]["key"],
                         "myonteinen_ja_sitoutunut_vuorovaik")
        self.assertEqual(kysely_data["indicators"]["secondary_indicators"][1]["key"],
                         "vastavuoroinen_vuorovaikutus")
        self.assertEqual(kysely_data["is_closed"], False)
        self.assertEqual(kysely_data["latest_answer_date"],
                         latest_vastaaja.luotuaika.strftime(DATE_INPUT_FORMAT))
        self.assertEqual(kysely_data["statistics"]["answered_count"], 2)
        self.assertEqual(kysely_data["statistics"]["answer_pct"], 67)
        self.assertEqual(kysely_data["statistics"]["sent_count"], 3)

        # # Statistics with no data
        kysely_data = resp.json()[1]
        self.assertEqual(kysely_data["nimi_fi"], "testikysely2")
        self.assertEqual(kysely_data["latest_answer_date"], None)
        self.assertEqual(kysely_data["statistics"]["answered_count"], 0)
        self.assertEqual(kysely_data["statistics"]["answer_pct"], 0)
        self.assertEqual(kysely_data["statistics"]["sent_count"], 0)

    @responses.activate
    def test_get_datacollection_max_60d_old(self):
        """Check that max 60 days old forms are included

        59, 60 & 61 days old kysely's are loaded on setup
        testikysely_59d_old
        testikysely_60d_old
        testikysely_61d_old
        """
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=toteuttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        timenow_minus_60d = datenow_delta(-60)

        for kysely in resp.json():
            self.assertTrue(kysely["voimassa_loppupvm"] >= timenow_minus_60d.strftime(DATE_INPUT_FORMAT))

        # Get Kysely's from database
        kysely_60d_old = Kysely.objects.get(nimi_fi="testikysely_60d_old")
        kysely_61d_old = Kysely.objects.get(nimi_fi="testikysely_61d_old")
        kysely_59d_old = Kysely.objects.get(nimi_fi="testikysely_59d_old")

        # 60d old are shown
        if not any(kysely["nimi_fi"] == kysely_60d_old.nimi_fi for kysely in resp.json()):
            self.assertTrue(False)

        # 61d old are not shown
        if any(kysely["nimi_fi"] == kysely_61d_old.nimi_fi for kysely in resp.json()):
            self.assertTrue(False)

        # 59d old are shown
        if not (kysely["nimi_fi"] == kysely_59d_old.nimi_fi for kysely in resp.json()):
            self.assertTrue(False)


@override_settings(RATELIMIT_ENABLE=False)
class DataCollectionPaakayttajaGetTests(TestCase):
    """Get tests for the data-collection paakayttaja"""
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_datacollection_paakayttaja_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_datacollection_paakayttaja_impersonate_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses)

        resp = self.client.get(
            RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_datacollection_paakayttaja_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(
            RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_datacollection_statistics(self):
        """Check data-collection paakayttaja response fields"""
        add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        kysely_data = resp.json()[1]
        self.assertEqual(kysely_data["nimi_fi"], "datacollection_paakayttaja_kysymysryhma")
        self.assertEqual(kysely_data["nimi_sv"], None)
        self.assertEqual(kysely_data["lomaketyyppi"], "henkilostolomake_prosessitekijat")
        self.assertEqual(kysely_data["indicators"]["main_indicator"]["key"], "pedagoginen_prosessi")
        self.assertEqual(kysely_data["indicators"]["secondary_indicators"][0]["key"],
                         "myonteinen_ja_sitoutunut_vuorovaik")
        self.assertEqual(kysely_data["indicators"]["secondary_indicators"][1]["key"],
                         "vastavuoroinen_vuorovaikutus")
        self.assertEqual(kysely_data["is_closed"], False)
        # Toimipaikka
        toimipaikka_statistics = kysely_data["toimipaikka_statistics"]
        self.assertEqual(toimipaikka_statistics["in_use_count"], 6)
        self.assertEqual(toimipaikka_statistics["sent_count"], 6)
        self.assertEqual(toimipaikka_statistics["answered_count"], 5)
        self.assertEqual(toimipaikka_statistics["answer_pct"], 83)
        self.assertEqual(
            toimipaikka_statistics["extra_data"]["answer_pct_lt_50"][0]["nimi_fi"], "datacollection_not_sent")
        self.assertEqual(toimipaikka_statistics["extra_data"]["answer_pct_lt_50"][0]["answer_pct"], 0)
        # Vastaaja
        vastaaja_statistics = kysely_data["vastaaja_statistics"]
        self.assertEqual(vastaaja_statistics["sent_count"], 17)
        self.assertEqual(vastaaja_statistics["answered_count"], 7)
        self.assertEqual(vastaaja_statistics["answer_pct"], 41)

    @responses.activate
    def test_get_datacollection_koulutustoimija_param_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(
            RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja"
            "&koulutustoimija=0.1.20.1")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        kysely_data = resp.json()[0]
        self.assertEqual(kysely_data["nimi_fi"], "datacollection_paakayttaja_kysymysryhma")
        self.assertEqual(kysely_data["nimi_sv"], None)
        self.assertEqual(kysely_data["lomaketyyppi"], "henkilostolomake_prosessitekijat")
        self.assertEqual(kysely_data["indicators"]["main_indicator"]["key"], "pedagoginen_prosessi")
        self.assertEqual(kysely_data["indicators"]["secondary_indicators"][0]["key"],
                         "myonteinen_ja_sitoutunut_vuorovaik")
        self.assertEqual(kysely_data["indicators"]["secondary_indicators"][1]["key"],
                         "vastavuoroinen_vuorovaikutus")
        self.assertEqual(kysely_data["is_closed"], False)
        # Toimipaikka
        toimipaikka_statistics = kysely_data["toimipaikka_statistics"]
        self.assertEqual(toimipaikka_statistics["in_use_count"], 5)
        self.assertEqual(toimipaikka_statistics["sent_count"], 5)
        self.assertEqual(toimipaikka_statistics["answered_count"], 5)
        self.assertEqual(toimipaikka_statistics["answer_pct"], 100)
        self.assertEqual(
            toimipaikka_statistics["extra_data"]["answer_pct_lt_50"][0]["nimi_fi"], "dc_toimipaikka3")
        self.assertEqual(toimipaikka_statistics["extra_data"]["answer_pct_lt_50"][0]["answer_pct"], 25)
        # Vastaaja
        vastaaja_statistics = kysely_data["vastaaja_statistics"]
        self.assertEqual(vastaaja_statistics["sent_count"], 16)
        self.assertEqual(vastaaja_statistics["answered_count"], 7)
        self.assertEqual(vastaaja_statistics["answer_pct"], 44)

    @responses.activate
    def test_get_datacollection_koulutustoimija_not_found(self):
        add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(
            RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja"
            "&koulutustoimija=notfound")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))

    @responses.activate
    def test_get_datacollection_latest_answer_date(self):
        """Check data-collection latest answer date is correct"""
        add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        kysely_data = resp.json()[1]
        self.assertEqual(kysely_data["latest_answer_date"], datenow_delta(40).strftime(DATE_INPUT_FORMAT))

    @responses.activate
    def test_get_datacollection_pct_lt_50_order(self):
        """Check the order of answer_pct_lt_50 response.
        Should be lowest to highest, eg. [0, 25, 33, 44]
        """
        add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        kysely_data = resp.json()[1]
        toimipaikka_statistics = kysely_data["toimipaikka_statistics"]
        self.assertEqual(toimipaikka_statistics["extra_data"]["answer_pct_lt_50"][0]["answer_pct"], 0)
        self.assertEqual(toimipaikka_statistics["extra_data"]["answer_pct_lt_50"][1]["answer_pct"], 25)
        self.assertEqual(toimipaikka_statistics["extra_data"]["answer_pct_lt_50"][2]["answer_pct"], 33)
        self.assertEqual(toimipaikka_statistics["extra_data"]["answer_pct_lt_50"][3]["answer_pct"], 40)

    @responses.activate
    def test_get_datacollection_no_toimipaikka(self):
        """check that datacollection with no toimipaikka does not return toimipaikka data"""
        add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        toimipaikka_statistics = resp.json()[0]["toimipaikka_statistics"]

        self.assertEqual(toimipaikka_statistics["in_use_count"], None)
        self.assertEqual(toimipaikka_statistics["sent_count"], None)
        self.assertEqual(toimipaikka_statistics["answered_count"], None)
        self.assertEqual(toimipaikka_statistics["answer_pct"], None)
        self.assertEqual(toimipaikka_statistics["extra_data"], {})


@override_settings(RATELIMIT_ENABLE=False)
class DataCollectionYllapitajaGetTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_datacollection_yllapitaja_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=yllapitaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_datacollection_statistics(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=yllapitaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        timenow = timezone.now().strftime(DATE_INPUT_FORMAT)
        timenow_plus_30d = datenow_delta(30).strftime(DATE_INPUT_FORMAT)
        timenow_minus_100d = datenow_delta(-100).strftime(DATE_INPUT_FORMAT)
        stats = resp.json()[0]
        self.assertEqual(stats["nimi_fi"], "dc_pk_no_toimipaikka")
        self.assertEqual(stats["lomaketyyppi"], "asiantuntijalomake_paakayttaja_prosessitekijat")
        self.assertEqual(stats["released_date"], timenow)
        self.assertEqual(stats["earliest_usage_date"], timenow)
        self.assertEqual(stats["latest_ending_date"], timenow_plus_30d)
        koulutustoimija_names = stats["koulutustoimija_statistics"]["extra_data"]["koulutustoimija_names"]["fi"]
        self.assertEqual(len(koulutustoimija_names), 1)
        self.assertEqual(koulutustoimija_names[0], "datacollection_toimija")

        stats = resp.json()[1]
        self.assertEqual(stats["nimi_fi"], "datacollection_paakayttaja_kysymysryhma")
        self.assertEqual(stats["lomaketyyppi"], "henkilostolomake_prosessitekijat")
        self.assertEqual(stats["koulutustoimija_statistics"]["in_use_count"], 2)
        self.assertEqual(stats["koulutustoimija_statistics"]["sent_count"], 2)
        self.assertEqual(stats["oppilaitos_statistics"]["in_use_count"], 6)
        self.assertEqual(stats["oppilaitos_statistics"]["sent_count"], 6)
        self.assertEqual(stats["vastaaja_statistics"]["sent_count"], 17)
        self.assertEqual(stats["vastaaja_statistics"]["answered_count"], 7)
        self.assertEqual(stats["vastaaja_statistics"]["answer_pct"], 41)

        stats = resp.json()[2]
        self.assertEqual(stats["nimi_fi"], "testikysymysryhma1")
        self.assertEqual(stats["earliest_usage_date"], timenow_minus_100d)
        koulutustoimija_names = stats["koulutustoimija_statistics"]["extra_data"]["koulutustoimija_names"]["fi"]
        self.assertEqual(len(koulutustoimija_names), 1)
        self.assertEqual(koulutustoimija_names[0], "testikoulutustoimija1")

    @responses.activate
    def test_get_datacollection_start_date(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        timenow_minus_30d = datenow_delta(-30).strftime(DATE_INPUT_FORMAT)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/data-collection/"
                               f"?role=yllapitaja&start_date={timenow_minus_30d}")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 3)

    @responses.activate
    def test_get_datacollection_end_date(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        timenow_minus_30d = datenow_delta(-30).strftime(DATE_INPUT_FORMAT)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/data-collection/"
                               f"?role=yllapitaja&end_date={timenow_minus_30d}")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["nimi_fi"], "testikysymysryhma1")

    @responses.activate
    def test_get_datacollection_yllapitaja_as_toteuttaja_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=yllapitaja")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @responses.activate
    def test_get_datacollection_yllapitaja_as_paakayttaja_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=yllapitaja")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(RATELIMIT_ENABLE=False)
class LimitedDataTests(TestCase):
    """Get tests for the data-collection"""
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_datacollection_paakayttaja_no_data(self):
        """Check that additional statistics do not return anything when there is no kyselykerta"""
        add_test_kayttajat()
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/data-collection/?role=paakayttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json(), [])


@override_settings(RATELIMIT_ENABLE=False)
class WrongMethodTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_put_datacollection_fail(self):
        resp = self.client.put(RAPORTOINTIPALVELU_API_URL + "/data-collection/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_datacollection_fail(self):
        resp = self.client.delete(RAPORTOINTIPALVELU_API_URL + "/data-collection/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_datacollection_fail(self):
        resp = self.client.post(RAPORTOINTIPALVELU_API_URL + "/data-collection/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
