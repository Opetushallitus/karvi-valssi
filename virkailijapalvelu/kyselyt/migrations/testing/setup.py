from copy import deepcopy
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.utils import timezone
from rest_framework import status

from kyselyt.constants import (
    EMAIL_STATUS_SENT, SERVICE_USER_GROUP, VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL, VALSSI_YLLAPITAJA_LEVEL,
    VALSSI_YLLAPITAJA_ORGANIZATION_OIDS, EMAIL_STATUS_FAILED, EMAIL_STATUS_DELIVERED)
from kyselyt.migrations.production.setup import create_scales
from kyselyt.models import (
    Kayttaja, Kysely, Kyselykerta, KyselySend, Indikaattori, Kysymysryhma, Kysymys, KyselyKysymysryhma, TilaEnum,
    Organisaatio, Vastaajatunnus, Scale, Koodi, ExternalServices, MalfunctionMessage)


def add_test_users():
    User.objects.create_user("test-user", "", "supersecret")
    service_user = User.objects.create_user("test-service-user", "", "supersecret")

    # create service-user group, add service-user to it
    service_user_group = Group.objects.create(name=SERVICE_USER_GROUP)
    service_user_group.user_set.add(service_user)


def add_test_kyselyt_kyselykerrat():
    kayttaja = Kayttaja.objects.create(oid="testikayttaja1_oid", uid="testikayttaja1", voimassa=True)
    vakajarjestaja = Organisaatio.objects.create(
        nimi_fi="testivakajarjestaja1", oid="0.1.2", kunta="001", voimassa=True,
        metatiedot=dict())
    toimipaikka = Organisaatio.objects.create(
        nimi_fi="testitoimipaikka1", oid="0.1.3", postinumero="12345", voimassa=True,
        metatiedot=dict(jarjestamismuoto_koodit=["jm-testi"], toimintamuoto_koodi="tm-testi"))
    time_now = timezone.now()
    kayttajat_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)
    kysely_kwargs = dict(
        voimassa_alkupvm=time_now,
        voimassa_loppupvm=time_now + timedelta(days=30),
        koulutustoimija=vakajarjestaja,
        oppilaitos=toimipaikka)
    kysely = Kysely.objects.create(**kysely_kwargs, **kayttajat_kwargs)
    kyselykerta_kwargs = dict(
        voimassa_alkupvm=time_now,
        voimassa_loppupvm=time_now + timedelta(days=30))
    Kyselykerta.objects.create(
        kyselyid=kysely, nimi="testikyselykerta1", lukittu=False, **kyselykerta_kwargs, **kayttajat_kwargs)
    Kyselykerta.objects.create(
        kyselyid=kysely, nimi="testikyselykerta2", lukittu=True, **kyselykerta_kwargs, **kayttajat_kwargs)
    Kyselykerta.objects.create(
        kyselyid=kysely, nimi="testikyselykerta3", lukittu=False, **kyselykerta_kwargs, **kayttajat_kwargs)
    Kyselykerta.objects.create(
        kyselyid=kysely, nimi="testikyselykerta3_2", lukittu=False, **kyselykerta_kwargs, **kayttajat_kwargs)

    # for kyselykerta-endpoint tests (koulutustoimija/vakajarjestaja)
    voimassa_kwargs = dict(
        voimassa_alkupvm=time_now - timedelta(days=30),
        voimassa_loppupvm=time_now + timedelta(days=30))
    kysymysryhma_kwargs = dict(taustakysymykset=False, valtakunnallinen=False)
    kysely2 = Kysely.objects.create(
        koulutustoimija=vakajarjestaja, **kayttajat_kwargs, **voimassa_kwargs)
    kysymysryhma1 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma1", **kayttajat_kwargs, **kysymysryhma_kwargs)
    Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma2", **kayttajat_kwargs, **kysymysryhma_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely2, kysymysryhmaid=kysymysryhma1, **kayttajat_kwargs)
    Kyselykerta.objects.create(  # outdated kyselykerta
        kyselyid=kysely2, nimi="testikyselykerta4", lukittu=True,
        voimassa_alkupvm=time_now - timedelta(days=100),
        voimassa_loppupvm=time_now - timedelta(days=30), **kayttajat_kwargs)
    kyselykerta5 = Kyselykerta.objects.create(
        kyselyid=kysely2, nimi="testikyselykerta5", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    KyselySend.objects.create(
        email="a@kk.aa", kyselykerta=kyselykerta5.kyselykertaid, vastaajatunnus="a1", msg_id=501,
        msg_status="delivered", message="test-msg")
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta5, tunnus="a1", kohteiden_lkm=1, lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)

    # for kyselykerta-endpoint tests (oppilaitos/toimipaikka)
    kysely3 = Kysely.objects.create(
        oppilaitos=toimipaikka, **kayttajat_kwargs, **voimassa_kwargs)
    kysymysryhma3 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma3", **kayttajat_kwargs, **kysymysryhma_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely3, kysymysryhmaid=kysymysryhma3, **kayttajat_kwargs)
    Kyselykerta.objects.create(
        kyselyid=kysely3, nimi="testikyselykerta6", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)

    # for tyontekija-endpoint tests
    kyselykerta7 = Kyselykerta.objects.create(
        kyselyid=kysely3, nimi="testikyselykerta7", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta7, tunnus="aaa001", kohteiden_lkm=1, lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    KyselySend.objects.create(
        tyontekija_id=123, email="a@a.bb", kyselykerta=kyselykerta7.kyselykertaid, vastaajatunnus="aaa001",
        msg_id=999, msg_status="sent")
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta7, tunnus="aaa002", kohteiden_lkm=1, lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    KyselySend.objects.create(
        email="a@a.bb", kyselykerta=kyselykerta7.kyselykertaid, vastaajatunnus="aaa002", msg_id=999, msg_status="sent")
    kysely4 = Kysely.objects.create(**kayttajat_kwargs, **voimassa_kwargs)
    kyselykerta8 = Kyselykerta.objects.create(
        kyselyid=kysely4, nimi="testikyselykerta8", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta8, tunnus="aaa003", kohteiden_lkm=1, lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    KyselySend.objects.create(
        tyontekija_id=123, email="a@a.bb", kyselykerta=kyselykerta8.kyselykertaid, vastaajatunnus="aaa003",
        msg_id=999, msg_status="sent")

    # for testing background info (taustatiedot) saving
    # - henkilostolomake_prosessitekijat (type 3)
    tila_julkaistu, _ = TilaEnum.objects.get_or_create(nimi="julkaistu")
    kysymysryhma9_1 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma9_1",
        metatiedot=dict(lomaketyyppi="henkilostolomake_prosessitekijat"),
        tila=tila_julkaistu, **kayttajat_kwargs, **kysymysryhma_kwargs)
    kysely9_1 = Kysely.objects.create(
        metatiedot=dict(valssi_kysymysryhma=kysymysryhma9_1.kysymysryhmaid),
        **kayttajat_kwargs, **kysely_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely9_1, kysymysryhmaid=kysymysryhma9_1, **kayttajat_kwargs)
    kyselykerta9_1 = Kyselykerta.objects.create(
        kyselyid=kysely9_1, nimi="testikyselykerta9_1", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta9_1, tunnus="AAA091", kohteiden_lkm=1, lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)

    # - taydennyskoulutuslomake_rakennetekijat (type 9)
    kysymysryhma9_2 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma9_2",
        metatiedot=dict(lomaketyyppi="taydennyskoulutuslomake_rakennetekijat"),
        tila=tila_julkaistu, **kayttajat_kwargs, **kysymysryhma_kwargs)
    kysely9_2 = Kysely.objects.create(
        metatiedot=dict(valssi_kysymysryhma=kysymysryhma9_2.kysymysryhmaid),
        **kayttajat_kwargs, **kysely_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely9_2, kysymysryhmaid=kysymysryhma9_2, **kayttajat_kwargs)
    kyselykerta9_2 = Kyselykerta.objects.create(
        kyselyid=kysely9_2, nimi="testikyselykerta9_2", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta9_2, tunnus="AAA092", kohteiden_lkm=1, lukittu=False,
        taustatiedot={}, **kayttajat_kwargs, **voimassa_kwargs)

    # for extend_enddate-endpoint tests
    kysymysryhma10 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma10",
        metatiedot=dict(), tila=tila_julkaistu, **kayttajat_kwargs, **kysymysryhma_kwargs)
    kysely10 = Kysely.objects.create(
        nimi_fi="testikysely10",
        koulutustoimija=vakajarjestaja, oppilaitos=toimipaikka,
        **kayttajat_kwargs, **voimassa_kwargs)
    kyselykerta10 = Kyselykerta.objects.create(
        kyselyid=kysely10, nimi="testikyselykerta10", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely10, kysymysryhmaid=kysymysryhma10, **kayttajat_kwargs)
    vastaajatunnus_voimassa_kwargs = dict(
        voimassa_alkupvm=time_now - timedelta(days=30),
        voimassa_loppupvm=time_now + timedelta(days=10))
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta10, tunnus="AAA101", kohteiden_lkm=1, lukittu=False,
        taustatiedot={}, **kayttajat_kwargs, **vastaajatunnus_voimassa_kwargs)
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta10, tunnus="AAA102", kohteiden_lkm=1, lukittu=False,
        taustatiedot={}, **kayttajat_kwargs, **vastaajatunnus_voimassa_kwargs)
    Kyselykerta.objects.create(
        kyselyid=kysely10, nimi="testikyselykerta10_2", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    # already ended kysely
    kysymysryhma10_3 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma10_3",
        metatiedot=dict(), tila=tila_julkaistu, **kayttajat_kwargs, **kysymysryhma_kwargs)
    kysely10_3 = Kysely.objects.create(
        nimi_fi="testikysely10_3",
        koulutustoimija=vakajarjestaja, oppilaitos=toimipaikka,
        voimassa_alkupvm=time_now - timedelta(days=40),
        voimassa_loppupvm=time_now - timedelta(days=1), **kayttajat_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely10_3, kysymysryhmaid=kysymysryhma10_3, **kayttajat_kwargs)

    # for kysymysryhma-pdf tests
    tila_not_julkaistu, _ = TilaEnum.objects.get_or_create(nimi="not_julkaistu")
    Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma11",
        metatiedot=dict(lomaketyyppi="henkilostolomake_prosessitekijat"),
        tila=tila_not_julkaistu, **kayttajat_kwargs, **kysymysryhma_kwargs)

    # for kyselykerta-active-multi endpoint tests
    vakajarjestaja2 = Organisaatio.objects.create(
        nimi_fi="testivakajarjestaja2", oid="0.1.2.2", kunta="001", voimassa=True,
        metatiedot=dict())
    toimipaikka2 = Organisaatio.objects.create(
        nimi_fi="testitoimipaikka2", oid="0.1.3.2", postinumero="12345", voimassa=True,
        metatiedot=dict(jarjestamismuoto_koodit=["jm-testi"], toimintamuoto_koodi="tm-testi"))
    kysely11_1 = Kysely.objects.create(
        koulutustoimija=vakajarjestaja, **kayttajat_kwargs, **voimassa_kwargs)
    kysely11_2 = Kysely.objects.create(
        koulutustoimija=vakajarjestaja2, oppilaitos=toimipaikka2, **kayttajat_kwargs, **voimassa_kwargs)
    kysymysryhma11_1 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma11_1", **kayttajat_kwargs, **kysymysryhma_kwargs)
    kysymysryhma11_2 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma11_2", **kayttajat_kwargs, **kysymysryhma_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely11_1, kysymysryhmaid=kysymysryhma11_1, **kayttajat_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely11_2, kysymysryhmaid=kysymysryhma11_2, **kayttajat_kwargs)
    kyselykerta11_1 = Kyselykerta.objects.create(
        kyselyid=kysely11_1, nimi="testikyselykerta11_1", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    Kyselykerta.objects.create(
        kyselyid=kysely11_2, nimi="testikyselykerta11_2", lukittu=False,
        **kayttajat_kwargs, **voimassa_kwargs)
    KyselySend.objects.create(
        email="a@kk.aa", kyselykerta=kyselykerta11_1.kyselykertaid, vastaajatunnus="a1", msg_id=1101,
        msg_status="delivered", message="test-msg")


def add_test_kyselysends():
    # for kyselysend list tests
    kyselykerta3_2 = Kyselykerta.objects.get(nimi="testikyselykerta3_2")
    KyselySend.objects.create(
        email="a1@ksl.aa", tyontekija_id=21, kyselykerta=kyselykerta3_2.kyselykertaid,
        vastaajatunnus="a1", msg_id=101, msg_status=EMAIL_STATUS_FAILED)
    KyselySend.objects.create(
        email="a2@ksl.aa", tyontekija_id=22, kyselykerta=kyselykerta3_2.kyselykertaid,
        vastaajatunnus="a2", msg_id=102, msg_status=EMAIL_STATUS_SENT)
    KyselySend.objects.create(
        email="a3@ksl.aa", kyselykerta=kyselykerta3_2.kyselykertaid,
        vastaajatunnus="a3", msg_id=103, msg_status=EMAIL_STATUS_SENT)
    KyselySend.objects.create(
        email="a4@ksl.aa", tyontekija_id=24, kyselykerta=kyselykerta3_2.kyselykertaid,
        vastaajatunnus="a4", msg_id=104, msg_status=EMAIL_STATUS_FAILED)

    # for kyselysend update tests
    kyselykerta3 = Kyselykerta.objects.get(nimi="testikyselykerta3")
    KyselySend.objects.create(
        email="a1@ksu.aa", kyselykerta=kyselykerta3.kyselykertaid, vastaajatunnus="a1", msg_id=111,
        msg_status=EMAIL_STATUS_FAILED)
    KyselySend.objects.create(
        email="a2@ksu.aa", kyselykerta=kyselykerta3.kyselykertaid, vastaajatunnus="a2", msg_id=112,
        msg_status=EMAIL_STATUS_DELIVERED)
    KyselySend.objects.create(
        email="a3@ksu.aa", kyselykerta=999, vastaajatunnus="a3", msg_id=113, msg_status=EMAIL_STATUS_FAILED)


def add_test_indikaattorit():
    Indikaattori.objects.create(group_id=11, key="a1", laatutekija="a", is_visible=True)
    Indikaattori.objects.create(group_id=11, key="a2", laatutekija="a", is_visible=True)
    Indikaattori.objects.create(group_id=12, key="a3", laatutekija="a", is_visible=True)
    Indikaattori.objects.create(group_id=21, key="b1", laatutekija="b", is_visible=True)
    Indikaattori.objects.create(group_id=21, key="b2", laatutekija="b", is_visible=True)
    Indikaattori.objects.create(group_id=21, key="b3", laatutekija="b", is_visible=False)


def add_test_scales():
    Scale.objects.create(
        name="scale1", min_value=1, max_value=3, default_value=1, step_count=3,
        scale=[{"value": 1, "fi": "fi11", "sv": "sv11"},
               {"value": 2, "fi": "fi12", "sv": "sv12"},
               {"value": 3, "fi": "fi13", "sv": "sv13"}])
    Scale.objects.create(
        name="scale2", min_value=1, max_value=2, default_value=1, step_count=2,
        scale=[{"value": 1, "fi": "fi21", "sv": "sv21"},
               {"value": 2, "fi": "fi22", "sv": "sv22"}])


def add_test_koodis():
    Koodi.objects.create(koodisto_uri="vardatehtavanimike", nimi_fi="a", nimi_sv="b", koodi_arvo="201")


def add_outdated_kyselysend():
    kayttaja = Kayttaja.objects.create(oid="testikayttaja_oid", uid="testikayttaja", voimassa=True)
    vakajarjestaja = Organisaatio.objects.create(nimi_fi="testivakajarjestaja", oid="0.1", voimassa=True)
    toimipaikka = Organisaatio.objects.create(nimi_fi="testitoimipaikka", oid="0.2", voimassa=True)

    time_now = timezone.now()

    kayttajat_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)
    organisaatio_kwargs = dict(
        koulutustoimija=vakajarjestaja,
        oppilaitos=toimipaikka)
    voimassa_valid_kwargs = dict(
        voimassa_alkupvm=time_now - timedelta(days=30),
        voimassa_loppupvm=time_now + timedelta(days=30))
    voimassa_od_kwargs = dict(
        voimassa_alkupvm=time_now - timedelta(days=30),
        voimassa_loppupvm=time_now - timedelta(days=1))
    kysely = Kysely.objects.create(**organisaatio_kwargs, **voimassa_valid_kwargs, **kayttajat_kwargs)
    kyselykerta_valid = Kyselykerta.objects.create(
        kyselyid=kysely, nimi="testikyselykerta_od", lukittu=False, **voimassa_valid_kwargs, **kayttajat_kwargs)
    KyselySend.objects.create(
        email="valid@a.aa", kyselykerta=kyselykerta_valid.kyselykertaid, vastaajatunnus="a1",
        msg_id=1, msg_status="delivered")
    kyselykerta_od = Kyselykerta.objects.create(
        kyselyid=kysely, nimi="testikyselykerta_od", lukittu=True, **voimassa_od_kwargs, **kayttajat_kwargs)
    KyselySend.objects.create(
        email="od@a.aa", kyselykerta=kyselykerta_od.kyselykertaid, vastaajatunnus="a2",
        msg_id=2, msg_status="delivered")


