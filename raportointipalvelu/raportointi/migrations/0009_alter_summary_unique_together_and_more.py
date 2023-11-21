# Generated by Django 4.1.7 on 2023-02-27 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raportointi', '0008_result'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='summary',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='summary',
            name='kysely_voimassa_alkupvm',
            field=models.DateField(default='2000-01-01'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='summary',
            name='kysymysryhmaid',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='summary',
            unique_together={('kysymysryhmaid', 'oppilaitos', 'kysely_voimassa_alkupvm')},
        ),
        migrations.RemoveField(
            model_name='summary',
            name='kyselykertaid',
        ),
    ]
