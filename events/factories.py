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


import factory
import pytz

from django.db import connection
from faker import Faker
from faker.providers import BaseProvider

from accounts.factories import UserInfoFactory
from .models import Event


class EventsProvider(BaseProvider):
    def schema_name(self,):
        name = self.generator.format('domain_word')
        name = name.replace('-', '')
        return name


factory.Faker.add_provider(EventsProvider)


class SiteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'sites.Site'
        django_get_or_create = ('domain', 'name')
        exclude = ('fake', )

    fake = Faker()

    domain = fake.domain_name
    name = fake.company


class ThemeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'events.Theme'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'Test Theme %d' % n)


class DomainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'events.Domain'
        django_get_or_create = ('domain', )
        exclude = ('site', 'subdomain')

    site = factory.SubFactory(SiteFactory)
    subdomain = factory.Faker('schema_name')

    domain = factory.LazyAttribute(lambda o: f'{o.subdomain}.{o.site.domain}')


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'events.Event'

    name = factory.Sequence(lambda n: 'Test Event %d' % n)
    schema_name = factory.Faker('schema_name')
    theme = factory.SubFactory(ThemeFactory)
    current = False
    about_text = factory.Faker('text')
    rules_text = factory.Faker('text')
    help_text = factory.Faker('text')
    examples_text = factory.Faker('text')
    max_team_size = factory.Faker('random_int', min=0, max=10)
    end_date = factory.Faker('date_time_between', start_date='+1h', end_date='+3y', tzinfo=pytz.utc)

    domain = factory.RelatedFactory(DomainFactory, 'tenant', subdomain=schema_name)

    @classmethod
    def _create(cls, *args, **kwargs):
        if connection.schema_name != 'public':
            event = Event.objects.get()  # In some badly written tests this would throw MultipleObjectsReturned.
            for k, v in kwargs.items():
                if k in ('about_text', 'rules_text', 'help_text', 'examples_text', 'max_team_size', 'end_date'):
                    setattr(event, k, v)
            event.save()
            return event
        else:
            return super()._create(*args, **kwargs)


class EventFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'events.EventFile'
        django_get_or_create = ('event', 'slug')

    event = factory.SubFactory(EventFactory)
    slug = factory.Faker('word')
    file = factory.django.FileField(
        filename=factory.Faker('file_name'),
        data=factory.Faker('binary')
    )


class AttendanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'events.Attendance'
        django_get_or_create = ('event', 'user_info')

    user_info = factory.SubFactory(UserInfoFactory)
    event = factory.SubFactory(EventFactory)
    seat = factory.Faker('bothify', text='??##', letters='ABCDEFGHJKLMNPQRSTUVWXYZ')
