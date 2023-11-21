from django.db import models


class Message(models.Model):
    msg_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=80)
    msg_status = models.CharField(max_length=20)
    template = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    email_service_msg_id = models.IntegerField(default=0)

    class Meta:
        managed = True
        db_table = 'message'


class OphAuthentication(models.Model):
    tgt = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        managed = True
        db_table = 'ophauthentication'


class FailedTask(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=80)
    vastaajatunnus = models.CharField(max_length=20)
    message = models.CharField(max_length=5000, default="")
    template = models.IntegerField()
    msg_id = models.IntegerField()
    pdfs_encoded = models.JSONField(default=list)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = True
        db_table = 'failedtask'
