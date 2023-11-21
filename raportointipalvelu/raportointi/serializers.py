import logging
from datetime import datetime

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.fields import SerializerMethodField
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from raportointi.constants import (
    MATRIX_ROOT_TYPE, REPORT_MIN_ANSWERS, VALSSI_PAAKAYTTAJA_LEVEL, DATE_INPUT_FORMAT, SUMMARY_FIELDS,
    VALSSI_YLLAPITAJA_LEVEL)
from raportointi.enums.error_messages import ErrorMessages
from raportointi.models import (
    Kysely, Kyselykerta, Kysymysryhma, ReportingTemplate, ReportingTemplateHelptext, Kysymys, Scale, Summary, Result,
    Organisaatio)
from raportointi.utils import is_expired, sanitize_string
from raportointi.utils_datacollection import (
    get_latest_answer_date, calculate_pct, get_toimipaikka_vastaaja_sent_count,
    get_toimipaikka_vastaaja_answered_count, get_toimipaikka_vastaaja_answer_pct, get_toimipaikka_extra_data,
    get_organisaatio_in_use_counts, get_organisaatio_sent_counts, get_earliest_starting_date, get_latest_ending_date,
    get_koulutustoimija_names)
from raportointi.utils_report import (
    get_matrix_question_answers, survey_participant_count, get_available_codes, get_job_title_names_from_codes,
    create_available_kyselykertas, survey_sent_count)
from raportointi.utils_summary import get_indicators_by_kysely


logger = logging.getLogger(__name__)


class AccessTokenObtainSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data["access"] = str(refresh.access_token)

        return data


class DataCollectionToteuttajaSerializer(serializers.Serializer):
    """Data collection serializer for "toteuttaja"."""

    def to_representation(self, instance):
        kysely_dict = instance

        kysymysryhma_dicts = self.context.get("kysymysryhma_dicts")
        kysymysryhma = kysymysryhma_dicts[instance["kysymysryhmaid"]]

        kyselykerta_dicts = self.context.get("kyselykerta_dicts")
        kyselykertas = [kyselykerta_dict for kyselykerta_dict in kyselykerta_dicts
                        if kyselykerta_dict["kyselyid"] == instance["kyselyid"]]
        kyselykertaid = kyselykertas[0]["kyselykertaid"] if kyselykertas else None

        vastaajatunnus_dicts = self.context.get("vastaajatunnus_dicts")
        vastaajatunnuses = [vastaajatunnus_dict for vastaajatunnus_dict in vastaajatunnus_dicts
                            if vastaajatunnus_dict["kyselykertaid"] == kyselykertaid]

        vastaaja_dicts = self.context.get("vastaaja_dicts")
        vastaajas = [vastaaja_dict for vastaaja_dict in vastaaja_dicts
                     if vastaaja_dict["kyselykertaid"] == kyselykertaid]

        answered_count = len(vastaajas)
        sent_count = len(vastaajatunnuses)

        return {
            "kyselyid": kysely_dict["kyselyid"],
            "voimassa_alkupvm": kysely_dict["voimassa_alkupvm"],
            "voimassa_loppupvm": kysely_dict["voimassa_loppupvm"],
            "latest_answer_date": get_latest_answer_date(vastaajas),
            "nimi_fi": kysely_dict["nimi_fi"],
            "nimi_sv": kysely_dict["nimi_sv"],
            "indicators": {
                "main_indicator": kysymysryhma["main_indicator"],
                "secondary_indicators": kysymysryhma["secondary_indicators"],
            },
            "is_closed": is_expired(kysely_dict["voimassa_loppupvm"]),
            "statistics": {
                "answer_pct": calculate_pct(answered_count, sent_count),
                "answered_count": answered_count,
                "sent_count": sent_count}
        }


