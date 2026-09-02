# Fix the execution-shape wording after review

## Why

A two-lens adversarial review of the four execution-shape commits found wording defects an agent could act on: check's pinned first sentence says the script runs once while the pinned mandate successor requires a second run for the digest comparison; review and supervise never say whether the writer counts among the three capped agents, so a host counting itself out spawns three helpers and complies; supervise enumerates three files it alone writes and omits the notes file, with no blanket no-write rule; review and write carry a "following a sibling is not a helper" clause with no sibling to follow, while the sibling change's own rule says the clause belongs only where one is followed; the helper contract's "no reasoning prose" sentence has no subject and reads as a rule for the review file; supervise restates the evidence bar's number, which will drift; lit-search's "the scripts gather" is false on its own networking-denied fallback; write's slogan misdescribes a two-file skill; reverse's section narrows the reading scope its own "What you read" section sets; the rung-5 sentence presumes every skill states a shape. AGENTS.md does not document the convention at all.

## What Changes

- Review and supervise: the cap is stated from the writer's side — three agents including you, where you are the full review and helpers are at most one adversarial check and one in-file citation read; a helper's return is what carries no reasoning prose or strengths list; a helper writes no file; supervise names its notes file among the files only it writes and refers to the evidence bar instead of restating its number; the sibling clause stays in supervise, which does follow import and lit-search, and leaves review.
- Check: the shape names the digest re-run of a non-interactive run as part of the single agent's two steps.
- Write: "One writer per file", sibling clause dropped. Lit-search: the networking-denied fallback is folded into the shape. Reverse: the section states the single-context claim and its reason without restating or narrowing the reading scope.
- Troubleshoot rung 5 and README: "where it states one", and the remedy names budget and effort controls as the spec already does.
- AGENTS.md "Skill header pattern" documents the convention: which skills carry the section, where it sits, how it is pinned and tested, how coverage extends.
- All six pins rewritten to the new sections; specs restated.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-review`: "Single-context execution" — cap counted including the writer; helper-return subject bound; sibling clause removed.
- `skill-supervise`: "Single-context execution" — cap counted including the writer; blanket no-write rule with the notes file named; evidence bar referenced, not restated; helper-return subject bound.
- `skill-check`: "Single-agent execution" — digest re-run named.
- `skill-write`: "One writer per file" — sibling clause removed.
- `skill-lit-search`: "Single-context execution" — fallback path folded in.
- `skill-reverse`: "Single-context execution" — reading scope no longer restated.
- `skill-troubleshoot`: "Non-defect causes named as such" — "where it states one".

## Impact

- Six `SKILL.md` first sections, their six pins, `skills/proposal-troubleshoot/SKILL.md` rung 5, `README.md` one clause, `AGENTS.md` one paragraph. Spec deltas for the seven capabilities. No scripts, no `shared/`, no frontmatter.
