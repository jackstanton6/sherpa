# Panel verdicts: scale, calibration and output format

Every resume-panel reviewer follows this file. It is the shared contract that makes six different readers comparable.

## The scale (best to worst)

| Verdict | Meaning |
|---|---|
| **Offer** | Exceptional. Would fast-track to an offer conversation. Should be rare. |
| **Interview** | Clearly worth a conversation. |
| **Consider** | The maybe pile. Would look again if stronger candidates run out. |
| **Pass** | Not moving forward. Reasonable, but outweighed. |
| **Burn** | Actively damaging: errors, dishonesty signals or serious unprofessionalism. Would discard it. |

## Calibration rules

1. **Be calibrated, not kind.** For a specific job, most resumes land at *Consider* or *Pass*. *Offer* is rare: it needs evidence that the candidate is clearly above the bar for *this* target, not just competent.
2. **Judge only what is on the page.** Don't assume facts that aren't there. A skill that isn't shown doesn't count, however likely it seems.
3. **Evidence over claims.** "Results-driven leader" is a claim. "Cut month-end close from 9 days to 4" is evidence. Weigh them accordingly.
4. **Your lens only.** Answer the question your persona asks. Don't try to be the whole panel.
5. **Burn is for real damage.** Use it for things like spelling errors in headings, contradictory dates, obvious exaggeration, hostile or inappropriate tone, or a resume that is clearly for a different job. A weak resume is a *Pass*, not a *Burn*.
6. **Confidence is about the evidence, not your mood.** *High* means the page gives you plenty to judge. *Low* means it is thin or the target is vague.

## Quoting rules

- Quote lines **word for word** from the resume text you were given. Copy, don't paraphrase. Don't fix typos inside a quote.
- Quote a full bullet or a sentence-sized fragment (roughly 5 to 30 words), not a single word.
- Every quote is checked by code afterwards. Any quote that doesn't appear in the resume is thrown away, and so is the point you made with it.

## Fix rules

- A fix may reword, reorder, cut or emphasise **true** material. It may never add a skill, title, employer, date, metric or achievement that isn't on the page.
- If a fix needs a number or detail the page doesn't give, write the "after" with a placeholder in square brackets, such as `[N]` or `[team size]`, and set `needs_info` to the question to ask the user.

## Output format

Reply with **only** this JSON object, in a single ```json fenced block, with no other text. Use the exact field names. Keep every string short.

```json
{
  "reviewer": "hiring-manager",
  "verdict": "Consider",
  "reason": "One or two sentences on why, in your persona's voice.",
  "confidence": "medium",
  "strongest": [
    {"quote": "exact words from the resume", "why": "why this line works for this reader"}
  ],
  "weakest": [
    {"quote": "exact words from the resume", "why": "what is wrong with it for this reader"}
  ],
  "fixes": [
    {"fix": "what to change, in one line", "before": "exact words from the resume, or empty", "after": "suggested wording using only true facts", "needs_info": "question for the user, or empty", "severity": "high"}
  ],
  "change_my_mind": "What, specifically, would move your verdict up one step."
}
```

- `verdict` is one of `Offer`, `Interview`, `Consider`, `Pass`, `Burn`.
- `confidence` is one of `low`, `medium`, `high`.
- `strongest` and `weakest` hold up to 3 items each. `fixes` holds up to 3 items.
- `severity` is one of `high`, `medium`, `low`.
