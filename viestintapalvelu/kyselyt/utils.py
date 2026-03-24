import logging
import requests
import time

from base64 import b64decode
from datetime import timedelta
from requests.exceptions import ReadTimeout
from time import sleep
from typing import List, Tuple

from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import status

from viestintapalvelu.celery import app as celery_app
from kyselyt.constants import (
    SUCCESS_STATUSES, PDF_CONTENT_TYPE, FIRST_MSG_TEMPLATE_NO, SECOND_MSG_TEMPLATE_NO, ANSWER_PDF_TEMPLATE_NO,
    KYSELY_LINK_BASE, FIRST_MSG_TEMPLATE_SUBJECT, SECOND_MSG_TEMPLATE_SUBJECT, ANSWER_PDF_TEMPLATE_SUBJECT,
    FIRST_MSG_TEMPLATE_LINES, SECOND_MSG_TEMPLATE_LINES, ANSWER_PDF_TEMPLATE_LINES, PRIVACY_STATEMENT_TEXT,
    PRIVACY_STATEMENT_LINK, EMAIL_STATUS_SENT, EMAIL_STATUS_FAILED, EMAIL_STATUS_DELIVERED, MAX_NO_OF_LOOPS,
    LOOP_SLEEPS, VIESTINVALITYS_STATUSES_SENT, VIESTINVALITYS_STATUSES_DELIVERED, VIESTINVALITYS_STATUSES_FAILED,
    POHDINTAKESKUSTELU_ADDITIONAL_TEXTS, ADDITIONAL_TEMPLATE_LINES,
)
from kyselyt.models import FailedTask, Message
from kyselyt.opintopolku_auth import get_authentication_header, clear_oph_auth_tgt


logger = logging.getLogger(__name__)


def send_email_vastaajatunnus(email: str, vastaajatunnus: str, message: str, template: int,
                              pdfs_encoded: List[dict]) -> Tuple[str, int]:
    html_body, subject = get_email_content(template, vastaajatunnus, message)

    resp = None
    attachments = send_attachments_to_email_service(pdfs_encoded)
    if attachments is None:
        pass
    else:
        resp = send_email_to_email_service([email], subject, html_body, attachments)

    if resp is None:
        pass
    elif resp.status_code in SUCCESS_STATUSES:
        return "OK", resp.json()["lahetysTunniste"]
    else:
        logger.warning(f"{settings.EMAIL_SERVICE_NAME} read error, http status code: {resp.status_code}.")

    log_msg = f"{settings.EMAIL_SERVICE_NAME} send failed."
    logger.warning(log_msg)
    return log_msg, None


def send_email_to_email_service(email_list: List[str], subject: str, html_body: str, attachments: List[str]):
    data = {
        "otsikko": subject,
        "sisalto": html_body,
        "sisallonTyyppi": "html",
        "kielet": ["fi", "sv"],
        "lahettaja": {
            "nimi": settings.EMAIL_FROM_NAME,
            "sahkopostiOsoite": settings.EMAIL_FROM_ADDRESS
        },
        "vastaanottajat": [{"sahkopostiOsoite": email} for email in email_list],
        "lahettavaPalvelu": settings.EMAIL_SERVICE_EMAIL_SENDING_SERVICE,
        "prioriteetti": "normaali",
        "sailytysaika": settings.EMAIL_SERVICE_EMAIL_STORAGE_PERIOD,
        "liitteidenTunnisteet": attachments,
        "kayttooikeusRajoitukset": [
            {
                "organisaatio": settings.EMAIL_SERVICE_PERMISSION_ORG,
                "oikeus": settings.EMAIL_SERVICE_PERMISSION
            },
        ],
    }

    resp = None
    try:
        resp = requests.post(
            f"{settings.EMAIL_SERVICE_URL}/viestit",
            json=data,
            headers=get_authentication_header(),
            timeout=settings.EMAIL_SERVICE_TIMEOUT)
    except ReadTimeout:
        logger.warning(f"{settings.EMAIL_SERVICE_NAME} read timeout.")
    except Exception as e:
        logger.warning(f"{settings.EMAIL_SERVICE_NAME} read error: {str(e)}")
    return resp


