import base64
import logging

from datetime import datetime

import django_cas_ng.signals
import django_cas_ng.views
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, NotFound, PermissionDenied, ValidationError
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from kyselyt.constants import (
    VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL, VALSSI_YLLAPITAJA_LEVEL,
    VALSSI_YLLAPITAJA_ORGANIZATION_OIDS, VALSSI_VERSION, TILAENUM_PUBLISHED, TILAENUM_ARCHIVED, TILAENUM_LOCKED,
    VARDA_ORG_LAST_UPDATE_DEADLINE_FOR_ERROR, DATE_INPUT_FORMAT, UI_LOG_CHAR_LIMIT, SERVICE_USER_GROUP,
)
from kyselyt.decorators import RATELIMIT_DECORATORS, CSRF_DECORATORS
from kyselyt.enums.error_messages import ErrorMessages
from kyselyt.models import (
    Indikaattori, Kayttaja, Kysely, Kyselykerta, KyselySend, Kysymysryhma, Scale, Vastaajatunnus, TilaEnum,
    MalfunctionMessage, Localisation)
from kyselyt.permissions import ServiceUserAccessPermission
from kyselyt.serializers import (
    IndikaattoriSerializer, KyselykertaTyontekijatPostSerializer, KyselySendListSerializer, KyselySendUpdateSerializer,
    KysymysryhmaOrganisaatioSerializer, ScaleSerializer, MalfunctionMessageSerializer, AluejakoAluePostSerializer,
    AluejakoAlueDeleteSerializer, AluejakoAluePutSerializer)
from kyselyt.utils import (
    add_data_to_tyontekija_list, add_token_to_blacklist, create_kyselysend_update_data, create_taustatiedot_data,
    fetch_vastaajatunnus_list, get_henkilo_oid_and_permissions, get_kyselykerta_or_raise_error,
    get_pdf_filenames_by_kysymysryhma, get_query_param_or_raise_error, get_tokens_for_user,
    get_tyontekijat_by_toimipaikka,
    get_valssi_organisaatio_oids_by_permission_levels, get_varda_tyontekija,
    remove_email_duplicates_and_resends_from_tyontekija_list, update_and_get_kyselykerta_kyselysend_statuses,
    update_kyselysends, validate_kyselysend_update_data, validate_language_code,
    validate_extend_enddate, validate_yllapitaja_permission, check_celery_worker_running,
    get_ci_pipeline_number, sanitize_string, get_last_organizations_update_ago_hours, create_kyselysend_reminder_data,
    get_aluejako_alueet, flush_oppilaitoses_aluejako, set_oppilaitoses_aluejako, check_and_fix_aluejako_oppilaitoses,
    validate_language_code_by_kysymysryhma, check_yllapitaja_permission, check_paakayttaja_permission,
    check_toteuttaja_permission,
)
from kyselyt.utils_pdf import create_kysely_pdf, post_kyselyt_to_viestintapalvelu


logger = logging.getLogger(__name__)


class RootView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Virkailijapalvelu")


class TyontekijaViewSet(GenericViewSet, RetrieveModelMixin):
    permission_classes = (IsAuthenticated, ServiceUserAccessPermission)
    valssi_permission_levels = [VALSSI_TOTEUTTAJA_LEVEL]

    def authorization(self, organisaatio_list):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # to impersonate other user, check current user have YLLAPITAJA permission
        impersonate_user = self.request.headers.get("Impersonate-User", None)
        if impersonate_user:
            validate_yllapitaja_permission(henkilo_permissions)
            impersonate_user_oid, impersonate_user_permissions = get_henkilo_oid_and_permissions(impersonate_user)
            if not impersonate_user_oid:
                raise PermissionDenied([ErrorMessages.ER020.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, self.valssi_permission_levels)
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN

    def retrieve(self, request, pk=None):
        vastaajatunnus_objs = Vastaajatunnus.objects.filter(tunnus=pk, kohteiden_lkm=1)
        if not vastaajatunnus_objs.exists():
            raise NotFound([ErrorMessages.ER003.value])  # HTTP_404_NOT_FOUND

        kyselysends = KyselySend.objects.filter(vastaajatunnus=pk)
        if kyselysends.count() != 1:
            logger.error(f"KyselySend not found. (vastaajatunnus {pk})")
            raise APIException([ErrorMessages.ER004.value])  # HTTP_500_INTERNAL_SERVER_ERROR

        tyontekija_id = kyselysends[0].tyontekija_id
        if not tyontekija_id:
            raise NotFound([ErrorMessages.ER008.value])  # HTTP_404_NOT_FOUND

        if not vastaajatunnus_objs[0].kyselykertaid.kyselyid.oppilaitos:
            raise NotFound([ErrorMessages.ER009.value])  # HTTP_404_NOT_FOUND
        toimipaikka_oid = vastaajatunnus_objs[0].kyselykertaid.kyselyid.oppilaitos.oid

        tyontekija = get_varda_tyontekija(toimipaikka_oid, tyontekija_id)
        if tyontekija is None:
            raise NotFound([ErrorMessages.ER007.value])  # HTTP_404_NOT_FOUND

        data = {"tehtavanimikkeet": tyontekija["tehtavanimikkeet"], "tutkinnot": tyontekija["tutkinnot"]}

        return Response(data)  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"list/toimipaikka=(?P<toimipaikka>[0-9.]+)", methods=["get"], detail=False)
    def listing(self, request, toimipaikka):
        self.authorization([toimipaikka])

        tyontekija_list = get_tyontekijat_by_toimipaikka(toimipaikka)
        return Response(tyontekija_list)  # HTTP_200_OK


