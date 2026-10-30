## Why

CI run 39270981381 (`l0-windows`, 2026-10-19, the OpenSpec bump branch) failed `test_keeper_writes_back_while_the_configuration_is_in_use` with `PermissionError: [Errno 13]` while reading the stored login. That branch changed only the OpenSpec pin, and the same tree passed on 2026-10-26, so the test is flaky. The failure can turn any Windows CI run red.

## What Changes

- **The keeper test raced its own writer (Windows `l0-windows`; test fix).** The test polls the stored login with `wait_for(lambda: refresh_token(source) == "refresh-1")` while the keeper thread writes the refresh back through `_write_private`, which calls `os.replace` onto that file. On Windows, opening a file that a concurrent replace is swapping out is refused with `PermissionError` for that moment. POSIX has no such moment, which is why Linux never showed it. `wait_for` let the refusal escape on the first poll that hit the window.
- `wait_for` in `tests/unit/test_host_login.py` treats a `PermissionError` from the condition as "not yet" and polls again. Its last call after the deadline stays unguarded, so a read that is still refused fails the test with the real error instead of a bare `False`.
- A new L0 test pins that contract: a condition refused twice and then true passes.
- Production is not affected. The harness's own readers of the stored login go through `expires_at`, which already treats any `OSError` as "unreadable", and the keeper retries a failed write-back on its next poll and in the exit check.

No spec-level behavior changes: the keeper and the write-back behave as their scenarios already state. Hence `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `tests/unit/test_host_login.py` (`wait_for`, one new test).
- `l0-windows` no longer fails intermittently on this test. The proof is a green Windows run after the push; Linux cannot reproduce the refusal.

Changelog: internal
