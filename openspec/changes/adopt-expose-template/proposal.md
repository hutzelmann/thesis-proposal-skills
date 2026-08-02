# Adopt the THI Exposé Template as the Deliverable

## Why

The skills produced a four-section proposal in a shape of their own invention and published it as a compact pandoc PDF. Students at the Faculty of Computer Science do not submit that; they submit an exposé built from the faculty template at <https://github.com/ignacioalvmar/thesis_expose_template>, on Overleaf. Every exposé therefore had to be re-shaped by hand after the skills were done with it, which is precisely the work the skills exist to remove.

The template is not a restyling of the previous output. It defines a different artifact, and three of its required sections were previously forbidden content:

| Template requires | Previous default |
|---|---|
| §7 Work Plan and Schedule, drawn as a Gantt chart | forbidden heading (`timeline`, `work plan`, `milestones`) |
| §6 Expected Contributions and **Results** | forbidden heading (`expected results`) |
| Title page with student ID and both supervisors | forbidden content; stripped on import |
| §3 Objectives, §4 Related Work with thematic clusters | no equivalent section |
| Methodology → Use Case / Independent Variables / Dependent Variables / Procedure | eight branch-specific subsection sets |
| 10–15 sources | `min_references = 3` |
| LaTeX + BibTeX, `natbib`/`dinat`, `glossaries`, `pgfgantt` | pandoc → typst, CSL-YAML |

## What Changes

- **Replace the four-section skeleton with the template's seven sections** in both languages: Introduction and Motivation, Problem Statement and Research Questions, Objectives, Related Work, Methodology: \<Methodology\>, Expected Contributions and Results, Work Plan and Schedule. The rendered document shows a plain "Methodology"; the branch name stays in the source so the check can verify subsections.
- **Prepend `Use Case Definition` to every methodology branch**, which is the template's first Methodology subsection. The template's Independent Variables / Dependent Variables / Procedure set becomes the Controlled Experiment branch — the design it was written for — while the other seven branches keep the subsections their design actually needs, so a literature review is not asked to name its dependent variables.
- **Invert the forbidden list**: work plans, timelines, and expected results are required sections and are removed from it. Supervisor sections, chapter outlines, deliverable lists, and confidentiality markers stay forbidden. Supervisors move to the title-page metadata rather than being stripped.
- **Add title-page metadata fields** (`student_id`, `degree_program`, `supervisor`, `second_supervisor`, `submission_date`) plus an optional `abbreviations` mapping feeding the List of Abbreviations. These are the only permitted location for personal data; the body-text strip rule and the check warnings are unchanged.
- **Raise `min_references` to 10** and **cap research questions at 3**, both from the template's own guidance. The cap is a new mechanical rule.
- **Replace the publish deliverable with an Overleaf-ready LaTeX project**: `expose.tex` with the title page filled and the body rendered, `literature.bib` converted from CSL-YAML, and `images/`. The generator is stdlib-only — no pandoc, no typst, no TeX — so a student with nothing installed can produce it. The work-plan table becomes the template's Gantt chart, degrading to a plain table with a note when rows carry no week range. The old pandoc pipeline survives as `--pdf`, explicitly not the deliverable.

## Capabilities

### Modified Capabilities

- `guidance-model`: canonical structure becomes the template's seven sections; every methodology branch gains Use Case Definition; forbidden content loses work plans, timelines, and expected results and gains an explicit note that they are required; new requirements for the research-question count cap and for the objectives-versus-research-questions distinction.
- `skill-publish`: the deliverable becomes the LaTeX template project, buildable with no toolchain; new requirement for Gantt rendering with a documented degradation path; the engine-resolution and compact-layout requirements are replaced, and the pandoc pipeline is demoted to a preview mode.
- `proposal-file-format`: the metadata block gains the title-page fields and the abbreviations mapping, with personal data confined to it.

## Impact

- `shared/structure.json`, `shared/guidelines/guidelines.md`: rewritten around the template; `structure.json` now also syncs into `skills/proposal-publish/references/`.
- `skills/proposal-check/scripts/check.py`: one new rule (`max_count` for research questions). The methodology-heading logic is unchanged, because the heading template kept its `<prefix>: {methodology}` shape.
- `skills/proposal-publish/`: new `scripts/expose.py` (~350 lines), new `templates/expose/` holding the parameterised `expose.tex.in` and the THI logo, `publish.py` rewired so the project is the default and `--pdf` the fallback.
- `skills/proposal-write|import|ideate|review|customize/SKILL.md`: seven-section shape, title-page metadata, Objectives-versus-RQ judgement, related-work clustering, work-plan and expected-results review dimensions, Overleaf workflow.
- `tests/fixtures/`: every fixture restructured. Compliant fixtures gained Objectives, Related Work, Expected Contributions, Work Plan, Use Case Definition, and enough references to clear the new minimum; defect fixtures kept their prose and had their oracles regenerated. `f04` was made near-canonical again so that the new research-question cap has a fixture that trips it.
- `tests/unit/test_expose.py`: new, 19 tests over the generator. `tests/unit/test_check.py`: the two override tests inverted, since the workspace override now *adds* a prohibition the default permits.
- `harness/skill_evals.py`: the import scorer no longer treats a timeline as content to strip; it now fails an import that drops the work plan instead of mapping it.

## Verification

`uv run pytest` (89 passed, 1 skipped), `uv run ruff check .`, `scripts/sync_shared.py --check`. Beyond the unit tests, the generated project was compiled end to end with the real toolchain (`pdflatex → bibtex → makeglossaries → pdflatex ×2`) for an English and a German fixture: both produce a PDF with no undefined citations or references.

## Known Follow-ups

- `openspec validate --all --strict` was not run — the CLI is not installed in this environment. Spec deltas were authored by hand against the archived format and applied to `openspec/specs/` directly.
- The four fixture PDF renderings (`f03`, `f09`, `f11`, `f16`) remain stale from the previous change and are now doubly so. No automated test consumes them.
- `docs/demo/` and the `f19` fixture derived from it stay in the pre-template four-section shape. `f19` is now the oracle for detecting a legacy-shape exposé, which is a useful role, but the README demo screenshots still show the old workflow and the old PDF output.
- The KOMA-Script deprecation warnings (`bigheadings`, `idxtotoc`, `bibtotoc`) come from the upstream template's `\documentclass` options and were left untouched so the generated document stays faithful to it. They are warnings, not errors.
