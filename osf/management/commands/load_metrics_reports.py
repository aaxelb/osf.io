from django.conf import settings
from django.core.management.base import BaseCommand
import requests

from osf.management.utils import date_fromisoformat
from api.metrics.views import VIEWABLE_REPORTS


def load_reports_from_api(api_base, report_name, days_back):
    report_class = VIEWABLE_REPORTS[report_name]
    recent_report_url = f'{api_base.strip("/")}/_/metrics/reports/{report_name}/recent/?days_back={days_back}'
    response = requests.get(recent_report_url)
    response.raise_for_status()
    recent_reports = response.json()['data']
    for recent_report in recent_reports:
        report_attrs = {**recent_report['attributes']}
        report_attrs.pop('timestamp')
        report_attrs['report_date'] = date_fromisoformat(report_attrs['report_date'])
        report_class(**report_attrs).save()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--api-url',
            type=str,
            default='https://api.osf.io/',
            help='base url of the osf api to load reports from',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1000,
            help='how many days back to load reports',
        )

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            raise NotImplementedError('load_metrics_reports not for production use')
        for report_name in VIEWABLE_REPORTS:
            load_reports_from_api(kwargs['api_url'], report_name, kwargs['days_back'])
        # fake_user_counts(1000)
        # fake_preprint_counts(1000)
        # TODO: more reports
