# Generated by Django 2.1.2 on 2018-12-25 07:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_telegram', '0002_auto_20181222_1550'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='content',
        ),
        migrations.RemoveField(
            model_name='message',
            name='deleted',
        ),
        migrations.RemoveField(
            model_name='message',
            name='forwarded',
        ),
    ]