def get_email_status(email_service_msg_id_str: str) -> (str, str):
    for i in range(MAX_NO_OF_LOOPS):
        email_status_code = get_email_status_from_email_service(email_service_msg_id_str)

        if email_status_code is None:
            pass
        elif email_status_code in VIESTINVALITYS_STATUSES_SENT:
            return EMAIL_STATUS_SENT, email_status_code
        elif email_status_code in VIESTINVALITYS_STATUSES_DELIVERED:
            return EMAIL_STATUS_DELIVERED, email_status_code
        else:
            if email_status_code not in VIESTINVALITYS_STATUSES_FAILED:
                logger.error(f"Faulty viestinvalitys email_status_code: {email_status_code}")
            return EMAIL_STATUS_FAILED, email_status_code
        sleep(LOOP_SLEEPS[i])

    logger.error(f"{settings.EMAIL_SERVICE_NAME} check email status max retries ({MAX_NO_OF_LOOPS}) exceeded.")
    return None, None


def get_email_status_from_email_service(email_service_msg_id_str: str) -> str:
    try:
        resp = requests.get(
            f"{settings.EMAIL_SERVICE_URL}/lahetykset/{email_service_msg_id_str}/vastaanottajat"
            "?enintaan=1",
            headers=get_authentication_header(),
            timeout=settings.EMAIL_SERVICE_TIMEOUT)
        if resp.status_code == status.HTTP_200_OK:
            return resp.json()["vastaanottajat"][0]["tila"]
        elif resp.status_code == status.HTTP_401_UNAUTHORIZED:
            logger.warning(
                f"{settings.EMAIL_SERVICE_NAME} (lahetykset/vastaanottajat) read error, http status code: "
                f"{resp.status_code}.")
            # Probably TGT is unvalid. Clear the one in DB.
            clear_oph_auth_tgt()
        else:
            logger.warning(
                f"{settings.EMAIL_SERVICE_NAME} (lahetykset/vastaanottajat) read error, http status code: "
                f"{resp.status_code}.")
    except ReadTimeout:
        logger.warning(f"{settings.EMAIL_SERVICE_NAME} read timeout.")
    except Exception as e:
        logger.warning(f"{settings.EMAIL_SERVICE_NAME} read error: {str(e)}")
    return None


def get_email_content(template: int, vastaajatunnus: str = None, message: str = "") -> Tuple[str, str]:
    subject = ""
    html_body = "<!doctype html><html></html>"

    kysely_link = KYSELY_LINK_BASE.format(vastaajatunnus)

    if template == FIRST_MSG_TEMPLATE_NO:
        subject = FIRST_MSG_TEMPLATE_SUBJECT
        message_lines = message.split("\n") if message else None
        html_body = render_to_string(
            "email.html", {
                "message": message_lines,
                "lines": FIRST_MSG_TEMPLATE_LINES,
                "kysely_link": kysely_link,
                "additional_lines": ADDITIONAL_TEMPLATE_LINES,
                "pohdintakeskustelu_texts": POHDINTAKESKUSTELU_ADDITIONAL_TEXTS,
                "tietosuojaseloste_text": PRIVACY_STATEMENT_TEXT,
                "tietosuojaseloste_link": PRIVACY_STATEMENT_LINK,
            },)
    elif template == SECOND_MSG_TEMPLATE_NO:
        subject = SECOND_MSG_TEMPLATE_SUBJECT
        message_lines = message.split("\n") if message else None
        html_body = render_to_string(
            "email.html", {
                "message": message_lines,
                "lines": SECOND_MSG_TEMPLATE_LINES,
                "kysely_link": kysely_link,
                "additional_lines": ADDITIONAL_TEMPLATE_LINES,
                "pohdintakeskustelu_texts": POHDINTAKESKUSTELU_ADDITIONAL_TEXTS,
                "tietosuojaseloste_text": PRIVACY_STATEMENT_TEXT,
                "tietosuojaseloste_link": PRIVACY_STATEMENT_LINK,
            },)
    elif template == ANSWER_PDF_TEMPLATE_NO:
        subject = ANSWER_PDF_TEMPLATE_SUBJECT
        html_body = render_to_string(
            "email.html", {
                "message": None,
                "lines": ANSWER_PDF_TEMPLATE_LINES,
                "kysely_link": None,
                "additional_lines": None,
                "pohdintakeskustelu_texts": None,
                "tietosuojaseloste_text": None,
                "tietosuojaseloste_link": None,
            },)

    return html_body, subject


