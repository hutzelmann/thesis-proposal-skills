## Why

When haiku 5.5 replaced haiku 4.5 on 2026-10-13, the 4.5 row was kept as a disabled registry entry: its verdict is the only shipped `fail`, which `proposal-troubleshoot` uses to warn users still on it, and the matrix judge stays on it. The README then showed both rows. The maintainer asked that the README show only the most recent models, because most readers don't care about old ones.

## What Changes

- The README model-support summary lists the enabled registry models only; its "measured on" date is the newest log among them.
- The model×task grid document and the exported verdict data (`shared/model-support.json`, vendored into `proposal-troubleshoot`) still cover every registry model. The grid marks a disabled one `(disabled)`; the data keeps its `enabled` flag.
- The roster-consistency test compares the data with the whole roster and the README with its enabled rows.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: "Generated model-support report" (README rows: enabled models; grid and data: every registry model), "Shipped verdicts list exactly the registry roster" (README against the enabled rows).

## Impact

- `harness/support.py` (`render_summary`, `render_grid`), `harness/report.py` (per-model log dates, `newest_day`), `tests/unit/test_support_matrix.py`; regenerated `README.md` and `docs/model-support.md`.
- No skill changes: `proposal-troubleshoot` reads the data, which is unchanged in shape and content.
- The open change `add-evidence-beads` also modifies "Generated model-support report"; its delta has to carry this rule when it is implemented.
