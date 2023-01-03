"""Utilities for pushing metadata to SHARE
"""
from functools import partial
import uuid
from django.apps import apps
from urllib.parse import urljoin
import random
import requests
from celery.exceptions import Retry

from framework.celery_tasks import app as celery_app
from framework.sentry import log_exception
from osf.metadata import rdfutils
from osf.metadata.gather import gather_description_set
from website import settings


def send_share_rdf(resource, rdfgraph):
    """send metadata to SHARE, using the provider for the given resource.
    """
    if getattr(resource, 'provider') and resource.provider.access_token:
        access_token = resource.provider.access_token
    else:
        access_token = settings.SHARE_API_TOKEN

    return requests.put(
        f'{settings.SHARE_URL}push///{rdfutils.guid_irl(resource)}',
        data=rdfgraph.serialize(format='turtle'),
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'text/turtle',
        },
    )


def update_share(resource):
    description = gather_description_set(resource._id)
    resp = send_share_rdf(resource, description)
    status_code = resp.status_code
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        if status_code >= 500:
            async_update_resource_share.delay(resource._id)
        else:
            log_exception()


@celery_app.task(bind=True, max_retries=4, acks_late=True)
def async_update_resource_share(self, guid):
    """
    This function updates share  takes Preprints, Projects and Registrations.
    :param self:
    :param guid:
    :return:
    """
    AbstractNode = apps.get_model('osf.AbstractNode')
    resource = AbstractNode.load(guid)
    if not resource:
        Preprint = apps.get_model('osf.Preprint')
        resource = Preprint.load(guid)

    description = gather_description_set(resource._id)
    resp = send_share_rdf(resource, description)
    try:
        resp.raise_for_status()
    except Exception as e:
        if self.request.retries == self.max_retries:
            log_exception()
        elif resp.status_code >= 500:
            try:
                self.retry(
                    exc=e,
                    countdown=(random.random() + 1) * min(60 + settings.CELERY_RETRY_BACKOFF_BASE ** self.request.retries, 60 * 10),
                )
            except Retry:  # Retry is only raise after > 5 retries
                log_exception()
        else:
            log_exception()

    return resp
