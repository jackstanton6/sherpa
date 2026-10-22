# Sherpa build plan

**v0.3, companion to WHITEPAPER.md.** Goal: the simplest thing that works, built in **one session** from a single linear checklist. There are no milestones: everything ships together.

## 1. Decisions already made

| Question | Decision |
|---|---|
| Name | **Sherpa** (the Job Finders Toolkit). Commands are `/sherpa:<skill>`. Check the name isn't already taken in the plugin marketplace before publishing. |
| Audience | Personal first, public later. Keep the profile and config generic from day one. |
| Job sources | Web search and fetch by default, plus optional job APIs when the user adds a key. |
| Resume format | PDF in (also accepts Word or Markdown), PDF out. |
| Resume review | A panel of six independent reviewer agents, each giving a five-step verdict. |
| Apply scope | Prepare the pack, plus assisted form-fill via Claude in Chrome that **stops for approval before every submit**. |
| Guide features | Adjacent roles, skills gap, a small interview prep tool, and a weekly review. All ship in the same build. |
| Scheduling | A morning brief and a weekly review. Both only read, analyse and report. |
| Docs format | Markdown in the repo. |

## 2. Repo layout

```
sherpa/
├── .claude-plugin/
│   └── plugin.json            # name, version, description
├── skills/
│   ├── setup/SKILL.md         # profile interview + resume intake (PDF)
│   ├── resume/SKILL.md        # the six-reviewer panel
│   ├── scout/SKILL.md         # find jobs (search, APIs, career pages)
│   ├── rank/SKILL.md          # filter, score, tier
│   ├── adjacent/SKILL.md      # roles you haven't searched for
│   ├── gaps/SKILL.md          # which missing skills block the most jobs
│   ├── apply/SKILL.md         # pack + PDF export + assisted form-fill
│   ├── prep/SKILL.md          # interview prep sheet + mock interview
│   ├── pipeline/SKILL.md      # tracker + follow-ups
│   ├── weekly/SKILL.md        # the weekly review (can be scheduled)
│   └── morning/SKILL.md       # scheduled daily brief (unattended-safe)
├── agents/                    # one small file per panel reviewer
│   ├── ats-screen.md
│   ├── hiring-manager.md
│   ├── coworker.md
│   ├── ceo.md
│   ├── rival.md
│   └── recruiter.md
├── reference/
│   ├── verdicts.md            # verdict scale, calibration rules, shared output format
│   ├── voice.md               # the guide's tone: candid, warm, evidence first
│   ├── ranking-rubric.md      # hard filters + 100-point fit score
│   └── ats-endpoints.md       # public feed URL patterns per ATS
├── scripts/
│   ├── jobs.py                # job helper (stdlib only)
│   └── resume_io.py           # PDF in/out + quote checking
├── tests/fixtures/            # sample resumes (PDF) and postings
└── README.md                  # install, what leaves your machine, limits
```

Check the current Claude Code plugin docs for the exact manifest fields, skill frontmatter and agent file format before writing them, because these have changed over time.

## 3. User data (local, outside the plugin folder so updates don't wipe it)

Default location: `~/.sherpa/`. Confirm at build time whether Claude Code now provides a dedicated per-plugin data directory and use that instead if so.

| File | Purpose |
|---|---|
| `profile.md` | Human-readable and editable. Target roles, location or commute limit, remote preference, salary floor, work rights, deal-breakers, seniority, target industries and companies, and morning-brief preferences. |
| `resume-original.pdf` | An untouched copy of the user's resume, as supplied. |
| `resume-master.md` | The full, true resume as clean Markdown. The source of truth for all tailoring. |
| `watchlist.json` | Companies to check: name, careers URL, detected ATS, last checked. |
| `jobs.jsonl` | Every job seen, in the normalised schema, with first-seen date, score and tier. |
| `tracker.csv` | Applied jobs, one row each: `job_id, company, role, source, tier_at_apply, likelihood_at_apply, applied, stage, last_update, follow_up, history, notes`. `stage` is one of applied, screen, interview, offer, rejected, withdrawn, no-reply. `history` is a short `date:stage;date:stage` trail, so the weekly review can see what happened and when. |
| `applications/<company>-<role>/` | Tailored resume (`.md` and `.pdf`), cover letter, answers, and `interview-prep.md`. |
| `reviews/<date>-resume.md` | Each resume panel report, kept so the user can compare before and after. |
| `briefs/<YYYY-MM-DD>.md` | One short morning brief per run. |
| `adjacent/<date>.md` | Each adjacent-roles report. |
| `gaps/<date>.md` | Each skills-gap report. |
| `weekly/<YYYY>-W<ww>.md` | Each weekly review. |

