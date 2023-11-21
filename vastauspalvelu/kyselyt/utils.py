import logging
import requests

from datetime import datetime
from requests.exceptions import ReadTimeout

from django.conf import settings
from rest_framework.exceptions import ValidationError

from vastauspalvelu.celery import app as celery_app
from kyselyt.constants import SUCCESS_STATUSES, ALLOWED_LANGUAGE_CODES, HTML_ESCAPE_REPLACES, MAX_NO_OF_LOOPS
from kyselyt.enums.error_messages import ErrorMessages
from kyselyt.models import TempVastaus


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
    localisation_key = "indik.desc_" + key
    values = dict(fi=f"FI {key}", sv=f"SV {key}")

    for i in range(MAX_NO_OF_LOOPS):
        resp = request_service(
            "Lokalisointipalvelu", "get",
            f"{settings.LOCALISATION_ENDPOINT}/?key={localisation_key}",
            timeout=settings.LOCALISATION_SERVICE_TIMEOUT)

        if resp is None:
            continue
        elif resp.status_code in SUCCESS_STATUSES:
            for item in resp.json():
                if item["locale"] == "fi":
                    values["fi"] = item["value"]
                elif item["locale"] == "sv":
                    values["sv"] = item["value"]
            return values
        else:
            logger.warning(f"Lokalisointipalvelu read error, http status code: {resp.status_code}. Error: {resp.text}")
    logger.warning("Vastauspalvelu not able to get localisation-data.")
    return values


def validate_language_code(language_code: str):
    if language_code not in ALLOWED_LANGUAGE_CODES:
        error = dict(ErrorMessages.DY002.value)
        error["description"] = error["description"].format(ALLOWED_LANGUAGE_CODES)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


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
