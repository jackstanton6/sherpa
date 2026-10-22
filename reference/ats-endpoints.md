# Public ATS feeds

`scripts/jobs.py probe` uses these. Each is a public, unauthenticated endpoint that the ATS vendor provides so companies can embed their job boards. All were verified live on 22 October 2026. Public feeds change, so if an adapter breaks, check here first and fix only that adapter.

| ATS | How to spot it | Feed URL | Not found |
|---|---|---|---|
| Greenhouse | `boards.greenhouse.io/<slug>`, `job-boards.greenhouse.io/<slug>`, `greenhouse.io/embed/job_board?for=<slug>`, `?gh_jid=` links | `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs?content=true` | 404 |
| Lever | `jobs.lever.co/<slug>` | `https://api.lever.co/v0/postings/<slug>?mode=json` | 404 |
| Ashby | `jobs.ashbyhq.com/<slug>` | `https://api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true` | 404 |
| Workable | `apply.workable.com/<slug>`, `<slug>.workable.com` | `https://apply.workable.com/api/v1/widget/accounts/<slug>?details=true` | 404 |

## Field mapping into the Sherpa schema

| Sherpa field | Greenhouse | Lever | Ashby | Workable |
|---|---|---|---|---|
| title | `title` | `text` | `title` | `title` |
| location | `location.name` | `categories.location` | `location` | `city, state, country` |
| work_mode | from location text | `workplaceType` | `workplaceType` / `isRemote` | `telecommuting` |
| salary | (rare, not mapped) | `salaryRange.min/max/currency` | `compensation.summaryComponents[Salary]` | (not mapped) |
| url | `absolute_url` | `hostedUrl` | `jobUrl` | `url` |
| apply_url | `absolute_url` | `applyUrl` | `applyUrl` | `application_url` |
| posted_at | `first_published` or `updated_at` | `createdAt` (ms epoch) | `publishedAt` | `published_on` |
| description | `content` (HTML-escaped HTML) | `descriptionPlain` + `additionalPlain` | `descriptionPlain` | `description` (HTML) |

## Not covered (reported as `no-feed`)

Workday, iCIMS, Taleo, SuccessFactors and most in-house career sites have no simple public feed. For these, `probe` returns `no-feed` and the scout skill reads the careers page with WebFetch instead. Sites that need a login or block automated access are skipped and reported, never worked around.

## Optional job API

**Adzuna** (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, optional `ADZUNA_COUNTRY`, default `us`): `https://api.adzuna.com/v1/api/jobs/<country>/search/1?app_id=…&app_key=…&what=…&where=…&results_per_page=50`. Free keys from developer.adzuna.com. Keys are read from the environment and never written to disk.

## Politeness

`jobs.py` identifies itself in the User-Agent, waits at least one second between requests to the same host, caches responses for an hour under `~/.sherpa/cache/`, and checks `robots.txt` before fetching any HTML careers page.
