## 1. Fix

- [x] 1.1 Close the child's stdin in `run_claude`

## 2. Verification

- [x] 2.1 `uv run pytest` green (129)
- [x] 2.2 `uv run ruff check .` clean
- [x] 2.3 Re-measured: **6/6 pass, no phantom write**, against roughly 1 in 11 before. Attribution is not clean — the script-path fix landed between the two measurements as well — so the honest claim is that the failure has not recurred since the tooling defects were repaired, not that stdin alone caused it