class DataCollectionPaakayttajaSerializer(serializers.Serializer):
    """Data collection serializer for "paakayttaja"."""

    def to_representation(self, instance):
        kysely_dicts = instance
        kysymysryhma_dicts = self.context.get("kysymysryhma_dicts")
        kyselykerta_dicts = self.context.get("kyselykerta_dicts")
        vastaajatunnus_dicts = self.context.get("vastaajatunnus_dicts")
        vastaaja_dicts = self.context.get("vastaaja_dicts")
        kysymysryhma = kysymysryhma_dicts[kysely_dicts[0]["kysymysryhmaid"]]

        # filter lists with current kysely-list
        kyselyids = [kysely["kyselyid"] for kysely in kysely_dicts]
        kyselykertas = [kyselykerta_dict for kyselykerta_dict in kyselykerta_dicts
                        if kyselykerta_dict["kyselyid"] in kyselyids]
        kyselykertaids = [kyselykerta["kyselykertaid"] for kyselykerta in kyselykertas]
        vastaajatunnuses = [vastaajatunnus_dict for vastaajatunnus_dict in vastaajatunnus_dicts
                            if vastaajatunnus_dict["kyselykertaid"] in kyselykertaids]
        vastaajas = [vastaaja_dict for vastaaja_dict in vastaaja_dicts
                     if vastaaja_dict["kyselykertaid"] in kyselykertaids]

        if not kysely_dicts[0]["oppilaitos"]:
            # Kyselys in Kysymysryhma has no toimipaikkas
            _, vastaaja_sent_count = get_toimipaikka_vastaaja_sent_count(vastaajatunnuses)
            _, vastaaja_answered_count = get_toimipaikka_vastaaja_answered_count(
                kyselykertas, vastaajatunnuses, vastaajas)
            _, vastaaja_answer_pct = get_toimipaikka_vastaaja_answer_pct(
                kyselykertas, vastaajatunnuses, vastaajas)
            toimipaikka_in_use_count = None
            toimipaikka_sent_count = None
            toimipaikka_answered_count = None
            toimipaikka_answer_pct = None
            toimipaikka_extra_data = {}
        else:
            toimipaikka_sent_count, vastaaja_sent_count = get_toimipaikka_vastaaja_sent_count(vastaajatunnuses)
            toimipaikka_answered_count, vastaaja_answered_count = get_toimipaikka_vastaaja_answered_count(
                kyselykertas, vastaajatunnuses, vastaajas)
            toimipaikka_answer_pct, vastaaja_answer_pct = get_toimipaikka_vastaaja_answer_pct(
                kyselykertas, vastaajatunnuses, vastaajas)
            toimipaikka_answer_pct_lt_50, toimipaikka_kysely_not_sent = get_toimipaikka_extra_data(
                kyselykertas, vastaajatunnuses, vastaajas)
            toimipaikka_in_use_count = len(kysely_dicts)
            toimipaikka_extra_data = {
                "kysely_not_sent": toimipaikka_kysely_not_sent,
                "answer_pct_lt_50": toimipaikka_answer_pct_lt_50,
            }

        return {
            "kysymysryhmaid": kysymysryhma["kysymysryhmaid"],
            "nimi_fi": kysymysryhma["nimi_fi"],
            "nimi_sv": kysymysryhma["nimi_sv"],
            "lomaketyyppi": kysymysryhma["lomaketyyppi"],
            "indicators": {
                "main_indicator": kysymysryhma["main_indicator"],
                "secondary_indicators": kysymysryhma["secondary_indicators"],
            },
            "voimassa_alkupvm": kysely_dicts[0]["voimassa_alkupvm"],
            "voimassa_loppupvm": kysely_dicts[0]["voimassa_loppupvm"],
            "is_closed": is_expired(kysely_dicts[0]["voimassa_loppupvm"]),
            "latest_answer_date": get_latest_answer_date(vastaajas),
            "toimipaikka_statistics": {
                "in_use_count": toimipaikka_in_use_count,
                "sent_count": toimipaikka_sent_count,
                "answered_count": toimipaikka_answered_count,
                "answer_pct": toimipaikka_answer_pct,
                "extra_data": toimipaikka_extra_data,
            },
            "vastaaja_statistics": {
                "sent_count": vastaaja_sent_count,
                "answered_count": vastaaja_answered_count,
                "answer_pct": vastaaja_answer_pct,
            }
        }


