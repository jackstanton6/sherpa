---
description: Suggest adjacent roles the user hasn't searched for but their real experience supports, grouped as close step, pivot or long reach. Each cites resume lines as evidence, lists alternative job titles to search, and is checked against real current postings. Use when the user asks what else they could apply for, is open to a change of direction, or their search is coming up thin.
---

# Adjacent roles

Find roles the user hasn't thought of, honestly. Every idea must come from evidence on the page, not flattery.

**Scripts.** `JOBS` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/jobs.py"` (use `python` if `python3` doesn't work). Tone: `${CLAUDE_PLUGIN_ROOT}/reference/voice.md`.

## Inputs

Run `JOBS status`. You need `resume-master.md` and `profile.md`. If either is missing, say "Run `/sherpa:setup` first" and stop.

## 1. What the resume actually shows

List the transferable evidence: skills, tools, the kinds of problems solved, domains, and strengths that carry over (for example forecasting, stakeholder reporting, process automation). Tie **each item to a resume line**, quoted word for word.

## 2. Propose 8 to 12 roles not already in the profile's target roles

Use three groups, with **at most four in each**. Skip an empty group rather than padding it:

- **Close step:** same core skills, different title or industry.
- **Pivot:** needs one or two real gaps closed.
- **Long reach:** a genuine stretch, labelled honestly.

## 3. For each role

- **Why it fits:** two resume lines, quoted word for word.
- **Search terms:** the other titles employers use for it.
- **Likely gaps:** as short phrases.
- **Likelihood:** *strong*, *possible* or *long shot*.

## 4. Check against real postings

For each role, run one or two web searches for current postings in the user's area (or remote, if they accept it). Record: do real postings exist (count roughly, with one or two example links), what they commonly ask for, and the rough pay where stated. **Drop roles with no real current postings**, and list them at the end as "dropped: no current postings found". Market signals from search are rough, so say so.

## 5. Write and ask

Write `HOME/adjacent/<YYYY-MM-DD>.md`: the evidence list, the three groups with everything above, the dropped roles, and a closing caveat: "These are possibilities, not promises. A pivot can still be a long shot."

Show a summary and ask: **"Which of these should I add to your target roles?"** Add **only** the ones the user approves to the `Target roles` line in `profile.md` (and their search terms to `Title keywords`). Show the changed lines. If they approve nothing, change nothing. `/sherpa:scout` picks up the additions on its next run.

## Rules

- Never suggest the user claim experience they don't have, even in a pivot.
- Call a long-shot pivot a long shot.
- Every role cites at least two real resume lines. If you can't find two, the role doesn't belong on the list.
