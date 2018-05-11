import factory


class ThemeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'events.Theme'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'Test Theme %d' % n)


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'events.Event'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: 'Test Event %d' % n)
    theme = factory.SubFactory(ThemeFactory)
    current = False
    about_text = factory.Faker('text')
    rules_text = factory.Faker('text')
    help_text = factory.Faker('text')
    examples_text = factory.Faker('text')
    max_team_size = factory.Faker('random_int', min=0, max=10)


class EventFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = 'events.EventFile'
        django_get_or_create = ('event', 'slug')

    event = factory.SubFactory(EventFactory)
    slug = factory.Faker('slug')
    file = factory.django.FileField(
        filename=factory.Faker('file_name'),
        data=factory.Faker('binary', length=factory.Faker('random-int', min=1, max=1048576))
    )
