import logging
import requests
import time

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
    HTML_ESCAPE_REPLACES, TINY_VALUE, LAATUTEKIJAS, REPORT_FILTER_LANGUAGE_CODES, MANDATORY_LANGUAGE_CODES,
    LIMITED_LANGUAGE_CODES,
)
from raportointi.enums.error_messages import ErrorMessages
from raportointi.models import Kyselykerta, Kysely, Kysymysryhma, Organisaatio, UserAuthorization, Localisation
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


def convert_list_to_percent(int_list: List[int], fixed_denominator=None) -> List[int]:
    """Convert a list of integers to a list of percentages."""

    denominator = fixed_denominator if fixed_denominator else sum(int_list)

    if denominator == 0:
        return [0] * len(int_list)

    result = []
    for value in int_list:
        # to fix exact half rounding always up, add tiny value
        result.append(round(value / denominator * 100 + TINY_VALUE))

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
            resp_json = resp.json()
        except Exception:
            logger.error("Raportointipalvelu getting data from kayttooikeus-service: response not valid json.")
            return None, None

        if len(resp_json):
            resp_json = resp_json[0]
        else:
            logger.warning("Raportointipalvelu getting data from kayttooikeus-service: user have no permissions.")
            return None, None

        oid_henkilo = resp_json.get("oidHenkilo")
        organisaatiot = resp_json.get("organisaatiot")
        if oid_henkilo and organisaatiot is not None:
            org_perms = get_valssi_organisaatiot_permissions(resp_json["organisaatiot"])
            UserAuthorization.objects.filter(id=user_auth.id).update(
                oid=oid_henkilo, permissions=org_perms, updated_time=timezone.now())
            return oid_henkilo, org_perms
    else:
        logger.warning(f"Kayttooikeus-service read error, http status code: {resp.status_code}. Error: {resp.text}")

    return None, None


def get_permissions_for_user(username):
    resp = None
    try:
        resp = requests.get(
            f"{settings.KAYTTOOIKEUS_SERVICE_URL}kayttooikeus/kayttaja?username={username}",
            headers=get_authentication_header(settings.KAYTTOOIKEUS_SERVICE),
            timeout=settings.KAYTTOOIKEUS_SERVICE_TIMEOUT)
    except ReadTimeout:
        logger.warning("Kayttooikeus-service read timeout.")
    except Exception as e:
        logger.error(f"Kayttooikeus-service read error: {str(e)}")
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


def get_kysymysryhmas_with_closed_kyselys(organisation_oids: Set[str]) -> Tuple[QuerySet[Kysymysryhma], Set[int]]:
    kyselys = Kysely.objects.filter(
        Q(koulutustoimija__oid__in=organisation_oids) | Q(oppilaitos__oid__in=organisation_oids),
        voimassa_loppupvm__lt=timezone.now().date()
    ).prefetch_related(
        "kysymysryhmat"
    ).order_by("voimassa_loppupvm")
    kysymysryhma_objs = list(dict.fromkeys(kysely.kysymysryhmat.all()[0] for kysely in kyselys))
    kysymysryhma_ids = {obj.kysymysryhmaid for obj in kysymysryhma_objs}

    return kysymysryhma_objs, kysymysryhma_ids


def get_koulutustoimija_by_oid(oid: str) -> Organisaatio:
    koulutustoimija = Organisaatio.objects.filter(
        oid=oid, parent_oid__oid=OPETUSHALLITUS_OID).first()
    if koulutustoimija is None:
        raise NotFound([ErrorMessages.ER017.value])  # HTTP_404_NOT_FOUND
    return koulutustoimija


def get_parent_oids_by_oppilaitos_oids(oids: Set[str]) -> Set[str]:
    organisaatio_objs = Organisaatio.objects.filter(oid__in=oids) \
        .exclude(parent_oid__oid=OPETUSHALLITUS_OID)
    return {obj.parent_oid.oid for obj in organisaatio_objs}


def get_query_param_filters(query_params: dict, permission_level: str) -> dict:
    """Get filtered query parameters from a query dictionary."""
    job_title_code = query_params.get("job_title_code")
    eligibility = query_params.get("eligibility")
    aluejako = query_params.get("aluejako")
    kyselykerta_alkupvm = query_params.get("kyselykerta_alkupvm")
    language_codes = query_params.get("language_code")

    filter_dict = dict()

    if permission_level != VALSSI_TOTEUTTAJA_LEVEL:
        filter_dict["answer_filters"] = dict()
        if job_title_code:
            filter_dict["answer_filters"]["tehtavanimike_koodi"] = job_title_code

        if eligibility:
            filter_dict["answer_filters"]["kelpoisuus_kytkin"] = eligibility.lower() == "true"

        if aluejako:
            filter_dict["aluejako"] = parse_str_to_int(aluejako, default=None)

    if kyselykerta_alkupvm:
        filter_dict["kyselykerta_alkupvm"] = kyselykerta_alkupvm

    if language_codes:
        validated_language_codes = validate_report_filter_language_codes(language_codes.upper().split(","))
        filter_dict["language_codes"] = validated_language_codes

    return filter_dict


def validate_report_filter_language_codes(language_codes: List[str]) -> Set[str]:
    validated_language_codes = set()
    for language_code in language_codes:
        if language_code in REPORT_FILTER_LANGUAGE_CODES["all"]:
            validated_language_codes.add(language_code)
        else:
            logger.error(f"Report filter language code not allowed. ({language_code})")

    return validated_language_codes


def validate_language_code(language_code: str, is_limited_languages: bool = True):
    allowed_codes = LIMITED_LANGUAGE_CODES if is_limited_languages else ALLOWED_LANGUAGE_CODES
    if language_code not in allowed_codes:
        error = dict(ErrorMessages.ER013.value)
        error["description"] = error["description"].format(allowed_codes)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


def validate_language_code_by_kysymysryhma(language_code: str, kysymysryhma: Kysymysryhma):
    # Mandatory language codes are always valid
    if language_code in MANDATORY_LANGUAGE_CODES:
        pass
    elif language_code == "en" and not kysymysryhma.nimi_en:
        raise ValidationError([ErrorMessages.ER034.value])  # HTTP_400_BAD_REQUEST


def validate_yllapitaja_permission(henkilo_permissions: List[dict], allowed_oids: Set[str] = None):
    if allowed_oids is None:
        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, [VALSSI_YLLAPITAJA_LEVEL])
    if not any([org in allowed_oids for org in VALSSI_YLLAPITAJA_ORGANIZATION_OIDS]):
        raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN


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
    values = dict(fi=key, sv=key)

    localisations = Localisation.objects.filter(key=key)
    for loc in localisations:
        if loc.locale == "fi":
            values["fi"] = loc.value
        elif loc.locale == "sv":
            values["sv"] = loc.value

    return values


def get_laatutekija_by_kysymysryhma(kysymysryhma: Kysymysryhma):
    try:
        group_id = kysymysryhma.metatiedot.get("paaIndikaattori")["group"]
    except Exception:
        logger.error(f"Kysymysryhma ({kysymysryhma.pk}) paaIndikaattori group not found.")
        return None

    for laatutekija in LAATUTEKIJAS:
        if group_id in laatutekija["group_ids"]:
            return laatutekija["laatutekija"]
    logger.error(f"Kysymysryhma ({kysymysryhma.pk}) laatutekija not found.")
    return None


def parse_str_to_int(text: str, default: int = 0):
    try:
        return int(text)
    except Exception:
        pass
    return default
