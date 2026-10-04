# Proposal

## Why

Isolated runs log the operator out. The dev runner's `--isolated` mode and the routing rig both run the host against a temporary `CLAUDE_CONFIG_DIR` that holds a symlink to the operator's `~/.claude/.credentials.json`. When the host refreshes an expired access token, it writes the new credentials by atomic replace. That replaces the symlink with a regular file inside the temporary directory, so the source file is never updated. The refresh also rotates the refresh token. The new one is deleted with the temporary directory, and the source keeps a refresh token the server has already invalidated. From then on, every run fails until the operator logs in again, isolated or not.

Measured on 2026-10-04 (host 2.1.284):

- **Incident.** The stored access token had expired at 04:29Z. At 19:34Z an agent started five isolated runs within 45 seconds. The first one refreshed and passed. The four others failed with `Failed to authenticate: OAuth session expired and could not be refreshed` at 0 USD. The source file's mtime did not change.
- **Probe.** An isolated run was linked to a scratch copy of the credentials with its expiry set to the past. Before the run, the link was a symlink. After the run, it was a regular file with mode 0600, a rotated refresh token and a new expiry, and the scratch source had not been written.
- **Recurrence.** Desktop-app sessions get their login from the app (`CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH=1`) and never refresh the stored file. The first isolated run after the stored token expires is therefore the one that refreshes it. The token lives about 8 hours, so this happens again after every expiry. An ambient run on 2026-10-03 failed the same way.

The host's refresh lock lives in the config directory (`.oauth_refresh.lock`). Two isolated runs therefore never serialize their refreshes, either with each other or with an ambient session.

## What Changes

- **Refreshes are written back.** While an isolated configuration links the stored login, the harness watches the link. When the host replaces it with credentials that expire later than the source, the harness writes them back to the source atomically with owner-only permissions, then restores the link. It checks once more when the run ends. Credentials that are not newer are never written.
- **Refreshes are serialized.** A run that starts with a stored token that is expired, or close to expiring, first takes a short-lived claim beside the source. Concurrent runs wait a bounded time for the refreshed login to be written back, then proceed. If the wait runs out, they refuse with a message. They never fall back to the ambient configuration.
- **Long-lived tokens skip the link.** When `CLAUDE_CODE_OAUTH_TOKEN` is set, which is the token `claude setup-token` issues, the isolated configuration links no credentials. The child authenticates from the environment, and there is nothing to refresh or strand.
- **A dead login gets a clear instruction.** When a run fails on authentication, the dev runner's failure message tells the operator to log in again: run `claude` and enter `/login`. The rig's missing-credentials refusal uses the same wording.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`:
  - *Isolated measurement environment* gains the login-keeping rules: write-back, serialized refresh, and a long-lived token in place of the link.
  - *Dev-runner cost and helper-agent telemetry* gains the re-login instruction on authentication failures, and its isolated-run scenario covers configurations without linked credentials.

## Impact

- `harness/host_login.py` (new): stored-login helpers — expiry reading, write-back, the refresh claim, and the link keeper.
- `harness/routing.py`: `prepare_config` skips the link when a long-lived token is present, and a new `isolated_config` context manager prepares, keeps and removes the configuration. Both the rig and the runner use it.
- `harness/claude_runner.py`: uses `isolated_config`. `host_failure` appends the re-login instruction.
- `tests/unit/test_host_login.py` (new) simulates the host replacing the symlink, plus additions to `tests/unit/test_dev_runner_probe.py`.
- `harness/README.md`: the isolated-mode note documents the long-lived token option.
- No user-side skill files, no new dependencies.
