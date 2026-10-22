---
description: Prepare for a job interview with Sherpa. Writes a short prep sheet with the role in five lines, a company brief, about ten likely questions (including awkward ones aimed at the user's weak spots), a story bank drawn only from their real experience, and truthful framings for gaps. Optionally runs a short mock interview with candid feedback. Use when the user has an interview coming up or wants to practise.
argument-hint: "<job id or company> [mock]"
---

# Interview prep

Deliberately small: one prep sheet and an optional short mock. This is not a coaching product.

**Scripts.** `JOBS` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jobs.py"` (use `python` if `python3` doesn't work). Voice: `${CLAUDE_PLUGIN_ROOT}/reference/voice.md`.

## Inputs

- The job: `JOBS show <id>`, or a pasted posting or URL (run new ones through `JOBS normalize`).
- `HOME/resume-master.md` (required). If it's missing, say "Run `/sherpa:setup` first".
- The latest `HOME/reviews/*-resume.md`, if any, for the lines the panel flagged as weak.
- The job's `gaps` from jobs.jsonl, if ranked.

## The prep sheet

Write `HOME/applications/<company>-<role>/interview-prep.md` (create the folder if needed). One or two pages:

1. **The role in five lines.** What they really care about, read from the posting (the first duties and the must-haves), not the boilerplate.
2. **Company brief.** Three to six lines from a quick web search: what they do, size or stage, recent news, and anything relevant to the team. Cite sources as links. If information is thin, say so rather than padding.
3. **Likely questions (about ten):**
   - four behavioural (tied to the role's real needs),
   - three role-specific or technical,
   - two aimed squarely at the user's **weak spots**, built from the job's gaps and the panel's weak lines (for example "You haven't used dbt. How would you get up to speed?"),
   - plus two or three good **questions for the user to ask them**.
4. **Story bank (four or five stories).** Each drawn **only** from `resume-master.md` or facts the user has confirmed. Format: **Situation → Action → Result**, and which questions it answers. Where a number or detail is missing, write *needs info from you:* and the question. Never fill the blank yourself.
5. **Awkward questions.** Truthful framings for CV gaps, a missing skill, a short stint or a career change. Frame honestly ("I took eight months to care for a family member, and kept my SQL current with…" only if that is true). **Never turn a fact into something untrue.** If you don't know the facts behind a gap, ask.
6. **Pay.** If pay might come up, run `JOBS pay <title keyword>` and state the range with its sample: "Median stated range $95-118K across 7 postings." If there is no data, say so.

Then ask the user for the *needs info from you* items and update the sheet with their answers.

## Mock interview (optional, or when `$ARGUMENTS` contains `mock`)

You play the interviewer, in chat, with one voice and no subagents.

- Ask **one question at a time**, up to five, mixing the sheet's questions (at least one weak-spot question).
- After each answer, give **short, candid** feedback: **clarity** (was the point clear?), **evidence** (was there a concrete result?), and **length** (too long, too short or about right), plus **one fix**. Praise only what earned it.
- At the end, name **the two things to improve most**, and add them to the bottom of `interview-prep.md` under "Mock notes".
