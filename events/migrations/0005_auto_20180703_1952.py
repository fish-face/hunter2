# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-03 19:52
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('events', '0004_attendance'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together=set([('event', 'user')]),
        ),
    ]