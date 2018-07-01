# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-13 19:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('hunts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='announcement',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='announcements', to='events.Event'),
        ),
        migrations.AlterField(
            model_name='episode',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='events.Event'),
        ),
        migrations.AlterField(
            model_name='userdata',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='events.Event'),
        ),
    ]