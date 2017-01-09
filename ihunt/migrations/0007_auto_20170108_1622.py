# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-08 16:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ihunt', '0006_auto_20161128_0743'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='team',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='team',
            name='at_event',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='teams',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='user',
        ),
        migrations.AlterField(
            model_name='guess',
            name='by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.UserProfile'),
        ),
        migrations.AlterField(
            model_name='teampuzzledata',
            name='team',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.Team'),
        ),
        migrations.AlterField(
            model_name='userpuzzledata',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.UserProfile'),
        ),
        migrations.DeleteModel(
            name='Team',
        ),
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]
