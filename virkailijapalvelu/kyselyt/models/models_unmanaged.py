from django.conf import settings
from django.db import models


managed = settings.TESTING


class Kayttaja(models.Model):
    oid = models.CharField(primary_key=True, max_length=80)
    uid = models.CharField(unique=True, max_length=80)
    etunimi = models.CharField(max_length=100, blank=True, null=True)
    sukunimi = models.CharField(max_length=100, blank=True, null=True)
    voimassa = models.BooleanField()
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)

    class Meta:
        managed = managed
        db_table = 'kayttaja'


class Koodi(models.Model):
    koodisto_uri = models.CharField(max_length=256)
    nimi_fi = models.CharField(max_length=256, blank=True, null=True)
    nimi_sv = models.CharField(max_length=256, blank=True, null=True)
    nimi_en = models.CharField(max_length=256, blank=True, null=True)
    koodi_arvo = models.CharField(max_length=256)
    voimassa_alkupvm = models.DateField(blank=True, null=True)
    voimassa_loppupvm = models.DateField(blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'koodi'


class Kysely(models.Model):
    kyselyid = models.AutoField(primary_key=True)
    voimassa_alkupvm = models.DateField(blank=True, null=True)
    voimassa_loppupvm = models.DateField(blank=True, null=True)
    nimi_fi = models.CharField(max_length=200, blank=True, null=True)
    nimi_sv = models.CharField(max_length=200, blank=True, null=True)
    selite_fi = models.TextField(blank=True, null=True)
    selite_sv = models.TextField(blank=True, null=True)
    koulutustoimija = models.ForeignKey(
        'Organisaatio', models.DO_NOTHING, db_column='koulutustoimija', related_name='kysely_koulutustoimija', blank=True, null=True)
    oppilaitos = models.ForeignKey(
        'Organisaatio', models.DO_NOTHING, db_column='oppilaitos', related_name='kysely_oppilaitos', blank=True, null=True)
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja', related_name='kysely_muutettu_kayttaja')
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    tila = models.ForeignKey('TilaEnum', models.DO_NOTHING, db_column='tila', blank=True, null=True)
    nimi_en = models.CharField(max_length=200, blank=True, null=True)
    selite_en = models.TextField(blank=True, null=True)
    uudelleenohjaus_url = models.CharField(max_length=2000, blank=True, null=True)
    sivutettu = models.BooleanField(blank=True, null=True)
    kyselypohjaid = models.ForeignKey(
        'Kyselypohja', models.DO_NOTHING, db_column='kyselypohjaid', blank=True, null=True)
    tyyppi = models.TextField(blank=True, null=True)
    metatiedot = models.JSONField(blank=True, null=True)
    kysymysryhmat = models.ManyToManyField('Kysymysryhma', through='KyselyKysymysryhma')

    class Meta:
        managed = managed
        db_table = 'kysely'


class KyselyKysymys(models.Model):
    kyselyid = models.ForeignKey(Kysely, models.DO_NOTHING, db_column='kyselyid')
    kysymysid = models.OneToOneField('Kysymys', models.DO_NOTHING, db_column='kysymysid', primary_key=True)
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja', related_name='kyselykysymys_muutettu_kayttaja')
    luotuaika = models.DateTimeField()
    muutettuaika = models.DateTimeField()

    class Meta:
        managed = managed
        db_table = 'kysely_kysymys'
        unique_together = (('kysymysid', 'kyselyid'),)


class KyselyKysymysryhma(models.Model):
    kyselyid = models.ForeignKey(Kysely, models.DO_NOTHING, db_column='kyselyid', related_name='kysely')
    kysymysryhmaid = models.ForeignKey('Kysymysryhma', models.DO_NOTHING, db_column='kysymysryhmaid', primary_key=True)
    jarjestys = models.IntegerField(blank=True, null=True)
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja', related_name='kyselykysymysryhma_muutettu_kayttaja')
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)

    class Meta:
        managed = managed
        db_table = 'kysely_kysymysryhma'
        unique_together = (('kyselyid', 'jarjestys'), ('kyselyid', 'kysymysryhmaid'),)
        ordering = ['jarjestys']


class Kyselykerta(models.Model):
    kyselykertaid = models.AutoField(primary_key=True)
    kyselyid = models.ForeignKey(Kysely, models.DO_NOTHING, db_column='kyselyid')
    nimi = models.CharField(max_length=200)
    voimassa_alkupvm = models.DateField()
    voimassa_loppupvm = models.DateField(blank=True, null=True)
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja', related_name='kyselykerta_muutettu_kayttaja')
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    lukittu = models.BooleanField(blank=True, null=True)
    metatiedot = models.JSONField(blank=True, null=True)
    automaattinen = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = managed
        db_table = 'kyselykerta'


