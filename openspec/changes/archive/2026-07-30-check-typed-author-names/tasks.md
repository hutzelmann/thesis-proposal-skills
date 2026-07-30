## 1. Detection

- [x] 1.1 Extend the narrow metadata extraction in `skills/proposal-check/scripts/check.py` to record, per reference id, the author surnames (`family:` with any non-dropping particle, and `literal:` names) alongside the existing author/editor presence flags
- [x] 1.2 Detect an author surname of the cited reference immediately before its citation, in both the bracketed and the author-in-text form, allowing the intervening "et al." / "and X" / "und X" shapes
- [x] 1.3 Emit one warning per occurrence naming the key, the line, and the form to use instead; keep it warning class so the run never fails on it

## 2. Corpus

- [x] 2.1 Run the new check across every fixture; treat any hit as a real defect in that fixture and fix the fixture rather than pinning the warning in its oracle
- [x] 2.2 Re-verify every `expected.json` oracle against the script

## 3. Tests

- [x] 3.1 Warning fires for a surname before a bracketed citation
- [x] 3.2 Warning fires for a surname before an author-in-text citation, which renders the name twice
- [x] 3.3 No warning for a sentence ending in a proper noun unrelated to the cited reference's authors
- [x] 3.4 No warning for the correct author-in-text form, and none for a surname that belongs to a different reference than the one cited
- [x] 3.5 The warning never changes the exit code

## 4. Rule wording

- [x] 4.1 Widen the citation-form rule in `shared/guidelines/guidelines.md` and `skills/proposal-write/SKILL.md` to cover the possessor case surfaced by the corpus sweep, then run `python3 scripts/sync_shared.py`

## 5. Verification

- [x] 5.1 `uv run pytest` green (113 passed)
- [x] 5.2 `uv run ruff check .` clean
- [x] 5.3 `openspec validate --all --strict` passes
