import html5validate
import responses

from datetime import datetime

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.migrations.testing.setup import (
    add_testing_responses_kayttooikeus_toteuttaja_ok, add_testing_responses_kayttooikeus_organisaatiot_empty,
    add_testing_responses_kayttooikeus_paakayttaja_ok, add_test_user, add_test_summaries,
    add_testing_responses_kayttooikeus_yllapitaja_ok, add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok,
    add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok, add_testing_responses_localisation_indikaattori)
from raportointi.models import Summary, Kysely
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES
from raportointi.utils_summary import create_summary_html


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class SummaryPostTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_summaries()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_post_summary_ok(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely3")
        post_data = {
            "kyselyid": kysely.kyselyid,
            "group_info": "test group",
            "kuvaus": "testi1",
            "aineisto": "testi2",
            "vahvuudet": "testi3",
            "kohteet": "testi4",
            "keh_toimenpiteet": "testi5",
            "seur_toimenpiteet": "testi6",
            "is_locked": True}
        resp = self.client.post(f"{RAPORTOINTIPALVELU_API_URL}/summary/", data=post_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # check data in db
        oppilaitos_oid = kysely.oppilaitos.oid
        summaries = Summary.objects.filter(oppilaitos=oppilaitos_oid, kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        self.assertEqual(summaries.count(), 1)
        summary = summaries.first()
        self.assertEqual(summary.group_info, "test group")
        self.assertEqual(summary.kuvaus, "testi1")
        self.assertEqual(summary.aineisto, "testi2")
        self.assertEqual(summary.vahvuudet, "testi3")
        self.assertEqual(summary.kohteet, "testi4")
        self.assertEqual(summary.keh_toimenpiteet, "testi5")
        self.assertEqual(summary.seur_toimenpiteet, "testi6")
        self.assertEqual(summary.is_locked, True)
        self.assertEqual(summary.taustatiedot["koulutustoimija"], kysely.koulutustoimija.oid)
        self.assertEqual(summary.taustatiedot["paaindikaattori"], "pedagoginen_prosessi")
        self.assertEqual(summary.taustatiedot["sekondaariset_indikaattorit"], ["toiminnan_havainnointi"])

    @responses.activate
    def test_post_summary_multiple_summary_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        post_data = {"kyselyid": kysely.kyselyid}

        resp = self.client.post(f"{RAPORTOINTIPALVELU_API_URL}/summary/", data=post_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER012" in str(resp.json()))

    def test_post_summary_kyselyid_missing_fail(self):
        resp = self.client.post(f"{RAPORTOINTIPALVELU_API_URL}/summary/", data={}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("kyselyid" in str(resp.json()))
        self.assertTrue("required" in str(resp.json()))

    @responses.activate
    def test_post_summary_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely3")
        post_data = {"kyselyid": kysely.kyselyid}
        resp = self.client.post(f"{RAPORTOINTIPALVELU_API_URL}/summary/", data=post_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class SummaryGetByKyselyIdTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_summaries()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_summary_ok(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)

        # get summary and check response data
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/kyselyid={kysely.kyselyid}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["id"], summary.id)
        self.assertEqual(resp.json()["kysymysryhmaid"], kysely.kysymysryhmat.first().kysymysryhmaid)
        self.assertEqual(resp.json()["oppilaitos"], kysely.oppilaitos.oid)
        self.assertEqual(resp.json()["kysely_voimassa_alkupvm"],
                         datetime.strftime(kysely.voimassa_alkupvm, "%Y-%m-%d"))
        self.assertEqual(resp.json()["group_info"], "testig")
        self.assertEqual(resp.json()["kuvaus"], "testi1")
        self.assertEqual(resp.json()["aineisto"], "testi2")
        self.assertEqual(resp.json()["vahvuudet"], "testi3")
        self.assertEqual(resp.json()["kohteet"], "testi4")
        self.assertEqual(resp.json()["keh_toimenpiteet"], "testi5")
        self.assertEqual(resp.json()["seur_toimenpiteet"], "testi6")
        self.assertEqual(resp.json()["is_locked"], True)
        self.assertEqual(resp.json()["taustatiedot"]["koulutustoimija"], kysely.koulutustoimija.oid)
        self.assertEqual(resp.json()["taustatiedot"]["paaindikaattori"], "aa")

    @responses.activate
    def test_get_summary_impersonate_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/summary/kyselyid={kysely.kyselyid}/",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_summary_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/summary/kyselyid={kysely.kyselyid}/",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_summary_summary_not_found_ok(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely3")
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/kyselyid={kysely.kyselyid}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["id"], None)
        self.assertEqual(resp.json()["kysymysryhmaid"], kysely.kysymysryhmat.first().kysymysryhmaid)
        self.assertEqual(resp.json()["oppilaitos"], kysely.oppilaitos.oid)
        self.assertEqual(resp.json()["kysely_voimassa_alkupvm"],
                         datetime.strftime(kysely.voimassa_alkupvm, "%Y-%m-%d"))
        self.assertEqual(resp.json()["group_info"], None)
        self.assertEqual(resp.json()["kuvaus"], None)
        self.assertEqual(resp.json()["aineisto"], None)
        self.assertEqual(resp.json()["vahvuudet"], None)
        self.assertEqual(resp.json()["kohteet"], None)
        self.assertEqual(resp.json()["keh_toimenpiteet"], None)
        self.assertEqual(resp.json()["seur_toimenpiteet"], None)
        self.assertEqual(resp.json()["is_locked"], False)
        self.assertEqual(resp.json()["taustatiedot"]["koulutustoimija"], kysely.koulutustoimija.oid)
        self.assertEqual(resp.json()["taustatiedot"]["paaindikaattori"], "pedagoginen_prosessi")

    @responses.activate
    def test_get_summary_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/kyselyid={kysely.kyselyid}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class SummaryGetByKyselyDataTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_summaries()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_summary_by_data_ok(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)

        # get summary and check response data
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/"
                               f"kysymysryhmaid={kysely.kysymysryhmat.first().kysymysryhmaid}/"
                               f"oppilaitos={kysely.oppilaitos.oid}/"
                               f"alkupvm={datetime.strftime(kysely.voimassa_alkupvm, '%Y-%m-%d')}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["id"], summary.id)
        self.assertEqual(resp.json()["kysymysryhmaid"], kysely.kysymysryhmat.first().kysymysryhmaid)
        self.assertEqual(resp.json()["oppilaitos"], kysely.oppilaitos.oid)
        self.assertEqual(resp.json()["kysely_voimassa_alkupvm"],
                         datetime.strftime(kysely.voimassa_alkupvm, "%Y-%m-%d"))
        self.assertEqual(resp.json()["group_info"], "testig")
        self.assertEqual(resp.json()["kuvaus"], "testi1")
        self.assertEqual(resp.json()["aineisto"], "testi2")
        self.assertEqual(resp.json()["vahvuudet"], "testi3")
        self.assertEqual(resp.json()["kohteet"], "testi4")
        self.assertEqual(resp.json()["keh_toimenpiteet"], "testi5")
        self.assertEqual(resp.json()["seur_toimenpiteet"], "testi6")
        self.assertEqual(resp.json()["is_locked"], True)
        self.assertEqual(resp.json()["taustatiedot"]["koulutustoimija"], kysely.koulutustoimija.oid)
        self.assertEqual(resp.json()["taustatiedot"]["paaindikaattori"], "aa")


@override_settings(RATELIMIT_ENABLE=False)
class SummaryGetPdfTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_summaries()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_summary_pdf_toteuttaja_permission_ok(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)

        # language fi
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # language sv
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/?language=sv")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # base64
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/?language=fi&base64=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(type(resp.content), bytes)
        self.assertTrue(resp.content.startswith(b"JVBER"))

    @responses.activate
    def test_get_summary_pdf_toteuttaja_impersonate_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_summary_pdf_toteuttaja_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_summary_pdf_paakayttaja_permission_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_summary_pdf_paakayttaja_impersonate_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_summary_pdf_paakayttaja_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_summary_pdf_not_locked_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely2")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER016" in str(resp.json()))

    @responses.activate
    def test_get_summary_pdf_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))

    def test_get_summary_pdf_summary_not_found_fail(self):
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/999/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER014" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class SummaryUpdateTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_summaries()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_put_summary_update_summary_ok(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely2")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        put_data = {"kuvaus": "updated"}
        resp = self.client.put(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/", data=put_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        summary = Summary.objects.get(id=summary.id)
        # check updated value in db
        self.assertEqual(summary.kuvaus, "updated")
        self.assertEqual(summary.aineisto, "testi2")
        self.assertEqual(summary.is_locked, False)

    @responses.activate
    def test_put_summary_update_summary_locked_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        put_data = {"kuvaus": "updated"}
        resp = self.client.put(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/", data=put_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("ER015" in str(resp.json()))

    @responses.activate
    def test_put_summary_update_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)
        put_data = {"kuvaus": "updated"}
        resp = self.client.put(f"{RAPORTOINTIPALVELU_API_URL}/summary/{summary.id}/", data=put_data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class SummaryListTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_summaries()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_summary_list_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)

        # get summary and check response data
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/list/"
                               f"kysymysryhmaid={kysely.kysymysryhmat.first().kysymysryhmaid}/"
                               f"alkupvm={kysely.voimassa_alkupvm}/"
                               f"koulutustoimija={kysely.koulutustoimija.oid}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["id"], summary.id)
        self.assertEqual(resp.json()[0]["oppilaitos"], kysely.oppilaitos.oid)
        self.assertEqual(resp.json()[0]["group_info"], "testig")
        self.assertEqual(resp.json()[0]["kuvaus"], "testi1")
        self.assertEqual(resp.json()[0]["aineisto"], "testi2")
        self.assertEqual(resp.json()[0]["vahvuudet"], "testi3")
        self.assertEqual(resp.json()[0]["kohteet"], "testi4")
        self.assertEqual(resp.json()[0]["keh_toimenpiteet"], "testi5")
        self.assertEqual(resp.json()[0]["seur_toimenpiteet"], "testi6")
        self.assertEqual(resp.json()[0]["taustatiedot"]["koulutustoimija"], kysely.koulutustoimija.oid)
        self.assertEqual(resp.json()[0]["taustatiedot"]["paaindikaattori"], "aa")

    @responses.activate
    def test_get_summary_list_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/list/"
                               f"kysymysryhmaid={kysely.kysymysryhmat.first().kysymysryhmaid}/"
                               f"alkupvm={kysely.voimassa_alkupvm}/"
                               f"koulutustoimija={kysely.koulutustoimija.oid}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


class SummaryPdfHtmlCreationTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        add_test_summaries()

    @responses.activate
    def test_summary_pdf_html_creation_by_kyselykertaid_validity(self):
        add_testing_responses_localisation_indikaattori(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        summary = Summary.objects.get(kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid)

        pdf_content = dict(
            title="test_title",
            koulutustoimija="test_koulutustoimija",
            group_info=summary.group_info,
            main_indicator_key=summary.taustatiedot.get("paaindikaattori"),
            secondary_indicator_keys=[],
            kuvaus=summary.kuvaus,
            aineisto=summary.aineisto,
            vahvuudet=summary.vahvuudet,
            kohteet=summary.kohteet,
            keh_toimenpiteet=summary.keh_toimenpiteet,
            seur_toimenpiteet=summary.seur_toimenpiteet)
        html_str = create_summary_html(pdf_content, "fi")
        html5validate.validate(html_str)

        self.assertTrue("test_title" in html_str)
        self.assertTrue("test_koulutustoimija" in html_str)
        self.assertTrue("testig" in html_str)
        self.assertTrue("FI indikaattori" in html_str)
        for i in range(1, 7):
            self.assertTrue(f"testi{i}" in html_str)


class SummaryCsvExportTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_test_user()
        add_test_summaries()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_summary_csv_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/csv/kysymysryhmaid="
                               f"{kysely.kysymysryhmat.first().kysymysryhmaid}/koulutustoimija="
                               f"{kysely.koulutustoimija.oid}/alkupvm={kysely.voimassa_alkupvm}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_summary_csv_base64_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysely = Kysely.objects.get(nimi_fi="summary_testikysely1")
        resp = self.client.get(f"{RAPORTOINTIPALVELU_API_URL}/summary/csv/kysymysryhmaid="
                               f"{kysely.kysymysryhmat.first().kysymysryhmaid}/koulutustoimija="
                               f"{kysely.koulutustoimija.oid}/alkupvm={kysely.voimassa_alkupvm}/?base64=true/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(type(resp.content), bytes)
        self.assertTrue(resp.content.startswith(b"\xef\xbb"))

    @responses.activate
    def test_get_summary_csv_no_permission_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/summary/csv/kysymysryhmaid=1/koulutustoimija=1/alkupvm=1/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
