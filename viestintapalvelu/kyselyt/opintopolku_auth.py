import logging
import requests

from datetime import datetime, timedelta
from time import sleep
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone
from rest_framework import status

from kyselyt.constants import OPINTOPOLKU_HEADERS, CALLER_ID_HEADER, MAX_NO_OF_LOOPS
from kyselyt.models import OphAuthentication


logger = logging.getLogger(__name__)


def get_or_create_oph_auth():
    oph_auth = OphAuthentication.objects.order_by("id").first()
    if not oph_auth:
        oph_auth = OphAuthentication.objects.create(tgt="")
    return oph_auth


def clear_oph_auth_tgt(oph_auth: OphAuthentication = None, sleep_seconds: int = 1):
    # Retrieve or create OphAuthentication if not provided
    if oph_auth is None:
        oph_auth = get_or_create_oph_auth()

    # Skip clearing if the last clearance was done within the last minute
    last_cleared = oph_auth.tgt_last_cleared_time
    if last_cleared and last_cleared + timedelta(minutes=1) > timezone.now():
        logger.warning("OphAuthentication TGT clearing skipped. Last cleared time less than 1 minute ago.")
        return None

    # Clear the TGT and update the last cleared timestamp
    oph_auth.tgt = ""
    oph_auth.tgt_last_cleared_time = timezone.now()
    oph_auth.save()
    logger.info("OphAuthentication TGT cleared.")

    sleep(sleep_seconds)
    return None


def get_new_ticket_granting_ticket(username, password):
    if username is None or password is None:
        username = settings.OPINTOPOLKU_USERNAME
        password = settings.OPINTOPOLKU_PASSWORD

    credentials = urlencode({"username": username, "password": password})

    headers = {"Content-Type": "application/x-www-form-urlencoded", **OPINTOPOLKU_HEADERS}

    try:
        resp = requests.post(settings.OPINTOPOLKU_URL + "/cas/v1/tickets", data=credentials, headers=headers)
    except Exception as e:
        logger.error(f"Exception for /cas/v1/tickets. Error: {str(e)}")
        return None

    if resp.status_code == status.HTTP_201_CREATED:
        return resp.headers["Location"]
    else:
        logger.warning(f"Error fetching tgt for user: {str(username)}. Status code: {resp.status_code}. {resp.content}")
        return None


def get_service_ticket(username, password):
    for i in range(MAX_NO_OF_LOOPS):
        headers = {"Content-Type": "application/x-www-form-urlencoded", **OPINTOPOLKU_HEADERS}

        oph_auth = get_or_create_oph_auth()

        ticket_granting_ticket_location = oph_auth.tgt
        if not ticket_granting_ticket_location.startswith("http"):
            ticket_granting_ticket_location = get_new_ticket_granting_ticket(username, password)

        if ticket_granting_ticket_location is None or not ticket_granting_ticket_location.startswith("http"):
            break

        try:
            resp = requests.post(
                ticket_granting_ticket_location,
                data=f"service={settings.EMAIL_URL_BASE}/lahetys/login/j_spring_cas_security_check",
                headers=headers)
        except Exception as e:
            logger.error(f"Exception for ticket_granting_ticket_location. Error: {str(e)}")
            sleep(2)
            continue

        if resp.status_code == status.HTTP_200_OK:
            oph_auth.tgt = ticket_granting_ticket_location
            oph_auth.save()
            return resp.content.decode("utf-8")
        elif resp.status_code != status.HTTP_404_NOT_FOUND:
            logger.error(f"Could not get a TGT. Status: {resp.status_code}. {resp.content}.")

        # Probably TGT is unvalid. Clear the one in DB, and fetch a new one.
        clear_oph_auth_tgt(oph_auth)

    logger.error(f"Error: Did not get a service ticket for user: {username}. TGT: {ticket_granting_ticket_location}")
    return ""


def get_session_cookie(service_ticket):
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    current_time = datetime.now()

    oph_auth = get_or_create_oph_auth()
    if oph_auth.viestinvalitys_session_cookie:
        last_update_str = oph_auth.viestinvalitys_session_cookie_last_update_time

        last_update_time = datetime.strptime(last_update_str, DATETIME_FORMAT)

        if current_time - last_update_time < timedelta(minutes=settings.EMAIL_SERVICE_SESSION_COOKIE_RENEWAL_INTERVAL):
            return oph_auth.viestinvalitys_session_cookie

    try:
        resp = requests.get(
            f"{settings.EMAIL_URL_BASE}/lahetys/login/j_spring_cas_security_check?ticket={service_ticket}",
            headers=CALLER_ID_HEADER,
            allow_redirects=False)

        session_cookie = resp.cookies.get("JSESSIONID", "")
        if session_cookie:
            oph_auth.viestinvalitys_session_cookie = session_cookie
            oph_auth.viestinvalitys_session_cookie_last_update_time = current_time.strftime(DATETIME_FORMAT)
            oph_auth.save()
            return session_cookie
        else:
            logger.error("Error getting session cookie in get_session_cookie().")
    except Exception as e:
        logger.error(f"Error in get_session_cookie(). Error: {str(e)}")

    return ""


def get_authentication_header(username=None, password=None):
    service_ticket = get_service_ticket(username, password)
    session_cookie = get_session_cookie(service_ticket)
    return {"Cookie": f"JSESSIONID={session_cookie};", **CALLER_ID_HEADER}


def get_contenttype_header():
    return {"Content-Type": "application/json", **OPINTOPOLKU_HEADERS}
