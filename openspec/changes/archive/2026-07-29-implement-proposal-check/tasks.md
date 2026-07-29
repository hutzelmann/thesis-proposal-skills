# Tasks: implement-proposal-check

## 1. Script

- [x] 1.1 `check.py`: narrow metadata extraction (trailing block, reference ids, lang) + TOML override loading with merge semantics
- [x] 1.2 `check.py`: mechanical checks per spec (guardrails, sections, methodology, forbidden headings, RQ cross-refs, citations, min_references, TODOs)
- [x] 1.3 `check.py`: warning-class patterns (first person en/de, sentence starts, personal data, confidentiality) + two-bucket report, exit 1 only on mechanical errors

## 2. Skill

- [x] 2.1 `SKILL.md`: frontmatter (name: proposal-check) + instructions (script first, agent pass second, chat-only, advisory)

## 3. Fixtures & tests

- [x] 3.1 `tests/fixtures/f15-format-broken/` per blueprint (missing blank line, boolean key, TODOs, 2 refs, duplicate id)
- [x] 3.2 `tests/fixtures/w02-override-workspace/` (guidelines.md TOML: timeline allowed+required, min_references = 8)
- [x] 3.3 `tests/unit/test_check.py`: f00 clean passes; f15 trips each guardrail; override changes verdicts
- [x] 3.4 `uv run pytest` green; sync check still green; commit
