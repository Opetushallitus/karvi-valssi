from django.db import models


class Message(models.Model):
    msg_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=80)
    msg_status = models.CharField(max_length=20)
    template = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    email_service_msg_id = models.IntegerField(default=0)
    email_service_msg_id_str = models.CharField(max_length=80, blank=True, null=True)
    email_service_status_code = models.CharField(max_length=20, default="")
    end_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'message'


class OphAuthentication(models.Model):
    tgt = models.CharField(max_length=300, blank=True)
    tgt_last_cleared_time = models.DateTimeField(blank=True, null=True)
    viestinvalitys_session_cookie = models.CharField(max_length=80, default="")
    viestinvalitys_session_cookie_last_update_time = models.CharField(max_length=50, default="")

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


class MessageQueue(models.Model):
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
        db_table = 'messagequeue'
