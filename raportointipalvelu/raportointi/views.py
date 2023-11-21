import base64
import logging

import django_cas_ng.signals
import django_cas_ng.views
from django.conf import settings
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, APIException, NotFound, ValidationError
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin, CreateModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from raportointi.constants import (
    VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_YLLAPITAJA_LEVEL, VALSSI_YLLAPITAJA_ORGANIZATION_OIDS, REPORT_MIN_ANSWERS,
    VALSSI_TOTEUTTAJA_LEVEL, VALSSI_VERSION, SUMMARY_TRANSLATIONS, REPORT_CSV_SINGLELINE_TYPES)
from raportointi.enums.error_messages import ErrorMessages
from raportointi.models import (
    Kysely, Kysymysryhma, ReportingTemplate, Summary, Result, Kyselykerta, Vastaaja, Koodi)
from raportointi.serializers import AccessTokenObtainSerializer, DataCollectionToteuttajaSerializer, \
    DataCollectionPaakayttajaSerializer, ReportingBaseSerializer, ReportingTemplateSerializer, \
    ClosedSurveysSerializer, ViewReportSerializer, SummaryUpdateSerializer, ResultSerializer, \
    ResultUpdateSerializer, SummarySerializer, DataCollectionYllapitajaSerializer
from raportointi.utils import (
    datenow_delta, get_henkilo_oid_and_permissions, get_valssi_organisaatio_oids_by_permission_levels,
    get_tokens_for_user, add_token_to_blacklist, group_kyselys_by_kysymysryhma_and_startdate,
    get_kysymysryhmas_with_closed_kyselys, get_query_param_filters, validate_language_code,
    get_koulutustoimija_by_oid, validate_yllapitaja_permission, check_celery_worker_running,
    get_ci_pipeline_number, filter_oppilaitos_oids_by_koulutustoimija, group_kyselys_by_kysymysryhma)
from raportointi.utils_answers_csv import create_answers_singleline_csv_by_kyselys
from raportointi.utils_datacollection import get_data_dicts_by_kyselys
from raportointi.utils_report import create_report_pdf, create_available_kyselykertas
from raportointi.utils_summary import (
    create_summary_pdf, create_summary_csv, get_indicators_by_kysely, get_locked_summaries_by_kyselydata,
    get_locked_results_by_koulutustoimija)


logger = logging.getLogger(__name__)

ratelimit_decorators = [
    ratelimit(key="ip", rate=f"{settings.TOKEN_RATELIMIT_PER_MINUTE}/m", block=True),
    ratelimit(key="ip", rate=f"{settings.TOKEN_RATELIMIT_PER_HOUR}/h", block=True)]

csrf_decorators = [ensure_csrf_cookie] if settings.CSRF_FORCE_ENABLED else []


