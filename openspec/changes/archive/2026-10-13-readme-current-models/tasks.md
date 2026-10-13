# Tasks

## 1. Report

- [x] 1.1 `support.render_summary` renders enabled models only and no longer appends "disabled in registry"; `support.render_grid` marks a disabled model `(disabled)`. Verify: `test_render_summary_leaves_disabled_models_out`.
- [x] 1.2 `report.py` keeps the newest log start per model and dates the README by the enabled models' logs (`newest_day`); the grid and the data keep the date of all logs. Verify: `test_newest_day_takes_the_newest_stamp_or_never`; the regenerated README reads 2026-08-06 (the newest log of an enabled model) while the grid reads 2026-08-10.
- [x] 1.3 `shipped_roster_mismatch` compares the data with the whole roster and the README with its enabled rows; the unregenerated-bump test picks an enabled row. Verify: `test_shipped_verdicts_list_exactly_the_registry_roster` and `test_shipped_verdict_check_catches_an_unregenerated_bump` pass.

## 2. Regenerate and gate

- [x] 2.1 `uv run poe report`, `python3 scripts/sync_shared.py`; the README drops the disabled haiku 4.5 row, and `shared/model-support.json` is unchanged.
- [x] 2.2 `uv run poe test`, `uv run poe specs` and `openspec validate readme-current-models --strict` green.
