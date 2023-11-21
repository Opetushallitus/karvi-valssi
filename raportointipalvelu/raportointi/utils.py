"""Utility functions for raportointipalvelu"""
import logging
import requests

from datetime import timedelta, datetime
from requests import ReadTimeout
from typing import List, Set, Tuple

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework_simplejwt.tokens import RefreshToken

from raportointipalvelu.celery import app as celery_app
from raportointi.constants import (
    SUCCESS_STATUSES, VALSSI_PERMISSION_LEVELS, OPINTOPOLKU_HEADERS, VALSSI_TOTEUTTAJA_LEVEL, VALSSI_YLLAPITAJA_LEVEL,
    ALLOWED_LANGUAGE_CODES, OPETUSHALLITUS_OID, VALSSI_YLLAPITAJA_ORGANIZATION_OIDS, USER_PERMISSIONS_RECHECK_TIME,
    HTML_ESCAPE_REPLACES, TINY_VALUE, MAX_NO_OF_LOOPS)
from raportointi.enums.error_messages import ErrorMessages
from raportointi.models import Kyselykerta, Kysely, Kysymysryhma, Organisaatio, UserAuthorization
from raportointi.opintopolku_auth import get_service_ticket


logger = logging.getLogger(__name__)


def datenow_delta(days: int) -> datetime:
    """Returns datetime n-days from current date"""
    return timezone.now() + timedelta(days=days)


def is_expired(end_date) -> bool:
    """Check if a date is past the current date"""
    if end_date < timezone.now().date():
        return True
    return False


def transform_tuples_lists_to_integers(
        list_length: int, answers_lists_raw: List[List[tuple[int, int]]]) -> List[List[int]]:
    """Transforms a list of lists containing tuples into a list of lists of integers.
    Example:
        transform_list([[(1, 5), (3, 1)], [(1, 2), (2, 2), (3, 2), (4, 2), (5, 2)]])
        returns: [[5, 0, 1, 0, 0], [2, 2, 2, 2, 2]]
    """
    final_list = []

    for answer_list in answers_lists_raw:
        question_results_list = [0] * list_length
        for answer in answer_list:
            if not answer[0]:  # if answer is None
                continue
            index = int(answer[0]) - 1
            if index < 0 or index >= list_length:
                logger.error(f"Index {index} out of range for list of length {list_length}")
                continue
            question_results_list[index] = answer[1]
        final_list.append(question_results_list)

    return final_list


def convert_int_lists_to_zero_lists_if_total_lt_limit(answers_lists: List[List[int]], limit: int) -> List[List[int]]:
    final_list = []
    for answers_list in answers_lists:
        if sum(answers_list) < limit:
            final_list.append([0] * len(answers_list))
        else:
            final_list.append(answers_list)

    return final_list


def convert_lists_to_percent(lists: List[List[int]]) -> List[List[int]]:
    """Convert a list of lists of integers to a list of lists of percentages."""
    result = []
    for sublist in lists:
        total = sum(sublist)
        if total == 0:
            result.append([0] * len(sublist))
        else:
            # to fix exact half rounding always up, add tiny value
            percent_list = [round(x / total * 100 + TINY_VALUE) for x in sublist]
            result.append(percent_list)
    return result


def convert_lists_to_sum(lists: List[List[int]]) -> List[int]:
    """Convert a list of lists to a list of sums."""
    result = []
    for sublist in lists:
        total = sum(sublist)
        result.append(total)
    return result


def convert_lists_to_bool_with_limit(lists: List[List[int]], limit: int) -> List[bool]:
    """Convert a list of lists to a list of booleans,
    where True means that the sum of the list is greater than the limit.
    """
    result = []
    for sublist in lists:
        limit_ok = sum(sublist) >= limit
        result.append(limit_ok)
    return result


def convert_lists_to_average(lists: List[List[int]]) -> List[str]:
    """Convert a list of lists to the average of their weighted elements."""
    result = []
    for sublist in lists:
        if sum(sublist) == 0:
            result.append("0")
            continue
        total_sum = sum(i * item for i, item in enumerate(sublist, 1))
        # to fix exact half rounding always up, add tiny value
        result.append(str(round(total_sum / sum(sublist) + TINY_VALUE, 1)).replace(".", ","))
    return result


