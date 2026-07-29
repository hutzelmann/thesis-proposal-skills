# Tasks: implement-remaining-skills

## 1. Instruction files

- [x] 1.1 proposal-write SKILL.md (guidance-driven, no fabricated sources, surgical refinement, bilingual)
- [x] 1.2 proposal-review SKILL.md (content-only, format-agnostic, `<slug>-review.md` in proposal lang, grammar hint rule)
- [x] 1.3 proposal-ideate SKILL.md (Socratic, literature-grounded via vendored scripts, seeds proposal file, graceful ungrounded mode)
- [x] 1.4 proposal-import SKILL.md (PDF→standard format, personal-data stripping with removal note, figure TODOs, robustness)
- [x] 1.5 proposal-customize SKILL.md (dialog→TOML+prose guidelines.md, conflict validation with consequences)
- [x] 1.6 proposal-publish SKILL.md (optional build, engine order, install guidance, hand-in export, artifact hygiene)

## 2. Publish script

- [x] 2.1 `publish.py`: engine resolution, pandoc pipeline (citeproc + rq-filter + template), docx fallback, `--handout` export, `.gitignore` ensure
- [x] 2.2 L0 tests (offline: resolution logic, handout stripping, gitignore idempotence) + live build smoke on f00

## 3. Verification

- [x] 3.1 Adversarial workflow: each SKILL.md vs. its capability spec; apply confirmed findings
- [x] 3.2 Full pytest + sync check green; archive; commit