class DataCollectionYllapitajaSerializer(serializers.Serializer):
    def to_representation(self, instance):
        kysely_dicts = instance
        kysymysryhma_dicts = self.context.get("kysymysryhma_dicts")
        kyselykerta_dicts = self.context.get("kyselykerta_dicts")
        vastaajatunnus_dicts = self.context.get("vastaajatunnus_dicts")
        vastaaja_dicts = self.context.get("vastaaja_dicts")
        kysymysryhma = kysymysryhma_dicts[kysely_dicts[0]["kysymysryhmaid"]]

        # filter lists with current kysely-list
        kyselyids = [kysely["kyselyid"] for kysely in kysely_dicts]
        kyselykertas = [kyselykerta_dict for kyselykerta_dict in kyselykerta_dicts
                        if kyselykerta_dict["kyselyid"] in kyselyids]
        kyselykertaids = [kyselykerta["kyselykertaid"] for kyselykerta in kyselykertas]
        vastaajatunnuses = [vastaajatunnus_dict for vastaajatunnus_dict in vastaajatunnus_dicts
                            if vastaajatunnus_dict["kyselykertaid"] in kyselykertaids]
        vastaajas = [vastaaja_dict for vastaaja_dict in vastaaja_dicts
                     if vastaaja_dict["kyselykertaid"] in kyselykertaids]

        koulutustoimija_in_use_count, oppilaitos_in_use_count = get_organisaatio_in_use_counts(kysely_dicts)
        koulutustoimija_sent_count, oppilaitos_sent_count = get_organisaatio_sent_counts(vastaajatunnuses, kyselykertas)

        # TODO: use released date field (VAL-936)
        released_date = datetime.strftime(kysymysryhma["muutettuaika"], DATE_INPUT_FORMAT)

        return {
            "kysymysryhmaid": kysymysryhma["kysymysryhmaid"],
            "nimi_fi": kysymysryhma["nimi_fi"],
            "nimi_sv": kysymysryhma["nimi_sv"],
            "lomaketyyppi": kysymysryhma["lomaketyyppi"],
            "released_date": released_date,
            "earliest_usage_date": get_earliest_starting_date(kysely_dicts),
            "latest_ending_date": get_latest_ending_date(kysely_dicts),
            "indicators": {
                "main_indicator": kysymysryhma["main_indicator"],
                "secondary_indicators": kysymysryhma["secondary_indicators"],
            },
            "koulutustoimija_statistics": {
                "in_use_count": koulutustoimija_in_use_count,
                "sent_count": koulutustoimija_sent_count,
                "extra_data": get_koulutustoimija_names(kysely_dicts),
            },
            "oppilaitos_statistics": {
                "in_use_count": oppilaitos_in_use_count,
                "sent_count": oppilaitos_sent_count,
            },
            "vastaaja_statistics": {
                "sent_count": len(vastaajatunnuses),
                "answered_count": len(vastaajas),
                "answer_pct": calculate_pct(len(vastaajas), len(vastaajatunnuses)),
            }
        }


class ReportingTemplateHelptextSerializer(serializers.ModelSerializer):
    """Serializer for the reporting template"""
    id = serializers.IntegerField(required=False)

    class Meta:
        model = ReportingTemplateHelptext
        fields = ["id",
                  "question_id",
                  "title_fi",
                  "title_sv",
                  "description_fi",
                  "description_sv"]


