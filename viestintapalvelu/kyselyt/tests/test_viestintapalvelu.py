from datetime import timedelta

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from kyselyt.migrations.testing.setup import load_testing_data
from kyselyt.models import Message
from kyselyt.opintopolku_auth import get_or_create_oph_auth, clear_oph_auth_tgt
from kyselyt.tests.constants import get_test_access_token, VIESTINTAPALVELU_API_URL, TEST_USER
from kyselyt.utils import empty_email_fields_from_old_messages


@override_settings(RATELIMIT_ENABLE=False)
class AccessTokenTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_post_token_faulty_credentials(self):
        faulty_cred = {"username": "test-user", "password": "faulty-pw"}
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/token/", data=faulty_cred, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class AccessTokenBruteforceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        load_testing_data()

    def test_access_token_bruteforce_exceed_ratelimit(self):
        # +10 is for ensuring test wont fail because internal rate calculation system which sometimes occur
        for i in range(settings.RATELIMIT_PER_MINUTE + 10):
            get_test_access_token(self.client)
        resp = self.client.post(f"{VIESTINTAPALVELU_API_URL}/token/", data=TEST_USER, format='json')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


class EmptyEmailFieldInMessageTests(TestCase):
    def test_empty_email_fields_from_old_messages_emptyed(self):
        now_minus_1d = timezone.now().date() - timedelta(days=1)
        msg1 = Message.objects.create(
            email="a1@a.aa", template=1, end_date=now_minus_1d)
        msg2 = Message.objects.create(
            email="a2@a.aa", template=1, end_date=None)
        msg2.created = timezone.now() - timedelta(days=181)
        msg2.save()
        update_count = empty_email_fields_from_old_messages()
        self.assertEqual(update_count, 2)

        # check emails emptyed in db
        msg = Message.objects.filter(pk=msg1.pk).first()
        self.assertEqual(msg.email, "")
        msg = Message.objects.filter(pk=msg2.pk).first()
        self.assertEqual(msg.email, "")

    def test_empty_email_fields_from_old_messages_not_emptyed(self):
        msg1 = Message.objects.create(
            email="a1@a.aa", template=1, end_date=timezone.now().date())
        msg2 = Message.objects.create(
            email="a2@a.aa", template=1, end_date=None)
        msg2.created = timezone.now() - timedelta(days=179)
        msg2.save()
        update_count = empty_email_fields_from_old_messages()
        self.assertEqual(update_count, 0)

        # check emails emptyed in db
        msg = Message.objects.filter(pk=msg1.pk).first()
        self.assertEqual(msg.email, "a1@a.aa")
        msg = Message.objects.filter(pk=msg2.pk).first()
        self.assertEqual(msg.email, "a2@a.aa")


class FunctionTests(TestCase):
    def test_oph_auth_tgt_and_clearance(self):
        # set tgt
        oph_auth = get_or_create_oph_auth()
        oph_auth.tgt = "test_tgt"
        oph_auth.save()

        # check tgt is changed
        oph_auth = get_or_create_oph_auth()
        self.assertEqual(oph_auth.tgt, "test_tgt")

        # test tgt clearance: with OphAuthentication object
        clear_oph_auth_tgt(oph_auth, sleep_seconds=0)
        oph_auth = get_or_create_oph_auth()
        self.assertEqual(oph_auth.tgt, "")

        # set tgt
        oph_auth.tgt = "test_tgt"
        oph_auth.save()

        # test tgt clearance: tgt not cleared within 1 minute interval
        clear_oph_auth_tgt(oph_auth, sleep_seconds=0)
        oph_auth = get_or_create_oph_auth()
        self.assertEqual(oph_auth.tgt, "test_tgt")

        # set tgt_last_cleared_time 2 minutes ago
        oph_auth.tgt_last_cleared_time = timezone.now() - timedelta(minutes=2)
        oph_auth.save()

        # test tgt clearance: without OphAuthentication object
        clear_oph_auth_tgt(sleep_seconds=0)
        oph_auth = get_or_create_oph_auth()
        self.assertEqual(oph_auth.tgt, "")
