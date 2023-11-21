import re

from django.contrib.auth.models import User
from rest_framework import status

from raportointi.constants import (
    VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL, VALSSI_YLLAPITAJA_ORGANIZATION_OIDS,
    VALSSI_YLLAPITAJA_LEVEL, SURVEY_TYPE_ASIANTUNTIJALOMAKE, OPETUSHALLITUS_OID)
from raportointi.models import (
    Kayttaja, Kysely, KyselySend, Kyselykerta, Kysymysryhma, KyselyKysymysryhma, Vastaajatunnus, Vastaaja,
    Organisaatio, Kysymys, Vastaus, Scale, Koodi, Summary, Result)
from raportointi.utils import datenow_delta
from django.utils import timezone

from raportointipalvelu import settings

DATACOLLECTION_KYSELY_NAME = "dc_kysely"

DATACOLLECTIONS_KWARGS = [dict(
    kysely_name=f"{DATACOLLECTION_KYSELY_NAME}{i}",
    vastaajatunnus_name=f"dc_vastaajatunnus{i}",
    kyselykerta_name=f"dc_kyselykerta{i}",
) for i in range(5)]


def add_test_user():
    User.objects.create_user("test-user", "", "supersecret")


def add_test_kayttajat():
    Kayttaja.objects.create(oid="testikayttaja1_oid", uid="testikayttaja1", voimassa=True)


def add_test_kyselyt():
    koulutustoimija = Organisaatio.objects.create(nimi_fi="testikoulutustoimija1", oid="0.1.2", voimassa=True)
    datacollection_toimija = Organisaatio.objects.create(
        nimi_fi="datacollection_toimija", oid="0.1.2.1", voimassa=True)
    toimipaikka = Organisaatio.objects.create(nimi_fi="testitoimipaikka1", oid="0.1.3", voimassa=True)
    toimipaikka_not_sent = Organisaatio.objects.create(nimi_fi="datacollection_not_sent", oid="0.1.3.4", voimassa=True)

    time_now = timezone.now()
    timenow_plus_30d = datenow_delta(30)
    timenow_minus_100d = datenow_delta(-100)
    timenow_minus_60d = datenow_delta(-60)
    timenow_minus_61d = datenow_delta(-61)
    timenow_minus_59d = datenow_delta(-59)

    kayttaja1 = Kayttaja.objects.get(pk="testikayttaja1_oid")

    kysymysryhma1 = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma1")
    kysymysryhma2 = Kysymysryhma.objects.get(nimi_fi="testikysymysryhma2")
    kysymysryhma3 = Kysymysryhma.objects.get(nimi_fi="datacollection_paakayttaja_kysymysryhma")

    kayttajat_kwargs = dict(luotu_kayttaja=kayttaja1, muutettu_kayttaja=kayttaja1)
    default_kwargs = dict(voimassa_alkupvm=time_now,
                          voimassa_loppupvm=timenow_plus_30d,
                          koulutustoimija=koulutustoimija,
                          oppilaitos=toimipaikka,
                          metatiedot={"valssi_kysymysryhma": kysymysryhma1.pk},
                          **kayttajat_kwargs)

    # More than 2 month old kyselys
    kwargs_60d = dict(voimassa_alkupvm=timenow_minus_100d,
                      voimassa_loppupvm=timenow_minus_60d,
                      koulutustoimija=koulutustoimija,
                      oppilaitos=toimipaikka,
                      metatiedot={"valssi_kysymysryhma": kysymysryhma1.pk},
                      **kayttajat_kwargs)

    kwargs_61d = dict(voimassa_alkupvm=timenow_minus_100d,
                      voimassa_loppupvm=timenow_minus_61d,
                      koulutustoimija=koulutustoimija,
                      oppilaitos=toimipaikka,
                      metatiedot={"valssi_kysymysryhma": kysymysryhma1.pk},
                      **kayttajat_kwargs)

    kwargs_59d = dict(voimassa_alkupvm=timenow_minus_100d,
                      voimassa_loppupvm=timenow_minus_59d,
                      koulutustoimija=koulutustoimija,
                      oppilaitos=toimipaikka,
                      metatiedot={"valssi_kysymysryhma": kysymysryhma1.pk},
                      **kayttajat_kwargs)

    organisaatio_kwargs = dict(voimassa_alkupvm=time_now,
                               voimassa_loppupvm=timenow_plus_30d,
                               koulutustoimija=koulutustoimija,
                               metatiedot={"valssi_kysymysryhma": kysymysryhma1.pk},
                               **kayttajat_kwargs)

    toimipaikka_kwargs = dict(voimassa_alkupvm=time_now,
                              voimassa_loppupvm=timenow_plus_30d,
                              koulutustoimija=koulutustoimija,
                              oppilaitos=toimipaikka,
                              metatiedot={"valssi_kysymysryhma": kysymysryhma1.pk},
                              **kayttajat_kwargs)

    datacollection_paakayttaja_kwargs = dict(voimassa_alkupvm=time_now,
                                             voimassa_loppupvm=timenow_plus_30d,
                                             koulutustoimija=datacollection_toimija,
                                             metatiedot={"valssi_kysymysryhma": kysymysryhma3.pk},
                                             **kayttajat_kwargs)

    kysely1 = Kysely.objects.create(nimi_fi="testikysely1", **default_kwargs)
    kysely2 = Kysely.objects.create(nimi_fi="testikysely2", **default_kwargs)
    Kysely.objects.create(nimi_fi="testikysely_60d_old", **kwargs_60d)
    Kysely.objects.create(nimi_fi="testikysely_61d_old", **kwargs_61d)
    Kysely.objects.create(nimi_fi="testikysely_59d_old", **kwargs_59d)
    Kysely.objects.create(nimi_fi="organisaatiokysely", **organisaatio_kwargs)
    Kysely.objects.create(nimi_fi="toimipaikkakysely", **toimipaikka_kwargs)
    Kysely.objects.create(nimi_fi="dc_pk_no_kyselysend_vastaaja",
                          oppilaitos=toimipaikka_not_sent,
                          **datacollection_paakayttaja_kwargs)

    KyselyKysymysryhma.objects.create(kyselyid=kysely1, kysymysryhmaid=kysymysryhma1, **kayttajat_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely2, kysymysryhmaid=kysymysryhma2, **kayttajat_kwargs)

    # Create datacollection toimipaikka's & kysely's
    create_toimipaikka_kyselys(DATACOLLECTION_KYSELY_NAME, "dc_toimipaikka", "dc_koulutustoimija", 5)


def create_toimipaikka_kyselys(kysely_name, toimipaikka_name, koulutustoimija_name, amount):
    """Create multiple kysely's & toimipaikka's"""
    time_now = timezone.now()
    timenow_plus_30d = datenow_delta(30)

    kayttaja1 = Kayttaja.objects.get(pk="testikayttaja1_oid")
    kayttajat_kwargs = dict(luotu_kayttaja=kayttaja1, muutettu_kayttaja=kayttaja1)

    koulutustoimija = Organisaatio.objects.create(nimi_fi=f"{koulutustoimija_name}", oid="0.1.20.1", voimassa=True)

    kysymysryhma3 = Kysymysryhma.objects.get(nimi_fi="datacollection_paakayttaja_kysymysryhma")
    datacollection_paakayttaja_kwargs = dict(voimassa_alkupvm=time_now,
                                             voimassa_loppupvm=timenow_plus_30d,
                                             koulutustoimija=koulutustoimija,
                                             metatiedot={"valssi_kysymysryhma": kysymysryhma3.pk},
                                             **kayttajat_kwargs)

    for i in range(amount):
        toimipaikka = Organisaatio.objects.create(nimi_fi=f"{toimipaikka_name}{i}", oid=f"0.1.30.{i}", voimassa=True)
        Kysely.objects.create(nimi_fi=f"{kysely_name}{i}",
                              oppilaitos=toimipaikka,
                              **datacollection_paakayttaja_kwargs)


