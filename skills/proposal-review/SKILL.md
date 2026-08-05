---
name: proposal-review
description: High-level content review of a thesis proposal — argument structure, soundness, literature grounding, sharpness. Writes an enumerated review file with actionable suggestions. Use when the user asks for feedback, a review, or whether the proposal is ready for their supervisor.
---

# Proposal Review

Reads a finished draft the way a supervisor would and writes an enumerated `<slug>-review.md` next to it: what is weak, where, and a concrete suggestion for each point, ordered by severity.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → **proposal-review** → proposal-publish. Also: proposal-import (start from an existing document), proposal-customize (adapt the rules to a supervisor's requirements).

Content review only. You judge arguments and substance — never formatting, section layout, headings, or markup conventions (that is the check skill's territory; a proposal in a completely free-form structure gets zero structural complaints from you). The thesis title is the one thing in the metadata block you do judge: it is content, and it is printed on the student's study certificate.

## What to assess

Read `references/guidelines.md` (plus any workspace `guidelines.md` overrides) for the semantic rules, then review:

- **The title** — does it name a contribution and its object, or does it carry a tool, product, vendor or company name as the instrument, frame implementation work, name a whole field, or borrow marketing tone? Does it still describe what the research questions actually ask? Flag it as an enumerated item like any other finding, say that it reaches the study certificate, and suggest one to three abstracted alternatives. A named technology that is the object of the proposal's own research questions — an SLR of one platform, a study of one specific environment — is not a finding.
- **Research questions** — analytical rather than implementation goals ("how can X be built" is the classic failure), self-contained, answerable by the chosen methodology, non-overlapping, not yes/no.
- **Contribution delta** — is the difference to prior work stated explicitly and precisely, or does the section read as a feature list? Are claims grounded in cited literature, or do vendor/commercial sources carry scientific weight?
- **Argument soundness** — introduction motivates without overreaching; no repetition between sections; the methodology actually answers each research question; evaluation measures what the RQs ask.
- **Single methodology** — mixed methods (e.g. prototype plus full user study) get flagged with a scope-down suggestion.
- **Sharpness** — vague language, unnecessary information, inconsistencies between sections, scope risks for the thesis level (Bachelor vs Master).
- **Missing substance** — absent literature areas, missing information a supervisor would ask about.

## Output

Write `<slug>-review.md` next to the proposal (overwrite a previous review), in the proposal's `lang`:

- Enumerated issues, each with: what is wrong, where, and a concrete actionable suggestion. Order by severity.
- End — only if obvious grammar/spelling problems exist — with a brief hint naming the problem class plus one or two examples. Never an exhaustive language list; point to the check skill for that.

Summarize the top findings in chat (2–4 sentences) and mention the file. If the user wants fixes applied, that is the write skill's job ("apply the review").
