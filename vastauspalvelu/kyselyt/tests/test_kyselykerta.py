from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data


BASE_URL = settings.BASE_URL
VASTAUSPALVELU_API_URL = f"/{BASE_URL}api/v1"


@override_settings(RATELIMIT_ENABLE=False)
class KyselykertaApiTests(TestCase):
    databases = ["valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_get_kyselykerta_ok(self):
        resp = self.client.get(VASTAUSPALVELU_API_URL + "/kyselykerta/testivastaajatunnus1_1/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["tempvastaus_allowed"], False)

    def test_get_kyselykerta_vastaajatunnus_single_use_ok(self):
        resp = self.client.get(VASTAUSPALVELU_API_URL + "/kyselykerta/testivastaajatunnus1_5/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["tempvastaus_allowed"], True)

    def test_get_kyselykerta_kysymysryhmat_list_sorted_ok(self):
        resp = self.client.get(VASTAUSPALVELU_API_URL + "/kyselykerta/testivastaajatunnus7_1/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["kysely"]["kysymysryhmat"][0]["jarjestys"], 0)
        self.assertEqual(resp.json()["kysely"]["kysymysryhmat"][1]["jarjestys"], 1)

    def test_get_kyselykerta_kysymykset_list_sorted_ok(self):
        resp = self.client.get(VASTAUSPALVELU_API_URL + "/kyselykerta/testivastaajatunnus7_1/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json()["kysely"]["kysymysryhmat"][1]["kysymysryhma"]["nimi_fi"], "testikysymysryhma7_1")
        self.assertEqual(resp.json()["kysely"]["kysymysryhmat"][1]["kysymysryhma"]["kysymykset"][0]["jarjestys"], 0)
        self.assertEqual(resp.json()["kysely"]["kysymysryhmat"][1]["kysymysryhma"]["kysymykset"][1]["jarjestys"], 1)

    def test_get_kyselykerta_matrix_ok(self):
        resp = self.client.get(VASTAUSPALVELU_API_URL + "/kyselykerta/testivastaajatunnus11/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        matriisi = resp.json()["kysely"]["kysymysryhmat"][0]["kysymysryhma"]["kysymykset"][0]
        self.assertEqual(matriisi["vastaustyyppi"], "matrix_root")
        self.assertEqual(matriisi["kysymys_fi"], "testikysymys11_0")
        self.assertEqual(len(matriisi["matriisikysymykset"]), 2)
        self.assertEqual(matriisi["matriisikysymykset"][0]["kysymys_fi"], "testikysymys11_1")


@override_settings(RATELIMIT_ENABLE=False)
class WrongMethodTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_kyselykerta_fail(self):
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/kyselykerta/somecode/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_kyselykerta_fail(self):
        resp = self.client.put(VASTAUSPALVELU_API_URL + "/kyselykerta/somecode/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_kyselykerta_fail(self):
        resp = self.client.delete(VASTAUSPALVELU_API_URL + "/kyselykerta/somecode/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
