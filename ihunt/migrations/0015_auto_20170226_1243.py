# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-26 12:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ihunt', '0014_auto_20170226_1243'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='answer',
            field=models.TextField(max_length=255),
        ),
    ]
