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

from kyselyt.constants import ANSWER_PDF_TEMPLATE_NO, VALSSI_VERSION, FAILED_MSGS_EARLIEST_CREATED_DEADLINE_FOR_ERROR
from kyselyt.models import Message, MessageQueue
from kyselyt.serializers import (
    MessagePostSerializer, AccessTokenObtainSerializer, PdfUploadDataSerializer, MessagePostSingleSerializer,
    MessageIdsPostSerializer)
from kyselyt.tasks import send_email_by_message_queue_task
from kyselyt.utils import (
    check_celery_worker_running, get_ci_pipeline_number, get_failed_messages_count,
    get_earliest_failed_message_time_ago_minutes)


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
        pdf_file_fi = request.FILES["pdf_file_fi"]
        pdf_file_fi.name = request.data["filename_fi"]
        pdf_file_fi_encoded = b64encode(pdf_file_fi.read()).decode("utf-8")
        pdf_file_sv = request.FILES["pdf_file_sv"]
        pdf_file_sv.name = request.data["filename_sv"]
        pdf_file_sv_encoded = b64encode(pdf_file_sv.read()).decode("utf-8")

        pdfs_encoded = list()
        pdfs_encoded.append(dict(file_encoded=pdf_file_fi_encoded, filename=request.data["filename_fi"]))
        pdfs_encoded.append(dict(file_encoded=pdf_file_sv_encoded, filename=request.data["filename_sv"]))

        # Add optional EN pdf
        if request.data.get("filename_en", None):
            pdf_file_en = request.FILES["pdf_file_en"]
            pdf_file_en.name = request.data["filename_en"]
            pdf_file_en_encoded = b64encode(pdf_file_en.read()).decode("utf-8")
            pdfs_encoded.append(dict(file_encoded=pdf_file_en_encoded, filename=request.data["filename_en"]))

        saved_messages = file_and_data_serializer.save()
        messages_serializer = MessagePostSingleSerializer(saved_messages, many=True)

        # Add to MessageQueue table
        message_queue_objs = []
        msg_ids_to_add_celery_queue = []
        for i, msg in enumerate(file_and_data_serializer.validated_data["messages"]):
            msg_id = messages_serializer.data[i]["msg_id"]

            # this is for frontend testing purposes only (disabled in production)
            if not settings.PRODUCTION_ENV and msg["email"].endswith(".invalid"):
                continue

            msg_ids_to_add_celery_queue.append(msg_id)

            message_queue_objs.append(
                MessageQueue(
                    email=msg["email"],
                    vastaajatunnus=msg["vastaajatunnus"],
                    message=msg["message"],
                    template=msg["template"],
                    msg_id=msg_id,
                    pdfs_encoded=pdfs_encoded,
                )
            )

        MessageQueue.objects.bulk_create(message_queue_objs)

        # Send messages (add to celery-queue)
        for msg_id in msg_ids_to_add_celery_queue:
            send_email_by_message_queue_task.delay(msg_id)

        return Response(messages_serializer.data, status=status.HTTP_201_CREATED)


class PdfUploadViewSet(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, format=None):
        upload_data_serializer = PdfUploadDataSerializer(data=request.data)
        upload_data_serializer.is_valid(raise_exception=True)

        # get pdf from request, base64-encode file + decode to str-format
        pdf_file = request.FILES["pdf_file"]
        pdf_file.name = request.data["filename"]
        pdf_file_encoded = b64encode(pdf_file.read()).decode("utf-8")
        pdfs_encoded = [dict(file_encoded=pdf_file_encoded, filename=request.data["filename"])]

        email = upload_data_serializer.validated_data["email"]
        end_date = upload_data_serializer.validated_data["end_date"]
        message_serializer = MessagePostSingleSerializer(
            data={"template": ANSWER_PDF_TEMPLATE_NO,
                  "email": email,
                  "end_date": end_date, "vastaajatunnus": "null", "message": "null"})
        message_serializer.is_valid(raise_exception=True)
        message_serializer.save()

        msg_id = message_serializer.data["msg_id"]

        # Add to MessageQueue table
        MessageQueue.objects.create(
            email=email,
            vastaajatunnus="",
            message="",
            template=ANSWER_PDF_TEMPLATE_NO,
            msg_id=msg_id,
            pdfs_encoded=pdfs_encoded)

        # Send answer pdf (add to celery-queue)
        send_email_by_message_queue_task.delay(msg_id)

        return Response("OK", status=status.HTTP_201_CREATED)


class AccessTokenView(TokenObtainPairView):
    serializer_class = AccessTokenObtainSerializer

    @method_decorator(ratelimit(key="ip", rate=f"{settings.RATELIMIT_PER_MINUTE}/m", block=True))
    @method_decorator(ratelimit(key="ip", rate=f"{settings.RATELIMIT_PER_HOUR}/h", block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class HealthViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        worker_active, worker_count = check_celery_worker_running()
        failed_msg_count = get_failed_messages_count(default_value=9999)
        earliest_failed_msg_time = get_earliest_failed_message_time_ago_minutes()
        health_response = dict(
            environment=settings.ENVIRONMENT,
            version=VALSSI_VERSION,
            build_id=get_ci_pipeline_number(),
            worker_active=worker_active,
            worker_count=worker_count,
            failed_msgs=failed_msg_count,
            failed_msg_time=earliest_failed_msg_time,
        )

        if not worker_active:
            logger.error("Celery worker is not active.")
            return Response(health_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        elif earliest_failed_msg_time > FAILED_MSGS_EARLIEST_CREATED_DEADLINE_FOR_ERROR:
            logger.error("Earliest failed msg created more than "
                         f"{FAILED_MSGS_EARLIEST_CREATED_DEADLINE_FOR_ERROR} min ago.")
            return Response(health_response, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health_response, status=status.HTTP_200_OK)


class HealthDbViewSet(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        try:
            user_count = User.objects.count()
        except Exception:
            logger.error("Valssi-db connection error.")
            return Response("Valssi-db connection error.", status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"db": user_count}, status=status.HTTP_200_OK)
