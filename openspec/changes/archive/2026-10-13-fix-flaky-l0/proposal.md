## Why

CI run 38388692453 on `43b121b` failed two L0 tests whose code that commit did not touch. Its only change since the green `c47e7cb` was a price edit in `harness/models.toml`, so both failures are flakes. One of them points at a real defect: the judge's child process leaked its pipes.

## What Changes

- **The waiter test raced its own writer (Linux `l0`; test fix).** `test_waiter_proceeds_with_the_refreshed_login` failed with `JSONDecodeError` on an empty file. The test's holder thread slept 0.1 s, then rewrote the stored login in place with `Path.write_text`, which truncates the file before it writes. A waiter polling between the two read no expiry. `needs_refresh` reports "no refresh due" for an unreadable login, so the waiter stopped waiting, and the test then read the empty file. A forced interleaving reproduces it deterministically. Production is not affected. The harness writes credentials only through `_write_private`, which uses a `mkstemp` file (mode 0600) beside the resolved target and `os.replace`. The host writes its refresh by atomic rename (recorded on 2.1.284). A reader therefore sees the old login or the new one, never a partial file. The test now writes back the way the harness does: a simulated host refresh, then `settle`. The holder starts only once the waiter has failed to take the claim, signalled by an `Event` set from a wrapped `take_claim`. The thread is joined, and the test asserts the write-back happened. No sleep is used to synchronize.
- **The judge's child left its pipes to the garbage collector (Windows `l0-windows`; production fix).** `test_rejudge_of_a_stream_without_init_records_the_cli_version_as_none` failed with five unraisable `ResourceWarning`s: an unclosed `_WindowsSubprocessTransport` (`returncode=1`, stdin closed, both reads cancelled) and its two pipes. That test starts no process. It was only where the collector ran. The leak came from `claude_cli.run_child`, which opened the child with `anyio.open_process` and never closed it. On a time limit the child is terminated (exit code 1 on Windows) and reaped, but its pending reads were cancelled when the event loop closed. The pipe transports then stayed open until garbage collection. `filterwarnings = ["error"]` in `pyproject.toml` makes every unraisable warning an error in whichever test the collector happens to run in. A grandchild that holds the pipes after its parent is stopped reproduces the same five warnings on Linux. A real `claude` can leave such a holder, and outside the tests the leak is open descriptors. `run_child` now runs inside `async with process`, so anyio closes stdin, stdout, stderr and their pipe transports on every path, after the child is reaped.
- **L0 coverage that catches the leak on Linux.** The new test `test_a_stopped_child_leaves_no_pipe_to_the_collector` runs `run_child` against a child that starts such a grandchild, under `error::ResourceWarning`, and kills the grandchild afterwards. It fails without the fix and passes with it. A `collected` fixture runs `gc.collect()` at teardown for every test that spawns a real child. A leak then fails the test that opened it, not a later bystander.

No spec-level behavior changes: the refresh claim, the time-limit stop and the re-grade summary behave as their scenarios already state. Hence `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `harness/claude_cli.py` (`run_child`), `tests/unit/test_claude_cli.py`, `tests/unit/test_host_login.py`.
- A judge call, or its `auth status` preflight, no longer leaves open pipe descriptors behind a stopped child.
