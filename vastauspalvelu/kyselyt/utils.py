import logging
import requests
import time

from datetime import datetime
from requests.exceptions import ReadTimeout

from django.conf import settings
from rest_framework.exceptions import ValidationError

from vastauspalvelu.celery import app as celery_app
from kyselyt.constants import (
    SUCCESS_STATUSES, ALLOWED_LANGUAGE_CODES, HTML_ESCAPE_REPLACES, MAX_NO_OF_LOOPS, UI_LOG_EPOCH_DIFF_LIMIT,
    MANDATORY_LANGUAGE_CODES,
)
from kyselyt.enums.error_messages import ErrorMessages
from kyselyt.models import TempVastaus, Kysymysryhma


logger = logging.getLogger(__name__)


def request_service(service_name: str, request_type: str, address: str, token: str = None, auth: set = None,
                    data: dict = None, json: dict = None, files: dict = None, timeout: int = 5):
    resp = None
    headers = {"Authorization": f"Bearer {token}"} if token else None
    try:
        if request_type == "get":
            resp = requests.get(address, auth=auth, headers=headers, timeout=timeout)
        elif request_type == "post":
            resp = requests.post(
                address, auth=auth, headers=headers, data=data, json=json, files=files, timeout=timeout)
    except ReadTimeout:
        logger.warning(f"{service_name} read timeout.")
    except Exception as e:
        logger.warning(f"{service_name} read error: {str(e)}")
    return resp


def get_localisation_values_by_key(key: str) -> dict:
    values = dict(fi=key, sv=key, en=key)

    for i in range(MAX_NO_OF_LOOPS):
        resp = request_service(
            "Virkailijapalvelu/localisation", "get",
            f"{settings.LOCALISATION_ENDPOINT}/?key={key}",
            timeout=settings.LOCALISATION_SERVICE_TIMEOUT)

        if resp is None:
            continue
        elif resp.status_code in SUCCESS_STATUSES:
            for item in resp.json():
                if item["locale"] == "fi":
                    values["fi"] = item["value"]
                elif item["locale"] == "sv":
                    values["sv"] = item["value"]
                elif item["locale"] == "en":
                    values["en"] = item["value"]
            return values
        else:
            logger.warning(
                f"Virkailijapalvelu/localisation read error, http status code: {resp.status_code}. "
                f"Error: {resp.text}"
            )
    logger.error(f"Vastauspalvelu not able to get localisation-data. ({key})")
    return values


def validate_language_code(language_code: str):
    if language_code not in ALLOWED_LANGUAGE_CODES:
        error = dict(ErrorMessages.DY002.value)
        error["description"] = error["description"].format(ALLOWED_LANGUAGE_CODES)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


def validate_language_code_by_kysymysryhma(language_code: str, kysymysryhma: Kysymysryhma):
    # Mandatory language codes are always valid
    if language_code in MANDATORY_LANGUAGE_CODES:
        pass
    elif language_code == "en" and not kysymysryhma.nimi_en:
        raise ValidationError([ErrorMessages.DY003.value])  # HTTP_400_BAD_REQUEST


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


def sanitize_string(string: str) -> str:
    if not isinstance(string, str):
        return string
    str_modified = string
    for esc_repl in HTML_ESCAPE_REPLACES:
        str_modified = str_modified.replace(esc_repl[0], esc_repl[1])
    return str_modified


def delete_outdated_tempvastauses() -> int:
    delete_count, _ = TempVastaus.objects.filter(kysely_voimassa_loppupvm__lt=datetime.now().date()).delete()
    return delete_count


def validate_log_timestamp(log_timestamp: int) -> bool:
    timenow = time.time()
    if timenow - UI_LOG_EPOCH_DIFF_LIMIT < log_timestamp < timenow + UI_LOG_EPOCH_DIFF_LIMIT:
        return True
    return False