def add_test_kysymysryhmat():
    metatiedot_henkilostolomake = {
        "lomaketyyppi": "henkilostolomake_prosessitekijat",
        "paaIndikaattori": {
            "key": "pedagoginen_prosessi",
            "group": 1002
        },
        "sekondaariset_indikaattorit": [
            {
                "key": "myonteinen_ja_sitoutunut_vuorovaik",
                "group_id": 1000,
                "laatutekija": "prosessi"
            },
            {
                "key": "vastavuoroinen_vuorovaikutus",
                "group_id": 1001,
                "laatutekija": "prosessi"
            }
        ]
    }

    kayttaja1 = Kayttaja.objects.get(pk="testikayttaja1_oid")

    # Kysymysryhma kwargs
    kysymysryhma_kwargs = dict(luotu_kayttaja=kayttaja1,
                               muutettu_kayttaja=kayttaja1,
                               taustakysymykset=False,
                               valtakunnallinen=False,
                               metatiedot=metatiedot_henkilostolomake)

    # kysymysryhma1
    Kysymysryhma.objects.create(nimi_fi="testikysymysryhma1", **kysymysryhma_kwargs)

    # kysymysryhma2
    Kysymysryhma.objects.create(nimi_fi="testikysymysryhma2", **kysymysryhma_kwargs)

    # kysymysryhma for data-collection tests
    Kysymysryhma.objects.create(nimi_fi="datacollection_paakayttaja_kysymysryhma", **kysymysryhma_kwargs)

    # kysymysryhma for data-collection tests
    Kysymysryhma.objects.create(nimi_fi="reportingtemplate_yllapitaja_kysymysryhma", **kysymysryhma_kwargs)


def add_test_kysymykset():
    kayttaja = Kayttaja.objects.create(oid="html_test_user_oid", uid="html_test_user", voimassa=True)

    kayttaja_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    kysymysryhma = Kysymysryhma.objects.get(nimi_fi="reportingtemplate_yllapitaja_kysymysryhma")

    kysymys_kwargs = dict(
        kysymysryhmaid=kysymysryhma, pakollinen=False, eos_vastaus_sallittu=False, poistettava=False,
        jatkokysymys=False, **kayttaja_kwargs)

    # Textfield (tekstikenttä)
    Kysymys.objects.create(
        kysymys_fi="reportingtemplate test question FI", kysymys_sv="reportingtemplate test question SV",
        **kysymys_kwargs,
        vastaustyyppi="string",
        jarjestys=1, matriisi_jarjestys=None,
        metatiedot={
            "type": "string", "numeric": False, "multiline": False,
            "description": {"fi": "test description FI", "sv": "test description SV"}})

    Kysymys.objects.create(
        kysymys_fi="reportingtemplate test question FI2", kysymys_sv="reportingtemplate test question SV2",
        **kysymys_kwargs,
        vastaustyyppi="string",
        jarjestys=2, matriisi_jarjestys=None,
        metatiedot={
            "type": "string", "numeric": False, "multiline": False,
            "description": {"fi": "test description FI2", "sv": "test description SV2"}})


def add_test_kyselykerrat_vastaajatunnukset():
    time_now = timezone.now()
    timenow_plus_30d = datenow_delta(30)
    kayttaja1 = Kayttaja.objects.get(pk="testikayttaja1_oid")

    default_kwargs = dict(luotu_kayttaja=kayttaja1,
                          muutettu_kayttaja=kayttaja1,
                          voimassa_alkupvm=time_now,
                          voimassa_loppupvm=timenow_plus_30d)

    kysely1 = Kysely.objects.get(nimi_fi="testikysely1")
    kysely2 = Kysely.objects.get(nimi_fi="testikysely2")
    kysely6 = Kysely.objects.get(nimi_fi="dc_pk_no_kyselysend_vastaaja")

    kyselykerta1 = Kyselykerta.objects.create(
        kyselyid=kysely1, nimi="testikyselykerta1", lukittu=False, **default_kwargs)

    Kyselykerta.objects.create(
        kyselyid=kysely2, nimi="testikyselykerta2", lukittu=False, **default_kwargs)

    kyselykerta_no_vastaaja = Kyselykerta.objects.create(
        kyselyid=kysely6, nimi="dc_pk_no_kyselysend_vastaaja", lukittu=False, **default_kwargs)

    # 1.x
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_1",
        kohteiden_lkm=10, lukittu=False, **default_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_2",
        kohteiden_lkm=10, lukittu=False, **default_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_3",
        kohteiden_lkm=10, lukittu=False, **default_kwargs)

    # x.x
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta_no_vastaaja, tunnus="testivastaajatunnus5_1",
        kohteiden_lkm=10, lukittu=False, **default_kwargs)

    # Create kyselykerta's & vastaajatunnus'es for datacollection
    create_kyselykerta_vastaajatunnus(3, **DATACOLLECTIONS_KWARGS[0])

    create_kyselykerta_vastaajatunnus(3, **DATACOLLECTIONS_KWARGS[1])

    create_kyselykerta_vastaajatunnus(1, **DATACOLLECTIONS_KWARGS[2])

    create_kyselykerta_vastaajatunnus(4, **DATACOLLECTIONS_KWARGS[3])

    create_kyselykerta_vastaajatunnus(5, **DATACOLLECTIONS_KWARGS[4])


def create_kyselykerta_vastaajatunnus(amount, kysely_name, vastaajatunnus_name, kyselykerta_name):
    """Create multiple kyselykerta's & vastaajatunnus'es"""
    time_now = timezone.now()
    timenow_plus_30d = datenow_delta(30)
    kayttaja1 = Kayttaja.objects.get(pk="testikayttaja1_oid")

    default_kwargs = dict(luotu_kayttaja=kayttaja1,
                          muutettu_kayttaja=kayttaja1,
                          voimassa_alkupvm=time_now,
                          voimassa_loppupvm=timenow_plus_30d)

    kysely = Kysely.objects.get(nimi_fi=kysely_name)
    kyselykerta = Kyselykerta.objects.create(
        kyselyid=kysely, nimi=kyselykerta_name, lukittu=False, **default_kwargs)

    for i in range(amount):
        Vastaajatunnus.objects.create(
            kyselykertaid=kyselykerta, tunnus=f"{vastaajatunnus_name}{i}",
            kohteiden_lkm=10, lukittu=False, **default_kwargs)


def add_test_vastaaja():
    timenow_plus_30d = datenow_delta(30)

    kysely1 = Kysely.objects.get(nimi_fi="testikysely1")
    kyselykerta1 = Kyselykerta.objects.get(kyselyid=kysely1, nimi="testikyselykerta1")

    vastaajatunnus1_1 = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus1_1")

    Vastaaja.objects.create(
        kyselykertaid=kyselykerta1.kyselykertaid,
        kyselyid=kysely1.kyselyid,
        vastaajatunnus=vastaajatunnus1_1.vastaajatunnusid,
        luotuaika=timenow_plus_30d,
    )

    vastaajatunnus1_2 = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus1_2")

    Vastaaja.objects.create(
        kyselykertaid=kyselykerta1.kyselykertaid,
        kyselyid=kysely1.kyselyid,
        vastaajatunnus=vastaajatunnus1_2.vastaajatunnusid,
        luotuaika=timenow_plus_30d,
    )

    # Create vastaaja's for datecollection
    create_vastaajas(2, datenow_delta(30), **DATACOLLECTIONS_KWARGS[0])

    create_vastaajas(1, datenow_delta(35), **DATACOLLECTIONS_KWARGS[1])

    create_vastaajas(1, datenow_delta(40), **DATACOLLECTIONS_KWARGS[2])  # Latest answer date

    create_vastaajas(1, datenow_delta(-5), **DATACOLLECTIONS_KWARGS[3])

    create_vastaajas(2, datenow_delta(15), **DATACOLLECTIONS_KWARGS[4])


