import logging
import requests
import requests_pkcs12

from datetime import date, datetime, timedelta
from requests.exceptions import ReadTimeout
from typing import List, Any, Set

from django.conf import settings
from django.db.models.query import QuerySet
from django.utils import timezone

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import APIException, ValidationError, PermissionDenied

from virkailijapalvelu.celery import app as celery_app
from kyselyt.constants import (
    VALSSI_PERMISSION_LEVELS, VIESTINTAPALVELU_SETTINGS, SUCCESS_STATUSES, TEMPLATE_NO_ORIGINAL_SEND, EMAIL_STATUS_SENT,
    PDF_FILENAME_REPLACES, PDF_FILENAME_ALLOWED_CHARS, PDF_FILENAME_DEFAULT, VASTAAJATUNNUS_TAUSTATIEDOT_SETTINGS,
    ALLOWED_LANGUAGE_CODES, DATE_INPUT_FORMAT, VALSSI_YLLAPITAJA_LEVEL, VALSSI_YLLAPITAJA_ORGANIZATION_OIDS,
    DEFAULT_ORGANIZATION_YTUNNUS, USER_PERMISSIONS_RECHECK_TIME, HTML_ESCAPE_REPLACES, EMAIL_STATUS_FAILED,
    MAX_NO_OF_LOOPS)
from kyselyt.enums.error_messages import ErrorMessages
from kyselyt.models import (
    KyselySend, ExternalServices, Kyselykerta, KyselyKysymysryhma, Kysymysryhma, Organisaatio, Koodi, UserAuthorization)
from kyselyt.opintopolku_auth import get_authentication_header
from kyselyt.tokens import TOKENS


logger = logging.getLogger(__name__)


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
        logger.warning("Virkailijapalvelu not able to get henkilo oid and permissions.")
    elif resp.status_code in SUCCESS_STATUSES:
        # check response json validity
        try:
            resp_json = resp.json()[0]
        except Exception:
            logger.error("Virkailijapalvelu getting data from käyttöoikeus-service: response not valid json.")
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


def get_valssi_organisaatio_oids_by_permission_levels(permissions: List[dict], levels: List[str]) -> Set[str]:
    return {perm["organisaatioOid"] for level in levels
            for perm in permissions if level in perm["valssiPermissions"]}


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


def get_viestintapalvelu_access_token():
    token = TOKENS["viestintapalvelu"]
    palvelu = VIESTINTAPALVELU_SETTINGS

    if not token:
        resp = None
        try:
            resp = requests.post(
                f"{palvelu['url']}/api/v1/token/", data=palvelu["login_cred"], timeout=palvelu["timeout"])
        except ReadTimeout:
            logger.warning(f"{palvelu['name'].title()} login timeout.")
            return None
        except Exception as e:
            logger.error(f"{palvelu['name'].title()} login error: {str(e)}")
            return None

        if resp.status_code in SUCCESS_STATUSES and "access" in resp.json():
            token = resp.json()["access"]
            TOKENS["viestintapalvelu"] = token
            logger.info(f"{palvelu['name'].title()} access token updated.")
        else:
            logger.warning(
                f"{palvelu['name'].title()} login error, http status code: {resp.status_code}. Error: {resp.text}")

    return token


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


def fetch_vastaajatunnus_list(kyselykerta: int, kayttaja_oid: str, vastaajatunnus_count: int, object_count: int,
                              start_date: str, end_date: str) -> List[str]:
    data = {
        "tunnusten_lkm": vastaajatunnus_count, "kohteiden_lkm": object_count,
        "voimassa_alkupvm": start_date, "voimassa_loppupvm": end_date,
        "kayttaja_oid": kayttaja_oid,
        "taustatiedot": {}, "metatiedot": {}}

    for i in range(MAX_NO_OF_LOOPS):
        resp = request_service(
            "Arvo/vastaajatunnus", "post",
            f"{settings.ARVO_VASTAAJATUNNUS_ENDPOINT}{kyselykerta}",
            auth=(settings.ARVO_API_USERNAME, settings.ARVO_API_PASSWORD), json=data,
            timeout=settings.ARVO_TIMEOUT)

        if resp is None:
            pass
        elif resp.status_code in SUCCESS_STATUSES:
            vastaajatunnus_response = resp.json()
            return [vastaajatunnus["tunnus"] for vastaajatunnus in vastaajatunnus_response]
        else:
            logger.warning(
                f"Error getting vastaajatunnus list, http status code: {resp.status_code}. Error: {resp.text}")
    raise APIException([ErrorMessages.ER017.value])  # HTTP_500_INTERNAL_SERVER_ERROR


