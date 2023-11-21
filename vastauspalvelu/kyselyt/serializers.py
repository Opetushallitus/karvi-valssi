from collections import OrderedDict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError as ValidationErrorRest
from rest_framework.fields import SerializerMethodField

from kyselyt.constants import ALL_ANSWER_TYPES, NUMEROVALINTA_ANSWER_TYPES, VAPAATEKSTI_ANSWER_TYPES
from kyselyt.enums.error_messages import ErrorMessages
from kyselyt.models import (
    Kysely, Kyselykerta, KyselyKysymysryhma, Kysymysryhma, Kysymys, Vastaus, Vastaaja, Vastaajatunnus, TempVastaus)
from kyselyt.utils import sanitize_string
from kyselyt.utils_auth import get_tyontekija_data
from kyselyt.validators import (
    validate_only_one_answer_type, validate_vastaajatunnus_tunnus, validate_eos_when_not_allowed,
    validate_numerovalinta_answer_types, validate_string_answer_types, validate_answers_for_mandatory_questions,
    validate_answer_counts, validate_vastaajatunnus_kohteiden_lkm)


class MatriisiKysymysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kysymys
        fields = ["kysymysid",
                  "pakollinen",
                  "poistettava",
                  "vastaustyyppi",
                  "kysymys_fi",
                  "kysymys_sv",
                  "kysymys_en",
                  "jarjestys",
                  "monivalinta_max",
                  "max_vastaus",
                  "eos_vastaus_sallittu",
                  "jatkokysymys",
                  "rajoite",
                  "selite_fi",
                  "selite_sv",
                  "selite_en",
                  "raportoitava",
                  "metatiedot",
                  "matriisi_jarjestys"]


class KysymysSerializer(serializers.ModelSerializer):
    matriisikysymykset = SerializerMethodField()

    class Meta:
        model = Kysymys
        fields = ["kysymysid",
                  "pakollinen",
                  "poistettava",
                  "vastaustyyppi",
                  "kysymys_fi",
                  "kysymys_sv",
                  "kysymys_en",
                  "jarjestys",
                  "monivalinta_max",
                  "max_vastaus",
                  "eos_vastaus_sallittu",
                  "jatkokysymys",
                  "rajoite",
                  "selite_fi",
                  "selite_sv",
                  "selite_en",
                  "raportoitava",
                  "metatiedot",
                  "matriisikysymykset"]

    def get_matriisikysymykset(self, instance):
        if instance.vastaustyyppi != "matrix_root":
            return []
        matriisikysymykset = (
            Kysymys.objects.filter(matriisi_kysymysid=instance.kysymysid)
            .filter(matriisi_jarjestys__gt=0).order_by("matriisi_jarjestys"))
        return MatriisiKysymysSerializer(matriisikysymykset, many=True, read_only=True).data


class KysymysryhmaSerializer(serializers.ModelSerializer):
    kysymykset = SerializerMethodField()

    class Meta:
        model = Kysymysryhma
        fields = ["kysymysryhmaid",
                  "taustakysymykset",
                  "valtakunnallinen",
                  "nimi_fi",
                  "nimi_sv",
                  "nimi_en",
                  "selite_fi",
                  "selite_sv",
                  "selite_en",
                  "tila",
                  "kuvaus_fi",
                  "kuvaus_sv",
                  "kuvaus_en",
                  "metatiedot",
                  "kysymykset"]

    def get_kysymykset(self, instance):
        # filter out matrixes other than matrix-root
        kysymykset = (
            instance.kysymykset.filter(matriisi_jarjestys=0) |
            instance.kysymykset.filter(matriisi_jarjestys=None)).order_by("jarjestys")
        return KysymysSerializer(kysymykset, many=True, read_only=True).data


class KyselyKysymysryhmaSerializer(serializers.ModelSerializer):
    kysymysryhma = KysymysryhmaSerializer(source="kysymysryhmaid", read_only=True)

    class Meta:
        model = KyselyKysymysryhma
        fields = ["kysymysryhma", "jarjestys"]


