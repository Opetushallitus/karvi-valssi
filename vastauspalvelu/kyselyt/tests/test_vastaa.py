import responses

from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_virkailijapalvelu_token, add_testing_responses_viestintapalvelu,
    add_testing_responses_virkailijapalvelu_tyontekija_info, add_testing_responses_virkailijapalvelu_scales)
from kyselyt.models import Vastaus, Vastaaja, Kysymys


BASE_URL = settings.BASE_URL
VASTAUSPALVELU_API_URL = f"/{BASE_URL}api/v1"


@override_settings(RATELIMIT_ENABLE=False)
class VastaaApiTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_post_vastaa_faulty_vastaajatunnus(self):
        data = {"vastaajatunnus": "NOTFOUND", "email": "", "vastaukset": []}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue("AR001" in str(resp.json()))

    def test_post_vastaa_vastaajatunnus_missing(self):
        data = {"email": "", "vastaukset": []}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_vastaa_locked_vastaajatunnus(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_2",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AR002" in str(resp.json()))

    def test_post_vastaa_vastaajatunnus_not_valid_yet(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_3",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AR004" in str(resp.json()))

    def test_post_vastaa_vastaajatunnus_not_valid_anymore(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_4",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AR005" in str(resp.json()))

    def test_post_vastaa_vastaajatunnus_locked_after_use(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_5",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AR002" in str(resp.json()))

    def test_post_vastaa_email_missing(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_5",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_vastaa_faulty_email(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_5",
                "email": "faulty_email",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Enter a valid email address" in str(resp.json()))

    @responses.activate
    def test_post_vastaa_email_ok(self):
        add_testing_responses_viestintapalvelu(responses)
        add_testing_responses_virkailijapalvelu_scales(responses)
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys8_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus8_2",
                "email": "a@a.aa",
                "vastaukset": [{"kysymysid": kysymysid, "string": "a"}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_post_vastaa_vastaukset_missing(self):
        data = {"vastaajatunnus": "testivastaajatunnus1_1", "email": ""}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("This field is required" in str(resp.json()))

    def test_post_vastaa_vastaukset_not_list(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": {"kysymysid": kysymysid, "numerovalinta": 3}}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("Expected a list" in str(resp.json()))

    def test_post_vastaa_missing_answer_add_to_db(self):
        data = {"vastaajatunnus": "testivastaajatunnus8_1", "email": "", "vastaukset": []}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus8_1").latest("luotuaika")
        vastaukset = Vastaus.objects.filter(vastaajaid=vastaaja.vastaajaid)
        self.assertEqual(len(vastaukset), 1)

    def test_post_vastaa_numerovalinta_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_6",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus1_6").latest("luotuaika")
        vastaus = Vastaus.objects.get(vastaajaid=vastaaja.vastaajaid, kysymysid=kysymysid)
        self.assertEqual(str(vastaus.numerovalinta), "3")

    def test_post_vastaa_numerovalinta_numvalue_as_string_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": str(kysymysid), "numerovalinta": "3"}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_post_vastaa_numerovalinta_mandatory_empty_str(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": ""}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN003" in str(resp.json()))

    def test_post_vastaa_numerovalinta_mandatory_none(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": None}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN003" in str(resp.json()))

    def test_post_vastaa_numerovalinta_numvalue_too_small(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 0}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("DY001" in str(resp.json()))

    def test_post_vastaa_numerovalinta_numvalue_too_big(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 6}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("DY001" in str(resp.json()))

    def test_post_vastaa_numerovalinta_numvalue_double(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1.3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("no more than 0 decimal places" in str(resp.json()))

    def test_post_vastaa_numerovalinta_not_mandatory_empty_str(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_1").kysymysid
        kysymysid2 = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": ""},
                               {"kysymysid": kysymysid2, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN003" in str(resp.json()))

    def test_post_vastaa_numerovalinta_not_mandatory_none(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_1").kysymysid
        kysymysid2 = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": None},
                               {"kysymysid": kysymysid2, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN003" in str(resp.json()))

    def test_post_vastaa_and_eos(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3, "en_osaa_sanoa": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN002" in str(resp.json()))

    def test_post_vastaa_eos_when_not_allowed(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_1").kysymysid
        kysymysid2 = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "en_osaa_sanoa": 1},
                               {"kysymysid": kysymysid2, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN001" in str(resp.json()))

    def test_post_vastaa_eos_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys3_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus3_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "en_osaa_sanoa": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus3_1").latest("luotuaika")
        vastaukset = Vastaus.objects.filter(vastaajaid=vastaaja.vastaajaid)
        self.assertEqual(len(vastaukset), 1)

    def test_post_vastaa_unrelated_question(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        kysymysid2 = Kysymys.objects.get(kysymys_fi="testikysymys2_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3},
                               {"kysymysid": kysymysid2, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN006" in str(resp.json()))

    def test_post_vastaa_duplicate(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3},
                               {"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN005" in str(resp.json()))

    def test_post_vastaa_locked_kyselykerta(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus2_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AR003" in str(resp.json()))

    def test_post_vastaa_mandatory_answer_missing(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN004" in str(resp.json()))

    def test_post_vastaa_string_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys5_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus5_3",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "string": "asd"}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus5_3").latest("luotuaika")
        vastaus = Vastaus.objects.get(vastaajaid=vastaaja.vastaajaid, kysymysid=kysymysid)
        self.assertEqual(vastaus.string, "asd")

    def test_post_vastaa_string_too_long(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys5_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus5_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "string": "toolong"}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN007" in str(resp.json()))

    def test_post_vastaa_string_mandatory_and_empty(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys5_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus5_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "string": ""}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN004" in str(resp.json()))

    def test_post_vastaa_string_not_mandatory_and_empty_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys5_1").kysymysid
        kysymysid2 = Kysymys.objects.get(kysymys_fi="testikysymys5_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus5_2",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "string": ""},
                               {"kysymysid": kysymysid2, "string": "asd"}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus5_2").latest("luotuaika")
        vastaus = Vastaus.objects.filter(vastaajaid=vastaaja.vastaajaid, kysymysid=kysymysid)[0]
        self.assertEqual(vastaus.string, "")

    def test_post_vastaa_monivalinta_checkbox_single_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus4_1").latest("luotuaika")
        vastaukset = Vastaus.objects.filter(vastaajaid=vastaaja.vastaajaid)
        self.assertEqual(len(vastaukset), 1)

    def test_post_vastaa_monivalinta_checkbox_multi_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1},
                               {"kysymysid": kysymysid, "numerovalinta": 2}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus4_1").latest("luotuaika")
        vastaukset = Vastaus.objects.filter(vastaajaid=vastaaja.vastaajaid)
        self.assertEqual(len(vastaukset), 2)

    def test_post_vastaa_monivalinta_checkbox_duplicate_fail(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1},
                               {"kysymysid": kysymysid, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN008" in str(resp.json()))

    def test_post_vastaa_monivalinta_checkbox_multi_too_many_fail(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1},
                               {"kysymysid": kysymysid, "numerovalinta": 2},
                               {"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN005" in str(resp.json()))

    def test_post_vastaa_monivalinta_checkbox_out_of_limits_fail(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 0}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("DY001" in str(resp.json()))

    def test_post_vastaa_monivalinta_radiobutton_single_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_2_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus4_2_1").latest("luotuaika")
        vastaukset = Vastaus.objects.filter(vastaajaid=vastaaja.vastaajaid)
        self.assertEqual(len(vastaukset), 1)

    def test_post_vastaa_monivalinta_radiobutton_duplicate_fail(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_2_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1},
                               {"kysymysid": kysymysid, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN005" in str(resp.json()))

    def test_post_vastaa_monivalinta_radiobutton_multi_too_many_fail(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_2_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1},
                               {"kysymysid": kysymysid, "numerovalinta": 2}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN005" in str(resp.json()))

    def test_post_vastaa_monivalinta_radiobutton_out_of_limits_fail(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys4_2_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus4_2_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 0}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("DY001" in str(resp.json()))

    def test_post_vastaa_kyllaei_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys6_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus6_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus6_1").latest("luotuaika")
        vastaukset = Vastaus.objects.filter(vastaajaid=vastaaja.vastaajaid)
        self.assertEqual(len(vastaukset), 1)

    def test_post_vastaa_kyllaei_value_out_of_limits(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys6_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus6_1",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 3}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("DY001" in str(resp.json()))

    def test_post_vastaa_string_numerokentta_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys10_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus10",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "string": "3"}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_post_vastaa_string_numerokentta_negative_double_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys10_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus10",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "string": "-3.123"}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_post_vastaa_string_numerokentta_empty_ok(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys10_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus10",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "string": ""}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_post_vastaa_string_numerokentta_not_numeric_fail(self):
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys10_1").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus10",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "string": "a"}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN010" in str(resp.json()))

    def test_post_vastaa_mandatory_matrix_ok(self):
        # also matrix-root is marked as mandatory, but answering not allowed
        kysymysid1 = Kysymys.objects.get(kysymys_fi="testikysymys11_1").kysymysid
        kysymysid2 = Kysymys.objects.get(kysymys_fi="testikysymys11_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus11",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid1, "numerovalinta": 1},
                               {"kysymysid": kysymysid2, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_post_vastaa_answer_mandatory_matrix_root_fail(self):
        kysymysid0 = Kysymys.objects.get(kysymys_fi="testikysymys11_0").kysymysid
        kysymysid1 = Kysymys.objects.get(kysymys_fi="testikysymys11_1").kysymysid
        kysymysid2 = Kysymys.objects.get(kysymys_fi="testikysymys11_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus11",
                "email": "",
                "vastaukset": [{"kysymysid": kysymysid0},
                               {"kysymysid": kysymysid1, "numerovalinta": 1},
                               {"kysymysid": kysymysid2, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("AN009" in str(resp.json()))

    @responses.activate
    def test_post_vastaa_tyontekija_info_found_in_db(self):
        add_testing_responses_virkailijapalvelu_token(responses)
        add_testing_responses_virkailijapalvelu_tyontekija_info(responses)
        kysymysid = Kysymys.objects.get(kysymys_fi="testikysymys1_2").kysymysid
        data = {"vastaajatunnus": "testivastaajatunnus1_7", "email": "",
                "vastaukset": [{"kysymysid": kysymysid, "numerovalinta": 1}]}
        resp = self.client.post(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        vastaaja = Vastaaja.objects.filter(vastaajatunnus="testivastaajatunnus1_7").latest("luotuaika")
        self.assertEqual(len(vastaaja.tehtavanimikkeet), 1)
        self.assertEqual(vastaaja.tehtavanimikkeet[0]["tehtavanimike_koodi"], "0001")
        self.assertEqual(len(vastaaja.tutkinnot), 1)
        self.assertEqual(vastaaja.tutkinnot[0], "0002")


@override_settings(RATELIMIT_ENABLE=False)
class WrongMethodTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_get_vastaa_fail(self):
        data = {"vastaajatunnus": "", "vastaukset": []}
        resp = self.client.get(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_put_vastaa_fail(self):
        data = {"vastaajatunnus": "", "vastaukset": []}
        resp = self.client.put(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_vastaa_fail(self):
        data = {"vastaajatunnus": "", "vastaukset": []}
        resp = self.client.delete(VASTAUSPALVELU_API_URL + "/vastaa/", data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
