"""Resend metadata for all (or some) public objects (registrations, preprints...) to SHARE/Trove
"""
import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from osf.models import AbstractProvider, Institution, Registration, Preprint, Node
from api.share.utils import update_share

logger = logging.getLogger(__name__)


def recatalog_chunk(provided_model, provider_qs, institution_qs, start_id, chunk_size):
    items = provided_model.objects.filter(
        id__gte=start_id,
    ).order_by('id')

    if provider_qs is not None:
        items = items.filter(provider__in=provider_qs)

    if institution_qs is not None:
        # easy: filter to items directly affiliated via `affiliated_institutions` m2m
        # harder: filter to items that have a *contributor* affiliated
        directly_or_indirectly_affiliated = (
            Q(affiliated_institutions__in=institution_qs)
            | Q(_contributors__affiliated_institutions__in=institution_qs)
        )
        items = items.filter(directly_or_indirectly_affiliated)

    item_chunk = list(items[:chunk_size])
    last_id = None
    if item_chunk:
        first_id = item_chunk[0].id
        last_id = item_chunk[-1].id

        for item in item_chunk:
            update_share(item)

        logger.info(f'Recatalogued metadata for {len(item_chunk)} {provided_model.__name__}ses (ids in range [{first_id},{last_id}])')
    else:
        logger.info(f'Done recataloguing metadata for {provided_model.__name__}ses!')

    return last_id


class Command(BaseCommand):
    def add_arguments(self, parser):
        filter_group = parser.add_mutually_exclusive_group(required=True)
        filter_group.add_argument(
            '--providers',
            type=str,
            nargs='+',
            help='recatalog metadata for items from specific providers (by `_id`)',
        )
        filter_group.add_argument(
            '--all-providers',
            '-a',
            action='store_true',
            help='recatalog metadata for items from all providers',
        )
        filter_group.add_argument(
            '--institution',
            type=str,
            nargs='+',
            help='recatalog metadata for items affiliated with a specific institution',
        )

        type_group = parser.add_mutually_exclusive_group(required=True)
        type_group.add_argument(
            '--preprints',
            action='store_true',
            help='recatalog metadata for preprints',
        )
        type_group.add_argument(
            '--registrations',
            action='store_true',
            help='recatalog metadata for registrations (and registration components)',
        )
        type_group.add_argument(
            '--projects',
            action='store_true',
            help='recatalog metadata for non-registration projects (and components)',
        )

        parser.add_argument(
            '--start-id',
            type=int,
            default=0,
            help='id to start from, if resuming a previous run (default 0)',
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=500,
            help='maximum number of items to query at one time',
        )
        parser.add_argument(
            '--chunk-count',
            type=int,
            default=int(9e9),
            help='maximum number of chunks (default all/enough/lots)',
        )

    def handle(self, *args, **options):
        provider_ids = options['providers']
        institution_id = options['institution']

        pls_recatalog_preprints = options['preprints']
        pls_recatalog_registrations = options['registrations']
        pls_recatalog_projects = options['projects']

        start_id = options['start_id']
        chunk_size = options['chunk_size']
        chunk_count = options['chunk_count']

        provider_qs = None  # `None` means "don't filter by provider"
        if provider_ids:
            provider_qs = AbstractProvider.objects.filter(_id__in=provider_ids)

        institution_qs = None
        if institution_id:
            institution_qs = Institution.objects.filter(_id=institution_id)

        provided_model = None
        if pls_recatalog_preprints:
            provided_model = Preprint
        if pls_recatalog_registrations:
            provided_model = Registration
        if pls_recatalog_projects:
            provided_model = Node

        for _ in range(chunk_count):
            last_id = recatalog_chunk(provided_model, provider_qs, institution_qs, start_id, chunk_size)
            if last_id is None:
                logger.info('All done!')
                return
            start_id = last_id + 1