class DataCollectionViewset(GenericViewSet, ListModelMixin):
    """View for "Tiedonkeruun Seuranta"
    Returns surveys with statistics of answers.
    Active surveys & max 2-month old.
    """
    queryset = Kysely.objects.none()
    permission_classes = (IsAuthenticated,)
    permission_level = None

    def authorization(self, permission_levels):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # to impersonate organization or other user, check current user have YLLAPITAJA permission
        impersonate_org = self.request.headers.get("Impersonate-Organization", None)
        impersonate_user = self.request.headers.get("Impersonate-User", None)
        if impersonate_org:
            validate_yllapitaja_permission(henkilo_permissions)
            return [impersonate_org]  # given oid is now 'allowed_oids'
        elif impersonate_user:
            validate_yllapitaja_permission(henkilo_permissions)
            impersonate_user_oid, impersonate_user_permissions = get_henkilo_oid_and_permissions(impersonate_user)
            if not impersonate_user_oid:
                raise PermissionDenied([ErrorMessages.ER026.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, permission_levels)

        if not allowed_oids:
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

        return allowed_oids

    def set_permission_level(self):
        role = self.request.query_params.get("role", "toteuttaja").lower()
        if role == "toteuttaja":
            self.permission_level = VALSSI_TOTEUTTAJA_LEVEL
        elif role == "paakayttaja":
            self.permission_level = VALSSI_PAAKAYTTAJA_LEVEL
        else:
            self.permission_level = VALSSI_YLLAPITAJA_LEVEL

    @method_decorator(csrf_decorators)
    def list(self, request, *args, **kwargs):
        self.set_permission_level()

        kyselys = self.get_queryset()

        kysely_dicts, kysymysryhma_dicts, kyselykerta_dicts, vastaajatunnus_dicts, \
            vastaaja_dicts = get_data_dicts_by_kyselys(kyselys)

        if self.permission_level == VALSSI_PAAKAYTTAJA_LEVEL:
            kysely_dicts = group_kyselys_by_kysymysryhma_and_startdate(kysely_dicts)
        elif self.permission_level == VALSSI_YLLAPITAJA_LEVEL:
            kysely_dicts = group_kyselys_by_kysymysryhma(kysely_dicts)

        serializer = self.get_serializer(
            kysely_dicts, many=True,
            context=dict(
                kysymysryhma_dicts=kysymysryhma_dicts,
                kyselykerta_dicts=kyselykerta_dicts,
                vastaajatunnus_dicts=vastaajatunnus_dicts,
                vastaaja_dicts=vastaaja_dicts))
        return Response(serializer.data)  # HTTP_200_OK

    def get_serializer_class(self):
        if self.permission_level == VALSSI_TOTEUTTAJA_LEVEL:
            return DataCollectionToteuttajaSerializer
        elif self.permission_level == VALSSI_PAAKAYTTAJA_LEVEL:
            return DataCollectionPaakayttajaSerializer
        return DataCollectionYllapitajaSerializer

    def get_queryset(self):
        allowed_oids = self.authorization([self.permission_level])
        if not allowed_oids:
            return Kysely.objects.none()

        # VALSSI_TOTEUTTAJA_LEVEL
        if self.permission_level == VALSSI_TOTEUTTAJA_LEVEL:
            datenow_minus_60d = datenow_delta(-60)
            return Kysely.objects.filter(
                oppilaitos__oid__in=allowed_oids,
                voimassa_loppupvm__gte=datenow_minus_60d) \
                .select_related("oppilaitos", "koulutustoimija") \
                .order_by("-voimassa_alkupvm", "-kyselyid")

        # VALSSI_PAAKAYTTAJA_LEVEL
        elif self.permission_level == VALSSI_PAAKAYTTAJA_LEVEL:
            datenow_minus_60d = datenow_delta(-60)
            koulutustoimija = self.request.query_params.get("koulutustoimija", None)
            if koulutustoimija is not None and koulutustoimija not in allowed_oids:
                raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

            koulutustoimija_oids = [koulutustoimija] if koulutustoimija is not None else allowed_oids
            return Kysely.objects.filter(
                koulutustoimija__oid__in=koulutustoimija_oids,
                voimassa_loppupvm__gte=datenow_minus_60d) \
                .select_related("oppilaitos", "koulutustoimija") \
                .order_by("-voimassa_alkupvm", "-kyselyid")

        # VALSSI_YLLAPITAJA_LEVEL
        start_date = self.request.query_params.get("start_date", None)
        end_date = self.request.query_params.get("end_date", None)

        # use the date year ago if startdate is not given
        if start_date is None:
            start_date = datenow_delta(-365)

        enddate_query = dict(voimassa_alkupvm__lte=end_date) if end_date else dict()

        return Kysely.objects.filter(
            voimassa_alkupvm__gte=start_date, **enddate_query) \
            .select_related("oppilaitos", "koulutustoimija") \
            .order_by("-voimassa_alkupvm", "-kyselyid")


class ReportingBaseViewset(GenericViewSet, RetrieveModelMixin):
    """View for reporting base, requires YLLAPITAJA permissions"""
    permission_classes = (IsAuthenticated,)
    valssi_permission_levels = [VALSSI_YLLAPITAJA_LEVEL]

    def authorization(self, organisaatio_list):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, self.valssi_permission_levels)
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER003.value])  # HTTP_403_FORBIDDEN

    @method_decorator(csrf_decorators)
    def retrieve(self, request, pk=None):
        self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)
        kysymysryhma = get_object_or_404(Kysymysryhma, kysymysryhmaid=pk)
        serializer = ReportingBaseSerializer(kysymysryhma)

        return Response(serializer.data)  # HTTP_200_OK


class ReportingTemplateViewset(GenericViewSet, UpdateModelMixin):
    """View for reporting template, requires YLLAPITAJA permissions"""
    queryset = ReportingTemplate.objects.all()
    permission_classes = (IsAuthenticated,)
    valssi_permission_levels = [VALSSI_YLLAPITAJA_LEVEL]

    def authorization(self, organisaatio_list):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, self.valssi_permission_levels)
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER003.value])  # HTTP_403_FORBIDDEN

    @method_decorator(csrf_decorators)
    def create(self, request):
        self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)
        serializer = ReportingTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @method_decorator(csrf_decorators)
    def update(self, request, *args, **kwargs):
        self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = ReportingTemplateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)