def insert_line_breaks(strings: List[str], max_line_length: int, max_words_per_line: int) -> List[str]:
    """Insert line breaks in strings based on max line length and words per line."""
    new_strings = []
    for string in strings:
        words = string.split()
        new_string = ""
        count = 0
        word_count = 0
        for word in words:
            if count + len(word) > max_line_length or word_count >= max_words_per_line:
                new_string += "<br>"
                count = 0
                word_count = 0
            new_string += word + " "
            count += len(word) + 1
            word_count += 1
        new_strings.append(new_string)
    return new_strings


def get_henkilo_oid_and_permissions(username=None):
    if not username:
        logger.error("No user logged in to Opintopolku.")
        return None, None

    # check db for user authorization
    user_auth, _ = UserAuthorization.objects.get_or_create(username=username)
    if not user_auth.updated_time:
        pass
    elif user_auth.updated_time + timedelta(minutes=USER_PERMISSIONS_RECHECK_TIME) > timezone.now():
        return user_auth.oid, user_auth.permissions

    resp = get_permissions_for_user(username)

    if resp is None:
        logger.warning("Raportointipalvelu not able to get henkilo oid and permissions.")
    elif resp.status_code in SUCCESS_STATUSES:
        # check response json validity
        try:
            resp_json = resp.json()[0]
        except Exception:
            logger.error("Raportointipalvelu getting data from käyttöoikeus-service: response not valid json.")
            return None, None
        oid_henkilo = resp_json.get("oidHenkilo")
        organisaatiot = resp_json.get("organisaatiot")
        if oid_henkilo and organisaatiot is not None:
            org_perms = get_valssi_organisaatiot_permissions(resp_json["organisaatiot"])
            UserAuthorization.objects.filter(id=user_auth.id).update(
                oid=oid_henkilo, permissions=org_perms, updated_time=timezone.now())
            return oid_henkilo, org_perms
    else:
        logger.warning(f"Käyttöoikeus-service read error, http status code: {resp.status_code}. Error: {resp.text}")

    return None, None


def get_permissions_for_user(username):
    resp = None
    try:
        resp = requests.get(
            f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username={username}",
            headers=get_authentication_header(settings.KAYTTOOIKEUS_SERVICE),
            timeout=settings.KAYTTOOIKEUS_SERVICE_TIMEOUT)
    except ReadTimeout:
        logger.warning("Käyttöoikeus-service read timeout.")
    except Exception as e:
        logger.error(f"Käyttöoikeus-service read error: {str(e)}")
    return resp


def get_valssi_organisaatiot_permissions(organisaatiot: List[dict]) -> List[dict]:
    return [dict(organisaatioOid=org["organisaatioOid"],
                 valssiPermissions=get_valssi_permission_levels(org["kayttooikeudet"])) for org in organisaatiot]


def get_valssi_permission_levels(permissions: List[dict]) -> List:
    # parse Valssi related permissions from permission list
    return [lvl for lvl in VALSSI_PERMISSION_LEVELS
            for p in permissions if p["palvelu"] == "VALSSI" and p["oikeus"] == lvl]


def get_authentication_header(service_name, username=None, password=None):
    service_ticket_url = get_service_ticket(service_name + "/j_spring_cas_security_check", username, password)
    return {"CasSecurityTicket": service_ticket_url, "Content-Type": "application/json", **OPINTOPOLKU_HEADERS}


def get_kyselykerta_or_raise_error(kyselykertaid: int) -> Kyselykerta:
    kyselykerta = Kyselykerta.objects.filter(kyselykertaid=kyselykertaid)
    if not kyselykerta.exists():
        raise ValidationError([ErrorMessages.ER002.value])  # HTTP_400_BAD_REQUEST
    return kyselykerta[0]


def get_valssi_organisaatio_oids_by_permission_levels(permissions: List[dict], levels: List[str]) -> Set[str]:
    return {perm["organisaatioOid"] for level in levels
            for perm in permissions if level in perm["valssiPermissions"]}


