# Generated by Django 4.1.6 on 2023-02-09 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raportointi', '0005_summary_taustatiedot'),
    ]

    operations = [
        migrations.AddField(
            model_name='summary',
            name='is_locked',
            field=models.BooleanField(default=True),
        ),
    ]
