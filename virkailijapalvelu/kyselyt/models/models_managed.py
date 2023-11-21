from django.db import models


class UserAuthorization(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=200, unique=True)
    oid = models.CharField(max_length=40, blank=True, null=True)
    permissions = models.JSONField(default=dict)
    updated_time = models.DateTimeField(null=True)

    class Meta:
        managed = True
        db_table = 'userauthorization'


class KyselySend(models.Model):
    id = models.AutoField(primary_key=True)
    tyontekija_id = models.IntegerField(blank=True, null=True)
    kutsumanimi = models.CharField(max_length=50, blank=True, null=True)
    sukunimi = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(max_length=80)
    tehtavanimikkeet = models.JSONField(default=dict)
    kyselykerta = models.IntegerField()
    vastaajatunnus = models.CharField(max_length=20)
    msg_id = models.IntegerField()
    msg_status = models.CharField(max_length=20)
    message = models.CharField(max_length=5000, default="")

    class Meta:
        managed = True
        db_table = 'kyselysend'


class ExternalServices(models.Model):
    oph_tgt = models.CharField(max_length=300, blank=True)
    varda_apikey = models.CharField(max_length=100, blank=True)
    varda_organisaatiot_last_update_time = models.CharField(max_length=50, blank=True)
    varda_toimipaikat_last_update_time = models.CharField(max_length=50, blank=True)

    class Meta:
        managed = True
        db_table = 'externalservices'


class Indikaattori(models.Model):
    id = models.AutoField(primary_key=True)
    group_id = models.IntegerField()
    key = models.CharField(max_length=100, unique=True)
    laatutekija = models.CharField(max_length=100)
    is_visible = models.BooleanField()

    class Meta:
        managed = True
        db_table = 'indikaattori'


class Scale(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    label_fi = models.CharField(max_length=50, blank=True, null=True)
    label_sv = models.CharField(max_length=50, blank=True, null=True)
    min_value = models.IntegerField()
    max_value = models.IntegerField()
    default_value = models.IntegerField()
    step_count = models.IntegerField()
    order_no = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    eos_allowed = models.BooleanField(default=True)
    eos_value = models.JSONField(null=True)
    scale = models.JSONField()

    class Meta:
        managed = True
        db_table = 'scale'


class MalfunctionMessage(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.IntegerField(unique=True)
    message = models.CharField(max_length=500)
    is_active = models.BooleanField(default=False)
    service = models.CharField(max_length=50, default="virkailijapalvelu")

    class Meta:
        managed = True
        db_table = 'malfunctionmessage'
