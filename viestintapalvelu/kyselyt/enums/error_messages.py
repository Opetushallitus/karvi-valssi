import enum

from typing import Dict


def get_error_dict(error_code: str, error_description: str) -> Dict:
    return {'error_code': error_code, 'description': error_description}


class ErrorMessages(enum.Enum):
    """
    This enum contains all error messages. New errors should be added here.
    The code contains of a two-character prefix and a three-number code (e.g. XX000).
    """

    # Validation errors, prefix: VA
    VA001 = get_error_dict('VA001', 'Ensure vastaajatunnus length within limits. ({})')
    VA002 = get_error_dict('VA002', "Ensure there is 'msg_ids' query param.")