**Normalised job schema** (one JSON object per line): `id, title, company, location, work_mode (onsite|hybrid|remote|unknown), salary_min, salary_max, currency, source (ats|api|web), url, apply_url, posted_at, first_seen, description, ats`. The `rank` skill adds `must_have, nice_to_have, gaps, score, tier, likelihood`. The skills-gap and weekly features depend on these, so `gaps` entries are short, consistent lowercase phrases (for example `sql`, `people management`, `aws certification`) so they can be counted.

Optional API keys come from environment variables (for example `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`). They are never written to files.

## 4. Skills in brief

**setup**
Interview the user a few questions at a time. Write `profile.md`. Ask for their resume (PDF preferred), copy it to `resume-original.pdf`, run `resume_io.py extract`, and save the cleaned text as `resume-master.md`. Show the extraction to the user and fix anything garbled before saving. Always ask about work rights and deal-breakers, because these become hard filters.

**resume** (the panel)

*Inputs:* the resume (PDF path or the saved original) and a target, either a job posting (URL or pasted text) or the target role from `profile.md`. If neither exists and the user is present, ask once. If unattended, use the profile.

*Flow:*
1. Run `resume_io.py extract`. It returns the text plus flags: scanned or no text layer, suspected multi-column or scrambled order, very long or very short, missing contact details or links, text in images, odd characters. If the PDF has no text layer, tell the user and ask for the text (or OCR it if a tool is installed).
2. Take a quick look at the first page visually, using Claude's PDF reading, to note layout problems that the text hides. Pass these as a short layout note.
3. Launch the **six reviewer agents in parallel, in a single step**. Each receives only its own persona file, the resume text, the target, and the shared `verdicts.md`. They never see each other's output or the user's opinions. The automated screen gets the *raw* extraction exactly as a parser would see it. The others get the same text plus the layout note.
4. Run `resume_io.py verify-quotes` on all quoted lines. Any quote that does not appear in the resume is dropped and noted in the report.
5. Write the merged report (below) to `reviews/<date>-resume.md` and show it.
6. Offer next steps: draft truthful rewrites of the weakest lines (asking for any missing numbers), update `resume-master.md`, export a PDF, and **re-run the panel** to show verdict changes (before and after).

*The six reviewers:*

| Agent | Focus |
|---|---|
| `ats-screen` | Strict and mechanical. Parse quality, section headings, date formats, contact info, keyword match against the posting (exact and close), mandatory criteria (years, degree, location, work rights), keyword stuffing. Thinks in filters, not feelings. |
| `hiring-manager` | Can this person do the job and reduce my pain? Scope, outcomes, depth of skills, evidence over claims, risk. |
| `coworker` | Would I want to work with this person? Collaboration signals, "I" versus "we", credit and blame, tone, mentoring, communication. Flags ego and red flags. |
| `ceo` | A thirty-second skim. Trajectory, business impact (revenue, cost, risk), judgement, would I trust this person to represent the company. |
| `rival` | Imagines a strong, realistic rival for the same job (no real person is invented, and the assumptions are stated) and says where this resume is weaker, and where it is stronger. Adversarial but fair. |
| `recruiter` | Experienced. Six-second scan, story coherence, gaps and job-hopping, title progression, formatting, red flags, and whether they would put their name behind submitting this. |

*Shared rules (in `reference/verdicts.md`, used by every agent):*

| Verdict | Meaning |
|---|---|
| **Offer** | Exceptional. Would fast-track to an offer conversation. Should be rare. |
| **Interview** | Clearly worth a conversation. |
| **Consider** | The maybe pile. Would look again if stronger candidates run out. |
| **Pass** | Not moving forward. Reasonable, but outweighed. |
| **Burn** | Actively damaging: errors, dishonesty signals or serious unprofessionalism. Would discard it. |

