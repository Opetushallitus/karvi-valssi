from rest_framework import status


VALSSI_VERSION = "1.1.3"

TINY_VALUE = 1e-10  # small positive value for 'rounding up exact half value'

VALSSI_YLLAPITAJA_LEVEL = "YLLAPITAJA"
VALSSI_PAAKAYTTAJA_LEVEL = "PAAKAYTTAJA"
VALSSI_TOTEUTTAJA_LEVEL = "TOTEUTTAJA"

VALSSI_YLLAPITAJA_ORGANIZATION_OIDS = [
    "1.2.246.562.10.00000000001",  # Opetushallitus oid
    "1.2.246.562.10.12218193316"]  # Karvi oid

OPETUSHALLITUS_OID = "1.2.246.562.10.00000000001"

VALSSI_PERMISSION_LEVELS = (VALSSI_YLLAPITAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL)

ALLOWED_LANGUAGE_CODES = ["fi", "sv"]

OPINTOPOLKU_HEADERS = {"Caller-Id": "csc.valssi", "CSRF": "csc.valssi", "Cookie": "CSRF=csc.valssi"}

USER_PERMISSIONS_RECHECK_TIME = 30  # minutes

SUCCESS_STATUSES = (status.HTTP_200_OK, status.HTTP_201_CREATED)

DATE_INPUT_FORMAT = "%Y-%m-%d"

REPORT_MIN_ANSWERS = 5

SURVEY_TYPE_ASIANTUNTIJALOMAKE = "asiantuntijalomake_paakayttaja_prosessitekijat"

MATRIX_ROOT_TYPE = "matrix_root"

MATRIX_QUESTION_TYPES = [
    "toteutuu-asteikko",
    "toteutuu_ekm",
    "kuinka_usein_6",
    "kuinka_usein_5",
    "kylla_ei_valinta",
    "olen_lukenut",
    "likert_asteikko",
    "likert_ekm",
    "toteutuminen",
    "toteutuminen_3",
    "vastuut"]

MATRIX_GRAPH_COLORS = {
    6: ["rgba(239, 159, 60, 1)", "rgba(249, 217, 177, 1)", "rgba(13, 147, 210, 1)", "rgba(158, 212, 237, 1)",
        "rgba(206, 232, 230, 1)", "rgba(133, 197, 152, 1)"],
    5: ["rgba(239, 159, 60, 1)", "rgba(249, 217, 177, 1)", "rgba(13, 147, 210, 1)", "rgba(206, 232, 230, 1)",
        "rgba(133, 197, 152, 1)"],
    4: ["rgba(239, 159, 60, 1)", "rgba(249, 217, 177, 1)", "rgba(206, 232, 230, 1)", "rgba(133, 197, 152, 1)"],
    3: ["rgba(239, 159, 60, 1)", "rgba(13, 147, 210, 1)", "rgba(133, 197, 152, 1)"],
    2: ["rgba(239, 159, 60, 1)", "rgba(133, 197, 152, 1)"]}

DEFAULT_FONT = "lato"

DEFAULT_BLACK_COLOR = "rgb(0,0,0)"
DEFAULT_WHITE_COLOR = "rgb(255,255,255)"

MATRIX_LEGEND_X_POSITIONS = {2: 0.2, 3: 0.2, 4: 0.15, 5: -0.1, 6: -0.25}
MATRIX_LEGEND_Y_POSITIONS_BY_HEIGHT = [
    dict(min_height=500, y=-0.1),
    dict(min_height=450, y=-0.15),
    dict(min_height=400, y=-0.2),
    dict(min_height=350, y=-0.25),
    dict(min_height=300, y=-0.3),
    dict(min_height=0, y=-0.35)]

PLOT_TRANSLATIONS = dict(
    fi=dict(percentage_title="Osuus vastaajista (%)",
            answers_not_available_text=f"Vastauksia vähemmän kuin {REPORT_MIN_ANSWERS}, tuloksia ei voida näyttää",
            average_title="Ka"),
    sv=dict(percentage_title="Andel svar (%)",
            answers_not_available_text=f"Färre än {REPORT_MIN_ANSWERS} svar, resultaten kan inte visas",
            average_title="MV"))

