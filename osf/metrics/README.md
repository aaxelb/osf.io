# osf-metrics

imagine three information tiers:
- raw events
- regular reports
- retrospective analysis

## raw events
one user action (such as viewing a web page) becomes one stored event
(often referred to as "counted usage" in code).

raw events are:
- anonymized: cannot identify the user for a given event, nor query events for a given user
- deduplicated: if the exact same event occurs multiple times in a 30-second window, only the latest is stored
- grouped by "session": one user's actions within a time-window up to one day
- private: not directly exposed via api

## regular reports
regular reports let us observe how some statistic or variable changes over time.
reports may be based on raw events or any other data available in the system.

reports are:
- registered: the code to generate each report is committed to a public code
  repository, so there will be a record of any changes
- recurring: run automatically on a regular basis (every day or month)
- public: available via api

## retrospective analysis
osf-metrics makes its reports publicly available, but then stops there.
you can use those reports as inputs to any sort of analysis you like. go wild!
