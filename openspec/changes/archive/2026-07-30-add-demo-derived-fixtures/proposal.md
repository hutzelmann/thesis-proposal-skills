# Add Demo-Derived Fixtures and Regression Tests

## Why

The README demo session produced real, high-quality skill output that the test suite currently lacks: a skills-generated clean-with-TODOs proposal, a proposal with a citation inside a research question (the exact pattern that crashed `proposal-publish`'s `rq-filter.lua` until commit `a8127ef`), and a naturally phrased student voice. Turning these into fixtures and tests locks in the bug fix and makes the evals more realistic — explicitly requested by the maintainer.

## What Changes

- New fixture `f19-drift-alert-validity`: the skills-generated MSc/EN proposal from the demo session (15 verified references, 5 open `[TODO: …]` markers, citation `[@Tan25Flexibl]` inside RQ2) plus its `expected.json` oracle; blueprint table row added in `tests/fixtures/README.md`. Addition, not replacement — no existing fixture covers "skill-generated clean-with-TODOs" or "citation inside an RQ".
- New L0 regression test for `rq-filter.lua`: run pandoc's typst writer with the filter over an RQ list containing a citation and assert the citation reaches typst resolved (no `@key` leftovers); skipped when `pandoc` is unavailable.
- New ideate persona derived from the demo student (practically motivated, concrete work anecdote, data-access constraint) for the `persona_dialogue` evals in `harness/skill_evals.py`.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `testing-harness`: two ADDED requirements — publish-filter regression coverage (citation-inside-RQ fixture must build), and provenance rules for session-derived fixtures (synthetic topic, audited against the session log, no personal data).

## Impact

- `tests/fixtures/f19-drift-alert-validity/` (proposal + `expected.json`), `tests/fixtures/README.md` (blueprint row).
- `tests/unit/` new regression test module for the rq-filter (pandoc-gated).
- `harness/personas/` new persona file; no changes to eval task code (personas are data).
- Source material: `docs/demo/harvest.log` and the demo scratch workspace; content is already synthetic and audited.
