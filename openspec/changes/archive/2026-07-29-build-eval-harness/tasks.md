# Tasks: build-eval-harness

## 1. Harness

- [x] 1.1 `harness/rubrics/`: judge templates (RQ quality, review quality, Socratic compliance)
- [x] 1.2 `harness/skill_evals.py`: task factory (sandbox staging, agent solver, L1 artifact scorers, L2 rubric scorers) with tasks `write_from_seed`, `review_fixture`, `check_report`
- [x] 1.3 Unit tests for pure scoring helpers

## 2. Prove it

- [x] 2.1 Smoke-run: three scored end-to-end runs completed (DeepSeek ×2, Haiku ×1); harness fixed twice from findings (transcript-wide report scan, byte-identity assert, neutral framing). Post-fix passing run still to demonstrate — command in harness/README.md
- [x] 2.2 Document run commands in harness/README.md (dev runner + authoritative matrix)
- [x] 2.3 Full pytest green; archive; commit