class ReportingTemplateSerializer(serializers.ModelSerializer):
    """Serializer for the reporting template"""
    template_helptexts = ReportingTemplateHelptextSerializer(many=True)

    class Meta:
        model = ReportingTemplate
        fields = ["id",
                  "kysymysryhmaid",
                  "title_fi",
                  "title_sv",
                  "description_fi",
                  "description_sv",
                  "template_helptexts"]

    def validate(self, attrs):
        kysymysryhmaid = attrs.get("kysymysryhmaid")

        # Check if kysymysryhma exists
        if kysymysryhmaid:
            kysymysryhma = Kysymysryhma.objects.filter(kysymysryhmaid=kysymysryhmaid)
            if not kysymysryhma.exists():
                raise ValidationError([ErrorMessages.ER005.value])  # HTTP_400_BAD_REQUEST

        # sanitize input data
        for field in ("title_fi", "title_sv", "description_fi", "description_sv"):
            if field in attrs:
                attrs[field] = sanitize_string(attrs[field])

        return attrs

    def create(self, validated_data):
        template_helptexts_data = validated_data.pop("template_helptexts")

        # Create ReportingTemplate
        reporting_template = ReportingTemplate.objects.create(**validated_data)

        # Create ReportingTemplateHelptext(s)
        for template_helptext in template_helptexts_data:
            ReportingTemplateHelptext.objects.create(reporting_template=reporting_template, **template_helptext)
        return reporting_template

    def update(self, instance, validated_data):
        template_helptexts_data = validated_data.pop("template_helptexts")

        # sanitize input data
        title_fi_sanitized = sanitize_string(validated_data.get("title_fi", instance.title_fi))
        title_sv_sanitized = sanitize_string(validated_data.get("title_sv", instance.title_sv))
        description_fi_sanitized = sanitize_string(validated_data.get("description_fi", instance.description_fi))
        description_sv_sanitized = sanitize_string(validated_data.get("description_sv", instance.description_sv))

        # Update ReportingTemplate
        instance.title_fi = title_fi_sanitized
        instance.title_sv = title_sv_sanitized
        instance.description_fi = description_fi_sanitized
        instance.description_sv = description_sv_sanitized

        # Update ReportingTemplateHelptext(s)
        for template_helptext in template_helptexts_data:
            try:
                reporting_template_helptext = ReportingTemplateHelptext.objects.get(pk=template_helptext.get("id"))
            except ReportingTemplateHelptext.DoesNotExist:
                reporting_template = ReportingTemplate.objects.get(kysymysryhmaid=validated_data.get("kysymysryhmaid"))
                reporting_template_helptext = ReportingTemplateHelptext.objects.create(
                    reporting_template=reporting_template, **template_helptext)

            # sanitize input data
            title_fi_sanitized = sanitize_string(
                template_helptext.get("title_fi", reporting_template_helptext.title_fi))
            title_sv_sanitized = sanitize_string(
                template_helptext.get("title_sv", reporting_template_helptext.title_sv))
            description_fi_sanitized = sanitize_string(
                template_helptext.get("description_fi", reporting_template_helptext.description_fi))
            description_sv_sanitized = sanitize_string(
                template_helptext.get("description_sv", reporting_template_helptext.description_sv))

            reporting_template_helptext.title_fi = title_fi_sanitized
            reporting_template_helptext.title_sv = title_sv_sanitized
            reporting_template_helptext.description_fi = description_fi_sanitized
            reporting_template_helptext.description_sv = description_sv_sanitized
            reporting_template_helptext.save()

        instance.save()

        return instance


class MatriisiKysymysSerializer(serializers.ModelSerializer):
    """Serializer for matrix questions"""

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
    """Kysymys Serializer"""
    matriisikysymykset = SerializerMethodField()
    question_answers = SerializerMethodField()
    matrix_question_scale = SerializerMethodField()

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
                  "matriisikysymykset",
                  "question_answers",
                  "matrix_question_scale"]

    def get_matriisikysymykset(self, instance):
        if instance.vastaustyyppi != MATRIX_ROOT_TYPE:
            return []
        matriisikysymykset = (
            Kysymys.objects.filter(matriisi_kysymysid=instance.kysymysid)
            .filter(matriisi_jarjestys__gt=0).order_by("matriisi_jarjestys"))
        return MatriisiKysymysSerializer(matriisikysymykset, many=True, read_only=True).data

    def get_matrix_question_scale(self, instance):
        if instance.vastaustyyppi != MATRIX_ROOT_TYPE:
            return None
        matrix_questions = (
            Kysymys.objects.filter(matriisi_kysymysid=instance.kysymysid)
            .filter(matriisi_jarjestys__gt=0).order_by("matriisi_jarjestys"))

        scale = Scale.objects.get(name=matrix_questions.first().vastaustyyppi)

        return scale.scale

    def get_question_answers(self, instance):
        if self.context.get("permission_level") == VALSSI_YLLAPITAJA_LEVEL:
            return None

        koulutustoimija = self.context.get("koulutustoimija")
        if not koulutustoimija:
            return []

        question_answers = None

        # Matrix question answers
        if instance.vastaustyyppi == MATRIX_ROOT_TYPE:
            question_answers = get_matrix_question_answers(instance, koulutustoimija, self.context.get("filters"))
        return question_answers


