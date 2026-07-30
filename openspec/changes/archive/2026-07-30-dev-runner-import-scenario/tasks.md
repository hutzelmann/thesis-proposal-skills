## 1. Share the verdict

- [x] 1.1 Move the pasted source document out of `harness/skill_evals.py` into `harness/sources.py`, importable without the eval framework
- [x] 1.2 Add `verdict_import(proposal_text, filename)` to `harness/l1_checks.py`, preserving the existing assertions exactly: file produced, standard format, no leaked personal or confidential data, no kept timeline heading, no author name typed beside a bracketed citation
- [x] 1.3 Reduce `import_l1()` in `harness/skill_evals.py` to a thin wrapper that discovers the produced file and delegates to `verdict_import()`

## 2. Dev-runner scenario

- [x] 2.1 Make `fixture` optional in `stage()` so a scenario can stage only its skill
- [x] 2.2 Add a `produces` key marking scenarios that judge a file the skill creates; the source document travels inside the request itself, assembled once in `harness/sources.py` so both runners send identical text (no separate `paste` key needed)
- [x] 2.3 Add produced-file discovery to `verdict()` for such scenarios, ignoring workspace files that are not the produced proposal
- [x] 2.4 Register the `import_messy` scenario and route it to `verdict_import()`

## 3. Tests

- [x] 3.1 L0 tests for `verdict_import()`: no file produced, missing metadata block, leaked matriculation number, leaked confidentiality marker, kept timeline heading
- [x] 3.2 L0 test that an author name typed beside a bracketed citation fails the verdict
- [x] 3.3 L0 test that a correctly imported document passes, including one using the author-in-text form

## 4. Documentation

- [x] 4.1 Add `import_messy` to the dev-runner usage in `harness/README.md`

## 5. Verification

- [x] 5.1 `uv run pytest` green
- [x] 5.2 `uv run ruff check .` clean
- [x] 5.3 `openspec validate --all --strict` passes
- [x] 5.4 Ran the dev runner 5× against the real Claude Code binary (haiku, subscription): 3 PASS / 2 FAIL, both verdict paths exercised. The failures are the model reporting a file it did not write — the scenario works; the skill's reliability is the open question