def create_vastaajas(amount, date_created, kysely_name, vastaajatunnus_name, kyselykerta_name):
    """Create multiple vastaaja's"""
    kysely = Kysely.objects.get(nimi_fi=kysely_name)
    kyselykerta = Kyselykerta.objects.get(kyselyid=kysely, nimi=kyselykerta_name)
    for i in range(amount):
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus=f"{vastaajatunnus_name}{i}")

        vastaaja = Vastaaja.objects.create(
            kyselykertaid=kyselykerta.kyselykertaid,
            kyselyid=kysely.kyselyid,
            vastaajatunnus=vastaajatunnus.vastaajatunnusid,
        )

        vastaaja.luotuaika = date_created
        vastaaja.save()


def add_test_kyselysend():
    kysely1 = Kysely.objects.get(nimi_fi="testikysely1")
    kyselykerta1 = Kyselykerta.objects.get(kyselyid=kysely1, nimi="testikyselykerta1")
    vastaajatunnus1_1 = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus1_1")
    vastaajatunnus1_2 = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus1_2")
    vastaajatunnus1_3 = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus1_3")

    # Test answer 1
    KyselySend.objects.create(
        email="asd1@example.com",
        kyselykerta=kyselykerta1.kyselykertaid,
        vastaajatunnus=vastaajatunnus1_1.vastaajatunnusid,
        msg_id=101,
        msg_status="delivered",
        message="test-msg1"
    )

    # Test answer 2
    KyselySend.objects.create(
        email="asd2@example.com",
        kyselykerta=kyselykerta1.kyselykertaid,
        vastaajatunnus=vastaajatunnus1_2.vastaajatunnusid,
        msg_id=102,
        msg_status="delivered",
        message="test-msg2"
    )

    # Test answer 3
    KyselySend.objects.create(
        email="asd3@example.com",
        kyselykerta=kyselykerta1.kyselykertaid,
        vastaajatunnus=vastaajatunnus1_3.vastaajatunnusid,
        msg_id=103,
        msg_status="delivered",
        message="test-msg3"
    )

    # Create kyselysends for datacollection
    create_kyselysends(3, **DATACOLLECTIONS_KWARGS[0])

    create_kyselysends(3, **DATACOLLECTIONS_KWARGS[1])

    create_kyselysends(1, **DATACOLLECTIONS_KWARGS[2])

    create_kyselysends(4, **DATACOLLECTIONS_KWARGS[3])

    create_kyselysends(5, **DATACOLLECTIONS_KWARGS[4])


def create_kyselysends(amount, kysely_name, vastaajatunnus_name, kyselykerta_name):
    """Create multiple kyselysend's"""
    kysely = Kysely.objects.get(nimi_fi=kysely_name)
    kyselykerta = Kyselykerta.objects.get(kyselyid=kysely, nimi=kyselykerta_name)
    for i in range(amount):
        vastaajatunnus = Vastaajatunnus.objects.get(tunnus=f"{vastaajatunnus_name}{i}")
        kysely_nr = re.findall(r"(\w+?)(\d+)", kysely_name)[0][1]
        KyselySend.objects.create(
            email=f"test-email{i}@example.com",
            kyselykerta=kyselykerta.kyselykertaid,
            vastaajatunnus=vastaajatunnus.vastaajatunnusid,
            msg_id=int(f"{kysely_nr}{i}"),
            msg_status="delivered",
            message=f"test-msg{i}"
        )


