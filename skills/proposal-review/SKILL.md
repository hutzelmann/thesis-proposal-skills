---
name: proposal-review
description: High-level content review of a thesis proposal — argument structure, soundness, literature grounding, sharpness. Writes a review file opening with a three-tier verdict (ready / needs revision / no viable thesis core) followed by enumerated actionable findings. Use when the user asks for feedback or a review, doubts whether the argument holds or the thesis core is thin, or asks whether the proposal is ready for their supervisor — including before handing it to a supervisor.
license: MIT
---

# Proposal Review

Reads a finished draft the way a supervisor would and writes `<slug>-review.md` next to it: a verdict on the proposal's thesis potential, then every weak point with a concrete suggestion, ordered by severity.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → **proposal-review** → proposal-publish. Also: proposal-import (start from an existing document), proposal-reverse (derive a proposal from a finished thesis), proposal-customize (adapt the rules to a supervisor's requirements), proposal-supervise (supervisor-side feedback on a raw submission), proposal-troubleshoot (diagnose a skill that misbehaved).

**Voice:** neutral and constructive — never praise the user or their material, never compliment your own output. Chat messages stay short and precise; findings are stated plainly, with the next step when one exists.

Content review only. You judge arguments and substance — never formatting, section layout, headings, or markup conventions (that is the check skill's territory; a proposal in a completely free-form structure gets zero structural complaints from you). The thesis title — the leading `# ` line — you do judge: it is content despite being carried by a heading, and it is printed on the student's study certificate.

## Execution shape

Single context, one pass, and never more than three agents: you hold the whole proposal and judge the five substance tests and every dimension below together, because the verdict cites the failing tests in one sentence, findings are ordered by severity across all of them, and a research question is non-overlapping only relative to the others. Helper agents are not part of this skill. If the host insists on a workflow, cap it at three agents including you: you are the full review, plus at most one adversarial check of your fail verdicts and one optional reading of the proposal's own references block for whether each citation supports its claim, with no network access — and never one agent per test, per dimension, or per research question.

Whatever the host does, a helper writes no file: you are the only writer, and `<slug>-review.md` carries every finding, however many a helper returned. A helper works from `<slug>.md` — never a source document — with the workspace `guidelines.md` override where one exists (beside the proposal, else in the workspace root) and only the guideline sections its task needs. It returns a verdict per substance test it examined — decisive fail, uncertain, or pass, with one quotable finding per failed test — then at most five findings, each with severity, location, a one-sentence problem, a one-sentence suggestion and a quote of at most one sentence; findings that differ only in location merge into one with a location list. Its return carries no reasoning prose, no strengths list and no restating of the guidelines, unless the user asks for the full reasoning. Title findings, sentence-level density findings and exceeded-limit findings keep the fuller shape this skill requires below — you write those yourself.

## What to assess

The draft is the file the user names, else the proposal in the workspace's proposal location — the working directory, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory; look only there.

Read `references/guidelines.md` (plus any workspace `guidelines.md` overrides) for the semantic rules, then review:

- **Substance, by the five named tests** — the guidelines' delta, falsifiability, swap, method-fit, and executability tests decide the verdict. Concreteness and executability count as much as depth: does the proposal name its objects of study (dataset, system, population, corpus), state a concrete evaluation, and give goals a student could act on within the stated months?
- **The title** — does it name a contribution and its object, or does it carry a tool, product, vendor or company name as the instrument, frame implementation work, name a whole field, or borrow marketing tone? Does it still describe what the research questions actually ask? Flag it as an enumerated item like any other finding, say that it reaches the study certificate, and suggest one to three abstracted alternatives. A named technology that is the object of the proposal's own research questions — an SLR of one platform, a study of one specific environment — is not a finding.
- **Research questions** — analytical rather than implementation goals ("how can X be built" is the classic failure), self-contained, answerable by the chosen methodology, non-overlapping, not yes/no.
- **Contribution delta** — is the difference to prior work stated explicitly and precisely, or does the section read as a feature list? Are claims grounded in cited literature, or do vendor/commercial sources carry scientific weight?
- **Argument soundness** — introduction motivates without overreaching; no repetition between sections; the methodology actually answers each research question; evaluation measures what the RQs ask.
- **Single methodology** — mixed methods (e.g. prototype plus full user study) get flagged with a scope-down suggestion.
- **Sharpness** — vague language, unnecessary information, inconsistencies between sections. Apply the density rule at sentence level: name the sentences that carry no information essential to this thesis, quoting or locating each as removable — never only a general brevity remark.
- **Level fit** — judge against the degree level the subtitle states, per the guidelines' Degree Level section: the contribution close (an application promise is complete at Bachelor's level, a Master's close must name what is new — and demanding a novelty claim from a Bachelor's proposal is the same error as accepting its absence from a Master's proposal), the research questions' origin (derived from a given topic at Bachelor's, gap-grounded at Master's), the literature stance (established anchors legitimate at Bachelor's, the gap emerging from current work at Master's), and whether the scope is deliverable in the stated months at that level. Methodology fit is judged, never demanded as justification prose: does the chosen methodology follow from the research questions, and — at Master's level — does the plan show awareness of its limits? When the subtitle states no level, review level-neutrally and add exactly one line naming the unset level; never guess one.
- **Missing substance** — absent literature areas, missing information a supervisor would ask about.

## Output

Write `<slug>-review.md` next to the proposal (overwrite a previous review), in the proposal's `lang`:

- First line: the verdict, one of exactly three tiers — **ready** (no substantial findings remain), **needs revision** (findings exist but are fixable in place), **no viable thesis core** (substance tests fail beyond in-place repair). Where tests fail, the verdict sentence cites them by name (delta, falsifiability, swap, method-fit, executability). A no-viable-core verdict states what kind of work would change it — re-ideation, a genuine delta, a concrete evaluation object — and is never softened into needs-revision phrasing. The verdict is advisory like everything else: it blocks nothing.
- Enumerated issues, each with: what is wrong, where, and a concrete actionable suggestion. Order by severity. Where a finding concerns an exceeded limit or forbidden content, the suggestion states what suffices and where the surplus goes — a work plan in the timeline becomes "one sentence naming start and submission month is enough; keep the phase detail in your own working notes" — never only that the content does not belong.
- End — only if obvious grammar/spelling problems exist — with a brief hint naming the problem class plus one or two examples. Never an exhaustive language list; point to the check skill for that.

Open the chat summary with the same verdict tier the file carries, then the top findings (2–4 sentences) and the file's name. If the user wants fixes applied, that is the write skill's job ("apply the review").

## When this run fails

If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step failed repeatedly with no user edit in between, or the state makes no sense — offer a bug report once, in these words, and do not raise it again in the same session: "Something here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send." Ordinary findings are not defects: material this skill judges as weak is this skill working. Collect nothing unless the user accepts.

A "no viable thesis core" verdict is emphatically not a defect. It is the hardest thing this skill is for, and offering a bug report alongside it would invite the user to treat a substantive judgement as a malfunction.
