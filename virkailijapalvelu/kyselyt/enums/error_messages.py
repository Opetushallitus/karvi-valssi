import enum

from typing import Dict


def get_error_dict(error_code: str, error_description: str) -> Dict:
    return {"error_code": error_code, "description": error_description}


class ErrorMessages(enum.Enum):
    """
    This enum contains all error messages. New errors should be added here.
    The code contains of a two-character prefix and a three-number code (e.g. XX000).
    """

    # Validation errors, prefix: VA
    VA001 = get_error_dict("VA001", "Ensure there is '{}' query param.")
    VA002 = get_error_dict("VA002", "Only same kyselykerta is allowed.")
    VA003 = get_error_dict("VA003", "Only existing ids allowed.")
    VA004 = get_error_dict("VA004", "Id duplicates not allowed.")
    VA005 = get_error_dict("VA005", "Ensure the language code is allowed. {}")
    VA006 = get_error_dict("VA006", "Validity is out of kyselykerta's validity. [{}, {}]")
    VA007 = get_error_dict("VA007", "'voimassa_loppupvm' can't be earlier than before. ({})")
    VA008 = get_error_dict("VA008", "'voimassa_loppupvm' is in wrong format. ({})")
    VA009 = get_error_dict("VA009", "'voimassa_loppupvm' can't be earlier than 'voimassa_alkupvm'.")

    # General errors, prefix: ER
    ER001 = get_error_dict("ER001", "Problem getting henkilo oid and permissions.")
    ER002 = get_error_dict("ER002", "Henkilo don't have any permissions.")
    ER003 = get_error_dict("ER003", "Vastaajatunnus object not found.")
    ER004 = get_error_dict("ER004", "KyselySend object not found.")
    ER005 = get_error_dict("ER005", "Error getting tyontekija list from Varda.")
    ER006 = get_error_dict("ER006", "Kyselykerta not found.")
    ER007 = get_error_dict("ER007", "Tyontekija not found.")
    ER008 = get_error_dict("ER008", "KyselySend doesn't have 'tyontekija_id'")
    ER009 = get_error_dict("ER009", "Kysely related to vastaajatunnus doesn't have oppilaitos.")
    ER010 = get_error_dict("ER010", "No permission to organisaatio.")
    ER011 = get_error_dict("ER011", "No YLLAPITAJA permission.")
    ER012 = get_error_dict("ER012", "Field 'voimassa_loppupvm' is required.")
    ER013 = get_error_dict("ER013", "Error with Vastaajatunnus'.")
    ER014 = get_error_dict("ER014", "Error sending kyselyt to viestintapalvelu.")
    ER015 = get_error_dict("ER015", "Kyselykerta is locked.")
    ER016 = get_error_dict("ER016", "Kysymysryhma not found.")
    ER017 = get_error_dict("ER017", "Error getting vastaajatunnus list.")
    ER018 = get_error_dict("ER018", "Error getting Varda apikey.")
    ER019 = get_error_dict("ER019", "Error in setting jwt tokens.")
    ER020 = get_error_dict("ER020", "Problem getting impersonate user oid and permissions.")
    ER021 = get_error_dict("ER021", "Kysely not found.")
