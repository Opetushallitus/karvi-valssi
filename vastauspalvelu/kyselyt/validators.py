from typing import Dict, List

from django.utils import timezone
from rest_framework.exceptions import ValidationError, NotFound

from kyselyt.constants import NUMEROVALINTA_TYPES_AND_LIMITS
from kyselyt.enums.error_messages import ErrorMessages
from kyselyt.models import Vastaajatunnus, Kysymys


def validate_arvosana(arvosana: int, lower_limit: int, upper_limit: int):
    """
    Validate the numeric value is within limits
    """
    if lower_limit <= arvosana <= upper_limit:
        pass
    else:
        error = dict(ErrorMessages.DY001.value)
        error["description"] = error["description"].format(lower_limit, upper_limit)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


def validate_only_one_answer_type(data: Dict):
    """
    Validate that only (max) one answer type is given
    """
    type_count = 0
    if "string" in data and data["string"] is not None:
        type_count += 1
    if "numerovalinta" in data and str(data["numerovalinta"]).isnumeric():
        type_count += 1
    if "en_osaa_sanoa" in data and data["en_osaa_sanoa"]:
        type_count += 1

    if type_count > 1:
        raise ValidationError([ErrorMessages.AN002.value])  # HTTP_400_BAD_REQUEST


def validate_vastaajatunnus_tunnus(tunnus: str) -> Vastaajatunnus:
    # check the tunnus is valid
    vastaajatunnus = Vastaajatunnus.objects.filter(tunnus=tunnus)
    if vastaajatunnus:
        vastaajatunnus = vastaajatunnus[0]
    else:
        raise NotFound([ErrorMessages.AR001.value])  # HTTP_404_NOT_FOUND

    # check Vastaajatunnus isn't locked
    if vastaajatunnus.lukittu:
        raise ValidationError([ErrorMessages.AR002.value])  # HTTP_400_BAD_REQUEST

    # check Kyselykerta isn't locked
    if vastaajatunnus.kyselykertaid.lukittu:
        raise ValidationError([ErrorMessages.AR003.value])  # HTTP_400_BAD_REQUEST

    # check Vastaajatunnus is valid
    datenow = timezone.now().date()
    if vastaajatunnus.voimassa_alkupvm and datenow < vastaajatunnus.voimassa_alkupvm:
        raise ValidationError([ErrorMessages.AR004.value])  # HTTP_400_BAD_REQUEST
    if vastaajatunnus.voimassa_loppupvm and vastaajatunnus.voimassa_loppupvm < datenow:
        raise ValidationError([ErrorMessages.AR005.value])  # HTTP_400_BAD_REQUEST

    return vastaajatunnus


def validate_vastaajatunnus_kohteiden_lkm(vastaajatunnus: Vastaajatunnus):
    # check the tunnus is valid
    if vastaajatunnus.kohteiden_lkm != 1:
        raise ValidationError([ErrorMessages.AR006.value])  # HTTP_400_BAD_REQUEST
    return


def validate_eos_when_not_allowed(data: Dict, kysymys: Kysymys):
    """
    Validate that not eos when it's not allowed
    """
    if not kysymys.eos_vastaus_sallittu:
        if "en_osaa_sanoa" in data and data["en_osaa_sanoa"]:
            raise ValidationError([ErrorMessages.AN001.value])  # HTTP_400_BAD_REQUEST


def validate_numerovalinta_answer_types(data: Dict, kysymys: Kysymys):
    """
    Validate numerovalinta answer types
    """
    vastaustyyppi = kysymys.vastaustyyppi

    if "numerovalinta" not in data:
        raise ValidationError([ErrorMessages.AN003.value])  # HTTP_400_BAD_REQUEST
    elif not str(data["numerovalinta"]).isnumeric():
        raise ValidationError([ErrorMessages.AN003.value])  # HTTP_400_BAD_REQUEST
    elif vastaustyyppi == "monivalinta":
        vaihtoehto_upper = len(kysymys.metatiedot.get("vastausvaihtoehdot", []))
        validate_arvosana(data["numerovalinta"], 1, vaihtoehto_upper)
    else:
        for nv in NUMEROVALINTA_TYPES_AND_LIMITS:
            if vastaustyyppi == nv["vastaustyyppi"]:
                validate_arvosana(data["numerovalinta"], nv["lower"], nv["upper"])


def validate_string_answer_types(data: Dict, kysymys: Kysymys):
    """
    Validate string answer types
    """
    if "string" not in data:
        raise ValidationError([ErrorMessages.AN003.value])  # HTTP_400_BAD_REQUEST
    elif kysymys.pakollinen and not data["string"]:
        error = dict(ErrorMessages.AN004.value)
        error["description"] = error["description"].format(kysymys.kysymysid)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST
    elif isinstance(kysymys.metatiedot, dict) and kysymys.metatiedot.get("numeric", False) and len(data["string"]):
        try:
            float(data["string"])
        except Exception:
            raise ValidationError([ErrorMessages.AN010.value])  # HTTP_400_BAD_REQUEST

    max_vastaus_length = kysymys.max_vastaus
    if max_vastaus_length and len(data["string"]) > max_vastaus_length:
        error = dict(ErrorMessages.AN007.value)
        error["description"] = error["description"].format(max_vastaus_length)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


def validate_answers_for_mandatory_questions(data: Dict, kysymykset_list: List):
    """
    Validate there is answer for every mandatory question
    """
    not_answered_ids = []
    for kysymys in kysymykset_list:
        answered = False
        for vastaus in data["vastaukset"]:
            if vastaus["kysymysid"] == kysymys.kysymysid:
                answered = True
                break
        if kysymys.pakollinen and not answered:
            not_answered_ids.append(kysymys.kysymysid)
    if not_answered_ids:
        error = dict(ErrorMessages.AN004.value)
        error["description"] = error["description"].format(not_answered_ids)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


def validate_answer_counts(data: Dict, kysymykset_list: List):
    """
    Validate there is allowed answer count for every question
    """
    for kysymys in kysymykset_list:
        if kysymys.vastaustyyppi == "monivalinta":
            if kysymys.monivalinta_max:
                max_answer_count = kysymys.monivalinta_max
            elif kysymys.metatiedot.get("type", "") == "radiobutton":
                max_answer_count = 1
            else:
                max_answer_count = None
        else:
            max_answer_count = 1

        vaihtoehto_set = set()
        answer_count = 0
        for vastaus in data["vastaukset"]:
            if vastaus["kysymysid"] == kysymys.kysymysid:
                answer_count += 1
                if max_answer_count and answer_count > max_answer_count:
                    error = dict(ErrorMessages.AN005.value)
                    error["description"] = error["description"].format(max_answer_count)
                    raise ValidationError([error])  # HTTP_400_BAD_REQUEST

                # check if there is monivalinta answer duplicates
                if kysymys.vastaustyyppi == "monivalinta":
                    if str(vastaus["numerovalinta"]) in vaihtoehto_set:
                        raise ValidationError([ErrorMessages.AN008.value])  # HTTP_400_BAD_REQUEST
                    else:
                        vaihtoehto_set.add(str(vastaus["numerovalinta"]))
