# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-13 23:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hunts', '0051_auto_20170813_2352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='puzzlefile',
            name='slug',
            field=models.SlugField(help_text='Include the URL of the file in puzzle content using $slug or ${slug}.'),
        ),
    ]