import responses

from datetime import datetime

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.migrations.testing.setup import (
    add_testing_responses_kayttooikeus_organisaatiot_empty, add_testing_responses_kayttooikeus_paakayttaja_ok,
    add_testing_responses_kayttooikeus_yllapitaja_ok, add_test_user, add_test_results,
    add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok)
from raportointi.models import Kysely, Result, Kysymysryhma
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class ResultPostTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_results()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_post_result_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely3")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma3")
        post_data = {
            "kysymysryhmaid": kysymysryhma.kysymysryhmaid,
            "koulutustoimija": kysely.koulutustoimija.oid,
            "kysely_voimassa_alkupvm": kysely.voimassa_alkupvm,
            "kuvaus": "testi1",
            "aineisto": "testi2",
            "vahvuudet": "testi3",
            "kohteet": "testi4",
            "keh_toimenpiteet": "testi5",
            "seur_toimenpiteet": "testi6",
            "is_locked": True}
        resp = self.client.post(f"{RAPORTOINTIPALVELU_API_URL}/result/", data=post_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # check data in db
        results = Result.objects.filter(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        self.assertEqual(results.count(), 1)
        result = results.first()
        self.assertEqual(result.kuvaus, "testi1")
        self.assertEqual(result.aineisto, "testi2")
        self.assertEqual(result.vahvuudet, "testi3")
        self.assertEqual(result.kohteet, "testi4")
        self.assertEqual(result.keh_toimenpiteet, "testi5")
        self.assertEqual(result.seur_toimenpiteet, "testi6")
        self.assertEqual(result.is_locked, True)
        self.assertEqual(result.taustatiedot["koulutustoimija"], kysely.koulutustoimija.oid)
        self.assertEqual(result.taustatiedot["paaindikaattori"], "pedagoginen_prosessi")
        self.assertEqual(result.taustatiedot["sekondaariset_indikaattorit"], ["toiminnan_havainnointi"])
        self.assertEqual(result.taustatiedot["kysymysryhma_name"]["fi"], "summary_testikysymysryhma3")

    @responses.activate
    def test_post_result_multiple_result_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        post_data = {
            "kysymysryhmaid": kysymysryhma.kysymysryhmaid,
            "koulutustoimija": kysely.koulutustoimija.oid,
            "kysely_voimassa_alkupvm": kysely.voimassa_alkupvm,
            "kuvaus": "testi1",
            "aineisto": "testi2",
            "vahvuudet": "testi3",
            "kohteet": "testi4",
            "keh_toimenpiteet": "testi5",
            "seur_toimenpiteet": "testi6",
            "is_locked": True}
        resp = self.client.post(f"{RAPORTOINTIPALVELU_API_URL}/result/", data=post_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("unique set" in str(resp.json()))

    def test_post_result_fields_missing_fail(self):
        resp = self.client.post(f"{RAPORTOINTIPALVELU_API_URL}/result/", data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("kysymysryhmaid" in str(resp.json()))
        self.assertTrue("koulutustoimija" in str(resp.json()))
        self.assertTrue("kysely_voimassa_alkupvm" in str(resp.json()))
        self.assertTrue("required" in str(resp.json()))

    @responses.activate
    def test_post_result_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely3")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma3")
        post_data = {
            "kysymysryhmaid": kysymysryhma.kysymysryhmaid,
            "koulutustoimija": kysely.koulutustoimija.oid,
            "kysely_voimassa_alkupvm": kysely.voimassa_alkupvm,
            "is_locked": True}
        resp = self.client.post(f"{RAPORTOINTIPALVELU_API_URL}/result/", data=post_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class ResultGetTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_results()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_result_paakayttaja_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)

        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/"
                               f"kysymysryhmaid={kysymysryhma.kysymysryhmaid}/"
                               f"koulutustoimija={kysely.koulutustoimija.oid}/"
                               f"alkupvm={kysely.voimassa_alkupvm}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # check response data
        self.assertEqual(resp.json()["id"], result.id)
        self.assertEqual(resp.json()["kysymysryhmaid"], result.kysymysryhmaid)
        self.assertEqual(resp.json()["koulutustoimija"], result.koulutustoimija)
        self.assertEqual(resp.json()["kysely_voimassa_alkupvm"],
                         datetime.strftime(result.kysely_voimassa_alkupvm, "%Y-%m-%d"))
        self.assertEqual(resp.json()["kuvaus"], "testi1")
        self.assertEqual(resp.json()["aineisto"], "testi2")
        self.assertEqual(resp.json()["vahvuudet"], "testi3")
        self.assertEqual(resp.json()["kohteet"], "testi4")
        self.assertEqual(resp.json()["keh_toimenpiteet"], "testi5")
        self.assertEqual(resp.json()["seur_toimenpiteet"], "testi6")
        self.assertEqual(resp.json()["is_locked"], True)
        self.assertEqual(resp.json()["taustatiedot"]["koulutustoimija"], result.koulutustoimija)
        self.assertEqual(resp.json()["taustatiedot"]["paaindikaattori"], "aa")

    @responses.activate
    def test_get_result_yllapitaja_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")

        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/"
                               f"kysymysryhmaid={kysymysryhma.kysymysryhmaid}/"
                               f"koulutustoimija={kysely.koulutustoimija.oid}/"
                               f"alkupvm={kysely.voimassa_alkupvm}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_result_result_not_found_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/result/kysymysryhmaid=999/koulutustoimija=0.1.2/alkupvm=2000-01-01/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["id"], None)
        self.assertEqual(resp.json()["kysymysryhmaid"], None)
        self.assertEqual(resp.json()["koulutustoimija"], None)
        self.assertEqual(resp.json()["kysely_voimassa_alkupvm"], None)
        self.assertEqual(resp.json()["kuvaus"], None)
        self.assertEqual(resp.json()["aineisto"], None)
        self.assertEqual(resp.json()["vahvuudet"], None)
        self.assertEqual(resp.json()["kohteet"], None)
        self.assertEqual(resp.json()["keh_toimenpiteet"], None)
        self.assertEqual(resp.json()["seur_toimenpiteet"], None)
        self.assertEqual(resp.json()["is_locked"], False)
        self.assertEqual(resp.json()["taustatiedot"]["koulutustoimija"], None)
        self.assertEqual(resp.json()["taustatiedot"]["paaindikaattori"], None)

    @responses.activate
    def test_get_result_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")

        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/"
                               f"kysymysryhmaid={kysymysryhma.kysymysryhmaid}/"
                               f"koulutustoimija={kysely.koulutustoimija.oid}/"
                               f"alkupvm={kysely.voimassa_alkupvm}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class ResultGetPdfTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_results()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_result_pdf_paakayttaja_permission_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)

        # language fi
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # language sv
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/pdf/?language=sv")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # base64
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/pdf/?language=fi&base64=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(type(resp.content), bytes)
        self.assertTrue(resp.content.startswith(b"JVBER"))

    @responses.activate
    def test_get_result_pdf_yllapitaja_permission_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_result_pdf_not_locked_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely2")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma2")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER022" in str(resp.json()))

    @responses.activate
    def test_get_result_pdf_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))

    def test_get_result_pdf_result_not_found_fail(self):
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/result/999/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER020" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class ResultUpdateTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_results()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_put_result_update_result_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely2")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma2")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        put_data = {"kuvaus": "updated"}
        resp = self.client.put(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/", data=put_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        result = Result.objects.get(id=result.id)
        # check updated value in db
        self.assertEqual(result.kuvaus, "updated")
        self.assertEqual(result.aineisto, "testi2")
        self.assertEqual(result.is_locked, False)

    @responses.activate
    def test_put_result_update_result_impersonate_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely2")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma2")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        put_data = {"kuvaus": "updated-imp"}
        resp = self.client.put(
            f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/", data=put_data, format="json",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        result = Result.objects.get(id=result.id)
        self.assertEqual(result.kuvaus, "updated-imp")

    @responses.activate
    def test_put_result_update_result_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely2")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma2")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        put_data = {"kuvaus": "updated-imp2"}
        resp = self.client.put(
            f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/", data=put_data, format="json",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        result = Result.objects.get(id=result.id)
        self.assertEqual(result.kuvaus, "updated-imp2")

    @responses.activate
    def test_put_result_update_result_locked_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        put_data = {"kuvaus": "updated"}
        resp = self.client.put(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/", data=put_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER021" in str(resp.json()))

    @responses.activate
    def test_put_result_update_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely2")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma2")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        put_data = {"kuvaus": "updated"}
        resp = self.client.put(f"{RAPORTOINTIPALVELU_API_URL}/result/{result.id}/", data=put_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class ResultListTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_results()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_result_list_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
        result = Result.objects.get(
            kysymysryhmaid=kysymysryhma.kysymysryhmaid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)

        # get summary and check response data
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/result/list/koulutustoimija={kysely.koulutustoimija.oid}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["id"], result.id)
        self.assertEqual(resp.json()[0]["kysymysryhmaid"], kysymysryhma.kysymysryhmaid)
        self.assertEqual(resp.json()[0]["koulutustoimija"], kysely.koulutustoimija.oid)
        self.assertEqual(resp.json()[0]["kuvaus"], "testi1")
        self.assertEqual(resp.json()[0]["aineisto"], "testi2")
        self.assertEqual(resp.json()[0]["vahvuudet"], "testi3")
        self.assertEqual(resp.json()[0]["kohteet"], "testi4")
        self.assertEqual(resp.json()[0]["keh_toimenpiteet"], "testi5")
        self.assertEqual(resp.json()[0]["seur_toimenpiteet"], "testi6")
        self.assertEqual(resp.json()[0]["taustatiedot"]["koulutustoimija"], kysely.koulutustoimija.oid)
        self.assertEqual(resp.json()[0]["taustatiedot"]["paaindikaattori"], "aa")

    @responses.activate
    def test_get_result_list_not_locked_not_listed_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely2")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/result/list/koulutustoimija={kysely.koulutustoimija.oid}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)

    @responses.activate
    def test_get_result_list_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/result/list/koulutustoimija={kysely.koulutustoimija.oid}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))
