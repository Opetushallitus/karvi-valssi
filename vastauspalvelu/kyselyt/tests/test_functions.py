import responses

from django.test import TestCase

from kyselyt.migrations.testing.setup import (
    load_testing_data, add_testing_responses_viestintapalvelu, add_testing_responses_virkailijapalvelu_scales,
    add_test_duplicate_vastaajas,
)
from kyselyt.models import Vastaajatunnus, Vastaaja, VastausSend, Vastaus
from kyselyt.tasks import send_answer_pdf_task
from vastauspalvelu.celery import check_and_remove_duplicate_vastaajas


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


class CeleryTaskTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        add_test_duplicate_vastaajas()

    def test_check_and_remove_duplicate_vastaajas(self):
        # Check there are duplicates (single use vastaajatunnus)
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus2_1")
        vastaajas = Vastaaja.objects.filter(vastaajatunnus=vastaajatunnus.tunnus)
        self.assertEqual(vastaajas.count(), 3)
        vastauses = Vastaus.objects.filter(vastaajaid__in=vastaajas)
        self.assertEqual(vastauses.count(), 12)

        check_and_remove_duplicate_vastaajas()

        # Check duplicates are removed (single use vastaajatunnus)
        vastaajas = Vastaaja.objects.filter(vastaajatunnus=vastaajatunnus.tunnus)
        self.assertEqual(vastaajas.count(), 1)
        vastauses = Vastaus.objects.filter(vastaajaid__in=vastaajas)
        self.assertEqual(vastauses.count(), 4)

        # Check duplicates aren't removed (multi use vastaajatunnus)
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus1_1")
        vastaajas = Vastaaja.objects.filter(vastaajatunnus=vastaajatunnus.tunnus)
        self.assertEqual(vastaajas.count(), 3)
        vastauses = Vastaus.objects.filter(vastaajaid__in=vastaajas)
        self.assertEqual(vastauses.count(), 12)

        # Check single answer isn't removed (single use vastaajatunnus)
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus3_1")
        vastaajas = Vastaaja.objects.filter(vastaajatunnus=vastaajatunnus.tunnus)
        self.assertEqual(vastaajas.count(), 1)
        vastauses = Vastaus.objects.filter(vastaajaid__in=vastaajas)
        self.assertEqual(vastauses.count(), 4)
