# Tasks: troubleshoot-prefilled-issue-url

## 1. SKILL.md delivery step

- [x] 1.1 Rewrite the issue bullet in "Delivering it": construct the prefilled URL (`issues/new?template=skill-defect.yml` + URL-encoded `skill`, `rung`, `what_happened`, `self_reported` from the filled report.md), name `measured`/`script_output`/`repro` as paste-in, restate that the user opens/reviews/submits and the skill files nothing
- [x] 1.2 Confirm pinned prose untouched: mandate paragraph (`tests/unit/data/skill_mandates/proposal-troubleshoot.txt`) and report-offer rules unaffected

## 2. Verify

- [x] 2.1 `uv run poe test` green; `openspec validate --all --strict` green