def add_viewreport_data():
    add_test_user()
    add_test_scales()
    add_test_codes()

    kysymysryhma_metatiedot = {
        "lomaketyyppi": "henkilostolomake_prosessitekijat",
        "paaIndikaattori": {
            "key": "pedagoginen_prosessi",
            "group": 1002
        },
        "sekondaariset_indikaattorit": [
            {
                "key": "myonteinen_ja_sitoutunut_vuorovaik",
                "group_id": 1000,
                "laatutekija": "prosessi"
            },
            {
                "key": "vastavuoroinen_vuorovaikutus",
                "group_id": 1001,
                "laatutekija": "prosessi"
            }
        ]
    }

    kayttaja = Kayttaja.objects.create(oid="viewreport_test_user_oid", uid="viewreport_user", voimassa=True)

    oph_org = Organisaatio.objects.create(
        nimi_fi="testi_opetushallitus", oid=OPETUSHALLITUS_OID, voimassa=True)
    # set parent_oid with self
    Organisaatio.objects.filter(oid=OPETUSHALLITUS_OID).update(parent_oid=oph_org)
    koulutustoimija = Organisaatio.objects.create(
        nimi_fi="testikoulutustoimija1", oid="0.1.2", parent_oid=oph_org, voimassa=True)
    toimipaikka = Organisaatio.objects.create(
        nimi_fi="testitoimipaikka1", oid="0.1.3", parent_oid=koulutustoimija, voimassa=True)

    second_koulutustoimija = Organisaatio.objects.create(nimi_fi="second_toimija", oid="0.1.999", voimassa=True)
    second_toimipaikka = Organisaatio.objects.create(
        nimi_fi="second_toimipaikka", oid="0.1.888", parent_oid=koulutustoimija, voimassa=True)

    timenow_minus_1d = datenow_delta(-1)
    timenow_minus_30d = datenow_delta(-30)

    timenow_minus_15d = datenow_delta(-15)
    timenow_minus_45d = datenow_delta(-45)

    timenow_minus_20d = datenow_delta(-20)
    timenow_minus_50d = datenow_delta(-50)

    timenow_minus_60d = datenow_delta(-60)

    timenow_minus_40d = datenow_delta(-40)
    timenow_minus_70d = datenow_delta(-70)

    timenow_minus_61d = datenow_delta(-61)
    timenow_minus_100d = datenow_delta(-100)

    # KWARGS
    kayttaja_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    # Kysymysryhma kvargs
    kysymysryhma_kwargs = dict(taustakysymykset=False,
                               valtakunnallinen=False,
                               metatiedot=kysymysryhma_metatiedot,
                               **kayttaja_kwargs)

    kyselykerta_vastaajatunnus_kwargs30d = dict(voimassa_alkupvm=timenow_minus_30d,
                                                voimassa_loppupvm=timenow_minus_1d,
                                                **kayttaja_kwargs)

    kyselykerta_vastaajatunnus_kwargs45d = dict(voimassa_alkupvm=timenow_minus_45d,
                                                voimassa_loppupvm=timenow_minus_15d,
                                                **kayttaja_kwargs)

    kyselykerta_vastaajatunnus_kwargs50d = dict(voimassa_alkupvm=timenow_minus_50d,
                                                voimassa_loppupvm=timenow_minus_20d,
                                                **kayttaja_kwargs)

    kyselykerta_vastaajatunnus_kwargs60d = dict(voimassa_alkupvm=timenow_minus_60d,
                                                voimassa_loppupvm=timenow_minus_20d,
                                                **kayttaja_kwargs)

    kyselykerta_vastaajatunnus_kwargs70d = dict(voimassa_alkupvm=timenow_minus_70d,
                                                voimassa_loppupvm=timenow_minus_40d,
                                                **kayttaja_kwargs)

    kyselykerta_vastaajatunnus_kwargs100d = dict(voimassa_alkupvm=timenow_minus_100d,
                                                 voimassa_loppupvm=timenow_minus_61d,
                                                 **kayttaja_kwargs)

    viewreport_kysymys_kwargs = dict(poistettava=False, jatkokysymys=False, **kayttaja_kwargs)

    # Create Kysymysryhmas
    viewreport_kysymysryhma = Kysymysryhma.objects.create(nimi_fi="reportview_kysymysryhma", **kysymysryhma_kwargs)
    viewreport_kysymysryhma2 = Kysymysryhma.objects.create(nimi_fi="reportview_kysymysryhma2", **kysymysryhma_kwargs)
    Kysymysryhma.objects.create(nimi_fi="reportview_kysymysryhma3", **kysymysryhma_kwargs)
    viewreport_kysymysryhma4 = Kysymysryhma.objects.create(nimi_fi="reportview_kysymysryhma4", **kysymysryhma_kwargs)

    kysely_kwargs = dict(voimassa_alkupvm=timenow_minus_30d,
                         voimassa_loppupvm=timenow_minus_1d,
                         koulutustoimija=koulutustoimija,
                         oppilaitos=toimipaikka,
                         metatiedot={"valssi_kysymysryhma": viewreport_kysymysryhma.pk},
                         **kayttaja_kwargs)

    kysely_kwargs2 = dict(voimassa_alkupvm=timenow_minus_30d,
                          voimassa_loppupvm=timenow_minus_1d,
                          koulutustoimija=koulutustoimija,
                          oppilaitos=toimipaikka,
                          metatiedot={"valssi_kysymysryhma": viewreport_kysymysryhma2.pk},
                          **kayttaja_kwargs)

    kysely_kwargs3 = dict(voimassa_alkupvm=timenow_minus_30d,
                          voimassa_loppupvm=timenow_minus_1d,
                          koulutustoimija=second_koulutustoimija,
                          oppilaitos=second_toimipaikka,
                          metatiedot={"valssi_kysymysryhma": viewreport_kysymysryhma4.pk},
                          **kayttaja_kwargs)

    # Create Kyselys
    viewreport_kysely = Kysely.objects.create(nimi_fi="viewreport", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="viewreport1", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="viewreport2", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="viewreport3", **kysely_kwargs2)
    Kysely.objects.create(nimi_fi="viewreport4", **kysely_kwargs2)
    viewreport_kysely_second_toimija = Kysely.objects.create(nimi_fi="viewreport_separate_toimija", **kysely_kwargs3)

    KyselyKysymysryhma.objects.create(
        kysymysryhmaid=viewreport_kysymysryhma, kyselyid=viewreport_kysely, **kayttaja_kwargs)

    # Create Kyselykerta which belongs to second koulutustoimija
    Kyselykerta.objects.create(
        kyselyid=viewreport_kysely_second_toimija,
        nimi="viewreport_kyselykerta_second_toimija",
        lukittu=False,
        **kyselykerta_vastaajatunnus_kwargs30d)

    kysymys_metatiedot = {"type": "matrix_sliderscale", "description": {"fi": "fi description", "sv": "sv description"}}
    # Create Kysymys
    matrix_root = Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="matrix_root", kysymysryhmaid=viewreport_kysymysryhma,
        kysymys_fi="view report matrix title", eos_vastaus_sallittu=False,
        matriisi_jarjestys=0, metatiedot=kysymys_metatiedot, **viewreport_kysymys_kwargs)
    matrix_root.matriisi_kysymysid = matrix_root.kysymysid

    matrix_1 = Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="toteutuu-asteikko", kysymysryhmaid=viewreport_kysymysryhma,
        kysymys_fi="view report question1", eos_vastaus_sallittu=False,
        matriisi_kysymysid=matrix_root.kysymysid, matriisi_jarjestys=1, metatiedot=kysymys_metatiedot,
        **viewreport_kysymys_kwargs)

    matrix_2 = Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="toteutuu-asteikko", kysymysryhmaid=viewreport_kysymysryhma,
        kysymys_fi="view report question2", eos_vastaus_sallittu=False,
        matriisi_kysymysid=matrix_root.kysymysid, matriisi_jarjestys=2, metatiedot=kysymys_metatiedot,
        **viewreport_kysymys_kwargs)

    # Create Kyselykerta
    viewreport_kyselykerta = Kyselykerta.objects.create(
        kyselyid=viewreport_kysely, nimi="viewreport_kyselykerta", lukittu=False,
        **kyselykerta_vastaajatunnus_kwargs30d)

    # Create Kyselykerta for kyselykerta list
    Kyselykerta.objects.create(
        kyselyid=viewreport_kysely, nimi="viewreport_kyselykerta_01", lukittu=False,
        **kyselykerta_vastaajatunnus_kwargs45d)

    # Create Kyselykerta for kyselykerta list
    Kyselykerta.objects.create(
        kyselyid=viewreport_kysely, nimi="viewreport_kyselykerta_02", lukittu=False,
        **kyselykerta_vastaajatunnus_kwargs50d)

    # Create Kyselykerta for kyselykerta list
    Kyselykerta.objects.create(
        kyselyid=viewreport_kysely, nimi="viewreport_kyselykerta_02", lukittu=False,
        **kyselykerta_vastaajatunnus_kwargs70d)

    # Create Summary
    Summary.objects.create(
        kysymysryhmaid=viewreport_kysely.kysymysryhmat.first().kysymysryhmaid,
        oppilaitos=viewreport_kysely.oppilaitos.oid,
        koulutustoimija=viewreport_kysely.koulutustoimija.oid,
        kysely_voimassa_alkupvm=viewreport_kysely.voimassa_alkupvm,
        is_locked=True, taustatiedot=dict())

    # not locked summary
    Summary.objects.create(
        kysymysryhmaid=viewreport_kysymysryhma.kysymysryhmaid,
        oppilaitos=viewreport_kysely.oppilaitos.oid,
        koulutustoimija=viewreport_kysely.koulutustoimija.oid,
        kysely_voimassa_alkupvm=timenow_minus_100d,
        is_locked=False, taustatiedot=dict())

    # Create Vastaajatunnus 1_1
    vastaajatunnus = Vastaajatunnus.objects.create(
        kyselykertaid=viewreport_kyselykerta, tunnus="viewreport_tunnus_1_1",
        kohteiden_lkm=10, lukittu=False, **kyselykerta_vastaajatunnus_kwargs30d)

    # Create Vastaaja 1_1
    vastaaja = Vastaaja.objects.create(
        kyselykertaid=viewreport_kyselykerta.kyselykertaid,
        kyselyid=viewreport_kyselykerta.kyselyid.kyselyid,
        vastaajatunnus=vastaajatunnus,
        tehtavanimikkeet=[
            {
                "kelpoisuus_kytkin": True,
                "tehtavanimike_koodi": "77826"
            },
            {
                "kelpoisuus_kytkin": True,
                "tehtavanimike_koodi": "77827"
            }
        ]
    )

    # Create Vastaajatunnus 1_2
    vastaajatunnus_1_2 = Vastaajatunnus.objects.create(
        kyselykertaid=viewreport_kyselykerta, tunnus="viewreport_tunnus_1_2",
        kohteiden_lkm=10, lukittu=False, **kyselykerta_vastaajatunnus_kwargs30d)

    # Create Vastaaja 1_2
    vastaaja_1_2 = Vastaaja.objects.create(
        kyselykertaid=viewreport_kyselykerta.kyselykertaid,
        kyselyid=viewreport_kyselykerta.kyselyid.kyselyid,
        vastaajatunnus=vastaajatunnus_1_2,
        tehtavanimikkeet=[
            {
                "kelpoisuus_kytkin": True,
                "tehtavanimike_koodi": "77826"
            },
            {
                "kelpoisuus_kytkin": True,
                "tehtavanimike_koodi": "77827"
            }
        ]
    )

    for i in range(3, 7):  # create at least 6 answers so view-report page is available
        vastaajatunnus_temp = Vastaajatunnus.objects.create(
            kyselykertaid=viewreport_kyselykerta, tunnus=f"viewreport_tunnus_1_{i}",
            kohteiden_lkm=10, lukittu=False, **kyselykerta_vastaajatunnus_kwargs30d)

        Vastaaja.objects.create(
            kyselykertaid=viewreport_kyselykerta.kyselykertaid,
            kyselyid=viewreport_kyselykerta.kyselyid.kyselyid,
            vastaajatunnus=vastaajatunnus_temp)

    # Create Vastaus
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja, numerovalinta=None)  # No answer
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_1_2, numerovalinta=1)
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja, numerovalinta=1)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=1)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=1)

    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=2)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=2)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=2)

    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=3)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=3)

    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=4)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=4)

    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=5)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=5)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja, numerovalinta=5)

    # Create Vastaus with answers less than 6
    # Create Kyselykerta 2
    viewreport_kyselykerta_2 = Kyselykerta.objects.create(
        kyselyid=viewreport_kysely, nimi="viewreport_kyselykerta_2", lukittu=False,
        **kyselykerta_vastaajatunnus_kwargs100d)

    # Create Vastaajatunnus 2
    vastaajatunnus_2 = Vastaajatunnus.objects.create(
        kyselykertaid=viewreport_kyselykerta_2, tunnus="viewreport_tunnus_2",
        kohteiden_lkm=10, lukittu=False, **kyselykerta_vastaajatunnus_kwargs100d)

    # Create Vastaaja 2
    vastaaja = Vastaaja.objects.create(
        kyselykertaid=viewreport_kyselykerta_2.kyselykertaid,
        kyselyid=viewreport_kyselykerta_2.kyselyid.kyselyid,
        vastaajatunnus=vastaajatunnus_2)
    # -----------------------------------------------------------

    # Create Kyselykerta 3
    viewreport_kyselykerta_3 = Kyselykerta.objects.create(
        kyselyid=viewreport_kysely, nimi="viewreport_kyselykerta_3", lukittu=False,
        **kyselykerta_vastaajatunnus_kwargs30d)

    # Create Vastaajatunnus 3
    vastaajatunnus_3 = Vastaajatunnus.objects.create(
        kyselykertaid=viewreport_kyselykerta_3, tunnus="viewreport_tunnus_3_1",
        kohteiden_lkm=10, lukittu=False, **kyselykerta_vastaajatunnus_kwargs30d)

    # Create Vastaaja 2
    vastaaja_2 = Vastaaja.objects.create(
        kyselykertaid=viewreport_kyselykerta_3.kyselykertaid,
        kyselyid=viewreport_kyselykerta_3.kyselyid.kyselyid,
        vastaajatunnus=vastaajatunnus_3)

    for i in range(2, 7):  # create at least 6 respondants & answers so view-report page is available
        vastaajatunnus_temp = Vastaajatunnus.objects.create(
            kyselykertaid=viewreport_kyselykerta_3, tunnus=f"viewreport_tunnus_3_{i}",
            kohteiden_lkm=10, lukittu=False, **kyselykerta_vastaajatunnus_kwargs30d)

        Vastaaja.objects.create(
            kyselykertaid=viewreport_kyselykerta_3.kyselykertaid,
            kyselyid=viewreport_kyselykerta_3.kyselyid.kyselyid,
            vastaajatunnus=vastaajatunnus_temp)

    # Create Vastaus
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_2, numerovalinta=None)  # No answer
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_2, numerovalinta=1)
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_2, numerovalinta=1)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_2, numerovalinta=1)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_2, numerovalinta=2)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_2, numerovalinta=2)
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_2, numerovalinta=3)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_2, numerovalinta=3)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_2, numerovalinta=4)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_2, numerovalinta=5)

    # Create Kyselykerta 4
    viewreport_kyselykerta_4 = Kyselykerta.objects.create(
        kyselyid=viewreport_kysely, nimi="viewreport_kyselykerta_4", lukittu=False,
        **kyselykerta_vastaajatunnus_kwargs60d)

    # Create Vastaajatunnus 3
    vastaajatunnus_4 = Vastaajatunnus.objects.create(
        kyselykertaid=viewreport_kyselykerta_4, tunnus="viewreport_tunnus_4_1",
        kohteiden_lkm=10, lukittu=False, **kyselykerta_vastaajatunnus_kwargs60d)

    for i in range(2, 7):  # create at least 6 respondants & answers so view-report page is available
        vastaajatunnus_4_temp = Vastaajatunnus.objects.create(
            kyselykertaid=viewreport_kyselykerta_4, tunnus=f"viewreport_tunnus_4_{i}",
            kohteiden_lkm=10, lukittu=False, **kyselykerta_vastaajatunnus_kwargs60d)

        Vastaaja.objects.create(
            kyselykertaid=viewreport_kyselykerta_4.kyselykertaid,
            kyselyid=viewreport_kyselykerta_4.kyselyid.kyselyid,
            vastaajatunnus=vastaajatunnus_4_temp)

    # Create Vastaaja 4
    vastaaja_4 = Vastaaja.objects.create(
        kyselykertaid=viewreport_kyselykerta_4.kyselykertaid,
        kyselyid=viewreport_kyselykerta_4.kyselyid.kyselyid,
        vastaajatunnus=vastaajatunnus_4)

    # Create Vastaus
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_4, numerovalinta=None)  # No answer
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_4, numerovalinta=1)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_4, numerovalinta=1)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_4, numerovalinta=2)
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_4, numerovalinta=3)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_4, numerovalinta=4)
    Vastaus.objects.create(kysymysid=matrix_2.kysymysid, vastaajaid=vastaaja_4, numerovalinta=5)
    Vastaus.objects.create(kysymysid=matrix_1.kysymysid, vastaajaid=vastaaja_4, numerovalinta=1)

    # data-export lomaketyyppi not found test data
    kysymysryhma_lomaketyyppi_not_found = Kysymysryhma.objects.create(
        nimi_fi="lomaketyyppi_not_found",
        taustakysymykset=False,
        valtakunnallinen=False,
        metatiedot=dict(lomaketyyppi="notfound"),
        **kayttaja_kwargs)
    kysely_lomaketyyppi_not_found = Kysely.objects.create(
        nimi_fi="lomaketyyppi_not_found",
        voimassa_alkupvm=timenow_minus_30d, voimassa_loppupvm=timenow_minus_1d,
        koulutustoimija=koulutustoimija, oppilaitos=toimipaikka,
        metatiedot=dict(valssi_kysymysryhma=kysymysryhma_lomaketyyppi_not_found.pk),
        **kayttaja_kwargs)
    KyselyKysymysryhma.objects.create(
        kysymysryhmaid=kysymysryhma_lomaketyyppi_not_found, kyselyid=kysely_lomaketyyppi_not_found, **kayttaja_kwargs)


