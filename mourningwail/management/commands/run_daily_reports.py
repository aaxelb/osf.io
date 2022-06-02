from django.core.management.base import BaseCommand

from mourningwail.tasks import daily_reporters_go


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        daily_reporters_go()
