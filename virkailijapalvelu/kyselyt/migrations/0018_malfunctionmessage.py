# Generated by Django 4.1.7 on 2023-05-22 06:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kyselyt', '0017_userauthorization'),
    ]

    operations = [
        migrations.CreateModel(
            name='MalfunctionMessage',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('code', models.IntegerField(unique=True)),
                ('message', models.CharField(max_length=500)),
                ('is_active', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'malfunctionmessage',
                'managed': True,
            },
        ),
    ]