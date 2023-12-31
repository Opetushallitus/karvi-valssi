# Generated by Django 4.0.5 on 2022-09-13 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kyselyt', '0011_delete_tyontekija'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scale',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('label_fi', models.CharField(blank=True, max_length=50, null=True)),
                ('label_sv', models.CharField(blank=True, max_length=50, null=True)),
                ('min_value', models.IntegerField()),
                ('max_value', models.IntegerField()),
                ('default_value', models.IntegerField()),
                ('step_count', models.IntegerField()),
                ('scale', models.JSONField()),
            ],
            options={
                'db_table': 'scale',
                'managed': True,
            },
        ),
    ]
