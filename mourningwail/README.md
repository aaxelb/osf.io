# mourningwail
for recording observations two ways:
- everflowing stream of events ('EventRecord')
- planned, periodic analysis reports ('DailyReport')

## notable code locations

### `mourningwail.tests`
the most important TODO

### `mourningwail.metrics`
this is mourningwail's data layer: definitions of
`MeteredEvent` and `DailyReport` for storage in elasticsearch

### `mourningwail.reporters`
each `DailyReporter` generates a `DailyReport` for a given date (most often yesterday)

may query/analyze past `MeteredEvent` and `DailyReport`,
may also observe data other ways

### `mourningwail.management.commands`
`fake_reports`: for filling a local instance with random data
`daily_reporters_go`: calls `mourningwail.tasks.daily_reporters_go`

### `mourningwail.tasks`
`daily_reporters_go` has each `DailyReporter` do their thing
for yesterday, then stores the results

### `mourningwail.urls`
up for inclusion in another django app (see `../api/base/urls.py`)

- `/report/*` (read-only): for viewing `DailyReport`
- `/event/*` (write-only): for storing `MeteredEvent`
- `/query/*` (read-only): for querying `MeteredEvent`

### `mourningwail.views`
- store `MeteredEvent` (but not directly view them)
- view `DailyReporter` names
- view latest `DailyReport` from a given `DailyReporter` name
- query `MeteredEvent` (only static-coded queries for now)


## possible future work
- make it a community-friendly, reusable tool
    - separably installable django addon (or python package?)
- expose reports in agreement with "COUNTER" (http://projectcounter.org)
    - add `MonthlyReport` (sibling of `DailyReport`) and `monthly_reporters_go`
    - per-item reports
- lean into parallel between COUNTER and OAI-PMH
    - start to compose a "general repository protocol" of existing open protocols with good constraints
    - OAI-PMH exposes items from a community, each on equal footing
    - COUNTER exposes a community's enthusiasm, how they have focused their attention
    - lean on open web standards for accessible web interface: embrace the simple semantics of HTTP methods and HTML tags
