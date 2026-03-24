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
    VALSSI_PAAKAYTTAJA_LEVEL, VALSSI_YLLAPITAJA_LEVEL, VALSSI_YLLAPITAJA_ORGANIZATION_OIDS, VALSSI_TOTEUTTAJA_LEVEL,
    VALSSI_VERSION, SUMMARY_TRANSLATIONS, REPORT_CSV_SINGLELINE_TYPES, LAATUTEKIJA_PROSESSI, LAATUTEKIJA_RAKENNE,
    DATE_INPUT_FORMAT, SKIPPED_TEXT, REPORT_VALUE_NULL,
)
from raportointi.enums.error_messages import ErrorMessages
from raportointi.models import (
    Kysely, Kysymysryhma, ReportingTemplate, Summary, Result, Kyselykerta, Vastaaja, Koodi)
from raportointi.serializers import (
    AccessTokenObtainSerializer, DataCollectionToteuttajaSerializer, DataCollectionPaakayttajaSerializer,
    ReportingBaseSerializer, ReportingTemplateSerializer, ClosedSurveysSerializer, ViewReportSerializer,
    SummaryUpdateSerializer, ResultSerializer, ResultUpdateSerializer, SummarySerializer,
    DataCollectionYllapitajaSerializer, KyselykertaAvailableSerializer,
)
from raportointi.utils import (
    datenow_delta, get_henkilo_oid_and_permissions, get_valssi_organisaatio_oids_by_permission_levels,
    get_tokens_for_user, add_token_to_blacklist, group_kyselys_by_kysymysryhma_and_startdate,
    get_kysymysryhmas_with_closed_kyselys, get_query_param_filters, validate_language_code,
    get_koulutustoimija_by_oid, validate_yllapitaja_permission, check_celery_worker_running,
    get_ci_pipeline_number, filter_oppilaitos_oids_by_koulutustoimija, group_kyselys_by_kysymysryhma,
    get_parent_oids_by_oppilaitos_oids, get_laatutekija_by_kysymysryhma, validate_language_code_by_kysymysryhma,
)
from raportointi.utils_answers_csv import create_answers_singleline_csv_by_kyselys, create_lomake_usage_csv_by_kyselys
from raportointi.utils_datacollection import get_data_dicts_by_kyselys
from raportointi.utils_report import (
    create_report_pdf, create_available_kyselykertas, remove_duplicate_kysymysryhmas, sort_kysymysryhmas_by_laatutekija)
from raportointi.utils_summary import (
    create_summary_pdf, create_summary_csv, get_indicators_by_kysely, get_locked_summaries_by_kyselydata,
    get_locked_results_by_koulutustoimija, get_summaries_by_kysymysryhma_and_date_range,
    get_results_by_kysymysryhma_and_date_range, create_result_csv,
)


logger = logging.getLogger(__name__)

ratelimit_decorators = [
    ratelimit(key="ip", rate=f"{settings.RATELIMIT_PER_MINUTE}/m", block=True),
    ratelimit(key="ip", rate=f"{settings.RATELIMIT_PER_HOUR}/h", block=True)]

csrf_decorators = [ensure_csrf_cookie] if settings.CSRF_FORCE_ENABLED else []