class KyselySingleSerializer(serializers.ModelSerializer):
    kysymysryhmat = SerializerMethodField()

    class Meta:
        model = Kysely
        fields = ["kyselyid",
                  "voimassa_alkupvm",
                  "voimassa_loppupvm",
                  "nimi_fi",
                  "nimi_sv",
                  "nimi_en",
                  "tila",
                  "uudelleenohjaus_url",
                  "sivutettu",
                  "tyyppi",
                  "metatiedot",
                  "kysymysryhmat"]

    def get_kysymysryhmat(self, instance):
        kysymysryhmat = instance.kysely.order_by("jarjestys")
        return KyselyKysymysryhmaSerializer(kysymysryhmat, many=True, read_only=True).data


class KyselykertaSerializer(serializers.ModelSerializer):
    tempvastaus_allowed = SerializerMethodField(read_only=True)
    kysely = KyselySingleSerializer(source="kyselyid", read_only=True)

    class Meta:
        model = Kyselykerta
        fields = ["kyselykertaid",
                  "nimi",
                  "voimassa_alkupvm",
                  "voimassa_loppupvm",
                  "tempvastaus_allowed",
                  "kysely"]

    def get_tempvastaus_allowed(self, instance):
        vastaajatunnus = self.context.get("vastaajatunnus")
        if vastaajatunnus.kohteiden_lkm == 1:
            return True
        return False


class VastausPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vastaus
        fields = ["kysymysid",
                  "string",
                  "numerovalinta",
                  "en_osaa_sanoa"]

    def validate(self, data):
        validate_only_one_answer_type(data)

        # get Kysymys
        kysymys = Kysymys.objects.filter(pk=data["kysymysid"])
        if len(kysymys):
            kysymys = kysymys[0]
        else:
            raise ValidationErrorRest([ErrorMessages.AN006.value])  # HTTP_400_BAD_REQUEST

        # check if eos chosen when not allowed
        validate_eos_when_not_allowed(data, kysymys)

        vastaustyyppi = kysymys.vastaustyyppi

        # this is for dev purposes
        if vastaustyyppi not in ALL_ANSWER_TYPES:
            raise ValidationErrorRest([ErrorMessages.AN009.value])  # HTTP_400_BAD_REQUEST

        # if eos chosen then no need to validate other answer types
        if "en_osaa_sanoa" in data and data["en_osaa_sanoa"]:
            pass
        elif vastaustyyppi in NUMEROVALINTA_ANSWER_TYPES:
            validate_numerovalinta_answer_types(data, kysymys)
        elif vastaustyyppi in VAPAATEKSTI_ANSWER_TYPES:
            # sanitize string input
            if "string" in data:
                data["string"] = sanitize_string(data["string"])

            validate_string_answer_types(data, kysymys)

        return data


