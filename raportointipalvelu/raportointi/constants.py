from rest_framework import status


VALSSI_VERSION = "4.0.0"

TINY_VALUE = 1e-10  # small positive value for 'rounding up exact half value'

VALSSI_YLLAPITAJA_LEVEL = "YLLAPITAJA"
VALSSI_PAAKAYTTAJA_LEVEL = "PAAKAYTTAJA"
VALSSI_TOTEUTTAJA_LEVEL = "TOTEUTTAJA"

VALSSI_YLLAPITAJA_ORGANIZATION_OIDS = [
    "1.2.246.562.10.00000000001",  # Opetushallitus oid
    "1.2.246.562.10.12218193316",  # Karvi oid
]

OPETUSHALLITUS_OID = "1.2.246.562.10.00000000001"

VALSSI_PERMISSION_LEVELS = [VALSSI_YLLAPITAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL]

MANDATORY_LANGUAGE_CODES = ["fi", "sv"]
ALLOWED_LANGUAGE_CODES = ["fi", "sv", "en"]
LIMITED_LANGUAGE_CODES = ["fi", "sv"]

# report filter codes
REPORT_FILTER_LANGUAGE_CODES = dict(
    fi="FI",
    sv="SV",
    en="EN",
    other="XX",
    all=["FI", "SV", "EN", "XX"],
)

OPINTOPOLKU_HEADERS = {"Caller-Id": "csc.valssi", "CSRF": "csc.valssi", "Cookie": "CSRF=csc.valssi"}

USER_PERMISSIONS_RECHECK_TIME = 30  # minutes

SUCCESS_STATUSES = [status.HTTP_200_OK, status.HTTP_201_CREATED]

DATE_INPUT_FORMAT = "%Y-%m-%d"

REPORT_MIN_ANSWERS = 5
REPORT_MATRIX_MAX_SVG_QUESTIONS = 8
REPORT_MONIVALINTA_MAX_SVG_QUESTIONS = 8

MATRIX_ROOT_TYPE = "matrix_root"
MONIVALINTA_QUESTION_TYPE = "monivalinta"
TEXT_QUESTION_TYPE = "string"

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
    "vastuut",
]

MATRIX_GRAPH_COLORS = {
    6: ["rgba(239, 159, 60, 1)", "rgba(249, 217, 177, 1)", "rgba(13, 147, 210, 1)",
        "rgba(158, 212, 237, 1)", "rgba(206, 232, 230, 1)", "rgba(133, 197, 152, 1)"],
    5: ["rgba(239, 159, 60, 1)", "rgba(249, 217, 177, 1)", "rgba(13, 147, 210, 1)",
        "rgba(206, 232, 230, 1)", "rgba(133, 197, 152, 1)"],
    4: ["rgba(239, 159, 60, 1)", "rgba(249, 217, 177, 1)", "rgba(206, 232, 230, 1)",
        "rgba(133, 197, 152, 1)"],
    3: ["rgba(239, 159, 60, 1)", "rgba(13, 147, 210, 1)", "rgba(133, 197, 152, 1)"],
    2: ["rgba(239, 159, 60, 1)", "rgba(133, 197, 152, 1)"],
}

MONIVALINTA_GRAPH_COLOR = "rgba(133, 197, 152, 1)"

DEFAULT_BLACK_COLOR = "rgb(0,0,0)"
DEFAULT_WHITE_COLOR = "rgb(255,255,255)"

DEFAULT_FONT = "lato"
PLOTLY_FONT_SIZE = 12

DEFAULT_BLACK_FONT = dict(family=DEFAULT_FONT, size=PLOTLY_FONT_SIZE, color=DEFAULT_BLACK_COLOR)

MATRIX_LEGEND_X_POSITIONS = {2: 0.2, 3: 0.2, 4: 0.15, 5: -0.1, 6: -0.25}
MATRIX_LEGEND_Y_POSITIONS_BY_HEIGHT = [
    dict(min_height=500, y=-0.1),
    dict(min_height=450, y=-0.15),
    dict(min_height=400, y=-0.2),
    dict(min_height=350, y=-0.25),
    dict(min_height=300, y=-0.3),
    dict(min_height=0, y=-0.35),
]

