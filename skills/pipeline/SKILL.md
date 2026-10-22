---
description: Show and update the user's job application tracker. Lists applications by stage, flags overdue follow-ups, records stage changes (screen, interview, offer, rejected, withdrawn, no-reply) with dates, and drafts short follow-up messages. Use when the user asks about their applications, reports news from an employer, or wants to follow up.
argument-hint: "[job id] [new stage]"
---

# Pipeline

A simple tracker of what the user applied to, what happened, and what to chase.

**Scripts.** `JOBS` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jobs.py"` (use `python` if `python3` doesn't work). All tracker changes go through `JOBS track`. **Never edit `tracker.csv` by hand.**

Stages: `applied`, `screen`, `interview`, `offer`, `rejected`, `withdrawn`, `no-reply`.

## Show

Run `JOBS track list`. Show the active applications (applied, screen, interview) grouped by stage, oldest first, with days since the last update. Put **overdue follow-ups** at the top (the `overdue` list). Show closed ones (offer, rejected, withdrawn, no-reply) as a one-line count, unless the user asks for them.

## Update

When the user reports news ("Acme rejected me", "I've got a screen with Northwind on Tuesday"):

- Find the job id from the list. If it's ambiguous, ask.
- `JOBS track update <job_id> --stage <stage> [--date YYYY-MM-DD] [--follow-up YYYY-MM-DD] [--note "..."]`. The date is when it happened (default today). Set a follow-up when there is a next step to chase (for example the day after an interview, or a week after a screen).
- If they applied somewhere outside Sherpa, add it: `JOBS track add --job-id <id from normalize> ` (normalize the posting first), or `--company`, `--role` and `--source board|direct|referral` with a made-up id such as `manual:acme-analyst`.
- Confirm the change in one line.

## Follow-up drafts

On request, draft a short follow-up (about 60 to 100 words): polite, specific (role, date applied or interviewed, one line on fit from the resume), and with no pressure tactics. Show it for the user to send themselves. **Sherpa never sends messages.** After they send it, offer to push the follow-up date out a week with `--follow-up`.

## Gentle honesty

If several applications have gone 14+ days with no update, suggest marking clearly dead ones as `no-reply`, so the weekly numbers stay true. Do it only with the user's say-so.
