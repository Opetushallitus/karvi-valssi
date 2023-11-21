from django.db import models


class ExternalServices(models.Model):
    oph_tgt = models.CharField(max_length=300, blank=True)

    class Meta:
        managed = True
        db_table = "externalservices"


class ReportingTemplate(models.Model):
    kysymysryhmaid = models.IntegerField(unique=True)
    title_fi = models.CharField(max_length=200, blank=True, null=True)
    title_sv = models.CharField(max_length=200, blank=True, null=True)
    description_fi = models.TextField(blank=True, null=True)
    description_sv = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "reportingtemplate"


class ReportingTemplateHelptext(models.Model):
    reporting_template = models.ForeignKey(
        ReportingTemplate, models.DO_NOTHING, db_column='reportingtemplate', related_name="template_helptexts")
    question_id = models.IntegerField()
    title_fi = models.CharField(max_length=200, blank=True, null=True)
    title_sv = models.CharField(max_length=200, blank=True, null=True)
    description_fi = models.TextField(blank=True, null=True)
    description_sv = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "ReportingTemplateHelptext"


class Summary(models.Model):
    id = models.AutoField(primary_key=True)
    kysymysryhmaid = models.IntegerField()
    oppilaitos = models.CharField(max_length=40)
    koulutustoimija = models.CharField(max_length=40)
    kysely_voimassa_alkupvm = models.DateField()
    kuvaus = models.CharField(max_length=20000, blank=True, null=True)
    aineisto = models.CharField(max_length=20000, blank=True, null=True)
    vahvuudet = models.CharField(max_length=20000, blank=True, null=True)
    kohteet = models.CharField(max_length=20000, blank=True, null=True)
    keh_toimenpiteet = models.CharField(max_length=20000, blank=True, null=True)
    seur_toimenpiteet = models.CharField(max_length=20000, blank=True, null=True)
    taustatiedot = models.JSONField(default=dict)
    is_locked = models.BooleanField(default=True)
    group_info = models.CharField(max_length=200, default="")

    class Meta:
        managed = True
        db_table = "summary"
        unique_together = (("kysymysryhmaid", "oppilaitos", "kysely_voimassa_alkupvm"), )


class Result(models.Model):
    id = models.AutoField(primary_key=True)
    kysymysryhmaid = models.IntegerField()
    koulutustoimija = models.CharField(max_length=40)
    kysely_voimassa_alkupvm = models.DateField()
    kuvaus = models.CharField(max_length=20000, blank=True, null=True)
    aineisto = models.CharField(max_length=20000, blank=True, null=True)
    vahvuudet = models.CharField(max_length=20000, blank=True, null=True)
    kohteet = models.CharField(max_length=20000, blank=True, null=True)
    keh_toimenpiteet = models.CharField(max_length=20000, blank=True, null=True)
    seur_toimenpiteet = models.CharField(max_length=20000, blank=True, null=True)
    taustatiedot = models.JSONField(default=dict)
    is_locked = models.BooleanField(default=True)

    class Meta:
        managed = True
        db_table = "result"
        unique_together = (("kysymysryhmaid", "koulutustoimija", "kysely_voimassa_alkupvm"), )
