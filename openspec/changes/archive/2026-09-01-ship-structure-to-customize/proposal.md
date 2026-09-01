# Ship structure.json to proposal-customize

## Why

`skills/proposal-customize/SKILL.md` names `references/structure.json` as the source of the override key paths, and its shipped `references/guidelines.md` points at `structure.json` for the machine-checkable skeleton — but the installed skill ships neither: `scripts/sync_shared.py` materializes `shared/structure.json` into seven skills and proposal-customize is not among them. The gap is not only a dangling file mention. The skill's own workflow requires content that exists only in that file: reproducing the default forbidden heading list minus one entry (lists replace, so the full default list must be retyped verbatim), and naming shipped methodology branch ids to disable or replace them. An installed customize agent has no ground truth for either and would have to guess or read a sibling skill that may not be installed — exactly the situation the packaging spec's synchronized-copy rule exists to prevent.

## What Changes

- `shared/structure.json` gains `skills/proposal-customize/references` as a sync destination in `scripts/sync_shared.py`'s `SYNC_MAP`, with the rationale comment every other destination carries.
- The generated copy `skills/proposal-customize/references/structure.json` and the derived `.gitattributes` entry are materialized by running the sync.
- `skills/proposal-customize/SKILL.md` line 63 needs no rewording: the file it names now exists in the installed skill.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-customize`: the skill SHALL ship the structured guidance data it writes key paths against, so that the exact key paths, default list values, and shipped branch ids it must reproduce are available inside the installed skill.

## Impact

- `scripts/sync_shared.py` (one `SYNC_MAP` entry)
- `skills/proposal-customize/references/structure.json` (new generated copy)
- `.gitattributes` (regenerated block, derived from `SYNC_MAP`)
- No user-facing behavior of other skills changes; check.py and the harness are untouched.
