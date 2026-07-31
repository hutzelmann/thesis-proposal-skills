## 1. Check

- [x] 1.1 Warn when a reference id does not match the documented key shape or reaches the length limit
- [x] 1.2 Keep it warning class, so an unusual author name never fails a run

## 2. Corpus

- [x] 2.1 Rename `Bacchelli13Expectations` to a conforming key in the body, the reference entry, and the oracle's semantic note, preserving its role as the real correctly-cited control
- [x] 2.2 Re-verify every oracle

## 3. Simplify

- [x] 3.1 Drop the key-shape rule from the import instructions now the check makes it

## 4. Tests

- [x] 4.1 The shapes the eval actually produced (`RiveraYearSurvey`, `TanakaYearLoRA`) warn
- [x] 4.2 An over-long key warns
- [x] 4.3 Conforming keys stay silent, including institutional and particle-bearing ones
- [x] 4.4 The warning never changes the exit code

## 5. Verification

- [x] 5.1 `uv run pytest` green
- [x] 5.2 `uv run ruff check .` clean
- [x] 5.3 `python3 scripts/sync_shared.py --check` clean
- [x] 5.4 `openspec validate --all --strict` passes
