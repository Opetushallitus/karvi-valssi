# Generated by Django 4.0.5 on 2022-08-31 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kyselyt', '0009_externalservices_delete_ophauthentication'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='kyselysend',
            name='tehtavanimike',
        ),
        migrations.AddField(
            model_name='kyselysend',
            name='tehtavanimikkeet',
            field=models.JSONField(default=dict),
        ),
    ]
