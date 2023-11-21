import logging
import requests

from requests.exceptions import ReadTimeout

from django.conf import settings
from rest_framework import status

from kyselyt.constants import VIRKAILIJAPALVELU_SETTINGS, SUCCESS_STATUSES, MAX_NO_OF_LOOPS
from kyselyt.tokens import TOKENS
from kyselyt.utils import request_service


logger = logging.getLogger(__name__)


def get_access_token_for_palvelu(palvelu: dict):
    token = TOKENS[palvelu["name"]]

    if not token:
        resp = None
        try:
            resp = requests.post(
                f"{palvelu['url']}/api/v1/token/", data=palvelu["login_cred"], timeout=palvelu["timeout"])
        except ReadTimeout:
            logger.warning(f"{palvelu['name'].title()} login timeout.")
            return None
        except Exception as e:
            logger.error(f"{palvelu['name'].title()} login error: {str(e)}")
            return None

        if resp.status_code in SUCCESS_STATUSES and "access" in resp.json():
            token = resp.json()["access"]
            TOKENS[palvelu["name"]] = token
            logger.info(f"{palvelu['name'].title()} access token updated.")
        else:
            logger.warning(f"{palvelu['name'].title()} login error, http status code: {resp.status_code}")

    return token


def get_tyontekija_data(vastaajatunnus: str):
    for i in range(MAX_NO_OF_LOOPS):
        token = get_access_token_for_palvelu(VIRKAILIJAPALVELU_SETTINGS)
        if not token:
            continue

        resp = request_service(
            "Virkailijapalvelu", "get",
            f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/tyontekija/{vastaajatunnus}/",
            token, timeout=settings.VIRKAILIJAPALVELU_TIMEOUT)

        if resp is None:
            pass
        elif resp.status_code in SUCCESS_STATUSES:
            return resp.json()
        elif resp.status_code == status.HTTP_401_UNAUTHORIZED:
            logger.info("Virkailijapalvelu read: 401 Unauthorized.")
            TOKENS["virkailijapalvelu"] = None
            logger.info("Virkailijapalvelu expired access token removed.")
        else:
            logger.warning(f"Virkailijapalvelu read error, http status code: {resp.status_code}")
    logger.warning("Virkailijapalvelu not able to get tyontekija data.")
    return None


def get_scales():
    for i in range(MAX_NO_OF_LOOPS):
        resp = request_service(
            "Virkailijapalvelu", "get",
            f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/scale/",
            timeout=settings.VIRKAILIJAPALVELU_TIMEOUT)

        if resp is None:
            pass
        elif resp.status_code in SUCCESS_STATUSES:
            return resp.json()
        else:
            logger.warning(f"Virkailijapalvelu read error, http status code: {resp.status_code}")
    logger.warning("Error in requesting scales from Virkailijapalvelu.")
    return None


def get_malfunction_message():
    for i in range(MAX_NO_OF_LOOPS):
        resp = request_service(
            "Virkailijapalvelu", "get",
            f"{settings.VIRKAILIJAPALVELU_URL}/api/v1/malfunction-message/get-active/?service=vastauspalvelu",
            timeout=settings.VIRKAILIJAPALVELU_TIMEOUT)

        if resp is None:
            pass
        elif resp.status_code in SUCCESS_STATUSES:
            return resp.json()
        else:
            logger.warning(f"Virkailijapalvelu read error, http status code: {resp.status_code}")
    logger.warning("Error in requesting malfunction-message from Virkailijapalvelu.")
    return None