class KyselySendViewSet(GenericViewSet):
    serializer_class = KyselykertaTyontekijatPostSerializer
    permission_classes = (IsAuthenticated, )
    valssi_permission_levels = [VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL]

    def authorization(self, kyselykertaid):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # to impersonate organization or other user, check current user have YLLAPITAJA permission
        impersonate_org = self.request.headers.get("Impersonate-Organization", None)
        impersonate_user = self.request.headers.get("Impersonate-User", None)
        if impersonate_org:
            validate_yllapitaja_permission(henkilo_permissions)
        elif impersonate_user:
            validate_yllapitaja_permission(henkilo_permissions)
            impersonate_user_oid, impersonate_user_permissions = get_henkilo_oid_and_permissions(impersonate_user)
            if not impersonate_user_oid:
                raise PermissionDenied([ErrorMessages.ER020.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        kyselykerta = get_kyselykerta_or_raise_error(kyselykertaid)
        koulutustoimija_oid = kyselykerta.kyselyid.koulutustoimija.oid if kyselykerta.kyselyid.koulutustoimija else None
        oppilaitos_oid = kyselykerta.kyselyid.oppilaitos.oid if kyselykerta.kyselyid.oppilaitos else None

        # when impersonating organization, check the oid is correct with kyselykerta
        if impersonate_org and koulutustoimija_oid:
            if impersonate_org == koulutustoimija_oid:
                return henkilo_oid, koulutustoimija_oid, oppilaitos_oid, kyselykerta

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, self.valssi_permission_levels)
        if koulutustoimija_oid not in allowed_oids and oppilaitos_oid not in allowed_oids:
            raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN
        return henkilo_oid, koulutustoimija_oid, oppilaitos_oid, kyselykerta

    @method_decorator(CSRF_DECORATORS)
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        kyselykertaid = serializer.validated_data["kyselykerta"]
        tyontekijat_input = serializer.validated_data["tyontekijat"]
        if len(tyontekijat_input) == 0:
            return Response({"created": 0}, status=status.HTTP_201_CREATED)

        henkilo_oid, koulutustoimija_oid, oppilaitos_oid, kyselykerta = self.authorization(kyselykertaid)

        # check email duplicates and if email has already sent to tyontekija
        tyontekijat = remove_email_duplicates_and_resends_from_tyontekija_list(tyontekijat_input, kyselykertaid)
        if len(tyontekijat) == 0:
            return Response({"created": 0}, status=status.HTTP_201_CREATED)

        # create vastaajatunnus for every tyontekija
        vastaajatunnukset = fetch_vastaajatunnus_list(
            kyselykertaid, henkilo_oid, len(tyontekijat), 1, str(serializer.validated_data["voimassa_alkupvm"]),
            str(serializer.validated_data["voimassa_loppupvm"]))

        # sanitize message
        sanitized_msg = sanitize_string(str(serializer.validated_data["message"]))

        # add data to tyontekija list
        end_date = str(serializer.validated_data["voimassa_loppupvm"])
        add_data_to_tyontekija_list(
            tyontekijat, vastaajatunnukset, kyselykertaid, sanitized_msg, end_date)

        # send kyselyt to viestintapalvelu
        viestintapalvelu_response = post_kyselyt_to_viestintapalvelu(kyselykertaid, tyontekijat)
        if viestintapalvelu_response is None:
            raise APIException([ErrorMessages.ER014.value])  # HTTP_500_INTERNAL_SERVER_ERROR

        # add msg data from response to data
        for i, tyontekija in enumerate(tyontekijat):
            tyontekija["msg_id"] = viestintapalvelu_response[i]["msg_id"]
            tyontekija["msg_status"] = viestintapalvelu_response[i]["msg_status"]

        # add background info (taustatiedot) to Kyselykerta' metatiedot (if not already)
        if not kyselykerta.metatiedot or not kyselykerta.metatiedot.get("organisaatio"):
            kyselykerta.metatiedot = create_taustatiedot_data(kyselykerta, koulutustoimija_oid, oppilaitos_oid)
            kyselykerta.save()

        serializer.validated_data["tyontekijat"] = tyontekijat
        serializer.save()
        return Response({"created": len(tyontekijat)}, status=status.HTTP_201_CREATED)

    @method_decorator(CSRF_DECORATORS)
    @action(detail=False, url_path=r"list", methods=["post"])
    def listing(self, request):
        kyselykertaid = get_query_param_or_raise_error(self.request.query_params, "kyselykerta")

        self.authorization(kyselykertaid)

        kyselysend_list = update_and_get_kyselykerta_kyselysend_statuses(kyselykertaid)
        kyselysend_list_ser = KyselySendListSerializer(kyselysend_list, many=True)
        return Response(kyselysend_list_ser.data)  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(detail=False, url_path=r"update", methods=["put"])
    def updating(self, request):
        serializer = KyselySendUpdateSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        # return if no data
        if not serializer.validated_data:
            return Response({"updates": 0})  # HTTP_200_OK

        # validation (no id duplicates, every id exists, every msg has same kyselykerta)
        validated_data = serializer.validated_data
        kyselysend_list = validate_kyselysend_update_data(validated_data)

        if not kyselysend_list.exists():
            return Response({"updates": 0})  # HTTP_200_OK

        kyselykertaid = kyselysend_list[0].kyselykerta

        self.authorization(kyselykertaid)

        kyselykerta = get_kyselykerta_or_raise_error(kyselykertaid)
        end_date = kyselykerta.kyselyid.voimassa_loppupvm.strftime(DATE_INPUT_FORMAT)

        messages_data = create_kyselysend_update_data(validated_data, kyselysend_list, end_date)
        viestintapalvelu_response = post_kyselyt_to_viestintapalvelu(kyselykertaid, messages_data)
        if viestintapalvelu_response is None:
            raise APIException([ErrorMessages.ER014.value])  # HTTP_500_INTERNAL_SERVER_ERROR

        update_count = update_kyselysends(kyselysend_list, messages_data, viestintapalvelu_response)

        return Response({"updates": update_count})  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(detail=False, url_path=r"reminder", methods=["put"])
    def reminder_send(self, request):
        kyselykertaid = get_query_param_or_raise_error(self.request.query_params, "kyselykerta")
        self.authorization(kyselykertaid)

        kyselykerta = get_kyselykerta_or_raise_error(kyselykertaid)
        end_date = kyselykerta.kyselyid.voimassa_loppupvm.strftime(DATE_INPUT_FORMAT)

        active_vastaajatunnuses = Vastaajatunnus.objects.filter(kyselykertaid=kyselykerta, lukittu=False)

        if not active_vastaajatunnuses.exists():
            return Response({"updates": 0})  # HTTP_200_OK

        active_tunnuses = [vastaajatunnus.tunnus for vastaajatunnus in active_vastaajatunnuses]

        kyselysend_list = KyselySend.objects.filter(vastaajatunnus__in=active_tunnuses)

        messages_data = create_kyselysend_reminder_data(kyselysend_list, end_date)
        viestintapalvelu_response = post_kyselyt_to_viestintapalvelu(kyselykertaid, messages_data)
        if viestintapalvelu_response is None:
            raise APIException([ErrorMessages.ER014.value])  # HTTP_500_INTERNAL_SERVER_ERROR

        update_count = update_kyselysends(kyselysend_list, messages_data, viestintapalvelu_response)

        return Response({"updates": update_count})  # HTTP_200_OK


class IndikaattoriViewSet(GenericViewSet, ListModelMixin):
    serializer_class = IndikaattoriSerializer
    queryset = Indikaattori.objects.all()

    def get_queryset(self):
        laatutekija = self.request.query_params.get("laatutekija", None)
        group_id = self.request.query_params.get("group_id", None)

        indikaattorit = Indikaattori.objects.filter(is_visible=True).order_by("group_id")
        if laatutekija:
            indikaattorit = indikaattorit.filter(laatutekija=laatutekija)
        if group_id:
            indikaattorit = indikaattorit.filter(group_id=group_id)

        return indikaattorit

    @action(detail=False, url_path=r"grouped")
    def grouped_indicators(self, request):
        indikaattorit = self.get_queryset()
        group_ids = sorted(list(set(indikaattorit.values_list("group_id", flat=True))))

        response_data = [dict(
            group_id=gid,
            indicators=[
                dict(
                    group_id=ind.group_id, key=ind.indicator_key,
                    laatutekija=ind.laatutekija) for ind in indikaattorit.filter(group_id=gid)]) for gid in group_ids]

        return Response(response_data)  # HTTP_200_OK


class KyselykertaViewSet(GenericViewSet):
    permission_classes = (IsAuthenticated, )
    valssi_permission_levels = [VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_TOTEUTTAJA_LEVEL]

    def authorization(self, organisaatio_list, is_multi=False):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # to impersonate organization or other user, check current user have YLLAPITAJA permission
        impersonate_org = self.request.headers.get("Impersonate-Organization", None)
        impersonate_user = self.request.headers.get("Impersonate-User", None)
        if impersonate_org:
            validate_yllapitaja_permission(henkilo_permissions)
            return  # no need to check org-permissions
        elif impersonate_user:
            validate_yllapitaja_permission(henkilo_permissions)
            impersonate_user_oid, impersonate_user_permissions = get_henkilo_oid_and_permissions(impersonate_user)
            if not impersonate_user_oid:
                raise PermissionDenied([ErrorMessages.ER020.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, self.valssi_permission_levels)
        if not is_multi and not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN
        elif is_multi and not all([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"active/kysymysryhma=(?P<kysymysryhmaid>[0-9]+)/organisaatio=(?P<organisaatio>[0-9.]+)",
            detail=False)
    def kyselykerta_by_kysymysryhmaid(self, request, kysymysryhmaid, organisaatio):
        self.authorization([organisaatio])

        active_kyselykerta = Kyselykerta.objects.filter(
            Q(kyselyid__koulutustoimija__oid=organisaatio) | Q(kyselyid__oppilaitos__oid=organisaatio),
            kyselyid__kysely__kysymysryhmaid__kysymysryhmaid=kysymysryhmaid,
            voimassa_loppupvm__gte=datetime.now().date()).order_by("voimassa_alkupvm").last()
        if not active_kyselykerta:
            return Response([])  # HTTP_200_OK
        kyselykerta_data = dict(
            kyselykertaid=active_kyselykerta.kyselykertaid,
            kyselyid=active_kyselykerta.kyselyid.kyselyid,
            voimassa_alkupvm=active_kyselykerta.voimassa_alkupvm,
            voimassa_loppupvm=active_kyselykerta.voimassa_loppupvm,
            last_kyselysend=None)

        # get message from previous KyselySend (of this kyselykerta)
        last_kyselysend = KyselySend.objects.filter(kyselykerta=active_kyselykerta.kyselykertaid).order_by("id").last()
        if last_kyselysend:
            kyselykerta_data["last_kyselysend"] = dict(
                message=last_kyselysend.message,
                vastaajatunnus=None)
            vastaajatunnus = Vastaajatunnus.objects.filter(tunnus=last_kyselysend.vastaajatunnus).first()
            if vastaajatunnus:
                kyselykerta_data["last_kyselysend"]["vastaajatunnus"] = dict(
                    voimassa_alkupvm=vastaajatunnus.voimassa_alkupvm,
                    voimassa_loppupvm=vastaajatunnus.voimassa_loppupvm)

        return Response([kyselykerta_data])  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"active/multi", detail=False, methods=["post"])
    def kyselykerta_by_kysymysryhmaid_multi(self, request):
        serializer = KysymysryhmaOrganisaatioSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        # check user have permission to every organization
        organizations = [data_item["organisaatio"] for data_item in validated_data]
        self.authorization(organizations, is_multi=True)
        kysymysryhmaids = [data_item["kysymysryhmaid"] for data_item in validated_data]

        active_kyselykertas = Kyselykerta.objects.filter(
            Q(kyselyid__koulutustoimija__oid__in=organizations) | Q(kyselyid__oppilaitos__oid__in=organizations),
            kyselyid__kysely__kysymysryhmaid__kysymysryhmaid__in=kysymysryhmaids,
            voimassa_loppupvm__gte=datetime.now().date()
        ).select_related(
            "kyselyid__koulutustoimija", "kyselyid__oppilaitos"
        ).prefetch_related(
            "kyselyid__kysely__kysymysryhmaid"
        ).order_by("-voimassa_alkupvm")

        active_kyselykerta_dicts = [
            dict(
                kyselykertaid=active_kyselykerta.kyselykertaid,
                kyselyid=active_kyselykerta.kyselyid.kyselyid,
                voimassa_alkupvm=active_kyselykerta.voimassa_alkupvm,
                voimassa_loppupvm=active_kyselykerta.voimassa_loppupvm,
                kyselyid_koulutustoimija_oid=active_kyselykerta.kyselyid.koulutustoimija.oid,
                kyselyid_oppilaitos_oid=(
                    active_kyselykerta.kyselyid.oppilaitos.oid
                    if active_kyselykerta.kyselyid.oppilaitos else None
                ),
                kyselyid_kysymysryhmaids=[
                    kysely_kysymysryhma.kysymysryhmaid.kysymysryhmaid
                    for kysely_kysymysryhma in active_kyselykerta.kyselyid.kysely.all()
                ]
            )
            for active_kyselykerta in active_kyselykertas
        ]

        # add kyselykerta data to response
        kyselykerta_datas = []
        for data_item in validated_data:
            # get active kyselykerta for every kysymysryhma/organization pair
            active_kyselykerta = next(
                (active_kyselykerta_dict for active_kyselykerta_dict in active_kyselykerta_dicts
                    if (active_kyselykerta_dict["kyselyid_koulutustoimija_oid"] == data_item["organisaatio"] or
                        active_kyselykerta_dict["kyselyid_oppilaitos_oid"] == data_item["organisaatio"]) and
                    data_item["kysymysryhmaid"] in active_kyselykerta_dict["kyselyid_kysymysryhmaids"]), None)
            kyselykerta_datas += [dict(
                kysymysryhmaid=data_item["kysymysryhmaid"],
                kyselykertaid=active_kyselykerta["kyselykertaid"],
                kyselyid=active_kyselykerta["kyselyid"],
                voimassa_alkupvm=active_kyselykerta["voimassa_alkupvm"],
                voimassa_loppupvm=active_kyselykerta["voimassa_loppupvm"],
                last_kyselysend=None)] if active_kyselykerta else [dict()]

        # add last messages to response
        kyselykertaids = [kyselykerta["kyselykertaid"] for kyselykerta in kyselykerta_datas if kyselykerta]
        kyselysend_dicts = list(KyselySend.objects.filter(kyselykerta__in=kyselykertaids).order_by("-id").values())
        vastaajatunnus_list = []
        last_kyselysends = []
        for kyselykerta_data in kyselykerta_datas:
            if not kyselykerta_data:
                last_kyselysends.append(None)
                continue

            # get message from previous KyselySend (of this kyselykerta)
            last_kyselysend = next(
                (kyselysend_dict for kyselysend_dict in kyselysend_dicts
                    if kyselysend_dict["kyselykerta"] == kyselykerta_data["kyselykertaid"]), None)
            if last_kyselysend:
                kyselykerta_data["last_kyselysend"] = dict(
                    message=last_kyselysend["message"],
                    vastaajatunnus=None)
                vastaajatunnus_list.append(last_kyselysend["vastaajatunnus"])
            last_kyselysends.append(last_kyselysend)

        # add vastaajatunnus data to response
        vastaajatunnus_dicts = list(Vastaajatunnus.objects.filter(tunnus__in=vastaajatunnus_list).values(
            "tunnus", "voimassa_alkupvm", "voimassa_loppupvm"))
        for kyselykerta_data, last_kyselysend in zip(kyselykerta_datas, last_kyselysends):
            if last_kyselysend:
                vastaajatunnus = next(
                    (vastaajatunnus_dict for vastaajatunnus_dict in vastaajatunnus_dicts
                        if vastaajatunnus_dict["tunnus"] == last_kyselysend["vastaajatunnus"]), None)
                if vastaajatunnus:
                    kyselykerta_data["last_kyselysend"]["vastaajatunnus"] = dict(
                        voimassa_alkupvm=vastaajatunnus["voimassa_alkupvm"],
                        voimassa_loppupvm=vastaajatunnus["voimassa_loppupvm"])

        return Response(kyselykerta_datas)  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"extend-enddate/kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija>[0-9.]+)/"
            r"alkupvm=(?P<kysely_voimassa_alkupvm>[0-9-]+)", detail=False, methods=["patch"])
    def extend_enddates_by_kyselydata(self, request, kysymysryhmaid, koulutustoimija, kysely_voimassa_alkupvm):
        # check Kysymysryhma
        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).first()
        if kysymysryhma is None:
            raise NotFound([ErrorMessages.ER016.value])  # HTTP_404_NOT_FOUND

        # check permission
        self.authorization([koulutustoimija])

        kyselys = Kysely.objects.filter(
            kysymysryhmat__kysymysryhmaid=kysymysryhmaid,
            koulutustoimija__oid=koulutustoimija,
            voimassa_alkupvm=kysely_voimassa_alkupvm,
            voimassa_loppupvm__gte=datetime.now().date())
        if kyselys.first() is None:
            raise NotFound([ErrorMessages.ER021.value])  # HTTP_404_NOT_FOUND

        # validate new voimassa_loppupvm
        new_voimassa_loppupvm = request.data.get("voimassa_loppupvm", None)
        if new_voimassa_loppupvm is None:
            raise ValidationError([ErrorMessages.ER012.value])  # HTTP_400_BAD_REQUEST
        validate_extend_enddate(new_voimassa_loppupvm, kyselys.first().voimassa_alkupvm)

        kyselykertas = Kyselykerta.objects.filter(kyselyid__in=kyselys)
        vastaajatunnuses = Vastaajatunnus.objects.filter(kyselykertaid__in=kyselykertas)

        # update voimassa_loppupvm
        update_count_kysely = kyselys.update(
            voimassa_loppupvm=new_voimassa_loppupvm, muutettuaika=timezone.now())
        update_count_kyselykerta = kyselykertas.update(
            voimassa_loppupvm=new_voimassa_loppupvm, muutettuaika=timezone.now())
        update_count_vastaajatunnus = vastaajatunnuses.update(
            voimassa_loppupvm=new_voimassa_loppupvm, muutettuaika=timezone.now())

        return Response({
            "updates_kysely": update_count_kysely,
            "updates_kyselykerta": update_count_kyselykerta,
            "updates_vastaajatunnus": update_count_vastaajatunnus})  # HTTP_200_OK