class ClosedSurveysViewset(GenericViewSet):
    """View for report index page of closed surveys (Kysely)"""
    serializer_class = ClosedSurveysSerializer
    permission_classes = (IsAuthenticated, )

    def authorization(self, permission_levels):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # to impersonate organization or other user, check current user have YLLAPITAJA permission
        impersonate_org = self.request.headers.get("Impersonate-Organization", None)
        impersonate_user = self.request.headers.get("Impersonate-User", None)
        if impersonate_org:
            validate_yllapitaja_permission(henkilo_permissions)
            return [impersonate_org]  # given oid is now 'allowed_oids'
        elif impersonate_user:
            validate_yllapitaja_permission(henkilo_permissions)
            impersonate_user_oid, impersonate_user_permissions = get_henkilo_oid_and_permissions(impersonate_user)
            if not impersonate_user_oid:
                raise PermissionDenied([ErrorMessages.ER026.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, permission_levels)

        if not allowed_oids:
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

        return allowed_oids

    @method_decorator(csrf_decorators)
    @action(url_path=r"koulutustoimija=(?P<koulutustoimija_oid>[0-9.]+)", detail=False)
    def get_closedsurveys_by_koulutustoimija(self, request, koulutustoimija_oid):
        role = self.request.query_params.get("role", "paakayttaja").lower()
        valssi_level = VALSSI_TOTEUTTAJA_LEVEL if role == "toteuttaja" else VALSSI_PAAKAYTTAJA_LEVEL
        allowed_oids = self.authorization([valssi_level])
        oppilaitos_oids = allowed_oids if role == "toteuttaja" else []

        koulutustoimija = get_koulutustoimija_by_oid(koulutustoimija_oid)

        if oppilaitos_oids:
            oppilaitos_oids = filter_oppilaitos_oids_by_koulutustoimija(oppilaitos_oids, koulutustoimija)

        kysymysryhmas, kysymysryhmaids = get_kysymysryhmas_with_closed_kyselys(allowed_oids)

        kyselykertas = Kyselykerta.objects.filter(
            kyselyid__kysely__kysymysryhmaid__kysymysryhmaid__in=set(kysymysryhmaids)) \
            .select_related("kyselyid", "kyselyid__koulutustoimija", "kyselyid__oppilaitos") \
            .prefetch_related("kyselyid__kysely__kysymysryhmaid") \
            .order_by("voimassa_alkupvm")
        kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas}

        vastaajas = Vastaaja.objects.filter(kyselykertaid__in=kyselykertaids)

        summarys = Summary.objects.filter(kysymysryhmaid__in=set(kysymysryhmaids), is_locked=True)
        results = Result.objects.filter(kysymysryhmaid__in=set(kysymysryhmaids), is_locked=True)

        serializer = self.get_serializer(kysymysryhmas, many=True, context={
            "koulutustoimija": koulutustoimija,
            "oppilaitos_oids": oppilaitos_oids,
            "kyselykertas": kyselykertas,
            "vastaajas": vastaajas,
            "summarys": summarys,
            "results": results})

        return Response(serializer.data)  # HTTP_200_OK


class ViewReportViewset(GenericViewSet):
    """View for viewing report
    Returns preview data needed for view report page.
    """
    serializer_class = ViewReportSerializer
    permission_classes = (IsAuthenticated, )
    permission_level = None

    def authorization(self, permission_levels):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # to impersonate organization or other user, check current user have YLLAPITAJA permission
        impersonate_org = self.request.headers.get("Impersonate-Organization", None)
        impersonate_user = self.request.headers.get("Impersonate-User", None)
        if impersonate_org:
            validate_yllapitaja_permission(henkilo_permissions)
            return [impersonate_org]  # given oid is now 'allowed_oids'
        elif impersonate_user:
            validate_yllapitaja_permission(henkilo_permissions)
            impersonate_user_oid, impersonate_user_permissions = get_henkilo_oid_and_permissions(impersonate_user)
            if not impersonate_user_oid:
                raise PermissionDenied([ErrorMessages.ER026.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, permission_levels)

        if not allowed_oids:
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

        return allowed_oids

    def set_permission_level(self):
        role = self.request.query_params.get("role", "toteuttaja").lower()
        if role == "toteuttaja":
            self.permission_level = VALSSI_TOTEUTTAJA_LEVEL
        elif role == "paakayttaja":
            self.permission_level = VALSSI_PAAKAYTTAJA_LEVEL
        else:
            self.permission_level = VALSSI_YLLAPITAJA_LEVEL

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija_oid>[0-9.]+)", detail=False)
    def get_viewreport_by_koulutustoimija(self, request, kysymysryhmaid, koulutustoimija_oid):
        self.set_permission_level()
        allowed_oids = self.authorization([self.permission_level])

        # validate YLLAPITAJA
        if self.permission_level == VALSSI_YLLAPITAJA_LEVEL:
            validate_yllapitaja_permission(None, allowed_oids=allowed_oids)

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).prefetch_related("kysymykset").first()
        if kysymysryhma is None:
            raise NotFound([ErrorMessages.ER025.value])  # HTTP_404_NOT_FOUND

        if self.permission_level == VALSSI_YLLAPITAJA_LEVEL:
            kysymysryhmaids = [kysymysryhmaid]
        else:
            kysymysryhmas, kysymysryhmaids = get_kysymysryhmas_with_closed_kyselys(allowed_oids)
            if kysymysryhma not in kysymysryhmas:
                raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN

        koulutustoimija = get_koulutustoimija_by_oid(koulutustoimija_oid)

        kyselykertas = Kyselykerta.objects.filter(
            kyselyid__kysely__kysymysryhmaid__kysymysryhmaid__in=set(kysymysryhmaids)) \
            .select_related("kyselyid", "kyselyid__koulutustoimija") \
            .prefetch_related("kyselyid__kysely__kysymysryhmaid") \
            .order_by("voimassa_alkupvm")
        kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas}

        vastaajas = Vastaaja.objects.filter(kyselykertaid__in=kyselykertaids)

        filters = get_query_param_filters(request.query_params, self.permission_level)
        serializer = self.get_serializer(kysymysryhma, context={
            "koulutustoimija": koulutustoimija,
            "kyselykertas": kyselykertas,
            "vastaajas": vastaajas,
            "filters": filters,
            "koodis": Koodi.objects.all(),
            "permission_level": self.permission_level})

        if self.permission_level == VALSSI_YLLAPITAJA_LEVEL:
            return Response(serializer.data)  # HTTP_200_OK
        elif serializer.data["survey_participants_count"] < REPORT_MIN_ANSWERS:
            error = dict(ErrorMessages.ER009.value)
            error["description"] = error["description"].format(REPORT_MIN_ANSWERS)
            raise PermissionDenied([error])  # HTTP_403_FORBIDDEN

        return Response(serializer.data)  # HTTP_200_OK


