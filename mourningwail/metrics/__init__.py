from .events import (
    FileDownloadEvent,
    PageVisitEvent,
    SystemLogEvent,
    UiInteractionEvent,
)
from .reports import (
    AddonUsageReportV0,
    DownloadCountReportV0,
    InstitutionSummaryReportV0,
    NewUserDomainReportV1,
    NodeSummaryReportV0,
    OsfstorageFileCountReportV0,
    PreprintSummaryReportV0,
    UserSummaryReportV0,
)


METERED_EVENTS = (
    FileDownloadEvent,
    PageVisitEvent,
    SystemLogEvent,
    UiInteractionEvent,
)
DAILY_REPORTS = (
    AddonUsageReportV0,
    DownloadCountReportV0,
    InstitutionSummaryReportV0,
    NewUserDomainReportV1,
    NodeSummaryReportV0,
    OsfstorageFileCountReportV0,
    PreprintSummaryReportV0,
    UserSummaryReportV0,
)


__all__ = ('METERED_EVENTS', 'DAILY_REPORTS')
