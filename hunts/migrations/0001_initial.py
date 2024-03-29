# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-05-13 16:53
from __future__ import unicode_literals

import datetime
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import enumfields.fields
import hunts.models
import sortedm2m.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),
        ('accounts', '0001_initial'),
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('posted', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField(blank=True)),
                ('type', enumfields.fields.EnumField(default='I', enum=hunts.models.AnnouncementType, max_length=1)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='announcements', to='events.Event')),
            ],
        ),
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('runtime', models.CharField(choices=[('I', 'IFrame Runtime'), ('L', 'Lua Runtime'), ('R', 'Regex Runtime'), ('S', 'Static Runtime')], default='S', max_length=1)),
                ('answer', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('flavour', models.TextField(blank=True)),
                ('start_date', models.DateTimeField()),
                ('parallel', models.BooleanField(default=False, help_text='Allow players to answer riddles in this episode in any order they like')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.Event')),
                ('headstart_from', models.ManyToManyField(blank=True, help_text='Episodes which should grant a headstart for this episode', to='hunts.Episode')),
                ('prequels', models.ManyToManyField(blank=True, help_text='Set of episodes which must be completed before starting this one', related_name='sequels', to='hunts.Episode')),
            ],
        ),
        migrations.CreateModel(
            name='Guess',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guess', models.TextField()),
                ('given', models.DateTimeField(auto_now_add=True)),
                ('correct_current', models.BooleanField(default=False)),
                ('by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.UserProfile')),
                ('by_team', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='teams.Team')),
                ('correct_for', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='hunts.Answer')),
            ],
            options={
                'verbose_name_plural': 'Guesses',
            },
        ),
        migrations.CreateModel(
            name='Hint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Text displayed when this clue is unlocked')),
                ('time', models.DurationField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Puzzle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, unique=True)),
                ('flavour', models.TextField(blank=True, help_text='Separate flavour text for the puzzle. Should not be required for solving the puzzle', verbose_name='Flavour text')),
                ('runtime', models.CharField(choices=[('I', 'IFrame Runtime'), ('L', 'Lua Runtime'), ('R', 'Regex Runtime'), ('S', 'Static Runtime')], default='S', help_text='Runtime for generating the question content', max_length=1)),
                ('content', models.TextField()),
                ('cb_runtime', models.CharField(choices=[('I', 'IFrame Runtime'), ('L', 'Lua Runtime'), ('R', 'Regex Runtime'), ('S', 'Static Runtime')], default='S', help_text='Runtime for responding to an AJAX callback for this question, should return JSON', max_length=1, verbose_name='Callback runtime')),
                ('cb_content', models.TextField(blank=True, default='', verbose_name='Callback content')),
                ('start_date', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('headstart_granted', models.DurationField(default=datetime.timedelta(0), help_text='How much headstart this puzzle gives to later episodes which gain headstart from this episode')),
            ],
        ),
        migrations.CreateModel(
            name='PuzzleFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.CharField(help_text='Include the URL of the file in puzzle content using $slug or ${slug}.', max_length=50)),
                ('file', models.FileField(upload_to=hunts.models.puzzle_file_path)),
                ('puzzle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Puzzle')),
            ],
        ),
        migrations.CreateModel(
            name='TeamData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('team', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='teams.Team')),
            ],
            options={
                'verbose_name_plural': 'Team data',
            },
        ),
        migrations.CreateModel(
            name='TeamPuzzleData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.DateTimeField(blank=True, null=True)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('puzzle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Puzzle')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.Team')),
            ],
            options={
                'verbose_name_plural': 'Team puzzle data',
            },
        ),
        migrations.CreateModel(
            name='Unlock',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Text displayed when this clue is unlocked')),
                ('puzzle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Puzzle')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UnlockAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('runtime', models.CharField(choices=[('I', 'IFrame Runtime'), ('L', 'Lua Runtime'), ('R', 'Regex Runtime'), ('S', 'Static Runtime')], default='S', max_length=1)),
                ('guess', models.TextField()),
                ('unlock', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Unlock')),
            ],
        ),
        migrations.CreateModel(
            name='UserData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='events.Event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.UserProfile')),
            ],
            options={
                'verbose_name_plural': 'User data',
            },
        ),
        migrations.CreateModel(
            name='UserPuzzleData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('data', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('puzzle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Puzzle')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.UserProfile')),
            ],
            options={
                'verbose_name_plural': 'User puzzle data',
            },
        ),
        migrations.AddField(
            model_name='hint',
            name='puzzle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Puzzle'),
        ),
        migrations.AddField(
            model_name='guess',
            name='for_puzzle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Puzzle'),
        ),
        migrations.AddField(
            model_name='episode',
            name='puzzles',
            field=sortedm2m.fields.SortedManyToManyField(blank=True, help_text=None, to='hunts.Puzzle'),
        ),
        migrations.AddField(
            model_name='answer',
            name='for_puzzle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Puzzle'),
        ),
        migrations.AddField(
            model_name='announcement',
            name='puzzle',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='announcements', to='hunts.Puzzle'),
        ),
        migrations.AlterUniqueTogether(
            name='userpuzzledata',
            unique_together=set([('puzzle', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='userdata',
            unique_together=set([('event', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='teampuzzledata',
            unique_together=set([('puzzle', 'team')]),
        ),
        migrations.AlterUniqueTogether(
            name='puzzlefile',
            unique_together=set([('puzzle', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='episode',
            unique_together=set([('event', 'start_date')]),
        ),
    ]
