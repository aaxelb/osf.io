"""


"""
import json

from django.views.decorators.http import require_GET, require_POST
from django.http import HttpResponse, JsonResponse

from mourningwail.metrics.events import PageViewRecord
from mourningwail.metrics import reports
from mourningwail.node_analytics import get_node_analytics


@require_GET
def node_analytics_query(request, node_guid, timespan):
    return JsonResponse({
        'data': {
            'id': node_guid,
            'type': 'node-analytics',
            'attributes': get_node_analytics(node_guid, timespan),
        },
    })


@require_POST
def post_keenstyle_pageview(request):
    # request body expected to be json `{eventData: {...}}`,
    # where `{...}` is similar to what's constructed by
    # `_defaultKeenPayload` in website/static/js/keen.js
    request_bod = json.loads(request.body)
    keen_eventdata = request_bod['eventData']

    # TODO-quest: check for obvious fakery

    pagedata = keen_eventdata.get('page', {})

    PageViewRecord.record(
        referer_url=keen_eventdata.get('referrer', {}).get('url'),
        page_url=pagedata.get('url'),
        page_title=pagedata.get('title'),
        page_public=pagedata.get('meta', {}).get('public'),
        session_id=keen_eventdata.get('anon', {}).get('id'),
        node_guid=keen_eventdata.get('node', {}).get('id'),
        keenstyle_event_info=keen_eventdata,
    )
    return HttpResponse(status=201)


VIEWABLE_REPORTS = {
    'preprint_count': reports.PreprintSummaryReportV0,
    'user_count': reports.UserSummaryReportV0,
    # 'addon_usage': reports.AddonUsageReport,
    # 'daily_download_count': reports.DailyDownloadCountReport,
    # 'institution_summary': reports.InstitutionSummaryReport,
}


def serialize_report(report):
    # TODO-quest: consider detangling representation in elasticsearch from this serialization
    report_as_dict = report.to_dict()
    return {
        'id': report.meta.id,
        'type': 'report',
        'attributes': {
            **report_as_dict,
            'report_date': report_as_dict['report_date'].date().isoformat(),
        },
    }


MAX_REPORTS = 1000


@require_GET
def get_report_names(request):
    return JsonResponse({
        'report_names': list(VIEWABLE_REPORTS.keys()),
    })


@require_GET
def get_recent_reports(request, report_name):
    try:
        report_class = VIEWABLE_REPORTS[report_name]
    except KeyError:
        return HttpResponse(status=404, content=f'unknown report: "{report_name}"')

    # TODO-quest: start/end daterange?
    days_back = request.GET.get('days_back', 13)

    search_recent = (
        report_class.search()
        .filter('range', report_date={'gte': f'now/d-{days_back}d'})
        .sort('-report_date')
        [:MAX_REPORTS]
    )

    search_response = search_recent.execute()
    return JsonResponse({
        'data': [
            serialize_report(hit)
            for hit in search_response
        ],
    })


@require_GET
def get_latest_report(request, report_name):
    try:
        report_class = VIEWABLE_REPORTS[report_name]
    except KeyError:
        return HttpResponse(status=404, content=f'unknown report: "{report_name}"')

    latest_search = (
        report_class.search()
        .sort('-report_date', '-timestamp')
        [0]
    )

    search_response = latest_search.execute()
    if not search_response.hits:
        return HttpResponse(status=404, content=f'no "{report_name}" reports found')
    latest_report = search_response.hits[0]

    return JsonResponse({
        'data': serialize_report(latest_report),
    })