def check_celery_worker_running() -> (bool, int):
    MAX_NO_OF_LOOPS = 3
    SLEEPS = [1, 1, 0]  # No sleep after last fail
    for i in range(MAX_NO_OF_LOOPS):
        try:
            active_workers = celery_app.control.ping()
            if active_workers:
                return True, len(active_workers)
            return False, len(active_workers)
        except Exception:
            pass
        time.sleep(SLEEPS[i])

    return False, 0


def get_ci_pipeline_number() -> int:
    pipeline_number = -1
    try:
        f = open("./ci_pipeline_id", "r")
        pipeline_number = int(f.readline().strip())
        f.close()
    except Exception:
        pass
    return pipeline_number


def get_failed_messages_count(default_value: int = None) -> int:
    failed_task_count = default_value
    try:
        failed_task_count = FailedTask.objects.count()
    except Exception:
        pass
    return failed_task_count


def get_earliest_failed_message_time_ago_minutes() -> int:
    oldest_minutes = 0
    try:
        oldest_failed_msg = FailedTask.objects.earliest("created")
        oldest_minutes = int((timezone.now() - oldest_failed_msg.created).total_seconds()) // 60
    except Exception:
        pass
    return oldest_minutes


def empty_email_fields_from_old_messages() -> int:
    # past end dates
    messages = Message.objects.filter(end_date__lt=timezone.now().date()) \
        .exclude(email__exact="")
    update_count = messages.update(email="")

    # end dates missing and created over 180d ago
    now_minus_180d = timezone.now() - timedelta(days=180)
    messages = Message.objects.filter(end_date=None, created__lt=now_minus_180d) \
        .exclude(email__exact="")
    update_count += messages.update(email="")

    return update_count


def send_attachments_to_email_service(pdfs_encoded: List[dict]):
    attachment_identifiers = []
    for pdf in pdfs_encoded:
        files = {
            "liite": (pdf["filename"], b64decode(pdf["file_encoded"]), PDF_CONTENT_TYPE)
        }
        try:
            resp = requests.post(
                f"{settings.EMAIL_SERVICE_URL}/liitteet",
                files=files,
                headers=get_authentication_header(),
                timeout=settings.EMAIL_SERVICE_TIMEOUT,)
            if resp.status_code == status.HTTP_200_OK:
                attachment_identifiers.append(resp.json()["liiteTunniste"])
            else:
                resp_errors = ""
                try:
                    resp_errors = resp.json().get("virheet", "")
                except Exception:
                    pass
                logger.warning(
                    f"{settings.EMAIL_SERVICE_NAME} (liitteet) read error, http status code: "
                    f"{resp.status_code}. {resp_errors}")
                return None
        except ReadTimeout:
            logger.warning(f"{settings.EMAIL_SERVICE_NAME} read timeout.")
            return None
        except Exception as e:
            logger.warning(f"{settings.EMAIL_SERVICE_NAME} read error: {str(e)}")
            return None

    return attachment_identifiers
