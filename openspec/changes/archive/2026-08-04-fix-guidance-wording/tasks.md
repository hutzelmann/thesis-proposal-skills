## 1. Guidance source

- [x] 1.1 `shared/guidelines/guidelines.md` line 68 (Prototype Implementation): `explicitly which requirements are neglectable` → `explicitly which requirements are out of scope`
- [x] 1.2 `shared/guidelines/guidelines.md` line 69 (Theoretical Analysis): `and what is neglectable` → `and what is out of scope`
- [x] 1.3 `shared/guidelines/guidelines.md` line 15: `decide for one and stick to it` → `decide on one and stick to it`
- [x] 1.4 `shared/guidelines/guidelines.md` line 82: `Especially the introduction and the contribution section must ground their claims` → `The introduction and the contribution section in particular must ground their claims`
- [x] 1.5 `shared/guidelines/guidelines.md` line 4: `it may un-forbid sections listed as forbidden here` → wording without the coinage
- [x] 1.6 `shared/guidelines/guidelines.md` line 22: `the channel you hand the proposal in through` → `the channel you submit it through`
- [x] 1.7 `shared/guidelines/guidelines.md` line 98: heading `Quality Checklist Before Handover` → `Quality Checklist Before Hand-In`
- [x] 1.8 Run `python3 scripts/sync_shared.py`; confirm `--check` clean

## 2. Skills

- [x] 2.1 `proposal-import/SKILL.md` line 42: the TODO template in the shape block — `which requirements are neglectable` → `which requirements are out of scope`
- [x] 2.2 `proposal-customize/SKILL.md` lines 26 and 32: replace both `un-forbid` uses
- [x] 2.3 `proposal-write/SKILL.md` line 16: replace `un-forbidding allowed`; line 62: retarget the cross-reference from `handover checklist` to the renamed heading
- [x] 2.4 Grep the whole `skills/` tree for surviving `neglectable`, `un-forbid`, `handover` outside generated copies

## 3. Spec prose

- [x] 3.1 `openspec/specs/guidance-model/spec.md`: replace `un-forbidding a default-forbidden section is allowed` with the new wording. Terminology only — the requirement, its scenarios, and its behavior stay exactly as they are

## 4. Fixtures

- [x] 4.1 Replace `neglectable` in the six English fixtures: `f06-prototype-testbed`, `f07-network-pathfinding`, `f16-figures-import`, `f19-drift-alert-validity` (two occurrences), `f20-timeline-gantt`, `w03-snowball-seed`. Reword per sentence rather than substituting mechanically — several read `X is neglectable`, which becomes `X is out of scope`, but others need the surrounding clause adjusted
- [x] 4.2 Leave the German fixtures alone: `f04` and `f11` use `vernachlässigbar`, which is correct German for deliberately omitted scope and is the word the broken English term was calqued from
- [x] 4.3 Confirm no `expected.json` needs changing — the term only ever appears in body prose, never in a pinned error

## 5. Out of scope, deliberately

- [x] 5.1 Do not touch `docs/demo/harvest.log`. It records real session output, including both the original wording and the model's own correction of it; editing it would falsify the audit trail that `docs/demo/README.md` requires

## 6. Verification

- [x] 6.1 `uv run pytest`
- [x] 6.2 `uv run ruff check .`
- [x] 6.3 `python3 scripts/sync_shared.py --check`
- [x] 6.4 `openspec validate --all --strict`
- [x] 6.5 Final grep: no `neglectable` and no `un-forbid` anywhere outside `docs/demo/harvest.log` and the archived change folders
