# Tasks — adopt-expose-template

## 1. Skeleton (guidance-model)

- [x] 1.1 Replace the four canonical sections in `shared/structure.json` with the template's seven, en + de
- [x] 1.2 Prepend `Use Case Definition` to all eight methodology branches; align Controlled Experiment to the template's Independent Variables / Dependent Variables / Procedure and add Statistical Analysis
- [x] 1.3 Remove work-plan, timeline, milestone, and expected-results patterns from `forbidden_heading_patterns`; keep supervisor, chapter-outline, deliverables, confidentiality
- [x] 1.4 Raise `min_references` to 10; add `research_questions.max_count = 3`
- [x] 1.5 Implement the `max_count` rule in `check.py` (the only check change — the methodology heading kept its `<prefix>: {methodology}` shape, so that logic is untouched)
- [x] 1.6 Rewrite `shared/guidelines/guidelines.md`: per-section guidance for all seven, Objectives-vs-RQ distinction, related-work clustering, work-plan week-granularity rule, expected-results honesty rule, title-page metadata, abbreviations. Mirror every title verbatim (`test_structure_drift.py` is the gate)

## 2. Publish (skill-publish)

- [x] 2.1 Vendor the template as `templates/expose/expose.tex.in` with placeholders, plus `templates/expose/images/thiRGB.jpg`; make the glossary machinery conditional so a source without abbreviations emits no `glossaries` package
- [x] 2.2 New `scripts/expose.py`: metadata extraction, CSL-YAML → BibTeX, markdown → LaTeX (headings, lists, tables, figures, emphasis, inline code, citations), Gantt rendering, title-page substitution. Stdlib only
- [x] 2.3 Strip the branch name off the methodology heading so the rendered document shows a plain `Methodology`
- [x] 2.4 Fix citation keys swallowing trailing sentence punctuation (`@Key.` cited `Key.`, which bibtex could not resolve)
- [x] 2.5 Rewire `publish.py`: project is the default, `--pdf` the pandoc preview, `--handout` unchanged; sync `structure.json` into `proposal-publish/references/`
- [x] 2.6 Verify by compiling: `pdflatex → bibtex → makeglossaries → pdflatex ×2` on an English and a German fixture, both clean of undefined citations and references

## 3. Skills

- [x] 3.1 `proposal-publish/SKILL.md`: Overleaf workflow, regeneration warning, title-page prerequisites
- [x] 3.2 `proposal-write`: seven sections, metadata fields, RQ cap, work-plan week ranges, ten-reference minimum
- [x] 3.3 `proposal-import`: seven-section mapping incl. the old-shape mapping, title-page relocation, work plan and expected results mapped rather than stripped
- [x] 3.4 `proposal-review`: Objectives-vs-RQ, related-work clustering, expected-contributions honesty, work-plan feasibility
- [x] 3.5 `proposal-ideate` and `proposal-customize`: seed shape and new default values

## 4. Corpus

- [x] 4.1 Mechanical restructure: rename headings, move Related Work after the RQ section, insert Use Case Definition
- [x] 4.2 Write Objectives, Expected Contributions and Results, Work Plan and Schedule, and Use Case Definition for every compliant fixture, and raise each to ten cited references
- [x] 4.3 Regenerate every oracle from actual check output; review each for whether the seeded defect still means what the blueprint says
- [x] 4.4 Restore `f15`'s missing-blank-line defect, which the restructure script had silently repaired
- [x] 4.5 Make `f04` near-canonical again so its four sub-questions trip the new `max_count` rule — otherwise no fixture covers it
- [x] 4.6 Rebuild `w02` from `f00` and invert its override: it now forbids a heading the default permits and raises the minimum to 14
- [x] 4.7 Update the semantic notes of the ten fixtures whose defect set changed meaning, and rewrite `tests/fixtures/README.md`

## 5. Tests and harness

- [x] 5.1 New `tests/unit/test_expose.py` — 19 tests over the generator, including the punctuation-in-citation regression and the Gantt degradation path
- [x] 5.2 Invert the two override tests in `test_check.py`
- [x] 5.3 Fix the harness import scorer: a dropped work plan is now the failure, not a kept one; title-page data is checked against the body rather than the whole file

## 6. Verification

- [x] 6.1 `uv run pytest` — 89 passed, 1 skipped
- [x] 6.2 `uv run ruff check .` — clean
- [x] 6.3 `uv run python scripts/sync_shared.py --check` — in sync
- [ ] 6.4 `openspec validate --all --strict` — **not run**: the CLI is not installed in this environment. Validate before archiving.

## 7. Deferred

- [ ] 7.1 Regenerate the `f03`, `f09`, `f11`, `f16` PDF renderings (needs pandoc + typst; no automated test consumes them)
- [ ] 7.2 Re-record `docs/demo/` against the exposé workflow — the screenshots still show the four-section flow and the old PDF build. `f19`, derived from that session, is meanwhile serving as the legacy-shape oracle