class KysymysryhmaViewSet(GenericViewSet):
    permission_classes = (IsAuthenticated, )
    valssi_permission_levels = [VALSSI_YLLAPITAJA_LEVEL]

    def authorization(self, organisaatio_list):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, self.valssi_permission_levels)
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"(?P<kysymysryhmaid>[0-9]+)/used", detail=False)
    def kysymysryhma_used(self, request, kysymysryhmaid):
        self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        kysely_objs = Kysely.objects.filter(
            kysely__kysymysryhmaid__kysymysryhmaid=kysymysryhmaid) \
            .order_by("-voimassa_loppupvm")

        is_used = "not_used"
        is_active_until = None
        if kysely_objs.exists():
            if kysely_objs.filter(voimassa_alkupvm__lte=datetime.today(),
                                  voimassa_loppupvm__gte=datetime.today()).exists():
                is_used = "active"
            else:
                is_used = "used"

            is_active_until = kysely_objs.first().voimassa_loppupvm.strftime(DATE_INPUT_FORMAT)

        return Response(dict(
            is_used=is_used,
            is_active_until=is_active_until,
        ))  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"(?P<kysymysryhmaid>[0-9]+)/pdf", detail=False)
    def pdf_by_kysymysryhmaid(self, request, kysymysryhmaid):
        language = self.request.query_params.get("language", "fi")
        validate_language_code(language, is_limited_languages=False)

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).first()
        if kysymysryhma is None:
            raise NotFound([ErrorMessages.ER016.value])  # HTTP_404_NOT_FOUND

        validate_language_code_by_kysymysryhma(language, kysymysryhma)

        # check YLLAPITAJA permission if kysymysryhma is not published or locked
        if kysymysryhma.tila.nimi not in [TILAENUM_PUBLISHED, TILAENUM_LOCKED]:
            self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        pdf_file = create_kysely_pdf(kysymysryhmaid=kysymysryhmaid, language=language)
        filename = get_pdf_filenames_by_kysymysryhma(kysymysryhma)[language]

        # if base64 query param is "true"
        if self.request.query_params.get("base64", "false").lower() in ("true", "1"):
            encoded_file = base64.b64encode(pdf_file)
            return HttpResponse(encoded_file)  # HTTP_200_OK

        return HttpResponse(
            pdf_file, content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'})  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"(?P<kysymysryhmaid>[0-9]+)/set-archived", detail=False, methods=["patch"])
    def set_archived(self, request, kysymysryhmaid):
        self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        kysymysryhmas = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid)
        if kysymysryhmas.first() is None:
            raise NotFound([ErrorMessages.ER016.value])  # HTTP_404_NOT_FOUND

        tila_archived, _ = TilaEnum.objects.get_or_create(nimi=TILAENUM_ARCHIVED)
        update_count = kysymysryhmas.update(tila=tila_archived, muutettuaika=timezone.now())

        return Response({"updates": update_count})  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"(?P<kysymysryhmaid>[0-9]+)/set-locked", detail=False, methods=["patch"])
    def set_locked(self, request, kysymysryhmaid):
        self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        kysymysryhmas = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid)
        if kysymysryhmas.first() is None:
            raise NotFound([ErrorMessages.ER016.value])  # HTTP_404_NOT_FOUND

        # check Kysymysryhma status is published
        if kysymysryhmas.first().tila.nimi != TILAENUM_PUBLISHED:
            raise ValidationError([ErrorMessages.ER022.value])  # HTTP_400_BAD_REQUEST

        tila_locked, _ = TilaEnum.objects.get_or_create(nimi=TILAENUM_LOCKED)
        update_count = kysymysryhmas.update(tila=tila_locked, muutettuaika=timezone.now())

        return Response({"updates": update_count})  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"(?P<kysymysryhmaid>[0-9]+)/set-unlocked", detail=False, methods=["patch"])
    def set_unlocked(self, request, kysymysryhmaid):
        self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        kysymysryhmas = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid)
        if kysymysryhmas.first() is None:
            raise NotFound([ErrorMessages.ER016.value])  # HTTP_404_NOT_FOUND

        # check Kysymysryhma status is locked
        if kysymysryhmas.first().tila.nimi != TILAENUM_LOCKED:
            raise ValidationError([ErrorMessages.ER023.value])  # HTTP_400_BAD_REQUEST

        tila_published, _ = TilaEnum.objects.get_or_create(nimi=TILAENUM_PUBLISHED)
        update_count = kysymysryhmas.update(tila=tila_published, muutettuaika=timezone.now())

        return Response({"updates": update_count})  # HTTP_200_OK