def validate_kyselysend_update_data(validated_data: list) -> QuerySet:
    kyselysend_ids = [msg["id"] for msg in validated_data]

    # validate there are no id duplicates
    if len(kyselysend_ids) != len(set(kyselysend_ids)):
        raise ValidationError([ErrorMessages.VA004.value])  # HTTP_400_BAD_REQUEST

    kyselysend_list = KyselySend.objects.filter(pk__in=kyselysend_ids)

    # validate that every id exists
    if len(kyselysend_ids) != kyselysend_list.count():
        raise ValidationError([ErrorMessages.VA003.value])  # HTTP_400_BAD_REQUEST

    # validate that every msg has same kyselykerta
    if len(set(kyselysend_list.values_list("kyselykerta", flat=True))) > 1:
        raise ValidationError([ErrorMessages.VA002.value])  # HTTP_400_BAD_REQUEST

    return kyselysend_list


def create_kyselysend_update_data(validated_data: list, kyselysend_list: QuerySet) -> List[dict]:
    tyontekija_data = []
    for msg in validated_data:
        kyselysend_item = kyselysend_list.get(id=msg["id"])
        tyontekija_data.append(
            dict(id=msg["id"],
                 email=msg["email"],
                 vastaajatunnus=kyselysend_item.vastaajatunnus,
                 template=TEMPLATE_NO_ORIGINAL_SEND,
                 kyselykerta=kyselysend_item.kyselykerta,
                 message=kyselysend_item.message))
    return tyontekija_data


def update_and_get_kyselykerta_kyselysend_statuses(kyselykerta: int) -> QuerySet:
    kyselysends = KyselySend.objects.filter(kyselykerta=kyselykerta).order_by("email", "msg_status", "id")
    kyselysends_dict = {kyselysend.msg_id: kyselysend for kyselysend in kyselysends}

    msg_ids_to_update = [
        kyselysend.msg_id for kyselysend in kyselysends
        if kyselysend.msg_status in (EMAIL_STATUS_SENT, EMAIL_STATUS_FAILED)]

    # return if there is no statuses to update
    if not msg_ids_to_update:
        return kyselysends

    for i in range(MAX_NO_OF_LOOPS):
        token = get_viestintapalvelu_access_token()
        if not token:
            continue

        resp = request_service(
            "Viestintapalvelu", "post",
            f"{settings.VIESTINTAPALVELU_URL}/api/v1/viestit/", token,
            data={"msg_ids": set(msg_ids_to_update)}, timeout=settings.VIESTINTAPALVELU_TIMEOUT)

        if resp is None:
            pass
        elif resp.status_code in SUCCESS_STATUSES:
            # update statuses in db
            messages = resp.json()
            objs_to_update = []
            for msg in messages:
                kyselysend = kyselysends_dict[msg["msg_id"]]
                kyselysend.msg_status = msg["msg_status"]
                objs_to_update.append(kyselysend)
            update_count = KyselySend.objects.bulk_update(objs_to_update, ["msg_status"])
            logger.info(f"Kyselysend msg statuses updated: {update_count}")
            return kyselysends
        elif resp.status_code == status.HTTP_401_UNAUTHORIZED:
            logger.info("Viestintapalvelu read: 401 Unauthorized.")
            TOKENS["viestintapalvelu"] = None
            logger.info("Viestintapalvelu expired access token removed.")
        else:
            logger.warning(f"Viestintapalvelu read error, http status code: {resp.status_code}. Error: {resp.text}")
    logger.error("Viestintapalvelu not able to send kyselysend-data.")
    return None


