# Tasks

## 1. The keeper test rides out a refused read

- [x] 1.1 Confirm the root cause. Verify: in the CI log of run 39270981381 the `PermissionError` is raised by `refresh_token(source)` inside `wait_for`, while the keeper writes back through `_write_private` (`mkstemp` beside the target, `os.replace`). The other keeper tests read the stored login only after the keeper has been joined or after its claim is released, which happens after its last write.
  - 2026-10-30: the log's traceback runs from the test through `wait_for` into `refresh_token` → `Path.read_text` on `stored/.credentials.json`. `test_claim_is_released_once_the_refresh_is_written_back` reads after the claim is gone, and the keeper releases the claim only after `settle` wrote and relinked; with the link restored, `settle` writes nothing more. The remaining reads follow `keep_login`'s exit, which joins the keeper.
- [x] 1.2 `wait_for` in `tests/unit/test_host_login.py` suppresses `PermissionError` from the condition while the deadline has not passed, and leaves its last call unguarded. Add `test_wait_for_rides_out_a_refused_read`: a condition that raises `PermissionError` twice and then holds makes `wait_for` return True. Verify: the new test fails against the old `wait_for` and passes with the new one; `test_keeper_writes_back_while_the_configuration_is_in_use` passes 50 of 50 separate runs on Linux.
  - 2026-10-30: the new test failed against the old `wait_for` (the `PermissionError` escaped from its first poll) and passes with the new one. The keeper test passed 50 of 50 separate runs.

## 2. Gate

- [x] 2.1 `uv run poe test` green; `openspec validate fix-windows-keeper-read-race --strict`. The Windows proof is the `l0-windows` job after the maintainer's push.
  - 2026-10-30: `poe test` 6162 passed, 2 skipped; ruff clean, generated copies in sync, 11 skills conform. `openspec validate --strict` reports the change valid. The `l0-windows` proof is still open; it comes with the push.
