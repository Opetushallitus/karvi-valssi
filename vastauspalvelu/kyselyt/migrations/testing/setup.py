from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from kyselyt.migrations.testing.test_scales import TEST_SCALES
from kyselyt.models import (
    Kysely, Kayttaja, Organisaatio, Kysymys, Kysymysryhma, KyselyKysymysryhma, Kyselykerta, Vastaajatunnus, TilaEnum,
    Vastaaja, Vastaus)


def add_test_kayttajat():
    Kayttaja.objects.create(oid="testikayttaja1_oid", uid="testikayttaja1", voimassa=True)


def add_test_kyselyt():
    time_now = timezone.now()
    timenow_plus_30d = time_now + timedelta(days=30)
    kayttaja = Kayttaja.objects.get(pk="testikayttaja1_oid")

    oppilaitos = Organisaatio.objects.create(nimi_fi="testioppilaitos1", oid="0.1.3", voimassa=True)

    kysely_kwargs = dict(
        voimassa_alkupvm=time_now, voimassa_loppupvm=timenow_plus_30d,
        luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    Kysely.objects.create(nimi_fi="testikysely1", oppilaitos=oppilaitos, **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely3", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely4", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely4_2", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely5", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely6", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely7", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely8", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely9", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely10", **kysely_kwargs)
    Kysely.objects.create(nimi_fi="testikysely11", **kysely_kwargs)


def add_test_kysymysryhmat_kysymykset_kyselykysymysryhmat():
    kayttaja = Kayttaja.objects.get(pk="testikayttaja1_oid")

    kayttaja_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    kysymys_kwargs = dict(poistettava=False, jatkokysymys=False, **kayttaja_kwargs)

    kysymysryhma_kwargs = dict(taustakysymykset=False, valtakunnallinen=False, **kayttaja_kwargs)

    # # kysymysryhma1
    kysymysryhma1 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma1", **kysymysryhma_kwargs)

    # arvosana question
    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="likert_asteikko",
        kysymysryhmaid=kysymysryhma1,
        kysymys_fi="testikysymys1_1", eos_vastaus_sallittu=False, **kysymys_kwargs)

    # mandatory arvosana question
    Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="likert_asteikko",
        kysymysryhmaid=kysymysryhma1,
        kysymys_fi="testikysymys1_2", eos_vastaus_sallittu=False, **kysymys_kwargs)

    kysely1 = Kysely.objects.get(nimi_fi="testikysely1")
    KyselyKysymysryhma.objects.create(kyselyid=kysely1, kysymysryhmaid=kysymysryhma1, **kayttaja_kwargs)

    # # kysymysryhma2
    kysymysryhma2 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma2", **kysymysryhma_kwargs)

    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="likert_asteikko",
        kysymysryhmaid=kysymysryhma2,
        kysymys_fi="testikysymys2_1", eos_vastaus_sallittu=False, **kysymys_kwargs)

    # # kysymysryhma3
    kysymysryhma3 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma3", **kysymysryhma_kwargs)

    # eos allowed question
    Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="likert_asteikko",
        kysymysryhmaid=kysymysryhma3,
        kysymys_fi="testikysymys3_1", eos_vastaus_sallittu=True, **kysymys_kwargs)

    kysely3 = Kysely.objects.get(nimi_fi="testikysely3")
    KyselyKysymysryhma.objects.create(kyselyid=kysely3, kysymysryhmaid=kysymysryhma3, **kayttaja_kwargs)

    # # kysymysryhma4
    kysymysryhma4 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma4", **kysymysryhma_kwargs)

    # monivalinta question (checkbox, multi-choice)
    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="monivalinta",
        kysymysryhmaid=kysymysryhma4,
        kysymys_fi="testikysymys4_2", monivalinta_max=2, eos_vastaus_sallittu=False, **kysymys_kwargs,
        metatiedot={
            "type": "checkbox",
            "vastausvaihtoehdot": [
                {"id": 1, "label": "ve1", "checked": False},
                {"id": 2, "label": "ve2", "checked": False},
                {"id": 3, "label": "ve3", "checked": False}]})

    # kysely for monivalinta/checkbox tests
    kysely4 = Kysely.objects.get(nimi_fi="testikysely4")
    KyselyKysymysryhma.objects.create(kyselyid=kysely4, kysymysryhmaid=kysymysryhma4, **kayttaja_kwargs)

    # # kysymysryhma4_2
    kysymysryhma4_2 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma4_2", **kysymysryhma_kwargs)

    # monivalinta question (radiobutton, 1-choice)
    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="monivalinta",
        kysymysryhmaid=kysymysryhma4_2,
        kysymys_fi="testikysymys4_2_1", eos_vastaus_sallittu=True, **kysymys_kwargs,
        metatiedot={
            "type": "radiobutton",
            "vastausvaihtoehdot": [
                {"id": 1, "label": "ve1", "checked": False},
                {"id": 2, "label": "ve2", "checked": False},
                {"id": 3, "label": "ve3", "checked": False}]})

    # kysely for monivalinta/radiobutton tests
    kysely4_2 = Kysely.objects.get(nimi_fi="testikysely4_2")
    KyselyKysymysryhma.objects.create(kyselyid=kysely4_2, kysymysryhmaid=kysymysryhma4_2, **kayttaja_kwargs)

    # # kysymysryhma5
    kysymysryhma5 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma5", **kysymysryhma_kwargs)

    # string question
    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="string",
        kysymysryhmaid=kysymysryhma5,
        kysymys_fi="testikysymys5_1", max_vastaus=3, eos_vastaus_sallittu=False, **kysymys_kwargs)

    # string question (mandatory)
    Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="string",
        kysymysryhmaid=kysymysryhma5,
        kysymys_fi="testikysymys5_2", max_vastaus=3, eos_vastaus_sallittu=False, **kysymys_kwargs)

    kysely5 = Kysely.objects.get(nimi_fi="testikysely5")
    KyselyKysymysryhma.objects.create(kyselyid=kysely5, kysymysryhmaid=kysymysryhma5, **kayttaja_kwargs)

    # # kysymysryhma6
    kysymysryhma6 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma6", **kysymysryhma_kwargs)

    # kylla_ei_valinta question
    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="kylla_ei_valinta",
        kysymysryhmaid=kysymysryhma6,
        kysymys_fi="testikysymys6_1", eos_vastaus_sallittu=False, **kysymys_kwargs)

    kysely6 = Kysely.objects.get(nimi_fi="testikysely6")
    KyselyKysymysryhma.objects.create(kyselyid=kysely6, kysymysryhmaid=kysymysryhma6, **kayttaja_kwargs)

    # # kysymysryhma7_1 kysymysryhma7_2
    kysymysryhma71 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma7_1", **kysymysryhma_kwargs)

    # questions created in "wrong" order
    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="likert_asteikko", kysymysryhmaid=kysymysryhma71,
        kysymys_fi="testikysymys7_1_1", eos_vastaus_sallittu=False, jarjestys=1, **kysymys_kwargs)

    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="likert_asteikko", kysymysryhmaid=kysymysryhma71,
        kysymys_fi="testikysymys7_1_2", eos_vastaus_sallittu=False, jarjestys=0, **kysymys_kwargs)

    kysymysryhma72 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma7_2", **kysymysryhma_kwargs)

    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="likert_asteikko", kysymysryhmaid=kysymysryhma72,
        kysymys_fi="testikysymys7_2_1", eos_vastaus_sallittu=False, **kysymys_kwargs)

    # question groups in "wrong" order
    kysely7 = Kysely.objects.get(nimi_fi="testikysely7")
    KyselyKysymysryhma.objects.create(kyselyid=kysely7, kysymysryhmaid=kysymysryhma71, jarjestys=1, **kayttaja_kwargs)
    KyselyKysymysryhma.objects.create(kyselyid=kysely7, kysymysryhmaid=kysymysryhma72, jarjestys=0, **kayttaja_kwargs)

    # # kysymysryhma8
    tila_julkaistu, _ = TilaEnum.objects.get_or_create(nimi="julkaistu")
    kysymysryhma8 = Kysymysryhma.objects.create(
        nimi_fi="testikysymysryhma8", tila=tila_julkaistu,
        metatiedot={"paaIndikaattori": {"key": "somekey"}}, **kysymysryhma_kwargs)

    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="string", kysymysryhmaid=kysymysryhma8,
        kysymys_fi="testikysymys8_1", eos_vastaus_sallittu=False, **kysymys_kwargs,
        matriisi_jarjestys=None,
        metatiedot={
            "type": "string", "numeric": False, "multiline": False,
            "description": {"fi": "html_test_description_0", "sv": "html_test_description_0_sv"}})

    kysely8 = Kysely.objects.get(nimi_fi="testikysely8")
    KyselyKysymysryhma.objects.create(kyselyid=kysely8, kysymysryhmaid=kysymysryhma8, **kayttaja_kwargs)

    # # kysymysryhma9
    kysymysryhma9 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma9", **kysymysryhma_kwargs)

    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="likert_asteikko", kysymysryhmaid=kysymysryhma9,
        kysymys_fi="testikysymys9_1", eos_vastaus_sallittu=False, **kysymys_kwargs)

    # kysely for pdfemail queue test
    kysely9 = Kysely.objects.get(nimi_fi="testikysely9")
    KyselyKysymysryhma.objects.create(kyselyid=kysely9, kysymysryhmaid=kysymysryhma9, **kayttaja_kwargs)

    # # kysymysryhma10
    kysymysryhma10 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma10", **kysymysryhma_kwargs)

    Kysymys.objects.create(
        pakollinen=False, vastaustyyppi="string", kysymysryhmaid=kysymysryhma10,
        kysymys_fi="testikysymys10_1", eos_vastaus_sallittu=False,
        metatiedot={"numeric": True}, **kysymys_kwargs)

    # kysely for numerovalinta tests
    kysely10 = Kysely.objects.get(nimi_fi="testikysely10")
    KyselyKysymysryhma.objects.create(kyselyid=kysely10, kysymysryhmaid=kysymysryhma10, **kayttaja_kwargs)

    # # kysymysryhma11
    kysymysryhma11 = Kysymysryhma.objects.create(nimi_fi="testikysymysryhma11", **kysymysryhma_kwargs)

    matriisi_root1 = Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="matrix_root", kysymysryhmaid=kysymysryhma11,
        kysymys_fi="testikysymys11_0", eos_vastaus_sallittu=False,
        matriisi_jarjestys=0, **kysymys_kwargs)
    matriisi_root1.matriisi_kysymysid = matriisi_root1.kysymysid

    Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="likert_asteikko", kysymysryhmaid=kysymysryhma11,
        kysymys_fi="testikysymys11_1", eos_vastaus_sallittu=False,
        matriisi_kysymysid=matriisi_root1.kysymysid, matriisi_jarjestys=1, **kysymys_kwargs)

    Kysymys.objects.create(
        pakollinen=True, vastaustyyppi="likert_asteikko", kysymysryhmaid=kysymysryhma11,
        kysymys_fi="testikysymys11_2", eos_vastaus_sallittu=False,
        matriisi_kysymysid=matriisi_root1.kysymysid, matriisi_jarjestys=2, **kysymys_kwargs)

    # kysely for matrix tests
    kysely11 = Kysely.objects.get(nimi_fi="testikysely11")
    KyselyKysymysryhma.objects.create(kyselyid=kysely11, kysymysryhmaid=kysymysryhma11, **kayttaja_kwargs)


