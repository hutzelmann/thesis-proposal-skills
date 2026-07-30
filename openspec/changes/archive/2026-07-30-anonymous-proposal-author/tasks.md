## 1. Gate on the citation change

- [x] 1.1 Confirm `render-author-in-text-citations` is fully implemented and archived (`openspec/changes/archive/`); do not start any task below before it is
- [x] 1.2 Re-baseline `specs/skill-check/spec.md` in this change onto the archived "Warning-class pattern checks" text (it gains the authorless-`@key` warning), keeping the `author:` key warning and the no-name-regex sentence
- [x] 1.3 `openspec validate anonymous-proposal-author --strict` passes after the re-baseline

## 2. Guidance source of truth

- [x] 2.1 `shared/guidelines/guidelines.md`: add the author's own name to the forbidden-content list, next to supervisor names
- [x] 2.2 `shared/guidelines/guidelines.md`: add the one sentence stating the writer is identified outside the document (hand-in channel, upload form, filename), and that a program requiring a named title page is a workspace-`guidelines.md` prose override
- [x] 2.3 Run `python3 scripts/sync_shared.py` and confirm `--check` is clean (re-materializes write, review, customize, ideate copies)

## 3. Format contract in the skills

- [x] 3.1 `skills/proposal-ideate/SKILL.md:46`: drop `author` and the `[TODO: add author]` placeholder from the seeded metadata block
- [x] 3.2 `skills/proposal-write/SKILL.md:8`: drop `author` from the stated key list
- [x] 3.3 `skills/proposal-import/SKILL.md:8`: drop `author` from the stated key list; add the writer's name to the strip list at `SKILL.md:22`, and to what the removal note reports
- [x] 3.4 Grep the remaining skills for `author` used as a metadata key (not as a citation/reference field) and clear any straggler

## 4. Check rule

- [x] 4.1 `skills/proposal-check/scripts/check.py`: warn when the metadata block declares an `author` key, with the wording ``author: found — proposals are anonymous by default; remove it unless your program requires a named cover page``
- [x] 4.2 Confirm the warning lands in the warning bucket only — never an error, never a non-zero exit
- [x] 4.3 `skills/proposal-check/SKILL.md`: note in the limitations list that writer names in body prose are not detected mechanically

## 5. Fixtures and oracles

- [x] 5.1 Remove the top-level `author:` line from all 22 fixture proposals except `tests/fixtures/f15-format-broken/broken-format.md`, which keeps `Erika Musterfrau` as the deliberate tripwire (leave every `author:` inside `references:` entries untouched)
- [x] 5.2 `tests/fixtures/f15-format-broken/expected.json`: add the author warning
- [x] 5.3 Re-verify every other fixture's `expected.json` against `check.py` and update where the run disagrees
- [x] 5.4 `tests/fixtures/README.md`: record that f15 owns the author-key tripwire

## 6. Tests

- [x] 6.1 `tests/unit/test_format_prose_drift.py`: drop `author` from `CANONICAL_KEYS`, update the "two or more of the five" discovery rule to four, and confirm `test_discovery_finds_known_describers` still finds write, import, ideate
- [x] 6.2 Add the L0 check test: the f15 fixture produces the author warning; a clean fixture produces none
- [x] 6.3 Add the L0 guard test: no `skills/**/SKILL.md`, no publish template, and no fixture except f15 declares a top-level `author:` metadata key
- [x] 6.4 `uv run pytest` green, `uv run ruff check .` clean, `python3 scripts/sync_shared.py --check` clean

## 7. Close out

- [x] 7.1 `openspec validate --all --strict` passes
- [ ] 7.2 Commit the change, then archive it (`openspec archive`) and sync the spec deltas into `openspec/specs/`