class ScaleViewSet(GenericViewSet, ListModelMixin):
    permission_classes = (AllowAny,)
    serializer_class = ScaleSerializer
    queryset = Scale.objects.all()

    def get_queryset(self):
        return Scale.objects.order_by("order_no")


class MalfunctionMessageViewSet(GenericViewSet):
    permission_classes = (AllowAny,)

    def authorization(self):
        user = self.request.user

        # Allow service user
        if user and SERVICE_USER_GROUP in [group.name for group in user.groups.all()]:
            return

        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(user)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # check current user have YLLAPITAJA permission
        validate_yllapitaja_permission(henkilo_permissions)

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"get-active", detail=False)
    def get_active_message(self, request):
        service = self.request.query_params.get("service", "virkailijapalvelu")

        active_msg = MalfunctionMessage.objects.filter(is_active=True, service=service).first()
        message = active_msg.message if active_msg else None
        return Response({"message": message})  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"list", detail=False)
    def list_messages(self, request):
        self.authorization()  # check YLLAPITAJA or service-user permission

        malfmessages = MalfunctionMessage.objects.order_by("code")
        serializer = MalfunctionMessageSerializer(malfmessages, many=True)
        return Response(serializer.data)  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"(?P<code>[0-9]+)/set-active", detail=False, methods=["patch"])
    def set_message_active(self, request, code):
        self.authorization()  # check YLLAPITAJA or service-user permission

        service = self.request.query_params.get("service", "virkailijapalvelu")

        # inactivate currently active message, and set new active
        MalfunctionMessage.objects.filter(is_active=True, service=service).update(is_active=False)
        MalfunctionMessage.objects.filter(code=code, service=service).update(is_active=True)

        return Response("OK")  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"set-inactive", detail=False, methods=["patch"])
    def set_messages_inactive(self, request):
        self.authorization()  # check YLLAPITAJA or service-user permission

        service = self.request.query_params.get("service", "virkailijapalvelu")

        MalfunctionMessage.objects.filter(is_active=True, service=service).update(is_active=False)
        return Response("OK")  # HTTP_200_OK


