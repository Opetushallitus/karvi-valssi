from string import ascii_letters, digits
from django.conf import settings
from rest_framework import status


VALSSI_VERSION = "4.0.0"

VALSSI_PAAKAYTTAJA_LEVEL = "PAAKAYTTAJA"
VALSSI_TOTEUTTAJA_LEVEL = "TOTEUTTAJA"
VALSSI_YLLAPITAJA_LEVEL = "YLLAPITAJA"

VALSSI_PERMISSION_LEVELS = [VALSSI_YLLAPITAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL]

VALSSI_YLLAPITAJA_ORGANIZATION_OIDS = [
    "1.2.246.562.10.00000000001",  # Opetushallitus oid
    "1.2.246.562.10.12218193316",  # Karvi oid
]

OPETUSHALLITUS_OID = "1.2.246.562.10.00000000001"

DEFAULT_ORGANIZATION_YTUNNUS = "0000000-0"
YRITYSMUOTO_KUNNALLINEN = [
    "41",  # Kunta
    "42",  # Kuntayhtymä
]
ALLOWED_TOIMINTAMUOTO_CODES = ["tm01", ]
ANONYMIZED_TOIMINTAMUOTO_CODES = ["tm02", "tm03"]

OPINTOPOLKU_HEADERS = {"Caller-Id": "csc.valssi", "CSRF": "csc.valssi", "Cookie": "CSRF=csc.valssi"}

USER_PERMISSIONS_RECHECK_TIME = 30  # minutes

VIESTINTAPALVELU_SETTINGS = dict(
    name="viestintapalvelu",
    login_cred={
        "username": settings.VIESTINTAPALVELU_AUTH_USER,
        "password": settings.VIESTINTAPALVELU_AUTH_PW,
    },
    url=settings.VIESTINTAPALVELU_URL,
    timeout=settings.VIESTINTAPALVELU_TIMEOUT
)

TEMPLATE_NO_ORIGINAL_SEND = 1
TEMPLATE_NO_REMINDER_SEND = 2

SUCCESS_STATUSES = [status.HTTP_200_OK, status.HTTP_201_CREATED]

DATE_INPUT_FORMAT = "%Y-%m-%d"

KYSELYSEND_MESSAGE_MAX_LENGTH = 5000

# Email message statuses
EMAIL_STATUS_SENT = "sent"
EMAIL_STATUS_DELIVERED = "delivered"
EMAIL_STATUS_FAILED = "failed"

SERVICE_USER_GROUP = "palvelukayttaja"
SERVICE_USER_ACTIONS = ["retrieve", ]

PDF_FILENAME_REPLACES = [("Å", "A"), ("Ä", "A"), ("Ö", "O"), ("å", "a"), ("ä", "a"), ("ö", "o")]
PDF_FILENAME_ALLOWED_CHARS = ascii_letters + digits + "_-. "
PDF_FILENAME_DEFAULT = "name_missing"

MANDATORY_LANGUAGE_CODES = ["fi", "sv"]
ALLOWED_LANGUAGE_CODES = ["fi", "sv", "en"]
LIMITED_LANGUAGE_CODES = ["fi", "sv"]

