# Tasks: upgrade-dev-runner

## 1. Shared L1 logic

- [x] 1.1 harness/l1_checks.py (pure functions) + skill_evals scorers delegate to it
- [x] 1.2 Unit tests move/extend to cover the pure functions

## 2. Dev runner

- [x] 2.1 claude_runner.py rewrite (fixture staging, .claude/skills install, headless run, L1 verdict)
- [x] 2.2 One live run on the subscription validates the flow

## 3. Docs

- [x] 3.1 harness/README.md: findings log removed, stable notes + dev-runner usage documented
- [x] 3.2 pytest green; archive; commit