class DataCollectionViewset(GenericViewSet, ListModelMixin):
    """View for "Tiedonkeruun Seuranta"
    Returns surveys with statistics of answers.
    Active surveys & max <max_age> old.
    """
    queryset = Kysely.objects.none()
    permission_classes = (IsAuthenticated,)
    permission_level = None
    max_age = 360  # days

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

        datenow_minus_max_age = datenow_delta(-self.max_age)

        # VALSSI_TOTEUTTAJA_LEVEL
        if self.permission_level == VALSSI_TOTEUTTAJA_LEVEL:
            return Kysely.objects.filter(
                oppilaitos__oid__in=allowed_oids,
                voimassa_loppupvm__gte=datenow_minus_max_age) \
                .select_related("oppilaitos", "koulutustoimija") \
                .order_by("-voimassa_alkupvm", "-kyselyid")

        # VALSSI_PAAKAYTTAJA_LEVEL
        elif self.permission_level == VALSSI_PAAKAYTTAJA_LEVEL:
            koulutustoimija = self.request.query_params.get("koulutustoimija", None)
            if koulutustoimija is not None and koulutustoimija not in allowed_oids:
                raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

            koulutustoimija_oids = [koulutustoimija] if koulutustoimija is not None else allowed_oids
            return Kysely.objects.filter(
                koulutustoimija__oid__in=koulutustoimija_oids,
                voimassa_loppupvm__gte=datenow_minus_max_age) \
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

        # append allowed_oids with koulutustoimija_oids related oppilaitoses in allowed_oids
        if role == "toteuttaja":
            allowed_oids |= get_parent_oids_by_oppilaitos_oids(allowed_oids)

        kysymysryhmas, kysymysryhmaids = get_kysymysryhmas_with_closed_kyselys(allowed_oids)

        kyselykertas = Kyselykerta.objects.filter(
            kyselyid__kysely__kysymysryhmaid__kysymysryhmaid__in=kysymysryhmaids
        ).select_related(
            "kyselyid", "kyselyid__koulutustoimija", "kyselyid__oppilaitos"
        ).prefetch_related(
            "kyselyid__kysymysryhmat"
        ).order_by("voimassa_alkupvm")
        kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas}

        vastaajas = Vastaaja.objects.filter(kyselykertaid__in=kyselykertaids)

        summarys = Summary.objects.filter(kysymysryhmaid__in=kysymysryhmaids, is_locked=True)
        results = Result.objects.filter(kysymysryhmaid__in=kysymysryhmaids, is_locked=True)

        serializer = self.get_serializer(
            kysymysryhmas, many=True, context={
                "koulutustoimija": koulutustoimija,
                "oppilaitos_oids": oppilaitos_oids,
                "kyselykertas": kyselykertas,
                "vastaajas": vastaajas,
                "summarys": summarys,
                "results": results,
            }
        )

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

        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

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
            kyselyid__kysely__kysymysryhmaid__kysymysryhmaid__in=kysymysryhmaids,
            voimassa_loppupvm__lt=timezone.now().date()
        ).select_related(
            "kyselyid", "kyselyid__koulutustoimija", "kyselyid__oppilaitos"
        ).prefetch_related(
            "kyselyid__kysymysryhmat"
        ).order_by("voimassa_alkupvm")
        kyselykertaids = {kyselykerta.pk for kyselykerta in kyselykertas}

        vastaajas = Vastaaja.objects.filter(kyselykertaid__in=kyselykertaids)

        filters = get_query_param_filters(request.query_params, self.permission_level)
        serializer = self.get_serializer(kysymysryhma, context={
            "koulutustoimija": koulutustoimija,
            "kyselykertas": kyselykertas,
            "vastaajas": vastaajas,
            "filters": filters,
            "koodis": Koodi.objects.all(),
            "permission_level": self.permission_level,
            "language": language,
        })

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
        # Base language
        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        # Secondary language used in content
        lomake_language = self.request.query_params.get("lomake_language", "fi")
        validate_language_code(lomake_language, is_limited_languages=False)

        role = self.request.query_params.get("role", "paakayttaja").lower()
        valssi_level = VALSSI_TOTEUTTAJA_LEVEL if role == "toteuttaja" else VALSSI_PAAKAYTTAJA_LEVEL
        allowed_oids = self.authorization([valssi_level])

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).prefetch_related("kysymykset").first()
        if kysymysryhma is None:
            raise NotFound([ErrorMessages.ER025.value])  # HTTP_404_NOT_FOUND

        validate_language_code_by_kysymysryhma(lomake_language, kysymysryhma)

        kysymysryhmas, _ = get_kysymysryhmas_with_closed_kyselys(allowed_oids)
        if kysymysryhma not in kysymysryhmas:
            raise PermissionDenied([ErrorMessages.ER010.value])  # HTTP_403_FORBIDDEN

        kyselykertas = Kyselykerta.objects.filter(
            kyselyid__kysely__kysymysryhmaid=kysymysryhma,
            voimassa_loppupvm__lt=timezone.now().date()) \
            .select_related("kyselyid", "kyselyid__koulutustoimija", "kyselyid__oppilaitos")
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

        pdf = create_report_pdf(serializer.data, filters, language, lomake_language)

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
    allowed_laatutekijas = (LAATUTEKIJA_PROSESSI, LAATUTEKIJA_RAKENNE)

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

    def validate_laatutekija(self, kysymysryhma):
        laatutekija = get_laatutekija_by_kysymysryhma(kysymysryhma)
        if laatutekija not in self.allowed_laatutekijas:
            raise ValidationError([ErrorMessages.ER030.value])  # HTTP_400_BAD_REQUEST

    @method_decorator(csrf_decorators)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        oppilaitos = serializer.validated_data["oppilaitos"]
        self.authorization([VALSSI_TOTEUTTAJA_LEVEL], [oppilaitos])

        kyselyid = serializer.validated_data["kyselyid"]
        kysely = Kysely.objects.filter(kyselyid=kyselyid).first()

        # Check Kysymysryhma laatutekija
        self.validate_laatutekija(kysely.kysymysryhmat.first())

        serializer.save()

    @method_decorator(csrf_decorators)
    @action(url_path=r"kyselyid=(?P<kyselyid>[0-9]+)", detail=False)
    def get_summary_by_kyselyid(self, request, kyselyid):
        kysely = Kysely.objects.filter(kyselyid=kyselyid) \
            .select_related("koulutustoimija", "oppilaitos") \
            .prefetch_related("kysymysryhmat").first()
        if kysely is None:
            raise NotFound([ErrorMessages.ER024.value])  # HTTP_404_NOT_FOUND

        # Check Kysely is not active
        if kysely.voimassa_loppupvm >= timezone.now().date():
            raise ValidationError([ErrorMessages.ER029.value])  # HTTP_400_BAD_REQUEST

        oppilaitos = kysely.oppilaitos.oid
        self.authorization([VALSSI_TOTEUTTAJA_LEVEL], [oppilaitos])

        # Check Kysymysryhma laatutekija
        self.validate_laatutekija(kysely.kysymysryhmat.first())

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

        return self.get_summary_by_kyselyid(request, kysely.pk)

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
            main_indicator_key=summary.taustatiedot.get("paaindikaattori", None),
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
    @action(url_path=r"set-skipped/kyselyid=(?P<kyselyid>[0-9]+)", detail=False, methods=["post"])
    def set_summary_skipped_by_kyselyid(self, request, kyselyid):
        kysely = Kysely.objects.filter(kyselyid=kyselyid) \
            .select_related("koulutustoimija", "oppilaitos") \
            .prefetch_related("kysymysryhmat").first()
        if kysely is None:
            raise NotFound([ErrorMessages.ER024.value])  # HTTP_404_NOT_FOUND

        # Check Kysely is not active
        if kysely.voimassa_loppupvm >= timezone.now().date():
            raise ValidationError([ErrorMessages.ER029.value])  # HTTP_400_BAD_REQUEST

        oppilaitos = kysely.oppilaitos.oid
        self.authorization([VALSSI_TOTEUTTAJA_LEVEL], [oppilaitos])

        oppilaitos_name = kysely.oppilaitos.nimi_fi if kysely.oppilaitos else REPORT_VALUE_NULL
        group_info = f"{SKIPPED_TEXT} ({oppilaitos_name})"
        summaries = Summary.objects.filter(
            kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid,
            oppilaitos=kysely.oppilaitos.oid,
            kysely_voimassa_alkupvm=kysely.voimassa_alkupvm)
        if summaries:
            summaries.update(
                group_info=group_info, kuvaus=SKIPPED_TEXT, aineisto=SKIPPED_TEXT, vahvuudet=SKIPPED_TEXT,
                kohteet=SKIPPED_TEXT, keh_toimenpiteet=SKIPPED_TEXT, seur_toimenpiteet=SKIPPED_TEXT,
                is_locked=True,
                is_skipped=True)
        else:
            paaindikaattori_key, sekondaariset_indikaattorit_keys = get_indicators_by_kysely(kysely)
            kysymysryhma = kysely.kysymysryhmat.first()

            # Create Summary object if not already found
            Summary.objects.create(
                kysymysryhmaid=kysely.kysymysryhmat.first().kysymysryhmaid,
                oppilaitos=kysely.oppilaitos.oid,
                koulutustoimija=kysely.koulutustoimija.oid,
                kysely_voimassa_alkupvm=kysely.voimassa_alkupvm,
                group_info=group_info, kuvaus=SKIPPED_TEXT, aineisto=SKIPPED_TEXT, vahvuudet=SKIPPED_TEXT,
                kohteet=SKIPPED_TEXT, keh_toimenpiteet=SKIPPED_TEXT, seur_toimenpiteet=SKIPPED_TEXT,
                taustatiedot=dict(
                    koulutustoimija=kysely.koulutustoimija.oid,
                    paaindikaattori=paaindikaattori_key,
                    sekondaariset_indikaattorit=sekondaariset_indikaattorit_keys,
                    kysymysryhma_name=dict(fi=kysymysryhma.nimi_fi, sv=kysymysryhma.nimi_sv)),
                is_locked=True,
                is_skipped=True,
            )

        return Response("OK")  # HTTP_200_OK

    @method_decorator(csrf_decorators)
    @action(url_path=r"csv/kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija>[0-9.]+)/"
            r"alkupvm=(?P<kysely_voimassa_alkupvm>[0-9-]+)", detail=False)
    def get_summary_csv(self, request, kysymysryhmaid, kysely_voimassa_alkupvm, koulutustoimija):
        self.authorization([VALSSI_PAAKAYTTAJA_LEVEL], [koulutustoimija])

        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        summaries = get_locked_summaries_by_kyselydata(
            kysymysryhmaid, kysely_voimassa_alkupvm, koulutustoimija, language)

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

    @method_decorator(csrf_decorators)
    @action(
        url_path=r"csv/kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
        r"pvm1=(?P<loppupvm1>[0-9-]+)/"
        r"pvm2=(?P<loppupvm2>[0-9-]+)",
        detail=False
    )
    def get_summaries_csv_by_kysymysryhma_and_loppupvm_range(
        self, request, kysymysryhmaid, loppupvm1, loppupvm2
    ):
        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        self.authorization([VALSSI_YLLAPITAJA_LEVEL], VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).first()
        if kysymysryhma is None:
            raise NotFound([ErrorMessages.ER025.value])  # HTTP_404_NOT_FOUND

        try:
            pvm1 = datetime.strptime(loppupvm1, DATE_INPUT_FORMAT).date()
            pvm2 = datetime.strptime(loppupvm2, DATE_INPUT_FORMAT).date()
        except Exception:
            raise ValidationError([ErrorMessages.ER032.value])  # HTTP_400_BAD_REQUEST

        summaries = get_summaries_by_kysymysryhma_and_date_range(kysymysryhmaid, pvm1, pvm2, language)
        if not summaries:
            raise NotFound([ErrorMessages.ER014.value])  # HTTP_404_NOT_FOUND

        csv_file = create_summary_csv(summaries).encode("utf-8-sig")

        # if base64 query param is 'true'
        if self.request.query_params.get("base64", "false").lower() in ("true", "1"):
            encoded_file = base64.b64encode(csv_file)
            return HttpResponse(encoded_file)  # HTTP_200_OK

        return HttpResponse(
            csv_file, content_type="text/csv;charset=utf-8-sig;",
            headers={"Content-Disposition": 'attachment; filename="yllapitaja_summaries.csv"'}
        )  # HTTP_200_OK


