# Tasks: repo-presence-and-ci

## 1. Poe tasks + CI

- [x] 1.1 `pyproject.toml`: add `specs = "npx -y @fission-ai/openspec@1.7.0 validate --all --strict"` and `setup` (`uv sync --dev` + `git config core.hooksPath .githooks`)
- [x] 1.2 `.github/workflows/ci.yml` l0 job: replace lint/pytest/drift/validate steps with `uv run poe test`, `uv run poe cov`, `uv run poe specs`

## 2. audit_status.py roster + 404

- [x] 2.1 Derive `SKILLS` from `sorted(skills/proposal-*)` directories; docstring drops "eight"; 404 on fetch records `"unpublished"` for that skill instead of failing the run
- [x] 2.2 L0 tests: roster matches the nine shipped skills; 404 → unpublished entry; other HTTP errors still exit 2

## 3. Contributor surface

- [x] 3.1 `CONTRIBUTING.md`: thin pointer (install uv, `uv run poe setup`, `uv run poe test`; spec-first loop in two sentences; rules live in AGENTS.md)
- [x] 3.2 `.github/PULL_REQUEST_TEMPLATE.md`: checklist — openspec change folder or skip_specs rationale, `poe test` green, fixtures synthetic with `expected.json`, edits to sync sources not generated copies, nothing from `confidential/`
- [x] 3.3 README badge row under title: CI, license, last-commit, skills.sh link

## 4. Doc drift

- [x] 4.1 AGENTS.md: coverage floor 70→78; Commands block gains `poe setup` + `poe specs`
- [x] 4.2 `harness/README.md`: task roster prose gains `review_hollow`, `ideate_probing`, `troubleshoot_model_rung`

## 5. Private-path hygiene (added mid-implementation on user request)

- [x] 5.1 No committed file outside the immutable `openspec/changes/archive/` names the private local proposals directory; rule prose refers to it by role. Guard test in `test_repo_conventions.py` reads the names from `.git/info/exclude` at runtime, so the test never names them either (skips on machines without the exclude entries). Archive mentions are write-protected — flagged to the user for a separate decision.

## 6. Verify

- [x] 6.1 `uv run poe test` green; `uv run poe cov` above floor; `uv run poe specs` green locally