def update_kyselysends(kyselysend_list: QuerySet, messages: List[dict], updated_messages: List[dict]) -> int:
    objs_to_update = []
    for i, msg in enumerate(messages):
        kyselysend_item = kyselysend_list.get(id=msg["id"])
        kyselysend_item.email = msg["email"]
        kyselysend_item.msg_id = updated_messages[i]["msg_id"]
        kyselysend_item.msg_status = updated_messages[i]["msg_status"]
        objs_to_update.append(kyselysend_item)
    return KyselySend.objects.bulk_update(objs_to_update, ["email", "msg_id", "msg_status"])


def varda_client(address: str, authenticate: bool = False, headers: str = None) -> dict:
    response = None
    try:
        auth = (settings.VARDA_USERNAME, settings.VARDA_PASSWORD) if authenticate else None
        response = requests_pkcs12.get(
            address, headers=headers, auth=auth,
            timeout=settings.VARDA_TIMEOUT,
            pkcs12_filename=settings.VARDA_CERT_FILE,
            pkcs12_password=settings.VARDA_CERT_PASSWORD,
            verify=False)
    except ReadTimeout:
        logger.warning("Varda read timeout.")
    except Exception as e:
        logger.warning(f"Varda read error: {str(e)}")
    return response


def arvo_client(address, service_name, data):
    return request_service(
        service_name, "post", address,
        auth=(settings.ARVO_API_USERNAME, settings.ARVO_API_PASSWORD), json=data,
        timeout=settings.ARVO_TIMEOUT)


def get_or_create_external_services() -> ExternalServices:
    ext_services = ExternalServices.objects.order_by("id").first()
    if not ext_services:
        ext_services = ExternalServices.objects.create(
            oph_tgt="",
            varda_apikey="",
            varda_organisaatiot_last_update_time="",
            varda_toimipaikat_last_update_time="")
    return ext_services


def get_varda_apikey(refresh: bool = False) -> str:
    ext_services = get_or_create_external_services()

    if refresh:
        logger.info("Refresh Varda apikey.")
        ExternalServices.objects.filter(id=ext_services.id).update(varda_apikey="")
    elif ext_services.varda_apikey:
        return ext_services.varda_apikey

    logger.info("Request Varda apikey.")
    resp = varda_client(settings.VARDA_APIKEY_ENDPOINT, authenticate=True)

    if resp is None:
        pass
    elif resp.status_code in SUCCESS_STATUSES:
        new_apikey = resp.json().get("token")
        ExternalServices.objects.filter(id=ext_services.id).update(varda_apikey=new_apikey)
        return new_apikey
    else:
        logger.warning(
            f"Error getting Varda apikey, http status code: {resp.status_code}. Error: {resp.text}")
    raise APIException([ErrorMessages.ER018.value])  # HTTP_500_INTERNAL_SERVER_ERROR


def update_organizations(timenow: str = None, is_toimipaikat: bool = False) -> str:
    ext_services = get_or_create_external_services()

    if is_toimipaikat:
        address = settings.VARDA_TOIMIPAIKAT_ENDPOINT
        last_update_time = ext_services.varda_toimipaikat_last_update_time
        service = "toimipaikat update"
    else:
        address = settings.VARDA_ORGANISAATIOT_ENDPOINT
        last_update_time = ext_services.varda_organisaatiot_last_update_time
        service = "organisaatiot update"

    address += f"?page_size={settings.VARDA_ORG_COUNT_PER_REQUEST}"
    timenow = timenow if timenow else datetime.utcnow().isoformat() + "Z"

    if last_update_time:
        # changes from last update
        address += f"&datetime_gt={last_update_time}"
    else:
        # initial query if there is no previous update
        address += f"&datetime_lte={timenow}"

    # get updates from Varda
    update_datas = get_varda_updates(address, service)
    if update_datas is None:
        return f"Error in requesting Varda {service}."

    # post updates to Arvo
    for update_data in update_datas:
        update_succeeded = post_arvo_organisaatiot_update(update_data)
        if not update_succeeded:
            # return if updating organizations to Arvo fails
            return f"Error in updating Varda {service} data to Arvo."

    if is_toimipaikat:
        ExternalServices.objects.filter(id=ext_services.id).update(varda_toimipaikat_last_update_time=timenow)
    else:
        ExternalServices.objects.filter(id=ext_services.id).update(varda_organisaatiot_last_update_time=timenow)

    return "OK"


