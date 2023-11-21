import logging


logger = logging.getLogger(__name__)


def create_indicators():
    from kyselyt.models import Indikaattori

    indicators = [
        {"group_id": 1000, "key": "myonteinen_ja_sitoutunut_vuorovaik", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1000, "key": "sensitiivinen_vuorovaikutus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1000, "key": "yhdenvertainen_vuorovaikutus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1001, "key": "vastavuoroinen_vuorovaikutus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1001, "key": "kielellinen_vuorovaikutus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1002, "key": "pedagoginen_prosessi", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1002, "key": "toiminnan_havainnointi", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1003, "key": "monipuolinen_pedagoginen_toiminta", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1003, "key": "toiminnan_merkityksellisyys", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1003, "key": "lapsen_yksilollisyyden_huom", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1004, "key": "perustoiminnot_ja_ruokailu", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1004, "key": "paivittaiset_siirtymatilanteet", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1005, "key": "yksilollinen_tuki", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1006, "key": "oppimisymparisto", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1008, "key": "pedagogiikan_johtaminen", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1008, "key": "pedagoginen_vastuu", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1009, "key": "myonteinen_oppimisymparisto", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1009, "key": "yhteisollinen_oppiminen", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1009, "key": "yhteenkuuluvuus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1010, "key": "lapsen_kokemus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1011, "key": "moninaisuus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1012, "key": "moniammatillinen_vuorovaikutus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1012, "key": "yhteinen_ja_eriytynyt_ammat", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1012, "key": "monialainen_yhteistyo", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1013, "key": "kasvatusyhteistyo", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 1013, "key": "huoltajien_osallisuus", "laatutekija": "prosessi", "is_visible": True},
        {"group_id": 2000, "key": "lainsaadannon_kehittaminen", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2000, "key": "suhdelukua_koskeva_lainsaadanto", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2000, "key": "henkiloston_kelpoisuusvaatimukset", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2000, "key": "toimintamuoto_lainsaadanto", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2001, "key": "ohjausjarjestelma", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2001, "key": "kansalliset_linjaukset", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2001, "key": "inklusiivisten_saatavuus", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2001, "key": "paikalliset_linjaukset", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2001, "key": "henkiloston_riittavyys", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2001, "key": "yhdenvertainen_osallistuminen", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2002, "key": "kansallinen_opetussuunnitelma", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2002, "key": "paikallinen_ops_tyovalineena", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2002, "key": "paikallisen_opsn_arviointi", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2003, "key": "koulutuksen_kansalliset_linjaukset", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2003, "key": "paikallinen_taydennyskoulutus", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2004, "key": "palveluohjaus_ja_toimintamuodot", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2004, "key": "lasten_yhdenvertaisuus", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2005, "key": "kansallinen_ohjausjarjestelma", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2005, "key": "yksityisten_palveluiden_ohjaus", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2006, "key": "siirtymat_koulutus_kasvatus", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2006, "key": "siirtymat_varhaiskasvatuksessa", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2006, "key": "siirtyma_kotoa_varhaiskasvatukseen", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2006, "key": "siirtymien_suunnittelu_kaytannot", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2007, "key": "kansallinen_arviointijarjestelma", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2007, "key": "paikallinen_laadunhallinta", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2007, "key": "osallistava_arviointi_kehittaminen", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2008, "key": "johtamisjarjestelma_ja_rakenteet", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2008, "key": "tiedolla_johtaminen", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2009, "key": "henkilosto_taloudelliset_resurssit", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2009, "key": "henkilostorakenne_ja_maara", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2010, "key": "tyoaikarakenteiden_suunnittelu", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2010, "key": "osaamisen_hyodyntaminen", "laatutekija": "rakenne", "is_visible": True},
        {"group_id": 2011, "key": "lapsiryhman_rakenne_ja_koko", "laatutekija": "rakenne", "is_visible": True}
    ]

    created_count = 0
    updated_count = 0
    for ind in indicators:
        ind_values = dict(group_id=ind["group_id"], laatutekija=ind["laatutekija"], is_visible=ind["is_visible"])
        indikaattori_obj = Indikaattori.objects.filter(key=ind["key"])
        # create if key is missing, update if there is changes
        if not indikaattori_obj.exists():
            Indikaattori.objects.create(key=ind["key"], **ind_values)
            created_count += 1
        elif not indikaattori_obj.filter(**ind_values).exists():
            indikaattori_obj.update(**ind_values)
            updated_count += 1

    logger.info(f"Indicators created: {created_count}, updated: {updated_count}")


def create_scales():
    from kyselyt.models import Scale

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

    created_count = 0
    updated_count = 0
    for scale in scales:
        scale_values = dict(
            order_no=scale["order_no"], label_fi=scale["label"]["fi"], label_sv=scale["label"]["sv"],
            min_value=scale["min_value"], max_value=scale["max_value"], default_value=scale["default_value"],
            step_count=scale["step_count"], scale=scale["scale"], eos_value=scale["eos_value"])
        scale_obj = Scale.objects.filter(name=scale["name"])
        # create if name is missing, update if there is changes
        if not scale_obj.exists():
            Scale.objects.create(name=scale["name"], **scale_values)
            created_count += 1
        elif not scale_obj.filter(**scale_values).exists():
            scale_obj.update(**scale_values)
            updated_count += 1

    logger.info(f"Scales created: {created_count}, updated: {updated_count}")


def create_malfunction_messages():
    from kyselyt.models import MalfunctionMessage

    malfmessages = [
        # Virkailijapalvelu messages
        {"service": "virkailijapalvelu", "code": 1,
         "message": "Järjestelmässä on tilapäinen häiriö. / Det finns ett tillfälligt fel i systemet."},

        # Vastauspalvelu messages
        {"service": "vastauspalvelu", "code": 51,
         "message": "Järjestelmässä on tilapäinen häiriö. / Det finns ett tillfälligt fel i systemet."}
    ]

    created_count = 0
    updated_count = 0
    for malfmessage in malfmessages:
        obj = MalfunctionMessage.objects.filter(code=malfmessage["code"])
        # create if code is missing, update if there is changes
        if not obj.exists():
            MalfunctionMessage.objects.create(**malfmessage)
            created_count += 1
        elif not MalfunctionMessage.objects.filter(**malfmessage).exists():
            obj.update(**malfmessage)
            updated_count += 1

    logger.info(f"MalfunctionMessages created: {created_count}, updated: {updated_count}")
