# Generated by Django 2.1.2 on 2019-01-24 09:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_telegram', '0029_telegramclientapi'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telegramclientapi',
            name='api_id',
            field=models.IntegerField(),
        ),
    ]