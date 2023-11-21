from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data


BASE_URL = settings.BASE_URL


class SetUpTestClient:

    def __init__(self, name):
        self.name = name

    def client(self):
        user = User.objects.filter(username=self.name)[0]
        api_c = APIClient()
        api_c.force_authenticate(user=user)
        return api_c


class HealthCheckTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="tester", password="12345")
        self.client = APIClient()
        load_testing_data()

    def test_get_health_fail_without_worker(self):
        resp = self.client.get(f"/{BASE_URL}health/")
        self.assertEqual(resp.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(resp.json()["worker_active"], False)
        self.assertEqual(resp.json()["failed_msgs"], 0)

    def test_get_healthdb_ok(self):
        client = SetUpTestClient("tester").client()
        resp = client.get(f"/{BASE_URL}health-db/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue("db" in resp.json() and resp.json()["db"] > 0)
