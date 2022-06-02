# mourningwail
for collecting observations, two ways:
- everflowing stream of events
- daily cadence of reports


## notable code locations

### `mourningwail.tests`
the most important TODO

### `mourningwail.metrics`
the data layer: definitions of `MeteredEvent` and `DailyReport`
models for storage in elasticsearch

### `mourningwail.reporters`
each `DailyReporter` generates a `DailyReport` for a given date (most often yesterday)

may query/analyze past `MeteredEvent` and `DailyReport`
may observe data other ways

### `mourningwail.tasks`
`daily_reporters_go` has each `DailyReporter` do their thing and stores the results

### `mourningwail.urls`
entry point for inclusion in another django app (see `../api/base/urls.py`)

- `/reports` (read-only): for viewing `DailyReport`
- `/events` (write-only): for storing `MeteredEvent`
- `/queries` (read-only): for querying `MeteredEvent`

### `mourningwail.views`
- store `MeteredEvent` (but not directly view them)
- view `DailyReport` (latest one or recent n)
- querying `MeteredEvent` (only static-coded for now)
