## Why

`scripts/sync_shared.py` builds the GENERATED headers it writes into every generated copy by interpolating a `Path` into an f-string. On Windows that renders `skills\proposal-check\references`, so `--check` reports drift on every file in a fresh Windows clone, and a real sync there rewrites the committed headers with backslashes. The drift check is a CI gate and a pre-commit hook, which makes the repository effectively unusable on Windows — while `AGENTS.md` requires the user-side scripts to be cross-platform.

The bug was reported by an external contributor against the `.py` header alone; the repository has since grown the same defect in the JSON header path. Nothing catches the class, and CI runs only on `ubuntu-latest`.

## What Changes

- Render every repository-relative path through `.as_posix()` in `scripts/sync_shared.py`: the JSON header value, the `.py` header comment, the drift list, and the sync log line.
- Fix the same defect at every other site where a relative path becomes a string. Two are correctness bugs rather than cosmetics, and both would fail the new Windows job: `tests/unit/test_audit_invariants.py` compares a path against the POSIX literal in `SUBPROCESS_ALLOWED` (on Windows `publish.py` would be wrongly flagged for `subprocess`), and `harness/claude_runner.py` builds dict keys the verdicts match by name. The rest are display and pytest ids.
- Add a repo-convention test that fails when a `relative_to(...)` result is turned into a string — inside an f-string or via `str()` — without `.as_posix()`, scanning `harness/`, `scripts/`, `skills/*/scripts/` and `tests/`. Pure `Path` comparisons are deliberately not flagged.
- Add a `windows-latest` job to CI running the fast L0 subset, catching the platform differences a source-level rule cannot see (line endings, encoding defaults, `tmp_path` behaviour).

## Capabilities

### New Capabilities

None. Tooling and a defect fix; no user-facing behavior changes.

### Modified Capabilities

None — `skip_specs: true`.

## Impact

- `scripts/sync_shared.py` — four call sites.
- `harness/claude_runner.py`, `harness/report.py`, `harness/routing.py` — one site each.
- `tests/unit/test_audit_invariants.py`, `tests/unit/test_anonymity_guard.py`, `tests/unit/test_skill_header_pattern.py`, `tests/unit/test_repo_conventions.py` — assertion messages and test ids.
- `tests/unit/test_repo_conventions.py` — one new parametrized convention test plus its coverage guard.
- `.github/workflows/ci.yml` — one new job.
- No skill file, no generated copy, and no fixture changes. Header *content* is unchanged on POSIX hosts, so no generated copy is rewritten by this change.
