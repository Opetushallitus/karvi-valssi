import logging

from base64 import b64encode

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView

from kyselyt.constants import ANSWER_PDF_TEMPLATE_NO, VALSSI_VERSION
from kyselyt.models import Message
from kyselyt.serializers import (
    MessagePostSerializer, AccessTokenObtainSerializer, PdfUploadDataSerializer, MessagePostSingleSerializer,
    MessageIdsPostSerializer)
from kyselyt.tasks import send_email_to_answer_task
from kyselyt.utils import check_celery_worker_running, get_ci_pipeline_number, get_failed_task_count


logger = logging.getLogger(__name__)


class MessageListViewSet(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, format=None):
        msg_ids_serializer = MessageIdsPostSerializer(data=request.data)
        msg_ids_serializer.is_valid(raise_exception=True)

        msgs = Message.objects.filter(pk__in=msg_ids_serializer.validated_data["msg_ids"])
        msgs_list = [{"msg_id": msg.msg_id,
                      "email": msg.email,
                      "template": msg.template,
                      "msg_status": msg.msg_status,
                      "created": msg.created} for msg in msgs]

        return Response(msgs_list, status=status.HTTP_200_OK)


class SendViewSet(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, format=None):
        file_and_data_serializer = MessagePostSerializer(data=request.data)
        file_and_data_serializer.is_valid(raise_exception=True)

        # get pdfs from request, base64-encode files + decode to str-format
        pdf_file_fi = request.FILES['pdf_file_fi']
        pdf_file_fi_encoded = b64encode(pdf_file_fi.read()).decode("utf-8")
        pdf_file_sv = request.FILES['pdf_file_sv']
        pdf_file_sv_encoded = b64encode(pdf_file_sv.read()).decode("utf-8")

        pdfs_encoded = list()
        pdfs_encoded.append(dict(file_encoded=pdf_file_fi_encoded, filename=request.data['filename_fi']))
        pdfs_encoded.append(dict(file_encoded=pdf_file_sv_encoded, filename=request.data['filename_sv']))

        saved_messages = file_and_data_serializer.save()
        messages_serializer = MessagePostSingleSerializer(saved_messages, many=True)

        # send kyselyt (add to celery-queue)
        for i, msg in enumerate(file_and_data_serializer.validated_data["messages"]):
            msg_id = messages_serializer.data[i]["msg_id"]

            # this is for frontend testing purposes only (disabled in production)
            if not settings.PRODUCTION_ENV and msg["email"].endswith(".invalid"):
                continue

            send_email_to_answer_task.delay(
                msg["email"], msg["vastaajatunnus"], msg["message"], msg["template"], msg_id, pdfs_encoded)

        return Response(messages_serializer.data, status=status.HTTP_201_CREATED)


class PdfUploadViewSet(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, format=None):
        upload_data_serializer = PdfUploadDataSerializer(data=request.data)
        upload_data_serializer.is_valid(raise_exception=True)

        # get pdf from request, base64-encode file + decode to str-format
        pdf_file = request.FILES['pdf_file']
        pdf_file_encoded = b64encode(pdf_file.read()).decode("utf-8")
        pdfs_encoded = [dict(file_encoded=pdf_file_encoded, filename=request.data['filename'])]

        email = upload_data_serializer.validated_data["email"]
        message_serializer = MessagePostSingleSerializer(
            data={"template": ANSWER_PDF_TEMPLATE_NO, "email": email, "vastaajatunnus": "null", "message": "null"})
        message_serializer.is_valid(raise_exception=True)
        message_serializer.save()

        # send answer pdf (add to celery-queue)
        msg_id = message_serializer.data["msg_id"]
        send_email_to_answer_task.delay(email, "", "", ANSWER_PDF_TEMPLATE_NO, msg_id, pdfs_encoded)

        return Response("OK", status=status.HTTP_201_CREATED)


class AccessTokenView(TokenObtainPairView):
    serializer_class = AccessTokenObtainSerializer

    @method_decorator(ratelimit(key='ip', rate=f'{settings.TOKEN_RATELIMIT_PER_MINUTE}/m', block=True))
    @method_decorator(ratelimit(key='ip', rate=f'{settings.TOKEN_RATELIMIT_PER_HOUR}/h', block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class HealthViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        worker_active = check_celery_worker_running()
        failedtask_count = get_failed_task_count(default_value=9999)
        health_response = dict(
            environment=settings.ENVIRONMENT,
            version=VALSSI_VERSION,
            build_id=get_ci_pipeline_number(),
            worker_active=worker_active,
            failed_msgs=failedtask_count)

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
            logger.error("Valssi-db connection error.")
            return Response("Valssi-db connection error.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"db": user_count}, status=status.HTTP_200_OK)
