# Generated by Django 4.1.7 on 2023-09-21 05:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kyselyt', '0003_message_email_service_msg_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='FailedTask',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('email', models.EmailField(max_length=80)),
                ('vastaajatunnus', models.CharField(max_length=20)),
                ('message', models.CharField(default='', max_length=5000)),
                ('template', models.IntegerField()),
                ('msg_id', models.IntegerField()),
                ('pdfs_encoded', models.JSONField(default=list)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'failedtask',
                'managed': True,
            },
        ),
    ]