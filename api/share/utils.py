"""Utilities for pushing metadata to SHARE
"""
import random

import requests
from celery.exceptions import Retry
from django.apps import apps

from framework.celery_tasks import app as celery_app
from framework import sentry
from website import settings
from osf.metadata.osf_gathering import pls_gather_metadata_file


def is_qa_resource(resource):
    """
    QA puts tags and special titles on their project to stop them from appearing in the search results. This function
    check if a resource is a 'QA resource' that should be indexed.
    :param resource: should be Node/Registration/Preprint
    :return:
    """
    tags = set(resource.tags.all().values_list('name', flat=True))
    has_qa_tags = bool(set(settings.DO_NOT_INDEX_LIST['tags']).intersection(tags))
    has_qa_title = any(substring in resource.title for substring in settings.DO_NOT_INDEX_LIST['titles'])
    return has_qa_tags or has_qa_title


class ShareTroubles(Exception):
    pass


class OsfTroubles(Exception):
    pass


def update_share(osf_resource):
    try:
        _do_update_share(osf_resource)
    except OsfTroubles:
        sentry.log_exception()
    except ShareTroubles:
        async_update_resource_share.delay(osf_resource._id)


@celery_app.task(bind=True, max_retries=4, acks_late=True)
def async_update_resource_share(self, guid):
    """
    This function updates share  takes Preprints, Projects and Registrations.
    :param self:
    :param guid:
    :return:
    """
    Guid = apps.get_model('osf.Guid')
    osf_resource = Guid.load(guid).referent
    try:
        _do_update_share(osf_resource)
    except OsfTroubles:
        sentry.log_exception()
    except ShareTroubles as error:
        self.retry(
            exc=error,
            countdown=(random.random() + 1) * min(60 + settings.CELERY_RETRY_BACKOFF_BASE ** self.request.retries, 60 * 10),
        )


def _do_update_share(osf_resource):
    if is_qa_resource(osf_resource):
        return
    metadata_file = pls_gather_metadata_file(osf_resource, 'turtle')
    resource_provider = getattr(osf_resource, 'provider')
    if resource_provider and resource_provider.access_token:
        access_token = resource_provider.access_token
    else:
        access_token = settings.SHARE_API_TOKEN
    resp = requests.put(
        f'{settings.SHARE_URL}push///{metadata_file.focus_iri}',
        data=metadata_file.serialized_metadata,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': metadata_file.mediatype,
        },
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as error:
        if resp.status_code >= 500:
            raise ShareTroubles from error
        raise OsfTroubles from error
