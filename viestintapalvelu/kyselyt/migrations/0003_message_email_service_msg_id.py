# Generated by Django 3.2.10 on 2022-03-30 10:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kyselyt', '0002_ophauthentication'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='email_service_msg_id',
            field=models.IntegerField(default=0),
        ),
    ]