def add_datacollection_no_toimipaikka_data():
    """Add kysely with no toimipaikka, 1 sent & 1 answered"""
    time_now = timezone.now()
    timenow_plus_30d = datenow_delta(30)
    kayttaja = Kayttaja.objects.get(pk="testikayttaja1_oid")

    kayttajat_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    datacollection_toimija = Organisaatio.objects.get(nimi_fi="datacollection_toimija")

    metatiedot_asiantuntijalomake = {
        "lomaketyyppi": SURVEY_TYPE_ASIANTUNTIJALOMAKE,
        "paaIndikaattori": {
            "key": "pedagoginen_prosessi", "group": 1002
        },
        "sekondaariset_indikaattorit": []
    }

    kysymysryhma_no_toimipaikka_kwargs = dict(luotu_kayttaja=kayttaja,
                                              muutettu_kayttaja=kayttaja,
                                              taustakysymykset=False,
                                              valtakunnallinen=False,
                                              metatiedot=metatiedot_asiantuntijalomake)

    # Create Kysymysryhma
    kysymysryhma = Kysymysryhma.objects.create(nimi_fi="dc_pk_no_toimipaikka", **kysymysryhma_no_toimipaikka_kwargs)

    dc_pk_no_toimipaikka_kwargs = dict(voimassa_alkupvm=time_now,
                                       voimassa_loppupvm=timenow_plus_30d,
                                       koulutustoimija=datacollection_toimija,
                                       metatiedot={"valssi_kysymysryhma": kysymysryhma.pk},
                                       **kayttajat_kwargs)

    default_kwargs = dict(luotu_kayttaja=kayttaja,
                          muutettu_kayttaja=kayttaja,
                          voimassa_alkupvm=time_now,
                          voimassa_loppupvm=timenow_plus_30d)

    # Create Kysely
    kysely_no_toimipaikka = Kysely.objects.create(nimi_fi="dc_pk_no_toimipaikka",
                                                  oppilaitos=None,
                                                  **dc_pk_no_toimipaikka_kwargs)

    # Create Kyselykerta
    kyselykerta_no_toimipaikka = Kyselykerta.objects.create(
        kyselyid=kysely_no_toimipaikka, nimi="dc_pk_no_toimipaikka", lukittu=False, **default_kwargs)

    # Create Vastaajatunnus
    vastaajatunnus_no_toimipaikka = Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta_no_toimipaikka, tunnus="no_toimipaikka_tunnus_1",
        kohteiden_lkm=10, lukittu=False, **default_kwargs)

    # Create Vastaaja
    Vastaaja.objects.create(
        kyselykertaid=kyselykerta_no_toimipaikka.kyselykertaid,
        kyselyid=kysely_no_toimipaikka.kyselyid,
        vastaajatunnus=vastaajatunnus_no_toimipaikka.vastaajatunnusid,
        luotuaika=timenow_plus_30d,
    )

    # Create Kyselysend
    KyselySend.objects.create(
        email="no_toimipaikka@example.com",
        kyselykerta=kyselykerta_no_toimipaikka.kyselykertaid,
        vastaajatunnus=vastaajatunnus_no_toimipaikka.vastaajatunnusid,
        msg_id=987,
        msg_status="delivered",
        message="no_toimipaikka_msg"
    )


