import responses
from datetime import timedelta

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_kayttooikeus_ok,
    add_testing_responses_service_ticket, add_testing_responses_viestintapalvelu_token,
    add_testing_responses_viestintapalvelu_laheta_single,
    add_testing_responses_vastaajatunnus, add_testing_responses_viestintapalvelu_viestit, add_test_kyselysends,
    add_testing_responses_viestintapalvelu_laheta_update,
    add_testing_responses_varda_apikey, add_testing_responses_varda_tyontekijat,
    add_testing_responses_kayttooikeus_toteuttaja_ok, add_testing_responses_taustatiedot_ok,
    add_testing_responses_taustatiedot_missing, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok)
from kyselyt.models import Kyselykerta, KyselySend, Vastaajatunnus
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token


@override_settings(RATELIMIT_ENABLE=False)
class KyselysendPostTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_post_kyselysend_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a@a.aa", "tyontekija_id": 123}],
                "message": "testmessage"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json().get("created", None), 1)

        # check created kyselysend in db
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid, email="a@a.aa")
        self.assertEqual(kyselysends.count(), 1)
        self.assertEqual(kyselysends[0].tyontekija_id, 123)
        self.assertEqual(kyselysends[0].vastaajatunnus, "AAA001")
        self.assertEqual(kyselysends[0].message, "testmessage")

        # check kyselysend not duplicated
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json().get("created", None), 0)
        self.assertEqual(KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid, email="a@a.aa").count(), 1)

    @responses.activate
    def test_post_kyselysend_impersonate_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a@a.aa", "tyontekija_id": 123}],
                "message": "testmessage"}
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json().get("created", None), 1)

    @responses.activate
    def test_post_kyselysend_impersonate_org_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a@a.aa", "tyontekija_id": 123}],
                "message": "testmessage"}
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json().get("created", None), 1)

    @responses.activate
    def test_post_kyselysend_duplicate_email_noticed_once_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a2@a.aa"}, {"email": "a2@a.aa"}],
                "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json().get("created", None), 1)

        # check created kyselysend in db
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid, email="a2@a.aa")
        self.assertEqual(kyselysends.count(), 1)
        self.assertEqual(kyselysends[0].vastaajatunnus, "AAA001")

    @responses.activate
    def test_post_kyselysend_empty_tyontekijat_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [],
                "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_post_kyselysend_voimassa_too_early(self):
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm - timedelta(days=1),
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [],
                "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("VA006" in str(resp.json()))

    def test_post_kyselysend_voimassa_too_late(self):
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm + timedelta(days=1),
                "tyontekijat": [],
                "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("VA006" in str(resp.json()))

    def test_post_kyselysend_enddate_before_startdate(self):
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": "2022-01-02",
                "voimassa_loppupvm": "2022-01-01",
                "tyontekijat": [],
                "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("VA009" in str(resp.json()))

    def test_post_kyselysend_kysely_missing_fail(self):
        data = {"voimassa_alkupvm": "2022-01-01", "voimassa_loppupvm": "2022-12-31", "tyontekijat": [], "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("kyselykerta" in str(resp.json()))
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_kyselysend_tyontekijat_missing_fail(self):
        data = {"voimassa_alkupvm": "2022-01-01", "voimassa_loppupvm": "2022-12-31", "kyselykerta": 1, "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("tyontekijat" in str(resp.json()))
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_kyselysend_voimassa_alkupvm_missing_fail(self):
        data = {"voimassa_loppupvm": "2022-12-31", "kyselykerta": 1, "tyontekijat": [], "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("voimassa_alkupvm" in str(resp.json()))
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_kyselysend_voimassa_loppupvm_missing_fail(self):
        data = {"voimassa_alkupvm": "2022-01-01", "kyselykerta": 1, "tyontekijat": [], "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("voimassa_loppupvm" in str(resp.json()))
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_kyselysend_message_missing_fail(self):
        data = {"voimassa_alkupvm": "2022-01-01", "voimassa_loppupvm": "2022-12-31",
                "kyselykerta": 1, "tyontekijat": []}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("message" in str(resp.json()))
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_kyselysend_kyselykerta_locked_fail(self):
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta2")
        data = {"voimassa_alkupvm": "2022-01-01", "voimassa_loppupvm": "2022-12-31",
                "kyselykerta": kyselykerta.kyselykertaid, "tyontekijat": [], "message": ""}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER015" in str(resp.json()))

    @responses.activate
    def test_post_kyselysend_toteuttaja_sending_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a_tot@a.aa", "tyontekija_id": 123}],
                "message": "testmessage"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.json().get("created", None), 1)

        # check created kyselysend in db
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid, email="a_tot@a.aa")
        self.assertEqual(kyselysends.count(), 1)
        self.assertEqual(kyselysends[0].tyontekija_id, 123)

    @responses.activate
    def test_post_kyselysend_henkilostolomake_prosessitekijat_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a@a.aa", "tyontekija_id": 123}],
                "message": "testmessage"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # check created kyselysend in db
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid, email="a@a.aa")
        self.assertEqual(kyselysends.count(), 1)

        # check background info (taustatiedot)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_1")
        self.assertEqual(kyselykerta.metatiedot["toimipaikka"]["nimi"]["fi"], "testitoimipaikka1")
        self.assertEqual(kyselykerta.metatiedot["toimipaikka"]["toimipaikka_oid"], "0.1.3")
        self.assertEqual(kyselykerta.metatiedot["toimipaikka"]["postinumero"], "12345")
        self.assertEqual(kyselykerta.metatiedot["toimipaikka"]["toimintamuoto_koodi"], "tm-testi")
        self.assertEqual(kyselykerta.metatiedot["toimipaikka"]["jarjestamismuoto_koodit"], ["jm-testi"])
        self.assertEqual(kyselykerta.metatiedot["organisaatio"]["organisaatio_oid"], "0.1.2")
        self.assertEqual(kyselykerta.metatiedot["organisaatio"]["kunta_koodi"], "001")
        self.assertEqual(kyselykerta.metatiedot["taydennyskoulutukset"], None)
        self.assertEqual(kyselykerta.metatiedot["rakennetekijalomake_data"], None)

    @responses.activate
    def test_post_kyselysend_taydennyskoulutuslomake_rakennetekijat_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        add_testing_responses_taustatiedot_ok(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_2")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a@a.aa", "tyontekija_id": 123}],
                "message": "testmessage"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # check created kyselysend in db
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid, email="a@a.aa")
        self.assertEqual(kyselysends.count(), 1)

        # check background info (taustatiedot)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_2")
        self.assertEqual(kyselykerta.metatiedot["toimipaikka"], None)
        self.assertEqual(kyselykerta.metatiedot["organisaatio"]["organisaatio_oid"], "0.1.2")
        self.assertEqual(kyselykerta.metatiedot["organisaatio"]["kunta_koodi"], "001")

        self.assertEqual(kyselykerta.metatiedot["taydennyskoulutukset"]["koulutuspaivat"], "2.0")
        self.assertEqual(kyselykerta.metatiedot["taydennyskoulutukset"]["tehtavanimikkeet"], {"123": 1, "124": 1})
        self.assertEqual(
            kyselykerta.metatiedot["taydennyskoulutukset"]["tehtavanimikkeet_koulutuspaivat"],
            {"123": "1.0", "124": "1.0"})

        self.assertEqual(
            kyselykerta.metatiedot["rakennetekijalomake_data"]["toimipaikat"], dict(tm01=dict(jm01=1, total=1)))
        self.assertEqual(kyselykerta.metatiedot["rakennetekijalomake_data"]["lapset_voimassa"], 10)

        meta_tyontekijat = kyselykerta.metatiedot["rakennetekijalomake_data"]["tyontekijat"]
        self.assertEqual(meta_tyontekijat["total"], 12)
        self.assertEqual(meta_tyontekijat["tehtavanimikkeet"], {"123": 5, "124": 7})
        self.assertEqual(meta_tyontekijat["tehtavanimikkeet_kelpoiset"], {"123": 5, "124": 7})

        # check Vastaajatunnus' taustatiedot not added
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus="AAA092")
        self.assertEqual(vastaajatunnus.taustatiedot, {})

    @responses.activate
    def test_post_kyselysend_henkilostolomake_prosessitekijat_tyontekija_id_missing_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_1")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a@a.aa"}],
                "message": "testmessage"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @responses.activate
    def test_post_kyselysend_taydennyskoulutuslomake_rakennetekijat_tyontekija_id_missing_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        add_testing_responses_taustatiedot_ok(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_2")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a@a.aa"}],
                "message": "testmessage"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @responses.activate
    def test_post_kyselysend_taydennyskoulutuslomake_rakennetekijat_taustatiedot_missing(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_single(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_vastaajatunnus(responses)
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        add_testing_responses_taustatiedot_missing(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_2")
        data = {"kyselykerta": kyselykerta.kyselykertaid,
                "voimassa_alkupvm": kyselykerta.voimassa_alkupvm,
                "voimassa_loppupvm": kyselykerta.voimassa_loppupvm,
                "tyontekijat": [{"email": "a@a.aa", "tyontekija_id": 123}],
                "message": "testmessage"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # check background info (taustatiedot)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_2")
        self.assertEqual(kyselykerta.metatiedot["taydennyskoulutukset"], {})
        self.assertEqual(kyselykerta.metatiedot["rakennetekijalomake_data"]["toimipaikat"], {})
        self.assertEqual(kyselykerta.metatiedot["rakennetekijalomake_data"]["lapset_voimassa"], None)
        self.assertEqual(kyselykerta.metatiedot["rakennetekijalomake_data"]["tyontekijat"], {})

    def test_get_kyselysend_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kyselysend_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(RATELIMIT_ENABLE=False)
class KyselysendListTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_post_kyselysend_list_message_statuses_update_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_viestit(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()

        # before listing status is "failed" and "sent"
        self.assertEqual(KyselySend.objects.get(email="a1@ksl.aa").msg_status, "failed")
        self.assertEqual(KyselySend.objects.get(email="a2@ksl.aa").msg_status, "sent")
        self.assertEqual(KyselySend.objects.get(email="a4@ksl.aa").msg_status, "failed")

        kyselykertaid = Kyselykerta.objects.get(nimi="testikyselykerta3_2").kyselykertaid
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/list/?kyselykerta={kyselykertaid}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 4)

        # after listing status "failed" stays "failed"
        self.assertEqual(resp.json()[0]["tyontekija_id"], 21)
        self.assertEqual(resp.json()[0]["email"], "a1@ksl.aa")
        self.assertEqual(resp.json()[0]["msg_status"], "failed")
        self.assertEqual(KyselySend.objects.get(email="a1@ksl.aa").msg_status, "failed")

        # after listing statuses are "delivered"
        self.assertEqual(resp.json()[1]["tyontekija_id"], 22)
        self.assertEqual(resp.json()[1]["email"], "a2@ksl.aa")
        self.assertEqual(resp.json()[1]["msg_status"], "delivered")
        self.assertEqual(KyselySend.objects.get(email="a2@ksl.aa").msg_status, "delivered")
        self.assertEqual(resp.json()[2]["tyontekija_id"], None)
        self.assertEqual(resp.json()[2]["email"], "a3@ksl.aa")
        self.assertEqual(resp.json()[2]["msg_status"], "delivered")
        self.assertEqual(KyselySend.objects.get(email="a3@ksl.aa").msg_status, "delivered")
        self.assertEqual(resp.json()[3]["tyontekija_id"], 24)
        self.assertEqual(resp.json()[3]["email"], "a4@ksl.aa")
        self.assertEqual(resp.json()[3]["msg_status"], "delivered")
        self.assertEqual(KyselySend.objects.get(email="a4@ksl.aa").msg_status, "delivered")

    @responses.activate
    def test_post_kyselysend_list_impersonate_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_viestit(responses)
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)
        kyselykertaid = Kyselykerta.objects.get(nimi="testikyselykerta3_2").kyselykertaid
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/list/?kyselykerta={kyselykertaid}",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 4)

    @responses.activate
    def test_post_kyselysend_list_impersonate_org_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_viestit(responses)
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        kyselykertaid = Kyselykerta.objects.get(nimi="testikyselykerta3_2").kyselykertaid
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/list/?kyselykerta={kyselykertaid}",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 4)

    @responses.activate
    def test_post_kyselysend_list_kyselykerta_not_found_fail(self):
        add_testing_responses_kayttooikeus_ok(responses)
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/list/?kyselykerta=9999")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER006" in str(resp.json()))

    @responses.activate
    def test_post_kyselysend_list_kyselykerta_missing_fail(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/list/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("VA001" in str(resp.json()))

    def test_get_kyselysend_list_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/list/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kyselysend_list_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/list/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(RATELIMIT_ENABLE=False)
class KyselysendUpdateTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_put_kyselysend_update_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_update(responses)
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        # check database before update
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta3")
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid)
        self.assertEqual(kyselysends[0].email, "a1@ksu.aa")
        self.assertEqual(kyselysends[0].msg_status, "failed")
        self.assertEqual(kyselysends[0].msg_id, 111)
        data = [{"id": kyselysends[0].id, "email": "new1@ok.ok"},
                {"id": kyselysends[1].id, "email": "new2@ok.ok"}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("updates"), 2)
        # check changes in database after update
        kyselysend_1 = KyselySend.objects.get(id=kyselysends[0].id)
        self.assertEqual(kyselysend_1.email, "new1@ok.ok")
        self.assertEqual(kyselysend_1.msg_status, "updateok")
        self.assertEqual(kyselysend_1.msg_id, 121)
        kyselysend_2 = KyselySend.objects.get(id=kyselysends[1].id)
        self.assertEqual(kyselysend_2.email, "new2@ok.ok")
        self.assertEqual(kyselysend_2.msg_status, "updateok")
        self.assertEqual(kyselysend_2.msg_id, 122)

    @responses.activate
    def test_put_kyselysend_update_impersonate_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_update(responses)
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta3")
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid)
        data = [{"id": kyselysends[0].id, "email": "new1@ok.ok"},
                {"id": kyselysends[1].id, "email": "new2@ok.ok"}]
        resp = self.client.put(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("updates"), 2)

    @responses.activate
    def test_put_kyselysend_update_impersonate_org_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_update(responses)
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta3")
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid)
        data = [{"id": kyselysends[0].id, "email": "new1@ok.ok"},
                {"id": kyselysends[1].id, "email": "new2@ok.ok"}]
        resp = self.client.put(
            f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("updates"), 2)

    @responses.activate
    def test_put_kyselysend_update_toteuttaja_ok(self):
        add_testing_responses_viestintapalvelu_token(responses)
        add_testing_responses_viestintapalvelu_laheta_update(responses)
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        # check database before update
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta3")
        kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid)
        self.assertEqual(kyselysends[0].email, "a1@ksu.aa")
        self.assertEqual(kyselysends[0].msg_status, "failed")
        self.assertEqual(kyselysends[0].msg_id, 111)
        data = [{"id": kyselysends[0].id, "email": "new1@ok.ok"},
                {"id": kyselysends[1].id, "email": "new2@ok.ok"}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json().get("updates"), 2)

    @responses.activate
    def test_put_kyselysend_update_id_duplicate_fail(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        data = [{"id": 1, "email": "new1@ok.ok"},
                {"id": 1, "email": "new2@ok.ok"}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("VA004" in str(resp.json()))

    @responses.activate
    def test_put_kyselysend_update_non_existing_id_fail(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        data = [{"id": 9999, "email": "new1@ok.ok"}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("VA003" in str(resp.json()))

    @responses.activate
    def test_put_kyselysend_update_not_same_kyselykerta_fail(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_test_kyselysends()
        kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta3")
        kyselysend_id_1 = KyselySend.objects.filter(kyselykerta=kyselykerta.kyselykertaid)[0].id
        kyselysend_id_2 = KyselySend.objects.filter(kyselykerta=999)[0].id
        data = [{"id": kyselysend_id_1, "email": "new1@ok.ok"},
                {"id": kyselysend_id_2, "email": "new2@ok.ok"}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("VA002" in str(resp.json()))

    def test_put_kyselysend_update_id_missing_fail(self):
        data = [{"email": "new1@ok.ok"}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("id" in str(resp.json()))
        self.assertTrue("This field is required." in str(resp.json()))

    def test_put_kyselysend_update_email_missing_fail(self):
        data = [{"id": 123}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("email" in str(resp.json()))
        self.assertTrue("This field is required." in str(resp.json()))

    def test_put_kyselysend_update_faulty_email_fail(self):
        data = [{"id": 123, "email": "new1"}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Enter a valid email address." in str(resp.json()))

    def test_put_kyselysend_update_faulty_id_fail(self):
        data = [{"id": "a", "email": "new1@ok.ok"}]
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("A valid integer is required." in str(resp.json()))

    def test_get_kyselysend_update_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_post_kyselysend_update_fail(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kyselysend/update/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
