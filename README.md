<p align="center">
  <img src="assets/banner.svg" alt="Sherpa: the honest job-search toolkit for Claude Code" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT license" src="https://img.shields.io/badge/license-MIT-14b8a6"></a>
  <img alt="Claude Code plugin" src="https://img.shields.io/badge/Claude%20Code-plugin-f97316">
  <img alt="Python standard library only" src="https://img.shields.io/badge/python-stdlib%20only-0b1222">
  <img alt="No servers, no accounts" src="https://img.shields.io/badge/data-stays%20local-2dd4bf">
</p>

<p align="center">
  <b>A candid guide for the job-search climb.</b><br>
  Six simulated readers review your resume, Sherpa finds roles that never reach the big boards,<br>
  ranks them honestly, prepares your application, and never presses submit for you.
</p>

---

## Why Sherpa?

Job searching is slow, noisy and demoralising. Boards are crowded and stale, the best roles sit on company career pages, resume tools hand out flattering scores, and "auto-apply" bots spam employers on your behalf.

Sherpa takes the opposite approach:

| Most job tools | Sherpa |
|---|---|
| One flattering "resume score" | **Six independent reviewers**, each with a verdict and quoted evidence |
| The same stale board listings everyone sees | **Hidden jobs** pulled straight from company ATS feeds (Greenhouse, Lever, Ashby, Workable) |
| Hundreds of unranked results | **About ten ranked roles**, with reasons, gaps and an honest likelihood band |
| Fake "87% match" percentages | Bands only: *strong*, *possible*, *long shot* |
| Auto-apply spam | Prepares everything, then **stops for your yes** before every submit |
| Rewrites that invent achievements | **True facts only**: missing numbers become questions for you |
| Your data on someone's server | **Plain files on your machine.** No servers, no accounts |

## See it work

**The resume panel.** Six reviewers judge your resume in parallel, none seeing the others:

```
                         VERDICT      CONF    WHY
Automated screen         Consider     high    5/7 must-haves exact; two-column layout scrambles reading order
Hiring manager           Interview    medium  Forecasting work maps straight onto their inventory problem
Potential coworker       Interview    medium  Mentoring and cross-team work read as easy to work with
CEO                      Consider     medium  The $410K saving is buried in bullet four
Rival applicant          Consider     medium  Rival: 5 yrs, dbt + Looker. You win on domain, lose on dbt
Experienced recruiter    Interview    high    Coherent story, steady progression; would submit

PANEL  3 Interview · 3 Consider · 0 Pass
The humans like you; the software doesn't. That's a formatting fix, not a content fix.

FIX THESE (flagged by 3 reviewers)
  "Responsible for reporting across the department"
  → "Rebuilt [N] weekly reports for [team], cutting [time/requests] by [X]"
    needs info from you: how many reports, and what changed?
```

<sub>Illustrative output on a synthetic resume. Every quoted line is checked against your resume by code, and any quote that doesn't match is dropped.</sub>

**The morning brief.** An optional scheduled run, read-only:

```
# Morning brief: Thursday, 22 October

## Best new roles
1. Senior Data Analyst, Northwind Analytics (direct): Apply now · 84 · strong
   Denver, hybrid · $95-120K · posted 2 days ago
   /sherpa:apply greenhouse:northwind:4410

## Follow-ups due
- Copperline Energy, Analytics Analyst: due 1 Oct

## Coverage
Checked 30 of 42 companies. 2 unreachable. 12 new jobs seen, 3 worth your time.
```

## Install

In Claude Code:

```
/plugin marketplace add jackstanton6/sherpa
/plugin install sherpa@sherpa
```

Then start the climb:

```
/sherpa:setup ~/Downloads/resume.pdf
```

