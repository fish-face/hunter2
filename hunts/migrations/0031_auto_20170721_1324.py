# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-21 12:24
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hunts', '0030_auto_20170721_1119'),
    ]

    operations = [
        migrations.RenameModel('UnlockGuess', 'UnlockAnswer')
    ]
