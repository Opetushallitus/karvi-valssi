import html5validate
import responses
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from kyselyt.constants import VALSSI_PERMISSION_LEVELS, VALSSI_PAAKAYTTAJA_LEVEL, USER_PERMISSIONS_RECHECK_TIME
from kyselyt.migrations.testing.setup import (
    add_testing_responses_varda_apikey, add_testing_varda_apikey_to_db, add_testing_responses_organisaatiot_update,
    add_testing_responses_toimipaikat_update, add_outdated_kyselysend, add_testing_responses_localisation_ok,
    add_testing_responses_localisation_sv_missing_ok, add_testing_responses_localisation_key_missing_ok,
    add_test_kyselykerta_for_html_test, add_testing_responses_kayttooikeus_userauthorization)
from kyselyt.models import ExternalServices, Kyselykerta, KyselySend, Scale, Kysymysryhma, UserAuthorization
from kyselyt.utils import (
    get_valssi_permission_levels, get_valssi_organisaatiot_permissions, get_varda_apikey, update_organizations,
    delete_outdated_kyselysends, get_localisation_values_by_key, get_henkilo_oid_and_permissions)
from kyselyt.utils_pdf import create_content_html


class PermissionFunctionsTests(TestCase):
    def test_get_valssi_permission_levels_higher_before(self):
        perms = [{"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[0]},
                 {"palvelu": "some", "oikeus": "some"},
                 {"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[1]}]
        self.assertEqual(get_valssi_permission_levels(perms), list(VALSSI_PERMISSION_LEVELS[0:2]))

    def test_get_valssi_permission_levels_higher_later(self):
        perms = [{"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[1]},
                 {"palvelu": "some", "oikeus": "some"},
                 {"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[0]}]
        self.assertEqual(get_valssi_permission_levels(perms), list(VALSSI_PERMISSION_LEVELS[0:2]))

    def test_get_valssi_permission_levels_none_perms(self):
        perms = [{"palvelu": "some", "oikeus": "some"}, {"palvelu": "some2", "oikeus": "some2"}]
        self.assertEqual(get_valssi_permission_levels(perms), [])

    def test_get_valssi_permission_levels_empty_list(self):
        self.assertEqual(get_valssi_permission_levels([]), [])

    def test_get_valssi_organisaatiot_permissions(self):
        orgs = [{"organisaatioOid": "test",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PERMISSION_LEVELS[0]}]}]
        org_perms = get_valssi_organisaatiot_permissions(orgs)
        self.assertEqual(org_perms, [{"organisaatioOid": "test", "valssiPermissions": [VALSSI_PERMISSION_LEVELS[0]]}])


class VardaApikeyTests(TestCase):
    @responses.activate
    def test_getting_varda_apikey(self):
        add_testing_responses_varda_apikey(responses)
        self.assertEqual(ExternalServices.objects.order_by("id").first(), None)
        apikey = get_varda_apikey()
        self.assertEqual(apikey, "test-apikey")
        apikey_db = ExternalServices.objects.order_by("id").first().varda_apikey
        self.assertEqual(apikey_db, "test-apikey")

    @responses.activate
    def test_getting_varda_apikey_refresh(self):
        add_testing_responses_varda_apikey(responses)
        add_testing_varda_apikey_to_db()
        apikey_db = ExternalServices.objects.order_by("id").first().varda_apikey
        self.assertEqual(apikey_db, "old-apikey")
        apikey = get_varda_apikey(refresh=True)  # refresh apikey
        self.assertEqual(apikey, "test-apikey")
        apikey_db = ExternalServices.objects.order_by("id").first().varda_apikey
        self.assertEqual(apikey_db, "test-apikey")


class VardaUpdateTests(TestCase):
    @responses.activate
    def test_update_organizations(self):
        add_testing_responses_varda_apikey(responses)
        add_testing_responses_organisaatiot_update(responses)
        add_testing_responses_toimipaikat_update(responses)

        # no update-time at first
        varda_org_update = ExternalServices.objects.count()
        self.assertEqual(varda_org_update, 0)

        # update-time after init
        timenow = "2022-01-01T00:00:00.000000%2B0300"
        update_organizations(timenow=timenow)  # organisaatiot
        update_organizations(timenow=timenow, is_toimipaikat=True)  # toimipaikat
        varda_org_update = ExternalServices.objects.order_by("id").first()
        self.assertEqual(varda_org_update.varda_organisaatiot_last_update_time, timenow)
        self.assertEqual(varda_org_update.varda_toimipaikat_last_update_time, timenow)

        # update-time after update
        timenow = "2022-01-02T00:00:00.000000%2B0300"
        update_organizations(timenow=timenow)  # organisaatiot
        update_organizations(timenow=timenow, is_toimipaikat=True)  # toimipaikat
        varda_org_update = ExternalServices.objects.order_by("id").first()
        self.assertEqual(varda_org_update.varda_organisaatiot_last_update_time, timenow)
        self.assertEqual(varda_org_update.varda_toimipaikat_last_update_time, timenow)


class PdfFunctionsTests(TestCase):
    databases = ["default", "valssi"]

    def setUp(self):
        add_test_kyselykerta_for_html_test()

    def test_get_pdf_html_creation_by_kyselykertaid_validity(self):
        scale_count = Scale.objects.count()
        self.assertTrue(scale_count > 0)

        kyselykerta = Kyselykerta.objects.get(nimi="html_test_kyselykerta")
        html_str = create_content_html(kyselykertaid=kyselykerta.kyselykertaid, language="fi")
        html5validate.validate(html_str)

        # test questions found in html
        for i in range(6):
            self.assertTrue(f"html_test_kysymys_{i}" in html_str)

        # test hidden questions not found in html
        self.assertFalse("html_test_kysymys_hidden" in html_str)
        self.assertFalse("html_test_kysymys_hidden_m" in html_str)
        self.assertFalse("html_test_kysymys_hidden_m_1" in html_str)

        # test descriptions found in html
        for i in range(7):
            self.assertTrue(f"html_test_description_{i}" in html_str)

        # test multi-options found in html
        for i in range(6):
            self.assertTrue(f"html_test_multioption_{i}" in html_str)

        # test eos matrises
        self.assertTrue("html_test_kysymys_eos_s0" in html_str)
        self.assertTrue("html_test_kysymys_eos_s1" in html_str)
        self.assertTrue("html_test_kysymys_eos_s2" in html_str)
        self.assertTrue("html_test_kysymys_eos_r0" in html_str)
        self.assertTrue("html_test_kysymys_eos_r1" in html_str)
        self.assertTrue("html_test_kysymys_eos_r2" in html_str)

        # test matrix sliderscale (s) and matrix radiobutton (r) (all scales)
        for mtype in ("s", "r"):
            for i in range(scale_count):
                self.assertTrue(f"html_test_kysymys_{mtype}{i}0" in html_str)
                self.assertTrue(f"html_test_kysymys_{mtype}{i}1" in html_str)
                self.assertTrue(f"html_test_kysymys_{mtype}{i}2" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}0" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}1" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}2" in html_str)

    def test_get_pdf_html_creation_by_kyselykertaid_validity_sv(self):
        scale_count = Scale.objects.count()
        self.assertTrue(scale_count > 0)

        kyselykerta = Kyselykerta.objects.get(nimi="html_test_kyselykerta")
        html_str = create_content_html(kyselykertaid=kyselykerta.kyselykertaid, language="sv")
        html5validate.validate(html_str)

        # test questions found in html
        for i in range(6):
            self.assertTrue(f"html_test_kysymys_{i}_sv" in html_str)

        # test descriptions found in html
        for i in range(7):
            self.assertTrue(f"html_test_description_{i}_sv" in html_str)

        # test multi-options found in html
        for i in range(6):
            self.assertTrue(f"html_test_multioption_{i}_sv" in html_str)

        # test eos matrises
        self.assertTrue("html_test_kysymys_eos_s0_sv" in html_str)
        self.assertTrue("html_test_kysymys_eos_s1_sv" in html_str)
        self.assertTrue("html_test_kysymys_eos_s2_sv" in html_str)
        self.assertTrue("html_test_kysymys_eos_r0_sv" in html_str)
        self.assertTrue("html_test_kysymys_eos_r1_sv" in html_str)
        self.assertTrue("html_test_kysymys_eos_r2_sv" in html_str)

        # test matrix sliderscale (s) and matrix radiobutton (r) (all scales)
        for mtype in ("s", "r"):
            for i in range(scale_count):
                self.assertTrue(f"html_test_kysymys_{mtype}{i}0_sv" in html_str)
                self.assertTrue(f"html_test_kysymys_{mtype}{i}1_sv" in html_str)
                self.assertTrue(f"html_test_kysymys_{mtype}{i}2_sv" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}0_sv" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}1_sv" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}2_sv" in html_str)

    def test_get_pdf_html_creation_validity_by_kysymysryhmaid(self):
        scale_count = Scale.objects.count()
        self.assertTrue(scale_count > 0)

        kysymysryhma = Kysymysryhma.objects.get(nimi_fi="html_test_kysymysryhma")
        html_str = create_content_html(kysymysryhmaid=kysymysryhma.kysymysryhmaid, language="fi")
        html5validate.validate(html_str)

        # test questions found in html
        for i in range(6):
            self.assertTrue(f"html_test_kysymys_{i}" in html_str)

        # test descriptions found in html
        for i in range(7):
            self.assertTrue(f"html_test_description_{i}" in html_str)

        # test multi-options found in html
        for i in range(6):
            self.assertTrue(f"html_test_multioption_{i}" in html_str)

        # test matrix sliderscale (s) and matrix radiobutton (r) (all scales)
        for mtype in ("s", "r"):
            for i in range(scale_count):
                self.assertTrue(f"html_test_kysymys_{mtype}{i}0" in html_str)
                self.assertTrue(f"html_test_kysymys_{mtype}{i}1" in html_str)
                self.assertTrue(f"html_test_kysymys_{mtype}{i}2" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}0" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}1" in html_str)
                self.assertTrue(f"html_test_description_{mtype}{i}2" in html_str)


class OutdatedKyselySendDeleteTests(TestCase):
    databases = ["default", "valssi"]

    def test_delete_outdated_kyselysends(self):
        add_outdated_kyselysend()
        self.assertEqual(KyselySend.objects.count(), 2)
        delete_count = delete_outdated_kyselysends()
        self.assertEqual(delete_count, 1)
        kyselysends = KyselySend.objects.all()
        self.assertEqual(kyselysends.count(), 1)
        self.assertEqual(kyselysends[0].email, "valid@a.aa")


class LocalisationValuesTests(TestCase):
    @responses.activate
    def test_get_localisation_values_by_key_ok(self):
        add_testing_responses_localisation_ok(responses)
        values = get_localisation_values_by_key("testkey")
        self.assertEqual(values["fi"], "fi_value")
        self.assertEqual(values["sv"], "sv_value")

    @responses.activate
    def test_get_localisation_values_by_key_sv_missing_ok(self):
        add_testing_responses_localisation_sv_missing_ok(responses)
        values = get_localisation_values_by_key("testkey")
        self.assertEqual(values["fi"], "fi_value")
        self.assertEqual(values["sv"], "SV testkey")

    @responses.activate
    def test_get_localisation_values_by_key_key_missing_ok(self):
        add_testing_responses_localisation_key_missing_ok(responses)
        values = get_localisation_values_by_key("testkey")
        self.assertEqual(values["fi"], "FI testkey")
        self.assertEqual(values["sv"], "SV testkey")


class UserAuthorizationDbTests(TestCase):
    @responses.activate
    def test_user_authorization_db(self):
        add_testing_responses_kayttooikeus_userauthorization(responses)

        # check UserAuthorization not found in db
        self.assertFalse(UserAuthorization.objects.filter(username="test-userauth").exists())

        oid_henkilo, org_perms = get_henkilo_oid_and_permissions("test-userauth")

        self.assertEqual(oid_henkilo, "test-oidUA")
        self.assertEqual(len(org_perms), 1)
        self.assertEqual(org_perms[0]["organisaatioOid"], "test-oidUAorg")
        self.assertEqual(org_perms[0]["valssiPermissions"], [VALSSI_PAAKAYTTAJA_LEVEL])

        # check UserAuthorization found in db after request
        user_auth = UserAuthorization.objects.filter(username="test-userauth").first()
        updated_time_orig = user_auth.updated_time
        self.assertEqual(user_auth.oid, "test-oidUA")
        self.assertEqual(user_auth.permissions[0]["organisaatioOid"], "test-oidUAorg")
        self.assertEqual(user_auth.permissions[0]["valssiPermissions"], [VALSSI_PAAKAYTTAJA_LEVEL])

        # check data is same as first time
        oid_henkilo, org_perms = get_henkilo_oid_and_permissions("test-userauth")
        self.assertEqual(oid_henkilo, "test-oidUA")
        self.assertEqual(len(org_perms), 1)
        self.assertEqual(org_perms[0]["organisaatioOid"], "test-oidUAorg")
        self.assertEqual(org_perms[0]["valssiPermissions"], [VALSSI_PAAKAYTTAJA_LEVEL])

        # check UserAuthorization not updated after (instant) new request
        user_auths = UserAuthorization.objects.filter(username="test-userauth")
        self.assertEqual(user_auths.count(), 1)
        user_auth = user_auths.first()
        self.assertEqual(user_auth.updated_time, updated_time_orig)

        # check UserAuthorization is updated after recheck-time (outdate time manually)
        outdated_time = timezone.now() - timedelta(minutes=USER_PERMISSIONS_RECHECK_TIME, seconds=1)
        UserAuthorization.objects.filter(id=user_auth.id).update(updated_time=outdated_time)
        get_henkilo_oid_and_permissions("test-userauth")
        user_auth = UserAuthorization.objects.filter(username="test-userauth").first()
        self.assertTrue(user_auth.updated_time > updated_time_orig)
