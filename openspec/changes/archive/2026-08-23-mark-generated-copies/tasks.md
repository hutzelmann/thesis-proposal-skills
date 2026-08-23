## 1. Generate the attribute block

- [x] 1.1 Add a `GITATTRIBUTES` renderer to `scripts/sync_shared.py` that derives one line per
      destination from `SYNC_MAP` (`<dest-dir>/<source-name> linguist-generated=true merge=ours`),
      sorted, wrapped in `# BEGIN generated (scripts/sync_shared.py)` / `# END generated`
- [x] 1.2 Write the block into `.gitattributes` on a normal run, preserving any hand-written
      lines outside the sentinels; create the file with only the block when it does not exist
- [x] 1.3 Extend `--check` to report a stale or missing block as drift, using the same
      `OUT OF SYNC` reporting path as the file copies

## 2. Merge driver

- [x] 2.1 Register `merge.ours.driver true` in the `poe setup` task alongside `core.hooksPath`
- [x] 2.2 Document the driver in `AGENTS.md` (setup line) so a clone that skips `poe setup`
      knows what it is missing and that it fails open

## 3. Tests

- [x] 3.1 Extend `tests/unit/test_sync.py`: block content matches `SYNC_MAP` exactly (no
      missing destination, no extra line)
- [x] 3.2 Test that hand-written lines outside the sentinels survive a sync
- [x] 3.3 Test idempotency: syncing twice leaves `.gitattributes` byte-identical
- [x] 3.4 Test that `--check` returns non-zero when the block is stale

## 4. Verify

- [x] 4.1 Run `python3 scripts/sync_shared.py`, confirm the only changed file is
      `.gitattributes` and every synced copy is untouched
- [x] 4.2 Confirm each generated line names a file that exists on disk
- [x] 4.3 `uv run poe test` green; `uv run poe specs` green
