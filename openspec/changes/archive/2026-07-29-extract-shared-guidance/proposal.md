# Proposal: extract-shared-guidance

## Why

Implements the guidance-model and skill-packaging specs' foundation: the single dev-side source of truth in `shared/`, the machine-readable `structure.json`, and the sync mechanism that materializes committed copies into skills. Every skill change after this depends on it (write/review/customize/ideate need the prose; check/ideate need the structure data). Content is distilled from the legacy `AGENTS.md` — the proven guidance gold — with LaTeX mechanics replaced by the markdown/CSL conventions.

## What Changes

- `shared/guidelines/guidelines.md`: prose guidance (structure, RQ criteria, methodology subsections, citation usage, writing rules, en+de conventions) — LaTeX-specific rules dropped/translated.
- `shared/structure.json`: canonical section titles (en+de), order, methodology→subsections table, forbidden-heading patterns, `min_references`, RQ conventions.
- `scripts/sync_shared.py`: one-way deterministic materialization into skill `references/` dirs with GENERATED headers; `--check` mode.
- First sync run creates the skill `references/` trees (write, review, customize, ideate, check).
- L0 tests: sync `--check` consistency + `structure.json`↔prose drift guard.
- `skip_specs: true` — implements existing requirements (incl. "canonical German titles SHALL be defined"); no contract changes.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- New: `shared/`, `scripts/sync_shared.py`, `tests/unit/`, generated `skills/proposal-{write,review,customize,ideate,check}/references/`.
- Legacy `AGENTS.md` stays untouched for now (deleted in the later cleanup change).
