from django.conf import settings
from rest_framework import status


VALSSI_VERSION = "4.0.0"

MANDATORY_LANGUAGE_CODES = ["fi", "sv"]
ALLOWED_LANGUAGE_CODES = ["fi", "sv", "en"]

NUMEROVALINTA_ANSWER_TYPES = [
    "monivalinta",
    "likert_asteikko",
    "likert_ekm",
    "likert_eos",
    "kylla_ei_valinta",
    "kylla_ei_valinta_eos",
    "kuinka_usein_6",
    "kuinka_usein_6_eos",
    "kuinka_usein_5",
    "kuinka_usein_5_eos",
    "olen_lukenut",
    "olen_lukenut_eos",
    "toteutuminen",
    "toteutuminen_eos",
    "toteutuminen_3",
    "toteutuminen_3_eos",
    "vastuut",
    "vastuut_eos",
    "toteutuu-asteikko",
    "toteutuu_ekm",
    "toteutuu_eos",
]

VAPAATEKSTI_ANSWER_TYPES = ["string", ]

ALL_ANSWER_TYPES = NUMEROVALINTA_ANSWER_TYPES + VAPAATEKSTI_ANSWER_TYPES

NUMEROVALINTA_TYPES_AND_LIMITS = [
    {"vastaustyyppi": "likert_asteikko", "lower": 1, "upper": 5},
    {"vastaustyyppi": "likert_ekm", "lower": 1, "upper": 5},
    {"vastaustyyppi": "likert_eos", "lower": 1, "upper": 5},
    {"vastaustyyppi": "kylla_ei_valinta", "lower": 1, "upper": 2},
    {"vastaustyyppi": "kylla_ei_valinta_eos", "lower": 1, "upper": 2},
    {"vastaustyyppi": "kuinka_usein_6", "lower": 1, "upper": 6},
    {"vastaustyyppi": "kuinka_usein_6_eos", "lower": 1, "upper": 6},
    {"vastaustyyppi": "kuinka_usein_5", "lower": 1, "upper": 5},
    {"vastaustyyppi": "kuinka_usein_5_eos", "lower": 1, "upper": 5},
    {"vastaustyyppi": "olen_lukenut", "lower": 1, "upper": 3},
    {"vastaustyyppi": "olen_lukenut_eos", "lower": 1, "upper": 3},
    {"vastaustyyppi": "toteutuminen", "lower": 1, "upper": 4},
    {"vastaustyyppi": "toteutuminen_eos", "lower": 1, "upper": 4},
    {"vastaustyyppi": "toteutuminen_3", "lower": 1, "upper": 3},
    {"vastaustyyppi": "toteutuminen_3_eos", "lower": 1, "upper": 3},
    {"vastaustyyppi": "vastuut", "lower": 1, "upper": 3},
    {"vastaustyyppi": "vastuut_eos", "lower": 1, "upper": 3},
    {"vastaustyyppi": "toteutuu-asteikko", "lower": 1, "upper": 5},
    {"vastaustyyppi": "toteutuu_ekm", "lower": 1, "upper": 5},
    {"vastaustyyppi": "toteutuu_eos", "lower": 1, "upper": 5},
]

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
    "olen_lukenut": EOS_TRANSLATION_EKM,
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

PDF_FILENAME_SUFFIX = dict(fi="_vastaukset.pdf", sv="_svarar.pdf", en="_answers.pdf")

NO_ANSWER_LOCALE = dict(fi="Ei vastausta", sv="Inget svar", en="No answer")

VIRKAILIJAPALVELU_SETTINGS = dict(
    name="virkailijapalvelu",
    login_cred={
        "username": settings.VIRKAILIJAPALVELU_AUTH_USER,
        "password": settings.VIRKAILIJAPALVELU_AUTH_PW,
    },
    url=settings.VIRKAILIJAPALVELU_URL, timeout=settings.VIRKAILIJAPALVELU_TIMEOUT)
VIESTINTAPALVELU_SETTINGS = dict(
    name="viestintapalvelu",
    login_cred={
        "username": settings.VIESTINTAPALVELU_AUTH_USER,
        "password": settings.VIESTINTAPALVELU_AUTH_PW,
    },
    url=settings.VIESTINTAPALVELU_URL, timeout=settings.VIESTINTAPALVELU_TIMEOUT)

SUCCESS_STATUSES = (status.HTTP_200_OK, status.HTTP_201_CREATED)

PDF_INDICATOR_INFO_TRANSLATIONS = dict(
    fi="Tällä työkalulla arvioidaan seuraavan laatuindikaattorin toteutumista:",
    sv="Med det här verktyget utvärderar vi förverkligandet av följande kvalitetsindikator:",
    en="This tool is used to evaluate the implementation of the following quality indicators:",
)

PDF_INDICATORS_NO_INDICATORS = ["palautekysely"]
PDF_NO_INDICATORS_TRANSLATIONS = dict(fi="Ei indikaattoria", sv="Ingen indikator", en="No indicator")

PDF_LOGO_PATHS = dict(
    fi="kyselyt/css/karvi_logo_fi.png",
    sv="kyselyt/css/karvi_logo_sv.png",
    en="kyselyt/css/karvi_logo_en.png",
)

PDF_TRANSLATION_MISSING_TEXT = "NULL"

HTML_ESCAPE_REPLACES = [
    (">", "&gt;"),
    ("<", "&lt;"),
]

# loop configs
MAX_NO_OF_LOOPS = 3

DATE_INPUT_FORMAT = "%Y-%m-%d"

TYONTEKIJA_NOT_FOUND_ERROR_CODES = ["ER003", "ER004", "ER007", "ER008", "ER009"]
TYONTEKIJA_NOT_FOUND_STATUSES = [
    status.HTTP_404_NOT_FOUND,
    status.HTTP_500_INTERNAL_SERVER_ERROR,
]

UI_LOG_EPOCH_DIFF_LIMIT = 100  # seconds
UI_LOG_CHAR_LIMIT = 500