class ReportingBaseSerializer(serializers.ModelSerializer):
    """Serializer for the reporting base.
    Use fields from Kysymysryhma + Reportingtemplate
    """
    reporting_template = SerializerMethodField()
    questions = SerializerMethodField()

    class Meta:
        model = Kysymysryhma
        fields = ["kysymysryhmaid",
                  "nimi_fi",
                  "nimi_sv",
                  "reporting_template",
                  "questions"]

    def get_reporting_template(self, instance):
        try:
            reporting_template = ReportingTemplate.objects.get(kysymysryhmaid=instance.kysymysryhmaid)
        except ReportingTemplate.DoesNotExist:
            reporting_template = None
        serializer = ReportingTemplateSerializer(reporting_template)

        return serializer.data

    def get_questions(self, instance):
        # filter out matrixes other than matrix-root
        questions = (
            instance.kysymykset.filter(matriisi_jarjestys=0) | instance.kysymykset.filter(matriisi_jarjestys=None)
        ).order_by("jarjestys")

        return KysymysSerializer(questions, many=True, read_only=True,
                                 context=self.context).data


class ClosedSurveysSerializer(serializers.ModelSerializer):
    """Closed surveys serializer"""
    display_report = SerializerMethodField()
    kyselykertas = SerializerMethodField()
    available_kyselykertas = SerializerMethodField()
    koulutustoimija_oid = SerializerMethodField()

    class Meta:
        model = Kysymysryhma
        fields = ["kysymysryhmaid",
                  "nimi_fi",
                  "nimi_sv",
                  "display_report",
                  "kyselykertas",
                  "available_kyselykertas",
                  "koulutustoimija_oid"]

    def get_display_report(self, instance):
        kyselykertas = self.context.get("kyselykertas")
        vastaajas = self.context.get("vastaajas")
        koulutustoimija = self.context.get("koulutustoimija")
        filters = self.context.get("filters")

        kyselykertas_filtered = [
            kyselykerta for kyselykerta in kyselykertas
            if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
            kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == instance.kysymysryhmaid]

        if filters and filters.get("kyselykerta_alkupvm"):
            kyselykertas_filtered = [kyselykerta for kyselykerta in kyselykertas_filtered
                                     if kyselykerta.voimassa_alkupvm == filters["kyselykerta_alkupvm"]]

        kyselykertaids = [kyselykerta.pk for kyselykerta in kyselykertas_filtered]

        vastaajas_count = len([1 for vastaaja in vastaajas if vastaaja.kyselykertaid in kyselykertaids]) \
            if vastaajas else 0

        return vastaajas_count >= REPORT_MIN_ANSWERS

    def get_kyselykertas(self, instance):
        kyselykertas = self.context.get("kyselykertas")
        oppilaitos_oids = self.context.get("oppilaitos_oids")

        kyselykertas_filtered = [
            kyselykerta for kyselykerta in kyselykertas
            if kyselykerta.kyselyid.oppilaitos is not None and
            kyselykerta.kyselyid.oppilaitos.oid in oppilaitos_oids and
            kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == instance.kysymysryhmaid]

        return KyselykertaSerializer(kyselykertas_filtered, many=True, context={
            "koulutustoimija": self.context.get("koulutustoimija"),
            "kyselykertas": kyselykertas,
            "summarys": self.context.get("summarys"),
            "vastaajas": self.context.get("vastaajas")}).data

    def get_available_kyselykertas(self, instance):
        kyselykertas = self.context.get("kyselykertas")
        vastaajas = self.context.get("vastaajas")
        koulutustoimija = self.context.get("koulutustoimija")

        kyselykertas_start_times = []
        for kyselykerta in kyselykertas:
            kysely_kysymysryhma_id = kyselykerta.kyselyid.kysely.first().kysymysryhmaid.kysymysryhmaid
            if kysely_kysymysryhma_id == instance.pk and \
                    kyselykerta.kyselyid.koulutustoimija == koulutustoimija and \
                    kyselykerta.voimassa_loppupvm < timezone.now().date() and \
                    kyselykerta.voimassa_alkupvm not in kyselykertas_start_times:
                kyselykertas_start_times.append(kyselykerta.voimassa_alkupvm)

        return create_available_kyselykertas(
            instance, kyselykertas_start_times, koulutustoimija, kyselykertas, vastaajas)

    def get_koulutustoimija_oid(self, instance):
        koulutustoimija = self.context.get("koulutustoimija")
        return koulutustoimija.oid if koulutustoimija else None


