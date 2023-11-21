
import weasyprint

from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data
from kyselyt.tests.constants import (
    BASE_URL, VIRKAILIJAPALVELU_API_URL, TEST_USER, get_test_access_token, get_test_refresh_token)
from kyselyt.utils import add_token_to_blacklist


@override_settings(RATELIMIT_ENABLE=False)
class AdminPageTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_admin_page(self):
        resp = self.client.get(f"/{BASE_URL}admin/", follow=True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class PdfCreationTests(TestCase):
    def test_pdf_creation(self):
        pdf_file = None
        try:
            pdf_file = weasyprint.HTML(string="<html>something</html>").write_pdf()
        except Exception:
            pass
        self.assertIsNotNone(pdf_file)


@override_settings(RATELIMIT_ENABLE=False)
class AccessTokenTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.refresh_token = get_test_refresh_token(self.client)

    def test_post_token_faulty_credentials(self):
        faulty_cred = {"username": "test-user", "password": "faulty-pw"}
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/token/", data=faulty_cred, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_refresh_access_token_ok(self):
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/token/refresh/",
            data={"refresh": self.refresh_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in resp.json())
        first_cookie = resp.cookies["virkailijapalvelu_access_token"]
        self.assertTrue(resp.json().get("access") in str(first_cookie))
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/token/refresh/",
            data={"refresh": self.refresh_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue("access" in resp.json())
        second_cookie = resp.cookies["virkailijapalvelu_access_token"]
        self.assertTrue(resp.json().get("access") in str(second_cookie))
        self.assertNotEqual(first_cookie, second_cookie)


class AccessTokenBruteforceTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_access_token_bruteforce_exceed_ratelimit(self):
        # +10 is for ensuring test wont fail because internal rate calculation system which sometimes occur
        for i in range(settings.TOKEN_RATELIMIT_PER_MINUTE + 10):
            get_test_access_token(self.client)
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/token/", data=TEST_USER, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(RATELIMIT_ENABLE=False)
class RefreshTokenBlacklistTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.refresh_token = get_test_refresh_token(self.client)

    def test_refresh_token_blacklisting(self):
        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/token/refresh/",
            data={"refresh": self.refresh_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        add_token_to_blacklist(self.refresh_token)

        resp = self.client.post(
            f"{VIRKAILIJAPALVELU_API_URL}/token/refresh/",
            data={"refresh": self.refresh_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
