from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from kyselyt.constants import DATE_INPUT_FORMAT, KYSELYSEND_MESSAGE_MAX_LENGTH, MAX_ALUEJAKO_ALUE_COUNT
from kyselyt.enums.error_messages import ErrorMessages
from kyselyt.models import Kyselykerta, KyselySend, Indikaattori, Scale, MalfunctionMessage, AluejakoAlue, Organisaatio


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
    key = serializers.CharField(source="indicator_key")

    class Meta:
        model = Indikaattori
        fields = ["group_id", "key", "laatutekija"]


class ScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scale
        fields = [
            "name",
            "order_no",
            "label",
            "min_value",
            "max_value",
            "default_value",
            "step_count",
            "scale",
            "is_visible",
            "eos_allowed",
            "eos_value",
        ]


class KysymysryhmaOrganisaatioSerializer(serializers.Serializer):
    kysymysryhmaid = serializers.IntegerField(required=True)
    organisaatio = serializers.CharField(required=True)


class MalfunctionMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MalfunctionMessage
        fields = ["code", "service", "message", "is_active"]


class AluejakoAluePostSerializer(serializers.ModelSerializer):
    koulutustoimija = serializers.CharField(required=True, allow_blank=False, max_length=100)
    name_fi = serializers.CharField(required=True, allow_blank=False, max_length=100)
    name_sv = serializers.CharField(required=True, allow_blank=False, max_length=100)

    class Meta:
        model = AluejakoAlue
        fields = ["koulutustoimija", "name_fi", "name_sv"]

    def validate(self, attrs):
        # Check koulutustoimija is found
        try:
            koulutustoimija = Organisaatio.objects.get(oid=attrs["koulutustoimija"])
        except Organisaatio.DoesNotExist:
            raise ValidationError([ErrorMessages.ER024.value])  # HTTP_400_BAD_REQUEST

        # Validate max aluejako count
        alue_count = AluejakoAlue.objects.filter(koulutustoimija=koulutustoimija.oid).count()
        if alue_count >= MAX_ALUEJAKO_ALUE_COUNT:
            error = dict(ErrorMessages.ER025.value)
            error["description"] = error["description"].format(MAX_ALUEJAKO_ALUE_COUNT)
            raise ValidationError([error])  # HTTP_400_BAD_REQUEST

        return super().validate(attrs)


class AluejakoAluePutSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    koulutustoimija = serializers.CharField(required=True, allow_blank=False, max_length=100)
    name_fi = serializers.CharField(required=True, allow_blank=False, max_length=100)
    name_sv = serializers.CharField(required=True, allow_blank=False, max_length=100)
    oppilaitos_oids = serializers.ListField(
        child=serializers.CharField(required=True, allow_blank=False, max_length=100),
        allow_empty=True)

    def validate(self, attrs):
        # Check koulutustoimija is found
        try:
            Organisaatio.objects.get(oid=attrs["koulutustoimija"])
        except Organisaatio.DoesNotExist:
            raise ValidationError([ErrorMessages.ER024.value])  # HTTP_400_BAD_REQUEST

        # Check AluejakoAlue is found with given id and koulutustoimija
        try:
            AluejakoAlue.objects.get(id=attrs["id"], koulutustoimija=attrs["koulutustoimija"])
        except AluejakoAlue.DoesNotExist:
            raise ValidationError([ErrorMessages.ER026.value])  # HTTP_400_BAD_REQUEST

        return super().validate(attrs)

    def update(self):
        validated_data = self.validated_data

        # Update names
        AluejakoAlue.objects.filter(
            id=validated_data["id"],
            koulutustoimija=validated_data["koulutustoimija"]) \
            .update(
                name_fi=validated_data["name_fi"],
                name_sv=validated_data["name_sv"],)

        return None


class AluejakoAlueDeleteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=True)
    koulutustoimija = serializers.CharField(required=True, allow_blank=False, max_length=100)

    class Meta:
        model = AluejakoAlue
        fields = ["id", "koulutustoimija"]

    def validate(self, attrs):
        # Check koulutustoimija is found
        try:
            Organisaatio.objects.get(oid=attrs["koulutustoimija"])
        except Organisaatio.DoesNotExist:
            raise ValidationError([ErrorMessages.ER024.value])  # HTTP_400_BAD_REQUEST

        # Check AluejakoAlue is found with given id and koulutustoimija
        try:
            AluejakoAlue.objects.get(id=attrs["id"], koulutustoimija=attrs["koulutustoimija"])
        except AluejakoAlue.DoesNotExist:
            raise ValidationError([ErrorMessages.ER026.value])  # HTTP_400_BAD_REQUEST

        return super().validate(attrs)

    def delete(self):
        id = self.validated_data["id"]
        koulutustoimija = self.validated_data["koulutustoimija"]

        # perform delete
        AluejakoAlue.objects.filter(id=id, koulutustoimija=koulutustoimija).delete()

        return
