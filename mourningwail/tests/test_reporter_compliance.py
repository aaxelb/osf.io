from datetime import date
from django.test import TestCase

from mourningwail.reporters import DAILY_REPORTERS

class TestReportersDoSomething(TestCase):
    def test_for_smoke(self):
        today = date.today()
        for Reporter in DAILY_REPORTERS:
            report = Reporter().report(today)
            assert report.report_date == today