def add_test_kyselykerrat_vastaajatunnukset():
    time_now = timezone.now()
    timenow_plus_30d = time_now + timedelta(days=30)
    kayttaja = Kayttaja.objects.get(pk="testikayttaja1_oid")

    kayttaja_kwargs = dict(luotu_kayttaja=kayttaja, muutettu_kayttaja=kayttaja)

    voimassa_kwargs = dict(voimassa_alkupvm=time_now, voimassa_loppupvm=timenow_plus_30d)

    # # kyselykerta1
    kysely1 = Kysely.objects.get(nimi_fi="testikysely1")
    kyselykerta1 = Kyselykerta.objects.create(
        kyselyid=kysely1, nimi="testikyselykerta1", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_1",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_2",
        kohteiden_lkm=1, lukittu=True, **voimassa_kwargs, **kayttaja_kwargs)

    timenow_plus_3d = time_now + timedelta(days=3)
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_3",
        kohteiden_lkm=1, lukittu=False,
        voimassa_alkupvm=timenow_plus_3d,
        voimassa_loppupvm=timenow_plus_30d, **kayttaja_kwargs)

    timenow_minus_30d = time_now - timedelta(days=30)
    timenow_minus_3d = time_now - timedelta(days=3)
    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_4",
        kohteiden_lkm=1, lukittu=False,
        voimassa_alkupvm=timenow_minus_30d,
        voimassa_loppupvm=timenow_minus_3d, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_5",
        kohteiden_lkm=1, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_6",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta1, tunnus="testivastaajatunnus1_7",
        kohteiden_lkm=1, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta2
    kyselykerta2 = Kyselykerta.objects.create(
        kyselyid=kysely1, nimi="testikyselykerta2", lukittu=True, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta2, tunnus="testivastaajatunnus2_1",
        kohteiden_lkm=1, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta3
    kysely3 = Kysely.objects.get(nimi_fi="testikysely3")
    kyselykerta3 = Kyselykerta.objects.create(
        kyselyid=kysely3, nimi="testikyselykerta3", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta3, tunnus="testivastaajatunnus3_1",
        kohteiden_lkm=1, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta4
    kysely4 = Kysely.objects.get(nimi_fi="testikysely4")
    kyselykerta4 = Kyselykerta.objects.create(
        kyselyid=kysely4, nimi="testikyselykerta4", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta4, tunnus="testivastaajatunnus4_1",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta4_2
    kysely4_2 = Kysely.objects.get(nimi_fi="testikysely4_2")
    kyselykerta4_2 = Kyselykerta.objects.create(
        kyselyid=kysely4_2, nimi="testikyselykerta4_2", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta4_2, tunnus="testivastaajatunnus4_2_1",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta5
    kysely5 = Kysely.objects.get(nimi_fi="testikysely5")
    kyselykerta5 = Kyselykerta.objects.create(
        kyselyid=kysely5, nimi="testikyselykerta5", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta5, tunnus="testivastaajatunnus5_1",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta5, tunnus="testivastaajatunnus5_2",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta5, tunnus="testivastaajatunnus5_3",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta6
    kysely6 = Kysely.objects.get(nimi_fi="testikysely6")
    kyselykerta6 = Kyselykerta.objects.create(
        kyselyid=kysely6, nimi="testikyselykerta6", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta6, tunnus="testivastaajatunnus6_1",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta7
    kysely7 = Kysely.objects.get(nimi_fi="testikysely7")
    kyselykerta7 = Kyselykerta.objects.create(
        kyselyid=kysely7, nimi="testikyselykerta7", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta7, tunnus="testivastaajatunnus7_1",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta8
    kysely8 = Kysely.objects.get(nimi_fi="testikysely8")
    kyselykerta8 = Kyselykerta.objects.create(
        kyselyid=kysely8, nimi="testikyselykerta8", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta8, tunnus="testivastaajatunnus8_1",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta8, tunnus="testivastaajatunnus8_2",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta9
    kysely9 = Kysely.objects.get(nimi_fi="testikysely9")
    kyselykerta9 = Kyselykerta.objects.create(
        kyselyid=kysely9, nimi="testikyselykerta9", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta9, tunnus="testivastaajatunnus9",
        kohteiden_lkm=1, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta10
    kysely10 = Kysely.objects.get(nimi_fi="testikysely10")
    kyselykerta10 = Kyselykerta.objects.create(
        kyselyid=kysely10, nimi="testikyselykerta10", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta10, tunnus="testivastaajatunnus10",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    # # kyselykerta11
    kysely11 = Kysely.objects.get(nimi_fi="testikysely11")
    kyselykerta11 = Kyselykerta.objects.create(
        kyselyid=kysely11, nimi="testikyselykerta11", lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)

    Vastaajatunnus.objects.create(
        kyselykertaid=kyselykerta11, tunnus="testivastaajatunnus11",
        kohteiden_lkm=10, lukittu=False, **voimassa_kwargs, **kayttaja_kwargs)


def load_testing_data():
    add_test_kayttajat()
    add_test_kyselyt()
    add_test_kysymysryhmat_kysymykset_kyselykysymysryhmat()
    add_test_kyselykerrat_vastaajatunnukset()


def add_testing_responses_virkailijapalvelu_token(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/token/",
        json={"access": "test-token"}, status=200)


def add_testing_responses_virkailijapalvelu_tyontekija_OK(responses_obj):
    vastaajatunnus_list = [
        "testivastaajatunnus1_1",
        "testivastaajatunnus7_1",
        "testivastaajatunnus4_1",
        "testivastaajatunnus11"]

    for vt in vastaajatunnus_list:
        responses_obj.add(
            responses_obj.GET, f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/tyontekija/{vt}/",
            json={"data": "test-data"}, status=200)


def add_testing_responses_viestintapalvelu(responses_obj):
    responses_obj.add(
        responses_obj.POST, f"{settings.VIESTINTAPALVELU_URL}/api/v1/token/",
        json={"access": "test-token"}, status=200)

    responses_obj.add(
        responses_obj.POST, f"{settings.VIESTINTAPALVELU_URL}/api/v1/pdfsend/", status=200)


def add_testing_responses_virkailijapalvelu_tyontekija_info(responses_obj):
    # for tyontekija info tests
    responses_obj.add(
        responses_obj.GET, f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/tyontekija/testivastaajatunnus1_7/",
        json={
            "tehtavanimikkeet": [
                {"tehtavanimike_koodi": "0001", "kelpoisuus_kytkin": True}],
            "tutkinnot": ["0002"]}, status=200)


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

    # matrix sliderscale
    scales = get_scales()
    scale_names = [scale["name"] for scale in scales]
    for i, scale_name in enumerate(scale_names):
        jarjestys = 6 + i
        Kysymys.objects.create(
            kysymys_fi=f"html_test_kysymys_s{i}0", kysymys_sv=f"html_test_kysymys_s{i}0_sv", **kysymys_kwargs,
            vastaustyyppi="matrix_root",
            jarjestys=jarjestys, matriisi_jarjestys=0,
            metatiedot={
                "type": "matrix_sliderscale",
                "description": {"fi": f"html_test_description_s{i}0", "sv": f"html_test_description_s{i}0_sv"}})
        for j in range(1, 3):
            Kysymys.objects.create(
                kysymys_fi=f"html_test_kysymys_s{i}{j}", kysymys_sv=f"html_test_kysymys_s{i}{j}_sv", **kysymys_kwargs,
                vastaustyyppi=scale_name,
                jarjestys=jarjestys, matriisi_jarjestys=j,
                metatiedot={
                    "type": "matrix_sliderscale",
                    "description": {"fi": f"html_test_description_s{i}{j}", "sv": f"html_test_description_s{i}{j}_sv"}})

    # matrix radiobutton
    for i, scale_name in enumerate(scale_names):
        jarjestys = 6 + len(scale_names) + i
        Kysymys.objects.create(
            kysymys_fi=f"html_test_kysymys_r{i}0", kysymys_sv=f"html_test_kysymys_r{i}0_sv", **kysymys_kwargs,
            vastaustyyppi="matrix_root",
            jarjestys=jarjestys, matriisi_jarjestys=0,
            metatiedot={
                "type": "matrix_radiobutton",
                "description": {"fi": f"html_test_description_r{i}0", "sv": f"html_test_description_r{i}0_sv"}})
        for j in range(1, 3):
            Kysymys.objects.create(
                kysymys_fi=f"html_test_kysymys_r{i}{j}", kysymys_sv=f"html_test_kysymys_r{i}{j}_sv", **kysymys_kwargs,
                vastaustyyppi=scale_name,
                jarjestys=jarjestys, matriisi_jarjestys=j,
                metatiedot={
                    "type": "matrix_radiobutton",
                    "description": {"fi": f"html_test_description_r{i}{j}", "sv": f"html_test_description_r{i}{j}_sv"}})


def add_test_vastaaja_for_html_test():
    kyselykerta = Kyselykerta.objects.get(nimi="html_test_kyselykerta")
    vastaaja = Vastaaja.objects.create(
        kyselykertaid=kyselykerta.kyselykertaid,
        kyselyid=kyselykerta.kyselyid.kyselyid,
        vastaajatunnus="vtt001")

    # add answers
    Vastaus.objects.create(  # textfield (tekstikenttä)
        kysymysid=Kysymys.objects.get(kysymys_fi="html_test_kysymys_1").kysymysid,
        vastaajaid=vastaaja, string="vastaus_1")
    Vastaus.objects.create(  # multiline textfield (monirivinen tekstikenttä)
        kysymysid=Kysymys.objects.get(kysymys_fi="html_test_kysymys_2").kysymysid,
        vastaajaid=vastaaja, string="vastaus_2")
    Vastaus.objects.create(  # numeric textfield (numerokenttä)
        kysymysid=Kysymys.objects.get(kysymys_fi="html_test_kysymys_3").kysymysid,
        vastaajaid=vastaaja, string="3.0")
    Vastaus.objects.create(  # multi-option field, 1-choose
        kysymysid=Kysymys.objects.get(kysymys_fi="html_test_kysymys_4").kysymysid,
        vastaajaid=vastaaja, numerovalinta=1)
    Vastaus.objects.create(  # multi-option field, multi-choose
        kysymysid=Kysymys.objects.get(kysymys_fi="html_test_kysymys_5").kysymysid,
        vastaajaid=vastaaja, numerovalinta=1)
    Vastaus.objects.create(
        kysymysid=Kysymys.objects.get(kysymys_fi="html_test_kysymys_5").kysymysid,
        vastaajaid=vastaaja, numerovalinta=2)
    scale_count = len(get_scales())
    for i in range(scale_count):
        for j in range(3):
            Vastaus.objects.create(  # matrix sliderscale
                kysymysid=Kysymys.objects.get(kysymys_fi=f"html_test_kysymys_s{i}{j}").kysymysid,
                vastaajaid=vastaaja, numerovalinta=1)
            Vastaus.objects.create(  # matrix radiobutton
                kysymysid=Kysymys.objects.get(kysymys_fi=f"html_test_kysymys_r{i}{j}").kysymysid,
                vastaajaid=vastaaja, numerovalinta=1)


def add_test_duplicate_vastaajas():
    add_test_kayttajat()
    add_test_kyselyt()
    add_test_kyselykerrat_vastaajatunnukset()

    # Create duplicate Vastaajas with single use vastaajatunnus
    vastaajatunnus = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus2_1")
    for i in range(3):
        vastaaja = Vastaaja.objects.create(
            kyselykertaid=vastaajatunnus.kyselykertaid.pk,
            kyselyid=vastaajatunnus.kyselykertaid.kyselyid.pk,
            vastaajatunnus=vastaajatunnus.tunnus,
        )
        for j in range(1, 5):
            Vastaus.objects.create(
                kysymysid=j,
                vastaajaid=vastaaja,
                numerovalinta=1,
            )

    # Create duplicate Vastaajas with multi use vastaajatunnus
    vastaajatunnus = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus1_1")
    for i in range(3):
        vastaaja = Vastaaja.objects.create(
            kyselykertaid=vastaajatunnus.kyselykertaid.pk,
            kyselyid=vastaajatunnus.kyselykertaid.kyselyid.pk,
            vastaajatunnus=vastaajatunnus.tunnus,
        )
        for j in range(1, 5):
            Vastaus.objects.create(
                kysymysid=j,
                vastaajaid=vastaaja,
                numerovalinta=1,
            )

    # Create single Vastaaja with single use vastaajatunnus
    vastaajatunnus = Vastaajatunnus.objects.get(tunnus="testivastaajatunnus3_1")
    vastaaja = Vastaaja.objects.create(
        kyselykertaid=vastaajatunnus.kyselykertaid.pk,
        kyselyid=vastaajatunnus.kyselykertaid.kyselyid.pk,
        vastaajatunnus=vastaajatunnus.tunnus,
    )
    for j in range(1, 5):
        Vastaus.objects.create(
            kysymysid=j,
            vastaajaid=vastaaja,
            numerovalinta=1,
        )


def add_testing_responses_virkailijapalvelu_scale(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/scale/",
        json=[{"name": "asteikko1"}], status=200)


def add_testing_responses_virkailijapalvelu_scale_fail(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/scale/",
        status=500)


def add_testing_responses_virkailijapalvelu_scales(responses_obj):
    responses_obj.add(
        responses_obj.GET, f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/scale/",
        json=get_scales(), status=200)


def get_scales():
    return TEST_SCALES


def add_test_data_for_html_test():
    add_test_kyselykerta_for_html_test()
    add_test_vastaaja_for_html_test()