PLOT_TRANSLATIONS = dict(
    percentage_title=dict(fi="Osuus vastaajista (%)", sv="Andel svar (%)"),
    average_title=dict(fi="Ka", sv="MV"),
    answers_not_available_text=dict(
        fi=f"Vastauksia vähemmän kuin {REPORT_MIN_ANSWERS}, tuloksia ei voida näyttää",
        sv=f"Färre än {REPORT_MIN_ANSWERS} svar, resultaten kan inte visas",
    ),
)

PDF_INDICATOR_INFO_TRANSLATIONS = dict(
    fi="Tällä työkalulla arvioidaan seuraavien laatuindikaattorien toteutumista:",
    sv="Med det här verktyget utvärderar vi förverkligandet av följande kvalitetsindikatorer:",
)

PDF_INDICATORS_NO_INDICATORS = ["palautekysely"]
PDF_NO_INDICATORS_TRANSLATIONS = dict(fi="Ei indikaattoria", sv="Ingen indikator")

PDF_ANSWERS_HIDDEN_TEXT = dict(fi="Vastaukset piilotettu", sv="Svar dolda")

PDF_TRANSLATION_MISSING_TEXT = "NULL"

REPORT_PLOT_MIN_WIDTH = 2

SUMMARY_TRANSLATIONS = dict(
    koulutustoimija=dict(fi="Toimijan nimi", sv="Aktörens namn"),
    alkupvm=dict(fi="Alkamispäivämäärä", sv="Startdatum"),
    summary_title=dict(fi="Yhteenveto", sv="Sammanfattning"),
    result_title=dict(fi="Arviointitulokset", sv="Utvärderingsresultat"),
    kuvaus=dict(
        fi="Lyhyt kuvaus arvioinnin toteuttamisesta",
        sv="En kort beskrivning av genomförandet av utvärderingen",
    ),
    aineisto=dict(
        fi="Arvioinnissa hyödynnetty aineisto",
        sv="Material som användes vid utvärderingen",
    ),
    vahvuudet=dict(
        fi="Arvioinnin keskeiset tulokset (vahvuudet)",
        sv="De centrala resultaten av utvärderingen (styrkor)",
    ),
    kohteet=dict(
        fi="Arvioinnin keskeiset tulokset (kehittämiskohteet)",
        sv="De centrala resultaten av utvärderingen (utvecklingsområden)",
    ),
    keh_toimenpiteet=dict(
        fi="Kehittämissuunnitelma ja toimenpiteet",
        sv="En plan för förbättring och åtgärder",
    ),
    seur_toimenpiteet=dict(
        fi="Kehittämistoimenpiteiden seurantasuunnitelma",
        sv="En plan för att följa upp genomförandet av förbättringsåtgärderna",
    ),
)

SUMMARY_FIELDS = ["group_info", "kuvaus", "aineisto", "vahvuudet", "kohteet", "keh_toimenpiteet", "seur_toimenpiteet"]

PDF_LOGO_PATHS = dict(
    fi="raportointi/css/karvi_logo_fi.png",
    sv="raportointi/css/karvi_logo_sv.png",
)

PAAKAYTTAJA_LOMAKE_TYPES = [
    "asiantuntijalomake_paakayttaja_prosessitekijat",       # type 1
    "asiantuntijalomake_paakayttaja_rakennetekijat",        # type 62
    "asiantuntijalomake_palaute",                           # type 62P
    "asiantuntijalomake_kansallinen",                       # type 62K
    "taydennyskoulutuslomake_paakayttaja_rakennetekijat",   # type 92
]

ASIANTUNTIJA_LOMAKE_TYPES = [
    "asiantuntijalomake_paakayttaja_prosessitekijat",       # type 1
    # "asiantuntijalomake_paivakoti_prosessitekijat",         # type 2
    "asiantuntijalomake_paivakoti_rakennetekijat",          # type 61
    "asiantuntijalomake_paivakoti_kansallinen",             # type 61K
    "asiantuntijalomake_paakayttaja_rakennetekijat",        # type 62
    "asiantuntijalomake_palaute",                           # type 62P
    "asiantuntijalomake_kansallinen",                       # type 62K
    "taydennyskoulutuslomake_paakayttaja_rakennetekijat",   # type 92
]

