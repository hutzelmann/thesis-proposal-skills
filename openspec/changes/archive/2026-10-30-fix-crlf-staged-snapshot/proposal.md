## Why

The first CI run after the 2026-10-30 push (`17dd16e` on `develop`, `b6fd9e6` on the OpenSpec bump pull request) failed 9 tests on `l0-windows`, and only there. Since `decide-swap-claim-scope` (`cec14a5`), the dev runner's verdicts read the proposal the run was given from a byte snapshot that `stage()` takes. That keeps a fixture edited during a run from moving a verdict. `staged_original` and `staged_earlier_round` decode that snapshot with `bytes.decode`, while the run's output is read with `read_text`, which reads any line ending as `\n`. On a checkout with CRLF line endings, which the Windows runner has, an untouched proposal therefore differs from its own snapshot. The customize, review and repair verdicts then report "modified the proposal", and the unchanged seed counts as the run's draft and gets graded. A dev run on a Windows checkout would be graded the same wrong way. Linux checkouts are LF, so the Linux gate passed.

## What Changes

- **The snapshot is read as a file reads (harness fix).** `harness/claude_runner.py` decodes the staged bytes with universal newlines, as `read_text` does: CRLF and a lone CR become `\n`. `staged_original` and `staged_earlier_round` use it. The byte snapshot itself is unchanged, and so are `staged_files` and the verdicts that compare bytes with bytes.
- **One test compared written text as bytes (test fix).** `test_the_guard_compares_against_the_bytes_staged_for_the_run` wrote its edited fixture with `write_text`, which writes CRLF on Windows, then compared bytes with `b"edited after staging\n"`. It now writes the bytes it compares.
- **A regression test that runs on Linux.** Snapshot and workspace hold CRLF bytes: the staged original equals the file read back, and an untouched customize workspace is not read as modified.

No spec-level behavior changes: the verdicts behave as their scenarios already state, now on any checkout. Hence `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `harness/claude_runner.py`, `tests/unit/test_dev_runner_probe.py`.
- `l0-windows` is green again; its run after the push is the proof.

Changelog: internal
