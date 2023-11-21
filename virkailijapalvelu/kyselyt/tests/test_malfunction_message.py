import responses

from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_test_malfunction_messages, add_testing_responses_kayttooikeus_yllapitaja_ok)
from kyselyt.models import MalfunctionMessage
from kyselyt.tests.constants import VIRKAILIJAPALVELU_API_URL, get_test_access_token


@override_settings(RATELIMIT_ENABLE=False)
class MalfunctionMessageTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()
        add_test_malfunction_messages()
        self.access_token = get_test_access_token(self.client)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_get_malfunction_message_get_active_ok(self):
        MalfunctionMessage.objects.filter(code=1).update(is_active=True)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/get-active/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["message"], "message1")

    @responses.activate
    def test_get_malfunction_message_list_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/list/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 2)
        self.assertEqual(resp.json()[0]["code"], 1)
        self.assertEqual(resp.json()[0]["message"], "message1")
        self.assertEqual(resp.json()[0]["is_active"], False)
        self.assertEqual(resp.json()[1]["code"], 2)
        self.assertEqual(resp.json()[1]["message"], "message2")
        self.assertEqual(resp.json()[1]["is_active"], False)

    @responses.activate
    def test_patch_malfunction_message_set_active_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)

        self.assertEqual(MalfunctionMessage.objects.filter(code=1).first().is_active, False)

        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/1/set-active/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(MalfunctionMessage.objects.filter(code=1).first().is_active, True)

        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/get-active/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["message"], "message1")

        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/list/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 2)
        self.assertEqual(resp.json()[0]["code"], 1)
        self.assertEqual(resp.json()[0]["message"], "message1")
        self.assertEqual(resp.json()[0]["is_active"], True)
        self.assertEqual(resp.json()[1]["code"], 2)
        self.assertEqual(resp.json()[1]["message"], "message2")
        self.assertEqual(resp.json()[1]["is_active"], False)

    @responses.activate
    def test_patch_malfunction_message_set_active_change_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)

        MalfunctionMessage.objects.filter(code=1).update(is_active=True)

        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/2/set-active/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(MalfunctionMessage.objects.filter(code=1).first().is_active, False)
        self.assertEqual(MalfunctionMessage.objects.filter(code=2).first().is_active, True)

        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/get-active/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["message"], "message2")

    @responses.activate
    def test_patch_malfunction_message_set_inactive_ok(self):
        add_testing_responses_kayttooikeus_yllapitaja_ok(responses)

        MalfunctionMessage.objects.filter(code=1).update(is_active=True)
        self.assertEqual(MalfunctionMessage.objects.filter(code=1).first().is_active, True)

        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/set-inactive/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertEqual(MalfunctionMessage.objects.filter(code=1).first().is_active, False)

        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/get-active/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["message"], None)

    def test_get_malfunction_message_list_no_permission(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/list/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_malfunction_message_set_active_no_permission(self):
        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/1/set-active/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_malfunction_message_set_inactive_no_permission(self):
        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/set-inactive/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_malfunction_message_get_active_wrong_methods(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/get-active/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/get-active/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/get-active/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_malfunction_message_list_wrong_methods(self):
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/list/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/list/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.patch(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/list/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_malfunction_message_set_active_wrong_methods(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/1/set-active/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/1/set-active/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/1/set-active/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_malfunction_message_set_inactive_wrong_methods(self):
        resp = self.client.get(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/set-inactive/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.post(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/set-inactive/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        resp = self.client.put(f"{VIRKAILIJAPALVELU_API_URL}/malfunction-message/set-inactive/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
