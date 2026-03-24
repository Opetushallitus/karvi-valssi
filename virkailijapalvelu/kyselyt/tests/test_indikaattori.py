from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data, add_test_indikaattorit
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token


@override_settings(RATELIMIT_ENABLE=False)
class IndikaattoriApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_get_indikaattori_grouped_ok(self):
        add_test_indikaattorit()
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/indikaattori/grouped/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 3)  # group count
        self.assertEqual(resp.json()[0]["indicators"][0]["key"], "a1")
        self.assertEqual(resp.json()[0]["indicators"][0]["laatutekija"], "a")

    def test_get_indikaattori_grouped_ok_filter_laatutekija(self):
        add_test_indikaattorit()
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/indikaattori/grouped/?laatutekija=a")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 2)  # group count

    def test_get_indikaattori_grouped_ok_filter_group(self):
        add_test_indikaattorit()
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/indikaattori/grouped/?group_id=11")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)  # group count
        self.assertEqual(len(resp.json()[0]["indicators"]), 2)

    def test_get_indikaattori_grouped_ok_filter_visible(self):
        add_test_indikaattorit()
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/indikaattori/grouped/?group_id=21")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)  # group count
        self.assertEqual(len(resp.json()[0]["indicators"]), 2)

    def test_post_indikaattori_fail(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/indikaattori/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_indikaattori_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/indikaattori/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
