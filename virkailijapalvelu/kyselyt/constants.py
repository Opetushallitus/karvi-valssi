from string import ascii_letters, digits
from django.conf import settings
from rest_framework import status


VALSSI_VERSION = "1.1.3"

VALSSI_PAAKAYTTAJA_LEVEL = "PAAKAYTTAJA"
VALSSI_TOTEUTTAJA_LEVEL = "TOTEUTTAJA"
VALSSI_YLLAPITAJA_LEVEL = "YLLAPITAJA"

VALSSI_PERMISSION_LEVELS = (VALSSI_YLLAPITAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL)

VALSSI_YLLAPITAJA_ORGANIZATION_OIDS = [
    "1.2.246.562.10.00000000001",  # Opetushallitus oid
    "1.2.246.562.10.12218193316"]  # Karvi oid

OPETUSHALLITUS_OID = "1.2.246.562.10.00000000001"

DEFAULT_ORGANIZATION_YTUNNUS = "0000000-0"

OPINTOPOLKU_HEADERS = {'Caller-Id': 'csc.valssi', 'CSRF': 'csc.valssi', 'Cookie': 'CSRF=csc.valssi'}

USER_PERMISSIONS_RECHECK_TIME = 30  # minutes

VIESTINTAPALVELU_SETTINGS = dict(
    name="viestintapalvelu",
    login_cred={
        "username": settings.VIESTINTAPALVELU_AUTH_USER,
        "password": settings.VIESTINTAPALVELU_AUTH_PW},
    url=settings.VIESTINTAPALVELU_URL,
    timeout=settings.VIESTINTAPALVELU_TIMEOUT)

TEMPLATE_NO_ORIGINAL_SEND = 1

SUCCESS_STATUSES = (status.HTTP_200_OK, status.HTTP_201_CREATED)

DATE_INPUT_FORMAT = "%Y-%m-%d"

KYSELYSEND_MESSAGE_MAX_LENGTH = 5000

# Email message statuses
EMAIL_STATUS_SENT = "sent"
EMAIL_STATUS_DELIVERED = "delivered"
EMAIL_STATUS_FAILED = "failed"

SERVICE_USER_GROUP = "palvelukayttaja"
SERVICE_USER_ACTIONS = ("retrieve", )

PDF_FILENAME_REPLACES = [("Å", "A"), ("Ä", "A"), ("Ö", "O"), ("å", "a"), ("ä", "a"), ("ö", "o")]
PDF_FILENAME_ALLOWED_CHARS = ascii_letters + digits + "_-. "
PDF_FILENAME_DEFAULT = "name_missing"

ALLOWED_LANGUAGE_CODES = ["fi", "sv"]

PUBLISHED_STATUS = "julkaistu"

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

# Vastaajatunnus taustatiedot inclusion settings
VASTAAJATUNNUS_TAUSTATIEDOT_SETTINGS = dict(
    asiantuntijalomake_paakayttaja_prosessitekijat=dict(  # type 1
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=False,
            taydennyskoulutus_data=False,
            toimipaikka_data=False)),
    asiantuntijalomake_paivakoti_prosessitekijat=dict(  # type 2
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=False,
            taydennyskoulutus_data=False,
            toimipaikka_data=False)),
    henkilostolomake_prosessitekijat=dict(  # type 3
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=False,
            taydennyskoulutus_data=False,
            toimipaikka_data=True)),
    huoltajalomake_prosessitekijat=dict(  # type 4
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=False,
            taydennyskoulutus_data=False,
            toimipaikka_data=True)),
    asiantuntijalomake_paivakoti_rakennetekijat=dict(  # type 6(1)
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            taydennyskoulutus_data=False,
            toimipaikka_data=False)),
    asiantuntijalomake_paakayttaja_rakennetekijat=dict(  # type 6(2)
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            taydennyskoulutus_data=False,
            toimipaikka_data=False)),
    henkilostolomake_rakennetekijat=dict(  # type 7
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            taydennyskoulutus_data=False,
            toimipaikka_data=False)),
    huoltajalomake_rakennetekijat=dict(  # type 8
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            taydennyskoulutus_data=False,
            toimipaikka_data=True)),
    taydennyskoulutuslomake_rakennetekijat=dict(  # type 9(1)
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            taydennyskoulutus_data=True,
            toimipaikka_data=False)),
    taydennyskoulutuslomake_paakayttaja_rakennetekijat=dict(  # type 9(2)
        data_settings=dict(
            organisaatio_data=True,
            rakennetekija_data=True,
            taydennyskoulutus_data=True,
            toimipaikka_data=False)))

PDF_INDICATOR_INFO_TRANSLATIONS = dict(
    fi="Tällä työkalulla arvioidaan seuraavan laatuindikaattorin toteutumista:",
    sv="Med det här verktyget utvärderar vi förverkligandet av följande kvalitetsindikator:")

PDF_LOGO_PATHS = dict(fi="kyselyt/css/karvi_logo_fi.png", sv="kyselyt/css/karvi_logo_sv.png")

TILAENUM_ARCHIVED = "arkistoitu"

HTML_ESCAPE_REPLACES = [
    (">", "&gt;"),
    ("<", "&lt;")]

VARDA_ORG_LAST_UPDATE_DEADLINE_FOR_ERROR = 24  # hours

# loop configs
MAX_NO_OF_LOOPS = 3
