import enum

from typing import Dict


def get_error_dict(error_code: str, error_description: str) -> Dict:
    return {"error_code": error_code, "description": error_description}


class ErrorMessages(enum.Enum):
    """
    This enum contains all error messages. New errors should be added here.
    The code contains of a two-character prefix and a three-number code (e.g. XX000).
    """

    # General errors, prefix: ER
    ER001 = get_error_dict("ER001", "Problem getting henkilo oid and permissions.")
    ER002 = get_error_dict("ER002", "Kyselykerta not found.")
    ER003 = get_error_dict("ER003", "No YLLAPITAJA permission.")
    ER004 = get_error_dict("ER004", "No template helptext id found.")
    ER005 = get_error_dict("ER005", "Kysymysryhma does not exist.")
    ER006 = get_error_dict("ER006", "Question id of wrong type.")
    ER007 = get_error_dict("ER007", "Question does not exist.")
    ER008 = get_error_dict("ER008", "No permissions to Kyselykerta.")
    ER009 = get_error_dict("ER009", "Survey has less than {} answers and is not available.")
    ER010 = get_error_dict("ER010", "No access to Kysymysryhma.")
    ER011 = get_error_dict("ER011", "No permission to organisaatio.")
    ER012 = get_error_dict("ER012", "Only one summary allowed.")
    ER013 = get_error_dict("ER013", "Language code is not allowed. {}")
    ER014 = get_error_dict("ER014", "Summary not found.")
    ER015 = get_error_dict("ER015", "Summary is locked.")
    ER016 = get_error_dict("ER016", "Summary is not locked.")
    ER017 = get_error_dict("ER017", "Koulutustoimija not found.")
    ER018 = get_error_dict(
        "ER018", "There is no Kysely with given kysymysryhmaid, koulutustoimija and voimassa_alkupvm.")
    ER019 = get_error_dict("ER019", "Only one Result allowed.")
    ER020 = get_error_dict("ER020", "Result not found.")
    ER021 = get_error_dict("ER021", "Result is locked.")
    ER022 = get_error_dict("ER022", "Result is not locked.")
    ER023 = get_error_dict(
        "ER023", "There is no Kysely with given kysymysryhmaid, oppilaitos and voimassa_alkupvm.")
    ER024 = get_error_dict("ER024", "Kysely not found.")
    ER025 = get_error_dict("ER025", "Kysymysryhma not found.")
    ER026 = get_error_dict("ER026", "Problem getting impersonate user oid and permissions.")
    ER027 = get_error_dict("ER027", "lomaketyyppi not allowed.")
