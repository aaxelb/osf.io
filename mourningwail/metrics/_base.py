from hashlib import blake2s

from elasticsearch_metrics import metrics

from mourningwail.exceptions import ReportInvalid


class MeteredEvent(metrics.Metric):
    """MeteredEvent (abstract base for event-based metrics in mourningwail.events)

    Something happened! Let's quickly take note of it and move on,
    then come back later to query/analyze/investigate.
    """

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')
        source = metrics.MetaField(enabled=True)


class DailyReport(metrics.Metric):
    """DailyReport (abstract base for the report-based metrics in mourningwail.reports)

    There's something we'd like to know about every so often,
    so let's regularly run a report and stash the results here
    (then come back later to query/analyze/investigate)
    """
    DAILY_UNIQUE_FIELD = None  # set in subclasses that expect multiple reports per day

    report_date = metrics.Date(format='strict_date', required=True)

    def get_report_key(self) -> str:
        """a unique key for the report, to avoid accidental duplication
        """
        key_parts = [self.report_date.isoformat()]
        if self.DAILY_UNIQUE_FIELD is not None:
            duf_value = getattr(self, self.DAILY_UNIQUE_FIELD)
            if not isinstance(duf_value, str):
                raise ReportInvalid(f'{self.__class__.__name__}.{self.DAILY_UNIQUE_FIELD} MUST have a string value (got {duf_value})')
            key_parts.append(duf_value)

        plain_key = '--'.join(key_parts)
        # hash the key to get an opaque id
        return blake2s(bytes(plain_key, encoding='utf')).hexdigest()

    def save(self, **kwargs):
        self.meta.id = self.get_report_key()
        return super().save(**kwargs)

    class Meta:
        abstract = True
        dynamic = metrics.MetaField('strict')
        source = metrics.MetaField(enabled=True)
