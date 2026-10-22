---
description: Write Sherpa's weekly review of the user's job search, like a seasoned guide looking back over the week. Covers the numbers, what they do and don't say (with sample sizes), one thing to stop, start and keep, a realistic plan for next week, and a pace check. Can be scheduled. Use when the user asks how their search is going, wants a weekly recap, or says "weekly setup" to schedule it.
argument-hint: "[setup | scheduled]"
---

# Weekly review

A short look back, written like a guide who has walked this route before. It reads in about three minutes.

**Scripts.** `JOBS` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jobs.py"` (use `python` if `python3` doesn't work). **Voice:** read `${CLAUDE_PLUGIN_ROOT}/reference/voice.md` first and follow it.

## Mode

- `$ARGUMENTS` contains **`setup`**: go to "Schedule setup" at the end.
- `$ARGUMENTS` contains **`scheduled`**: an **unattended run**. Don't ask questions. Change no files except the review itself (the only folder you may write to is `HOME/weekly/`). Don't run `JOBS track` updates, `JOBS watch add` or `JOBS schedule` (they are blocked anyway). Only single-line `python …` commands are permitted: no PowerShell, heredocs or temp files.
- Otherwise: the user is present.

## 1. Check setup

Run `JOBS status`. If `profile.md` is missing, write "Run `/sherpa:setup` first." (as the review file's whole content, if unattended) and stop.

## 2. Catch up the tracker (present mode only)

Ask: **"Any replies, interviews or rejections I haven't logged?"** Record what they tell you with `JOBS track update …`, one call per change. In scheduled mode, skip this. Instead, the review notes how many applications have gone 14+ days without an update and says they need updating.

## 3. Numbers from code

Run `JOBS stats` (it reads `HOME/tracker.csv`). **Every figure in the review comes from this output. Never do arithmetic yourself.** Every group carries `n` and `too_early` (fewer than 5). Also read:

- `JOBS gaps` (top two gaps by unlock),
- `JOBS watch list` (for watchlist health),
- this week's `HOME/briefs/*.md` (what the morning brief surfaced),
- the latest `HOME/reviews/*-resume.md` (the verdict headline only),
- the best unapplied *Apply now* jobs: from `HOME/jobs.jsonl`, jobs with tier "Apply now" whose id isn't in the tracker (read the file, don't calculate scores).

## 4. Write the review

Write `HOME/weekly/<week from stats, e.g. 2026-W43>.md`:

### The week at a glance
Three or four lines of plain numbers: applications this week (and by tier), total so far, replies, interviews, offers, follow-ups due.

### What the trail is telling you
**Two or three insights, each stating its sample size.** Look for:
- Which sources get replies (`by_source`): direct vs board.
- Whether the *strong* likelihood band really predicts replies and interviews better than *possible* and *long shot* (`by_likelihood`). This checks whether **Sherpa's own rankings are working**. Say so plainly if they aren't.
- Whether too much effort is going to long shots or Skips (`by_tier`, `this_week.by_tier`).
- Where applications stall (`funnel`): no reply, screen, or interview.
- Time to reply (`days_to_reply`).

For any group with `too_early: true`, write **"too early to tell"** with the count, never a trend. With fewer than 5 applications in total, the whole section is "Too early to tell: N applications so far. Patterns need at least 5." Patterns are hints, not laws.

### Stop, start, keep
One of each, concrete, tied to the evidence above.

### The route ahead
Three to five actions for next week, in this order: follow-ups due (named), the best *Apply now* jobs not yet applied to (named, with ids), one gap to start closing (from `gaps`), and one adjacent role to try (from the latest `HOME/adjacent/` report, if any). Include a **weekly application cap**: the profile's `Weekly application cap`, or 8 to 10 by default. Quality beats volume.

### Pace check
Two or three lines. A short, kind word on **overload** (many applications, a run of rejections, no rest) or **drift** (nothing sent). Encourage a break when it's earned. A guide's word, not therapy.

### Watchlist health
Feeds that broke (`broken`) and companies not checked in 14 days. One line if all is well.

Footer: "Figures from `jobs.py stats` on N tracked applications, <date>."

## 5. Show it

Show the review (the whole thing; it's short). In scheduled mode, the file is the output, so end after writing it.

## Schedule setup (`/sherpa:weekly setup`)

1. Read the `Weekly day` and `Weekly time` in `profile.md` (defaults: Fri, 16:30). Confirm them with the user, and update `profile.md` if they want something different.
2. Run `JOBS schedule weekly`. It writes a small wrapper script in `HOME/schedule/` and prints the command that would register it with the operating system's scheduler (Task Scheduler on Windows, cron on macOS and Linux). Nothing is installed yet.
3. Explain plainly: it runs `claude -p "/sherpa:weekly scheduled"` on **this computer**, in its local time, while the user is logged in. Cloud schedules can't see `HOME`. The run is **read-and-report only**: it is limited to reading files, web search, the helper scripts, and writing inside `HOME/weekly/`. Everything else (other file edits, PowerShell, the browser, subagents) is denied, and `SHERPA_READONLY=1` blocks tracker changes. Show the `allowed_tools`.
4. Ask for a yes. On yes, run `JOBS schedule weekly --install` and report the result. To undo: `JOBS schedule weekly --remove`.
