from datetime import date
from django.test import SimpleTestCase, TestCase
from elasticsearch_metrics import metrics

from mourningwail.exceptions import ReportInvalid
from mourningwail.metrics._base import DailyReport
from mourningwail.reporters import DAILY_REPORTERS


class TestDailyReportKey(SimpleTestCase):
    def test_default(self):
        # only one of this type of report per day
        class UniqueByDate(DailyReport):
            blah = metrics.Keyword()

        today = date(2022, 5, 18)

        reports = [
            UniqueByDate(report_date=today),
            UniqueByDate(report_date=today, blah='blah'),
            UniqueByDate(report_date=today, blah='fleh'),
        ]
        expected_key = 'facd9753f0c2c37be44a71c66e4037d2d48ea21f1a9b7c342ecb03a9737763f0'
        assert all(
            report.get_report_key() == expected_key
            for report in reports
        ), 'DailyReport.get_report_key() (with DAILY_UNIQUE_FIELD=None) should depend only on report_date'

    def test_with_duf(self):
        # multiple reports of this type per day, unique by given field
        class UniqueByDateAndField(DailyReport):
            DAILY_UNIQUE_FIELD = 'duf'
            duf = metrics.Keyword()

        today = date(2022, 5, 18)

        expected_blah = 'dfd6f7d33ae8c4e6b53c9b1bb73332b59d1832d45f56bde610124b6123e1eb52'
        actual_blah = UniqueByDateAndField(report_date=today, duf='blah').get_report_key()
        assert actual_blah == expected_blah

        expected_fleh = '7eb3c317fa8bbdc230a9b8e9c42bd966e9ecc690104490c9d452067517d1f634'
        actual_fleh = UniqueByDateAndField(report_date=today, duf='fleh').get_report_key()
        assert actual_fleh == expected_fleh

        expected_message = 'UniqueByDateAndField.duf MUST have a string value'
        with self.assertRaisesMessage(ReportInvalid, expected_message):
            UniqueByDateAndField(report_date=today).get_report_key()


class TestReportersDoSomething(TestCase):
    def test_for_smoke(self):
        today = date.today()
        for Reporter in DAILY_REPORTERS:
            report = Reporter().report(today)
            assert report.report_date == today
