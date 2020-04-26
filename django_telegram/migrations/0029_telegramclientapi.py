# Generated by Django 2.1.2 on 2019-01-23 16:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_telegram', '0028_message_new_chat_members'),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramClientAPI',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('api_id', models.IntegerField(unique=True)),
                ('api_hash', models.CharField(max_length=50)),
            ],
        ),
    ]
