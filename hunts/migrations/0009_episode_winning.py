# Generated by Django 2.0.7 on 2018-08-29 20:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hunts', '0008_auto_20180815_2122'),
    ]

    operations = [
        migrations.AddField(
            model_name='episode',
            name='winning',
            field=models.BooleanField(default=False, help_text='Whether this episode must be won in order to win the event'),
        ),
    ]
