## Why

A real proposal drafted with the skills (2026-10-18) opened its methodology section with a suitability verdict — "*methodology* fits because …" — whose reasons were the shipped branch's own definition handed back as a property of the research questions, plus a feasibility argument and a contrast with participants nobody had proposed. The choice itself was sound; the sentence made it read like a defense of a doubtful one. Two causes stack:

- **The guidance contradicts itself.** "Methodology Content" (added by `2026-08-11-fix-shipped-branch-contracts`, from the SIGSOFT General Standard) makes every methodology section open with one or two sentences "stating why this methodology answers these research questions" and calls a section without them one that "skipped its own justification". The Degree Level section (added by `2026-09-02-add-degree-level-tailoring`) says "Neither level requires a statement justifying the methodology choice … judged in review, not written as defense", and `proposal-review` carries the same line. That change's wording check looked at its own diff, so the older rule survived beside it. A writer told both "justify" and "this is not to be written as defense" produces a hedge.
- **Nothing says what a good justification is.** The rule asks for a "why" and gives no shape, and the spec's own example scenario ("a user study is chosen because … rather than tool performance") models the defensive frame. All seventeen tracked fixtures with an opener use "*X* fits these questions because …", the ready-tier review fixtures included, so the harness calibrates on the same shape.

The maintainer settled the direction on 2026-10-18: the methodology section **does** justify its choice, and states it confidently — why this methodology is the right one for these questions, not why it is acceptable. This withdraws the 2026-09-02 "no justification prose at any level" clause.

## What Changes

- **The opening justification gets a shape.** `shared/guidelines/guidelines.md` "Methodology Content" keeps the one-or-two-sentence opening and states what it contains: what answering these research questions demands, and what this methodology does that meets the demand, in the questions' own terms (their conditions, objects and measures). It is written as a claim the plan then makes good. It names what to leave out: a suitability verdict ("fits", "is suitable", "lends itself", "is chosen because"), the branch's own definition handed back as a property of the questions, feasibility as the reason, and methodologies not taken. A short synthetic example shows the shape.
- **The contradiction goes.** The Degree Level section's no-justification sentence is replaced by one saying the opening justification is the same at both levels; `proposal-review`'s level-fit bullet stops saying methodology fit is "never demanded as justification prose" and judges the opening by the method-fit test instead.
- **Classification is fixed.** A missing opening, or one written as a suitability verdict, is a refinement. A justification whose stated demand is not what the research questions ask, or whose methodology cannot meet it, is a method-fit failure, which blocks as before.
- **Fixtures model the target.** The seventeen fixture openers are rewritten to the confident shape. Only prose before the first methodology subsection changes, so no `expected.json`, recorded research questions or review currency moves. The twenty fixtures with no opener at all stay as they are: they exercise other defects.
- **L1 guard on write output.** A new `verdict_methodology_opening()` in `harness/l1_checks.py` fails a draft whose methodology section has no prose before its first subsection, or whose opening uses a suitability verdict (English and German phrase lists). `verdict_draft()` calls it, so `write_l1`, `write_rich_seed_l1`, `write_repair_citations_l1` and the dev runner's write scenarios all apply it; the `evals.json` projection follows the docstring.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: MODIFIED "Methodology sections justify method fit" (the shape of the opening, what it leaves out, its classification), "Degree-level guidance" (the no-justification clause becomes a same-at-both-levels clause).
- `skill-review`: MODIFIED "Degree-level review lenses" (methodology fit judged on the opening justification by the method-fit test, not "never as a demand for justification prose").
- `testing-harness`: ADDED "Methodology-opening coverage".

## Impact

- `shared/guidelines/guidelines.md` (Degree Level, Methodology Content) and its generated `references/guidelines.md` copies, via `scripts/sync_shared.py`.
- `skills/proposal-review/SKILL.md` (level-fit bullet). `proposal-supervise` applies the review rules by reference and needs no edit.
- `harness/l1_checks.py`, `harness/README.md`, the generated `skills/proposal-write/evals/evals.json`; L0 tests in `tests/unit/`.
- Seventeen fixture proposals under `tests/fixtures/`.
- Shipped matrix verdicts for the three write tasks were measured without the new check; the next gated matrix run re-measures them. No metered run is part of this change; verification uses the subscription dev runner.

Changelog: Methodology sections now open by stating confidently why the chosen methodology is the right one for the research questions, instead of arguing that it fits; review no longer says such a justification is never required.
