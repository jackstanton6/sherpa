---
description: Show which missing skills are holding back the most near-miss jobs, using counts across all jobs Sherpa has ranked. Separates real gaps from hidden strengths the resume doesn't show and gaps not worth chasing, and names the cheapest honest way to close each. Use when the user asks what to learn, what's holding them back, or how to move more jobs into Apply now.
---

# Skills gap

Find the few gaps that would unlock the most jobs, and the cheap fixes hiding in plain sight.

**Scripts.** `JOBS` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jobs.py"` (use `python` if `python3` doesn't work). Tone: `${CLAUDE_PLUGIN_ROOT}/reference/voice.md`.

## 1. Get the numbers from code

Run `JOBS gaps`. **Every count in your report comes from this output. Never count by hand or estimate.**

- If `enough_data` is false (fewer than 10 ranked jobs), say "Run `/sherpa:scout` first. I need at least 10 ranked jobs to see a pattern (I have N)." and stop.
- Terms: **near-miss jobs** are *Stretch* jobs plus *Skip* jobs that failed on fit, not on a hard filter. A gap's **unlock** count is how many near-miss jobs list it as their main (first) gap. `only_gap` is how many have it as their only gap. `as_must_have` shows how often it is required rather than nice to have.

## 2. Sort the top gaps

Take the top gaps by unlock count (about eight). Read `resume-master.md` and put each into one of three kinds:

- **Hidden strength:** the user probably has it, but the resume doesn't show it in the employer's terms. For example, the gap is `stakeholder management` and the resume says "Partnered with finance and operations leaders to set quarterly reporting priorities". Quote the line that suggests it. **Ask the user** whether it's true. If yes, it becomes a resume fix (reword using their true facts), not a learning task. Cheapest win of all.
- **Real gap:** nothing on the page suggests they have it.
- **Not worth chasing:** it appears rarely (unlock of 1 or less and seldom a must-have), or only as a nice-to-have, or the effort is out of proportion to what it unlocks.

## 3. For the top five (hidden strengths and real gaps)

- Unlock count and tier mix (from the numbers).
- The **cheapest honest way to close it**: a resume edit (for hidden strengths), a small project, a short course, or a certification. Prefer free and small. Don't recommend an expensive credential unless the data shows it is a frequent must-have (`as_must_have` high).
- An **effort band**: days, weeks or months.
- A candid **worth it?**: yes, maybe or no, in one line.

## 4. Write the report

Write `HOME/gaps/<YYYY-MM-DD>.md`. Open with one paragraph like: **"Close these two gaps and up to N roles move up a tier."** N is the sum of their unlock counts. Say "up to", because some jobs share gaps. Then give the table of top gaps with their kind, the details from step 3, and the "not worth chasing" list with a reason each. Close with the sample note: "Based on N ranked jobs (M near-misses)."

Show the opening paragraph and the top five. Then ask about each hidden strength, and offer to draft the truthful resume wording for any the user confirms. Those edits go through the same rules as `/sherpa:resume`: true facts only, and the user approves the change before `resume-master.md` is updated.