- Be calibrated, not kind. For a specific job, most resumes are *Consider* or *Pass*.
- Judge only what is on the page. Don't assume facts that aren't there.
- Output the same fields every time: **Verdict**, **Reason** (one or two sentences), **Confidence** (low, medium, high), **Strongest lines** (up to 3, each quoted word-for-word with why), **Weakest lines** (up to 3, each quoted word-for-word with why), **Fixes** (up to 3, concrete, never inventing facts, and marked *needs info from you* where a number or detail is missing), and **What would change my mind**.
- Reviewers have no web or write tools. They only read what they are given.

*The merged report:*
1. **Verdict grid:** six reviewers, six verdicts, and each one's reason in a line.
2. **Panel headline:** for example "2 Interview, 3 Consider, 1 Pass", with a plain-English reading of it.
3. **Agreement and disagreement:** disagreements are shown, because they are informative (a coworker who likes you and a screen that rejects you means a formatting fix, not a content fix).
4. **Lines that matter:** lines flagged weak by two or more reviewers ("fix these") and lines flagged strong by two or more ("protect these").
5. **Ranked fixes:** priority is how many reviewers raised it times how severe it is. Each fix shows before and after wording using only true facts, or a question for the user.
6. **Caveat:** these are simulated perspectives, not real hiring data.

There is no numeric score. The verdicts are the result.

**scout**
1. Read `profile.md`.
2. Run web searches for the target roles and locations.
3. If API keys exist, call the job APIs through `jobs.py`.
4. Build or extend the watchlist. Find careers pages for target companies and for companies found in search results that fit the profile.
5. For each watchlist company, run `jobs.py probe` to detect the ATS and pull its public feed. If there is no feed, read the careers page with WebFetch. If that fails, record "unreachable" and move on.
6. Normalise, dedupe and apply the hard filters, then hand the survivors to `rank`.
7. Report coverage honestly: sources used, companies checked, companies skipped and why.

**rank**
- Hard filters first: location or commute, work rights, salary floor, deal-breakers. A job that fails is dropped with the reason noted.
- Fit score (100 points): skills match 30, seniority and experience match 20, role and preference match 15, location and work mode 10, compensation vs target 10, posting freshness and legitimacy 10, company signals 5.
- Output per job: tier (*Apply now* / *Stretch* / *Skip*), score, three reasons for, up to three gaps, legitimacy signals, likelihood band (*strong / possible / long shot*), and the source marked `direct` when it came from a careers page.
- Legitimacy signals (signals, not verdicts): posted more than 60 days ago, reposted repeatedly, vague duties, no team or location detail, listed on boards but absent from the careers page.
- Cap the "Apply now" list at about ten so attention stays focused.
- Save each job's `must_have`, `nice_to_have`, `gaps`, score, tier and likelihood to `jobs.jsonl`.

**adjacent**

*Inputs:* `resume-master.md` and `profile.md`. If either is missing, say "run `/sherpa:setup` first" and stop.

*Flow:*
1. List what the resume actually shows: skills, tools, the kinds of problems solved, domains, and strengths that carry over. Tie each to a resume line.
2. Propose **8 to 12 roles the user hasn't searched for**, in three groups with at most four each: **Close step** (same skills, different title or industry), **Pivot** (one or two real gaps), **Long reach** (a stretch, labelled honestly). Skip an empty group rather than padding it.
3. For each role give: why it fits (two resume lines as evidence), the other titles employers use for it (search terms), the likely gaps, and a likelihood band (*strong / possible / long shot*).
4. Check each role against current postings with web search, in the user's area or remote: do real postings exist, what do they ask for, roughly what do they pay. Drop roles with no real postings and say so.
5. Write the result to `adjacent/<date>.md`. Ask which roles to add to the target roles in `profile.md`, and add only the ones the user approves. `scout` then picks them up.

Rules: every idea comes from evidence on the page, not flattery. A long-shot pivot is called a long shot. Never suggest the user claim experience they don't have.

**gaps**

*Inputs:* `jobs.jsonl` (scored by `rank`) and `resume-master.md`. Needs at least about 10 scored jobs, otherwise say "run `/sherpa:scout` first".

