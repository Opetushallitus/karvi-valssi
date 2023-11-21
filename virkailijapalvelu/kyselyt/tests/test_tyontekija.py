import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_kayttooikeus_ok, add_testing_responses_kayttooikeus_organisaatiot_empty,
    add_testing_responses_service_ticket, add_testing_responses_service_ticket_fail_500,
    add_testing_responses_varda_apikey, add_testing_responses_varda_tyontekijat,
    add_testing_responses_kayttooikeus_toteuttaja_ok, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok)
from kyselyt.models import ExternalServices
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token


@override_settings(RATELIMIT_ENABLE=False)
class TyontekijaApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client, service_user=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_tyontekija_ok(self):
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_varda_tyontekijat(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/aaa001/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.json()["tehtavanimikkeet"]), 1)
        self.assertTrue(len(resp.json()["tutkinnot"]), 1)

    def test_get_tyontekija_tyontekijaid_missing_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/aaa002/")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue("ER008" in str(resp.json()))

    def test_get_tyontekija_kyselys_toimipaikka_missing_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/aaa003/")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue("ER009" in str(resp.json()))

    def test_get_tyontekija_access_token_missing(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/aaa001/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_tyontekija_access_token_faulty(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer faulty-token")
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/aaa001/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_tyontekija_normal_user_fail(self):
        self.access_token = get_test_access_token(self.client, service_user=False)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/aaa001/")
        self.assertTrue("User is not in group" in str(resp.json()))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_tyontekija_fail(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/aaa001/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_tyontekija_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/aaa001/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(RATELIMIT_ENABLE=False)
class TyontekijaListApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_tyontekija_list_ok(self):
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_varda_tyontekijat(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/toimipaikka=0.1.3/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["tyontekija_id"], 123)
        self.assertEqual(resp.json()[0]["kutsumanimi"], "aa")
        self.assertEqual(resp.json()[0]["sukunimi"], "aa")
        self.assertEqual(resp.json()[0]["email"], "a@a.aa")

        # check tehtavanimike data
        self.assertEqual(len(resp.json()[0]["tehtavanimikkeet"]), 1)
        tehtavanimike = resp.json()[0]["tehtavanimikkeet"][0]
        self.assertEqual(tehtavanimike["tehtavanimike_koodi"], "201")
        self.assertEqual(tehtavanimike["tehtavanimike_values"]["fi"]["nimi"], "a")
        self.assertEqual(tehtavanimike["tehtavanimike_values"]["sv"]["nimi"], "b")

    @responses.activate
    def test_get_tyontekija_list_impersonate_ok(self):
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_varda_tyontekijat(responses)
        add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses)
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/toimipaikka=0.1.3/",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["tyontekija_id"], 123)

    @responses.activate
    def test_get_tyontekija_list_impersonate_toteuttaja_fail(self):
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_kayttooikeus_toteuttaja_ok(responses)
        add_testing_responses_service_ticket(responses)
        add_testing_responses_varda_tyontekijat(responses)
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/toimipaikka=0.1.3/",
            HTTP_IMPERSONATE_USER="test-impersonate-user")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))

    @responses.activate
    def test_get_tyontekija_list_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        add_testing_responses_service_ticket(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/toimipaikka=0.1.3/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER010" in str(resp.json()))

    @responses.activate
    def test_get_tyontekija_list_tgt_appear_to_db_after_query(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket(responses)
        self.assertEqual(ExternalServices.objects.count(), 0)
        self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/toimipaikka=9999/")
        self.assertEqual(ExternalServices.objects.count(), 1)
        self.assertEqual(ExternalServices.objects.first().oph_tgt, "http://a")

    @responses.activate
    def test_get_tyontekija_list_tgt_clear_after_validity(self):
        add_testing_responses_kayttooikeus_ok(responses)
        add_testing_responses_service_ticket_fail_500(responses)
        ExternalServices.objects.get_or_create(id=1, defaults={"oph_tgt": "aaa"})
        self.assertEqual(ExternalServices.objects.first().oph_tgt, "aaa")
        self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/toimipaikka=9999/")
        self.assertEqual(ExternalServices.objects.first().oph_tgt, "")

    def test_get_tyontekija_list_access_token_missing(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/toimipaikka=9999/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("Authentication credentials were not provided" in str(resp.json()))

    def test_get_tyontekija_list_access_token_faulty(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer faulty-token")
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/toimipaikka=9999/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue("token_not_valid" in str(resp.json()))

    def test_post_tyontekija_list_fail(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_tyontekija_list_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/tyontekija/list/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
