# Tasks

## 1. Atomic write in sync_shared

- [x] 1.1 Replace `dest.write_text()` in `_materialize()` (scripts/sync_shared.py) with an atomic write: temp file in `dest.parent` via `tempfile`, then `os.replace()` onto `dest`; clean up the temp file on failure
- [x] 1.2 Add an L0 unit test pinning the atomic behavior (no truncation window observable through the public write path)

## 2. Verify

- [x] 2.1 `uv run poe test-fast` repeatedly (≥5 runs) with no `JSONDecodeError` flake
- [x] 2.2 `uv run poe test` green (includes ruff + drift check)