def filter_oppilaitos_oids_by_koulutustoimija(oppilaitos_oids: Set[str], koulutustoimija: Organisaatio) -> Set[str]:
    filtered_orgs = Organisaatio.objects.filter(oid__in=oppilaitos_oids, parent_oid=koulutustoimija)
    return set(filtered_orgs.values_list("oid", flat=True))


def get_tokens_for_user(user):
    """Create tokens for given user."""
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh),
            "access": str(refresh.access_token), }


def add_token_to_blacklist(token):
    try:
        rtoken = RefreshToken(token)
        rtoken.blacklist()
    except Exception:
        pass


def group_kyselys_by_kysymysryhma_and_startdate(kyselys: List[dict]) -> List[List[dict]]:
    grouped_kyselys = dict()
    for kysely in kyselys:
        grouped_kyselys.setdefault(f"{kysely['kysymysryhmaid']}-{kysely['voimassa_alkupvm']}", []).append(kysely)
    return list(grouped_kyselys.values())


def group_kyselys_by_kysymysryhma(kyselys: List[dict]) -> List[List[dict]]:
    grouped_kyselys = dict()
    for kysely in kyselys:
        grouped_kyselys.setdefault(f"{kysely['kysymysryhmaid']}", []).append(kysely)
    return list(grouped_kyselys.values())


def get_kysymysryhmas_with_closed_kyselys(organisation_oids: Set[str]) -> Tuple[QuerySet[Kysymysryhma], List[int]]:
    """Get kysymysryhmas with closed kyselys which user has access"""

    kysymysryhma_ids = Kysely.objects.filter(
        Q(koulutustoimija__oid__in=organisation_oids) | Q(oppilaitos__oid__in=organisation_oids),
        voimassa_loppupvm__lt=timezone.now().date()) \
        .values_list("metatiedot__valssi_kysymysryhma", flat=True).distinct()

    return Kysymysryhma.objects.filter(kysymysryhmaid__in=list(kysymysryhma_ids)), kysymysryhma_ids


def get_koulutustoimija_by_oid(oid: str) -> Organisaatio:
    koulutustoimija = Organisaatio.objects.filter(
        oid=oid, parent_oid__oid=OPETUSHALLITUS_OID).first()
    if koulutustoimija is None:
        raise NotFound([ErrorMessages.ER017.value])  # HTTP_404_NOT_FOUND
    return koulutustoimija


def get_query_param_filters(query_params: dict, permission_level: str) -> dict:
    """Get filtered query parameters from a query dictionary."""
    job_title_code = query_params.get("job_title_code")
    eligibility = query_params.get("eligibility")
    kyselykerta_alkupvm = query_params.get("kyselykerta_alkupvm")

    filter_dict = {}

    if permission_level != VALSSI_TOTEUTTAJA_LEVEL:
        filter_dict["answer_filters"] = {}
        if job_title_code:
            filter_dict["answer_filters"]["tehtavanimike_koodi"] = job_title_code

        if eligibility:
            filter_dict["answer_filters"]["kelpoisuus_kytkin"] = eligibility.lower() in [
                "true",
                "false"
            ] and eligibility.lower() == "true"

    if kyselykerta_alkupvm:
        filter_dict["kyselykerta_alkupvm"] = kyselykerta_alkupvm

    return filter_dict


def validate_language_code(language_code: str):
    if language_code not in ALLOWED_LANGUAGE_CODES:
        error = dict(ErrorMessages.ER013.value)
        error["description"] = error["description"].format(ALLOWED_LANGUAGE_CODES)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


def validate_yllapitaja_permission(henkilo_permissions: List[dict], allowed_oids: Set[str] = None):
    if allowed_oids is None:
        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, [VALSSI_YLLAPITAJA_LEVEL])
    if not any([org in allowed_oids for org in VALSSI_YLLAPITAJA_ORGANIZATION_OIDS]):
        raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN


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
    logger.error("Raportointipalvelu not able to get localisation-data.")
    return values
