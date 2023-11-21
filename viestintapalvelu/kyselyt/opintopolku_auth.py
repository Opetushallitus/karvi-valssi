import logging
import requests

from time import sleep
from urllib.parse import urlencode

from django.conf import settings
from rest_framework import status

from kyselyt.constants import OPINTOPOLKU_HEADERS, MAX_NO_OF_LOOPS
from kyselyt.models import OphAuthentication


logger = logging.getLogger(__name__)


def get_new_ticket_granting_ticket(username, password):
    if username is None or password is None:
        username = settings.OPINTOPOLKU_USERNAME
        password = settings.OPINTOPOLKU_PASSWORD

    credentials = urlencode({'username': username, 'password': password})

    headers = {'Content-Type': 'application/x-www-form-urlencoded', **OPINTOPOLKU_HEADERS}

    try:
        resp = requests.post(settings.OPINTOPOLKU_URL + '/cas/v1/tickets', data=credentials, headers=headers)
    except Exception as e:
        logger.error(f'Exception for /cas/v1/tickets. Error: {str(e)}')
        return None

    if resp.status_code == status.HTTP_201_CREATED:
        return resp.headers['Location']
    else:
        logger.warning(f'Error fetching tgt for user: {str(username)}. Status code: {resp.status_code}. {resp.content}')
        return None


def get_service_ticket(service_suffix, username, password):
    service_ticket_url = f'service={settings.OPINTOPOLKU_URL}/{service_suffix}'

    for i in range(MAX_NO_OF_LOOPS):
        headers = {'Content-Type': 'application/x-www-form-urlencoded', **OPINTOPOLKU_HEADERS}

        tgt = OphAuthentication.objects.order_by("id").first()
        if not tgt:
            tgt = OphAuthentication.objects.create(tgt="")

        ticket_granting_ticket_location = tgt.tgt
        if not ticket_granting_ticket_location.startswith('http'):
            ticket_granting_ticket_location = get_new_ticket_granting_ticket(username, password)

        if ticket_granting_ticket_location is None or not ticket_granting_ticket_location.startswith('http'):
            break

        try:
            resp = requests.post(
                ticket_granting_ticket_location, data=service_ticket_url, headers=headers)
        except Exception as e:
            logger.error(f'Exception for ticket_granting_ticket_location. Error: {str(e)}')
            sleep(2)
            continue

        if resp.status_code == status.HTTP_200_OK:
            tgt.tgt = ticket_granting_ticket_location
            tgt.save()
            return resp.content
        elif resp.status_code != status.HTTP_404_NOT_FOUND:
            logger.error(f'Could not get a TGT. Status: {resp.status_code}. {resp.content}.')

        # Probably TGT is unvalid. Clear the one in DB, and fetch a new one.
        tgt.tgt = ""
        tgt.save()

    logger.error(f'Error: Did not get a service ticket for user: {username}. TGT: {ticket_granting_ticket_location}')
    return ''


def get_authentication_header(service_name, username=None, password=None):
    service_ticket_url = get_service_ticket(service_name + '/j_spring_cas_security_check', username, password)
    return {'CasSecurityTicket': service_ticket_url, 'Content-Type': 'application/json', **OPINTOPOLKU_HEADERS}


def get_contenttype_header():
    return {'Content-Type': 'application/json', **OPINTOPOLKU_HEADERS}
