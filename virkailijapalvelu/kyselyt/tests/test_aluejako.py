import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.constants import MAX_ALUEJAKO_ALUE_COUNT
from kyselyt.migrations.testing.setup import (
    add_test_users, add_test_aluejako_organisaatiot, add_testing_responses_kayttooikeus_toteuttaja_ok,
    add_testing_responses_kayttooikeus_paakayttaja_ok, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok)
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token
from kyselyt.models import AluejakoAlue, Organisaatio


KOULUTUSTOIMIJA_OID = "0.1.2"
OPPILAITOS_OIDS = ["0.1.2.1", "0.1.2.2", "0.1.2.3"]
FIRST_OPPILAITOS = OPPILAITOS_OIDS[0]
EXTRA_OPPILAITOS = "0.1.2.4"


@override_settings(RATELIMIT_ENABLE=False)
class AluejakoTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        add_test_users()
        add_test_aluejako_organisaatiot()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_aluejako_list_empty(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)

        self.assertEqual(AluejakoAlue.objects.count(), 0)

        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/list/koulutustoimija={KOULUTUSTOIMIJA_OID}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()["grouped"]), 0)
        self.assertEqual(len(resp.json()["ungrouped"]), 1)
        self.assertEqual(len(resp.json()["ungrouped"][0]["oppilaitokset"]), 4)

    @responses.activate
    def test_aluejako_list_empty_impersonate(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses)

        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/aluejako/list/koulutustoimija={KOULUTUSTOIMIJA_OID}/",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_aluejako_list_empty_impersonate_org(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)

        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/aluejako/list/koulutustoimija={KOULUTUSTOIMIJA_OID}/",
            HTTP_IMPERSONATE_ORGANIZATION="some-org")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_aluejako_create(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)

        self.assertEqual(AluejakoAlue.objects.count(), 0)

        data = {"koulutustoimija": KOULUTUSTOIMIJA_OID, "name_fi": "Alue1", "name_sv": "SV Alue1"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/create/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AluejakoAlue.objects.count(), 1)

        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/list/koulutustoimija={KOULUTUSTOIMIJA_OID}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()["grouped"]), 1)
        self.assertEqual(resp.json()["grouped"][0]["name"]["fi"], "Alue1")
        self.assertEqual(len(resp.json()["ungrouped"]), 1)
        self.assertEqual(len(resp.json()["ungrouped"][0]["oppilaitokset"]), 4)
        self.assertEqual(resp.json()["ungrouped"][0]["oppilaitokset"][0]["name"]["fi"], "testitoimipaikka1")

    @responses.activate
    def test_aluejako_create_max_count_exceeded(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)

        self.assertEqual(AluejakoAlue.objects.count(), 0)

        for i in range(MAX_ALUEJAKO_ALUE_COUNT):
            data = {"koulutustoimija": KOULUTUSTOIMIJA_OID, "name_fi": f"Alue{i}", "name_sv": f"SV Alue{i}"}
            resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/create/", data, format="json")
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.assertEqual(AluejakoAlue.objects.count(), MAX_ALUEJAKO_ALUE_COUNT)

        data = {"koulutustoimija": KOULUTUSTOIMIJA_OID, "name_fi": "AlueX", "name_sv": "SV AlueX"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/create/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER025" in str(resp.json()))

    @responses.activate
    def test_aluejako_modify_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)

        self.assertEqual(AluejakoAlue.objects.count(), 0)
        alue = AluejakoAlue.objects.create(koulutustoimija=KOULUTUSTOIMIJA_OID, name_fi="Alue", name_sv="SV Alue")

        data = {
            "id": alue.id,
            "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue2", "name_sv": "SV Alue2",
            "oppilaitos_oids": OPPILAITOS_OIDS}
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["updates"], 3)

        # check changes are in listing
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/list/koulutustoimija={KOULUTUSTOIMIJA_OID}/")
        self.assertEqual(resp.json()["grouped"][0]["name"]["fi"], "Alue2")
        self.assertEqual(len(resp.json()["grouped"][0]["oppilaitokset"]), 3)
        self.assertEqual(resp.json()["grouped"][0]["oppilaitokset"][0]["name"]["fi"], "testitoimipaikka1")
        self.assertEqual(len(resp.json()["ungrouped"][0]["oppilaitokset"]), 1)

        # check oppilaitos aluejako is set correctly
        oppilaitos1 = Organisaatio.objects.get(oid=FIRST_OPPILAITOS)
        self.assertEqual(oppilaitos1.metatiedot.get("aluejako"), alue.id)

        # Test another oid list
        oppilaitos_oids = OPPILAITOS_OIDS[1:] + [EXTRA_OPPILAITOS]
        data = {
            "id": alue.id,
            "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue2", "name_sv": "SV Alue2",
            "oppilaitos_oids": oppilaitos_oids}
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")
        self.assertEqual(resp.json()["updates"], 3)

        # check oppilaitos aluejako is set correctly
        oppilaitos1 = Organisaatio.objects.get(oid=FIRST_OPPILAITOS)
        self.assertEqual(oppilaitos1.metatiedot.get("aluejako"), 0)
        oppilaitos4 = Organisaatio.objects.get(oid=EXTRA_OPPILAITOS)
        self.assertEqual(oppilaitos4.metatiedot.get("aluejako"), alue.id)

        # Test oid list length is not enough
        data = {
            "id": alue.id, "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue", "name_sv": "SV Alue",
            "oppilaitos_oids": OPPILAITOS_OIDS[:2]}
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")
        self.assertEqual(resp.json()["updates"], 0)

        # check oppilaitos aluejako is set 0
        oppilaitos1 = Organisaatio.objects.get(oid=FIRST_OPPILAITOS)
        self.assertEqual(oppilaitos1.metatiedot.get("aluejako"), 0)
        oppilaitos4 = Organisaatio.objects.get(oid=EXTRA_OPPILAITOS)
        self.assertEqual(oppilaitos4.metatiedot.get("aluejako"), 0)

    @responses.activate
    def test_aluejako_modify_alue_change(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)

        self.assertEqual(AluejakoAlue.objects.count(), 0)
        alue = AluejakoAlue.objects.create(koulutustoimija=KOULUTUSTOIMIJA_OID, name_fi="Alue", name_sv="SV Alue")
        alue2 = AluejakoAlue.objects.create(koulutustoimija=KOULUTUSTOIMIJA_OID, name_fi="Alue2", name_sv="SV Alue2")

        data = {
            "id": alue.id,
            "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue", "name_sv": "SV Alue",
            "oppilaitos_oids": OPPILAITOS_OIDS}
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")
        self.assertEqual(resp.json()["updates"], 3)

        # check oppilaitos aluejako is set correctly
        oppilaitos1 = Organisaatio.objects.get(oid=FIRST_OPPILAITOS)
        self.assertEqual(oppilaitos1.metatiedot.get("aluejako"), alue.id)

        # Test oppilaitoses partial move to another alue
        oppilaitos_oids = OPPILAITOS_OIDS[1:] + [EXTRA_OPPILAITOS]
        data = {
            "id": alue2.id,
            "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue2", "name_sv": "SV Alue2",
            "oppilaitos_oids": oppilaitos_oids}
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")
        self.assertEqual(resp.json()["updates"], 3)

        # check oppilaitos aluejako is set correctly
        oppilaitos1 = Organisaatio.objects.get(oid=FIRST_OPPILAITOS)
        self.assertEqual(oppilaitos1.metatiedot.get("aluejako"), 0)
        oppilaitos4 = Organisaatio.objects.get(oid=EXTRA_OPPILAITOS)
        self.assertEqual(oppilaitos4.metatiedot.get("aluejako"), alue2.id)

    def test_aluejako_modify_koulutustoimija_not_found(self):
        data = {
            "id": 999,
            "koulutustoimija": "not-found",
            "name_fi": "Alue", "name_sv": "SV Alue",
            "oppilaitos_oids": []}
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER024" in str(resp.json()))

    def test_aluejako_modify_alue_not_found(self):
        data = {
            "id": 999,
            "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue", "name_sv": "SV Alue",
            "oppilaitos_oids": []}
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER026" in str(resp.json()))

    @responses.activate
    def test_delete_aluejako(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)

        self.assertEqual(AluejakoAlue.objects.count(), 0)
        alue = AluejakoAlue.objects.create(koulutustoimija=KOULUTUSTOIMIJA_OID, name_fi="Alue", name_sv="SV Alue")

        data = {
            "id": alue.id,
            "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue", "name_sv": "SV Alue",
            "oppilaitos_oids": OPPILAITOS_OIDS}
        self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")

        data = {"id": alue.id, "koulutustoimija": KOULUTUSTOIMIJA_OID}
        resp = self.client.delete(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/delete/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

        # check oppilaitos aluejako is set 0 after delete
        oppilaitos1 = Organisaatio.objects.get(oid=FIRST_OPPILAITOS)
        self.assertEqual(oppilaitos1.metatiedot.get("aluejako"), 0)

    def test_delete_aluejako_koulutustoimija_not_found(self):
        data = {"id": 999, "koulutustoimija": "not-found"}
        resp = self.client.delete(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/delete/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER024" in str(resp.json()))

    def test_delete_aluejako_alue_not_found(self):
        data = {"id": 999, "koulutustoimija": KOULUTUSTOIMIJA_OID}
        resp = self.client.delete(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/delete/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER026" in str(resp.json()))

    @responses.activate
    def test_aluejako_list_no_permission(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)

        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/list/koulutustoimija={KOULUTUSTOIMIJA_OID}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @responses.activate
    def test_aluejako_create_no_permission(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)

        data = {
            "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue1", "name_sv": "SV Alue1"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/create/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    @responses.activate
    def test_aluejako_modify_no_permission(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)

        alue = AluejakoAlue.objects.create(koulutustoimija=KOULUTUSTOIMIJA_OID, name_fi="Alue2", name_sv="SV Alue2")

        data = {
            "id": alue.id,
            "koulutustoimija": KOULUTUSTOIMIJA_OID,
            "name_fi": "Alue", "name_sv": "SV Alue",
            "oppilaitos_oids": OPPILAITOS_OIDS}
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/aluejako/modify/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
