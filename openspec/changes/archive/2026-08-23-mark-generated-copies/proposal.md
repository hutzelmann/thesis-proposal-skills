## Why

Sixteen files under `skills/` are materialized copies of a `shared/` source, written by
`scripts/sync_shared.py` because skills.sh installs only a skill's own folder and offers no
dependency mechanism. The copies are correct and unavoidable, but they are invisible as
copies during review: PR #2 changed 856 lines, of which roughly 345 were the same 115-line
`check.py` diff replayed into `proposal-import`, `proposal-write`, and `proposal-supervise`.
Forty percent of a review's surface was noise a reviewer has to read to discover it is
noise, and external contributions are now a live flow.

Git already has the mechanism for this: `.gitattributes`. Nothing declares these paths
generated, so GitHub renders them expanded and merges them line by line.

## What Changes

- Add a repository `.gitattributes` that marks every synced copy `linguist-generated=true`,
  so review diffs collapse them by default and they are excluded from language statistics.
- Give the same paths a `merge=ours` driver, so a generated copy never produces a merge
  conflict — the resolution for a generated file is always to regenerate it, never to
  hand-edit a conflict marker into a file whose header says not to edit it.
- Generate the `.gitattributes` entries from `SYNC_MAP` in `scripts/sync_shared.py` rather
  than hand-maintaining a parallel list, and verify them under `--check`. A hand-written
  list would drift the moment a sync destination is added, which is the exact failure the
  file exists to prevent.
- Document the `merge=ours` driver registration in the developer setup path, since a merge
  driver named in `.gitattributes` but unregistered in git config is silently inert.

No user-facing behavior changes: the shipped skill folders, their contents, and the sync
output are byte-identical before and after.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — this is repository tooling and review ergonomics. `.openspec.yaml` sets
`skip_specs: true`.

## Impact

- `.gitattributes` (new, generated).
- `scripts/sync_shared.py` — gains a second output; `--check` covers it.
- `tests/unit/test_sync.py` — coverage for the generated attribute block.
- Developer setup (`poe setup` / `AGENTS.md`) — registers the `merge=ours` driver.
- No change to `skills/`, `shared/`, or anything installed by `npx skills add`.