def get_varda_updates(address: str, service: str) -> List[List[dict]]:
    update_datas = []
    addr = address
    while addr:
        resp = request_varda_service(addr, service)
        if resp is not None:
            orgs = resp.json().get("results", [])
            update_datas.append(create_arvo_organizations_update_data(orgs))
            addr = resp.json().get("next", None)  # next address
            if addr is None:
                break
        else:
            # return None if requesting Varda fails
            return None
    return update_datas


def get_varda_organisaatio_taustatiedot(organisaatio_oid: str) -> dict:
    addr = settings.VARDA_TAUSTATIEDOT_ENDPOINT.format(organisaatio_oid)
    resp = request_varda_service(addr, "organisaatiot/taustatiedot")
    if resp is None:
        # return None if requesting Varda fails
        return None

    return resp.json()


def request_varda_service(address: str, service_name: str):
    logger.info(f"Requesting '{service_name}' data from Varda.")
    apikey = get_varda_apikey()

    for i in range(MAX_NO_OF_LOOPS):
        response = varda_client(address, headers={"Authorization": f"Token {apikey}"})

        if response is None:
            pass
        elif response.status_code in SUCCESS_STATUSES:
            return response
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            apikey = get_varda_apikey(refresh=True)
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            logger.warning(f"Error getting Varda {service_name}, http status code: 404 Not found.")
            return None
        else:
            logger.warning(
                f"Error getting Varda {service_name}, http status code: {response.status_code}. Error: {response.text}")

    return None


def create_arvo_organizations_update_data(organizations: List[dict]) -> List[dict]:
    update_data = []
    for org in organizations:
        if not org["organisaatio_oid"]:  # skip if organisaatio_oid is missing
            continue
        org_data = dict(
            oid=org["organisaatio_oid"],
            parentOid=org["parent_oid"],
            nimi=dict(fi=org["nimi"], sv=org["nimi"], en=org["nimi"]),
            yhteystiedot=[],
            tyypit=org["organisaatiotyyppi"],
            metatiedot={},
            ytunnus=DEFAULT_ORGANIZATION_YTUNNUS)
        if org.get("paattymis_pvm", ""):
            org_data["lakkautusPvm"] = org["paattymis_pvm"]
        if org.get("kunta_koodi", ""):
            org_data["kotipaikkaUri"] = org["kunta_koodi"]
        if org.get("postinumero", ""):
            org_data["postiosoite"] = dict(postinumeroUri=f"posti_{org['postinumero']}", osoite="", postitoimipaikka="")
        if org.get("jarjestamismuoto_koodi", ""):
            org_data["metatiedot"]["jarjestamismuoto_koodit"] = org["jarjestamismuoto_koodi"]
        if org.get("toimintamuoto_koodi", ""):
            org_data["metatiedot"]["toimintamuoto_koodi"] = org["toimintamuoto_koodi"]
        update_data.append(org_data)
    return update_data


def post_arvo_organisaatiot_update(data: List[dict]) -> bool:
    logger.info(f"Updating Arvo organisaatiot, count {len(data)}.")

    for i in range(MAX_NO_OF_LOOPS):
        response = arvo_client(settings.ARVO_ORGANISAATIOT_UPDATE_ENDPOINT, "Arvo organisaatiot update", data)

        if response is None:
            pass
        elif response.status_code in SUCCESS_STATUSES:
            return True
        else:
            logger.warning(
                f"Error updating Arvo organisaatiot, http status code: {response.status_code}. Error: {response.text}")
    return False