**Requirements:** [Claude Code](https://code.claude.com), and Python 3.9+ (standard library only). Optional extras:

| For | Install |
|---|---|
| Reading PDF resumes | `pdftotext` ([poppler](https://poppler.freedesktop.org)), **or** `pip install pypdf` |
| Exporting PDF resumes | Google Chrome or Microsoft Edge (already on most machines), **or** `pip install weasyprint` |
| Assisted form-fill | The Claude in Chrome browser extension |
| More job sources | Free [Adzuna](https://developer.adzuna.com) keys in `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` (optional `ADZUNA_COUNTRY`, default `us`) |

Sherpa tells you what's missing, with an install hint, if you need a tool you don't have.

## Commands

| Command | What you get |
|---|---|
| `/sherpa:setup` | A short interview builds your profile (roles, location, salary floor, work rights, deal-breakers), and your PDF becomes a clean text master |
| `/sherpa:resume` | **The six-reviewer panel:** a verdict grid, agreements and splits, lines to fix and lines to protect, ranked truthful fixes, and before/after on re-runs |
| `/sherpa:scout` | Web search, optional job APIs, and your target companies' own ATS feeds, then ranks everything with a coverage report |
| `/sherpa:rank` | Hard filters, a 100-point fit score, legitimacy signals, and a tier: *Apply now*, *Stretch* or *Skip* |
| `/sherpa:adjacent` | Roles you haven't searched for, backed by your resume lines and checked against real postings |
| `/sherpa:gaps` | Which missing skills block the most near-miss jobs, and which are **hidden strengths** your resume just doesn't show |
| `/sherpa:apply` | A tailored resume (PDF), a cover letter and draft answers, plus optional form-fill that **stops before submit** |
| `/sherpa:prep` | An interview prep sheet with a story bank drawn only from your real experience, and an optional mock interview |
| `/sherpa:pipeline` | Your application tracker, overdue follow-ups, and follow-up drafts (you send them) |
| `/sherpa:weekly` | A three-minute look back: what the numbers say (with sample sizes), stop/start/keep, next week's route, and a pace check |
| `/sherpa:morning` | The daily brief of new jobs worth your time. `setup` schedules it |

## How Sherpa finds hidden jobs

Many employers post first, or only, on their own careers page. Sherpa:

1. Builds a **watchlist** from your target companies and the employers web search turns up.
2. Detects the **applicant-tracking system** behind each careers page: from the URL, from markers in the page, or by trying the company's name.
3. Pulls the **public job feed** that Greenhouse, Lever, Ashby and Workable provide for embedding job boards. No login and no scraping.
4. Marks each job's source, so you can see which roles came **direct** and never showed up on the boards.

Companies without a public feed are read from their careers page. Anything behind a login, or blocked by `robots.txt`, is skipped and reported, never worked around.

## Honest by design

- **Calibrated, not kind.** Reviewers are told that most resumes land at *Consider* or *Pass* for a specific job, and that *Offer* is rare.
- **Evidence or it didn't happen.** Every verdict quotes your resume word for word, and code drops any quote that isn't really there.
- **Never invents facts about you.** Sherpa may rephrase, reorder and emphasise. A missing number becomes a question, never a guess.
- **Independent reviewers.** Six read-only agents with no web or write access, run in parallel, never seeing each other's opinions. Disagreements are shown, not smoothed over.
- **Numbers come from code.** The skills-gap counts and weekly figures are computed by `jobs.py`, and every insight states its sample size. Below 5 applications, it says *too early to tell*.
- **Legitimacy signals.** Stale postings, endless reposts, vague duties and board-only listings are flagged as *signals, not verdicts*.
- **You press submit.** Form-fill pauses on a summary of exactly what will be sent. Log-ins, CAPTCHAs and demographic or legal questions are always left to you.

## What leaves your machine

| Data | Where it goes |
|---|---|
| Your profile, resume, tracker, reports | **Nowhere.** Plain files in `~/.sherpa/` (or `$SHERPA_HOME`) |
| Resume text | To Claude, to do the review and tailoring. Nothing else |
| Job searches | Keywords and location only, to web search, public ATS feeds and Adzuna (if enabled). **Never your resume** |
| API keys | Read from environment variables, never written to disk |

`jobs.py` identifies itself in its User-Agent, makes at most one request per second per host, caches responses for an hour, and checks `robots.txt` before reading any careers page.

## Scheduled runs (optional)

`/sherpa:morning setup` and `/sherpa:weekly setup` register a task with **your own computer's scheduler** (Task Scheduler on Windows, cron on macOS and Linux). Cloud schedules can't see your local files. Each run is headless `claude -p` with locked-down permissions:

- **Allowed:** reading files, web search, Sherpa's helper scripts, and writing into `briefs/` (or `weekly/`). **Everything else is denied.**
- **Blocked:** editing your profile, resume or tracker, the browser, subagents, sending anything, and submitting anything. `SHERPA_READONLY=1` also makes the scripts refuse tracker and watchlist changes.
- If setup is incomplete, the brief says *run `/sherpa:setup` first* and stops, rather than guessing.

Remove a schedule any time with `python scripts/jobs.py schedule morning --remove` (or `weekly`).

## Your data

```
~/.sherpa/
├── profile.md             your profile (human-readable, edit freely)
├── resume-original.pdf    untouched copy of what you supplied
├── resume-master.md       the source of truth for all tailoring
├── watchlist.json         companies, careers URLs, detected ATS
├── jobs.jsonl             every job seen, with score, tier and gaps
├── tracker.csv            your applications and their history
├── applications/<co>-<role>/   resume.md/.pdf, cover letter, answers, interview prep
├── reviews/  briefs/  adjacent/  gaps/  weekly/   dated reports
└── schedule/              wrapper scripts and logs for scheduled runs
```

Sherpa keeps your data outside the plugin folder, so plugin updates and uninstalls never touch it.

## Under the hood

Sherpa is mostly **instructions plus two small scripts**, not a system:

```
skills/       11 skills, Markdown files Claude follows (the rubrics, the questions, the honesty rules)
agents/       6 read-only reviewer personas for the resume panel
reference/    shared rules: verdict scale, ranking rubric, ATS endpoints, the guide's voice
scripts/
  jobs.py       ATS detection + 4 feed adapters, Adzuna, dedupe, seen, gaps, stats, tracker, scheduling
  resume_io.py  PDF/DOCX/MD → text with layout flags, quote verification, Markdown → clean PDF
tests/        synthetic fixtures + stdlib unittest suite
```

Run the checks:

```bash
python tests/make_fixtures.py                 # synthetic resumes, postings, tracker
python tests/test_scripts.py                  # offline
SHERPA_LIVE=1 python tests/test_scripts.py    # + one real company per ATS
```

## Known limits

Honest about what it can't do:

- **The panel is simulated.** Its verdicts come from Claude playing six perspectives, not from real recruiters or hiring data. Use it to catch problems, not to predict any employer's decision.
- **The panel's live checks haven't been run yet.** The automated tests cover quote verification, PDF flags and the PDF round trip. The plan's live panel checks are still to do: strong resume beats weak, re-runs stay within one verdict step, and the weak resume never gets *Offer*. Run `/sherpa:resume` on the files in `tests/fixtures/` to try them.
- **Form-fill is fragile, and its approval gate hasn't been tested live.** Application forms vary widely, so the prepared pack is always the fallback. The gate is a hard rule in the skill, not code.
- **Coverage is partial.** Workday, iCIMS, Taleo and most in-house sites have no public feed, so Sherpa reads those pages directly or reports them as skipped.
- **Public feed formats can change.** Each ATS is one small, isolated adapter (verified live on 22 Oct 2026), so a break affects one source.
- **PDF extraction is imperfect.** Unusual designs can garble text. Sherpa flags suspected problems and asks you for the text.
- **Scheduled runs can run Python.** The permission rule is `Bash(python *)`, so a determined prompt injection in a job posting could in principle run arbitrary Python. Sherpa treats postings as untrusted data, and the run has no browser, no subagents, and no write access outside its output folder.
- **Small numbers.** A job search produces few data points. Weekly insights are hints, and Sherpa says so.

## FAQ

<details>
<summary><b>Will Sherpa apply to jobs for me automatically?</b></summary>

No, and it never will. It prepares the pack and can fill a form, but it stops on a summary and waits for your explicit "yes" for that specific application. Scheduled runs can't apply to anything.
</details>

<details>
<summary><b>Does it scrape LinkedIn or Indeed?</b></summary>

No. Sherpa uses public ATS feeds, official APIs and ordinary web search. Big boards appear only as normal search results.
</details>

<details>
<summary><b>Can it make up achievements to make my resume look better?</b></summary>

No. That's the one thing it's built never to do. Rewrites use only facts in your resume or facts you confirm. If a stronger line needs a number, Sherpa asks you for it.
</details>

<details>
<summary><b>Why bands instead of a match percentage?</b></summary>

Because "73% match" implies a precision nobody has. *Strong / possible / long shot* is honest about what the evidence supports.
</details>

## Contributing

Issues and PRs are welcome, especially:

- **New ATS adapters** (SmartRecruiters, Recruitee, Personio, and others). Each is one small function in `scripts/jobs.py`, plus a row in `reference/ats-endpoints.md` and a canned-payload test.
- **Better layout detection** for tricky PDF designs.
- **Fixture resumes** that catch a failure Sherpa currently misses (synthetic people only, please).

Keep it simple: Python standard library only, plain files, and no servers.

## License

[MIT](LICENSE). Built for anyone who's tired of shouting into the void of online applications.

<p align="center"><img src="assets/logo.svg" width="64" alt=""></p>
