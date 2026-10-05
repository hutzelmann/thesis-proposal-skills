# Proposal

## Why

`--isolated` is documented as measuring the default host, but only the configuration directory is isolated. `run_claude` and the routing rig's `stream_events` build the child's environment as `dict(os.environ, CLAUDE_CONFIG_DIR=...)`. When the runner is started from a Claude desktop-app session, which is how agent sessions run it, the child inherits that session's variables. On 2026-10-04, child transcripts under `~/.claude/projects/-tmp-devrun-*/` recorded `entrypoint: claude-desktop`.

The inherited set is larger than the `CLAUDE*` family. A desktop session on 2026-10-04 exported these variables (names only):

| Kind | Variables |
|---|---|
| Session binding | `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_HOST_SESSION_ID`, `CLAUDE_CODE_CHILD_SESSION`, `CLAUDE_CODE_MESSAGING_SOCKET`, `CLAUDE_CODE_MESSAGING_TOKEN` (a secret), `CLAUDE_PID` |
| Auth path | `CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH`, `CLAUDE_CODE_OAUTH_SCOPES`, `CLAUDE_CODE_ACCOUNT_UUID`, `CLAUDE_CODE_ORGANIZATION_UUID` |
| Host behavior | `CLAUDE_EFFORT`, `CLAUDE_CODE_ENABLE_ASK_USER_QUESTION_TOOL`, `CLAUDE_CODE_REPORT_FINDINGS`, `CLAUDE_CODE_DISABLE_CRON`, `CLAUDE_CODE_EMIT_TOOL_USE_SUMMARIES` |
| Not `CLAUDE`-prefixed | `ANTHROPIC_BASE_URL`, `API_TIMEOUT_MS`, `DISABLE_MICROCOMPACT`, `DISABLE_AUTOUPDATER`, `MCP_CONNECTION_NONBLOCKING`, `MCP_SERVER_CONNECTION_BATCH_SIZE`, `AI_AGENT` |

Each of these can change what an isolated run measures. The effort level, the tool set, compaction, the API endpoint and the auth path all move. The messaging socket and token also hand a session capability to a child that runs with permission prompts skipped.

## What Changes

- **The isolated child gets an allowlisted environment.** A single function builds it, and both callers use it: the dev runner in `--isolated` mode, and the routing rig on every run. The child receives only these:
  - `PATH` and `HOME`;
  - `CLAUDE_CODE_OAUTH_TOKEN`, the long-lived token path;
  - the variables that describe the machine rather than the host: identity and shell, locale, temp directories, XDG base directories, proxy and CA trust, and the Windows process basics;
  - `CLAUDE_CONFIG_DIR`, set to the isolated directory.

  Every other variable is dropped, including names the host may add later.
- **Ambient mode is unchanged.** Without `--isolated`, the runner still inherits the operator's environment, because ambient mode measures the operator's own configuration.
- **No variable value is printed.** The function prints nothing. Its tests use fake values and assert that they never appear in output.
- **Documentation.** The runner's module docstring and `harness/README.md` say that `--isolated` isolates the environment as well as the configuration directory.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: Isolated measurement environment. An isolated child's environment is allowlisted by one shared function, used by the routing rig and the dev runner's isolated mode.

## Impact

- `harness/routing.py`: a new `isolated_env`, used by `stream_events`.
- `harness/claude_runner.py`: `run_claude` uses `isolated_env` when a configuration is given.
- `tests/unit/`: a new L0 test file for the function and both call sites.
- `harness/README.md`, and the docstring of `claude_runner.py`.
- No skill text changes. Verification needs one cheap haiku isolated dev run, and only with the operator's approval.
- Overlap: the unmerged change `keep-isolated-login` on `claude/frosty-elion-54aef7` touches the same call sites. Whichever change merges second resolves the conflict and keeps `isolated_env` at both call sites.