class Kyselypohja(models.Model):
    kyselypohjaid = models.AutoField(primary_key=True)
    valtakunnallinen = models.BooleanField()
    voimassa_alkupvm = models.DateField(blank=True, null=True)
    voimassa_loppupvm = models.DateField(blank=True, null=True)
    nimi_fi = models.CharField(max_length=200, blank=True, null=True)
    nimi_sv = models.CharField(max_length=200, blank=True, null=True)
    selite_fi = models.TextField(blank=True, null=True)
    selite_sv = models.TextField(blank=True, null=True)
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja', related_name='kyselypohja_muutettu_kayttaja')
    luotuaika = models.DateTimeField()
    muutettuaika = models.DateTimeField()
    tila = models.ForeignKey('TilaEnum', models.DO_NOTHING, db_column='tila', blank=True, null=True)
    nimi_en = models.CharField(max_length=200, blank=True, null=True)
    selite_en = models.TextField(blank=True, null=True)
    metatiedot = models.JSONField(blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'kyselypohja'


class Kysymys(models.Model):
    kysymysid = models.AutoField(primary_key=True)
    pakollinen = models.BooleanField()
    poistettava = models.BooleanField()
    vastaustyyppi = models.CharField(max_length=20)
    kysymysryhmaid = models.ForeignKey(
        'Kysymysryhma', models.DO_NOTHING, db_column='kysymysryhmaid', related_name='kysymykset')
    kysymys_fi = models.CharField(max_length=500, blank=True, null=True)
    kysymys_sv = models.CharField(max_length=500, blank=True, null=True)
    jarjestys = models.IntegerField(blank=True, null=True)
    monivalinta_max = models.IntegerField(blank=True, null=True)
    max_vastaus = models.IntegerField(blank=True, null=True)
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja', related_name='kysymys_muutettu_kayttaja')
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    eos_vastaus_sallittu = models.BooleanField(blank=True, null=True)
    kysymys_en = models.CharField(max_length=500, blank=True, null=True)
    jatkokysymys = models.BooleanField()
    rajoite = models.TextField(blank=True, null=True)
    selite_fi = models.TextField(blank=True, null=True)
    selite_sv = models.TextField(blank=True, null=True)
    selite_en = models.TextField(blank=True, null=True)
    raportoitava = models.BooleanField(blank=True, null=True)
    metatiedot = models.JSONField(blank=True, null=True)
    matriisi_kysymysid = models.IntegerField(blank=True, null=True)
    matriisi_jarjestys = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'kysymys'
        unique_together = (('kysymysryhmaid', 'jarjestys', 'matriisi_jarjestys'),)


class KysymysJatkokysymys(models.Model):
    kysymysid = models.ForeignKey(Kysymys, models.DO_NOTHING, db_column='kysymysid')
    jatkokysymysid = models.ForeignKey(
        Kysymys, models.DO_NOTHING, db_column='jatkokysymysid', related_name='kysymysjatkokysymys_jatkokysymysid')
    vastaus = models.CharField(max_length=20)
    nakyvissa = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'kysymys_jatkokysymys'


class Kysymysryhma(models.Model):
    kysymysryhmaid = models.AutoField(primary_key=True)
    taustakysymykset = models.BooleanField()
    valtakunnallinen = models.BooleanField()
    nimi_fi = models.CharField(max_length=200, blank=True, null=True)
    nimi_sv = models.CharField(max_length=200, blank=True, null=True)
    selite_fi = models.TextField(blank=True, null=True)
    selite_sv = models.TextField(blank=True, null=True)
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja', related_name='kysymysryhma_muutettu_kayttaja')
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    tila = models.ForeignKey('TilaEnum', models.DO_NOTHING, db_column='tila', blank=True, null=True)
    kuvaus_fi = models.CharField(max_length=800, blank=True, null=True)
    kuvaus_sv = models.CharField(max_length=800, blank=True, null=True)
    nimi_en = models.CharField(max_length=200, blank=True, null=True)
    selite_en = models.TextField(blank=True, null=True)
    kuvaus_en = models.CharField(max_length=800, blank=True, null=True)
    metatiedot = models.JSONField(blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'kysymysryhma'


class KysymysryhmaKyselypohja(models.Model):
    kysymysryhmaid = models.OneToOneField(Kysymysryhma, models.DO_NOTHING, db_column='kysymysryhmaid', primary_key=True)
    kyselypohjaid = models.ForeignKey(Kyselypohja, models.DO_NOTHING, db_column='kyselypohjaid')
    jarjestys = models.IntegerField()
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja',
        related_name='kysymysryhmakyselypohja_muutettu_kayttaja')
    luotuaika = models.DateTimeField()
    muutettuaika = models.DateTimeField()

    class Meta:
        managed = managed
        db_table = 'kysymysryhma_kyselypohja'
        unique_together = (('kysymysryhmaid', 'kyselypohjaid'),)


class Monivalintavaihtoehto(models.Model):
    monivalintavaihtoehtoid = models.AutoField(primary_key=True)
    kysymysid = models.ForeignKey(Kysymys, models.DO_NOTHING, db_column='kysymysid',
                                  related_name='monivalintavaihtoehdot')
    jarjestys = models.IntegerField()
    teksti_fi = models.CharField(max_length=400, blank=True, null=True)
    teksti_sv = models.CharField(max_length=400, blank=True, null=True)
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja',
        related_name='monivalintavaihtoehto_muutettu_kayttaja')
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    teksti_en = models.CharField(max_length=400, blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'monivalintavaihtoehto'
        unique_together = (('kysymysid', 'jarjestys'),)


class Organisaatio(models.Model):
    ytunnus = models.CharField(max_length=10, blank=True, null=True)
    nimi_fi = models.CharField(max_length=200)
    nimi_sv = models.CharField(max_length=200, blank=True, null=True)
    sahkoposti = models.CharField(max_length=100, blank=True, null=True)
    puhelin = models.CharField(max_length=100, blank=True, null=True)
    osoite = models.CharField(max_length=100, blank=True, null=True)
    postinumero = models.CharField(max_length=5, blank=True, null=True)
    postitoimipaikka = models.CharField(max_length=40, blank=True, null=True)
    www_osoite = models.CharField(max_length=200, blank=True, null=True)
    oid = models.CharField(primary_key=True, max_length=40)
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    voimassa = models.BooleanField()
    lakkautuspaiva = models.DateField(blank=True, null=True)
    nimi_en = models.CharField(max_length=200, blank=True, null=True)
    tyypit = models.TextField(blank=True, null=True)
    oppilaitoskoodi = models.CharField(max_length=5, blank=True, null=True)
    parent_oid = models.ForeignKey('self', models.DO_NOTHING, db_column='parent_oid', blank=True, null=True)
    oppilaitostyyppi = models.CharField(max_length=5, blank=True, null=True)
    toimipistekoodi = models.CharField(max_length=9, blank=True, null=True)
    kunta = models.CharField(max_length=3, blank=True, null=True)
    metatiedot = models.JSONField(blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'organisaatio'


class TilaEnum(models.Model):
    nimi = models.CharField(primary_key=True, max_length=20)
    muutettuaika = models.DateTimeField(auto_now=True)
    luotuaika = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = managed
        db_table = 'tila_enum'


class Tutkinto(models.Model):
    tutkintotunnus = models.CharField(primary_key=True, max_length=6)
    opintoala = models.CharField(max_length=3, blank=True, null=True)
    nimi_fi = models.CharField(max_length=200)
    nimi_sv = models.CharField(max_length=200, blank=True, null=True)
    voimassa_alkupvm = models.DateField(blank=True, null=True)
    voimassa_loppupvm = models.DateField(blank=True, null=True)
    luotuaika = models.DateTimeField()
    muutettuaika = models.DateTimeField()
    siirtymaajan_loppupvm = models.DateField(blank=True, null=True)
    nimi_en = models.CharField(max_length=200, blank=True, null=True)
    tutkintotyyppi = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'tutkinto'


class Vastaaja(models.Model):
    vastaajaid = models.AutoField(primary_key=True)
    kyselykertaid = models.ForeignKey(Kyselykerta, models.DO_NOTHING, db_column='kyselykertaid')
    vastaajatunnusid = models.OneToOneField('Vastaajatunnus', models.DO_NOTHING, db_column='vastaajatunnusid')
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    vastausaika = models.DateField()
    tyyppi = models.TextField(blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'vastaaja'


class Vastaajatunnus(models.Model):
    vastaajatunnusid = models.AutoField(primary_key=True)
    kyselykertaid = models.ForeignKey(Kyselykerta, models.DO_NOTHING, db_column='kyselykertaid')
    tutkintotunnus = models.ForeignKey(Tutkinto, models.DO_NOTHING, db_column='tutkintotunnus', blank=True, null=True)
    tunnus = models.CharField(unique=True, max_length=30)
    kohteiden_lkm = models.IntegerField(blank=True, null=True)
    lukittu = models.BooleanField()
    luotu_kayttaja = models.ForeignKey(Kayttaja, models.DO_NOTHING, db_column='luotu_kayttaja')
    muutettu_kayttaja = models.ForeignKey(
        Kayttaja, models.DO_NOTHING, db_column='muutettu_kayttaja', related_name='vastaajatunnus_muutettu_kayttaja')
    luotuaika = models.DateTimeField(auto_now_add=True)
    muutettuaika = models.DateTimeField(auto_now=True)
    voimassa_alkupvm = models.DateField(blank=True, null=True)
    voimassa_loppupvm = models.DateField(blank=True, null=True)
    suorituskieli = models.CharField(max_length=2, blank=True, null=True)
    koulutusmuoto = models.CharField(max_length=255, blank=True, null=True)
    kunta = models.CharField(max_length=3, blank=True, null=True)
    taustatiedot = models.JSONField(blank=True, null=True)
    metatiedot = models.JSONField(blank=True, null=True)

    class Meta:
        managed = managed
        db_table = 'vastaajatunnus'
