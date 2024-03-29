# Generated by Django 2.1.5 on 2019-02-07 15:37

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0002_auto_20180513_1909'),
        ('hunts', '0015_merge_20190126_1649'),
    ]

    operations = [
        migrations.CreateModel(
            name='Headstart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('headstart_adjustment', models.DurationField(default=datetime.timedelta(0), help_text='Time difference to apply to the headstart for the team on the specified episode. This will apply in addition to any headstart they earn through other mechanisms.')),
                ('episode', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hunts.Episode')),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='teams.Team')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='headstart',
            unique_together={('episode', 'team')},
        ),
    ]
