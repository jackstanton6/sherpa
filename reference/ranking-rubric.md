# Ranking rubric

Used by `/sherpa:rank`, and by `/sherpa:morning` when it scores new jobs.

## 1. Hard filters (applied first)

A job that fails any hard filter is **Skip**, with `filter_reason` set to a short phrase. It is not scored further.

| Filter | Fails when |
|---|---|
| Location / commute | Onsite or hybrid and outside the commute limit or listed locations in `profile.md`. Remote roles restricted to a region the user can't work from also fail. |
| Work rights | The posting requires a right to work, citizenship or clearance the profile doesn't have, or says no sponsorship and the user needs it. |
| Salary floor | A **stated** maximum is below the user's floor (same currency or a clear conversion). An unstated salary never fails this filter. |
| Deal-breakers | The company, industry or role matches a deal-breaker in the profile. |
| Work mode | The profile says remote-only and the job is onsite or hybrid (or the reverse, if stated). |

If the posting is unclear on a filter, the job **passes** and the doubt goes into `legitimacy` or `gaps` as a note. Don't drop jobs on guesses.

## 2. Fit score (100 points)

| Part | Points | What earns them |
|---|---|---|
| Skills match | 30 | Share of the posting's must-haves the resume clearly shows. Nice-to-haves add a little. Use the resume, not the profile's wishes. |
| Seniority and experience | 20 | Years and level match the posting. A one-level stretch scores about half. Two levels or more scores near zero. |
| Role and preference | 15 | The title and duties match the profile's target roles and industries. |
| Location and work mode | 10 | Matches the stated preference (remote, hybrid or onsite) and location. |
| Compensation vs target | 10 | Stated range meets or beats the floor: 10. Unstated: 5. Just under the floor but negotiable: 3. |
| Freshness and legitimacy | 10 | Starts at 10. Subtract for each legitimacy signal (below). |
| Company signals | 5 | The company is on the profile's target list, or in a target industry, or shows growth. |

## 3. Tiers and likelihood

| Tier | Rule of thumb |
|---|---|
| **Apply now** | Score 70 or more, and no must-have gap that the resume can't address. |
| **Stretch** | Score 50 to 69, or 70+ with one real must-have gap. |
| **Skip** | Score under 50, or failed a hard filter. |

Keep the *Apply now* list to about ten. If more qualify, keep the ten best and move the rest to *Stretch* with the note "cap".

**Likelihood band** (never a percentage): *strong* (clear match, few gaps), *possible* (decent match, one or two gaps or heavy competition), *long shot* (real gaps, big stretch, or a very competitive employer). Likelihood is about getting a reply, which is different from fit.

## 4. Legitimacy signals (signals, not verdicts)

Flag any that apply, and subtract about 3 points each from freshness/legitimacy:

- Posted more than 60 days ago.
- Reposted repeatedly (same title and company seen with new dates).
- Vague duties, or a description that could fit any company.
- No team, manager or location detail.
- Listed on job boards but absent from the company's own careers page.
- Asks for payment, unusual personal data, or contact through a personal messaging app (this one is serious: tell the user plainly).

## 5. Gap phrases

`gaps` entries must be short, consistent, lowercase phrases so they can be counted across jobs:

- Good: `sql`, `people management`, `aws certification`, `python`, `stakeholder management`, `b2b saas`, `5+ years experience`.
- Bad: `Needs more SQL experience`, `SQL (advanced)`, `Doesn't have AWS cert`.

Before inventing a new phrase, run `jobs.py gaps` and reuse an existing phrase if one fits. List gaps **most serious first**: the first gap is treated as the "main" gap for unlock counts.

## 6. Output per job

Tier, score, three reasons for (each tied to a resume line or posting line), up to three gaps, legitimacy signals, likelihood band, and the source, marked **direct** when it came from a company's own careers page or ATS feed.
