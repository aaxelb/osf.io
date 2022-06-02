"""


## report versioning
some `DailyReport`s (and their corresponding `DailyReporter`) were copied without revision from the
event structure defined by scripts in the (now-deleted) `scripts/analytics/` directory --
these classes are named with `V0` ("version zero", e.g. `NodeSummaryReportV0`)

when adding a new `DailyReport` class, start at `V1`

don't update a `DailyReport` in place! instead:
- add a new metric class incremented version number `V{n+1}`
- update the corresponding `DailyReporter`:
    - update `report` to generate `V{n+1}` reports
    - add method to convert from `V{n+1}` to `V{n}`
    - when saving a `V{n+1}` report, also convert to `V{n}` and save
- add recurring task to bulk-migrate past reports from the `V{n}` index to `V{n+1}`
- when `V{n+1}` index has all past reports:
    - update other code that uses `V{n}` to use `V{n+1}` instead
    - delete `V{n}` and accoutrement
"""
from elasticsearch_dsl import InnerDoc
from elasticsearch_metrics import metrics

from ._base import DailyReport


#### BEGIN reusable inner objects #####

class RunningTotal(InnerDoc):
    total = metrics.Integer()
    total_daily = metrics.Integer()

class FileRunningTotals(InnerDoc):
    total = metrics.Integer()
    public = metrics.Integer()
    private = metrics.Integer()
    total_daily = metrics.Integer()
    public_daily = metrics.Integer()
    private_daily = metrics.Integer()

class NodeRunningTotals(InnerDoc):
    total = metrics.Integer()
    total_excluding_spam = metrics.Integer()
    public = metrics.Integer()
    private = metrics.Integer()
    total_daily = metrics.Integer()
    total_daily_excluding_spam = metrics.Integer()
    public_daily = metrics.Integer()
    private_daily = metrics.Integer()

class RegistrationRunningTotals(InnerDoc):
    total = metrics.Integer()
    public = metrics.Integer()
    embargoed = metrics.Integer()
    embargoed_v2 = metrics.Integer()
    withdrawn = metrics.Integer()
    total_daily = metrics.Integer()
    public_daily = metrics.Integer()
    embargoed_daily = metrics.Integer()
    embargoed_v2_daily = metrics.Integer()
    withdrawn_daily = metrics.Integer()

##### END reusable inner objects #####


# TODO:
# class ActiveUsersReport(DailyReport):
#     past_day = metrics.Integer()
#     past_week = metrics.Integer()
#     past_30_days = metrics.Integer()
#     past_year = metrics.Integer()


class AddonUsageReportV0(DailyReport):
    DAILY_UNIQUE_FIELD = 'addon_shortname'

    addon_shortname = metrics.Keyword()
    users_enabled_count = metrics.Integer()
    users_authorized_count = metrics.Integer()
    users_linked_count = metrics.Integer()
    nodes_total_count = metrics.Integer()
    nodes_connected_count = metrics.Integer()
    nodes_deleted_count = metrics.Integer()
    nodes_disconnected_count = metrics.Integer()


class DownloadCountReportV0(DailyReport):
    daily_file_downloads = metrics.Integer()


class InstitutionSummaryReportV0(DailyReport):
    DAILY_UNIQUE_FIELD = 'institution_id'

    institution_id = metrics.Keyword()
    institution_name = metrics.Keyword()
    users = metrics.Object(RunningTotal)
    nodes = metrics.Object(NodeRunningTotals)
    projects = metrics.Object(NodeRunningTotals)
    registered_nodes = metrics.Object(RegistrationRunningTotals)
    registered_projects = metrics.Object(RegistrationRunningTotals)


class NewUserDomainReportV1(DailyReport):
    DAILY_UNIQUE_FIELD = 'domain_name'

    domain_name = metrics.Keyword()
    new_user_count = metrics.Integer()


class NodeSummaryReportV0(DailyReport):
    nodes = metrics.Object(NodeRunningTotals)
    projects = metrics.Object(NodeRunningTotals)
    registered_nodes = metrics.Object(RegistrationRunningTotals)
    registered_projects = metrics.Object(RegistrationRunningTotals)


class OsfstorageFileCountReportV0(DailyReport):
    files = metrics.Object(FileRunningTotals)


class PreprintSummaryReportV0(DailyReport):
    DAILY_UNIQUE_FIELD = 'provider_key'

    provider_key = metrics.Keyword()
    preprint_count = metrics.Integer()


class UserSummaryReportV0(DailyReport):
    active = metrics.Integer()
    deactivated = metrics.Integer()
    merged = metrics.Integer()
    new_users_daily = metrics.Integer()
    new_users_with_institution_daily = metrics.Integer()
    unconfirmed = metrics.Integer()
