import responses

from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_virkailijapalvelu_tyontekija_OK,
    add_testing_responses_virkailijapalvelu_token)


BASE_URL = settings.BASE_URL
VASTAUSPALVELU_API_URL = f"/{BASE_URL}api/v1"


@override_settings(RATELIMIT_ENABLE=False)
class AdminPageTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_admin_page(self):
        resp = self.client.get(f"/{BASE_URL}admin/", follow=True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


@override_settings(RATELIMIT_USE_CACHE="default")
class BruteforceTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    @responses.activate
    def test_get_kyselykerta_bruteforce_exceed_ratelimit(self):
        add_testing_responses_virkailijapalvelu_token(responses)
        add_testing_responses_virkailijapalvelu_tyontekija_OK(responses)
        resp = self.client.get(f"{VASTAUSPALVELU_API_URL}/kyselykerta/testivastaajatunnus1_1/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # +10 is for ensuring test wont fail because internal rate calculation system which sometimes occur
        for i in range(settings.RATELIMIT_PER_MINUTE + 10):
            self.client.get(f"{VASTAUSPALVELU_API_URL}/kyselykerta/somecode{i}/")

        resp = self.client.get(f"{VASTAUSPALVELU_API_URL}/kyselykerta/testivastaajatunnus1_1/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_vastaa_bruteforce_exceed_ratelimit(self):
        data = {"vastaajatunnus": "NOTFOUND", "email": "", "vastaukset": []}
        resp = self.client.post(f"{VASTAUSPALVELU_API_URL}/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # +10 is for ensuring test wont fail because internal rate calculation system which sometimes occur
        for i in range(settings.RATELIMIT_PER_MINUTE + 10):
            data = {"vastaajatunnus": f"NOTFOUND{i}", "email": "", "vastaukset": []}
            self.client.post(f"{VASTAUSPALVELU_API_URL}/vastaa/", data, format="json")

        data = {"vastaajatunnus": "NOTFOUND", "email": "", "vastaukset": []}
        resp = self.client.post(f"{VASTAUSPALVELU_API_URL}/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
