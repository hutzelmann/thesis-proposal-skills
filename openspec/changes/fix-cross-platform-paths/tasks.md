## 1. Fix the defect

- [x] 1.1 In `scripts/sync_shared.py`, render the JSON header value through `.as_posix()` and note in a comment that the header must not vary by host OS.
- [x] 1.2 Render the `.py` header comment path through `.as_posix()`.
- [x] 1.3 Render the drift list entries and the sync log line through `.as_posix()`.
- [x] 1.4 Confirm `python3 scripts/sync_shared.py --check` still passes and no generated copy changes on this host.
- [x] 1.5 Fix the two correctness sites the new Windows job would otherwise fail on: the `SUBPROCESS_ALLOWED` comparison in `tests/unit/test_audit_invariants.py` and the package-file dict keys in `harness/claude_runner.py`.
- [x] 1.6 Fix the remaining display and test-id sites in `harness/report.py`, `harness/routing.py`, `tests/unit/test_anonymity_guard.py`, `tests/unit/test_skill_header_pattern.py` and `tests/unit/test_repo_conventions.py`, so the rule needs no exception list.

## 2. Gate the class

- [x] 2.1 Add a convention test to `tests/unit/test_repo_conventions.py` that walks `harness/`, `scripts/`, `skills/*/scripts/` and `tests/`, and fails where a `relative_to(...)` result is stringified — in an f-string or via `str()` — without `.as_posix()`.
- [x] 2.2 Leave pure `Path` uses of `relative_to` unflagged: demanding `.as_posix()` on a path never turned into text would be wrong.
- [x] 2.3 Make the test parametrize over files (one failure names one file) and add a coverage guard, matching the style of the existing convention tests.
- [x] 2.4 Verify the test fails against the pre-fix source and passes after it.

## 3. Widen the net

- [x] 3.1 Add a `l0-windows` job to `.github/workflows/ci.yml` on `windows-latest` running `uv run poe test-fast`.
- [x] 3.2 Confirm the job's steps do not assume POSIX shell syntax or the pandoc/typst toolchain.

## 4. Verify

- [x] 4.1 `uv run poe test` green.
- [x] 4.2 `openspec validate --all --strict` green.
