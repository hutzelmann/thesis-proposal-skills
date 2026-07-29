# Design: Demo-Derived Fixtures

## Context

Source material exists and is already audited: `docs/demo/harvest.log` (committed) and the demo scratch workspace containing the final `drift-alert-validity.md` (15 references, 5 TODOs, citation inside RQ2). The fixture corpus, oracles, and eval personas follow established conventions (`tests/fixtures/README.md`, `harness/personas/`). See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Lock in the `rq-filter.lua` citation fix with an automated regression test.
- Add one realistic, skills-generated fixture and one realistic persona.

**Non-Goals:**
- Replacing existing fixtures (f00 clean control serves a different purpose: hand-invented, TODO-free).
- New eval task types or harness code changes.
- A w-series workflow seed from the anecdote (the persona covers the ideate entry point).

## Decisions

### 1. Fixture content copied from the scratch workspace, not regenerated
`drift-alert-validity.md` is copied verbatim from the demo session workspace (synthetic topic, no personal data — `author` is a `[TODO: add author]` placeholder). Regenerating would produce different references and break the audit trail to `harvest.log`. The fixture's `expected.json` encodes: check exit 0 (structure complete), warnings for the open TODOs, and semantic notes (deliberate open decisions, not defects).

### 2. Regression test drives pandoc directly, gated on availability
The test invokes `pandoc -t typst --citeproc --lua-filter rq-filter.lua` on a minimal in-test document (RQ list with one `[@key]` citation and a matching CSL-YAML reference) and asserts `#rq(1)[` wrapping plus no `@key` remnants. `pytest.mark.skipif(shutil.which("pandoc") is None)` keeps offline environments green; CI installs pandoc only if it already does — otherwise the test simply skips there too. A full typst-to-PDF build is out of scope (typst adds a second tool gate for little extra signal; the bug lived in filter output).

### 3. Persona as data, mirroring existing persona files
New persona file in `harness/personas/` describing the demo student: practically motivated, concrete churn-anecdote, delayed-labels pain, cannot use company data, tends to answer questions with anecdotes rather than research terms. Same file format as existing personas. Implementation note: each ideate eval task hardwires its persona file, so a minimal second `@task` (mirroring `ideate_socratic`, with the demo opening prompt) is added — persona files alone are not auto-discovered. Name and personal details are obviously fake per fixture rules.

## Risks / Trade-offs

- [Fixture references age (venues, DOIs never re-verified)] → acceptable: oracles test structure/consistency, not liveness of DOIs; references were verified at harvest time.
- [pandoc version differences change filter output shape] → assert on stable invariants only (`#rq(` marker present, no unresolved `@key`), not exact serialization.

## Migration Plan

Purely additive; rollback = delete the new files.

## Open Questions

- Exact persona filename/wording — settled at implementation against the existing persona files' format.
