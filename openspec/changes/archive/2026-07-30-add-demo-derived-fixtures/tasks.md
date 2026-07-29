# Tasks: Demo-Derived Fixtures

## 1. Fixture

- [x] 1.1 Copy `drift-alert-validity.md` from the demo scratch workspace into `tests/fixtures/f19-drift-alert-validity/` and verify no personal data (author stays a TODO placeholder)
- [x] 1.2 Write `expected.json`: check exit 0, TODO warnings, semantic notes (open decisions by design, citation inside RQ2 as publish-regression material)
- [x] 1.3 Add the f19 blueprint row to `tests/fixtures/README.md` (provenance: session-derived, see docs/demo/harvest.log)
- [x] 1.4 Confirm the fixture oracle passes: `uv run pytest tests/unit/test_fixture_oracles.py`

## 2. rq-filter regression test

- [x] 2.1 Write `tests/unit/test_rq_filter_citations.py`: pandoc typst-writer + citeproc + rq-filter.lua over a minimal RQ list with a citation; assert `#rq(` wrapping and no unresolved citation keys; skipif pandoc missing
- [x] 2.2 Verify the test fails against the pre-fix filter (git stash or `git show a8127ef^:...` copy) and passes against the current one

## 3. Persona

- [x] 3.1 Read existing `harness/personas/` files and add the demo-student persona (anecdote-driven, delayed-labels pain, no company data) in the same format
- [x] 3.2 Smoke-check `persona_dialogue` picks it up (list/lookup only, no metered eval run)

## 4. Wrap up

- [x] 4.1 `uv run ruff check .` and `uv run pytest` green; commit
