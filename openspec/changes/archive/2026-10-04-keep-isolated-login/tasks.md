# Tasks

## 1. Failing tests first

- [x] 1.1 Add `tests/unit/test_host_login.py`, which simulates the host's refresh. It starts from a synthetic stored login in `tmp_path`, links to it the way `prepare_config` does, then replaces the link with a newer file through a temporary file and `os.replace`. Cover:
  - a newer replacement is written back with mode 0600 and the link is restored;
  - an older or equal replacement is never written, though the link is restored;
  - an unreadable replacement is left alone;
  - the keeper writes back within a second while the configuration is in use, and the exit check writes back a replacement the poll missed;
  - a long-lived token in the environment makes `prepare_config` link nothing, even without a stored login;
  - the missing-credentials refusal names `/login`;
  - claims: an expired login takes the claim, and the claim is released after write-back; a waiter proceeds once the stored login turns fresh, refuses when the wait ends, and takes over an abandoned claim; a fresh login takes no claim.

  Verify: the new tests fail against the current code.
- [x] 1.2 Add tests to `tests/unit/test_dev_runner_probe.py`. The recorded expired-login result must name `claude` and `/login`; a budget overrun must not. Verify: they fail against the current code.

## 2. Implementation

- [x] 2.1 Create `harness/host_login.py` with the expiry reader, the write-back with re-linking, the refresh claim (acquire, wait, refuse, take over an abandoned claim, release by mark), the keeper thread, the `keep_login(link)` context manager, and the shared re-login instruction. Verify: the tests from 1.1 that target these helpers pass.
- [x] 2.2 In `harness/routing.py`, make `prepare_config` link nothing when `CLAUDE_CODE_OAUTH_TOKEN` is set, reword its missing-credentials refusal, and add `isolated_config(prefix)`. Make `routing.main` use `isolated_config`. Verify: the prepare and isolated-config tests from 1.1 pass.
- [x] 2.3 In `harness/claude_runner.py`, replace the hand-rolled config directory with `isolated_config`, and have `host_failure` append the re-login instruction on authentication failures. Verify: the tests from 1.2 pass, and the existing dev-runner probe tests stay green.

## 3. Documentation

- [x] 3.1 In `harness/README.md`, extend the isolated-mode sentence and the rig's isolation paragraph:
  - refreshes are written back to the stored login and serialized by a claim;
  - `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token` removes the link;
  - an expired login means running `claude` and entering `/login`.

  Update the docstrings in `routing.py` and `claude_runner.py` to match. Verify: by reading them.

## 4. Close

- [x] 4.1 One live check of the fixed path with a single haiku `claude -p`. Link a scratch copy of the stored login with its expiry forced into the past through `isolated_config`. The refresh must be written back to the scratch source and the link restored. The refresh rotates the real refresh token, so the scratch source is then put back in the stored location, as the 2026-10-04 probe did. Record the observation in this change, without token values. Verify: the recorded output.
- [x] 4.2 `uv run poe test` and `uv run poe specs` are green. Verify: their output.
