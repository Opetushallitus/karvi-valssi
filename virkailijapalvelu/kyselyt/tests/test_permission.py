import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    add_test_users, add_test_organisaatiot_getpermission, add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_paakayttaja_ok,
    add_testing_responses_kayttooikeus_toteuttaja_getpermission_allowed_toimipaikka,
    add_testing_responses_kayttooikeus_toteuttaja_getpermission_anonymized_toimipaikka,
    add_testing_responses_kayttooikeus_toteuttaja_getpermission_tm_code_missing,
    add_testing_responses_kayttooikeus_organisaatiot_empty,
)
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token


@override_settings(RATELIMIT_ENABLE=False)
class PermissionEndpointTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        add_test_users()
        add_test_organisaatiot_getpermission()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_getpermission_yllapitaja_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/getpermission/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_getpermission_paakayttaja_ok(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/getpermission/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_getpermission_toteuttaja_allowed_tm_koodi_ok(self):
        add_testing_responses_kayttooikeus_toteuttaja_getpermission_allowed_toimipaikka(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/getpermission/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_getpermission_toteuttaja_anonymized_tm_koodi_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_getpermission_anonymized_toimipaikka(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/getpermission/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER027" in str(resp.json()))

    @responses.activate
    def test_get_getpermission_toteuttaja_tm_koodi_missing_fail(self):
        add_testing_responses_kayttooikeus_toteuttaja_getpermission_tm_code_missing(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/getpermission/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER027" in str(resp.json()))

    @responses.activate
    def test_get_getpermission_no_permission_fail(self):
        add_testing_responses_kayttooikeus_organisaatiot_empty(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/getpermission/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER027" in str(resp.json()))

    def test_get_getpermission_unauthorized_fail(self):
        self.client.credentials()  # Clear credentials
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/getpermission/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