*Flow:*
1. Run `jobs.py gaps`. It counts how often each gap phrase appears across the saved jobs, split by tier. The skill never counts by hand.
2. Focus on **near-miss jobs**: *Stretch* roles, and *Skip* roles that failed on fit rather than on a hard filter. A gap's **unlock count** is how many near-miss jobs it is the only or main thing missing from.
3. Sort each gap into one of three kinds:
   - **Real gap:** the user doesn't have it.
   - **Hidden strength:** the user probably has it but the resume doesn't show it. Ask. If true, it becomes a resume fix, not a learning task.
   - **Not worth chasing:** it appears rarely or only as a nice-to-have.
4. For the top five gaps give: unlock count and tier mix, the cheapest honest way to close it (a course, a small project, a certification, or a resume edit), a rough effort band (days, weeks or months), and a candid view on whether it is worth it.
5. Write `gaps/<date>.md`, opening with one paragraph such as "Close these two gaps and N roles move up a tier".

Rules: numbers come from `jobs.py gaps`, never from estimation. State how many jobs the report rests on. Don't recommend expensive credentials unless the data supports it.

**apply**
1. Create `applications/<company>-<role>/`.
2. Write a tailored resume variant in Markdown (true facts only), then export it with `resume_io.py render` as a single-column PDF with real text and standard fonts. Also write a cover letter and draft answers to common application questions.
3. Show the user the pack and wait for approval.
4. Optional assisted form-fill: open the application in Claude in Chrome, fill fields from `profile.md` and the pack, and stop on a summary of exactly what will be submitted, including which PDF will be attached. Upload and submit only after the user says yes, for that application.
5. Rules: the user logs in themselves, CAPTCHAs and demographic or legal declarations are left to the user, and any field Claude can't fill truthfully is left blank and flagged.
6. Log the result in `tracker.csv`.

**prep** (small on purpose)

*Inputs:* a job (from `jobs.jsonl` or a pasted posting), `resume-master.md`, and the latest resume panel report if there is one.

*Output:* `applications/<company>-<role>/interview-prep.md`, one or two pages:
1. **The role in five lines:** what they really care about, from the posting.
2. **Company brief:** a few lines from web search, with sources. If information is thin, say so.
3. **Likely questions (about ten):** four behavioural, three role-specific, two aimed at the user's weak spots (use lines the panel flagged and the job's gaps), and a couple of good questions for the user to ask them.
4. **Story bank (four or five stories):** drawn only from the resume, each as situation, action and result, and mapped to the questions it answers. Where a number or detail is missing, mark it *needs info from you* and ask.
5. **Awkward questions:** truthful framings for CV gaps, a missing skill or a career change. Never turn facts into something untrue.

*Mock interview (optional):* Sherpa plays the interviewer in chat, one question at a time, up to five. After each answer it gives short, candid feedback on clarity, evidence and length, plus one fix. At the end it names the two things to improve most. There are no subagents here, just one voice.

Rules: no invented stories. Follow `reference/voice.md`. If asked about pay, use the ranges seen in `jobs.jsonl` and say how many postings they rest on.

**pipeline**
Show the tracker, flag overdue follow-ups, update a job's `stage` (adding to `history`), and draft short follow-up messages on request.