CSV_DELIMITER = ";"
REPORT_VALUE_DEFAULT = "999"
REPORT_VALUE_NULL = "NULL"
REPORT_VALUE_HIDDEN = "HIDDEN"
REPORT_VALUE_TRUE = "TRUE"
REPORT_VALUE_FALSE = "FALSE"

REPORT_EOS_VALUE_EKM = dict(fi="Ei koske minua", sv="Gäller inte mig")
REPORT_EOS_VALUE_EKR = dict(fi="Ei koske ryhmääni", sv="Gäller inte min grupp")
REPORT_EOS_VALUE_EOS = dict(fi="En osaa sanoa", sv="Jag kan inte säga")
REPORT_EOS_VALUE_DEFAULT = REPORT_EOS_VALUE_EOS
REPORT_EOS_VALUE_BY_SCALE = {
    "likert_asteikko": REPORT_EOS_VALUE_EKR,
    "likert_ekm": REPORT_EOS_VALUE_EKM,
    "likert_eos": REPORT_EOS_VALUE_EOS,
    "kylla_ei_valinta": REPORT_EOS_VALUE_EKR,
    "kylla_ei_valinta_eos": REPORT_EOS_VALUE_EOS,
    "kuinka_usein_6": REPORT_EOS_VALUE_EKR,
    "kuinka_usein_6_eos": REPORT_EOS_VALUE_EOS,
    "kuinka_usein_5": REPORT_EOS_VALUE_EKR,
    "kuinka_usein_5_eos": REPORT_EOS_VALUE_EOS,
    "olen_lukenut": REPORT_EOS_VALUE_EKR,
    "olen_lukenut_eos": REPORT_EOS_VALUE_EOS,
    "toteutuminen": REPORT_EOS_VALUE_EKR,
    "toteutuminen_eos": REPORT_EOS_VALUE_EOS,
    "toteutuminen_3": REPORT_EOS_VALUE_EKR,
    "toteutuminen_3_eos": REPORT_EOS_VALUE_EOS,
    "vastuut": REPORT_EOS_VALUE_EKR,
    "vastuut_eos": REPORT_EOS_VALUE_EOS,
    "toteutuu-asteikko": REPORT_EOS_VALUE_EKR,
    "toteutuu_ekm": REPORT_EOS_VALUE_EKM,
    "toteutuu_eos": REPORT_EOS_VALUE_EOS,
}
REPORT_CSV_SINGLELINE_TYPES = [
    "asiantuntijalomake_paakayttaja_prosessitekijat",       # type 1
    # "asiantuntijalomake_paivakoti_prosessitekijat",         # type 2
    "henkilostolomake_prosessitekijat",                     # type 3
    "henkilostolomake_palaute",                             # type 3P
    "henkilostolomake_kansallinen",                         # type 3K
    # "huoltajalomake_prosessitekijat",                       # type 4
    "asiantuntijalomake_paivakoti_rakennetekijat",          # type 61
    "asiantuntijalomake_paivakoti_kansallinen",             # type 61K
    "asiantuntijalomake_paakayttaja_rakennetekijat",        # type 62
    "asiantuntijalomake_palaute",                           # type 62P
    "asiantuntijalomake_kansallinen",                       # type 62K
    "henkilostolomake_rakennetekijat",                      # type 7
    # "huoltajalomake_rakennetekijat",                        # type 8
    "taydennyskoulutuslomake_rakennetekijat",               # type 91
    "taydennyskoulutuslomake_paakayttaja_rakennetekijat",   # type 92
]

