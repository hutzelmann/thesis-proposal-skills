## 1. Execution-shape sections

- [x] 1.1 `skills/proposal-reverse/SKILL.md`: insert `## Execution shape` as the first `##` section (above "What you read"): one reader, one record, one writer; never one helper per chapter, harvest item or section; knowledge-cut reason; import sibling in-context is not a helper.
- [x] 1.2 `skills/proposal-import/SKILL.md`: insert `## Execution shape` as the first `##` section (above "The shape you must produce"): one reader, one file; never one helper per section, reference, citation or figure; reordering and personal-data strip need the whole document; source read once.
- [x] 1.3 `skills/proposal-lit-search/SKILL.md`: insert `## Execution shape` as the first `##` section (above "Modes"): scripts gather, you judge the set together and merge alone; never one helper per candidate, source or research question; pairing and key-uniqueness reason.

## 2. Pins

- [x] 2.1 Add whole-section pins `tests/unit/data/pinned_sentences/proposal-{reverse,import,lit-search}--execution-shape.txt`.

## 3. Docs

- [x] 3.1 `harness/README.md` Known limitations: the fan-out bullet names all seven skills.

## 4. Verify

- [x] 4.1 `uv run poe test` green: `test_execution_shape.py` now parametrizes over seven skills; header-pattern and successor pins untouched.
- [x] 4.2 `openspec validate --all --strict` passes.