class VastaajaPostSerializer(serializers.ModelSerializer):
    vastaajatunnus = serializers.CharField(required=True, write_only=True)
    email = serializers.EmailField(required=True, allow_blank=True, write_only=True)
    vastaukset = VastausPostSerializer(required=True, many=True)

    class Meta:
        model = Vastaaja
        fields = ["vastaajatunnus", "email", "vastaukset"]

    def validate(self, data):
        # check the tunnus is valid
        vastaajatunnus = validate_vastaajatunnus_tunnus(data["vastaajatunnus"])
        self.vastaajatunnus = vastaajatunnus

        # kysymykset list, kysymykset id-list
        kysymykset = []
        kysymykset_id = []
        for kysymysryhma in KyselyKysymysryhma.objects.filter(kyselyid=vastaajatunnus.kyselykertaid.kyselyid):
            kysymys_objects = Kysymys.objects.filter(kysymysryhmaid=kysymysryhma.kysymysryhmaid).exclude(
                vastaustyyppi="matrix_root")
            kysymykset += [kysymys for kysymys in kysymys_objects]
            kysymykset_id += [str(kysymys.kysymysid) for kysymys in kysymys_objects]

        # check there is only answers related to this kysely
        vastaukset = []
        for vastaus in data["vastaukset"]:
            vastaukset.append(vastaus["kysymysid"])
            if str(vastaus["kysymysid"]) not in kysymykset_id:
                raise ValidationErrorRest([ErrorMessages.AN006.value])  # HTTP_400_BAD_REQUEST

        # check there is an answer for every mandatory question
        validate_answers_for_mandatory_questions(data, kysymykset)

        # check there is allowed answer count for every question
        validate_answer_counts(data, kysymykset)

        # add missing answers empty
        for kysymys in kysymykset:
            if kysymys.kysymysid not in vastaukset:
                data["vastaukset"].append(OrderedDict([("kysymysid", kysymys.kysymysid)]))

        return data

    def create(self, validated_data):
        vastaukset_validated = validated_data["vastaukset"]

        vastaaja_data = {
            "kyselykertaid": self.vastaajatunnus.kyselykertaid.kyselykertaid,
            "kyselyid": self.vastaajatunnus.kyselykertaid.kyselyid.kyselyid,
            "vastaajatunnus": self.vastaajatunnus.tunnus,
            "tehtavanimikkeet": {},
            "tutkinnot": {}}

        # if vastaajatunnus is single-use and related kysely has oppilaitos (vaka-toimipaikka),
        # get tyontekija data from Virkailijapalvelu, and add to vastaaja
        if self.vastaajatunnus.kohteiden_lkm == 1 and self.vastaajatunnus.kyselykertaid.kyselyid.oppilaitos:
            tyontekija_data = get_tyontekija_data(self.vastaajatunnus.tunnus)
            if tyontekija_data is not None:
                vastaaja_data.update({k: tyontekija_data[k] for k in ("tehtavanimikkeet", "tutkinnot")})

        vastaaja = Vastaaja.objects.create(**vastaaja_data)

        for v in vastaukset_validated:
            v["vastaajaid"] = vastaaja

        vastaukset_serializer = self.fields["vastaukset"]
        vastaukset_serializer.create(vastaukset_validated)

        # check if answer count is exceeded, and lock if needed
        tunnus = self.vastaajatunnus.tunnus
        vastaajat = Vastaaja.objects.filter(vastaajatunnus=tunnus)
        if vastaajat.count() >= self.vastaajatunnus.kohteiden_lkm:
            Vastaajatunnus.objects.filter(pk=self.vastaajatunnus.pk).update(lukittu=True)

        # remove TempVastauses if those are saved previously
        TempVastaus.objects.filter(vastaajatunnus=validated_data["vastaajatunnus"]).delete()

        return vastaaja


class TempVastausSerializer(serializers.ModelSerializer):
    class Meta:
        model = TempVastaus
        fields = ["kysymysid", "string", "numerovalinta", "en_osaa_sanoa"]


class TempVastausPostSerializer(serializers.Serializer):
    vastaajatunnus = serializers.CharField(required=True)
    vastaukset = TempVastausSerializer(required=True, many=True)

    def validate(self, data):
        # check the tunnus is valid
        vastaajatunnus = validate_vastaajatunnus_tunnus(data["vastaajatunnus"])
        validate_vastaajatunnus_kohteiden_lkm(vastaajatunnus)
        self.vastaajatunnus = vastaajatunnus

        return super().validate(data)

    def create(self, validated_data):
        vastaukset_validated = validated_data["vastaukset"]
        kysely = self.vastaajatunnus.kyselykertaid.kyselyid

        # add vastaajatunnus and kysely_voimassa_loppupvm to vastaukset
        for v in vastaukset_validated:
            v["vastaajatunnus"] = validated_data["vastaajatunnus"]
            v["kysely_voimassa_loppupvm"] = kysely.voimassa_loppupvm

        vastaukset_serializer = TempVastausSerializer(data=vastaukset_validated, many=True)
        vastaukset_serializer.is_valid(raise_exception=True)

        # remove previous TempVastauses
        TempVastaus.objects.filter(vastaajatunnus=validated_data["vastaajatunnus"]).delete()

        vastaukset_serializer.create(vastaukset_validated)

        return vastaukset_validated
