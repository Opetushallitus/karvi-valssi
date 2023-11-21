import enum

from typing import Dict


def get_error_dict(error_code: str, error_description: str) -> Dict:
    return {"error_code": error_code, "description": error_description}


class ErrorMessages(enum.Enum):
    """
    This enum contains all error messages. New errors should be added here.
    The code contains of a two-character prefix and a three-number code (e.g. XX000).
    """

    # Dynamic errors, prefix: DY
    DY001 = get_error_dict("DY001", "Ensure the value is within the limits. [{}, {}]")
    DY002 = get_error_dict("DY002", "Ensure the language code is allowed. {}")

    # Arvo errors, prefix: AR
    AR001 = get_error_dict("AR001", "Vastaajatunnus not found.")
    AR002 = get_error_dict("AR002", "Vastaajatunnus is locked.")
    AR003 = get_error_dict("AR003", "Kyselykerta is locked.")
    AR004 = get_error_dict("AR004", "Vastaajatunnus is not yet valid.")
    AR005 = get_error_dict("AR005", "Vastaajatunnus is no longer valid.")
    AR006 = get_error_dict("AR006", "Vastaajatunnus kohteiden_lkm is not 1.")

    # Answer errors, prefix: AN
    AN001 = get_error_dict("AN001", "en_osaa_sanoa is not allowed.")
    AN002 = get_error_dict("AN002", "Only one type of answer is allowed.")
    AN003 = get_error_dict("AN003", "Ensure there is an answer.")
    AN004 = get_error_dict("AN004", "Ensure there is an answer for every mandatory question. (kysymysid: {})")
    AN005 = get_error_dict("AN005", "Ensure the answer count is allowed. ({})")
    AN006 = get_error_dict("AN006", "Ensure there is only answers related to this Kysely.")
    AN007 = get_error_dict("AN007", "Ensure the answer length is within limits. (max length {}")
    AN008 = get_error_dict("AN008", "Ensure there is no monivalinta answer duplicates.")
    AN009 = get_error_dict("AN009", "Ensure the answer type is allowed.")
    AN010 = get_error_dict("AN010", "Ensure the answer is numeric (integer/float).")