# Pääkäyttäjä downloads csv:s
REPORT_CSV_COLS_TYPE_3 = [
    "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
    "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
    "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
    "aluejako", "toimintakieli",
    "tehtavanimike", "kelpoisuus",
]
REPORT_CSV_COLS_TYPE_61 = [
    "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
    "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
    "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
    "aluejako", "toimintakieli",
]
REPORT_CSV_COLS_TYPE_62 = [
    "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
    "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
    "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
]
REPORT_CSV_COLS = dict(
    # type 1
    asiantuntijalomake_paakayttaja_prosessitekijat=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
    ],
    # type 3
    henkilostolomake_prosessitekijat=REPORT_CSV_COLS_TYPE_3,
    # type 3P
    henkilostolomake_palaute=REPORT_CSV_COLS_TYPE_3,
    # type 3K
    henkilostolomake_kansallinen=REPORT_CSV_COLS_TYPE_3,
    # type 61
    asiantuntijalomake_paivakoti_rakennetekijat=REPORT_CSV_COLS_TYPE_61,
    # type 61K
    asiantuntijalomake_paivakoti_kansallinen=REPORT_CSV_COLS_TYPE_61,
    # type 62
    asiantuntijalomake_paakayttaja_rakennetekijat=REPORT_CSV_COLS_TYPE_62,
    # type 62P
    asiantuntijalomake_palaute=REPORT_CSV_COLS_TYPE_62,
    # type 62K
    asiantuntijalomake_kansallinen=REPORT_CSV_COLS_TYPE_62,
    # type 7
    henkilostolomake_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
        "aluejako", "toimintakieli",
        "tehtavanimike", "kelpoisuus",
    ],
    # type 91
    taydennyskoulutuslomake_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
        "koulutus_pv", "koulutus_tn", "koulutus_tn_pv",
    ],
    # type 92
    taydennyskoulutuslomake_paakayttaja_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
        "koulutus_pv", "koulutus_tn", "koulutus_tn_pv",
    ]
)

# Aineiston siirto csv:s
REPORT_CSV_COLS_SIIRTO_TYPE_3 = [
    "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
    "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
    "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
    "toimipaikka_postinumero", "toimipaikka_jarjmuoto", "toimipaikka_toimmuoto", "toimintakieli",
    "tehtavanimike", "kelpoisuus", "tutkinto"
]
REPORT_CSV_COLS_SIIRTO_TYPE_61 = [
    "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
    "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
    "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
    "toimipaikka_postinumero", "toimipaikka_jarjmuoto", "toimipaikka_toimmuoto", "toimintakieli"
]
REPORT_CSV_COLS_SIIRTO_TYPE_62 = [
    "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
    "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
    "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot"
]
REPORT_CSV_COLS_SIIRTO = dict(
    # type 1
    asiantuntijalomake_paakayttaja_prosessitekijat=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot"
    ],
    # type 3
    henkilostolomake_prosessitekijat=REPORT_CSV_COLS_SIIRTO_TYPE_3,
    # type 3P
    henkilostolomake_palaute=REPORT_CSV_COLS_SIIRTO_TYPE_3,
    # type 3K
    henkilostolomake_kansallinen=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
        "toimipaikka_oid", "toimipaikka_nimi",
        "toimipaikka_postinumero", "toimipaikka_jarjmuoto", "toimipaikka_toimmuoto", "toimintakieli",
        "tehtavanimike", "kelpoisuus", "tutkinto"
    ],
    # type 61
    asiantuntijalomake_paivakoti_rakennetekijat=REPORT_CSV_COLS_SIIRTO_TYPE_61,
    # type 61K
    asiantuntijalomake_paivakoti_kansallinen=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
        "toimipaikka_oid", "toimipaikka_nimi",
        "toimipaikka_postinumero", "toimipaikka_jarjmuoto", "toimipaikka_toimmuoto", "toimintakieli"
    ],
    # type 62
    asiantuntijalomake_paakayttaja_rakennetekijat=REPORT_CSV_COLS_SIIRTO_TYPE_62,
    # type 62P
    asiantuntijalomake_palaute=REPORT_CSV_COLS_SIIRTO_TYPE_62,
    # type 62K
    asiantuntijalomake_kansallinen=REPORT_CSV_COLS_SIIRTO_TYPE_62,
    # type 7
    henkilostolomake_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
        "toimipaikka_postinumero", "toimipaikka_jarjmuoto", "toimipaikka_toimmuoto", "toimintakieli",
        "tehtavanimike", "kelpoisuus", "tutkinto"
    ],
    # type 91
    taydennyskoulutuslomake_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
        "koulutus_pv", "koulutus_tn", "koulutus_tn_pv"
    ],
    # type 92
    taydennyskoulutuslomake_paakayttaja_rakennetekijat=[
        "vastaajaid", "lomake_nimi", "indikaattori", "alkamispaiva", "paattymispaiva",
        "organisaatio_nimi", "organisaatio_oid", "kuntakoodi", "yritysmuoto",
        "toimintamuodot", "henkilosto_total", "henkilosto_tn", "henkilosto_kelp", "lapset_voimassa", "tuen_tiedot",
        "koulutus_pv", "koulutus_tn", "koulutus_tn_pv"
    ]
)

