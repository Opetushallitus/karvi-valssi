from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data
from kyselyt.models import Kysymys, TempVastaus, Kysely


BASE_URL = settings.BASE_URL
VASTAUSPALVELU_API_URL = f"/{BASE_URL}api/v1"


@override_settings(RATELIMIT_ENABLE=False)
class TempVastausTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_post_tempvastaus_ok(self):
        data = {
            "vastaajatunnus": "testivastaajatunnus1_5",
            "vastaukset": [
                {
                    "kysymysid": "1",
                    "numerovalinta": 1,
                    "string": "testi",
                    "en_osaa_sanoa": True
                },
                {
                    "kysymysid": "2",
                    "numerovalinta": 2
                }
            ]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/tempvastaus/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # check data in db
        kysely = Kysely.objects.filter(nimi_fi="testikysely1").first()
        tempvastauses = TempVastaus.objects.filter(vastaajatunnus="testivastaajatunnus1_5")
        self.assertEqual(tempvastauses.count(), 2)
        self.assertEqual(tempvastauses[0].kysymysid, "1")
        self.assertEqual(tempvastauses[0].kysely_voimassa_loppupvm, kysely.voimassa_loppupvm)
        self.assertEqual(tempvastauses[0].numerovalinta, 1)
        self.assertEqual(tempvastauses[0].string, "testi")
        self.assertEqual(tempvastauses[0].en_osaa_sanoa, True)

        # check getting tempvastaus the same answers
        resp = self.client.get(VASTAUSPALVELU_API_URL + "/tempvastaus/testivastaajatunnus1_5/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.json()), 2)
        self.assertEqual(resp.json()[0]["kysymysid"], "1")
        self.assertEqual(resp.json()[0]["numerovalinta"], "1")
        self.assertEqual(resp.json()[0]["string"], "testi")
        self.assertEqual(resp.json()[0]["en_osaa_sanoa"], True)
        self.assertEqual(resp.json()[1]["string"], None)

        # give answers
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_5", "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 2}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        # check data is removed in db after answering
        tempvastauses = TempVastaus.objects.filter(vastaajatunnus="testivastaajatunnus1_5")
        self.assertEqual(tempvastauses.count(), 0)

    def test_post_tempvastaus_vastaajatunnus_missing_fail(self):
        data = {"vastaukset": []}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/tempvastaus/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_tempvastaus_vastaukset_missing_fail(self):
        data = {"vastaajatunnus": "tunnus"}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/tempvastaus/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_tempvastaus_locked_vastaajatunnus_fail(self):
        data = {"vastaajatunnus": "testivastaajatunnus1_2", "vastaukset": []}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/tempvastaus/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AR002" in str(resp.json()))

    def test_post_tempvastaus_vastaajatunnus_not_single_use_fail(self):
        data = {"vastaajatunnus": "testivastaajatunnus1_1", "vastaukset": []}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/tempvastaus/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AR006" in str(resp.json()))