def load_testing_data():
    add_test_users()
    add_test_kyselyt_kyselykerrat()
    add_test_koodis()


def add_testing_responses_kayttooikeus_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo",
            "organisaatiot": [
                {"organisaatioOid": "0.1.2",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PAAKAYTTAJA_LEVEL}]},
                {"organisaatioOid": "0.1.3",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_TOTEUTTAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_paakayttaja_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo",
            "organisaatiot": [
                {"organisaatioOid": "0.1.2",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PAAKAYTTAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_toteuttaja_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo",
            "organisaatiot": [
                {"organisaatioOid": "0.1.3",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_TOTEUTTAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_yllapitaja_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo",
            "organisaatiot": [
                {"organisaatioOid": VALSSI_YLLAPITAJA_ORGANIZATION_OIDS[0],
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_YLLAPITAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_multi_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo",
            "organisaatiot": [
                {"organisaatioOid": "0.1.2",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PAAKAYTTAJA_LEVEL}]},
                {"organisaatioOid": "0.1.3.2",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_TOTEUTTAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_impersonate_toteuttaja_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-impersonate-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo2",
            "organisaatiot": [
                {"organisaatioOid": "0.1.3",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_TOTEUTTAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_impersonate_paakayttaja_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-impersonate-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo2",
            "organisaatiot": [
                {"organisaatioOid": "0.1.2",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PAAKAYTTAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_organisaatiot_empty(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo",
            "organisaatiot": []}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_userauthorization(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-userauth",
        json=[{
            "oidHenkilo": "test-oidUA",
            "organisaatiot": [
                {"organisaatioOid": "test-oidUAorg",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PAAKAYTTAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_service_ticket(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.OPINTOPOLKU_URL}/cas/v1/tickets",
        headers={"Location": "http://a"}, status=status.HTTP_201_CREATED)

    responses_obj.add(
        responses_obj.POST, "http://a", json={}, status=status.HTTP_200_OK)


def add_testing_responses_viestintapalvelu_token(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.VIESTINTAPALVELU_URL}/api/v1/token/",
        json={"access": "a"}, status=status.HTTP_200_OK)


def add_testing_responses_viestintapalvelu_laheta_single(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.VIESTINTAPALVELU_URL}/api/v1/laheta/",
        json=[{"msg_id": 1, "msg_status": "a"}], status=status.HTTP_201_CREATED)


def add_testing_responses_viestintapalvelu_laheta_update(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.VIESTINTAPALVELU_URL}/api/v1/laheta/",
        json=[{"msg_id": 121, "msg_status": "updateok"},
              {"msg_id": 122, "msg_status": "updateok"}], status=status.HTTP_201_CREATED)


def add_testing_responses_service_ticket_fail_500(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.OPINTOPOLKU_URL}/cas/v1/tickets",
        headers={"Location": "http://a"}, status=status.HTTP_201_CREATED)

    responses_obj.add(
        responses_obj.POST, "http://a", json={}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def add_testing_responses_vastaajatunnus(responses_obj):
    kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta1")
    responses_obj.add(
        responses_obj.POST, f"{settings.ARVO_VASTAAJATUNNUS_ENDPOINT}{kyselykerta.kyselykertaid}",
        json=[{"tunnus": "AAA001"}], status=status.HTTP_200_OK)

    kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_1")
    responses_obj.add(
        responses_obj.POST, f"{settings.ARVO_VASTAAJATUNNUS_ENDPOINT}{kyselykerta.kyselykertaid}",
        json=[{"tunnus": "AAA091"}], status=status.HTTP_200_OK)

    kyselykerta = Kyselykerta.objects.get(nimi="testikyselykerta9_2")
    responses_obj.add(
        responses_obj.POST, f"{settings.ARVO_VASTAAJATUNNUS_ENDPOINT}{kyselykerta.kyselykertaid}",
        json=[{"tunnus": "AAA092"}], status=status.HTTP_200_OK)


def add_testing_responses_viestintapalvelu_viestit(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.VIESTINTAPALVELU_URL}/api/v1/viestit/",
        json=[{"msg_id": 102, "msg_status": "delivered"},
              {"msg_id": 103, "msg_status": "delivered"},
              {"msg_id": 104, "msg_status": "delivered"}],
        status=status.HTTP_200_OK)


def add_testing_responses_varda_apikey(responses_obj):
    responses_obj.add(
        responses_obj.GET, settings.VARDA_APIKEY_ENDPOINT,
        json={"token": "test-apikey"}, status=status.HTTP_200_OK)


def add_testing_varda_apikey_to_db():
    ext_services = ExternalServices.objects.order_by("id").first()
    if not ext_services:
        ext_services = ExternalServices.objects.create(varda_apikey="")
    ext_services.varda_apikey = "old-apikey"
    ext_services.save()


def add_testing_responses_organisaatiot_update(responses_obj):
    orgs_addr = f"{settings.VARDA_ORGANISAATIOT_ENDPOINT}?page_size={settings.VARDA_ORG_COUNT_PER_REQUEST}"

    responses_obj.add(
        responses_obj.GET,
        orgs_addr + "&datetime_lte=2022-01-01T00:00:00.000000%2B0300",
        json={
            "next": None,
            "previous": None,
            "results": [{
                "id": 1,
                "action": "CREATED",
                "nimi": "hki",
                "organisaatio_oid": "1.2.246.562.10.346830761110",
                "parent_oid": "1.2.246.562.10.00000000001",
                "organisaatiotyyppi": [],
                "kunta_koodi": "123",
                "sahkopostiosoite": "a@a.a",
                "postinumero": "12345",
                "paattymis_pvm": None}]},
        status=status.HTTP_200_OK)

    responses_obj.add(
        responses_obj.POST, settings.ARVO_ORGANISAATIOT_UPDATE_ENDPOINT,
        status=status.HTTP_201_CREATED)

    responses_obj.add(
        responses_obj.GET,
        orgs_addr + "&datetime_gt=2022-01-01T00:00:00.000000%2B0300",
        json={
            "next": None,
            "previous": None,
            "results": [{
                "id": 1,
                "action": "MODIFIED",
                "nimi": "hki new",
                "organisaatio_oid": "1.2.246.562.10.346830761110",
                "parent_oid": "1.2.246.562.10.00000000001",
                "organisaatiotyyppi": [],
                "kunta_koodi": "123",
                "sahkopostiosoite": "a@a.a",
                "postinumero": "12345",
                "paattymis_pvm": None}]},
        status=status.HTTP_200_OK)


def add_testing_responses_toimipaikat_update(responses_obj):
    orgs_addr = f"{settings.VARDA_TOIMIPAIKAT_ENDPOINT}?page_size={settings.VARDA_ORG_COUNT_PER_REQUEST}"

    responses_obj.add(
        responses_obj.GET,
        orgs_addr + "&datetime_lte=2022-01-01T00:00:00.000000%2B0300",
        json={
            "next": None,
            "previous": None,
            "results": [{
                "id": 1,
                "action": "CREATED",
                "nimi": "hki",
                "organisaatio_oid": "1.2.246.562.10.346830761110",
                "parent_oid": "1.2.246.562.10.00000000001",
                "organisaatiotyyppi": [],
                "postinumero": "12345",
                "jarjestamismuoto_koodi": [],
                "toimintamuoto_koodi": ""}]},
        status=status.HTTP_200_OK)

    responses_obj.add(
        responses_obj.POST, settings.VARDA_TOIMIPAIKAT_ENDPOINT,
        status=status.HTTP_201_CREATED)

    responses_obj.add(
        responses_obj.GET,
        orgs_addr + "&datetime_gt=2022-01-01T00:00:00.000000%2B0300",
        json={
            "next": None,
            "previous": None,
            "results": [{
                "id": 1,
                "action": "MODIFIED",
                "nimi": "hki new",
                "organisaatio_oid": "1.2.246.562.10.346830761110",
                "parent_oid": "1.2.246.562.10.00000000001",
                "organisaatiotyyppi": [],
                "postinumero": "12345",
                "jarjestamismuoto_koodi": [],
                "toimintamuoto_koodi": ""}]},
        status=status.HTTP_200_OK)


def add_test_kyselykerta_for_html_test():
    time_now = timezone.now()
    timenow_plus_30d = time_now + timedelta(days=30)
    kayttaja = Kayttaja.objects.create(oid="html_test_user_oid", uid="html_test_user", voimassa=True)

    kayttaja_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)
    voimassa_kwargs = dict(voimassa_alkupvm=time_now, voimassa_loppupvm=timenow_plus_30d)

    kysely = Kysely.objects.create(
        nimi_fi="html_test_kysely", **voimassa_kwargs, **kayttaja_kwargs)

    Kyselykerta.objects.create(
        kyselyid=kysely, nimi="html_test_kyselykerta", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    tila_julkaistu, _ = TilaEnum.objects.get_or_create(nimi="julkaistu")
    kysymysryhma = Kysymysryhma.objects.create(
        nimi_fi="html_test_kysymysryhma",
        taustakysymykset=False, valtakunnallinen=False,
        metatiedot={"paaIndikaattori": {"key": "somekey"}},
        tila=tila_julkaistu, **kayttaja_kwargs)

    KyselyKysymysryhma.objects.create(kyselyid=kysely, kysymysryhmaid=kysymysryhma, **kayttaja_kwargs)

    kysymys_kwargs = dict(
        kysymysryhmaid=kysymysryhma, pakollinen=False, eos_vastaus_sallittu=False, poistettava=False,
        jatkokysymys=False, **kayttaja_kwargs)

    # intertitle (väliotsikko)
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_0", kysymys_sv="html_test_kysymys_0_sv", **kysymys_kwargs,
        vastaustyyppi="string",
        jarjestys=0, matriisi_jarjestys=None,
        metatiedot={"type": "statictext"})

    # textfield (tekstikenttä)
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_1", kysymys_sv="html_test_kysymys_1_sv", **kysymys_kwargs,
        vastaustyyppi="string",
        jarjestys=1, matriisi_jarjestys=None,
        metatiedot={
            "type": "string", "numeric": False, "multiline": False,
            "description": {"fi": "html_test_description_0", "sv": "html_test_description_0_sv"}})

    # mandatory (tekstikenttä)
    mandatory_kwargs = deepcopy(kysymys_kwargs)
    mandatory_kwargs["pakollinen"] = True
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_1_2", kysymys_sv="html_test_kysymys_1_2_sv", **mandatory_kwargs,
        vastaustyyppi="string", jarjestys=1, matriisi_jarjestys=None,
        metatiedot={
            "type": "string", "numeric": False, "multiline": False,
            "description": {"fi": "html_test_description_0_2", "sv": "html_test_description_0_2_sv"}})

    # multiline textfield (monirivinen tekstikenttä)
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_2", kysymys_sv="html_test_kysymys_2_sv", **kysymys_kwargs,
        vastaustyyppi="string",
        jarjestys=2, matriisi_jarjestys=None,
        metatiedot={
            "type": "string", "numeric": False, "multiline": True,
            "description": {"fi": "html_test_description_1", "sv": "html_test_description_1_sv"}})

    # numeric textfield (numerokenttä)
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_3", kysymys_sv="html_test_kysymys_3_sv", **kysymys_kwargs,
        vastaustyyppi="string",
        jarjestys=3, matriisi_jarjestys=None,
        metatiedot={
            "type": "string", "numeric": True, "multiline": False,
            "description": {"fi": "html_test_description_2", "sv": "html_test_description_2_sv"}})

    # multi-option field, 1-choose
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_4", kysymys_sv="html_test_kysymys_4_sv", **kysymys_kwargs,
        vastaustyyppi="monivalinta",
        jarjestys=4, matriisi_jarjestys=None,
        metatiedot={
            "type": "radiobutton",
            "vastausvaihtoehdot": [
                {
                    "id": 1, "checked": False,
                    "title": {"fi": "html_test_multioption_0", "sv": "html_test_multioption_0_sv"},
                    "description": {"fi": "html_test_description_3", "sv": "html_test_description_3_sv"}},
                {"id": 2, "title": {
                    "fi": "html_test_multioption_1", "sv": "html_test_multioption_1_sv"}, "checked": False},
                {"id": 3, "title": {
                    "fi": "html_test_multioption_2", "sv": "html_test_multioption_2_sv"}, "checked": False}],
            "description": {"fi": "html_test_description_4", "sv": "html_test_description_4_sv"}})

    # multi-option field, multi-choose
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_5", kysymys_sv="html_test_kysymys_5_sv", **kysymys_kwargs,
        vastaustyyppi="monivalinta",
        jarjestys=5, matriisi_jarjestys=None,
        metatiedot={
            "type": "checkbox",
            "vastausvaihtoehdot": [
                {
                    "id": 1, "checked": False,
                    "title": {"fi": "html_test_multioption_3", "sv": "html_test_multioption_3_sv"},
                    "description": {"fi": "html_test_description_5", "sv": "html_test_description_5_sv"}},
                {"id": 2, "title": {
                    "fi": "html_test_multioption_4", "sv": "html_test_multioption_4_sv"}, "checked": False},
                {"id": 3, "title": {
                    "fi": "html_test_multioption_5", "sv": "html_test_multioption_5_sv"}, "checked": False}],
            "description": {"fi": "html_test_description_6", "sv": "html_test_description_6_sv"}})

    # eos matrises (sliderscale + radiobutton)
    create_scales()
    scales = Scale.objects.all()
    if scales:
        scale_name = scales[0].name
        # sliderscale
        jarjestys = 6
        kysymys_root = Kysymys.objects.create(
            kysymys_fi="html_test_kysymys_eos_s0", kysymys_sv="html_test_kysymys_eos_s0_sv", **kysymys_kwargs,
            vastaustyyppi="matrix_root",
            jarjestys=jarjestys, matriisi_jarjestys=0,
            metatiedot={"type": "matrix_sliderscale", "description": {"fi": "", "sv": ""}})
        matriisi_kysymysid = kysymys_root.kysymysid
        kysymys_root.matriisi_kysymysid = matriisi_kysymysid
        kysymys_root.save()
        Kysymys.objects.create(
            kysymys_fi="html_test_kysymys_eos_s1", kysymys_sv="html_test_kysymys_eos_s1_sv", **kysymys_kwargs,
            vastaustyyppi=scale_name,
            jarjestys=jarjestys, matriisi_jarjestys=1, matriisi_kysymysid=matriisi_kysymysid,
            metatiedot={"type": "matrix_sliderscale", "description": {"fi": "", "sv": ""}})
        Kysymys.objects.create(
            kysymys_fi="html_test_kysymys_eos_s2", kysymys_sv="html_test_kysymys_eos_s2_sv", **kysymys_kwargs,
            vastaustyyppi=scale_name,
            jarjestys=jarjestys, matriisi_jarjestys=2, matriisi_kysymysid=matriisi_kysymysid,
            metatiedot={"type": "matrix_sliderscale", "description": {"fi": "", "sv": ""}})

        # radiobutton
        jarjestys = 7
        kysymys_root = Kysymys.objects.create(
            kysymys_fi="html_test_kysymys_eos_r0", kysymys_sv="html_test_kysymys_eos_r0_sv", **kysymys_kwargs,
            vastaustyyppi="matrix_root",
            jarjestys=jarjestys, matriisi_jarjestys=0,
            metatiedot={"type": "matrix_radiobutton", "description": {"fi": "", "sv": ""}})
        matriisi_kysymysid = kysymys_root.kysymysid
        kysymys_root.matriisi_kysymysid = matriisi_kysymysid
        kysymys_root.save()
        Kysymys.objects.create(
            kysymys_fi="html_test_kysymys_eos_r1", kysymys_sv="html_test_kysymys_eos_r1_sv", **kysymys_kwargs,
            vastaustyyppi=scale_name,
            jarjestys=jarjestys, matriisi_jarjestys=1, matriisi_kysymysid=matriisi_kysymysid,
            metatiedot={"type": "matrix_radiobutton", "description": {"fi": "", "sv": ""}})
        Kysymys.objects.create(
            kysymys_fi="html_test_kysymys_eos_r2", kysymys_sv="html_test_kysymys_eos_r2_sv", **kysymys_kwargs,
            vastaustyyppi=scale_name,
            jarjestys=jarjestys, matriisi_jarjestys=2, matriisi_kysymysid=matriisi_kysymysid,
            metatiedot={"type": "matrix_radiobutton", "description": {"fi": "", "sv": ""}})

    # hidden question
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_hidden", kysymys_sv="html_test_kysymys_hidden_sv", **kysymys_kwargs,
        vastaustyyppi="string",
        jarjestys=8, matriisi_jarjestys=None,
        metatiedot={
            "hidden": True, "type": "string", "numeric": False, "multiline": False,
            "description": {"fi": "", "sv": ""}})

    # hidden matrix
    scale_name = scales[0].name
    jarjestys = 9
    kysymys_root = Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_hidden_m", kysymys_sv="html_test_kysymys_hidden_m_sv", **kysymys_kwargs,
        vastaustyyppi="matrix_root",
        jarjestys=jarjestys, matriisi_jarjestys=0,
        metatiedot={"hidden": True, "type": "matrix_radiobutton", "description": {"fi": "", "sv": ""}})
    matriisi_kysymysid = kysymys_root.kysymysid
    kysymys_root.matriisi_kysymysid = matriisi_kysymysid
    kysymys_root.save()
    Kysymys.objects.create(
        kysymys_fi="html_test_kysymys_hidden_m_1", kysymys_sv="html_test_kysymys_hidden_m_1_sv", **kysymys_kwargs,
        vastaustyyppi=scale_name,
        jarjestys=jarjestys, matriisi_jarjestys=1, matriisi_kysymysid=matriisi_kysymysid,
        metatiedot={"type": "matrix_radiobutton", "description": {"fi": "", "sv": ""}})

    # matrix sliderscale
    scale_names = [scale.name for scale in scales]
    for i, scale_name in enumerate(scale_names):
        jarjestys = 10 + i
        kysymys_root = Kysymys.objects.create(
            kysymys_fi=f"html_test_kysymys_s{i}0", kysymys_sv=f"html_test_kysymys_s{i}0_sv", **kysymys_kwargs,
            vastaustyyppi="matrix_root",
            jarjestys=jarjestys, matriisi_jarjestys=0,
            metatiedot={
                "type": "matrix_sliderscale",
                "description": {"fi": f"html_test_description_s{i}0", "sv": f"html_test_description_s{i}0_sv"}})
        matriisi_kysymysid = kysymys_root.kysymysid
        kysymys_root.matriisi_kysymysid = matriisi_kysymysid
        kysymys_root.save()
        Kysymys.objects.create(
            kysymys_fi=f"html_test_kysymys_s{i}1", kysymys_sv=f"html_test_kysymys_s{i}1_sv", **kysymys_kwargs,
            vastaustyyppi=scale_name,
            jarjestys=jarjestys, matriisi_jarjestys=1, matriisi_kysymysid=matriisi_kysymysid,
            metatiedot={
                "type": "matrix_sliderscale",
                "description": {"fi": f"html_test_description_s{i}1", "sv": f"html_test_description_s{i}1_sv"}})
        Kysymys.objects.create(
            kysymys_fi=f"html_test_kysymys_s{i}2", kysymys_sv=f"html_test_kysymys_s{i}2_sv", **kysymys_kwargs,
            vastaustyyppi=scale_name,
            jarjestys=jarjestys, matriisi_jarjestys=2, matriisi_kysymysid=matriisi_kysymysid,
            metatiedot={
                "type": "matrix_sliderscale",
                "description": {"fi": f"html_test_description_s{i}2", "sv": f"html_test_description_s{i}2_sv"}})

    # matrix radiobutton
    for i, scale_name in enumerate(scale_names):
        jarjestys = 10 + len(scale_names) + i
        kysymys_root = Kysymys.objects.create(
            kysymys_fi=f"html_test_kysymys_r{i}0", kysymys_sv=f"html_test_kysymys_r{i}0_sv", **kysymys_kwargs,
            vastaustyyppi="matrix_root",
            jarjestys=jarjestys, matriisi_jarjestys=0,
            metatiedot={
                "type": "matrix_radiobutton",
                "description": {"fi": f"html_test_description_r{i}0", "sv": f"html_test_description_r{i}0_sv"}})
        matriisi_kysymysid = kysymys_root.kysymysid
        kysymys_root.matriisi_kysymysid = matriisi_kysymysid
        kysymys_root.save()
        Kysymys.objects.create(
            kysymys_fi=f"html_test_kysymys_r{i}1", kysymys_sv=f"html_test_kysymys_r{i}1_sv", **kysymys_kwargs,
            vastaustyyppi=scale_name,
            jarjestys=jarjestys, matriisi_jarjestys=1, matriisi_kysymysid=matriisi_kysymysid,
            metatiedot={
                "type": "matrix_radiobutton",
                "description": {"fi": f"html_test_description_r{i}1", "sv": f"html_test_description_r{i}1_sv"}})
        Kysymys.objects.create(
            kysymys_fi=f"html_test_kysymys_r{i}2", kysymys_sv=f"html_test_kysymys_r{i}2_sv", **kysymys_kwargs,
            vastaustyyppi=scale_name,
            jarjestys=jarjestys, matriisi_jarjestys=2, matriisi_kysymysid=matriisi_kysymysid,
            metatiedot={
                "type": "matrix_radiobutton",
                "description": {"fi": f"html_test_description_r{i}2", "sv": f"html_test_description_r{i}2_sv"}})


def add_testing_responses_varda_tyontekijat(responses_obj):
    addr = (
        f"{settings.VARDA_TYONTEKIJAT_ENDPOINT.format('0.1.3')}"
        f"?page_size={settings.VARDA_TYONTEKIJA_COUNT_PER_REQUEST}")

    results = [{
        "id": 123,
        "kutsumanimi": "aa",
        "sukunimi": "aa",
        "sahkopostiosoite": "a@a.aa",
        "tutkinnot": ["101"],
        "tehtavanimikkeet": [{
            "tehtavanimike_koodi": "201", "kelpoisuus_kytkin": True}]}]
    responses_obj.add(
        responses_obj.GET,
        addr,
        json={"next": None, "previous": None, "results": results},
        status=status.HTTP_200_OK)
    responses_obj.add(
        responses_obj.GET,
        addr + "&tyontekija_id=123",
        json={"next": None, "previous": None, "results": results},
        status=status.HTTP_200_OK)


def add_testing_responses_localisation_ok(responses_obj):
    addr = f"{settings.LOCALISATION_ENDPOINT}/?key=indik.desc_testkey"
    responses_obj.add(
        responses_obj.GET,
        addr,
        json=[
            {"locale": "fi", "value": "fi_value", "key": "indik.desc_testkey"},
            {"locale": "sv", "value": "sv_value", "key": "indik.desc_testkey"}],
        status=status.HTTP_200_OK)


def add_testing_responses_localisation_sv_missing_ok(responses_obj):
    addr = f"{settings.LOCALISATION_ENDPOINT}/?key=indik.desc_testkey"
    responses_obj.add(
        responses_obj.GET,
        addr,
        json=[
            {"locale": "fi", "value": "fi_value", "key": "indik.desc_testkey"}],
        status=status.HTTP_200_OK)


def add_testing_responses_localisation_key_missing_ok(responses_obj):
    addr = f"{settings.LOCALISATION_ENDPOINT}/?key=indik.desc_testkey"
    responses_obj.add(
        responses_obj.GET, addr, json=[], status=status.HTTP_200_OK)


def add_testing_responses_taustatiedot_ok(responses_obj):
    addr = f"{settings.VARDA_TAUSTATIEDOT_ENDPOINT.format('0.1.2')}"
    responses_obj.add(
        responses_obj.GET, addr, json={
            "organisaatio_oid": "0.1.2",
            "toimipaikat": {"tm01": {"total": 1, "jm01": 1}},
            "lapset_voimassa": 10,
            "tyontekijat": {
                "total": 12,
                "tehtavanimikkeet": {"123": 5, "124": 7},
                "tehtavanimikkeet_kelpoiset": {"123": 5, "124": 7}},
            "taydennyskoulutukset": {
                "koulutuspaivat": "2.0",
                "tehtavanimikkeet": {"123": 1, "124": 1},
                "tehtavanimikkeet_koulutuspaivat": {"123": "1.0", "124": "1.0"}}
        }, status=status.HTTP_200_OK)


def add_testing_responses_taustatiedot_missing(responses_obj):
    addr = f"{settings.VARDA_TAUSTATIEDOT_ENDPOINT.format('0.1.2')}"
    responses_obj.add(
        responses_obj.GET, addr, json={
            "organisaatio_oid": "0.1.2",
            "toimipaikat": {},
            "lapset_voimassa": None,
            "tyontekijat": {},
            "taydennyskoulutukset": {}}, status=status.HTTP_200_OK)


def add_test_malfunction_messages():
    MalfunctionMessage.objects.create(code=1, message="message1")
    MalfunctionMessage.objects.create(code=2, message="message2")