class ReportPdfViewset(GenericViewSet):
    """Downloads a report as pdf"""
    serializer_class = ViewReportSerializer
    permission_classes = (IsAuthenticated, )

    def authorization(self, permission_levels):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        # to impersonate organization or other user, check current user have YLLAPITAJA permission
        impersonate_org = self.request.headers.get("Impersonate-Organization", None)
        impersonate_user = self.request.headers.get("Impersonate-User", None)
        if impersonate_org:
            validate_yllapitaja_permission(henkilo_permissions)
            return [impersonate_org]  # given oid is now 'allowed_oids'
        elif impersonate_user:
            validate_yllapitaja_permission(henkilo_permissions)
            impersonate_user_oid, impersonate_user_permissions = get_henkilo_oid_and_permissions(impersonate_user)
            if not impersonate_user_oid:
                raise PermissionDenied([ErrorMessages.ER026.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, permission_levels)

        if not allowed_oids:
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

        return allowed_oids

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija_oid>[0-9.]+)", detail=False)
    def get_report_pdf_by_koulutustoimija(self, request, kysymysryhmaid, koulutustoimija_oid):
        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        role = self.request.query_params.get("role", "paakayttaja").lower()
        valssi_level = VALSSI_TOTEUTTAJA_LEVEL if role == "toteuttaja" else VALSSI_PAAKAYTTAJA_LEVEL
        allowed_oids = self.authorization([valssi_level])

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).prefetch_related("kysymykset").first()
        if kysymysryhma is None:
            raise NotFound([ErrorMessages.ER025.value])  # HTTP_404_NOT_FOUND

        kysymysryhmas, _ = get_kysymysryhmas_with_closed_kyselys(allowed_oids)
        if kysymysryhma not in kysymysryhmas:
            raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN

        kyselykertas = Kyselykerta.objects.filter(kyselyid__kysely__kysymysryhmaid=kysymysryhma) \
            .select_related("kyselyid", "kyselyid__koulutustoimija")
        kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas}

        vastaajas = Vastaaja.objects.filter(kyselykertaid__in=kyselykertaids)

        koulutustoimija = get_koulutustoimija_by_oid(koulutustoimija_oid)

        filters = get_query_param_filters(request.query_params, valssi_level)
        serializer = self.get_serializer(kysymysryhma, context={
            "koulutustoimija": koulutustoimija,
            "kyselykertas": kyselykertas,
            "vastaajas": vastaajas,
            "filters": filters,
            "koodis": Koodi.objects.all()})

        if serializer.data["survey_participants_count"] < REPORT_MIN_ANSWERS:
            error = dict(ErrorMessages.ER009.value)
            error["description"] = error["description"].format(REPORT_MIN_ANSWERS)
            raise PermissionDenied([error])  # HTTP_403_FORBIDDEN

        pdf = create_report_pdf(serializer.data, language)

        # if base64 query param is 'true'
        if self.request.query_params.get("base64", "false").lower() in ("true", "1"):
            encoded_file = base64.b64encode(pdf)
            return HttpResponse(encoded_file)  # HTTP_200_OK

        # Return the PDF in the response
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={slugify(serializer.data['nimi_fi'])}.pdf"
        return response  # HTTP_200_OK