def add_reportingtemplate_data():
    add_test_user()
    add_test_scales()

    metatiedot = {
        "lomaketyyppi": "henkilostolomake_prosessitekijat",
        "paaIndikaattori": {
            "key": "pedagoginen_prosessi",
            "group": 1002
        },
        "sekondaariset_indikaattorit": [
            {
                "key": "myonteinen_ja_sitoutunut_vuorovaik",
                "group_id": 1000,
                "laatutekija": "prosessi"
            },
            {
                "key": "vastavuoroinen_vuorovaikutus",
                "group_id": 1001,
                "laatutekija": "prosessi"
            }
        ]
    }

    kayttaja = Kayttaja.objects.create(oid="reportingtemplate_test_user_oid", uid="reportingtemplate_user",
                                       voimassa=True)

    # KWARGS
    kayttaja_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    # Kysymysryhma kvargs
    kysymysryhma_kwargs = dict(luotu_kayttaja=kayttaja,
                               muutettu_kayttaja=kayttaja,
                               taustakysymykset=False,
                               valtakunnallinen=False,
                               metatiedot=metatiedot)

    reportingtemplate_kysymys_kwargs = dict(poistettava=False, jatkokysymys=False, **kayttaja_kwargs)

    # Create Kysymysryhma
    reportingtemplate_kysymysryhma = Kysymysryhma.objects.create(
        nimi_fi="reportingtemplate_kysymysryhma", **kysymysryhma_kwargs)

    # Create Kysymys
    matrix_root = Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="matrix_root", kysymysryhmaid=reportingtemplate_kysymysryhma,
        kysymys_fi="reportingtemplate matrix title", eos_vastaus_sallittu=False,
        matriisi_jarjestys=0, **reportingtemplate_kysymys_kwargs)
    matrix_root.matriisi_kysymysid = matrix_root.kysymysid

    Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="toteutuu-asteikko", kysymysryhmaid=reportingtemplate_kysymysryhma,
        kysymys_fi="reportingtemplate question1", eos_vastaus_sallittu=False,
        matriisi_kysymysid=matrix_root.kysymysid, matriisi_jarjestys=1, **reportingtemplate_kysymys_kwargs)

    Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="toteutuu-asteikko", kysymysryhmaid=reportingtemplate_kysymysryhma,
        kysymys_fi="reportingtemplate question2", eos_vastaus_sallittu=False,
        matriisi_kysymysid=matrix_root.kysymysid, matriisi_jarjestys=2, **reportingtemplate_kysymys_kwargs)


