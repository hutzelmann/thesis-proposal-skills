# Tasks

## 1. Implement

- [x] 1.1 Add the framing sentence to the finding format in `skills/proposal-review/SKILL.md` (Output section, enumerated-issues bullet): a finding about an exceeded limit or forbidden content phrases its suggestion as what suffices and where the surplus content goes — never only that the content does not belong.
- [x] 1.2 Reword the work-plan point in the `tests/unit/test_supervise_verdicts.py` FEEDBACK fixture to sufficiency framing — the snippet documents itself as mirroring what the instructions produce.
- [x] 1.3 Instrument the rule in `harness/rubrics/review_quality.txt`: PASS requires limit/forbidden-content findings to state what suffices and where the surplus goes.

## 2. Verify

- [x] 2.1 Confirm no pinned sentence or header-pattern test guards the edited bullet (grep `tests/unit/data/` and `tests/unit/test_skill_header_pattern.py` scope); run `uv run poe test`.
- [x] 2.2 Run `openspec validate --all --strict`.
