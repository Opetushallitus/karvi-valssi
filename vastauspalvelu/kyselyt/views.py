import logging

from django.conf import settings
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from kyselyt.constants import VALSSI_VERSION
from kyselyt.decorators import custom_ratelimit
from kyselyt.models import Kysely, Kyselykerta, Vastaus, VastausSend, TempVastaus
from kyselyt.serializers import (
    KyselykertaSerializer, VastaajaPostSerializer, TempVastausSerializer, TempVastausPostSerializer)
from kyselyt.tasks import send_answer_pdf_task
from kyselyt.utils import validate_language_code, check_celery_worker_running, get_ci_pipeline_number
from kyselyt.utils_auth import get_scales, get_malfunction_message
from kyselyt.validators import validate_vastaajatunnus_tunnus


logger = logging.getLogger(__name__)

# ratelimit rates
RATE_PER_MIN = f"{settings.RATELIMIT_PER_MINUTE}/m"
RATE_PER_H = f"{settings.RATELIMIT_PER_HOUR}/h"


class KyselykertaViewSet(GenericViewSet, RetrieveModelMixin):
    serializer_class = KyselykertaSerializer
    queryset = Kyselykerta.objects.none()

    @method_decorator(custom_ratelimit(group_prefix="vastauspalvelu_kk", rate=RATE_PER_MIN))
    @method_decorator(custom_ratelimit(group_prefix="vastauspalvelu", rate=RATE_PER_H))
    def retrieve(self, request, pk=None):
        vastaajatunnus = validate_vastaajatunnus_tunnus(pk)
        kyselykerta = Kyselykerta.objects.get(kyselykertaid=vastaajatunnus.kyselykertaid.kyselykertaid)
        serializer = KyselykertaSerializer(
            kyselykerta, context=dict(vastaajatunnus=vastaajatunnus))

        return Response(serializer.data)  # HTTP_200_OK


class VastaaViewSet(GenericViewSet):
    serializer_class = VastaajaPostSerializer
    queryset = Kysely.objects.none()

    @method_decorator(custom_ratelimit(group_prefix="vastauspalvelu_va", rate=RATE_PER_MIN))
    @method_decorator(custom_ratelimit(group_prefix="vastauspalvelu", rate=RATE_PER_H))
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vastaaja = serializer.save()
        email = serializer.validated_data["email"]
        language = self.request.query_params.get("language", "fi")
        validate_language_code(language)

        # Add answers to pdf emailing queue if email is given
        if email:
            vastaussend = VastausSend.objects.create(
                email=email,
                vastaajaid=vastaaja,
                language=language)
            send_answer_pdf_task.delay(vastaussend.id)

        return Response("OK", status=status.HTTP_201_CREATED)


class TempVastausViewSet(GenericViewSet):
    serializer_class = TempVastausSerializer
    queryset = TempVastaus.objects.none()

    @method_decorator(custom_ratelimit(group_prefix="vastauspalvelu_kk", rate=RATE_PER_MIN))
    @method_decorator(custom_ratelimit(group_prefix="vastauspalvelu", rate=RATE_PER_H))
    def retrieve(self, request, pk=None):
        validate_vastaajatunnus_tunnus(pk)
        tempvastaus_objs = TempVastaus.objects.filter(vastaajatunnus=pk)
        serializer = TempVastausSerializer(tempvastaus_objs, many=True)

        return Response(serializer.data)  # HTTP_200_OK

    @method_decorator(custom_ratelimit(group_prefix="vastauspalvelu_va", rate=RATE_PER_MIN))
    @method_decorator(custom_ratelimit(group_prefix="vastauspalvelu", rate=RATE_PER_H))
    def create(self, request):
        serializer = TempVastausPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response("OK", status=status.HTTP_201_CREATED)


class ScaleViewSet(APIView):
    def get(self, request, format=None):
        scales = get_scales()
        if scales is None:
            return Response("Virkailijapalvelu connection error.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(scales)  # HTTP_200_OK


class MalfunctionMessageViewSet(APIView):
    def get(self, request, format=None):
        msg = get_malfunction_message()
        if msg is None:
            logger.error("Virkailijapalvelu connection error.")
            return Response({"message": None})  # HTTP_200_OK
        return Response(msg)  # HTTP_200_OK


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
            kyselyt_count = Kysely.objects.count()
        except Exception:
            logger.error("Valssi-db connection error.")
            return Response("Valssi-db connection error.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            _ = Vastaus.objects.count()
        except Exception:
            logger.error("Vastauspalvelu-db connection error.")
            return Response("Vastauspalvelu-db connection error.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"db": kyselyt_count}, status=status.HTTP_200_OK)
