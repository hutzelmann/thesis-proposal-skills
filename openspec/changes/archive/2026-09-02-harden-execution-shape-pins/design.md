## Context

See proposal.md — Why. Two pin mechanisms exist: mandates are pinned as whole paragraphs (`tests/unit/data/skill_mandates/`, equality), load-bearing sentences as substrings (`tests/unit/data/pinned_sentences/`, containment). Both are hand-maintained by design (AGENTS.md: a pin generated from the prose it guards would confirm any reword). The execution-shape sections were pinned through the second mechanism by heading plus opening sentence.

## Goals / Non-Goals

**Goals:**

- The whole section is guarded, including the helper-contract paragraph.
- The section's position — first `##` of the body — is guarded.
- A partial pin cannot quietly replace a whole-section pin.
- Coverage extends to a new skill by adding one pin file, with no test edit.

**Non-Goals:**

- No change to the section wording itself.
- No new materialized block: the text differs per skill, and the sync script's anchors would need extending for two files.
- No generalization of the pin test: the equality assertion lives in a dedicated test scoped to execution-shape pins, so the substring semantics of every other pin are untouched.

## Decisions

- **Whole-section pin through the existing substring test, plus an equality assertion in a dedicated test.** The substring test alone accepts a whole-section pin today (strip and `in`), so the pin files simply grow. A pin that is a substring of the section but not all of it would still pass that test, which is the degradation this change closes: `test_execution_shape.py` extracts the section (from `## Execution shape` to the next `## `) and asserts it equals the pin. Alternative: a new `pinned_sections/` directory with its own test — rejected as a third mechanism for four files; the pinned-sentences directory already holds the files and the naming convention (`<skill>--execution-shape.txt`) is the discovery key.
- **Skill set discovered from pin filenames.** The test parametrizes over `pinned_sentences/*--execution-shape.txt`, so the sibling sweep extends coverage by adding a pin. A hard-coded skill list would have to be edited in the same change and would silently exclude a skill whose pin was added but not listed. The test asserts the corpus is non-empty so a glob that matches nothing cannot pass vacuously (the repo's stated rule for parametrized suites).
- **Position asserted as "first `##` heading", not "at a fixed line".** The header region's block count differs per skill (check has two paragraphs after its mandate), so a line number is wrong from the start; the first section heading is the property the design argued for.
- **Spec wording "first section" and "whole section pinned verbatim".** The previous wording promised an opening-sentence pin; a spec that says less than the test enforces would invite loosening the test back to the spec. Four MODIFIED requirements, each restated in full.

## Risks / Trade-offs

- [Every wording tweak now touches two files] → that is the mandate mechanism's stated cost, and the reason a reword shows up as a paired diff under review.
- [A future skill wants the section second, after an even more important one] → the position test fails and the spec has to change with it, which is the review this change wants to force.
- [Whole-section pins are long, so a reviewer skims the diff] → the pins are byte copies; the review question is only whether the SKILL.md change was intended, and the paired diff makes that visible.
