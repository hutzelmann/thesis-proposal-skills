# State the execution shape in the remaining exposed siblings

## Why

`2026-09-02-state-execution-shape` gave review, supervise, check and write an `## Execution shape` section after a real supervise run under a workflow-by-default host mode fanned out into 27 agents. Three siblings carry the same per-item shapes with no observed failure yet: reverse reads six thesis parts and harvests ten item classes from a document far larger than a proposal, import maps per section, reference, citation and figure into one file, and lit-search judges candidates one by one. A host that fans those out re-reads the thesis or the source per helper and gives one file several writers. The first change tracked this sweep as its own follow-up so the original could be measured on one variable; this is that sweep. Ideate (one question per turn), troubleshoot (stop at the first rung), customize and publish already run sequentially by construction and get nothing.

## What Changes

- `proposal-reverse`, `proposal-import`, `proposal-lit-search` each gain an `## Execution shape` section as the first section of the body, in the skill's own terms: reverse reads, harvests and writes in one context and never one helper per chapter, harvest item or section, because the knowledge cut is judged with a plan sentence and its outcome sentence side by side; import reads the source once and writes both files itself, never one helper per section, reference, citation or figure, because reordering and the personal-data strip need the whole document; lit-search judges the candidate set together and merges alone, never one helper per candidate, source or research question, because preprint-and-published pairing and key uniqueness are whole-set properties.
- Each section is pinned verbatim as a whole under `tests/unit/data/pinned_sentences/<skill>--execution-shape.txt`; `tests/unit/test_execution_shape.py` discovers the three from the pin names and enforces first position and completeness with no test edit.
- `harness/README.md` Known limitations names seven skills instead of four.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-reverse`: add a single-context execution requirement.
- `skill-import`: add a single-context execution requirement.
- `skill-lit-search`: add a single-context execution requirement.

## Impact

- `skills/proposal-reverse/SKILL.md`, `skills/proposal-import/SKILL.md`, `skills/proposal-lit-search/SKILL.md` (new first `##` section each; header regions untouched)
- Three new pin files; `harness/README.md` one bullet
- Spec deltas for the three capabilities. No scripts, no `shared/`, no frontmatter.