class SummaryViewset(GenericViewSet, CreateModelMixin):
    serializer_class = SummarySerializer
    permission_classes = (IsAuthenticated, )

    def authorization(self, permission_levels, organisaatio_list):
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
                raise PermissionDenied([ErrorMessages.ER026.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, permission_levels)
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

    @method_decorator(csrf_decorators)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        oppilaitos = serializer.validated_data["oppilaitos"]
        self.authorization([VALSSI_TOTEUTTAJA_LEVEL], [oppilaitos])
        serializer.save()

    @method_decorator(csrf_decorators)
    @action(url_path=r"kyselyid=(?P<kyselyid>[0-9]+)", detail=False)
    def get_summary_by_kyselyid(self, request, kyselyid):
        kysely = Kysely.objects.filter(kyselyid=kyselyid) \
            .select_related("koulutustoimija", "oppilaitos") \
            .prefetch_related("kysymysryhmat").first()
        if kysely is None:
            raise NotFound([ErrorMessages.ER024.value])  # HTTP_404_NOT_FOUND

        oppilaitos = kysely.oppilaitos.oid
        self.authorization([VALSSI_TOTEUTTAJA_LEVEL], [oppilaitos])

        summary = Summary.objects.filter(
            kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid,
            oppilaitos=kysely.oppilaitos.oid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm).first()
        if summary is None:
            # add organization (oppilaitos) and background info (taustatiedot) to default response
            paaindikaattori_key, sekondaariset_indikaattorit_keys = get_indicators_by_kysely(kysely)

            response_data = dict(
                id=None,
                kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid,
                oppilaitos=oppilaitos,
                koulutustoimija_name=dict(fi=None, sv=None),
                kysely_voimassa_alkupvm=kysely.voimassa_alkupvm,
                group_info=None, kuvaus=None, aineisto=None, vahvuudet=None,
                kohteet=None, keh_toimenpiteet=None, seur_toimenpiteet=None,
                taustatiedot=dict(
                    koulutustoimija=kysely.koulutustoimija.oid,
                    paaindikaattori=paaindikaattori_key,
                    sekondaariset_indikaattorit=sekondaariset_indikaattorit_keys,
                    kysymysryhma_name=dict(fi=None, sv=None)),
                is_locked=False)
            return Response(response_data)  # HTTP_200_OK

        serializer = self.get_serializer(summary, context=dict(kysely_obj=kysely))
        return Response(serializer.data)  # HTTP_200_OK

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"oppilaitos=(?P<oppilaitos>[0-9.]+)/"
            r"alkupvm=(?P<kysely_voimassa_alkupvm>[0-9-]+)", detail=False)
    def get_summary_by_kyselydata(self, request, kysymysryhmaid, oppilaitos, kysely_voimassa_alkupvm):
        kysely = Kysely.objects.filter(
            oppilaitos__oid=oppilaitos,
            voimassa_alkupvm=kysely_voimassa_alkupvm,
            kysymysryhmat__kysymysryhmaid=kysymysryhmaid).first()
        if kysely is None:
            raise NotFound([ErrorMessages.ER024.value])  # HTTP_404_NOT_FOUND

        return self.get_summary_by_kyselyid(request, kysely.kyselyid)

    @method_decorator(csrf_decorators)
    @action(url_path=r"(?P<summaryid>[0-9]+)", detail=False, methods=["put"])
    def update_summary_by_summaryid(self, request, summaryid):
        serializer = SummaryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        summaries = Summary.objects.filter(id=summaryid)
        summary = summaries.first()
        if summary is None:
            raise NotFound([ErrorMessages.ER014.value])  # HTTP_404_NOT_FOUND

        oppilaitos = summary.oppilaitos
        self.authorization([VALSSI_TOTEUTTAJA_LEVEL], [oppilaitos])

        if summary.is_locked:
            raise ValidationError([ErrorMessages.ER015.value])  # HTTP_400_BAD_REQUEST

        summaries.update(**serializer.validated_data)
        return Response("OK")  # HTTP_200_OK

    @method_decorator(csrf_decorators)
    @action(url_path=r"(?P<summaryid>[0-9]+)/pdf", detail=False)
    def get_summary_pdf(self, request, summaryid):
        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        summary = Summary.objects.filter(id=summaryid).first()
        if summary is None:
            raise NotFound([ErrorMessages.ER014.value])  # HTTP_404_NOT_FOUND
        elif not summary.is_locked:
            raise ValidationError([ErrorMessages.ER016.value])  # HTTP_400_BAD_REQUEST

        oppilaitos = summary.oppilaitos
        koulutustoimija_oid = summary.taustatiedot.get("koulutustoimija", None)
        self.authorization([VALSSI_TOTEUTTAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL], [oppilaitos, koulutustoimija_oid])
        koulutustoimija = get_koulutustoimija_by_oid(koulutustoimija_oid)

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=summary.kysymysryhmaid).first()

        pdf_title = ""
        if kysymysryhma:
            pdf_title = kysymysryhma.nimi_fi if language == "fi" else kysymysryhma.nimi_sv

        pdf_content = dict(
            title=pdf_title,
            koulutustoimija=koulutustoimija.nimi_fi if language == "fi" else koulutustoimija.nimi_sv,
            group_info=f"{SUMMARY_TRANSLATIONS['summary_title'][language]}: {summary.group_info}",
            main_indicator_key=summary.taustatiedot.get("paaindikaattori", ""),
            secondary_indicator_keys=summary.taustatiedot.get("sekondaariset_indikaattorit", []),
            kuvaus=summary.kuvaus,
            aineisto=summary.aineisto,
            vahvuudet=summary.vahvuudet,
            kohteet=summary.kohteet,
            keh_toimenpiteet=summary.keh_toimenpiteet,
            seur_toimenpiteet=summary.seur_toimenpiteet)
        pdf_file = create_summary_pdf(pdf_content, language)

        # if base64 query param is 'true'
        if self.request.query_params.get("base64", "false").lower() in ("true", "1"):
            encoded_file = base64.b64encode(pdf_file)
            return HttpResponse(encoded_file)  # HTTP_200_OK

        return HttpResponse(
            pdf_file, content_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="summary.pdf"'})  # HTTP_200_OK

    @method_decorator(csrf_decorators)
    @action(url_path=r"list/kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"alkupvm=(?P<kysely_voimassa_alkupvm>[0-9-]+)/"
            r"koulutustoimija=(?P<koulutustoimija>[0-9.]+)", detail=False)
    def get_summaries_by_kyselydata(self, request, kysymysryhmaid, kysely_voimassa_alkupvm, koulutustoimija):
        self.authorization([VALSSI_PAAKAYTTAJA_LEVEL], [koulutustoimija])

        summaries = get_locked_summaries_by_kyselydata(kysymysryhmaid, kysely_voimassa_alkupvm, koulutustoimija)

        return Response(summaries)  # HTTP_200_OK

    @method_decorator(csrf_decorators)
    @action(url_path=r"csv/kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija>[0-9.]+)/"
            r"alkupvm=(?P<kysely_voimassa_alkupvm>[0-9-]+)", detail=False)
    def get_summary_csv(self, request, kysymysryhmaid, kysely_voimassa_alkupvm, koulutustoimija):
        self.authorization([VALSSI_PAAKAYTTAJA_LEVEL], [koulutustoimija])

        summaries = get_locked_summaries_by_kyselydata(kysymysryhmaid, kysely_voimassa_alkupvm, koulutustoimija)

        if summaries is []:
            raise NotFound([ErrorMessages.ER020.value])  # HTTP_404_NOT_FOUND

        csv_file = create_summary_csv(summaries).encode("utf-8-sig")

        # if base64 query param is 'true'
        if self.request.query_params.get("base64", "false").lower() in ("true", "1"):
            encoded_file = base64.b64encode(csv_file)
            return HttpResponse(encoded_file)  # HTTP_200_OK

        return HttpResponse(
            csv_file, content_type="text/csv;charset=utf-8-sig;",
            headers={"Content-Disposition": 'attachment; filename="summary.csv"'})  # HTTP_200_OK


class ResultViewset(GenericViewSet, CreateModelMixin):
    serializer_class = ResultSerializer
    permission_classes = (IsAuthenticated, )

    def authorization(self, permission_levels, organisaatio_list):
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
                raise PermissionDenied([ErrorMessages.ER026.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, permission_levels)
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

    @method_decorator(csrf_decorators)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        koulutustoimija = serializer.validated_data["koulutustoimija"]
        self.authorization([VALSSI_PAAKAYTTAJA_LEVEL], [koulutustoimija])
        serializer.save()

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija>[0-9.]+)/"
            r"alkupvm=(?P<kysely_voimassa_alkupvm>[0-9-]+)", detail=False)
    def get_result(self, request, kysymysryhmaid, koulutustoimija, kysely_voimassa_alkupvm):
        self.authorization([VALSSI_YLLAPITAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL],
                           VALSSI_YLLAPITAJA_ORGANIZATION_OIDS + [koulutustoimija])

        result = Result.objects.filter(
            kysymysryhmaid=kysymysryhmaid,
            koulutustoimija=koulutustoimija,
            kysely_voimassa_alkupvm=kysely_voimassa_alkupvm).first()
        if result is None:
            response_data = dict(
                id=None,
                kysymysryhmaid=None,
                koulutustoimija=None,
                koulutustoimija_name=dict(fi=None, sv=None),
                kysely_voimassa_alkupvm=None,
                kuvaus=None, aineisto=None, vahvuudet=None,
                kohteet=None, keh_toimenpiteet=None, seur_toimenpiteet=None,
                taustatiedot=dict(
                    koulutustoimija=None,
                    paaindikaattori=None,
                    sekondaariset_indikaattorit=[],
                    kysymysryhma_name=dict(fi=None, sv=None)),
                is_locked=False)
            return Response(response_data)  # HTTP_200_OK

        serializer = self.get_serializer(result)
        return Response(serializer.data)  # HTTP_200_OK

    @method_decorator(csrf_decorators)
    @action(url_path=r"(?P<resultid>[0-9]+)", detail=False, methods=["put"])
    def update_result(self, request, resultid):
        serializer = ResultUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        results = Result.objects.filter(id=resultid)
        result = results.first()
        if result is None:
            raise NotFound([ErrorMessages.ER020.value])  # HTTP_404_NOT_FOUND

        koulutustoimija = result.koulutustoimija
        self.authorization([VALSSI_PAAKAYTTAJA_LEVEL], [koulutustoimija])

        if result.is_locked:
            raise ValidationError([ErrorMessages.ER021.value])  # HTTP_400_BAD_REQUEST

        results.update(**serializer.validated_data)
        return Response("OK")  # HTTP_200_OK

    @method_decorator(csrf_decorators)
    @action(url_path=r"list/koulutustoimija=(?P<koulutustoimija>[0-9.]+)", detail=False)
    def get_results_by_koulutustoimija(self, request, koulutustoimija):
        self.authorization([VALSSI_YLLAPITAJA_LEVEL], VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        results = get_locked_results_by_koulutustoimija(koulutustoimija)
        return Response(results)  # HTTP_200_OK

    @method_decorator(csrf_decorators)
    @action(url_path=r"(?P<resultid>[0-9]+)/pdf", detail=False)
    def get_result_pdf(self, request, resultid):
        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        result = Result.objects.filter(id=resultid).first()
        if result is None:
            raise NotFound([ErrorMessages.ER020.value])  # HTTP_404_NOT_FOUND
        elif not result.is_locked:
            raise ValidationError([ErrorMessages.ER022.value])  # HTTP_400_BAD_REQUEST

        koulutustoimija_oid = result.koulutustoimija
        self.authorization([VALSSI_YLLAPITAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL],
                           VALSSI_YLLAPITAJA_ORGANIZATION_OIDS + [koulutustoimija_oid])
        koulutustoimija = get_koulutustoimija_by_oid(koulutustoimija_oid)

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=result.kysymysryhmaid).first()

        pdf_title = ""
        if kysymysryhma:
            pdf_title = kysymysryhma.nimi_fi if language == "fi" else kysymysryhma.nimi_sv

        pdf_content = dict(
            title=pdf_title,
            koulutustoimija=koulutustoimija.nimi_fi if language == "fi" else koulutustoimija.nimi_sv,
            group_info=SUMMARY_TRANSLATIONS["result_title"][language],
            main_indicator_key=result.taustatiedot.get("paaindikaattori", ""),
            secondary_indicator_keys=result.taustatiedot.get("sekondaariset_indikaattorit", []),
            kuvaus=result.kuvaus,
            aineisto=result.aineisto,
            vahvuudet=result.vahvuudet,
            kohteet=result.kohteet,
            keh_toimenpiteet=result.keh_toimenpiteet,
            seur_toimenpiteet=result.seur_toimenpiteet)
        pdf_file = create_summary_pdf(pdf_content, language)

        # if base64 query param is 'true'
        if self.request.query_params.get("base64", "false").lower() in ("true", "1"):
            encoded_file = base64.b64encode(pdf_file)
            return HttpResponse(encoded_file)  # HTTP_200_OK

        return HttpResponse(
            pdf_file, content_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="result.pdf"'})  # HTTP_200_OK


class AvailableKyselykierrosListViewset(GenericViewSet):
    serializer_class = ResultSerializer
    permission_classes = (IsAuthenticated, )
    valssi_permission_levels = [VALSSI_PAAKAYTTAJA_LEVEL]

    def authorization(self, permission_levels, organisaatio):
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
                raise PermissionDenied([ErrorMessages.ER026.value])  # HTTP_403_FORBIDDEN
            henkilo_permissions = impersonate_user_permissions

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, permission_levels)
        if organisaatio not in allowed_oids:
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

        return allowed_oids

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija_oid>[0-9.]+)", detail=False)
    def get_available_kyselykierros_list(self, request, kysymysryhmaid, koulutustoimija_oid):
        allowed_oids = self.authorization(self.valssi_permission_levels, koulutustoimija_oid)

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).first()
        if kysymysryhma is None:
            raise NotFound([ErrorMessages.ER025.value])  # HTTP_404_NOT_FOUND

        kysymysryhmas, _ = get_kysymysryhmas_with_closed_kyselys(allowed_oids)
        if kysymysryhma not in kysymysryhmas:
            raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN

        koulutustoimija = get_koulutustoimija_by_oid(koulutustoimija_oid)

        kyselykertas = Kyselykerta.objects.filter(
            kyselyid__kysely__kysymysryhmaid__kysymysryhmaid=kysymysryhma.pk) \
            .select_related("kyselyid", "kyselyid__koulutustoimija") \
            .order_by("voimassa_alkupvm")
        kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas}

        vastaajas = Vastaaja.objects.filter(kyselykertaid__in=kyselykertaids)

        kyselykertas_start_times = []
        for kyselykerta in kyselykertas:
            if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and \
                    kyselykerta.voimassa_loppupvm < timezone.now().date() and \
                    kyselykerta.voimassa_alkupvm not in kyselykertas_start_times:
                kyselykertas_start_times.append(kyselykerta.voimassa_alkupvm)

        available_kyselykertas = create_available_kyselykertas(
            kysymysryhma, kyselykertas_start_times, koulutustoimija, kyselykertas, vastaajas)

        return Response(available_kyselykertas)  # HTTP_200_OK