def add_test_scales():
    scales = [
        {"name": "toteutuu-asteikko", "order_no": 1, "label": {"fi": "Toteutuu-asteikko", "sv": "Genomförs skala"}, "min_value": 1, "max_value": 5, "default_value": 3, "step_count": 5, "scale": [{"fi": "toteutuu erittäin heikosti", "sv": "genomförs mycket dåligt", "value": 1}, {"fi": "toteutuu heikosti", "sv": "genomförs dåligt", "value": 2}, {"fi": "toteutuu kohtalaisesti", "sv": "genomförs någorlunda", "value": 3}, {"fi": "toteutuu hyvin", "sv": "genomförs väl", "value": 4}, {"fi": "toteutuu erittäin hyvin", "sv": "genomförs mycket väl", "value": 5}], "eos_value": {"fi": "ei koske ryhmääni", "sv": "gäller inte min grupp", "value": 0}},
        {"name": "toteutuu_ekm", "order_no": 2, "label": {"fi": "Toteutuu EKM", "sv": "Genomförs GIM"}, "min_value": 1, "max_value": 5, "default_value": 3, "step_count": 5, "scale": [{"fi": "toteutuu erittäin heikosti", "sv": "genomförs mycket dåligt", "value": 1}, {"fi": "toteutuu heikosti", "sv": "genomförs dåligt", "value": 2}, {"fi": "toteutuu kohtalaisesti", "sv": "genomförs någorlunda", "value": 3}, {"fi": "toteutuu hyvin", "sv": "genomförs väl", "value": 4}, {"fi": "toteutuu erittäin hyvin", "sv": "genomförs mycket väl", "value": 5}], "eos_value": {"fi": "ei koske minua", "sv": "gäller inte mig", "value": 0}},
        {"name": "kuinka_usein_6", "order_no": 3, "label": {"fi": "Kuinka usein 6", "sv": "Hur ofta 6"}, "min_value": 1, "max_value": 6, "default_value": 3, "step_count": 6, "scale": [{"fi": "harvemmin kuin kerran kuukaudessa", "sv": "mer sällan än en gång i månaden", "value": 1}, {"fi": "kerran kuukaudessa", "sv": "en gång i månaden", "value": 2}, {"fi": "2-3 kertaa kuukaudessa", "sv": "2-3 gånger i månaden", "value": 3}, {"fi": "kerran viikossa", "sv": "en gång i veckan", "value": 4}, {"fi": "2-3 kertaa viikossa", "sv": "2-3 gånger i veckan", "value": 5}, {"fi": "päivittäin", "sv": "dagligen", "value": 6}], "eos_value": {"fi": "ei koske ryhmääni", "sv": "gäller inte min grupp", "value": 0}},
        {"name": "kuinka_usein_5", "order_no": 4, "label": {"fi": "Kuinka usein 5", "sv": "Hur ofta 5"}, "min_value": 1, "max_value": 5, "default_value": 3, "step_count": 5, "scale": [{"fi": "ei koskaan", "sv": "aldrig", "value": 1}, {"fi": "harvemmin kuin kerran kuukaudessa", "sv": "mer sällan än en gång i månaden", "value": 2}, {"fi": "kuukausittain", "sv": "varje månad", "value": 3}, {"fi": "viikoittain", "sv": "varje vecka", "value": 4}, {"fi": "päivittäin", "sv": "dagligen", "value": 5}], "eos_value": {"fi": "ei koske ryhmääni", "sv": "gäller inte min grupp", "value": 0}},
        {"name": "kylla_ei_valinta", "order_no": 5, "label": {"fi": "Kyllä-ei", "sv": "ja-nej"}, "min_value": 1, "max_value": 2, "default_value": 1, "step_count": 2, "scale": [{"fi": "ei", "sv": "nej", "value": 1}, {"fi": "kyllä", "sv": "ja", "value": 2}], "eos_value": {"fi": "ei koske ryhmääni", "sv": "gäller inte min grupp", "value": 0}},
        {"name": "olen_lukenut", "order_no": 6, "label": {"fi": "Olen lukenut", "sv": "Jag har läst"}, "min_value": 1, "max_value": 3, "default_value": 2, "step_count": 3, "scale": [{"fi": "en ole lukenut", "sv": "jag har inte läst", "value": 1}, {"fi": "olen lukenut osittain", "sv": "jag har läst delvis", "value": 2}, {"fi": "olen lukenut kokonaan", "sv": "jag har läst i sin helhet", "value": 3}], "eos_value": {"fi": "ei koske minua", "sv": "gäller inte mig", "value": 0}},
        {"name": "likert_asteikko", "order_no": 7, "label": {"fi": "Likert-asteikko", "sv": "Likertskala"}, "min_value": 1, "max_value": 5, "default_value": 3, "step_count": 5, "scale": [{"fi": "täysin eri mieltä", "sv": "helt av annan åsikt", "value": 1}, {"fi": "jokseenkin eri mieltä", "sv": "delvis av annan åsikt", "value": 2}, {"fi": "ei eri eikä samaa mieltä", "sv": "varken av annan eller av samma åsikt", "value": 3}, {"fi": "jokseenkin samaa mieltä", "sv": "delvis av samma åsikt", "value": 4}, {"fi": "täysin samaa mieltä", "sv": "helt av samma åsikt", "value": 5}], "eos_value": {"fi": "ei koske ryhmääni", "sv": "gäller inte min grupp", "value": 0}},
        {"name": "likert_ekm", "order_no": 8, "label": {"fi": "Likert-asteikko EKM", "sv": "Likertskala GIM"}, "min_value": 1, "max_value": 5, "default_value": 3, "step_count": 5, "scale": [{"fi": "täysin eri mieltä", "sv": "helt av annan åsikt", "value": 1}, {"fi": "jokseenkin eri mieltä", "sv": "delvis av annan åsikt", "value": 2}, {"fi": "ei eri eikä samaa mieltä", "sv": "varken av annan eller av samma åsikt", "value": 3}, {"fi": "jokseenkin samaa mieltä", "sv": "delvis av samma åsikt", "value": 4}, {"fi": "täysin samaa mieltä", "sv": "helt av samma åsikt", "value": 5}], "eos_value": {"fi": "ei koske minua", "sv": "gäller inte mig", "value": 0}},
        {"name": "toteutuminen", "order_no": 9, "label": {"fi": "Toteutuminen", "sv": "Förverkligas"}, "min_value": 1, "max_value": 4, "default_value": 2, "step_count": 4, "scale": [{"fi": "ei toteudu", "sv": "genomförs inte", "value": 1}, {"fi": "toteutuu osittain", "sv": "genomförs delvis", "value": 2}, {"fi": "toteutuu kokonaan", "sv": "genomförs helt", "value": 3}, {"fi": "ei koske kuntaamme", "sv": "gäller inte vår kommun", "value": 4}], "eos_value": {"fi": "ei koske ryhmääni", "sv": "gäller inte min grupp", "value": 0}},
        {"name": "toteutuminen_3", "order_no": 10, "label": {"fi": "Toteutuminen 3", "sv": "Förverkligas 3"}, "min_value": 1, "max_value": 3, "default_value": 2, "step_count": 3, "scale": [{"fi": "ei toteudu", "sv": "genomförs inte", "value": 1}, {"fi": "toteutuu osittain", "sv": "genomförs delvis", "value": 2}, {"fi": "toteutuu kokonaan", "sv": "genomförs helt", "value": 3}], "eos_value": {"fi": "ei koske ryhmääni", "sv": "gäller inte min grupp", "value": 0}},
        {"name": "vastuut", "order_no": 11, "label": {"fi": "Vastuut", "sv": "Ansvar"}, "min_value": 1, "max_value": 3, "default_value": 2, "step_count": 3, "scale": [{"fi": "vastuita ei ole määritelty", "sv": "ansvaret är inte definierat", "value": 1}, {"fi": "vastuut ovat jossain määrin epäselvät", "sv": "ansvaret är något oklart", "value": 2}, {"fi": "vastuut on määritelty", "sv": "ansvaret är definierat", "value": 3}], "eos_value": {"fi": "ei koske ryhmääni", "sv": "gäller inte min grupp", "value": 0}}
    ]

    for scale in scales:
        scale_values = dict(
            order_no=scale["order_no"], label_fi=scale["label"]["fi"], label_sv=scale["label"]["sv"],
            min_value=scale["min_value"], max_value=scale["max_value"], default_value=scale["default_value"],
            step_count=scale["step_count"], scale=scale["scale"], eos_value=scale["eos_value"])
        scale_obj = Scale.objects.filter(name=scale["name"])
        # create if name is missing, update if there is changes
        if not scale_obj.exists():
            Scale.objects.create(name=scale["name"], **scale_values)
        elif not scale_obj.filter(**scale_values).exists():
            scale_obj.update(**scale_values)


def add_test_codes():
    Koodi.objects.create(
        koodisto_uri="vardatehtavanimike", nimi_fi="test kindergarten", nimi_sv="test daghem", koodi_arvo="77826")
    Koodi.objects.create(
        koodisto_uri="vardatehtavanimike", nimi_fi="test kindergarten 2", nimi_sv="test daghem 2", koodi_arvo="77827")


