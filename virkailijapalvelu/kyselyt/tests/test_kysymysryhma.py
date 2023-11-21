import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.constants import TILAENUM_ARCHIVED
from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_kayttooikeus_ok,
    add_testing_responses_kayttooikeus_yllapitaja_ok,
    add_testing_responses_kayttooikeus_paakayttaja_ok)
from kyselyt.models import Kysymysryhma
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token


@override_settings(RATELIMIT_ENABLE=False)
class KysymysryhmaPdfApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_kysymysryhma_pdf_ok(self):
        add_testing_responses_kayttooikeus_ok(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma9_1")
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhma.kysymysryhmaid}/pdf/?language=fi")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_kysymysryhma_pdf_base64_ok(self):
        add_testing_responses_kayttooikeus_ok(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma9_1")
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhma.kysymysryhmaid}/pdf/?language=fi&base64=true")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(type(resp.content), bytes)
        self.assertTrue(resp.content.startswith(b"JVBER"))

    @responses.activate
    def test_get_kysymysryhma_pdf_not_published_yllapitaja_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma11")
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhma.kysymysryhmaid}/pdf/?language=fi")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_get_kysymysryhma_pdf_not_published_not_yllapitaja_fail(self):
        add_testing_responses_kayttooikeus_paakayttaja_ok(responses)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma11")
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhma.kysymysryhmaid}/pdf/?language=fi")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))

    def test_get_kysymysryhma_pdf_kysymysryhma_not_found_fail(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/999/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER016" in str(resp.json()))

    def test_get_kysymysryhma_pdf_unauthorized_fail(self):
        self.client.credentials(HTTP_AUTHORIZATION="")
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma9_1")
        resp = self.client.get(
            f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhma.kysymysryhmaid}/pdf/?language=fi")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_kysymysryhma_pdf_wrong_method_fail(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/1/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kysymysryhma_pdf_wrong_method_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/1/pdf/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(RATELIMIT_ENABLE=False)
class KysymysryhmaUsedApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_get_kysymysryhma_active_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhmaid}/used/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["is_used"], "active")

    @responses.activate
    def test_get_kysymysryhma_used_not_used_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/999/used/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["is_used"], "not_used")

    @responses.activate
    def test_get_kysymysryhma_used_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma10_3").kysymysryhmaid
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhmaid}/used/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["is_used"], "used")

    @responses.activate
    def test_get_kysymysryhma_used_no_permission_fail(self):
        add_testing_responses_kayttooikeus_ok(responses)  # no yllapitaja permission
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhmaid}/used/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue("ER011" in str(resp.json()))

    def test_get_kysymysryhma_used_id_missing(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma//used/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_kysymysryhma_used_wrong_method_fail(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/1/used/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kysymysryhma_used_wrong_method_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/1/used/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(RATELIMIT_ENABLE=False)
class KysymysryhmaSetArchivedApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    @responses.activate
    def test_patch_kysymysryhma_set_archived_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        kysymysryhmaid = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1").kysymysryhmaid
        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/{kysymysryhmaid}/set-archived/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["updates"], 1)
        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1")
        # check Kysymysryhma is archived after set-archived
        self.assertEqual(kysymysryhma.tila.nimi, TILAENUM_ARCHIVED)

    @responses.activate
    def test_patch_kysymysryhma_set_archived_kysymysryhma_not_found_fail(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/999/set-archived/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("ER016" in str(resp.json()))

    @responses.activate
    def test_patch_kysymysryhma_set_archived_no_permission_fail(self):
        add_testing_responses_kayttooikeus_ok(responses)  # no yllapitaja permission
        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/999/set-archived/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_kysymysryhma_set_archived_wrong_method_fail(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/1/set-archived/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kysymysryhma_set_archived_wrong_method_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/kysymysryhma/1/set-archived/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