def get_varda_tyontekijat(toimipaikka: str, tyontekija_id: str = None) -> List[dict]:
    tyontekijat = []
    addr = settings.VARDA_TYONTEKIJAT_ENDPOINT.format(toimipaikka)
    addr += f"?page_size={settings.VARDA_TYONTEKIJA_COUNT_PER_REQUEST}"
    if tyontekija_id is not None:
        addr += f"&tyontekija_id={tyontekija_id}"
    while addr:
        resp = request_varda_service(addr, "tyontekijat")
        if resp is not None:
            results = resp.json().get("results", [])
            tyontekijat += results
            addr = resp.json().get("next", None)  # next address
            if addr is None:
                break
        else:
            # return None if requesting Varda fails
            return None
    return tyontekijat


def get_varda_tyontekija(toimipaikka_oid: str, tyontekija_id: int) -> dict:
    tyontekija_list = get_varda_tyontekijat(toimipaikka_oid, tyontekija_id)
    if tyontekija_list is None:
        raise APIException([ErrorMessages.ER005.value])  # HTTP_500_INTERNAL_SERVER_ERROR

    return get_varda_tyontekija_from_list(tyontekija_list, tyontekija_id)


def get_varda_tyontekija_from_list(tyontekija_list: List[dict], tyontekija_id: int) -> dict:
    return next(filter(lambda tyontekija: tyontekija["id"] == tyontekija_id, tyontekija_list), None)


def get_query_param_or_raise_error(query_params: Any, param: str):
    value = query_params.get(param, None)
    if not value:
        error = dict(ErrorMessages.VA001.value)
        error["description"] = error["description"].format(param)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST
    return value


def get_kyselykerta_or_raise_error(kyselykertaid: int) -> Kyselykerta:
    kyselykerta = Kyselykerta.objects.filter(kyselykertaid=kyselykertaid)
    if not kyselykerta.exists():
        raise ValidationError([ErrorMessages.ER006.value])  # HTTP_400_BAD_REQUEST
    return kyselykerta[0]


def add_data_to_tyontekija_list(tyontekijat: List[dict], vastaajatunnus_list: List[str], kyselykertaid: int,
                                message: str):
    for tyontekija, vastaajatunnus in zip(tyontekijat, vastaajatunnus_list):
        tyontekija["vastaajatunnus"] = vastaajatunnus
        tyontekija["template"] = TEMPLATE_NO_ORIGINAL_SEND
        tyontekija["kyselykerta"] = kyselykertaid
        tyontekija["message"] = message


def get_tyontekijat_by_toimipaikka(toimipaikka: str) -> List[dict]:
    tyontekijat_varda = get_varda_tyontekijat(toimipaikka)
    if tyontekijat_varda is None:
        raise APIException([ErrorMessages.ER005.value])  # HTTP_500_INTERNAL_SERVER_ERROR
    tyontekijat = [{
        "tyontekija_id": tyontekija["id"],
        "kutsumanimi": tyontekija["kutsumanimi"],
        "sukunimi": tyontekija["sukunimi"],
        "email": tyontekija["sahkopostiosoite"],
        "tehtavanimikkeet": tyontekija["tehtavanimikkeet"]}
        for tyontekija in tyontekijat_varda]

    # add tehtavanimike values
    code_values = get_varda_tehtavanimike_code_values()
    for tyontekija in tyontekijat:
        for tehtavanimike in tyontekija["tehtavanimikkeet"]:
            code = str(tehtavanimike["tehtavanimike_koodi"])
            tehtavanimike["tehtavanimike_values"] = code_values.get(code, dict(
                fi=dict(nimi=f"FI_{code}"), sv=dict(nimi=f"SV_{code}")))  # default if code missing in db

            # remove kelpoisuus_kytkin from listing
            if "kelpoisuus_kytkin" in tehtavanimike:
                tehtavanimike.pop("kelpoisuus_kytkin")

    return tyontekijat


def delete_outdated_kyselysends() -> int:
    # outdated Kyselykerta ids
    kyselykerta_ids = Kyselykerta.objects.filter(
        voimassa_loppupvm__lt=datetime.now().date()).values_list("kyselykertaid", flat=True)
    delete_count, _ = KyselySend.objects.filter(kyselykerta__in=set(kyselykerta_ids)).delete()
    return delete_count