class ResultViewset(GenericViewSet, CreateModelMixin):
    serializer_class = ResultSerializer
    permission_classes = (IsAuthenticated, )
    allowed_laatutekijas = (LAATUTEKIJA_PROSESSI, LAATUTEKIJA_RAKENNE)

    def authorization(self, permission_levels, organisaatio_list=None):
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
        if not allowed_oids:
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN
        if organisaatio_list is None:
            return allowed_oids
        elif not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

    def validate_laatutekija(self, kysymysryhma):
        laatutekija = get_laatutekija_by_kysymysryhma(kysymysryhma)
        if laatutekija not in self.allowed_laatutekijas:
            raise ValidationError([ErrorMessages.ER030.value])  # HTTP_400_BAD_REQUEST

    @method_decorator(csrf_decorators)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        koulutustoimija = serializer.validated_data["koulutustoimija"]
        self.authorization([VALSSI_PAAKAYTTAJA_LEVEL], [koulutustoimija])

        kysymysryhmaid = serializer.validated_data["kysymysryhmaid"]
        kysymysryhma = Kysymysryhma.objects.filter(pk=kysymysryhmaid).first()

        # Check Kysymysryhma laatutekija
        self.validate_laatutekija(kysymysryhma)

        serializer.save()

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija>[0-9.]+)/"
            r"alkupvm=(?P<kysely_voimassa_alkupvm>[0-9-]+)", detail=False)
    def get_result(self, request, kysymysryhmaid, koulutustoimija, kysely_voimassa_alkupvm):
        oppilaitos = self.request.query_params.get("oppilaitos", None)
        role = self.request.query_params.get("role", "none").lower()
        if oppilaitos:
            # check permission if oppilaitos given as query param
            # check oppilaitos is related to koulutustoimija
            if not filter_oppilaitos_oids_by_koulutustoimija({oppilaitos}, koulutustoimija):
                raise ValidationError([ErrorMessages.ER028.value])  # HTTP_400_BAD_REQUEST
            self.authorization([VALSSI_TOTEUTTAJA_LEVEL], [oppilaitos])
        elif role == "toteuttaja":
            # check toteuttaja permission if role given as query param
            allowed_oids = self.authorization([VALSSI_TOTEUTTAJA_LEVEL])
            parent_oids = get_parent_oids_by_oppilaitos_oids(allowed_oids)
            # check koulutustoimija is related to allowed oppilaitoses
            if koulutustoimija not in parent_oids:
                raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN
        else:
            self.authorization(
                [VALSSI_YLLAPITAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL],
                VALSSI_YLLAPITAJA_ORGANIZATION_OIDS + [koulutustoimija])

        # Check inactive Kysely is found
        kyselys = Kysely.objects.filter(
            kysymysryhmat__kysymysryhmaid=kysymysryhmaid,
            koulutustoimija__oid=koulutustoimija,
            voimassa_alkupvm=kysely_voimassa_alkupvm,
            voimassa_loppupvm__lt=timezone.now().date())
        if kyselys.first() is None:
            raise NotFound([ErrorMessages.ER024.value])  # HTTP_404_NOT_FOUND

        # Check Kysymysryhma laatutekija
        kysymysryhma = Kysymysryhma.objects.filter(pk=kysymysryhmaid).first()
        self.validate_laatutekija(kysymysryhma)

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

        oppilaitos = self.request.query_params.get("oppilaitos", None)
        if oppilaitos:
            # check permission if oppilaitos given as query param
            # check oppilaitos is related to koulutustoimija
            if not filter_oppilaitos_oids_by_koulutustoimija({oppilaitos}, koulutustoimija_oid):
                raise ValidationError([ErrorMessages.ER028.value])  # HTTP_400_BAD_REQUEST
            self.authorization([VALSSI_TOTEUTTAJA_LEVEL], [oppilaitos])
        else:
            self.authorization(
                [VALSSI_YLLAPITAJA_LEVEL, VALSSI_PAAKAYTTAJA_LEVEL],
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

    @method_decorator(csrf_decorators)
    @action(
        url_path=r"csv/kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
        r"pvm1=(?P<loppupvm1>[0-9-]+)/"
        r"pvm2=(?P<loppupvm2>[0-9-]+)",
        detail=False
    )
    def get_results_csv_by_kysymysryhma_and_loppupvm_range(
        self, request, kysymysryhmaid, loppupvm1, loppupvm2
    ):
        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        self.authorization([VALSSI_YLLAPITAJA_LEVEL], VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid).first()
        if kysymysryhma is None:
            raise NotFound([ErrorMessages.ER025.value])  # HTTP_404_NOT_FOUND

        try:
            pvm1 = datetime.strptime(loppupvm1, DATE_INPUT_FORMAT).date()
            pvm2 = datetime.strptime(loppupvm2, DATE_INPUT_FORMAT).date()
        except Exception:
            raise ValidationError([ErrorMessages.ER032.value])  # HTTP_400_BAD_REQUEST

        results = get_results_by_kysymysryhma_and_date_range(kysymysryhmaid, pvm1, pvm2, language)
        if not results:
            raise NotFound([ErrorMessages.ER020.value])  # HTTP_404_NOT_FOUND

        csv_file = create_result_csv(results).encode("utf-8-sig")

        # if base64 query param is 'true'
        if self.request.query_params.get("base64", "false").lower() in ("true", "1"):
            encoded_file = base64.b64encode(csv_file)
            return HttpResponse(encoded_file)  # HTTP_200_OK

        return HttpResponse(
            csv_file, content_type="text/csv;charset=utf-8-sig;",
            headers={"Content-Disposition": 'attachment; filename="yllapitaja_results.csv"'}
        )  # HTTP_200_OK


class AvailableKyselykierrosListViewset(GenericViewSet):
    serializer_class = ResultSerializer
    permission_classes = (IsAuthenticated, )

    def authorization(self, permission_levels, organisaatio_list=None):
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
            henkilo_permissions, permission_levels
        )
        if not allowed_oids:
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

        if organisaatio_list is None:
            return allowed_oids
        elif not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

        return allowed_oids

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija_oid>[0-9.]+)", detail=False)
    def get_available_kyselykierros_list_by_kysymysryhmaid_and_koulutustoimija(
        self, request, kysymysryhmaid, koulutustoimija_oid
    ):
        allowed_oids = self.authorization([VALSSI_PAAKAYTTAJA_LEVEL], [koulutustoimija_oid])

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

    @method_decorator(csrf_decorators)
    @action(
        url_path=r"pvm1=(?P<voimassa_pvm1>[0-9-]+)/"
        r"pvm2=(?P<voimassa_pvm2>[0-9-]+)",
        detail=False)
    def get_available_kyselykierros_by_loppupvm_range(self, request, voimassa_pvm1, voimassa_pvm2):
        self.authorization([VALSSI_YLLAPITAJA_LEVEL], VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        try:
            pvm1 = datetime.strptime(voimassa_pvm1, DATE_INPUT_FORMAT).date()
            pvm2 = datetime.strptime(voimassa_pvm2, DATE_INPUT_FORMAT).date()
        except Exception:
            raise ValidationError([ErrorMessages.ER032.value])  # HTTP_400_BAD_REQUEST

        kyselykertas = Kyselykerta.objects.filter(
            voimassa_loppupvm__range=(pvm1, pvm2)
        ).select_related(
            "kyselyid"
        ).prefetch_related(
            "kyselyid__kysymysryhmat"
        ).order_by("-voimassa_loppupvm")

        kysymysryhma_objs = [kyselykerta.kyselyid.kysymysryhmat.all()[0] for kyselykerta in kyselykertas]
        kysymysryhma_ids = {obj.pk for obj in kysymysryhma_objs}

        kysymysryhma_objs = remove_duplicate_kysymysryhmas(kysymysryhma_objs)  # Keep latest (first in list)
        kysymysryhma_objs = sort_kysymysryhmas_by_laatutekija(kysymysryhma_objs)

        summary_objs = Summary.objects.filter(kysymysryhmaid__in=kysymysryhma_ids, is_locked=True)
        result_objs = Result.objects.filter(kysymysryhmaid__in=kysymysryhma_ids, is_locked=True)

        serializer = KyselykertaAvailableSerializer(kysymysryhma_objs, many=True, context={
            "kyselykertas": kyselykertas,
            "summary_objs": summary_objs,
            "result_objs": result_objs,
        })

        return Response(serializer.data)  # HTTP_200_OK


class AnswersExportViewset(GenericViewSet):
    permission_classes = (IsAuthenticated,)

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
            if impersonate_org not in organisaatio_list:
                raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN
            return
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
        if not any([org in allowed_oids for org in organisaatio_list]):
            raise PermissionDenied([ErrorMessages.ER011.value])  # HTTP_403_FORBIDDEN

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"koulutustoimija=(?P<koulutustoimija>[0-9.]+)/"
            r"alkupvm=(?P<voimassa_alkupvm>[0-9-]+)", detail=False)
    def get_answers_csv_by_kyselys(self, request, kysymysryhmaid, koulutustoimija, voimassa_alkupvm):
        self.authorization([VALSSI_PAAKAYTTAJA_LEVEL], [koulutustoimija])

        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        kyselys = Kysely.objects.filter(
            kysymysryhmat__kysymysryhmaid=kysymysryhmaid,
            koulutustoimija__oid=koulutustoimija,
            voimassa_alkupvm=voimassa_alkupvm) \
            .select_related("koulutustoimija", "oppilaitos") \
            .prefetch_related("kysymysryhmat")
        if not kyselys.exists():
            raise NotFound([ErrorMessages.ER018.value])  # HTTP_404_NOT_FOUND

        kysymysryhma = kyselys.first().kysymysryhmat.first()
        lomaketyyppi = kysymysryhma.metatiedot.get("lomaketyyppi")

        if lomaketyyppi in REPORT_CSV_SINGLELINE_TYPES:
            csv_file = create_answers_singleline_csv_by_kyselys(
                kyselys, kysymysryhma, language, hide_text_type_answers=True,
            )
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

    @method_decorator(csrf_decorators)
    @action(url_path=r"kysymysryhmaid=(?P<kysymysryhmaid>[0-9]+)/"
            r"alkupvm1=(?P<voimassa_alkupvm1>[0-9-]+)/"
            r"alkupvm2=(?P<voimassa_alkupvm2>[0-9-]+)", detail=False)
    def get_answers_csv_by_kysymysryhma_and_alkupvm_range(
            self, request, kysymysryhmaid, voimassa_alkupvm1, voimassa_alkupvm2):
        self.authorization([VALSSI_YLLAPITAJA_LEVEL], VALSSI_YLLAPITAJA_ORGANIZATION_OIDS)

        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        is_siirto = self.request.query_params.get("is_siirto", "false").lower() in ("true", "1")

        try:
            alkupvm1 = datetime.strptime(voimassa_alkupvm1, DATE_INPUT_FORMAT).date()
            alkupvm2 = datetime.strptime(voimassa_alkupvm2, DATE_INPUT_FORMAT).date()
        except Exception:
            raise ValidationError([ErrorMessages.ER032.value])  # HTTP_400_BAD_REQUEST

        kyselys = Kysely.objects.filter(
            kysymysryhmat__kysymysryhmaid=kysymysryhmaid,
            voimassa_alkupvm__range=(alkupvm1, alkupvm2)) \
            .select_related("koulutustoimija", "oppilaitos") \
            .prefetch_related("kysymysryhmat")
        if not kyselys.exists():
            raise NotFound([ErrorMessages.ER031.value])  # HTTP_404_NOT_FOUND

        kysymysryhma = kyselys.first().kysymysryhmat.first()
        lomaketyyppi = kysymysryhma.metatiedot.get("lomaketyyppi")

        if is_siirto and lomaketyyppi in REPORT_CSV_SINGLELINE_TYPES:
            csv_file = create_answers_singleline_csv_by_kyselys(
                kyselys, kysymysryhma, language, is_siirto=True, hide_hidden_report_questions=False,
            )
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