DATA_COLLECTION_TITLE = dict(
    fi="Tiedonkeruun ajankohta:",
    sv="Tidsperiod för datainsamling:")

MAIN_INDICATOR_TITLE = dict(
    fi="Pääindikaattori:",
    sv="Huvudindikator:")

SECONDARY_INDICATORS_TITLE = dict(
    fi="Arviointityökaluun liittyvät muut indikaattorit:",
    sv="Övriga indikatorer relaterade till utvärderingsverktyget:")

REPORT_PLOT_MIN_WIDTH = 2

SUMMARY_TRANSLATIONS = dict(
    summary_title=dict(fi="Yhteenveto", sv="Sammanfattning"),
    result_title=dict(fi="Arviointitulokset", sv="Utvärderingsresultat"),
    kuvaus=dict(
        fi="Lyhyt kuvaus arvioinnin toteuttamisesta",
        sv="En kort beskrivning av genomförandet av utvärderingen"),
    aineisto=dict(
        fi="Arvioinnissa hyödynnetty aineisto",
        sv="Material som användes vid utvärderingen"),
    vahvuudet=dict(
        fi="Arvioinnin keskeiset tulokset (vahvuudet)",
        sv="De centrala resultaten av utvärderingen (styrkor)"),
    kohteet=dict(
        fi="Arvioinnin keskeiset tulokset (kehittämiskohteet)",
        sv="De centrala resultaten av utvärderingen (utvecklingsområden)"),
    keh_toimenpiteet=dict(
        fi="Kehittämissuunnitelma ja toimenpiteet",
        sv="En plan för förbättring och åtgärder"),
    seur_toimenpiteet=dict(
        fi="Kehittämistoimenpiteiden seurantasuunnitelma",
        sv="En plan för att följa upp genomförandet av förbättringsåtgärderna"))

SUMMARY_FIELDS = ("group_info", "kuvaus", "aineisto", "vahvuudet", "kohteet", "keh_toimenpiteet", "seur_toimenpiteet")

PLOTLY_FONT_SIZE = 12

REPORT_LINK = dict(
    fi="https://wiki.eduuni.fi/pages/viewpage.action?pageId=249542063#Valssink%C3%A4ytt%C3%B6ohjeet-Raportintulkinta",
    sv="https://wiki.eduuni.fi/pages/viewpage.action?pageId=348984426#Bruksanvisningf%C3%B6rValssi-Tolkningavrapporten")

REPORT_LINK_TEXT = dict(
    fi="Raportin tulkinta",
    sv="Tolkning av rapporten")

PDF_LOGO_PATHS = dict(
    fi="raportointi/css/karvi_logo_fi.png",
    sv="raportointi/css/karvi_logo_sv.png")

CSV_DELIMITER = ";"
DEFAULT_REPORT_VALUE = "999"
REPORT_EOS_VALUE = "EKR"
REPORT_NULL_VALUE = "NULL"
REPORT_CSV_SINGLELINE_TYPES = [
    "henkilostolomake_prosessitekijat",                    # type 3
    "asiantuntijalomake_paakayttaja_rakennetekijat",       # type 6(2)
    "henkilostolomake_rakennetekijat",                     # type 7
    "taydennyskoulutuslomake_rakennetekijat",              # type 9(1)
    "taydennyskoulutuslomake_paakayttaja_rakennetekijat"]  # type 9(2)