def remove_email_duplicates_and_resends_from_tyontekija_list(tyontekijat: List[dict], kyselykertaid: int) -> List[dict]:
    # remove duplicate emails on list
    emails_already = set()
    tyontekijat_filtered = []
    for tyontekija in tyontekijat:
        if tyontekija["email"] not in emails_already:
            emails_already.add(tyontekija["email"])
            tyontekijat_filtered.append(tyontekija)

    # remove from list if already sent
    previously_sent_kyselysends = KyselySend.objects.filter(kyselykerta=kyselykertaid)
    previously_sent_emails = set(previously_sent_kyselysends.values_list("email", flat=True))
    return [tyontekija for tyontekija in tyontekijat_filtered if tyontekija["email"] not in previously_sent_emails]


def get_pdf_filenames_by_kyselykertaid(kyselykertaid: int) -> dict:
    kyselykerta = Kyselykerta.objects.get(kyselykertaid=kyselykertaid)
    kyselykysymysryhma = KyselyKysymysryhma.objects.filter(kyselyid=kyselykerta.kyselyid).first()
    if kyselykysymysryhma is not None:
        filenames = get_pdf_filenames_by_kysymysryhma(kyselykysymysryhma.kysymysryhmaid)
    else:
        filenames = get_pdf_filenames_by_kysymysryhma(None)
    return filenames


def get_pdf_filenames_by_kysymysryhma(kysymysryhma: Kysymysryhma) -> dict:
    if kysymysryhma is not None:
        if kysymysryhma.nimi_fi and kysymysryhma.nimi_sv:
            name_fi = create_pdf_filename(kysymysryhma.nimi_fi)
            name_sv = create_pdf_filename(kysymysryhma.nimi_sv)
        elif kysymysryhma.nimi_fi:
            name_fi = name_sv = create_pdf_filename(kysymysryhma.nimi_fi)
        elif kysymysryhma.nimi_sv:
            name_fi = name_sv = create_pdf_filename(kysymysryhma.nimi_sv)
        else:
            name_fi = name_sv = PDF_FILENAME_DEFAULT
    else:
        name_fi = name_sv = PDF_FILENAME_DEFAULT

    return dict(fi=f"FI_{name_fi}.pdf", sv=f"SV_{name_sv}.pdf")


def create_pdf_filename(name: str) -> str:
    mod_name = name

    # fixed replaces
    for repl in PDF_FILENAME_REPLACES:
        mod_name = mod_name.replace(repl[0], repl[1])

    # remove unallowed chars (replace with spaces)
    mod_name = "".join([char if char in PDF_FILENAME_ALLOWED_CHARS else " " for char in mod_name])

    # remove consecutive spaces
    while "  " in mod_name:
        mod_name = mod_name.replace("  ", " ")

    # remove ending space
    if mod_name.endswith(" "):
        mod_name = mod_name[:-1]

    # replace spaces with underlines
    mod_name = mod_name.replace(" ", "_")

    return mod_name


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
    logger.error("Virkailijapalvelu not able to get localisation-data.")
    return values


def validate_language_code(language_code: str):
    if language_code not in ALLOWED_LANGUAGE_CODES:
        error = dict(ErrorMessages.VA005.value)
        error["description"] = error["description"].format(ALLOWED_LANGUAGE_CODES)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


def get_lomaketyyppi_by_kyselykerta(kyselykerta: Kyselykerta) -> str:
    if (kysely_meta := kyselykerta.kyselyid.metatiedot) and (
            kysymysryhmaid := kysely_meta.get("valssi_kysymysryhma")) and (
            kysymysryhma := Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).first()) and (
            kysymysryhma.metatiedot):
        return kysymysryhma.metatiedot.get("lomaketyyppi", None)
    return None