class LomakeUsageExportViewset(GenericViewSet):
    permission_classes = (IsAuthenticated,)

    def authorization(self):
        username = self.request.user
        henkilo_oid, henkilo_permissions = get_henkilo_oid_and_permissions(username)
        if not henkilo_oid:
            raise PermissionDenied([ErrorMessages.ER001.value])  # HTTP_403_FORBIDDEN

        validate_yllapitaja_permission(henkilo_permissions)

    @method_decorator(csrf_decorators)
    @action(url_path=r"pvm1=(?P<voimassa_pvm1>[0-9-]+)/"
            r"pvm2=(?P<voimassa_pvm2>[0-9-]+)", detail=False)
    def get_lomake_usage_csv(self, request, voimassa_pvm1, voimassa_pvm2):
        self.authorization()

        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        try:
            pvm1 = datetime.strptime(voimassa_pvm1, DATE_INPUT_FORMAT).date()
            pvm2 = datetime.strptime(voimassa_pvm2, DATE_INPUT_FORMAT).date()
        except Exception:
            raise ValidationError([ErrorMessages.ER032.value])  # HTTP_400_BAD_REQUEST

        if pvm2 < pvm1:
            raise ValidationError([ErrorMessages.ER033.value])  # HTTP_400_BAD_REQUEST

        kyselys = Kysely.objects.filter(
            Q(voimassa_alkupvm__range=(pvm1, pvm2)) |
            Q(voimassa_loppupvm__range=(pvm1, pvm2)) |
            Q(voimassa_alkupvm__lte=pvm1, voimassa_loppupvm__gte=pvm2)
        ).select_related(
            "koulutustoimija", "oppilaitos"
        ).prefetch_related(
            "kysymysryhmat"
        )
        if not kyselys.exists():
            raise NotFound([ErrorMessages.ER024.value])  # HTTP_404_NOT_FOUND

        csv_file = create_lomake_usage_csv_by_kyselys(kyselys, pvm1, pvm2, language)
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
        worker_active, worker_count = check_celery_worker_running()
        health_response = dict(
            environment=settings.ENVIRONMENT,
            version=VALSSI_VERSION,
            build_id=get_ci_pipeline_number(),
            worker_active=worker_active,
            worker_count=worker_count,
        )

        if not worker_active:
            logger.error("Celery worker is not active.")
            return Response(health_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health_response, status=status.HTTP_200_OK)


class HealthDbViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        try:
            user_count = User.objects.count()
        except Exception:
            logger.error("Raportointipalvelu-db connection error.")
            return Response("Raportointipalvelu-db connection error.", status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"db": user_count}, status=status.HTTP_200_OK)