REPORT_CSV_COL_NAMES = dict(
    vastaajaid=dict(fi="Vastaaja-id", sv="Respondent-id"),
    lomake_nimi=dict(fi="Lomakkeen nimi", sv="Blankettens namn"),
    alkamispaiva=dict(fi="Alkamispäivämäärä", sv="Startdatum"),
    paattymispaiva=dict(fi="Päättymispäivämäärä", sv="Slutdatum"),
    organisaatio_nimi=dict(fi="Toimijan nimi", sv="Aktörens namn"),
    organisaatio_oid=dict(fi="Organisaatio-OID", sv="Organisations-OID"),
    kuntakoodi=dict(fi="Kuntakoodi", sv="Kommunkod"),
    tehtavanimike=dict(fi="Tehtävänimikkeet", sv="Yrkesbenämningar"),
    kelpoisuus=dict(fi="Kelpoisuus", sv="Behörighet"),
    tutkinto=dict(fi="Tutkinto", sv="SV Tutkinto"),
    yritysmuoto=dict(fi="Yritysmuoto", sv="Företagsform"),
    indikaattori=dict(fi="Indikaattorit", sv="Indikatorer"),
    toimintakieli=dict(fi="Toimintakieli", sv="Verksamhetsspråk"),
    aluejako=dict(fi="Alue", sv="Området"),
    toimipaikka_oid=dict(fi="Toimipaikan OID", sv="SV Toimipaikan OID"),
    toimipaikka_nimi=dict(fi="Toimipaikan nimi", sv="SV Toimipaikan nimi"),
    toimipaikka_postinumero=dict(fi="Toimipaikan postinumero", sv="SV Toimipaikan postinumero"),
    toimipaikka_jarjmuoto=dict(fi="Toimipaikan järjestämismuoto", sv="SV Toimipaikan järjestämismuoto"),
    toimipaikka_toimmuoto=dict(fi="Toimipaikan toimintamuoto", sv="SV Toimipaikan toimintamuoto"),
    toimintamuodot=dict(
        fi="Toimipaikkojen lukumäärät toiminta- ja järjestämismuodoittain",
        sv="Antalet verksamhetsställen enligt verksamhets- och anordningsform",
    ),
    henkilosto_total=dict(
        fi="Henkilöstön kokonaislukumäärä",
        sv="Det totala antalet anställda",
    ),
    henkilosto_tn=dict(
        fi="Henkilöstön lukumäärä tehtävänimikkeittäin",
        sv="Antal anställda enligt yrkesbenämning",
    ),
    henkilosto_kelp=dict(
        fi="Kelpoisen henkilöstön määrä tehtävänimikkeittäin",
        sv="Antalet behöriga anställda enligt yrkesbenämning",
    ),
    lapset_voimassa=dict(
        fi="Varhaiskasvatuksessa olevien lasten määrä",
        sv="Antal barn inom småbarnspedagogiken",
    ),
    tuen_tiedot=dict(
        fi="Tuen tiedot",
        sv="Uppgifter om stöd",
    ),
    koulutus_pv=dict(
        fi="Koulutuspäivien kokonaismäärä",
        sv="SV Koulutuspäivien kokonaismäärä",
    ),
    koulutus_tn=dict(
        fi="Koulutuspäivien määrä tehtävänimikkeittäin",
        sv="SV Koulutuspäivien määrä tehtävänimikkeittäin",
    ),
    koulutus_tn_pv=dict(
        fi="Täydennyskoulutuksessa olleiden työntekijöiden määrä keskimäärin tehtävänimikkeittäin",
        sv="SV Täydennyskoulutuksessa olleiden työntekijöiden määrä keskimäärin tehtävänimikkeittäin",
    ),
)

