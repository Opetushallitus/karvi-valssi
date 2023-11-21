from django.db import models


class Vastaaja(models.Model):
    vastaajaid = models.AutoField(primary_key=True)
    kyselykertaid = models.IntegerField()
    kyselyid = models.IntegerField()
    vastaajatunnus = models.CharField(max_length=30)
    tehtavanimikkeet = models.JSONField(default=dict)
    tutkinnot = models.JSONField(default=dict)
    luotuaika = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'vastaaja'


class Vastaus(models.Model):
    vastausid = models.AutoField(primary_key=True)
    kysymysid = models.IntegerField()
    vastaajaid = models.ForeignKey(Vastaaja, models.DO_NOTHING, db_column='vastaajaid')
    string = models.TextField(blank=True, null=True)
    numerovalinta = models.DecimalField(max_digits=5, decimal_places=0, blank=True, null=True)
    vaihtoehto = models.CharField(max_length=10, blank=True, null=True)
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    en_osaa_sanoa = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'vastaus'


class VastausSend(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=80)
    vastaajaid = models.ForeignKey(Vastaaja, models.DO_NOTHING, db_column='vastaajaid')
    language = models.CharField(max_length=3)

    class Meta:
        managed = True
        db_table = 'vastaussend'


class TempVastaus(models.Model):
    id = models.AutoField(primary_key=True)
    kysymysid = models.CharField(max_length=30)
    vastaajatunnus = models.CharField(max_length=30)
    kysely_voimassa_loppupvm = models.DateField(blank=True, null=True)
    string = models.TextField(blank=True, null=True)
    numerovalinta = models.DecimalField(max_digits=5, decimal_places=0, blank=True, null=True)
    en_osaa_sanoa = models.BooleanField(blank=True, null=True)
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'tempvastaus'
