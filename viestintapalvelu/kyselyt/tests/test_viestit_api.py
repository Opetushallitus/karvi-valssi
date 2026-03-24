from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data
from kyselyt.models import Message
from kyselyt.tests.constants import get_test_access_token, VIESTINTAPALVELU_API_URL


@override_settings(RATELIMIT_ENABLE=False)
class ViestitApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_post_viestit_ok(self):
        msg_id = Message.objects.get(email="a001@a.aa").msg_id
        data = {"msg_ids": [msg_id]}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0].get("email"), "a001@a.aa")
        self.assertEqual(resp.json()[0].get("msg_id"), msg_id)
        self.assertEqual(resp.json()[0].get("template"), 1)

    def test_post_viestit_missing_ok(self):
        data = {"msg_ids": [9998, 9999]}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    def test_post_viestit_empty_list_ok(self):
        data = {"msg_ids": []}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 0)

    def test_post_viestit_list_missing_fail(self):
        data = {}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("msg_ids" in str(resp.json()))
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_viestit_wrong_type_fail(self):
        data = {"msg_ids": ["a"]}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("A valid integer is required." in str(resp.json()))

    def test_post_viestit_wrong_type_inside_the_list_fail(self):
        data = {"msg_ids": [1, "a", 5]}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("A valid integer is required." in str(resp.json()))

    def test_post_viestit_not_a_list_str_fail(self):
        data = {"msg_ids": "a"}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/", data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Expected a list of items" in str(resp.json()))

    def test_get_viestit_fail(self):
        resp = self.client.get(f"{VIESTINTAPALVELU_API_URL}/viestit/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_viestit_fail(self):
        resp = self.client.put(f"{VIESTINTAPALVELU_API_URL}/viestit/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(RATELIMIT_ENABLE=False)
class ViestitApiAccessTokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_post_viestit_access_token_missing(self):
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_viestit_access_token_faulty(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer faulty-key")
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/viestit/")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
