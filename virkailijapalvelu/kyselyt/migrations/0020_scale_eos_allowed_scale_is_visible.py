# Generated by Django 4.1.7 on 2023-07-25 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kyselyt', '0019_malfunctionmessage_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='scale',
            name='eos_allowed',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='scale',
            name='is_visible',
            field=models.BooleanField(default=True),
        ),
    ]