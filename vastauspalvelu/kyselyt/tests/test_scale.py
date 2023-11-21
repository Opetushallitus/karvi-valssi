import responses

from django.conf import settings
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    add_testing_responses_virkailijapalvelu_scale, add_testing_responses_virkailijapalvelu_scale_fail)


BASE_URL = settings.BASE_URL
VASTAUSPALVELU_API_URL = f"/{BASE_URL}api/v1"


class ScaleTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @responses.activate
    def test_get_scales_ok(self):
        add_testing_responses_virkailijapalvelu_scale(responses)
        resp = self.client.get(f"{VASTAUSPALVELU_API_URL}/scale/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["name"], "asteikko1")

    @responses.activate
    def test_get_scales_fail(self):
        add_testing_responses_virkailijapalvelu_scale_fail(responses)
        resp = self.client.get(f"{VASTAUSPALVELU_API_URL}/scale/")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
