# Tasks

## 1. Sync map

- [x] 1.1 Add `skills/proposal-customize/references` to the `shared/structure.json` destination list in `scripts/sync_shared.py`, with a rationale comment matching the style of the existing entries (customize reproduces default lists and branch ids verbatim, and its shipped guidelines.md points at the file).

## 2. Materialize

- [x] 2.1 Run `python3 scripts/sync_shared.py` so the generated copy `skills/proposal-customize/references/structure.json` and the regenerated `.gitattributes` block land.

## 3. Verify

- [x] 3.1 Run `uv run poe test` (includes the `--check` drift gate) and confirm green.
- [x] 3.2 Confirm `skills/proposal-customize/SKILL.md` line 63 and the shipped `references/guidelines.md` now name a file present in the installed skill — no wording change needed.
