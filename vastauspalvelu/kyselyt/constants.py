from django.conf import settings
from rest_framework import status


VALSSI_VERSION = "1.1.3"

ALLOWED_LANGUAGE_CODES = ["fi", "sv"]

NUMEROVALINTA_ANSWER_TYPES = ("monivalinta",
                              "arvosana",  # deprecated
                              "arvosana6",  # deprecated
                              "arvosana7",  # deprecated
                              "likert_asteikko",
                              "likert_ekm",
                              "kylla_ei_valinta",
                              "kuinka_usein_6",
                              "kuinka_usein_5",
                              "olen_lukenut",
                              "toteutuminen",
                              "toteutuminen_3",
                              "vastuut",
                              "toteutuu-asteikko",
                              "toteutuu_ekm")

VAPAATEKSTI_ANSWER_TYPES = ("string", )

ALL_ANSWER_TYPES = NUMEROVALINTA_ANSWER_TYPES + VAPAATEKSTI_ANSWER_TYPES

NUMEROVALINTA_TYPES_AND_LIMITS = [
    {"vastaustyyppi": "arvosana", "lower": 1, "upper": 5},  # deprecated
    {"vastaustyyppi": "arvosana6", "lower": 1, "upper": 6},  # deprecated
    {"vastaustyyppi": "arvosana7", "lower": 1, "upper": 7},  # deprecated
    {"vastaustyyppi": "likert_asteikko", "lower": 1, "upper": 5},
    {"vastaustyyppi": "likert_ekm", "lower": 1, "upper": 5},
    {"vastaustyyppi": "kylla_ei_valinta", "lower": 1, "upper": 2},
    {"vastaustyyppi": "kuinka_usein_6", "lower": 1, "upper": 6},
    {"vastaustyyppi": "kuinka_usein_5", "lower": 1, "upper": 5},
    {"vastaustyyppi": "olen_lukenut", "lower": 1, "upper": 3},
    {"vastaustyyppi": "toteutuminen", "lower": 1, "upper": 4},
    {"vastaustyyppi": "toteutuminen_3", "lower": 1, "upper": 3},
    {"vastaustyyppi": "vastuut", "lower": 1, "upper": 3},
    {"vastaustyyppi": "toteutuu-asteikko", "lower": 1, "upper": 5},
    {"vastaustyyppi": "toteutuu_ekm", "lower": 1, "upper": 5}]

EOS_TRANSLATIONS = {
    "default": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "likert_asteikko": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "likert_ekm": dict(fi="ei koske minua", sv="gäller inte mig"),
    "kylla_ei_valinta": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "kuinka_usein_6": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "kuinka_usein_5": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "olen_lukenut": dict(fi="ei koske minua", sv="gäller inte mig"),
    "toteutuminen": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "toteutuminen_3": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "vastuut": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "toteutuu-asteikko": dict(fi="ei koske ryhmääni", sv="gäller inte min grupp"),
    "toteutuu_ekm": dict(fi="ei koske minua", sv="gäller inte mig")}

PDF_FILENAME_SUFFIX = dict(fi="_vastaukset.pdf", sv="_svarar.pdf", en="_answers.pdf")

NO_ANSWER_LOCALE = dict(fi="Ei vastausta", sv="Inget svar", en="No answer")

VIRKAILIJAPALVELU_SETTINGS = dict(
    name="virkailijapalvelu",
    login_cred={"username": settings.VIRKAILIJAPALVELU_AUTH_USER, "password": settings.VIRKAILIJAPALVELU_AUTH_PW},
    url=settings.VIRKAILIJAPALVELU_URL, timeout=settings.VIRKAILIJAPALVELU_TIMEOUT)
VIESTINTAPALVELU_SETTINGS = dict(
    name="viestintapalvelu",
    login_cred={"username": settings.VIESTINTAPALVELU_AUTH_USER, "password": settings.VIESTINTAPALVELU_AUTH_PW},
    url=settings.VIESTINTAPALVELU_URL, timeout=settings.VIESTINTAPALVELU_TIMEOUT)

SUCCESS_STATUSES = (status.HTTP_200_OK, status.HTTP_201_CREATED)

PDF_INDICATOR_INFO_TRANSLATIONS = dict(
    fi="Tällä työkalulla arvioidaan seuraavan laatuindikaattorin toteutumista:",
    sv="Med det här verktyget utvärderar vi förverkligandet av följande kvalitetsindikator:")

PDF_LOGO_PATHS = dict(fi="kyselyt/css/karvi_logo_fi.png", sv="kyselyt/css/karvi_logo_sv.png")

HTML_ESCAPE_REPLACES = [
    (">", "&gt;"),
    ("<", "&lt;")]

# loop configs
MAX_NO_OF_LOOPS = 3
