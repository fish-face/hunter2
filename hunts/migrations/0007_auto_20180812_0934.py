# Generated by Django 2.0.7 on 2018-08-12 09:34

from django.db import migrations, models


def initialise_puzzlefile_url_path(apps, schema_editor):
    Class=apps.get_model('hunts', 'PuzzleFile')
    for f in Class.objects.all():
        f.url_path = f.slug
        f.save()


def initialise_solutionfile_url_path(apps, schema_editor):
    Class=apps.get_model('hunts', 'SolutionFile')
    for f in Class.objects.all():
        f.url_path = f.slug
        f.save()


class Migration(migrations.Migration):

    dependencies = [
        ('hunts', '0006_auto_20180807_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='puzzlefile',
            name='url_path',
            field=models.CharField(help_text='The path you want to appear in the URL. Can include "directories" using /', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='solutionfile',
            name='url_path',
            field=models.CharField(help_text='The path you want to appear in the URL. Can include "directories" using /', max_length=50, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='puzzlefile',
            unique_together={('puzzle', 'slug'), ('puzzle', 'url_path')},
        ),
        migrations.AlterUniqueTogether(
            name='solutionfile',
            unique_together={('puzzle', 'slug'), ('puzzle', 'url_path')},
        ),
        migrations.RunPython(initialise_puzzlefile_url_path, migrations.RunPython.noop),
        migrations.RunPython(initialise_solutionfile_url_path, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='puzzlefile',
            name='url_path',
            field=models.CharField(help_text='The path you want to appear in the URL. Can include "directories" using /', max_length=50),
        ),
        migrations.AlterField(
            model_name='solutionfile',
            name='url_path',
            field=models.CharField(help_text='The path you want to appear in the URL. Can include "directories" using /', max_length=50),
        ),
    ]
