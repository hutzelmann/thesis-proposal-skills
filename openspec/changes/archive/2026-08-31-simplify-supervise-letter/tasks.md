# Tasks

## 1. Skill prose

- [x] 1.1 Rewrite `skills/proposal-supervise/SKILL.md`: curate section writes `<slug>-letter.md` (no package dir, no attachment copy); disclosure item drops the guideline claim and gains the decisions-stay-yours clause; wrap-up names the three flat artifacts and says the professor delivers the letter as pasted text through their own channel — an email reply or a learning platform's feedback field.
- [x] 1.2 Replace both blurbs in `skills/proposal-supervise/references/getting-started.md` with the agreed one-sentence EN/DE versions (repo link + guide-from-zero nod; no assistants, commands, or prescribed next step).
- [x] 1.3 Check `skills/proposal-supervise/description` frontmatter and `skills/proposal-troubleshoot/SKILL.md` for send-package wording; update where present.

## 2. Troubleshoot collector

- [x] 2.1 In `skills/proposal-troubleshoot/scripts/collect.py`, replace the `<slug>-package/` directory inventory with the `<slug>-letter.md` file inventory (placeholder name, size, hash; no content).
- [x] 2.2 Update the collector's unit tests to the letter-file inventory.

## 3. Harness

- [x] 3.1 In `harness/l1_checks.py`: rename `verdict_supervise_package` → `verdict_supervise_letter_contract`; update docstrings from package to letter vocabulary; `verdict_supervise_no_personal_data` keeps its dict signature with a letter-shaped docstring.
- [x] 3.2 In `harness/skill_evals.py`: replace `supervise_package()` with a letter-file reader; feed the personal-data scorer the letter file; audit the supervise sample request text for attachment/package phrasing.
- [x] 3.3 In `harness/claude_runner.py`: migrate `package_files` and the aggregate call to the letter file.
- [x] 3.4 Update `tests/unit/test_supervise_verdicts.py` to the renamed aggregate and letter-shaped inputs.

## 4. Verification

- [x] 4.1 Regenerate eval projections if `harness/eval_export.py` output shifts (`skills/*/evals/evals.json` drift gate).
- [x] 4.2 `uv run poe test` green; `openspec validate --all --strict` green.
- [x] 4.3 Grep the repo for `send-package`, `-package/`, and "attach" near supervise to confirm no stale reference outside the archive.