class ViewReportSerializer(serializers.ModelSerializer):
    """Serializer for view report."""
    survey_participants_count = SerializerMethodField()
    survey_sent_count = SerializerMethodField()
    reporting_base = SerializerMethodField()
    koulutustoimija_nimi_fi = SerializerMethodField()
    koulutustoimija_nimi_sv = SerializerMethodField()
    created_date = SerializerMethodField()
    job_titles_fi = SerializerMethodField()
    job_titles_sv = SerializerMethodField()
    available_kyselykertas = SerializerMethodField()

    class Meta:
        model = Kysymysryhma
        fields = ["kysymysryhmaid",
                  "nimi_fi",
                  "nimi_sv",
                  "reporting_base",
                  "survey_participants_count",
                  "survey_sent_count",
                  "koulutustoimija_nimi_fi",
                  "koulutustoimija_nimi_sv",
                  "created_date",
                  "job_titles_fi",
                  "job_titles_sv",
                  "available_kyselykertas",
                  "metatiedot"]

    def get_reporting_base(self, instance):
        serializer = ReportingBaseSerializer(instance, context=self.context)
        return serializer.data

    def get_survey_participants_count(self, instance):
        kyselykertas = self.context.get("kyselykertas")
        koulutustoimija = self.context.get("koulutustoimija")
        vastaajas = self.context.get("vastaajas")
        filters = self.context.get("filters")
        return survey_participant_count(instance, kyselykertas, koulutustoimija, vastaajas, filters)

    def get_survey_sent_count(self, instance):
        kyselykertas = self.context.get("kyselykertas")
        koulutustoimija = self.context.get("koulutustoimija")
        filters = self.context.get("filters")
        return survey_sent_count(instance, kyselykertas, koulutustoimija, filters)

    def get_koulutustoimija_nimi_fi(self, instance):
        koulutustoimija = self.context.get("koulutustoimija")
        return koulutustoimija.nimi_fi

    def get_koulutustoimija_nimi_sv(self, instance):
        koulutustoimija = self.context.get("koulutustoimija")
        return koulutustoimija.nimi_sv

    def get_created_date(self, instance):
        kyselykertas = self.context.get("kyselykertas")
        koulutustoimija = self.context.get("koulutustoimija")
        filters = self.context.get("filters")
        kyselykertas_filtered = [
            kyselykerta for kyselykerta in kyselykertas
            if kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == instance.kysymysryhmaid and
            kyselykerta.kyselyid.koulutustoimija == koulutustoimija]

        if filters and filters.get("kyselykerta_alkupvm"):
            alkupvm = filters.get("kyselykerta_alkupvm")
            if isinstance(alkupvm, str):
                alkupvm = datetime.strptime(alkupvm, DATE_INPUT_FORMAT).date()
                kyselykertas_filtered = [kyselykerta for kyselykerta in kyselykertas_filtered
                                         if kyselykerta.voimassa_alkupvm == alkupvm]

        if not kyselykertas_filtered:
            return None
        created_date = kyselykertas_filtered[0].voimassa_alkupvm
        return created_date.strftime("%d.%m.%Y")

    def get_job_titles_fi(self, instance, language: str = "fi"):
        kyselykertas = self.context.get("kyselykertas")
        koulutustoimija = self.context.get("koulutustoimija")
        vastaajas = self.context.get("vastaajas")
        filters = self.context.get("filters")
        koodis = self.context.get("koodis")
        if self.context.get("permission_level") in (VALSSI_PAAKAYTTAJA_LEVEL, ):
            respondent_codes = get_available_codes(instance, kyselykertas, koulutustoimija, vastaajas, filters)
            return get_job_title_names_from_codes(koodis, respondent_codes, language)
        return None

    def get_job_titles_sv(self, instance):
        return self.get_job_titles_fi(instance, language="sv")

    def get_available_kyselykertas(self, instance):
        if self.context.get("permission_level") == VALSSI_YLLAPITAJA_LEVEL:
            return None

        kyselykertas = self.context.get("kyselykertas")
        vastaajas = self.context.get("vastaajas")
        koulutustoimija = self.context.get("koulutustoimija")

        kyselykertas_start_times = []
        for kyselykerta in kyselykertas:
            kysely_kysymysryhma_id = kyselykerta.kyselyid.kysely.first().kysymysryhmaid.kysymysryhmaid
            if kysely_kysymysryhma_id == instance.pk and \
                    kyselykerta.kyselyid.koulutustoimija == koulutustoimija and \
                    kyselykerta.voimassa_loppupvm < timezone.now().date() and \
                    kyselykerta.voimassa_alkupvm not in kyselykertas_start_times:
                kyselykertas_start_times.append(kyselykerta.voimassa_alkupvm)

        return create_available_kyselykertas(
            instance, kyselykertas_start_times, koulutustoimija, kyselykertas, vastaajas)


class KyselySingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kysely
        fields = ["kyselyid",
                  "voimassa_alkupvm",
                  "voimassa_loppupvm",
                  "nimi_fi",
                  "nimi_sv",
                  "metatiedot"]


class KyselykertaSerializer(serializers.ModelSerializer):
    kysely = KyselySingleSerializer(source="kyselyid", read_only=True)
    show_summary = SerializerMethodField()
    display_report = SerializerMethodField()

    class Meta:
        model = Kyselykerta
        fields = ["kyselykertaid",
                  "nimi",
                  "voimassa_alkupvm",
                  "voimassa_loppupvm",
                  "kysely",
                  "show_summary",
                  "display_report"]

    def get_show_summary(self, instance):
        kysely = instance.kyselyid
        kysymysryhmaid = kysely.kysymysryhmat.first().kysymysryhmaid

        for summary in self.context.get("summarys"):
            if summary.kysymysryhmaid == kysymysryhmaid \
                    and summary.oppilaitos == kysely.oppilaitos.oid \
                    and summary.kysely_voimassa_alkupvm == kysely.voimassa_alkupvm:
                return True
        return False

    def get_display_report(self, instance):
        koulutustoimija = self.context.get("koulutustoimija")
        kyselykertas = self.context.get("kyselykertas")
        vastaajas = self.context.get("vastaajas")

        kysymysryhmaid = instance.kyselyid.kysymysryhmat.first().kysymysryhmaid
        kyselykertaids = [kyselykerta.pk for kyselykerta in kyselykertas
                          if kyselykerta.kyselyid.koulutustoimija == koulutustoimija and
                          kyselykerta.kyselyid.metatiedot.get("valssi_kysymysryhma") == kysymysryhmaid and
                          kyselykerta.voimassa_alkupvm == instance.voimassa_alkupvm]

        vastaajas_count = len([1 for vastaaja in vastaajas if vastaaja.kyselykertaid in kyselykertaids]) \
            if vastaajas else 0

        return vastaajas_count >= REPORT_MIN_ANSWERS


class SummarySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    kysymysryhmaid = serializers.IntegerField(read_only=True)
    oppilaitos = serializers.CharField(read_only=True)
    kysely_voimassa_alkupvm = serializers.DateField(read_only=True)
    taustatiedot = serializers.JSONField(read_only=True)
    kyselyid = serializers.IntegerField(write_only=True)
    koulutustoimija_name = SerializerMethodField()

    class Meta:
        model = Summary
        fields = [
            "kyselyid",
            "id",
            "kysymysryhmaid",
            "oppilaitos",
            "koulutustoimija_name",
            "kysely_voimassa_alkupvm",
            "group_info",
            "kuvaus",
            "aineisto",
            "vahvuudet",
            "kohteet",
            "keh_toimenpiteet",
            "seur_toimenpiteet",
            "taustatiedot",
            "is_locked"]

    def validate(self, data):
        kysely = Kysely.objects.filter(kyselyid=data["kyselyid"]).first()
        if kysely is None:
            raise NotFound([ErrorMessages.ER024.value])  # HTTP_404_NOT_FOUND

        koulutustoimija_oid = kysely.koulutustoimija.oid
        oppilaitos_oid = kysely.oppilaitos.oid
        kysymysryhma = kysely.kysymysryhmat.first()
        kysely_voimassa_alkupvm = kysely.voimassa_alkupvm
        paaindikaattori_key, sekondaariset_ind_keys = get_indicators_by_kysely(kysely)

        # validate there is no summary already
        if Summary.objects.filter(kysymysryhmaid=kysymysryhma.kysymysryhmaid,
                                  oppilaitos=oppilaitos_oid,
                                  kysely_voimassa_alkupvm=kysely_voimassa_alkupvm).exists():
            raise ValidationError([ErrorMessages.ER012.value])  # HTTP_400_BAD_REQUEST

        # add kysymysryhmaid, oppilaitos, taustatiedot
        data["kysymysryhmaid"] = kysymysryhma.kysymysryhmaid
        data["oppilaitos"] = oppilaitos_oid
        data["koulutustoimija"] = koulutustoimija_oid
        data["kysely_voimassa_alkupvm"] = kysely_voimassa_alkupvm
        data["taustatiedot"] = dict(
            koulutustoimija=koulutustoimija_oid,
            paaindikaattori=paaindikaattori_key,
            sekondaariset_indikaattorit=sekondaariset_ind_keys,
            kysymysryhma_name=dict(fi=kysymysryhma.nimi_fi, sv=kysymysryhma.nimi_sv))

        # sanitize input data
        for field in SUMMARY_FIELDS:
            if field in data:
                data[field] = sanitize_string(data[field])

        return data

    def create(self, validated_data):
        validated_data.pop("kyselyid")
        return super().create(validated_data)

    def get_koulutustoimija_name(self, instance):
        kysely_obj = self.context.get("kysely_obj")
        if kysely_obj:
            return dict(fi=kysely_obj.koulutustoimija.nimi_fi, sv=kysely_obj.koulutustoimija.nimi_sv)
        return dict(fi=None, sv=None)


class SummaryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = [
            "group_info",
            "kuvaus",
            "aineisto",
            "vahvuudet",
            "kohteet",
            "keh_toimenpiteet",
            "seur_toimenpiteet",
            "is_locked"]

    def validate(self, data):
        # sanitize input data
        for field in SUMMARY_FIELDS:
            if field in data:
                data[field] = sanitize_string(data[field])

        return data


class ResultSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    kysymysryhmaid = serializers.IntegerField()
    koulutustoimija = serializers.CharField()
    kysely_voimassa_alkupvm = serializers.DateField(required=True, input_formats=[DATE_INPUT_FORMAT])
    taustatiedot = serializers.JSONField(read_only=True)
    koulutustoimija_name = SerializerMethodField()

    class Meta:
        model = Result
        fields = [
            "id",
            "kysymysryhmaid",
            "koulutustoimija",
            "koulutustoimija_name",
            "kysely_voimassa_alkupvm",
            "kuvaus",
            "aineisto",
            "vahvuudet",
            "kohteet",
            "keh_toimenpiteet",
            "seur_toimenpiteet",
            "taustatiedot",
            "is_locked"]

    def validate(self, data):
        kysely = Kysely.objects.filter(
            koulutustoimija__oid=data["koulutustoimija"],
            voimassa_alkupvm=data["kysely_voimassa_alkupvm"],
            kysymysryhmat__kysymysryhmaid=data["kysymysryhmaid"]) \
            .prefetch_related("kysymysryhmat").first()
        if not kysely:
            raise NotFound([ErrorMessages.ER018.value])  # HTTP_404_NOT_FOUND

        paaindikaattori_key, sekondaariset_ind_keys = get_indicators_by_kysely(kysely)

        # add taustatiedot
        data["taustatiedot"] = dict(
            koulutustoimija=data["koulutustoimija"],
            paaindikaattori=paaindikaattori_key,
            sekondaariset_indikaattorit=sekondaariset_ind_keys,
            kysymysryhma_name=dict(
                fi=kysely.kysymysryhmat.first().nimi_fi,
                sv=kysely.kysymysryhmat.first().nimi_sv))

        # sanitize input data
        for field in SUMMARY_FIELDS:
            if field in data:
                data[field] = sanitize_string(data[field])

        return data

    def get_koulutustoimija_name(self, instance):
        koulutustoimija_obj = Organisaatio.objects.filter(oid=instance.koulutustoimija).first()
        return dict(fi=koulutustoimija_obj.nimi_fi, sv=koulutustoimija_obj.nimi_sv)


class ResultUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = [
            "kuvaus",
            "aineisto",
            "vahvuudet",
            "kohteet",
            "keh_toimenpiteet",
            "seur_toimenpiteet",
            "is_locked"]

    def validate(self, data):
        # sanitize input data
        for field in SUMMARY_FIELDS:
            if field in data:
                data[field] = sanitize_string(data[field])

        return data
