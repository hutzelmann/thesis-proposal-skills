# Tasks

## 1. The waiter test races no writer

- [x] 1.1 Confirm the root cause. Verify: a forced interleaving (the holder truncates the stored login, the waiter polls, then the holder writes) makes `acquire_claim` return None at once and leaves `''` to read. Every production credential write goes through `_write_private` (`mkstemp` beside the resolved target, `os.replace`), and nothing else in `harness/` writes a `.credentials.json`.
- [x] 1.2 `test_waiter_proceeds_with_the_refreshed_login`: the holder waits on an `Event` set when the waiter fails to take the claim, writes back through `host_refresh` + `settle`, and is joined; the test asserts the write-back happened. Verify: the test passes 50 of 50 separate runs, and `tests/unit/test_host_login.py` passes under `-n 8`.

## 2. The judge's child is closed on every path

- [x] 2.1 `claude_cli.run_child` runs inside `async with process`, so the pipes are closed after the child is reaped. Verify: the grandchild probe reports no `ResourceWarning` after the fix, and the five warnings of the Windows log (subprocess transport, two pipe transports, two pipe files) before it.
- [x] 2.2 Add `test_a_stopped_child_leaves_no_pipe_to_the_collector` (a grandchild holds the pipes; `error::ResourceWarning`; the grandchild is killed afterwards), and a `collected` fixture that runs `gc.collect()` at teardown of every test that spawns a real child. Verify: the new test errors with the unclosed-transport warnings against the old `run_child` and passes with 2.1; it passes 50 of 50 separate runs, as does `test_rejudge_of_a_stream_without_init_records_the_cli_version_as_none`.

## 3. Gate

- [x] 3.1 `uv run poe test` green; `openspec validate fix-flaky-l0 --strict`.
