# Generated by Django 4.1.6 on 2023-02-07 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raportointi', '0004_summary'),
    ]

    operations = [
        migrations.AddField(
            model_name='summary',
            name='taustatiedot',
            field=models.JSONField(default=dict),
        ),
    ]
