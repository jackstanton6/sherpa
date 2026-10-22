# Sherpa: an honest job-search toolkit for Claude Code

*Sherpa is the Job Finders Toolkit. Commands look like `/sherpa:scout`.*

**White paper, v0.3 draft, 22 October 2026**

## 1. The problem

Job searching is slow, noisy and demoralising, and most tools make it worse.

- **Job boards are crowded and stale.** The same postings appear everywhere, many are already filled, and some were never real ("ghost jobs").
- **The best roles are often elsewhere.** Many employers post first, or only, on their own careers page. Boards pick them up late or never.
- **Feedback is flattering or absent.** Resume tools tend to hand out inflated scores or generic tips. Nobody tells you plainly how different readers would react, or that a role is a long shot.
- **Applying is repetitive.** The same details get retyped into dozens of forms, and "auto-apply" tools spam employers with low-quality applications.

## 2. Thesis

A search assistant should behave like a smart, candid guide who knows the terrain. It does the legwork, says what it really thinks, and spends your effort where it is most likely to pay off.

Sherpa is a Claude Code plugin that guides the whole climb: **know you, test your resume, find jobs (including hidden ones and roles you hadn't thought of), rank them honestly, close your skills gaps, prepare applications and interviews, and review your progress each week.** A scheduled morning brief keeps the search going, and a weekly review keeps you honest about how it is really going.

## 3. Principles

1. **Honest over flattering.** Verdicts are calibrated, gaps are named, and long shots are labelled as long shots.
2. **Realistic over exhaustive.** Ten well-ranked roles beat two hundred unranked ones. Each result comes with reasons and evidence.
3. **Never invent facts about you.** Claude may rephrase, reorder and emphasise what is true. If it needs a fact it doesn't have, it asks.
4. **You press submit.** Claude prepares and can fill forms, but it stops for your explicit approval before every submission.
5. **Simple and local.** Plain files on your machine, two small helper scripts, and no servers or accounts.
6. **Respect the web.** It uses public career pages, public ATS feeds and official APIs. It does not scrape behind logins, bypass CAPTCHAs or hammer sites.

## 4. What it does

| Capability | What you get |
|---|---|
| **Setup** | A short interview produces a profile: target roles, location or commute limit, remote preference, salary floor, work rights, deal-breakers and target companies. You hand over your resume as a **PDF** (or Word or Markdown) and Sherpa keeps a clean text master. |
| **Resume panel** | Your resume is judged by **six independent reviewers**, each seeing it through a different lens (see section 5). Each gives a verdict, quotes your strongest and weakest lines, and suggests fixes. You get one merged report with the fixes ranked. |
| **Scout** | A search across web results, optional job APIs, and company career pages. It reads public feeds from the common applicant-tracking systems (ATS), which turns up roles that never reach LinkedIn. |
| **Rank** | Hard filters first, then a 100-point fit score with reasons, gaps, a legitimacy check, and a tier: *Apply now*, *Stretch* or *Skip*. |
| **Adjacent roles** | Roles you haven't searched for but your experience supports, grouped as *close step*, *pivot* or *long reach*. Each one cites your own resume as evidence, lists the alternative titles to search, and gets an honest likelihood band. |
| **Skills gap** | Across the jobs Sherpa has ranked, which missing skills block the most near-miss roles, whether each is a real gap or a strength your resume just doesn't show, and the cheapest honest way to close it. |
| **Apply** | A per-job pack with a tailored resume (exported as a **PDF**), a cover letter, draft answers to the application questions, and an optional approval-gated browser form-fill. |
| **Interview prep** | A small prep sheet per job: what the role cares about, a quick company brief, likely questions (including awkward ones about your weak spots), and a story bank built only from your true experience. Optionally, a short mock interview with candid feedback. |
| **Pipeline** | A simple tracker of what you applied to, when to follow up, and what happened. |
| **Weekly review** | A short look back written like a seasoned guide: what happened, what the numbers do and don't say, one thing to stop, start and keep, a realistic plan for next week, and a pace check. It can run on a schedule and only reads and reports. |
| **Morning brief** | An optional scheduled run each morning that checks for *new* roles, ranks them, and gives you a short brief of the best few plus any follow-ups due. It only reads and reports. It never applies or sends anything. |

## 5. The resume panel

Most resume feedback comes from a single viewpoint. Real resumes are judged by very different readers who want different things. Sherpa runs six separate reviewers, in parallel, each unaware of the others.

| Reviewer | The question they are really asking |
|---|---|
| **Automated hiring screen** (strict) | Does this parse cleanly, and does it clear the keyword and requirement filters most companies run? It reads the raw text extracted from the PDF, exactly as software would. |
| **Hiring manager** | Can this person do the job, and would they ease my workload? |
| **Potential coworker** | Would I want to work with this person every day? |
| **CEO** | In thirty seconds, does this person show impact, judgement and trajectory worth the company's money? |
| **Rival applicant** | Applying for the same job, where is this resume weaker than a strong competitor's? |
| **Experienced recruiter** | Is the story coherent, are there red flags, and would I put my name behind submitting this? |

Each reviewer returns one verdict on a five-step scale, from best to worst:

**Offer** (exceptional, fast-track) · **Interview** · **Consider** (the maybe pile) · **Pass** · **Burn** (actively damaging: errors, dishonesty signals or serious unprofessionalism).

Reviewers are told to be calibrated, not kind. For a specific job, most resumes land at *Consider* or *Pass*, and *Offer* should be rare.

Each reviewer also quotes the **strongest** and **weakest** lines straight from the resume and suggests fixes. Sherpa checks that every quoted line really appears in the resume and drops any that don't. The final report shows the verdict grid, where reviewers agree and disagree, which lines several reviewers flagged, and a ranked list of fixes. After you fix things, the panel can be re-run to show how the verdicts changed.

**An honest caveat:** the reviewers are simulated perspectives produced by Claude, not real recruiters or real hiring data. They are a structured way to catch problems you would otherwise miss, not a prediction of any employer's decision.

## 6. The guide features

Four features turn Sherpa from a search tool into a guide.

**Adjacent roles.** Sherpa reads what your resume actually shows and proposes roles you haven't searched for. They are grouped as a *close step* (same skills, different title or industry), a *pivot* (one or two real gaps) or a *long reach*. Each cites the resume lines that support it, lists the other titles employers use for it, and carries an honest likelihood band. Sherpa checks that real postings exist before suggesting a role, and adds nothing to your search targets without your say-so.

**Skills gap.** Sherpa looks across the jobs it has already ranked and counts which missing skills hold back the most near-miss roles. It separates three cases: a *real gap*, a *hidden strength* (something you probably have but your resume doesn't show, which is a cheap fix), and *not worth chasing*. For the top gaps it names the cheapest honest way to close them and says plainly whether the effort is worth it.

**Interview prep.** Deliberately small. For a chosen job you get one prep sheet: the role in five lines, a short company brief, about ten likely questions (including awkward ones aimed at your weak spots), and a story bank of four or five stories drawn only from your true experience, with blanks marked where Sherpa needs a detail from you. An optional mock interview asks one question at a time and gives short, candid feedback.

**Weekly review.** Sherpa reads your tracker and the week's results and writes a short review in the voice of a guide who has walked this route before. It covers the week at a glance, two or three insights from the data, one thing to stop, start and keep, a plan for next week with a realistic cap on applications, and a pace check so you don't burn out. It also checks whether Sherpa's own rankings are actually predicting replies. The numbers are computed by code, and every insight states how many applications it rests on.

## 7. How it works

Sherpa is mostly **instructions plus two small helper scripts**, not a large system.

- **Skills** (Markdown files Claude follows) define each step. They hold the rubrics, the questions to ask, and the rules about honesty and approval.
- **Six small reviewer agents** (one per panel member) are restricted to reading the material they are given. They have no web access and can't write files, which keeps them independent and safe.
- **A job helper script** does the mechanical job-search work: detecting which ATS a company uses, fetching its public job feed, calling optional job APIs, normalising every job into one schema, and removing duplicates.
- **A resume helper script** turns a PDF into text (and reports problems such as a scanned image or a suspect layout), checks the quoted lines, and exports a tailored resume back to PDF.
- **Claude does the judgement:** reviewing, fit reasoning, tailoring and spotting problems in a posting.
- **Your data lives in a local folder** (profile, resume, watchlist, seen jobs, reviews, tracker). Nothing is sent anywhere except job-search queries to the sources you enable. Search queries carry keywords and location, not your resume.

**PDF handling.** Sherpa reads your PDF, extracts the text, and warns you if the PDF would trip up real screening software (scanned pages, multiple columns that scramble the reading order, text inside images, or missing contact details). Tailored resumes are exported as single-column, real-text PDFs with standard fonts, because those are the safest for screening software.

**How "hidden" jobs are found.** The scout builds a list of target companies from your profile and web search. It finds each company's careers page, detects the ATS behind it (Greenhouse, Lever, Ashby, Workable and similar, which expose public job feeds), and pulls the live listings. It filters them against your profile and marks each job's source, so you can see which ones were *not* on the big boards. Pages without a public feed are read directly. Companies that need a login or block automated access are skipped, and the report says so.

## 8. Honesty and safety, by design

- **Calibrated verdicts.** Every verdict is backed by quoted evidence from the resume or posting. Job likelihood is shown as bands (*strong / possible / long shot*), never a fake percentage.
- **Independent reviewers.** Panel members never see each other's opinions, so one strong opinion can't sway the rest, and disagreement is shown, not smoothed over.
- **Legitimacy signals.** Posting age, repeated reposts, vague text and missing details are flagged as *signals, not verdicts*.
- **Truthful tailoring.** No made-up skills, titles, dates or metrics. Any suggested wording that needs a number you haven't given becomes a question for you.
- **Small-sample humility.** Weekly insights always state how many applications they rest on. With too few, Sherpa says "too early to tell" instead of inventing a trend.
- **Interview stories are yours.** Prep material uses only your real experience. Missing details become questions, and awkward gaps are framed truthfully, never spun into something untrue.
- **Human in the loop.** Form-fill pauses on a summary of exactly what will be sent. You log in yourself, you handle CAPTCHAs, and demographic or legal declarations are left for you. Your tailored PDF is attached only after you approve.
- **Unattended runs stay read-only.** The scheduled morning brief and weekly review can search, rank, analyse and report, but they cannot fill forms, submit, send messages or change your profile and resume. If setup is incomplete, it says so and stops rather than guessing. It reports only what is new, and says plainly when there is nothing worth your time.
- **Privacy.** Local files, minimal outbound data, and a clear README on what leaves your machine. Resume text is shared with Claude to do the review, and with nothing else.

## 9. Measuring success

- A reader can reproduce why a job got its tier, and why a reviewer gave a verdict, from the evidence shown.
- Re-running the panel on the same resume gives verdicts within one step of each other for every reviewer.
- Every quoted line in a report exists in the resume, and no rewrite contains a fabricated fact.
- A deliberately flawed test PDF (scanned, two-column, keyword-stuffed) is caught by the automated screen and the layout warnings.
- In a trial, hidden-job discovery surfaces at least some relevant roles not found on the major boards.
- Preparing an application takes minutes rather than an hour, and you never lose control of submission.
- Every adjacent role cites real lines from the resume and is backed by real current postings.
- The skills-gap counts match a hand count of the saved jobs.
- Every interview story traces back to the resume, and missing details are asked for, not invented.
- Every weekly insight states its sample size, and the figures match what the code computed from the tracker.

## 10. Limits and risks

- **The panel is simulated.** It is a lens, not a hiring outcome, and the report says so.
- **PDF extraction is imperfect.** Unusual designs can garble text. Sherpa flags suspected problems and falls back to asking you for the text.
- **Coverage is partial.** Some employers use ATS platforms without public feeds, and some sites block automation. Sherpa reports gaps rather than hiding them.
- **Public feed formats can change.** The helper script isolates this so a break affects one adapter, not the whole plugin.
- **Job data can be stale or fake.** Freshness and legitimacy checks reduce this but cannot remove it.
- **Form-fill is fragile.** Application forms vary, so the fallback is always the prepared pack for you to paste.
- **Adjacent roles are possibilities, not promises.** Market signals from web search are rough, and a pivot can still be a long shot. Sherpa says so.
- **Weekly insights rest on small numbers.** A job search produces few data points, so patterns are hints. Sherpa flags thin evidence rather than overstating it.
- **Scores are judgement, not science.** They are meant to guide your attention, not to predict outcomes.

## 11. Scope for the first release

Everything above ships together in one build: setup, the resume panel, scout, rank, adjacent roles, skills gap, apply pack, assisted form-fill, interview prep, tracker, the scheduled morning brief and the weekly review.
Not in this release: salary negotiation coaching, a networking tool and multi-user features.
