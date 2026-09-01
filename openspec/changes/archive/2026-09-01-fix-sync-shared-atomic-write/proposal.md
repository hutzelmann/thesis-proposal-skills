# Fix sync_shared non-atomic writes (concurrent-reader race)

## Why

`scripts/sync_shared.py` writes generated copies with `Path.write_text()`, which truncates the destination before writing. Any concurrent reader can observe an empty file in that window. This is not theoretical: `tests/unit/test_sync.py::test_synced_lines_stay_parseable_by_the_pre_commit_hook` runs a real `sync_shared.main([])` over the repository tree while other pytest-xdist workers read the same generated files, producing a one-off `JSONDecodeError('Expecting value: line 1 column 1 (char 0)')` in `test_check.py` when a worker read `skills/proposal-check/references/structure.json` mid-truncation. The `xdist_group('sync_shared_tree')` marker only serializes `test_sync.py`'s own tests, not readers elsewhere.

## What Changes

- `_materialize()` in `scripts/sync_shared.py` writes atomically: content goes to a temporary file in the destination's directory, then `os.replace()` swaps it into place. Readers see either the old or the new content, never a truncated file.
- No behavior change otherwise: same output, same `synced <src> -> <dst>` lines, same drift-check semantics. The atomic write also hardens the pre-commit hook path (an interrupted sync no longer leaves a half-written generated copy).

## Capabilities

### New Capabilities

(none — tooling fix, `skip_specs: true`)

### Modified Capabilities

(none)

## Impact

- `scripts/sync_shared.py` (`_materialize`), user-side constraints apply (stdlib only — `os.replace` and `tempfile` qualify).
- Flaky failure in `uv run poe test-fast` disappears; verified by repeated runs.
