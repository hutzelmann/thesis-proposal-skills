## 1. Fix

- [x] 1.1 Match oracle needles case-insensitively in `verdict_check_report`

## 2. Tests

- [x] 2.1 A relay that differs only in capitalisation counts as relayed
- [x] 2.2 A relay genuinely missing findings still fails
- [x] 2.3 The byte-identity assertion is unaffected

## 3. Verification

- [x] 3.1 `uv run pytest` green
- [x] 3.2 `uv run ruff check .` clean
- [x] 3.3 `openspec validate --all --strict` passes
- [x] 3.4 Re-ran on both models: haiku 2/5, sonnet 1/5 — still below the threshold, so the prediction of ≥3/5 was wrong. Inspecting the relay showed why: the dominant failure is not capitalisation but the model failing to locate `scripts/check.py` and falling back to manual inspection, whose findings differ in substance. This fix removes a real defect but is not sufficient on its own; the script-path problem is tracked separately
