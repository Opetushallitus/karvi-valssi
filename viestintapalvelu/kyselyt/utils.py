import logging
import requests

from requests.exceptions import ReadTimeout
from time import sleep
from typing import List, Tuple

from django.conf import settings
from django.template.loader import render_to_string

from viestintapalvelu.celery import app as celery_app
from kyselyt.constants import (
    SUCCESS_STATUSES, PDF_CONTENT_TYPE, FIRST_MSG_TEMPLATE_NO, SECOND_MSG_TEMPLATE_NO, ANSWER_PDF_TEMPLATE_NO,
    KYSELY_LINK_BASE, FIRST_MSG_TEMPLATE_SUBJECT, SECOND_MSG_TEMPLATE_SUBJECT, ANSWER_PDF_TEMPLATE_SUBJECT,
    FIRST_MSG_TEMPLATE_LINES, SECOND_MSG_TEMPLATE_LINES, ANSWER_PDF_TEMPLATE_LINES, PRIVACY_STATEMENT_TEXT,
    PRIVACY_STATEMENT_LINK, EMAIL_STATUS_SENT, EMAIL_STATUS_FAILED, MAX_NO_OF_LOOPS, LOOP_SLEEPS)
from kyselyt.models import FailedTask
from kyselyt.opintopolku_auth import get_authentication_header


logger = logging.getLogger(__name__)


def send_email_vastaajatunnus(email: str, vastaajatunnus: str, message: str, template: int,
                              pdfs_encoded: List[dict]) -> Tuple[str, int]:
    html_body, subject = get_email_content(template, vastaajatunnus, message)

    for i in range(MAX_NO_OF_LOOPS):
        resp = send_email_to_email_service([email], subject, html_body, pdfs_encoded)

        if resp is None:
            pass
        elif resp.status_code in SUCCESS_STATUSES:
            return "OK", resp.json()["id"]
        else:
            logger.warning(f"Ryhmasahkoposti-service read error, http status code: {resp.status_code}.")
        sleep(LOOP_SLEEPS[i])

    log_msg = f"Ryhmasahkoposti-service send max retries ({MAX_NO_OF_LOOPS}) exceeded."
    logger.error(log_msg)
    return log_msg, 0


def send_email_to_email_service(email_list: List[str], subject: str, html_body: str, pdfs_encoded: List[dict]):
    attachments = [{
        "data": pdf["file_encoded"],
        "name": pdf["filename"],
        "contentType": PDF_CONTENT_TYPE} for pdf in pdfs_encoded]
    data = {
        "recipient": [{"email": email} for email in email_list],
        "email": {
            "from": settings.EMAIL_FROM_ADDRESS,
            "subject": subject,
            "body": html_body,
            "html": "true",
            "attachments": attachments}}

    resp = None
    try:
        resp = requests.post(
            f"{settings.EMAIL_SERVICE_URL}email",
            json=data,
            headers=get_authentication_header(settings.EMAIL_SERVICE),
            timeout=settings.EMAIL_SERVICE_TIMEOUT)
    except ReadTimeout:
        logger.warning("Ryhmasahkoposti-service read timeout.")
    except Exception as e:
        logger.warning(f"Ryhmasahkoposti-service read error: {str(e)}")
    return resp


def get_email_status(email_service_msg_id: int) -> str:
    for i in range(MAX_NO_OF_LOOPS):
        resp = get_email_status_from_email_service(email_service_msg_id)

        if resp is None:
            pass
        elif resp.status_code in SUCCESS_STATUSES:
            if resp.json()["sendingStatus"]["numberOfSuccessfulSendings"]:
                return EMAIL_STATUS_SENT
            return EMAIL_STATUS_FAILED
        else:
            logger.warning(f"Ryhmasahkoposti-service read error, http status code: {resp.status_code}.")
        sleep(LOOP_SLEEPS[i])

    logger.error(f"Ryhmasahkoposti-service check email status max retries ({MAX_NO_OF_LOOPS}) exceeded.")
    return None


def get_email_status_from_email_service(email_service_msg_id: int) -> str:
    resp = None
    try:
        resp = requests.post(
            f"{settings.EMAIL_SERVICE_URL}email/result",
            json=email_service_msg_id,
            headers=get_authentication_header(settings.EMAIL_SERVICE),
            timeout=settings.EMAIL_SERVICE_TIMEOUT)
    except ReadTimeout:
        logger.warning("Ryhmasahkoposti-service read timeout.")
    except Exception as e:
        logger.warning(f"Ryhmasahkoposti-service read error: {str(e)}")
    return resp


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
                "tietosuojaseloste_text": PRIVACY_STATEMENT_TEXT,
                "tietosuojaseloste_link": PRIVACY_STATEMENT_LINK
            },)
    elif template == SECOND_MSG_TEMPLATE_NO:
        subject = SECOND_MSG_TEMPLATE_SUBJECT
        message_lines = message.split("\n") if message else None
        html_body = render_to_string(
            "email.html", {
                "message": message_lines,
                "lines": SECOND_MSG_TEMPLATE_LINES,
                "kysely_link": kysely_link,
                "tietosuojaseloste_text": PRIVACY_STATEMENT_TEXT,
                "tietosuojaseloste_link": PRIVACY_STATEMENT_LINK
            },)
    elif template == ANSWER_PDF_TEMPLATE_NO:
        subject = ANSWER_PDF_TEMPLATE_SUBJECT
        html_body = render_to_string(
            "email.html", {
                "message": None,
                "lines": ANSWER_PDF_TEMPLATE_LINES,
                "kysely_link": None,
                "tietosuojaseloste_text": None,
                "tietosuojaseloste_link": None
            },)

    return html_body, subject


def check_celery_worker_running() -> bool:
    try:
        celery_inspect = celery_app.control.inspect()
        if celery_inspect.active():
            return True
    except Exception:
        pass
    return False


def get_ci_pipeline_number() -> int:
    pipeline_number = -1
    try:
        f = open("./ci_pipeline_id", "r")
        pipeline_number = int(f.readline().strip())
        f.close()
    except Exception:
        pass
    return pipeline_number


def get_failed_task_count(default_value: int = None) -> int:
    failed_task_count = default_value
    try:
        failed_task_count = FailedTask.objects.count()
    except Exception:
        pass
    return failed_task_count
