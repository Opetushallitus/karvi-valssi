from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import SerializerMethodField

from kyselyt.constants import DATE_INPUT_FORMAT, KYSELYSEND_MESSAGE_MAX_LENGTH
from kyselyt.enums.error_messages import ErrorMessages
from kyselyt.models import Kyselykerta, KyselySend, Indikaattori, Scale, MalfunctionMessage


class KyselySendPostSerializer(serializers.ModelSerializer):
    kyselykerta = serializers.IntegerField(required=False)
    vastaajatunnus = serializers.CharField(required=False)
    template = serializers.IntegerField(required=False)
    msg_id = serializers.IntegerField(required=False)
    msg_status = serializers.CharField(required=False)
    message = serializers.CharField(required=False)

    class Meta:
        model = KyselySend
        fields = ["tyontekija_id",
                  "email",
                  "kyselykerta",
                  "vastaajatunnus",
                  "template",
                  "msg_id",
                  "msg_status",
                  "message"]


class KyselySendSerializer(serializers.ModelSerializer):
    message = serializers.CharField(allow_blank=True)

    class Meta:
        model = KyselySend
        fields = ["tyontekija_id",
                  "email",
                  "kyselykerta",
                  "vastaajatunnus",
                  "msg_id",
                  "msg_status",
                  "message"]


class KyselykertaTyontekijatPostSerializer(serializers.Serializer):
    kyselykerta = serializers.IntegerField(required=True)
    tyontekijat = KyselySendPostSerializer(required=True, many=True)
    voimassa_alkupvm = serializers.DateField(required=True, input_formats=[DATE_INPUT_FORMAT])
    voimassa_loppupvm = serializers.DateField(required=True, input_formats=[DATE_INPUT_FORMAT])
    message = serializers.CharField(required=True, allow_blank=True, max_length=KYSELYSEND_MESSAGE_MAX_LENGTH)

    def validate(self, attrs):
        # validate kyselykerta
        try:
            kyselykerta = Kyselykerta.objects.get(kyselykertaid=attrs["kyselykerta"])
        except Kyselykerta.DoesNotExist:
            raise ValidationError([ErrorMessages.ER006.value])  # HTTP_400_BAD_REQUEST

        # check if kyselykerta is locked
        if kyselykerta.lukittu is True:
            raise ValidationError([ErrorMessages.ER015.value])  # HTTP_400_BAD_REQUEST

        # validate voimassa-dates
        if attrs["voimassa_alkupvm"] > attrs["voimassa_loppupvm"]:
            raise ValidationError([ErrorMessages.VA009.value])  # HTTP_400_BAD_REQUEST
        if attrs["voimassa_alkupvm"] < kyselykerta.voimassa_alkupvm or (
                attrs["voimassa_loppupvm"] > kyselykerta.voimassa_loppupvm):
            error = dict(ErrorMessages.VA006.value)
            error["description"] = error["description"].format(
                kyselykerta.voimassa_alkupvm, kyselykerta.voimassa_loppupvm)
            raise ValidationError([error])  # HTTP_400_BAD_REQUEST

        return super().validate(attrs)

    def create(self, validated_data):
        # save tyontekijat only
        kyselysend_serializer = KyselySendSerializer(data=validated_data["tyontekijat"], many=True)
        kyselysend_serializer.is_valid(raise_exception=True)
        return kyselysend_serializer.save()


class KyselySendUpdateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)

    class Meta:
        model = KyselySend
        fields = ["id", "email"]


class KyselySendListSerializer(serializers.ModelSerializer):
    class Meta:
        model = KyselySend
        fields = ["id", "tyontekija_id", "email", "msg_status"]


class IndikaattoriSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indikaattori
        fields = ["group_id", "key", "laatutekija"]


class ScaleSerializer(serializers.ModelSerializer):
    label = SerializerMethodField()

    class Meta:
        model = Scale
        fields = ["name", "order_no", "label", "min_value", "max_value", "default_value", "step_count", "scale",
                  "is_visible", "eos_allowed", "eos_value"]

    def get_label(self, instance):
        return {"fi": instance.label_fi, "sv": instance.label_sv}


class KysymysryhmaOrganisaatioSerializer(serializers.Serializer):
    kysymysryhmaid = serializers.IntegerField(required=True)
    organisaatio = serializers.CharField(required=True)


class MalfunctionMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MalfunctionMessage
        fields = ["code", "service", "message", "is_active"]
