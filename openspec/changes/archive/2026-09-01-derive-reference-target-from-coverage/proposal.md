# Derive the reference target from coverage

## Why

The prose guidance states that a submitted proposal "usually carries ten to fifteen" references. The number has no stated justification — it was harvested from one argued-over exposé rewrite (`2026-08-11-harvest-proposal-guidance` left it deliberately unformalized) — and it is fixed to the default five-page length: a workspace that overrides `page_limit` keeps a target calibrated for a different document. By the repo's own standard for defaults, an asserted number without provenance is a preference wearing a citation's clothes.

The range is defensible, but for a reason the prose never gives: it falls out of rules the guidance already has. A contribution section that groups prior work into thematic clusters needs at least two sources per cluster to show a theme rather than an anecdote, each research question's motivation needs grounding, and the introduction must ground its claims — for a five-page proposal that lands at ten to fifteen. Stated as density (roughly four to six references per thousand words), the expectation also scales with the proposal's actual length instead of silently assuming the default limit.

## What Changes

- **Prose target restated as derived, not asserted.** The literature guidance derives the working range from coverage (clusters, research-question grounding) and states it as a density that scales with length, instead of asserting "usually carries ten to fifteen" as an observed frequency. The floor stays 3 and stays an error.
- **Scale-aware density advisory in the deterministic check.** A new structured constant `[references] min_per_1000_words` (default 4) drives a warning — never an error — when the proposal defines fewer references than `ceil(body words × min_per_1000_words / 1000)`. The warning is suppressed while the floor error already fires (one finding per defect), a value of `0` disables it, and an invalid override degrades to the default exactly like `page_limit`.
- **Workspace-overridable under the one naming rule.** The key path mirrors `structure.json` (`[references] min_per_1000_words`); no aliases. `proposal-customize` documents it beside `min_count`.
- Shipped fixtures are unaffected: their bodies span 76–995 words, and every fixture defines at least as many references as its length expects (the 995-word f19 carries 15 against an expectation of 4), so no fixture oracle changes.

Out of scope: measuring the constant against a real accepted-proposal corpus (the private directory). That pass would turn the default 4/1000 from a derived estimate into a measured one, but its result would be program-specific — a workspace value, not a shipped one — and it needs its own handling of the workspace boundary.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the reference-target requirement derives the range from coverage and states it as length-scaled density; the overridable set and the mechanically checkable skeleton gain the density constant.
- `skill-check`: new advisory reference-density warning with override, disable, and degradation semantics mirroring the estimated-length warning.

## Impact

- `shared/structure.json` (+ generated copies): `references.min_per_1000_words` with an estimation-constant comment.
- `shared/guidelines/guidelines.md` (+ generated copies): the literature-target paragraph.
- `skills/proposal-check/scripts/check.py` (+ vendored copy): word-count helper shared with the length rule, new rule, two new rule ids (`reference-density-low`, `reference-density-invalid`), `OVERRIDABLE` entry.
- `skills/proposal-customize/SKILL.md`: TOML example gains the key.
- `tests/unit/test_check_rules.py`, `tests/unit/test_check.py`: unit coverage for both new ids (no fixture reaches them, so they join `COVERED_BY_UNIT_TESTS`).
- No fixture or oracle changes; no harness changes.
