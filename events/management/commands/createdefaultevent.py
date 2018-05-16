import sys

from datetime import timedelta
from dateutil import parser as date_parser
from django.core.management import BaseCommand, CommandError
from django.utils import timezone

from events.models import Event, Theme


# Based on createsuperuser:
# https://github.com/django/django/blob/master/django/contrib/auth/management/commands/createsuperuser.py
class Command(BaseCommand):
    help = 'Creates a default development event and associated theme'

    DEFAULT_EVENT_NAME = "Development Event"
    DEFAULT_THEME_NAME = "Development Theme"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            '--theme',
            dest='theme_name',
            type=str,
            help="Name for the theme",
            default=None,
        )
        parser.add_argument(
            '--event',
            dest='event_name',
            type=str,
            help="Name for the event",
            default=None,
        )
        parser.add_argument(
            '--enddate', '--end-date',
            dest='end_date',
            type=str,
            help="End date for the event (accepts any format accepted by Python dateutil)",
            default=None,
        )
        parser.add_argument(
            '--noinput', '--no-input',
            action='store_false',
            dest='interactive',
            help=(
                "Tells Django to NOT prompt the user for input of any kind. "
                "You must use --theme and --event with --noinput."
            ),
        )

    def execute(self, *args, **options):
        self.stdin = options.get('stdin', sys.stdin)  # Used for testing
        return super().execute(*args, **options)

    def handle(self, *args, **options):
        theme_name = options['theme_name']
        event_name = options['event_name']
        end_date = options['end_date']

        if not options['interactive']:
            if not theme_name or not event_name or not end_date:
                raise CommandError("You must use --theme, --event and --enddate with --noinput.")
            try:
                end_date = date_parser.parse(end_date, default=timezone.now())  # TZ from default
            except ValueError as e:
                raise CommandError("End date is not a valid date.") from e

        while theme_name is None:
            theme_name = self.get_input_data("Theme name", default=self.DEFAULT_THEME_NAME)

        while event_name is None:
            event_name = self.get_input_data("Event name", default=self.DEFAULT_EVENT_NAME)

        while end_date is None:
            in_data = self.get_input_data("End date", default=self._default_end_date())
            try:
                end_date = date_parser.parse(in_data, default=timezone.now())  # TZ from default
            except ValueError:
                self.stderr.write(f'"{in_data}" is not a valid date')
                continue

        theme = Theme(name=theme_name)
        theme.save()
        event = Event(name=event_name, theme=theme, end_date=end_date, current=True)
        event.save()

        self.stdout.write("Created current event \"{}\" and theme \"{}\"".format(event_name, theme_name))

    @staticmethod
    def _default_end_date():
        return str(timezone.now() + timedelta(days=5))

    @staticmethod
    def get_input_data(field, default=None):
        if default:
            message = "{} (leave blank to use \'{}\'): ".format(field, default)
        else:
            message = "{}:".format(field)
        value = input(message)
        if default and value == '':
            value = default
        return value
