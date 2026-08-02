---
name: proposal-review
description: High-level content review of a thesis proposal — argument structure, soundness, literature grounding, sharpness. Writes an enumerated review file with actionable suggestions. Use when the user asks for feedback, a review, or whether the proposal is ready for their supervisor.
---

# Proposal Review

Content review only. You judge arguments and substance — never formatting, section layout, headings, or markup conventions (that is the check skill's territory; a proposal in a completely free-form structure gets zero structural complaints from you).

## What to assess

Read `references/guidelines.md` (plus any workspace `guidelines.md` overrides) for the semantic rules, then review:

- **Research questions** — analytical rather than implementation goals ("how can X be built" is the classic failure), self-contained, answerable by the chosen methodology, non-overlapping, not yes/no.
- **Contribution delta** — is the difference to prior work stated explicitly and precisely, or does the section read as a feature list? Are claims grounded in cited literature, or do vendor/commercial sources carry scientific weight?
- **Argument soundness** — introduction motivates without overreaching; no repetition between sections; the methodology actually answers each research question; evaluation measures what the RQs ask.
- **Methodology declaration** — the proposal declares exactly one methodology. A proposal that runs a qualitative and a quantitative strand must declare Mixed Methods and use that branch; two methodologies stacked under one heading, or a strand smuggled into another branch's subsections, gets flagged. Where Mixed Methods *is* declared, judge the Integration subsection hardest: if it does not say which research questions each strand answers and how the results combine, the proposal is two small studies wearing one title, and the suggestion is to drop a strand.
- **Scope for the level** — an added strand is the most common way a Bachelor's proposal becomes undeliverable. Flag scope risk on its own merits, not because the methodology is mixed.
- **Objectives versus research questions** — objectives say what the work will do and start with an action verb; research questions ask what it will find out. A "how can X be built" phrasing sitting in the research questions usually means the objectives leaked upward; say which one to move.
- **Related work** — thematic clusters rather than a chronological reading list, a synthesis that names each cluster's shared limitation, and a closing gap statement tied to the research questions.
- **Expected contributions** — findings stated as expectations rather than as results already obtained, contributions distinguished from objectives, and limitations named rather than implied.
- **Work plan** — phases that cover the full period, buffer before submission, and a critical path that matches the methodology. A plan whose data-collection phase ends the week before submission is not feasible.
- **Sharpness** — vague language, unnecessary information, inconsistencies between sections, scope risks for the thesis level (Bachelor vs Master).
- **Missing substance** — absent literature areas, missing information a supervisor would ask about.

## Output

Write `<slug>-review.md` next to the proposal (overwrite a previous review), in the proposal's `lang`:

- Enumerated issues, each with: what is wrong, where, and a concrete actionable suggestion. Order by severity.
- End — only if obvious grammar/spelling problems exist — with a brief hint naming the problem class plus one or two examples. Never an exhaustive language list; point to the check skill for that.

Summarize the top findings in chat (2–4 sentences) and mention the file. If the user wants fixes applied, that is the write skill's job ("apply the review").