EOS_TRANSLATION_EKM = dict(fi="ei koske minua", sv="gäller inte mig", en="does not apply to me")
EOS_TRANSLATION_EKR = dict(fi="ei koske ryhmääni", sv="gäller inte min grupp", en="does not apply to my group")
EOS_TRANSLATION_EOS = dict(fi="en osaa sanoa", sv="jag kan inte säga", en="I can't say")
EOS_TRANSLATION_DEFAULT = EOS_TRANSLATION_EOS
EOS_TRANSLATIONS = {
    "likert_asteikko": EOS_TRANSLATION_EKR,
    "likert_ekm": EOS_TRANSLATION_EKM,
    "likert_eos": EOS_TRANSLATION_EOS,
    "kylla_ei_valinta": EOS_TRANSLATION_EKR,
    "kylla_ei_valinta_eos": EOS_TRANSLATION_EOS,
    "kuinka_usein_6": EOS_TRANSLATION_EKR,
    "kuinka_usein_6_eos": EOS_TRANSLATION_EOS,
    "kuinka_usein_5": EOS_TRANSLATION_EKR,
    "kuinka_usein_5_eos": EOS_TRANSLATION_EOS,
    "olen_lukenut": EOS_TRANSLATION_EKR,
    "olen_lukenut_eos": EOS_TRANSLATION_EOS,
    "toteutuminen": EOS_TRANSLATION_EKR,
    "toteutuminen_eos": EOS_TRANSLATION_EOS,
    "toteutuminen_3": EOS_TRANSLATION_EKR,
    "toteutuminen_3_eos": EOS_TRANSLATION_EOS,
    "vastuut": EOS_TRANSLATION_EKR,
    "vastuut_eos": EOS_TRANSLATION_EOS,
    "toteutuu-asteikko": EOS_TRANSLATION_EKR,
    "toteutuu_ekm": EOS_TRANSLATION_EKM,
    "toteutuu_eos": EOS_TRANSLATION_EOS,
}

# Vastaajatunnus taustatiedot inclusion settings
VASTAAJATUNNUS_TAUSTATIEDOT_SETTINGS = dict(
    # type 1
    asiantuntijalomake_paakayttaja_prosessitekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=False)),
    # type 2
    asiantuntijalomake_paivakoti_prosessitekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=False,
            toimipaikka_data=False)),
    # type 3
    henkilostolomake_prosessitekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=True)),
    # type 3P
    henkilostolomake_palaute=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=True)),
    # type 3K
    henkilostolomake_kansallinen=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=True)),
    # type 4
    huoltajalomake_prosessitekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=False,
            toimipaikka_data=True)),
    # type 61
    asiantuntijalomake_paivakoti_rakennetekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=True)),
    # type 61K
    asiantuntijalomake_paivakoti_kansallinen=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=True)),
    # type 62
    asiantuntijalomake_paakayttaja_rakennetekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=False)),
    # type 62P
    asiantuntijalomake_palaute=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=False)),
    # type 62K
    asiantuntijalomake_kansallinen=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=False)),
    # type 7
    henkilostolomake_rakennetekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=True)),
    # type 8
    huoltajalomake_rakennetekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=True)),
    # type 91
    taydennyskoulutuslomake_rakennetekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=False)),
    # type 92
    taydennyskoulutuslomake_paakayttaja_rakennetekijat=dict(
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            toimipaikka_data=False)))

PDF_INDICATOR_INFO_TRANSLATIONS = dict(
    fi="Tällä työkalulla arvioidaan seuraavien laatuindikaattorien toteutumista:",
    sv="Med det här verktyget utvärderar vi förverkligandet av följande kvalitetsindikatorer:",
    en="This tool is used to evaluate the implementation of the following quality indicators:",
)

PDF_INDICATORS_NO_INDICATORS = ["palautekysely"]
PDF_NO_INDICATORS_TRANSLATIONS = dict(
    fi="Ei indikaattoria",
    sv="Ingen indikator",
    en="No indicator",
)

PDF_LOGO_PATHS = dict(
    fi="kyselyt/css/karvi_logo_fi.png",
    sv="kyselyt/css/karvi_logo_sv.png",
    en="kyselyt/css/karvi_logo_en.png",
)

PDF_TRANSLATION_MISSING_TEXT = "NULL"

TILAENUM_PUBLISHED = "julkaistu"
TILAENUM_ARCHIVED = "arkistoitu"
TILAENUM_LOCKED = "lukittu"

HTML_ESCAPE_REPLACES = [
    (">", "&gt;"),
    ("<", "&lt;"),
]

VARDA_ORG_LAST_UPDATE_DEADLINE_FOR_ERROR = 24  # hours

# loop configs
MAX_NO_OF_LOOPS = 3

UI_LOG_CHAR_LIMIT = 500

MAX_ALUEJAKO_ALUE_COUNT = 20  # Per koulutustoimija
MIN_OPPILAITOS_COUNT_PER_ALUEJAKO_ALUE = 3
