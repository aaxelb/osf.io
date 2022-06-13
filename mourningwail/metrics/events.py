from urllib.parse import urlparse
from django.utils import timezone
from elasticsearch_metrics import metrics

from mourningwail.metrics._base import MeteredEvent


class PageVisitEvent(MeteredEvent):
    # fields that should be provided by the client
    referer_url = metrics.Keyword()
    page_url = metrics.Keyword()
    page_title = metrics.Keyword()
    page_public = metrics.Boolean()
    session_id = metrics.Keyword()
    node_guid = metrics.Keyword()

    # fields generated from the above
    path_n_title = metrics.Keyword()
    hour_of_day = metrics.Integer()
    page_path = metrics.Keyword()
    referer_domain = metrics.Keyword()

    # whatever dumpbucket
    keenstyle_event_info = metrics.Object(dynamic=True)

    @classmethod
    def record(cls, *, timestamp=None, **kwargs):
        timestamp = timestamp or timezone.now()
        path = kwargs.get('page_path')
        title = kwargs.get('page_title')
        path_n_title = filter(None, [path, title])
        referer_url = kwargs.get('referer_url')
        page_url = kwargs.get('page_url')

        return super().record(
            timestamp=timestamp,
            hour_of_day=timestamp.hour,
            path_n_title=path_n_title,
            page_path=urlparse(page_url).path if page_url else None,
            referer_domain=urlparse(referer_url).netloc if referer_url else None,
            **kwargs,
        )


class FileDownloadEvent(MeteredEvent):
    file_guid = metrics.Keyword()


class SystemLogEvent(MeteredEvent):
    pass  # TODO-quest


class UiInteractionEvent(MeteredEvent):
    pass  # TODO-quest