class AluejakoViewSet(GenericViewSet):
    permission_classes = (IsAuthenticated,)
    valssi_permission_levels = [VALSSI_PAAKAYTTAJA_LEVEL]

    def authorization(self, organisaatio_list):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # to impersonate organization or other user, check current user have YLLAPITAJA permission
        impersonate_org = self.request.headers.get("Impersonate-Organization", None)
        impersonate_user = self.request.headers.get("Impersonate-User", None)
        if impersonate_org:
            validate_yllapitaja_permission(henkilo_permissions)
            return
        elif impersonate_user:
            validate_yllapitaja_permission(henkilo_permissions)
            impersonate_user_oid, impersonate_user_permissions = get_henkilo_oid_and_permissions(impersonate_user)
            if not impersonate_user_oid:
                raise PermissionDenied([ErrorMessages.ER020.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, self.valssi_permission_levels)
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"create", methods=["post"], detail=False)
    def create_alue(self, request):
        serializer = AluejakoAluePostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        koulutustoimija = serializer.validated_data["koulutustoimija"]
        self.authorization([koulutustoimija])

        alue_obj = serializer.save()

        return Response({"id": alue_obj.id}, status=status.HTTP_201_CREATED)

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"modify", methods=["put"], detail=False)
    def set_oppilaitoses(self, request):
        serializer = AluejakoAluePutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        koulutustoimija = serializer.validated_data["koulutustoimija"]
        self.authorization([koulutustoimija])

        serializer.update()

        alue_id = serializer.validated_data["id"]
        flush_oppilaitoses_aluejako(koulutustoimija, alue_id)

        oppilaitos_oids = serializer.validated_data["oppilaitos_oids"]
        update_count = set_oppilaitoses_aluejako(koulutustoimija, oppilaitos_oids, alue_id)

        check_and_fix_aluejako_oppilaitoses(koulutustoimija)

        return Response({"updates": update_count})  # HTTP_200_OK

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"delete", methods=["delete"], detail=False)
    def delete_alue(self, request):
        serializer = AluejakoAlueDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        koulutustoimija = serializer.validated_data["koulutustoimija"]
        self.authorization([koulutustoimija])

        alue_id = serializer.validated_data["id"]
        flush_oppilaitoses_aluejako(koulutustoimija, alue_id)

        serializer.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @method_decorator(CSRF_DECORATORS)
    @action(url_path=r"list/koulutustoimija=(?P<koulutustoimija>[0-9.]+)", methods=["get"], detail=False)
    def list_alues(self, request, koulutustoimija):
        self.authorization([koulutustoimija])

        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        aluejako_alueet = get_aluejako_alueet(koulutustoimija, order_by_language=language)

        return Response(aluejako_alueet)  # HTTP_200_OK


