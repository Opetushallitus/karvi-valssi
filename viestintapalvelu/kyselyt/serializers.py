from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from kyselyt.constants import VASTAAJATUNNUS_MAX_LENGTH, EMAIL_STATUS_SENT, EMAIL_STATUS_FAILED
from kyselyt.models import Message


class MessagePostSingleSerializer(serializers.ModelSerializer):
    msg_status = serializers.CharField(default=EMAIL_STATUS_SENT)
    vastaajatunnus = serializers.CharField(required=True, write_only=True, max_length=VASTAAJATUNNUS_MAX_LENGTH)
    message = serializers.CharField(required=True, write_only=True, allow_blank=True)

    class Meta:
        model = Message
        fields = ['msg_id',
                  'email',
                  'template',
                  'msg_status',
                  'vastaajatunnus',
                  'message']

    def create(self, validated_data):
        validated_data.pop("vastaajatunnus")
        validated_data.pop("message")

        # this is for frontend testing purposes only (disabled in production)
        if not settings.PRODUCTION_ENV and validated_data["email"].endswith(".invalid"):
            validated_data["msg_status"] = EMAIL_STATUS_FAILED

        return super().create(validated_data)


# messages is implemented using JSONField because
# "DRF doesn't support nested writable serializers with multipart/form-data"
# and "Nested serializers that are flagged many=True are not working with multipart/form-data"
# (https://github.com/encode/django-rest-framework/issues/7262)
# https://www.django-rest-framework.org/api-guide/relations/#writable-nested-serializers
class MessagePostSerializer(serializers.Serializer):
    filename_fi = serializers.CharField(required=True)
    filename_sv = serializers.CharField(required=True)
    pdf_file_fi = serializers.FileField(required=True, allow_empty_file=True)
    pdf_file_sv = serializers.FileField(required=True, allow_empty_file=True)
    messages = serializers.JSONField(required=True)

    def create(self, validated_data):
        # save messages only
        messages_serializer = MessagePostSingleSerializer(data=validated_data["messages"], many=True)
        messages_serializer.is_valid(raise_exception=True)
        return messages_serializer.save()


class MessageIdsPostSerializer(serializers.Serializer):
    msg_ids = serializers.ListField(child=serializers.IntegerField(), required=True)


class PdfUploadDataSerializer(serializers.Serializer):
    filename = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    pdf_file = serializers.FileField(required=True, allow_empty_file=True)


class AccessTokenObtainSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data['access'] = str(refresh.access_token)

        return data
