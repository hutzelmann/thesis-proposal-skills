## Why

A thesis exists; its proposal does not. That happens when a program requires a proposal on file and the work ran ahead of the paperwork, and it happens when a supervisor wants to show a cohort what the proposal for a thesis they supervised should have looked like. Both need the same document and neither has a route to it: `proposal-import` carries an existing proposal across, and nothing in the set reads a finished thesis.

Doing it by hand fails in a specific way. A thesis states its results, so a proposal written out of one states them too — claims the work had not yet earned, and specifics no planner could have known. That is not a wording problem to fix at review time; it is the whole difficulty of the direction, and it is what the new skill exists to handle.

## What Changes

- New skill `proposal-reverse`, the eleventh in the set: a finished thesis in, a proposal in the standard file format out.
- **Two steps.** Harvest reads only the framing and closing chapters of the thesis — title page, introduction, research-question statement, methodology chapter, limitations and future work, bibliography — and writes a small `<slug>.harvest.md` record the user can inspect before any proposal is written. Write turns that record into `<slug>.md`. Results chapters are read for evaluation *design* sentences or not at all.
- **Four rules govern the write step.** The knowledge cut: a sentence leaks hindsight if deleting the thesis's results makes it unsupportable, and this applies to specifics — a final sample size, the baseline settled on after a first one failed — as much as to claims. Scope and validity carry forward: the thesis's delimitations become the proposal's scope, its limitations become acknowledged risks. A reference survives if and only if a sentence citing it survives. Everything the thesis cannot supply becomes a `[TODO: …]` marker, and nothing is invented.
- **Reference shortfall has a defined escalation** rather than a shrug: it is first read as an underwritten Contribution section and repaired by writing the delta against the thesis's related-work chapter, then by widening to entries the thesis itself cites in its framing chapters, and only then reported as a shortfall pointing at `proposal-lit-search`.
- **`proposal-check` gains one warning-class rule** for hindsight leakage: result verbs with the work as subject, and quantitative outcomes stated as findings, in sentences carrying no citation. The citation anchor is what makes the rule usable — reporting what prior work established is exactly what the Contribution section does. Whether a research question is *secretly* a settled claim needs knowledge the document does not carry, and stays with `proposal-review` and the reader.
- The workflow line in `shared/blocks/workflow.md` names the new skill, and the sync materializes it into all eleven pages.

## Capabilities

### New Capabilities

- `skill-reverse`: deriving a proposal from a finished thesis — what is read, what is cut, what is carried forward, and what is reported rather than repaired.

### Modified Capabilities

- `skill-check`: gains the mechanical hindsight-leakage rule.

`skill-packaging` needs no delta: it states the set's rules without stating its size, and already carries the "Skill added to the set" scenario. The new skill is bound by it as written.

## Impact

- New `skills/proposal-reverse/` — `SKILL.md`, `references/structure.json`, and `scripts/` (check.py, validate_refs.py and the modules it imports), all synchronized copies, since verifying its own fresh output is core to its function and a skill installed alone cannot borrow a sibling's scripts. The semantic guidance travels the way import's does: named in the write skill's references when installed, with the essentials stated inline.
- `shared/blocks/workflow.md` and the resulting resync of every `SKILL.md`.
- `scripts/sync_shared.py` — new destinations in `SYNC_MAP`.
- `tests/unit/data/skill_mandates/proposal-reverse.txt` — the pinned mandate.
- `skills/proposal-check/scripts/check.py` plus its synchronized copies, `harness/l1_checks.py`, and the L0 tests for the new rule.
- `harness/skill_evals.py` and one synthetic harvest-record fixture. No thesis enters this repository: the harvest record is the boundary that keeps a copyrighted, hundred-page document out of the fixture set, and quality judgment stays with the human rather than an automatic test.
- Frontmatter budget: 4102 of 4500 characters are used, leaving under 400 for the new skill's metadata.
- Body size: the suite median is 1308.5 words and the cap is twice the median. An eleventh body below roughly 1300 words lowers the median and fails `proposal-ideate` at 2598. The new body has a floor as well as a ceiling.
