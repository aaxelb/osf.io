from django.core.management.base import BaseCommand

from mourningwail.tasks import daily_reporters_go


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--keen',
            type=bool,
            default=False,
            help='also send reports to keen',
        )
    def handle(self, *args, **options):
        daily_reporters_go(also_send_to_keen=options['keen'])
