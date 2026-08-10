## 1. Script

- [x] 1.1 Add `--force` to `publish.py`'s argument parser, documented as applying to the hand-in export.
- [x] 1.2 In the `--handout` branch, compare the rendered export against the existing file before writing.
- [x] 1.3 Refuse on a differing file: print the file name and the `--force` hint to stderr, return a non-zero exit code, write nothing.
- [x] 1.4 Write silently when the content is identical, or when the file is absent, or when `--force` is given.

## 2. Skill

- [x] 2.1 Add one line to `skills/proposal-publish/SKILL.md` under hand-in guidance: relay the refusal, and leave the rename-or-discard decision with the user.

## 3. Tests

- [x] 3.1 L0: writing a fresh handout succeeds and produces the stripped content.
- [x] 3.2 L0: re-running against an unchanged handout succeeds without a refusal.
- [x] 3.3 L0: an edited handout is refused, the file is left byte-identical, and the message names `--force`.
- [x] 3.4 L0: `--force` replaces the edited handout.

## 4. Verify

- [x] 4.1 `uv run poe test` green.
- [x] 4.2 `openspec validate --all --strict` green.
