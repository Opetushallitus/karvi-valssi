import responses

from django.test import TestCase

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_viestintapalvelu, add_testing_responses_virkailijapalvelu_scales)
from kyselyt.models import Vastaajatunnus, Vastaaja, VastausSend
from kyselyt.tasks import send_answer_pdf_task


class VastausSendTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        load_testing_data()

    @responses.activate
    def test_vastaussend_removed_after_send(self):
        add_testing_responses_viestintapalvelu(responses)
        add_testing_responses_virkailijapalvelu_scales(responses)
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus8_2")
        vastaaja = Vastaaja.objects.create(
            kyselykertaid=vastaajatunnus.kyselykertaid.kyselykertaid,
            kyselyid=vastaajatunnus.kyselykertaid.kyselyid.kyselyid,
            vastaajatunnus=vastaajatunnus.tunnus)
        vastaussend = VastausSend.objects.create(
            email="a2@a.aa", vastaajaid=vastaaja, language="fi")
        self.assertEqual(VastausSend.objects.count(), 1)
        send_answer_pdf_task(vastaussend.id)
        self.assertEqual(VastausSend.objects.count(), 0)
