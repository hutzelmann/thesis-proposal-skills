# Tasks

## 1. Skill prose

- [x] 1.1 `skills/proposal-supervise/SKILL.md`: full letter→feedback sweep — description, purpose, mandate ("the letter never commits" → "the feedback never commits", etc.), curate section (`<slug>-feedback.md`, "## Curate the feedback"), wrap-up (three artifacts; review referred to as the review, never feedback); update the mandate pin `tests/unit/data/skill_mandates/proposal-supervise.txt` identically.
- [x] 1.2 `skills/proposal-supervise/references/getting-started.md`: heading "for the feedback letter" → "for the feedback" (blurb content untouched).
- [x] 1.3 Direct Purpose edit in `openspec/specs/skill-supervise/spec.md`: drop "letter" and the stale "continuable artifact" clause.

## 2. Troubleshoot collector

- [x] 2.1 `collect.py`: glob `-letter.md` → `-feedback.md`; report line "supervise letter" → "supervise feedback"; docstring.
- [x] 2.2 `tests/unit/test_troubleshoot_collect.py`: letter file names → feedback.

## 3. Harness

- [x] 3.1 `l1_checks.py`: `verdict_supervise_letter` → `verdict_supervise_feedback`, `verdict_supervise_letter_contract` → `verdict_supervise_feedback_contract`; docstrings/explanations letter→feedback (keep "no numbered points" style messages otherwise).
- [x] 3.2 `skill_evals.py`: `supervise_letter_files` → `supervise_feedback_files`, `supervise_letter` → `supervise_feedback_text`, glob `ws/*-feedback.md`; scorer `supervise_l1_letter` → `supervise_l1_feedback` (decorator + function).
- [x] 3.3 `claude_runner.py`: `letter_files` → `feedback_files`, glob, scenario key `"letter"` → `"feedback"`, comments.
- [x] 3.4 `eval_export.py`: scorer map key; expected_output wording. Regenerate `evals.json`.
- [x] 3.5 `tests/unit/test_eval_wiring.py` pins; `tests/unit/test_supervise_verdicts.py` (imports, names, LETTER const → FEEDBACK, docstrings).

## 4. Docs

- [x] 4.1 `README.md`: table row ("draft feedback", drop "letter"); supervise paragraph — reword from current SKILL.md, removing the stale "attaching the normalized file" sentence.
- [x] 4.2 `harness/README.md` supervise task description; `tests/fixtures/README.md` s01 line.

## 5. Verification

- [x] 5.1 `uv run poe test` green; `openspec validate --all --strict` green.
- [x] 5.2 Sweep: `grep -rn "letter" skills/ harness/ tests/unit/ README.md openspec/specs/` shows no student-facing-artifact "letter" left (LaTeX `letterpaper` in the publish template and unrelated words exempt).
