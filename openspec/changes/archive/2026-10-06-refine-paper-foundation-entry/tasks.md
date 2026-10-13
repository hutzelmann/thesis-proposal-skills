# Tasks

## 1. Skill text and pins

- [x] 1.1 Rewrite step 1 of the paper bullet in `skills/proposal-ideate/SKILL.md`: sections named only and never summarized; text-file range of front matter, the slice headings' line ranges and the introduction's closing paragraphs; PDF "use nothing from the Method or Results part"; per-section fallback as a statement. Update `proposal-ideate--paper-slice.txt`. Verify with `uv run pytest tests/unit/test_pinned_sentences.py`
- [x] 1.2 Rewrite step 2: mirror the student's own words for how the thesis relates to the paper; Future Work never laid out as options, recommended, or restated before the student's answer points at an item. Update `proposal-ideate--paper-axis.txt`. Verify with the same test
- [x] 1.3 Rewrite step 3: the method-only gloss, grounding "Only then … never on the paper's own title", and one sentence for the re-run rule. Update `proposal-ideate--paper-transfer.txt`. Verify with the same test
- [x] 1.4 Change the metadata-block bullet in `## Ending — seeding` to "starter entries found during grounding or fetched at seeding". Verify by re-reading it against the "Seeds the proposal file" delta
- [x] 1.5 Record the body word count before and after in `measurement.md`, and verify `uv run pytest tests/unit/test_skill_frontmatter.py tests/unit/test_skill_header_pattern.py` passes. Result: 3617 before, 3667 after the review fixes, 3673 after D6; ceiling 4286

## 2. Harness

- [x] 2.1 Add "I don't have a supervisor or research group yet." to the `ideate_paper_foundation` request in `harness/claude_runner.py`, and assert in `tests/unit/test_paper_foundation.py` that the request answers every preamble item. Verify with `uv run pytest tests/unit/test_paper_foundation.py`
- [x] 2.2 Reword the verdict's file scope in `harness/README.md` to "a top-level markdown file the run produced", with no code change. Verify by comparing the wording with `workspace_markdown()` and the testing-harness delta

## 3. Gate and measurement

- [x] 3.1 `uv run poe test` and `uv run poe specs` exit 0, and `openspec validate refine-paper-foundation-entry --strict` passes
- [x] 3.2 One sonnet dev run, `uv run poe dev ideate_paper_foundation --model sonnet --isolated --keep --max-budget-usd 2`, under the unchanged verdict. Record PASS or FAIL, cost, the tool calls that touched the paper, and the question asked in `measurement.md`. On a FAIL, diagnose whether the wording or the verdict is at fault and fix it once, without re-running in a loop. Result: FAIL ($0.084): it read exactly the narrowed range, then re-asked the axis question behind a second question mark. The wording was at fault: fixed once per design D6, with the pin, the delta and an L0 failure case, and not re-run
- [x] 3.3 After the D6 fix, `uv run pytest tests/unit/test_pinned_sentences.py tests/unit/test_paper_foundation.py tests/unit/test_skill_frontmatter.py` passes and `openspec validate refine-paper-foundation-entry --strict` passes
- [x] 3.4 Archive with `openspec archive refine-paper-foundation-entry -y`, check that the synced main specs keep every prior scenario, and re-run `uv run poe test` and `uv run poe specs`
