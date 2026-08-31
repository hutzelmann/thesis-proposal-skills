# Tasks

## 1. SKILL.md wording

- [x] 1.1 Reword the `proposal-import` mandate to name the target directory: "Convert an existing proposal document into one `<slug>.md` in the working directory, in the standard format: …" (exact final wording at edit time; the directory statement must sit in the mandate).
- [x] 1.2 Update the pinned mandate copy `tests/unit/data/skill_mandates/proposal-import.txt` to match verbatim (same commit).
- [x] 1.3 Reword both `${CLAUDE_SKILL_DIR}` fallback paragraphs in `skills/proposal-import/SKILL.md` (validate_refs and check invocations) so the fallback names the script's path and states the command still runs from the workspace — the fallback never relocates the work or the output file. (Implementation note: the file carries one fallback paragraph, after the validate_refs command, covering both invocations — that one is reworded.)
- [x] 1.4 Add a sentence to the import SKILL.md making the out-of-workspace source case explicit: the imported file is written into the working directory even when the source document lives elsewhere; nothing is written beside the source.

## 2. Regression pins

- [x] 2.1 Pin the new location sentence under `tests/unit/data/pinned_sentences/proposal-import--output-location.txt` and confirm `tests/unit/test_pinned_sentences.py` picks it up (follow the existing naming/wiring convention in that test).

## 3. Verify

- [x] 3.1 `uv run poe test` green (header-pattern, mandate-pin, pinned-sentence, sync-drift checks all pass).
- [x] 3.2 `openspec validate --all --strict` passes.
- [x] 3.3 Re-read `skills/proposal-supervise/SKILL.md` normalize section against the new import wording — confirm no contradiction and no supervise edit needed. (Supervise's "the file sits in the working directory beside any other proposals there" now matches the import mandate's "in the working directory" — consistent, no edit.)
