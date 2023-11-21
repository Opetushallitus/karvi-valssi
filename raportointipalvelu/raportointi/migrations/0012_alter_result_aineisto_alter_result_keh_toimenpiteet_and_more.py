# Generated by Django 4.1.7 on 2023-05-25 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raportointi', '0011_userauthorization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='result',
            name='aineisto',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='keh_toimenpiteet',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='kohteet',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='kuvaus',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='seur_toimenpiteet',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='vahvuudet',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='summary',
            name='aineisto',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='summary',
            name='keh_toimenpiteet',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='summary',
            name='kohteet',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='summary',
            name='kuvaus',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='summary',
            name='seur_toimenpiteet',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
        migrations.AlterField(
            model_name='summary',
            name='vahvuudet',
            field=models.CharField(blank=True, max_length=20000, null=True),
        ),
    ]