class AccessTokenView(TokenObtainPairView):
    @method_decorator(RATELIMIT_DECORATORS)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    @method_decorator(RATELIMIT_DECORATORS)
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response

        # update access token cookie if successfully refreshed
        new_access_token = response.data["access"]
        response.set_cookie(
            key="virkailijapalvelu_access_token",
            value=new_access_token,
            expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
            path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
            samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"])
        return response


class CasLoginView(django_cas_ng.views.LoginView):
    def get(self, request: HttpRequest) -> HttpResponse:
        http_referer_found = "HTTP_REFERER" in request.META
        if http_referer_found and "/virkailija-ui/" in request.META["HTTP_REFERER"]:
            """
            We don't want Virkailija-UI to use session-cookie, instead should use JWT.
            """
            request.session.set_expiry(1)
        return super().get(request)

    def successful_login(self, request, next_page):
        logger.info(f"Successful login, user: {request.session.get('user', 'no_valid_session')}")

        response = HttpResponse("Login success")

        # set access/refresh token cookies
        if "user" in request.session and request.session["user"] and not next_page.startswith("/virkailijapalvelu"):
            try:
                user = User.objects.get(username=request.session["user"])
                tokens = get_tokens_for_user(user)
                response.set_cookie(
                    key="virkailijapalvelu_access_token",
                    value=tokens["access"],
                    expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
                    secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                    httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                    path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                    samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"])
                response.set_cookie(
                    key="virkailijapalvelu_refresh_token",
                    value=tokens["refresh"],
                    expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
                    secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                    httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                    path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                    samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"])

                request.session["refresh_token"] = tokens["refresh"]
                if not settings.QA_ENV and not settings.PRODUCTION_ENV:
                    response["X-Virkailijapalvelu-Access-Token"] = tokens["access"]
                    response["X-Virkailijapalvelu-Refresh-Token"] = tokens["refresh"]
            except Exception as e:
                logger.error(f"Error in setting jwt tokens. Error: {str(e)}")
                raise APIException([ErrorMessages.ER019.value])  # HTTP_500_INTERNAL_SERVER_ERROR
        return response


@receiver(django_cas_ng.signals.cas_user_logout)
def cas_logout_callback(user, **kwargs):
    logger.info(f"cas_logout_callback: Logged out user {user}")


class CasLogoutView(django_cas_ng.views.LogoutView):
    def get(self, request):
        refresh_token_qp = request.GET.get("refresh", None)
        if "refresh_token" in request.session:
            add_token_to_blacklist(request.session["refresh_token"])
            request.session.pop("refresh_token")
        elif refresh_token_qp:  # use query param as backup if token missing in session
            add_token_to_blacklist(refresh_token_qp)
        return super().get(request)


class GetPermissionViewSet(APIView):
    permission_classes = (IsAuthenticated, )

    def authorization(self):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        if check_yllapitaja_permission(henkilo_permissions):
            return None
        if check_paakayttaja_permission(henkilo_permissions):
            return None
        if check_toteuttaja_permission(henkilo_permissions):
            return None

        raise PermissionDenied([ErrorMessages.ER027.value])  # HTTP_403_FORBIDDEN

    def get(self, request, format=None):
        self.authorization()
        return Response("OK")  # HTTP_200_OK


class VirkailijaUILoggingViewSet(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            # log only when authenticated
            if not request.user.is_anonymous:
                username = self.request.user
                errlog = str(request.data["errlog"])
                logger.warning(f"[VIRKAILIJAUIERRLOG] [user:{username}] {errlog[:UI_LOG_CHAR_LIMIT]}")
        except Exception:
            pass
        return Response("OK")  # HTTP_200_OK


class LocalisationViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        localisation_key = request.GET.get("key", None)

        if localisation_key:
            localisations = Localisation.objects.filter(key=localisation_key)
        else:
            localisations = []

        response = [
            dict(
                namespace=localisation.namespace,
                category=localisation.category,
                key=localisation.key,
                locale=localisation.locale,
                value=localisation.value,
            )
            for localisation in localisations
        ]

        return Response(response, status=status.HTTP_200_OK)


class HealthViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        worker_active, worker_count = check_celery_worker_running()
        org_last_update = get_last_organizations_update_ago_hours(default_value=9999)
        health_response = dict(
            environment=settings.ENVIRONMENT,
            version=VALSSI_VERSION,
            build_id=get_ci_pipeline_number(),
            worker_active=worker_active,
            worker_count=worker_count,
            org_last_update=org_last_update,
        )

        if not worker_active:
            logger.error("Celery worker is not active.")
            return Response(health_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        elif org_last_update > VARDA_ORG_LAST_UPDATE_DEADLINE_FOR_ERROR:
            logger.error("Varda update deadline exceeded. Last update more than "
                         f"{VARDA_ORG_LAST_UPDATE_DEADLINE_FOR_ERROR} hour ago.")
            return Response(health_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health_response, status=status.HTTP_200_OK)


class HealthDbViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        try:
            user_count = User.objects.count()
        except Exception:
            logger.error("Virkailijapalvelu-db connection error.")
            return Response("Virkailijapalvelu-db connection error.", status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            _ = Kayttaja.objects.count()
        except Exception:
            logger.error("Valssi-db connection error.")
            return Response("Valssi-db connection error.", status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"db": user_count}, status=status.HTTP_200_OK)