def create_taustatiedot_data(kyselykerta: Kyselykerta, organisaatio_oid: str, toimipaikka_oid: str,
                             lomaketyyppi: str = None) -> dict:
    data = dict(organisaatio=None,
                rakennetekijalomake_data=None,
                taydennyskoulutukset=None,
                toimipaikka=None)

    lomaketyyppi = get_lomaketyyppi_by_kyselykerta(kyselykerta) if lomaketyyppi is None else lomaketyyppi
    settings = VASTAAJATUNNUS_TAUSTATIEDOT_SETTINGS.get(lomaketyyppi, None)
    if not settings:
        logger.error(f"Lomaketyyppi '{lomaketyyppi}' settings missing.")
        return data

    if settings["data_settings"]["organisaatio_data"]:
        organisaatio = Organisaatio.objects.filter(oid=organisaatio_oid).first()
        kunta_koodi = organisaatio.kunta if organisaatio else ""
        data["organisaatio"] = dict(
            organisaatio_oid=organisaatio_oid,
            kunta_koodi=kunta_koodi)

    if settings["data_settings"]["rakennetekija_data"] or settings["data_settings"]["taydennyskoulutus_data"]:
        org_taustatiedot = get_varda_organisaatio_taustatiedot(organisaatio_oid)

        if settings["data_settings"]["rakennetekija_data"]:
            data["rakennetekijalomake_data"] = dict(
                toimipaikat=org_taustatiedot["toimipaikat"],
                tyontekijat=org_taustatiedot["tyontekijat"],
                lapset_voimassa=org_taustatiedot["lapset_voimassa"]
            ) if org_taustatiedot else dict()

        if settings["data_settings"]["taydennyskoulutus_data"]:
            data["taydennyskoulutukset"] = org_taustatiedot["taydennyskoulutukset"] if org_taustatiedot else dict()

    if settings["data_settings"]["toimipaikka_data"] and toimipaikka_oid:
        toimipaikka = Organisaatio.objects.filter(oid=toimipaikka_oid).first()
        data["toimipaikka"] = dict(
            toimipaikka_oid=toimipaikka_oid,
            nimi=dict(fi=toimipaikka.nimi_fi, sv=toimipaikka.nimi_sv, en=toimipaikka.nimi_en),
            postinumero=toimipaikka.postinumero,
            jarjestamismuoto_koodit=toimipaikka.metatiedot.get("jarjestamismuoto_koodit", []),
            toimintamuoto_koodi=toimipaikka.metatiedot.get("toimintamuoto_koodi", "")
        ) if toimipaikka else dict()

    return data


def get_varda_tehtavanimike_code_values() -> dict:
    tehtavanimikkeet = dict()
    koodis = Koodi.objects.filter(koodisto_uri="vardatehtavanimike")
    for koodi in koodis:
        tehtavanimikkeet[koodi.koodi_arvo] = dict(fi=dict(nimi=koodi.nimi_fi), sv=dict(nimi=koodi.nimi_sv))
    return tehtavanimikkeet


def validate_extend_enddate(new_enddate: str, previous_enddate: date):
    # check the format
    try:
        new_enddate_date = datetime.strptime(new_enddate, DATE_INPUT_FORMAT).date()
    except Exception:
        error = dict(ErrorMessages.VA008.value)
        error["description"] = error["description"].format(DATE_INPUT_FORMAT)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST

    # check new enddate is not before previous enddate
    if previous_enddate and new_enddate_date < previous_enddate:
        error = dict(ErrorMessages.VA007.value)
        error["description"] = error["description"].format(previous_enddate)
        raise ValidationError([error])  # HTTP_400_BAD_REQUEST


def validate_yllapitaja_permission(henkilo_permissions: List[dict]):
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


def delete_userauths() -> int:
    delete_count, _ = UserAuthorization.objects.all().delete()
    return delete_count


def sanitize_string(string: str) -> str:
    if not isinstance(string, str):
        return string
    str_modified = string
    for esc_repl in HTML_ESCAPE_REPLACES:
        str_modified = str_modified.replace(esc_repl[0], esc_repl[1])
    return str_modified


def get_last_organizations_update_ago_hours(default_value: int = None) -> int:
    total_hours = default_value
    try:
        ext_services = get_or_create_external_services()
        last_update_time = datetime.fromisoformat(ext_services.varda_toimipaikat_last_update_time.split("Z")[0])
        time_now = datetime.utcnow()
        total_hours = int((time_now - last_update_time).total_seconds()) // 3600
    except Exception:
        pass
    return total_hours
