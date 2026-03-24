from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data, add_test_scales
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL


@override_settings(RATELIMIT_ENABLE=False)
class ScaleApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_get_scale_anonymous_ok(self):
        add_test_scales()
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/scale/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 2)  # scale count
        self.assertEqual(resp.json()[0]["name"], "scale1")
        self.assertEqual(resp.json()[0]["default_value"], 1)
        self.assertEqual(len(resp.json()[0]["scale"]), 3)
        self.assertEqual(resp.json()[0]["scale"][0]["value"], 1)
        self.assertEqual(resp.json()[0]["scale"][0]["fi"], "fi11")

    def test_post_scale_fail(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/scale/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_scale_fail(self):
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/scale/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
