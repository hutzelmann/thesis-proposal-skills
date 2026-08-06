## 1. Gate

- [x] 1.1 Add `tests/unit/data/pinned_sentences/proposal-import--continuation.txt` holding the continuation sentence verbatim, and confirm `uv run pytest tests/unit/test_pinned_sentences.py` fails on it — the pin exists before the prose it guards, so the gate is proven to bite

## 2. Prose

- [x] 2.1 Extend `## Wrap-up` in `skills/proposal-import/SKILL.md` with the continuation guidance: the markers are the work queue, the notes file's Next Focus ranks them, and the skill that closes them depends on the gap — write for prose, literature-search for a reference shortfall, ideation for absent research questions or method
- [x] 2.2 Confirm the sentence in `SKILL.md` matches the pin byte-for-byte, so `test_pinned_sentences.py` passes without the pin being adjusted to fit a drifted sentence
- [x] 2.3 Verify no wording added here restates or softens the mandate or the purpose block, per the header pattern's scope rule

## 3. Verify

- [x] 3.1 `uv run poe test` green — pinned sentences, header pattern, report offer, and the generated-copy drift check all pass
- [x] 3.2 `openspec validate --all --strict` clean