REPORT_CSV_COLS = dict(
    # type 3
    henkilostolomake_prosessitekijat=[
        "vastaajaid", "lomake_nimi", "alkamispaiva", "paattymispaiva",
        "organisaatio_oid", "kuntakoodi",
        "tehtavanimike", "kelpoisuus"],
    # type 6(2)
    asiantuntijalomake_paakayttaja_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "alkamispaiva", "paattymispaiva",
        "organisaatio_oid", "kuntakoodi",
        "toimintamuodot",
        "henkilosto_total", "henkilosto_tn", "henkilosto_kelp",
        "lapset_voimassa"],
    # type 7
    henkilostolomake_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "alkamispaiva", "paattymispaiva",
        "organisaatio_oid", "kuntakoodi",
        "tehtavanimike", "kelpoisuus",
        "toimintamuodot",
        "henkilosto_total", "henkilosto_tn", "henkilosto_kelp",
        "lapset_voimassa"],
    # type 9(1)
    taydennyskoulutuslomake_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "alkamispaiva", "paattymispaiva",
        "organisaatio_oid", "kuntakoodi",
        "toimintamuodot",
        "henkilosto_total", "henkilosto_tn", "henkilosto_kelp",
        "lapset_voimassa",
        "koulutus_pv", "koulutus_tn", "koulutus_tn_pv"],
    # type 9(2)
    taydennyskoulutuslomake_paakayttaja_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "alkamispaiva", "paattymispaiva",
        "organisaatio_oid", "kuntakoodi",
        "toimintamuodot",
        "henkilosto_total", "henkilosto_tn", "henkilosto_kelp",
        "lapset_voimassa",
        "koulutus_pv", "koulutus_tn", "koulutus_tn_pv"])

REPORT_CSV_COL_NAMES = dict(
    vastaajaid=dict(fi="Vastaaja-id", sv="Vastaaja-id"),
    lomake_nimi=dict(fi="Lomakkeen nimi", sv="Lomakkeen nimi"),
    alkamispaiva=dict(fi="Alkamispäivämäärä", sv="Alkamispäivämäärä"),
    paattymispaiva=dict(fi="Päättymispäivämäärä", sv="Päättymispäivämäärä"),
    organisaatio_oid=dict(fi="Organisaatio-OID", sv="Organisaatio-OID"),
    kuntakoodi=dict(fi="Kuntakoodi", sv="Kuntakoodi"),
    tehtavanimike=dict(fi="Tehtävänimike", sv="Tehtävänimike"),
    kelpoisuus=dict(fi="Kelpoisuus", sv="Kelpoisuus"),
    toimintamuodot=dict(
        fi="Toimipaikkojen lukumäärät toiminta- ja järjestämismuodoittain",
        sv="Toimipaikkojen lukumäärät toiminta- ja järjestämismuodoittain"),
    henkilosto_total=dict(
        fi="Henkilöstön kokonaislukumäärä",
        sv="Henkilöstön kokonaislukumäärä"),
    henkilosto_tn=dict(
        fi="Henkilöstön lukumäärä tehtävänimikkeittäin",
        sv="Henkilöstön lukumäärä tehtävänimikkeittäin"),
    henkilosto_kelp=dict(
        fi="Kelpoisen henkilöstön määrä tehtävänimikkeittäin",
        sv="Kelpoisen henkilöstön määrä tehtävänimikkeittäin"),
    lapset_voimassa=dict(
        fi="Varhaiskasvatuksessa olevien lasten määrä",
        sv="Varhaiskasvatuksessa olevien lasten määrä"),
    koulutus_pv=dict(
        fi="Koulutuspäivien kokonaismäärä",
        sv="Koulutuspäivien kokonaismäärä"),
    koulutus_tn=dict(
        fi="Koulutuspäivien määrä tehtävänimikkeittäin",
        sv="Koulutuspäivien määrä tehtävänimikkeittäin"),
    koulutus_tn_pv=dict(
        fi="Täydennyskoulutuksessa olleiden työntekijöiden määrä keskimäärin tehtävänimikkeittäin",
        sv="Täydennyskoulutuksessa olleiden työntekijöiden määrä keskimäärin tehtävänimikkeittäin"))

REPORT_PERCENTAGE_TITLE = dict(
    fi="Vastaajien määrä:",
    sv="Antal respondenter:")

REPORT_PERCENTAGE_TITLE = dict(
    fi="Vastaajien määrä:",
    sv="Antal respondenter:")

HTML_ESCAPE_REPLACES = [
    (">", "&gt;"),
    ("<", "&lt;")]

# loop configs
MAX_NO_OF_LOOPS = 3
