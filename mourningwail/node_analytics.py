from enum import Enum
import logging

from mourningwail.metrics.events import PageViewRecord


logger = logging.getLogger(__name__)


class MwTimespan(Enum):
    WEEK = 'week'
    FORTNIGHT = 'fortnight'
    MONTH = 'month'


# four aggregate queries to support the project/registration "analytics" page
MW_AGGREGATIONS = {
    'unique-visits': {
        'date_histogram': {
            'field': 'timestamp',
            'interval': 'day',
            'format': 'YYYY-MM-DD',
        },
    },
    'time-of-day': {
        'terms': {
            'field': 'hour_of_day',
            'size': 24,
        },
    },
    'referer-domain': {
        'terms': {
            'field': 'referer_domain',
            'size': 10,
        },
    },
    'popular-pages': {
        'terms': {
            'field': 'page_path',
            'exclude': '.*/project/.*',
            'size': 10,
        },
    },
}

def build_timespan_filter(timespan: MwTimespan):
    if timespan == MwTimespan.WEEK:
        return {
            'timestamp': {
                'gte': 'now-1w/d',
            },
        }
    if timespan == MwTimespan.FORTNIGHT:
        return {
            'timestamp': {
                'gte': 'now-2w/d',
            },
        }
    if timespan == MwTimespan.MONTH:
        return {
            'timestamp': {
                'gte': 'now-1m/d',
            },
        }
    raise NotImplementedError


def build_query_payload(node_guid: str, timespan: MwTimespan):
    return {
        'query': {
            'bool': {
                'filter': [
                    {'term': {'node_guid': node_guid}},
                    {'term': {'page_public': True}},
                    {'range': build_timespan_filter(timespan)},
                ],
            },
        },
        'size': 0,  # tell elasticsearch not to return any pagevisit events, just the aggregations
        'aggs': MW_AGGREGATIONS,
    }


def get_node_analytics(node_guid: str, timespan: str):
    analytics_search = PageViewRecord.search().update_from_dict(
        build_query_payload(node_guid, MwTimespan(timespan))
    )
    logger.warn(analytics_search.to_dict())
    analytics_results = analytics_search.execute()
    return {
        agg_name: analytics_results.aggregations[agg_name].to_dict()
        for agg_name in MW_AGGREGATIONS
    }