REPORT_TRANSLATIONS = dict(
    report_percentage_title=dict(
        fi="Vastaajien määrä:",
        sv="Antal respondenter:",
    ),
    report_oppilaitos_answered_title=dict(
        fi="Toimipaikkojen määrä:",
        sv="Antal verksamhetsställen:",
    ),
    data_collection_title=dict(
        fi="Tiedonkeruun ajankohta:",
        sv="Tidsperiod för datainsamling:",
    ),
    report_link=dict(
        fi="https://wiki.eduuni.fi/pages/viewpage.action?"
           "pageId=249542063#Valssink%C3%A4ytt%C3%B6ohjeet-Raportintulkinta",
        sv="https://wiki.eduuni.fi/pages/viewpage.action?"
           "pageId=348984426#Bruksanvisningf%C3%B6rValssi-Tolkningavrapporten",
    ),
    report_link_text=dict(
        fi="Raportin tulkinta",
        sv="Tolkning av rapporten",
    ),
    report_filter_title=dict(
        fi="Raportin suodatus",
        sv="Rapportfiltrering",
    ),
    report_filter_jobtitle=dict(
        fi="Vastaajan tehtävänimike",
        sv="Respondentens tjänstetitel",
    ),
    report_filter_eligibility=dict(
        fi="Kelpoisuus tehtävään",
        sv="Behörighet för uppgiften",
    ),
    report_filter_language=dict(
        fi="Toimintakieli",
        sv="Verksamhetsspråk",
    ),
    report_filter_alue=dict(
        fi="Alue",
        sv="Området",
    ),
    report_filter_no_choice=dict(
        fi="Ei valintaa",
        sv="Inget val",
    ),
    report_filter_yes_choice=dict(
        fi="Kyllä",
        sv="Ja",
    ),
    report_answer_count_text=dict(
        fi="valittujen vastausten lukumäärä:",
        sv="antal utvalda svar:",
    ),
)

HTML_ESCAPE_REPLACES = [
    (">", "&gt;"),
    ("<", "&lt;"),
]

# loop configs
MAX_NO_OF_LOOPS = 3

LAATUTEKIJA_PROSESSI = "prosessi"
LAATUTEKIJA_RAKENNE = "rakenne"
LAATUTEKIJA_KANSALLINEN = "kansallinen"
LAATUTEKIJAS = [
    dict(laatutekija=LAATUTEKIJA_PROSESSI, group_ids=range(1000, 2000)),
    dict(laatutekija=LAATUTEKIJA_RAKENNE, group_ids=range(2000, 3000)),
    dict(laatutekija=LAATUTEKIJA_KANSALLINEN, group_ids=range(3000, 4000)),
]

SKIPPED_TEXT = "Ohitettu/Ignorerad"

LOMAKE_USAGE_EXPORT_COLS = [
    "voimassa_pvm1",
    "voimassa_pvm2",
    "lomake_nimi",
    "yritysmuoto",
    "koulutustoimija_name",
    "kuntakoodi",
    "voimassa_loppupvm",
    "is_results_done",
    "is_lomake_sent",
]

LOMAKE_USAGE_EXPORT_COL_TRANSLATIONS = dict(
    voimassa_pvm1=dict(fi="Päivämäärävalinta 1", sv="SV Päivämäärävalinta 1",),
    voimassa_pvm2=dict(fi="Päivämäärävalinta 2", sv="SV Päivämäärävalinta 2",),
    lomake_nimi=dict(fi="Lomakkeen nimi", sv="Blankettens namn",),
    yritysmuoto=dict(fi="Yritysmuoto", sv="Företagsform",),
    koulutustoimija_name=dict(fi="Toimijan nimi", sv="Aktörens namn",),
    kuntakoodi=dict(fi="Kuntakoodi", sv="Kommunkod"),
    voimassa_loppupvm=dict(fi="Päättymispäivämäärä", sv="Slutdatum",),
    is_results_done=dict(fi="Arviointitulokset tehty", sv="SV Arviointitulokset tehty",),
    is_lomake_sent=dict(fi="Lomaketta lähetetty", sv="SV Lomaketta lähetetty",),
)
