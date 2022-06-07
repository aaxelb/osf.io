# mourningwail
for observing two ways:
- everflowing stream of events ('MeteredEvent')
- regular cadence of reports ('DailyReport')

## concepts


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

### `mourningwail.tasks`
`daily_reporters_go` has each `DailyReporter` do their thing
for yesterday, then stores the results

### `mourningwail.urls`
entry point for inclusion in another django app (see `../api/base/urls.py`)

- `/report/*` (read-only): for viewing `DailyReport`
- `/event/*` (write-only): for storing `MeteredEvent`
- `/query/*` (read-only): for querying `MeteredEvent`

### `mourningwail.views`
- store `MeteredEvent` (but not directly view them)
- view `DailyReport` (latest one or recent n)
- query `MeteredEvent` (only static-coded for now)


## possible future work

