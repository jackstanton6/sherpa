---
description: Run Sherpa's six-reviewer resume panel. An automated screen, hiring manager, coworker, CEO, rival applicant and recruiter each judge the resume independently and in parallel, then Sherpa merges their verdicts, checks every quote and ranks the fixes. Use when the user wants resume feedback, a resume review or score, or wants to compare before and after edits.
argument-hint: "[resume path] [job URL or 'rerun']"
---

# The resume panel

Six independent reviewers judge the resume through different lenses, then you merge their views into one honest report. This is Sherpa's most important skill, so be careful at every step.

**Scripts.** `JOBS` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jobs.py"` and `RESUME` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/resume_io.py"` (use `python` if `python3` doesn't work).

**Never run this skill unattended or on a schedule.**

## 0. Inputs

- Run `JOBS status` to find `HOME`.
- **Resume:** a path in `$ARGUMENTS`, otherwise `HOME/resume-original.pdf` (or `.docx` / `.md`). Prefer the PDF, because that is what employers' software reads. If the user has edited `resume-master.md` since, and there is no newer PDF, use the master and say so.
- **Target:** a job posting (a URL, pasted text, or a job id that `JOBS show <id>` returns), or else the target roles from `profile.md`. If neither exists, ask once. A specific posting gives sharper verdicts. Say which target you used.
- If the user said `rerun`, find the latest `HOME/reviews/*-resume.md` to compare against at the end.

## 1. Extract

Run `RESUME extract <resume>`. Keep `text` (the **raw extraction**) and `flags`.

If `no_text_layer` is flagged, stop. Tell the user that screening software sees a blank page, and offer OCR (`ocrmypdf`) or pasting the text. Do not run the panel on an empty resume.

## 2. Look at page one

If the resume is a PDF, read its first page yourself (Read the PDF with `pages: "1"`) to spot layout problems the text hides: columns, sidebars, icons, photos, skill bars, text in images, tiny fonts, heavy colour. Write a **layout note** of at most five short lines. If it isn't a PDF, the layout note is "Not a PDF; layout not assessed."

## 3. Launch the six reviewers in parallel, in one step

Send **all six Agent calls in a single message** so they run in parallel and none sees another's output. The `subagent_type` values are:

`sherpa:ats-screen`, `sherpa:hiring-manager`, `sherpa:coworker`, `sherpa:ceo`, `sherpa:rival`, `sherpa:recruiter`

Give each one **only** this material, and nothing about the user's hopes or your opinions:

```
TARGET
<the posting text, or "Target roles: …, seniority: …, location: …" from the profile>

RESUME TEXT
<<<
<the text>
>>>

EXTRACTOR FLAGS
<flags as short lines, or "none">

LAYOUT NOTE
<the layout note>   ← omit this block for ats-screen

Return only the JSON object described in reference/verdicts.md.
```

- `ats-screen` gets the **raw extraction exactly as returned**, with no clean-up, plus the flags. It sees what a parser sees.
- The other five get the same raw text plus the layout note. If the raw text is badly scrambled, give the five human reviewers `resume-master.md` instead and say so in their prompt, because people see the visual page, not the parse.

## 4. Check every quote

1. Parse the six JSON replies. If one is malformed or missing, re-run **only that reviewer** once. If it fails again, report the panel as five reviewers and say so.
2. Write all six replies, as a JSON array, to `HOME/reviews/.panel-<date>.json`.
3. Run `RESUME verify-quotes <the resume file the reviewers saw> HOME/reviews/.panel-<date>.json`. For a scrambled PDF where humans got the master, check those reviewers against `resume-master.md`.
4. **Drop every unmatched quote** and the point made with it. List the dropped quotes in the report's footnote. Never repair a quote into one that matches.

## 5. Merge into the report

Write `HOME/reviews/<YYYY-MM-DD>-resume.md` (add `-2`, `-3` and so on if one already exists) with these sections, in this order:

1. **Verdict grid.** A table with one row per reviewer: reviewer, verdict, confidence, and their one-line reason.
2. **Panel headline.** For example "2 Interview · 3 Consider · 1 Pass", then one or two plain sentences on what that means. **Don't average verdicts into a score.** There is no numeric score.
3. **Agreement and disagreement.** Where they agree, and where they split. Explain splits, because they are informative. For example, a coworker who likes you and a screen that rejects you means a *formatting* fix, not a content fix.
4. **Lines that matter.** *Fix these:* lines flagged weak by two or more reviewers. *Protect these:* lines flagged strong by two or more. Match lines by their normalised text. If no line was flagged twice, show the most-cited ones and say so.
5. **Ranked fixes.** Merge similar fixes. Priority = number of reviewers who raised it × severity (high 3, medium 2, low 1). Show the top five to eight, each with **before → after** wording that uses only true facts. Where a fix needs a number or detail, show the placeholder and the question: *needs info from you: how many stores used the forecast?*
6. **Extractor flags**, in plain English, if any.
7. **Caveat.** Close with: "These are simulated perspectives produced by Claude, not real recruiters or hiring data. Use them to catch problems, not to predict any employer's decision."
8. Footnote: the target used, the resume file, the date, and any dropped quotes.

Show the report to the user (the grid, the headline, the lines that matter and the top fixes inline, then point to the file for the rest).

## 6. Before and after (re-runs)

If there is an earlier report, add a **Changes since <date>** table: reviewer, old verdict → new verdict, with a one-line why. Moving one step either way between runs is normal noise. Call out only moves of two or more steps, or consistent moves across several reviewers.

## 7. Offer next steps

Offer, and wait for the user to choose:

- **Draft truthful rewrites** of the weakest lines. Ask for every missing number or detail. Never invent one. Rephrasing, reordering and cutting are fine. Adding skills, titles, dates, employers or metrics they haven't confirmed is not.
- **Update `resume-master.md`** with the rewrites they approve. Show a diff of the change first.
- **Export a PDF:** write the updated Markdown, then `RESUME render HOME/resume-master.md HOME/resume-master.pdf`. If no renderer is found, give the install hint the script returns and offer the Markdown instead.
- **Re-run the panel** on the new version to show what changed.
