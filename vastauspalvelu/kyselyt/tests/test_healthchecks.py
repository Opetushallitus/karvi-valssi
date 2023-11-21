from django.conf import settings
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data


BASE_URL = settings.BASE_URL


class HealthCheckTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_get_health_fail_without_worker(self):
        resp = self.client.get(f"/{BASE_URL}health/")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resp.json()["worker_active"], False)

    def test_get_healthdb_ok(self):
        resp = self.client.get(f"/{BASE_URL}health-db/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue("db" in resp.json() and resp.json()["db"] > 0)
