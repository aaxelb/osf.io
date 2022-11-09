# osf-metrics
what is, what isn't, and what could be

## what is
* pageview info stored in our own elasticsearch timeseries database
    * pageviews from legacy ui and ember_osf_web
    * structured/documented to make COUNTER reports easy
    * kept secret
* reports also stored in our own es-ts-db
    * run daily
    * available in public json api (https://api.osf.io/_/metrics/reports/)

## what isn't (yet)
* visualizations based on our own data
* reports based on our own pageview info
* monthly COUNTER reports

## what could be
* visualization
    * kibana (for private use only, free-range exploratory analyses, devops burden)
    * public ui (existing reports api, limited to "preregistered" analyses, frontend burden)
* more usage logging
    * api requests by route (distinguish between web-client and direct access)
    * ui interactions (e.g. clicks)
* more (or improved) reports -- collab with data scientists
    * daily unique sessions
    * storage addon config by node/user
    * file downloads/views by storage addon
    * paths taken by users
