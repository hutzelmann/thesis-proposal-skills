## 1. Fix the call sites

- [x] 1.1 `skills/proposal-check/SKILL.md` — the check invocation
- [x] 1.2 `skills/proposal-import/SKILL.md` — the verification and reference-validation invocations
- [x] 1.3 `skills/proposal-lit-search/SKILL.md` — the search and snowball invocations
- [x] 1.4 `skills/proposal-publish/SKILL.md` — the build and handout invocations

## 2. Forbid silent degradation

- [x] 2.1 State in each script-bearing skill that a missing script is reported, naming what went unverified, and never replaced by unaided inspection presented as the script's result

## 3. Verification

- [x] 3.1 `uv run pytest` green
- [x] 3.2 `uv run ruff check .` clean
- [x] 3.3 `python3 scripts/sync_shared.py --check` clean
- [x] 3.4 `openspec validate --all --strict` passes
- [x] 3.5 Re-ran on both models: **haiku PASS 5/5**, **sonnet PASS 5/5**, file untouched in both — from 1–2/5 before, where the model reported the script missing and substituted manual inspection. The sonnet measurement additionally required closing the runner's stdin, a separate harness defect tracked on its own
