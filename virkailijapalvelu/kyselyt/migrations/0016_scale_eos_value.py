# Generated by Django 4.0.5 on 2022-11-28 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kyselyt', '0015_koodi'),
    ]

    operations = [
        migrations.AddField(
            model_name='scale',
            name='eos_value',
            field=models.JSONField(null=True),
        ),
    ]