**weekly** (the guide's look back)

*Inputs:* `tracker.csv`, `jobs.jsonl`, the week's `briefs/`, the latest `gaps/` and `reviews/`, and `profile.md`.

*Flow:*
1. If the user is present, ask first: "Any replies, interviews or rejections I haven't logged?" and update `tracker.csv` with their say-so. If the run is unattended, don't ask, and don't edit the tracker. Instead note how many applications have had no update for 14 days or more and say they need updating.
2. Run `jobs.py stats`. It returns the counts: applications this week and in total, by stage, by source (`direct` versus boards), by `tier_at_apply` and likelihood band, reply rate, median days to a reply, overdue follow-ups and stale entries. The skill never does arithmetic by hand.
3. Write `weekly/<YYYY>-W<ww>.md` in the voice of a seasoned guide (`reference/voice.md`), short enough to read in about three minutes:
   - **The week at a glance:** a few lines, in plain numbers.
   - **What the trail is telling you:** two or three insights, each with its sample size. Examples of what to look for: which sources or tiers get replies, whether the *strong* band really predicts interviews, whether too much effort goes to long shots, where applications stall (no reply, screen, interview), and whether tailored applications get more replies than quick ones. Below the minimum sample (default 5 applications), say "too early to tell" instead of guessing.
   - **Stop, start, keep:** one of each.
   - **The route ahead:** three to five concrete actions for next week, in order: follow-ups due, the best *Apply now* jobs, a gap to start closing, an adjacent role to try. Include a realistic weekly application cap, so quality beats volume.
   - **Pace check:** a short, kind note if the week suggests overload (many applications, a run of rejections, no rest) or drift (nothing sent). Encourage a break when it's earned. It is a guide's word, not therapy.
   - **Watchlist health:** feeds that broke and companies not checked in two weeks.
4. Show the review.

*Schedule (optional):* default Friday late afternoon in the user's own time zone, set in `profile.md` and created by a `/sherpa:weekly setup` step. Same rules as the morning brief: it reads, analyses and reports. It writes only its own review file and never edits the profile, resume or tracker. As with the morning brief, check the current scheduling options at build time, because it needs the user's own machine to read `~/.sherpa/`.

**morning** (scheduled)
A lightweight daily run of the same scout and rank steps, built to work with nobody watching.
1. Run `jobs.py seen` plus a scout pass over the watchlist and any enabled APIs, so only **new or changed** jobs come through.
2. Apply the hard filters and score the survivors with the `rank` rubric.
3. Write `briefs/<date>.md` and show it as the run's result: the top new jobs (default max 5, and only *Apply now* or strong *Stretch*), anything on the tracker with a follow-up due, and a one-line coverage note (sources checked, anything unreachable).
4. If nothing new clears the bar, say so in one line rather than padding the list.

Rules for scheduled runs:
- **Read, rank and report only.** Never fill forms, never submit, never send messages, and never edit `resume-master.md` or `profile.md`. The resume panel is never run on a schedule.
- **Don't stop to ask questions.** If `profile.md` is missing or incomplete, the brief says "run `/sherpa:setup` first" and ends.
- **Keep it cheap and polite.** Reuse the same rate limits and caching as `scout`, and stop after a fixed number of companies per run (default 30) so a run stays short. The rest are picked up on following days.
- **Watchlist health** (feeds that broke, companies not checked in two weeks) is reported in the weekly review, not in the daily brief.

Schedule preferences live in `profile.md`: days (default weekdays), time (default 8:00 in the user's own time zone), and brief length. Set up the actual schedule with Claude's scheduled-task feature through a small `/sherpa:morning setup` step that creates it for the user. **Check the current scheduling options at build time**: tasks that read `~/.sherpa/` must run on the user's own machine, not in a cloud sandbox that can't see those files.

## 5. The helper scripts

Both print JSON so skills can consume the output.

### `scripts/jobs.py` (Python standard library only)

| Subcommand | Does |
|---|---|
| `probe <careers-url-or-company>` | Detect the ATS from URL patterns or page markers, fetch the public feed, output normalised jobs. |
| `api <name> --query ... --where ...` | Call an optional job API (start with Adzuna) and output normalised jobs. |
| `dedupe` | Merge a list of jobs on company + title + location + URL, keeping the earliest first-seen. |
| `seen` | Compare against `jobs.jsonl` and report only new or changed jobs. |
| `stats <tracker.csv>` | Compute the weekly numbers: counts by stage, source, tier and likelihood band, reply rate, median days to a reply, overdue follow-ups and stale entries. Prints the sample size behind every figure. |
| `gaps` | Count how often each `gaps` phrase appears across `jobs.jsonl`, split by tier. For near-miss jobs, also count how often a gap is the only or main one (the "unlock count"). |

Start with adapters for **Greenhouse, Lever, Ashby and Workable**, which each expose public job feeds. URL patterns live in `reference/ats-endpoints.md`. **Verify each endpoint against current docs when building the adapter**, since public feeds change. Each adapter is a small isolated function, so one breaking doesn't affect the rest. Be polite: identify the tool in the User-Agent, rate-limit requests, cache results for the session, and respect robots.txt and site terms.

### `scripts/resume_io.py` (uses outside tools if installed, with friendly errors if not)

| Subcommand | Does |
|---|---|
| `extract <file>` | Turn a PDF into text. Try `pdftotext` first, then the `pypdf` library. Also accepts `.docx` and `.md`. Output the text and the flags (no text layer, suspected columns or scrambled order, length, missing contact details or links, odd characters). If there is no text layer, say so and suggest OCR (for example `ocrmypdf`) or pasting the text. |
| `verify-quotes <resume-text> <quotes.json>` | Check each quoted line against the resume, ignoring whitespace and line breaks. Report which quotes matched and which did not. |
| `render <resume.md> <out.pdf>` | Export Markdown to a clean single-column PDF through a plain HTML template. Try `weasyprint`, then `pandoc`, then headless Chrome. Standard fonts, real text, no tables or images for layout. |

If none of the rendering tools is installed, say which to install and fall back to handing over the Markdown.

## 6. Build order (one session)

Work straight down the list. Each step names the files it produces. Don't stop for sign-off between steps. Run the checks in section 7 at the end.

1. **Skeleton.** Create the repo layout and `plugin.json`. Stub `README.md`. Confirm the plugin loads locally.
2. **Reference files.** Write `reference/verdicts.md` (verdict scale, calibration rules, shared output format), `reference/ranking-rubric.md`, `reference/ats-endpoints.md` and `reference/voice.md` (the guide's tone, shared by the weekly review and interview prep: candid, warm, concrete, evidence first, honest about small samples).
3. **`resume_io.py`.** Build `extract`, `verify-quotes` and `render`. Try each on a fixture PDF straight away.
4. **`jobs.py`.** Build the normalised schema, `probe` with the four ATS adapters, `dedupe`, `seen`, `stats` and `gaps`. Add the Adzuna adapter behind the optional key. Try one real company per ATS.
5. **Six reviewer agents.** Write the files in `agents/`, each with its persona, focus and the shared rules, and with read-only tools.
6. **`setup` skill.** Profile interview and PDF intake. Test it on a fixture PDF, then on your real resume.
7. **`resume` skill.** The panel flow end to end: extract, layout note, six parallel agents, quote check, merged report, optional re-run. This is the biggest skill, so give it the most care.
8. **`scout` and `rank` skills.** Run them on a sample profile, and confirm `rank` saves `must_have`, `nice_to_have`, `gaps`, score, tier and likelihood.
9. **`adjacent` and `gaps` skills.** `gaps` needs ranked jobs in `jobs.jsonl`, so run `scout` and `rank` first (or use the fixture file). Check the counts against a hand count.
10. **`apply` skill.** Pack and PDF export first, then the assisted form-fill with the approval gate.
11. **`prep` skill.** The prep sheet first, then the mock interview. Test it on a fixture job and the fixture resume.
12. **`pipeline` skill and `tracker.csv`.** Create the tracker with the columns and `history` format from section 3.
13. **`weekly` skill and schedule setup.** Write the skill around `jobs.py stats` and `reference/voice.md` from the earlier steps. Run it by hand on the fixture tracker, then create the schedule.
14. **`morning` skill and schedule setup.** Run it by hand, then create the schedule.
15. **README.** Install steps, what leaves your machine, limits, and the honest caveats about the panel, adjacent roles and weekly insights.
16. **Run the checks** in section 7, fix what fails, and finish.

## 7. Testing (keep it light, all in the same session)

**Fixtures:** three resume PDFs (strong, average, weak) plus one deliberately flawed one (scanned image, or two-column with scrambled order, or keyword-stuffed), about thirty postings already ranked into a fixture `jobs.jsonl` (good fit, stretch, mismatch, suspicious, with `must_have` and `gaps` filled in, including one gap that matches a skill the strong resume shows in different words), and a fixture `tracker.csv` of about twenty applications with mixed outcomes. Generate synthetic ones; use no real people's details.

**Checks:**
- **Panel runs fully:** all six reviewers return, in the required format, without seeing each other's output.
- **Quotes are real:** `verify-quotes` passes for every quote that survives into the report.
- **Verdicts are sensible:** the strong resume scores better on average than the weak one, and the weak one never gets an *Offer*.
- **Stability:** running the panel twice on the same resume gives verdicts within one step for every reviewer.
- **PDF problems caught:** the flawed PDF is flagged by `extract` and picked up by the automated screen.
- **Truthful rewrites:** no rewrite adds a fact that isn't in the resume or confirmed by the user.
- **PDF round trip:** a tailored resume renders to a readable single-column PDF, and extracting it again gives back the same text.
- **Hard filters** drop what they should, and tiers broadly match a hand-labelled answer key.
- **Live smoke test for `jobs.py`:** one real company per ATS. If one breaks, fix that adapter only.
- **Morning brief:** a manual run shows only new jobs. A second run shows none. A scheduled run finishes without prompts and never touches forms, messages or profile files.
- **Apply gate:** form-fill never submits without a yes, and never touches login, CAPTCHA or declaration fields.
- **Adjacent roles:** every suggested role cites at least two real resume lines, has been checked against current postings, and nothing is added to `profile.md` without approval.
- **Skills gap:** counts match a hand count on the fixture `jobs.jsonl`, and the planted "hidden strength" is classified as one.
- **Interview prep:** every story traces back to the resume, missing details are marked *needs info from you*, and the mock interview asks one question at a time.
- **Weekly review:** figures match `jobs.py stats` on the fixture tracker, every insight states its sample size, a run with fewer than 5 applications says "too early to tell", and a scheduled run changes no files except its own review.

## 8. Non-goals for v1

- No scraping behind logins, and no LinkedIn, Seek or Indeed scraping. They are reached only as ordinary web search results.
- No auto-submit, ever.
- No database, server, accounts or dashboard.
- No claims that the panel predicts real hiring decisions.
- No salary negotiation coaching, networking outreach tool or multi-user support in v1. Interview prep is deliberately small: a prep sheet and a short mock interview, not a coaching product.
- Scheduled runs are limited to the morning brief and the weekly review, and only read, analyse and report: no scheduled applying, messaging, resume panel runs or editing of your profile, resume or tracker.

## 9. Risks and how we keep them small

| Risk | Mitigation |
|---|---|
| Reviewers sound alike or flatter | Distinct persona focus, calibration rules in `verdicts.md`, independence (no shared context), and the stability check. |
| Reviewers invent or misquote lines | Word-for-word quoting, then `verify-quotes` drops anything that doesn't match. |
| PDF text comes out garbled | Layout flags, a visual look at page one, the raw-extraction view for the automated screen, and asking the user for text if needed. |
| Six agents is slower and heavier than one | The panel runs on demand only, reviewers run in parallel, and each gets just the material it needs. |
| Public ATS feeds change | One adapter per ATS, a coverage report that shows failures, and a smoke test. |
| Fabricated resume content | The "true facts only, ask when missing" rule in every skill that writes about the user, checked in tests. |
| Form-fill goes wrong | Approval gate before each submit, a pause on anything sensitive, and the pack as a fallback. |
| Site terms and rate limits | Public feeds and official APIs only, rate limiting and caching, and a clear README. |
| Scheduled runs act without supervision | The morning skill is read-and-report only, has a per-run company cap, and treats missing setup as "stop and say so". |
| Scheduled task can't see local files | Check scheduling options during the morning step and require the local machine for runs that read `~/.sherpa/`. |
| Weekly insights over-read tiny samples | `jobs.py stats` does the maths in code, every insight states its sample size, and below the minimum (default 5 applications) the review says "too early to tell". |
| Adjacent roles are wishful thinking | Each must cite resume evidence, be checked against current postings, carry an honest likelihood band, and wait for the user's approval before joining the profile. |
| Skills-gap numbers are fuzzy | `rank` saves gaps as short, consistent phrases and `jobs.py gaps` counts them in code. |
| Interview stories get embellished | Stories use only resume facts or facts the user confirmed, with blanks marked *needs info from you*, and the mock interview gives candid feedback rather than praise. |
| Scope creep | The non-goals list above, and the build order. |

## 10. Definition of done

- Every item in section 7 passes, or any exception is written down in the README under "Known limits".
- A new user can install Sherpa, run `/sherpa:setup` with a PDF resume, run `/sherpa:resume` to get the six-reviewer report, run `/sherpa:scout` to get a ranked list, find adjacent roles and skills gaps, prepare an application pack with a PDF and an interview prep sheet, and schedule the morning brief and weekly review, using the README alone.
