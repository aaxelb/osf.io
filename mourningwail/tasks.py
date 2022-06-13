from datetime import timedelta
import logging

from django.utils import timezone

from framework.celery_tasks import app as celery_app
from mourningwail.reporters import DAILY_REPORTERS
from scripts.utils import add_file_logger
from website.app import init_app


logger = logging.getLogger(__file__)


@celery_app.task(name='mourningwail.tasks.daily_reporters_go')
def daily_reporters_go(also_send_to_keen=False):
    add_file_logger(logger, __file__)

    init_app()  # OSF-specific setup

    # run all reports for the same yesterday
    yesterday = (timezone.now() - timedelta(days=1)).date()

    for reporter_class in DAILY_REPORTERS:
        reporter_class().run_and_record_for_yesterday(
            verify_yesterday=yesterday,
            also_send_to_keen=also_send_to_keen,
        )
