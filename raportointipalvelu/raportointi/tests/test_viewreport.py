import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from raportointi.constants import OPETUSHALLITUS_OID
from raportointi.migrations.testing.setup import (
    add_testing_responses_service_ticket, add_testing_responses_kayttooikeus_toteuttaja_ok, add_viewreport_data,
    add_testing_responses_kayttooikeus_paakayttaja_ok, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok,
    add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok)
from raportointi.models import Kysymysryhma, Kyselykerta
from raportointi.tests.constants import RAPORTOINTIPALVELU_API_URL, TEST_USER, TEST_DATABASES
from raportointi.utils import datenow_delta


def get_test_access_token(client) -> str:
    """Get access token for test-user"""
    resp = client.post(f"{RAPORTOINTIPALVELU_API_URL}/token/", data=TEST_USER).json()
    return resp.get("access")


@override_settings(RATELIMIT_ENABLE=False)
class ViewReportToteuttajaGetTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_viewreport_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_viewreport_toteuttaja_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=toteuttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["job_titles_fi"], None)

    @responses.activate
    def test_get_viewreport_toteuttaja_impersonate_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=toteuttaja",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_viewreport_toteuttaja_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=toteuttaja",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_viewreport_not_found_toteuttaja(self):
        """Check for 404 response"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        resp = self.client.get(RAPORTOINTIPALVELU_API_URL + "/view-kysymysryhma-report/999/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    @responses.activate
    def test_get_viewreport_data_toteuttaja(self):
        """Check that viewreport returns correct data"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=toteuttaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()

        self.assertEqual(data["nimi_fi"], "reportview_kysymysryhma")

        reporting_base = data["reporting_base"]
        self.assertEqual(reporting_base["nimi_fi"], "reportview_kysymysryhma")

        reporting_base_questions = reporting_base["questions"]
        self.assertEqual(reporting_base_questions[0]["kysymys_fi"], "view report matrix title")
        self.assertEqual(reporting_base_questions[0]["matrix_question_scale"][0]["fi"], "toteutuu erittäin heikosti")

        question_answers = reporting_base_questions[0]["question_answers"]
        self.assertEqual(len(question_answers["answers_pct"][0]), 5)
        self.assertEqual(question_answers["answers_pct"][0][0], 75)
        self.assertEqual(question_answers["answers_pct"][0][1], 0)
        self.assertEqual(question_answers["answers_pct"][0][2], 25)
        self.assertEqual(question_answers["answers_pct"][0][3], 0)
        self.assertEqual(question_answers["answers_pct"][0][4], 0)

        self.assertEqual(question_answers["answers_pct"][1][0], 18)
        self.assertEqual(question_answers["answers_pct"][1][1], 27)
        self.assertEqual(question_answers["answers_pct"][1][2], 14)
        self.assertEqual(question_answers["answers_pct"][1][3], 18)
        self.assertEqual(question_answers["answers_pct"][1][4], 23)

        self.assertEqual(question_answers["answers_int"][0][0], 6)
        self.assertEqual(question_answers["answers_int"][1][4], 5)

        self.assertEqual(question_answers["answers_sum"][0], 8)
        self.assertEqual(question_answers["answers_sum"][1], 22)

        self.assertEqual(question_answers["answers_available"][0], True)
        self.assertEqual(question_answers["answers_available"][1], True)

        self.assertEqual(question_answers["answers_average"][0], "1,5")
        self.assertEqual(question_answers["answers_average"][1], "3,0")

        matrix_questions = reporting_base_questions[0]["matriisikysymykset"]
        self.assertEqual(matrix_questions[0]["kysymys_fi"], "view report question1")
        self.assertEqual(matrix_questions[0]["matriisi_jarjestys"], 1)

        matrix_question_scale = reporting_base_questions[0]["matrix_question_scale"]
        self.assertEqual(matrix_question_scale[0]["fi"], "toteutuu erittäin heikosti")
        self.assertEqual(matrix_question_scale[0]["sv"], "genomförs mycket dåligt")
        self.assertEqual(matrix_question_scale[0]["value"], 1)

        self.assertEqual(matrix_question_scale[4]["fi"], "toteutuu erittäin hyvin")
        self.assertEqual(matrix_question_scale[4]["sv"], "genomförs mycket väl")
        self.assertEqual(matrix_question_scale[4]["value"], 5)

        self.assertEqual(data["survey_participants_count"], 19)
        self.assertEqual(data["survey_sent_count"], 19)

        timenow_minus_100d = datenow_delta(-100)
        self.assertEqual(data["available_kyselykertas"][0]["kyselykerta_alkupvm"],
                         timenow_minus_100d.strftime("%Y-%m-%d"))

    @responses.activate
    def test_get_viewreport_query_toteuttaja(self):
        """Check that query with toteuttaja does not work"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=toteuttaja&job_title_code=77826")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        question_answers = data["reporting_base"]["questions"][0]["question_answers"]
        self.assertEqual(question_answers["answers_pct"][0][0], 75)

    @responses.activate
    def test_get_viewreport_kyselykerta_query_data_toteuttaja(self):
        """Check that viewreport returns correct data with kyselykerta query"""
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        kyselykerta = Kyselykerta.objects.get(nimi="viewreport_kyselykerta_4")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=toteuttaja"
            f"&kyselykerta_alkupvm={kyselykerta.voimassa_alkupvm}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        question_answers = data["reporting_base"]["questions"][0]["question_answers"]

        self.assertEqual(question_answers["answers_pct"][0][0], 0)

        self.assertEqual(data["survey_participants_count"], 6)
        self.assertEqual(data["survey_sent_count"], 6)


@override_settings(RATELIMIT_ENABLE=False)
class ViewReportPaakayttajaGetTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_viewreport_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_viewreport_paakayttaja_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=paakayttaja")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_viewreport_paakayttaja_impersonate_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=paakayttaja",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_viewreport_paakayttaja_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=paakayttaja",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_viewreport_data_paakayttaja(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=paakayttaja")

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        self.assertEqual(data["survey_participants_count"], 19)
        self.assertEqual(data["survey_sent_count"], 19)

        self.assertEqual(data["koulutustoimija_nimi_fi"], "testikoulutustoimija1")

        time_now_minus_100d = datenow_delta(-100)
        self.assertEqual(data["created_date"], time_now_minus_100d.strftime("%d.%m.%Y"))

        self.assertEqual(data["job_titles_fi"][0]["name"], "test kindergarten")
        self.assertEqual(data["job_titles_fi"][0]["job_title_code"], "77826")

        self.assertEqual(data["job_titles_sv"][0]["name"], "test daghem")
        self.assertEqual(data["job_titles_sv"][0]["job_title_code"], "77826")

    @responses.activate
    def test_get_viewreport_query_ok_paakayttaja(self):
        """Check for OK response with query data"""
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=paakayttaja&job_title_code=77826")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=paakayttaja&eligibility=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/"
            "?role=paakayttaja&job_title_code=77826&eligibility=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_viewreport_query_data_paakayttaja(self):
        """Check that viewreport with query params returns correct data"""
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/"
            "?role=paakayttaja&job_title_code=77826&eligibility=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()

        self.assertEqual(data["nimi_fi"], "reportview_kysymysryhma")

        reporting_base = data["reporting_base"]
        self.assertEqual(reporting_base["nimi_fi"], "reportview_kysymysryhma")

        reporting_base_questions = reporting_base["questions"]
        self.assertEqual(reporting_base_questions[0]["kysymys_fi"], "view report matrix title")
        self.assertEqual(reporting_base_questions[0]["matrix_question_scale"][0]["fi"],
                         "toteutuu erittäin heikosti")

        question_answers = reporting_base_questions[0]["question_answers"]
        self.assertEqual(len(question_answers["answers_pct"][0]), 5)
        self.assertEqual(question_answers["answers_pct"][0][0], 0)
        self.assertEqual(question_answers["answers_pct"][0][1], 0)
        self.assertEqual(question_answers["answers_pct"][0][2], 0)
        self.assertEqual(question_answers["answers_pct"][0][3], 0)
        self.assertEqual(question_answers["answers_pct"][0][4], 0)

        self.assertEqual(question_answers["answers_pct"][1][0], 17)
        self.assertEqual(question_answers["answers_pct"][1][1], 25)
        self.assertEqual(question_answers["answers_pct"][1][2], 17)
        self.assertEqual(question_answers["answers_pct"][1][3], 17)
        self.assertEqual(question_answers["answers_pct"][1][4], 25)

        self.assertEqual(question_answers["answers_int"][0][0], 0)
        self.assertEqual(question_answers["answers_int"][1][4], 3)

        self.assertEqual(question_answers["answers_sum"][0], 0)
        self.assertEqual(question_answers["answers_sum"][1], 12)

        self.assertEqual(question_answers["answers_available"][0], False)
        self.assertEqual(question_answers["answers_available"][1], True)

        self.assertEqual(question_answers["answers_average"][0], "0")
        self.assertEqual(question_answers["answers_average"][1], "3,1")

        matrix_questions = reporting_base_questions[0]["matriisikysymykset"]
        self.assertEqual(matrix_questions[0]["kysymys_fi"], "view report question1")
        self.assertEqual(matrix_questions[0]["matriisi_jarjestys"], 1)

        matrix_question_scale = reporting_base_questions[0]["matrix_question_scale"]
        self.assertEqual(matrix_question_scale[0]["fi"], "toteutuu erittäin heikosti")
        self.assertEqual(matrix_question_scale[0]["sv"], "genomförs mycket dåligt")
        self.assertEqual(matrix_question_scale[0]["value"], 1)

        self.assertEqual(matrix_question_scale[4]["fi"], "toteutuu erittäin hyvin")
        self.assertEqual(matrix_question_scale[4]["sv"], "genomförs mycket väl")
        self.assertEqual(matrix_question_scale[4]["value"], 5)

        self.assertEqual(data["survey_participants_count"], 19)
        self.assertEqual(data["survey_sent_count"], 19)
        self.assertEqual(data["metatiedot"]["lomaketyyppi"], "henkilostolomake_prosessitekijat")

    @responses.activate
    def test_get_viewreport_kyselykerta_query_data_paakayttaja(self):
        """Check that viewreport returns correct data with kyselykerta query"""
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        kyselykerta = Kyselykerta.objects.get(nimi="viewreport_kyselykerta_4")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/"
            f"?role=paakayttaja&kyselykerta_alkupvm={kyselykerta.voimassa_alkupvm}")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        reporting_base = data["reporting_base"]
        reporting_base_questions = reporting_base["questions"]
        question_answers = reporting_base_questions[0]["question_answers"]

        self.assertEqual(question_answers["answers_pct"][0][0], 0)

        self.assertEqual(data["survey_participants_count"], 6)
        self.assertEqual(data["survey_sent_count"], 6)


@override_settings(RATELIMIT_ENABLE=False)
class ViewReportYllapitajaGetTests(TestCase):
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_viewreport_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_viewreport_yllapitaja_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija={OPETUSHALLITUS_OID}/?role=yllapitaja")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_viewreport_yllapitaja_as_toteuttaja_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/view-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/?role=yllapitaja")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))


@override_settings(RATELIMIT_ENABLE=False)
class DownloadReportTest(TestCase):
    """GET tests for view report as toteuttaja."""
    databases = TEST_DATABASES

    def setUp(self):
        self.client = APIClient()
        add_viewreport_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_download_report_pdf_ok(self):
        """Check for OK response"""
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        add_testing_responses_service_ticket(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")

        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/download-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.headers['content-type'], 'application/pdf')

    @responses.activate
    def test_download_report_pdf_impersonate_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/download-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_download_report_pdf_impersonate_org_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportview_kysymysryhma")
        resp = self.client.get(
            f"{RAPORTOINTIPALVELU_API_URL}/download-kysymysryhma-report/"
            f"kysymysryhmaid={kysymysryhma.pk}/koulutustoimija=0.1.2/",
            HTTP_IMPERSONATE_ORGANIZATION="0.1.2")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