def add_testing_responses_kayttooikeus_yllapitaja_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo",
            "organisaatiot": [
                {"organisaatioOid": VALSSI_YLLAPITAJA_ORGANIZATION_OIDS[0],
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_YLLAPITAJA_LEVEL}]}
            ]}], status=status.HTTP_200_OK)


def add_testing_responses_kayttooikeus_paakayttaja_only_ok(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username=test-user",
        json=[{
            "oidHenkilo": "test-oidhenkilo",
            "organisaatiot": [
                {"organisaatioOid": "0.1.2.1",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PAAKAYTTAJA_LEVEL}]},
                {"organisaatioOid": "0.1.20.1",
                 "kayttooikeudet": [{"palvelu": "VALSSI", "oikeus": VALSSI_PAAKAYTTAJA_LEVEL}]},
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


def add_testing_responses_service_ticket_fail_500(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.OPINTOPOLKU_URL}/cas/v1/tickets",
        headers={"Location": "http://a"}, status=status.HTTP_201_CREATED)

    responses_obj.add(
        responses_obj.POST, "http://a", json={}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def add_test_summaries():
    add_test_kayttajat()

    timenow = timezone.now()
    timenow_minus_1d = datenow_delta(-1)
    timenow_minus_2d = datenow_delta(-2)
    timenow_plus_30d = datenow_delta(30)
    kayttaja1 = Kayttaja.objects.get(pk="testikayttaja1_oid")

    oph = Organisaatio.objects.create(nimi_fi="oph", oid=OPETUSHALLITUS_OID, voimassa=True)
    koulutustoimija = Organisaatio.objects.create(
        nimi_fi="summary_testikoulutustoimija", oid="0.1.2", parent_oid=oph, voimassa=True)
    oppilaitos = Organisaatio.objects.create(nimi_fi="summary_testioppilaitos", oid="0.1.3", voimassa=True)

    kayttaja_kwargs = dict(luotu_kayttaja=kayttaja1, muutettu_kayttaja=kayttaja1)
    default_kwargs = dict(voimassa_loppupvm=timenow_plus_30d, **kayttaja_kwargs)

    # test Kysymysryhmas
    kysymysryhma_metatiedot = {
        "lomaketyyppi": "testilomaketyyppi",
        "paaIndikaattori": {"key": "pedagoginen_prosessi", "group": 1002},
        "sekondaariset_indikaattorit": [{"key": "toiminnan_havainnointi", "group": 1002}]}
    kysymysryhma1 = Kysymysryhma.objects.create(
        nimi_fi="summary_testikysymysryhma1",
        taustakysymykset=False, valtakunnallinen=False,
        metatiedot=kysymysryhma_metatiedot, **kayttaja_kwargs)
    kysymysryhma2 = Kysymysryhma.objects.create(
        nimi_fi="summary_testikysymysryhma2",
        taustakysymykset=False, valtakunnallinen=False,
        metatiedot=kysymysryhma_metatiedot, **kayttaja_kwargs)
    kysymysryhma3 = Kysymysryhma.objects.create(
        nimi_fi="summary_testikysymysryhma3",
        taustakysymykset=False, valtakunnallinen=False,
        metatiedot=kysymysryhma_metatiedot, **kayttaja_kwargs)

    # test Kyselys
    kysely1 = Kysely.objects.create(
        nimi_fi="summary_testikysely1", koulutustoimija=koulutustoimija, oppilaitos=oppilaitos,
        voimassa_alkupvm=timenow_minus_2d, **default_kwargs)
    kysely2 = Kysely.objects.create(
        nimi_fi="summary_testikysely2", koulutustoimija=koulutustoimija, oppilaitos=oppilaitos,
        voimassa_alkupvm=timenow_minus_1d, **default_kwargs)
    kysely3 = Kysely.objects.create(
        nimi_fi="summary_testikysely3", koulutustoimija=koulutustoimija, oppilaitos=oppilaitos,
        voimassa_alkupvm=timenow, **default_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely1, kysymysryhmaid=kysymysryhma1, **kayttaja_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely2, kysymysryhmaid=kysymysryhma2, **kayttaja_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely3, kysymysryhmaid=kysymysryhma3, **kayttaja_kwargs)

    summary_data_kwargs = dict(
        group_info="testig", kuvaus="testi1", aineisto="testi2", vahvuudet="testi3",
        kohteet="testi4", keh_toimenpiteet="testi5", seur_toimenpiteet="testi6")

    # test Summaries
    # locked summary
    Summary.objects.create(
        kysymysryhmaid=kysymysryhma1.kysymysryhmaid,
        oppilaitos=kysely1.oppilaitos.oid,
        koulutustoimija=kysely1.koulutustoimija.oid,
        kysely_voimassa_alkupvm=kysely1.voimassa_alkupvm,
        is_locked=True, **summary_data_kwargs,
        taustatiedot=dict(koulutustoimija=kysely1.koulutustoimija.oid, paaindikaattori="aa"))

    # not locked summary
    Summary.objects.create(
        kysymysryhmaid=kysymysryhma2.kysymysryhmaid,
        oppilaitos=kysely2.oppilaitos.oid,
        koulutustoimija=kysely2.koulutustoimija.oid,
        kysely_voimassa_alkupvm=kysely2.voimassa_alkupvm,
        is_locked=False, **summary_data_kwargs,
        taustatiedot=dict(koulutustoimija=kysely2.koulutustoimija.oid, paaindikaattori="aa"))


def add_test_results():
    add_test_summaries()

    kysymysryhma1 = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma1")
    kysymysryhma2 = Kysymysryhma.objects.get(nimi_fi="summary_testikysymysryhma2")
    koulutustoimija = Organisaatio.objects.get(nimi_fi="summary_testikoulutustoimija")

    result_data_kwargs = dict(
        kuvaus="testi1", aineisto="testi2", vahvuudet="testi3",
        kohteet="testi4", keh_toimenpiteet="testi5", seur_toimenpiteet="testi6")

    kysely1 = Kysely.objects.get(nimi_fi="summary_testikysely1")
    kysely2 = Kysely.objects.get(nimi_fi="summary_testikysely2")

    # test Results
    # locked result
    Result.objects.create(
        kysymysryhmaid=kysymysryhma1.kysymysryhmaid,
        koulutustoimija=koulutustoimija.oid,
        kysely_voimassa_alkupvm=kysely1.voimassa_alkupvm,
        is_locked=True, **result_data_kwargs,
        taustatiedot=dict(koulutustoimija=koulutustoimija.oid, paaindikaattori="aa"))

    # not locked result
    Result.objects.create(
        kysymysryhmaid=kysymysryhma2.kysymysryhmaid,
        koulutustoimija=koulutustoimija.oid,
        kysely_voimassa_alkupvm=kysely2.voimassa_alkupvm,
        is_locked=False, **result_data_kwargs,
        taustatiedot=dict(koulutustoimija=koulutustoimija.oid, paaindikaattori="aa"))


def add_testing_responses_localisation_indikaattori(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.LOCALISATION_ENDPOINT}/?key=indik.desc_aa",
        json=[{"locale": "fi", "value": "FI indikaattori"},
              {"locale": "sv", "value": "SV indikaattori"}], status=status.HTTP_200_OK)


def load_testing_data():
    add_test_user()
    add_test_kayttajat()
    add_test_kysymysryhmat()
    add_test_kyselyt()
    add_test_kysymykset()
    add_test_kyselykerrat_vastaajatunnukset()
    add_test_vastaaja()
    add_test_kyselysend()
    add_datacollection_no_toimipaikka_data()