class AnswersExportViewset(GenericViewSet):
    permission_classes = (IsAuthenticated,)
    valssi_permission_levels = [VALSSI_YLLAPITAJA_LEVEL]

    def authorization(self, organisaatio_list):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        allowed_oids = get_valssi_organisaatio_oids_by_permission_levels(
            henkilo_permissions, self.valssi_permission_levels)
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER003.value])  # HTTP_403_FORBIDDEN

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija>[0-9.]+)/"
            r"alkupvm=(?P<voimassa_alkupvm>[0-9-]+)", detail=False)
    def get_answers_csv_by_kyselys(self, request, kysymysryhmaid, koulutustoimija, voimassa_alkupvm):
        self.authorization(VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        kyselys = Kysely.objects.filter(
            kysymysryhmat__kysymysryhmaid=kysymysryhmaid,
            koulutustoimija__oid=koulutustoimija,
            voimassa_alkupvm=voimassa_alkupvm) \
            .select_related("koulutustoimija") \
            .prefetch_related("kysymysryhmat")
        if not kyselys.exists():
            raise NotFound([ErrorMessages.ER018.value])  # HTTP_404_NOT_FOUND

        kysymysryhma = kyselys.first().kysymysryhmat.first()
        lomaketyyppi = kysymysryhma.metatiedot.get("lomaketyyppi")

        if lomaketyyppi in REPORT_CSV_SINGLELINE_TYPES:
            csv_file = create_answers_singleline_csv_by_kyselys(kyselys, kysymysryhma, language)
        else:
            raise ValidationError([ErrorMessages.ER027.value])  # HTTP_400_BAD_REQUEST

        csv_file = csv_file.encode("utf-8-sig")  # add BOM to csv-file

        # if base64 query param is 'true'
        if self.request.query_params.get("base64", "false").lower() in ("true", "1"):
            encoded_file = base64.b64encode(csv_file)
            return HttpResponse(encoded_file)  # HTTP_200_OK

        return HttpResponse(
            csv_file, content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="output.csv"'})  # HTTP_200_OK


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
        if "user" in request.session and request.session["user"] and not next_page.startswith("/raportointipalvelu"):
            try:
                user = User.objects.get(username=request.session["user"])
                tokens = get_tokens_for_user(user)
                response.set_cookie(
                    key="raportointipalvelu_access_token",
                    value=tokens["access"],
                    expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
                    secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                    httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                    path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                    samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"])
                response.set_cookie(
                    key="raportointipalvelu_refresh_token",
                    value=tokens["refresh"],
                    expires=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"],
                    secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
                    httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
                    path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
                    samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"])

                request.session["refresh_token"] = tokens["refresh"]
                if not settings.QA_ENV and not settings.PRODUCTION_ENV:
                    response["X-Raportointipalvelu-Access-Token"] = tokens["access"]
                    response["X-Raportointipalvelu-Refresh-Token"] = tokens["refresh"]
            except Exception as e:
                logger.error(f"Error in setting jwt tokens. Error: {str(e)}")
                raise APIException("Error in setting jwt tokens.")  # HTTP_500_INTERNAL_SERVER_ERROR
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


class AccessTokenView(TokenObtainPairView):
    serializer_class = AccessTokenObtainSerializer

    @method_decorator(ratelimit_decorators)
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RefreshTokenView(TokenRefreshView):
    @method_decorator(ratelimit_decorators)
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != status.HTTP_200_OK:
            return response

        # update access token cookie if successfully refreshed
        new_access_token = response.data["access"]
        response.set_cookie(
            key="raportointipalvelu_access_token",
            value=new_access_token,
            expires=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"],
            secure=settings.SIMPLE_JWT["AUTH_COOKIE_SECURE"],
            httponly=settings.SIMPLE_JWT["AUTH_COOKIE_HTTP_ONLY"],
            path=settings.SIMPLE_JWT["AUTH_COOKIE_PATH"],
            samesite=settings.SIMPLE_JWT["AUTH_COOKIE_SAMESITE"])
        return response


class HealthViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        worker_active = check_celery_worker_running()
        health_response = dict(
            environment=settings.ENVIRONMENT,
            version=VALSSI_VERSION,
            build_id=get_ci_pipeline_number(),
            worker_active=worker_active)

        if not worker_active:
            logger.error("Celery worker is not active.")
            return Response(health_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(health_response, status=status.HTTP_200_OK)


class HealthDbViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        try:
            user_count = User.objects.count()
        except Exception:
            logger.error("Raportointipalvelu-db connection error.")
            return Response("Raportointipalvelu-db connection error.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"db": user_count}, status=status.HTTP_200_OK)
