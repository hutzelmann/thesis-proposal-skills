## Why

The research-question conventions bound the count below — `min_count: 1`, and the check errors when the section has no ordered list — but not above. A proposal with nine research questions passes the mechanical check silently, and nine questions is not a rich proposal: it is a proposal whose scope has not been decided. Reviewers spend their first pass on that, which is exactly the work these skills exist to remove.

The gap was found by an external contributor whose faculty template caps the count at three. The cap belongs in the guidance regardless of that template, because it is a property of a thesis-sized project rather than of one faculty's form.

## What Changes

- Add `max_count` to the research-question conventions in `structure.json`, default `5`, and report an error when a proposal exceeds it.
- State the bound in `guidelines.md` prose so the data and the guidance agree, naming the failure it detects (undecided scope) rather than only the number.
- Both bounds are workspace-overridable like every other structured key, so a supervisor who wants a stricter or looser count says so in their `guidelines.md`. The override wiring itself lands in `nest-workspace-overrides`; this change adds the data and the check.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the research-question conventions gain an upper bound alongside the existing lower bound.
- `skill-check`: the deterministic check reports a proposal exceeding the bound as an error.

## Impact

- `shared/structure.json` and its five generated copies under `skills/*/references/`.
- `skills/proposal-check/scripts/check.py` — one branch in the research-question section.
- `shared/guidelines/guidelines.md` and its five generated copies.
- No fixture exceeds three research questions, so no oracle changes. A new unit test covers the bound in both directions.
