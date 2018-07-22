# Copyright (C) 2018 The Hunter2 Contributors.
#
# This file is part of Hunter2.
#
# Hunter2 is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# Hunter2 is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with Hunter2.  If not, see <http://www.gnu.org/licenses/>.


from django.db import models
from django.core.validators import MinValueValidator
from django_tenants.models import TenantMixin, DomainMixin

from .fields import SingleTrueBooleanField

import accounts.models


class Theme(models.Model):
    name = models.CharField(max_length=255, unique=True)
    script = models.TextField(blank=True)
    style = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass


class Event(TenantMixin):
    auto_drop_schema = True
    name = models.CharField(max_length=255, unique=True)
    theme = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='theme')
    current = SingleTrueBooleanField()
    about_text = models.TextField(help_text='Content for the event about page', blank=True)
    rules_text = models.TextField(help_text='Content for the event rules page', blank=True)
    help_text = models.TextField(help_text='Content for the event help page', blank=True)
    examples_text = models.TextField(help_text='Content for the example puzzles for this event', blank=True)
    max_team_size = models.IntegerField(default=0, help_text="Maximum size for a team at this event, or 0 for no limit.", validators=[MinValueValidator(0)])
    end_date = models.DateTimeField()

    def __str__(self):
        return self.name

    def save(self, verbosity=0, *args, **kwargs):
        super().save(verbosity, *args, **kwargs)


def event_file_path(instance, filename):
    return 'events/{0}/{1}'.format(instance.event.id, filename)


class EventFile(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    slug = models.SlugField()
    file = models.FileField(upload_to=event_file_path)

    class Meta:
        unique_together = (('event', 'slug'), )


class Attendance(models.Model):
    user = models.ForeignKey(accounts.models.UserProfile, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    seat = models.CharField(
        max_length=12,
        blank=True,
        default='',
        help_text='Enter your seat so we can find you easily if you get stuck. (To help you, not to mock you <3)'
    )

    class Meta:
        unique_together = (('event', 'user'), )
