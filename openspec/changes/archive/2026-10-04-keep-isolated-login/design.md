# Design

## Context

`routing.prepare_config` builds the isolated configuration. It writes `{}` settings and symlinks `.credentials.json` to the stored login, and refuses when no stored login exists. Its callers are `routing.main` (one configuration shared by a thread pool of cases) and `claude_runner.main --isolated` (one configuration per run). Both delete the directory when they finish.

Host behavior the design rests on, measured on 2026-10-04 with host 2.1.284 (see proposal.md, Why):

- A refresh writes a new file with mode 0600 by atomic replace. The symlink is gone and the target is untouched.
- The refresh rotates the refresh token.
- `claude auth status` does not refresh an expired token. There is no refresh path without a model call.
- With `CLAUDE_CODE_OAUTH_TOKEN` set and an empty config directory, `claude auth status` reports `loggedIn: true` and `authMethod: oauth_token`.
- The host's refresh lock (`.oauth_refresh.lock`) lives in the config directory.
- Agent sessions launch runs with differing `TMPDIR` values. On 2026-10-04 the runs were launched with `TMPDIR` set to a session scratchpad.

## Goals / Non-Goals

**Goals:**

- No isolated run, interrupted or not, leaves the stored login holding a refresh token the server has rotated out.
- Isolated runs started together after the token expires do not race each other's refreshes.
- Each refusal names its cause, and none falls back to the ambient configuration.

**Non-Goals:**

- Refreshing the stored login when no run needs it. The desktop app never refreshes the stored file, and that stays the operator's business.
- Coordinating with an interactive `claude` that refreshes the same stored login at the same moment. Its lock is internal to the host.
- Making `setup-token` mandatory. It needs an interactive browser login, and it issues a year-long credential the operator then has to keep.
- Env-variable leakage from the launching session into the child. See Risks.

## Decisions

### 1. Keep the link; write refreshes back, then restore the link

A keeper watches the link while the configuration is in use. When the link has become a regular file, the keeper acts on what it finds:

- The file has a later `claudeAiOauth.expiresAt` than the stored login: the keeper copies it to the stored location byte for byte, through a temporary file in the same directory created with mode 0600, followed by `os.replace`. Then it re-creates the link, also by atomic replace.
- The file is no newer: the keeper only re-creates the link.
- The file is unreadable, or the stored login is: the keeper leaves both alone and looks again on the next poll.

The write targets the resolved path of the link target. Writing through a stored login that is itself a symlink, such as a dotfiles link, would repeat the bug one level up.

*Alternative: copy the credentials into the configuration instead of linking them.* That makes a second copy of the secret, and a refresh still strands the source unless it is written back. It would also give up the existing "link, never copy" rule for nothing.

*Alternative: write back only when the run ends.* The stored login would stay stale for the whole run, up to the 600 s default timeout or the length of a full rig sweep. Every other run, and the operator's terminal sessions, would fail meanwhile. The 2026-10-04 runs D and E started 40 s after run A refreshed. They are exactly that case.

Restoring the link keeps the steady state a symlink. Rig cases that start later read the current stored login, and polling stays a single `lstat`.

### 2. Serialize refreshes with a claim file beside the stored login

When the stored token expires within `REFRESH_MARGIN_S` (300 s), a run tries to create `<stored dir>/.devrun-refresh.claim` with `O_CREAT | O_EXCL`. Its content is a mark unique to the run, and a run deletes only a claim that carries its own mark.

- **Holder.** It runs normally. The keeper releases the claim once a write-back has happened, or after `CLAIM_HOLD_S` (60 s) without one, since the host refreshes at its first request, seconds after start. The claim is also released when the run ends.
- **Waiter.** It polls once a second for up to `CLAIM_WAIT_S` (90 s). It proceeds without a claim as soon as the stored login is fresh. It takes the claim itself if the claim has disappeared. When the wait runs out, it refuses.
- **Abandoned claim.** A claim older than `CLAIM_STALE_S` (120 s) was left by a run that died without its `finally`. The next waiter removes it and competes for a new one.

*Alternative: put the lock in the temp directory.* `TMPDIR` differs between the agent sessions that share one login, so such a lock would not be shared. The stored login's own directory is the one place all of them have in common.

*Alternative: refuse at once instead of waiting.* Agents launch runs in parallel batches. Refusing would turn a refresh of a few seconds into failed runs that someone has to relaunch.

*Alternative: refresh before the run in the operator's configuration.* `auth status` does not refresh, as measured. A `claude -p` in the operator's configuration would cost a model call and run the operator's hooks and plugins.

### 3. A long-lived token replaces the link

If `CLAUDE_CODE_OAUTH_TOKEN` is set, `prepare_config` links nothing and the keeper has nothing to do. The child inherits the environment and authenticates from it. Nothing in the configuration can be refreshed, so nothing can be stranded and nothing can race. The README offers this as the preferred setup for heavy isolated use. The design does not depend on it.

### 4. The re-login instruction is keyed on the reason text

`host_failure` appends one shared instruction when the composed message matches `Failed to authenticate`, `OAuth session` or `Not logged in`. The instruction says to run `claude`, enter `/login`, and rerun. The reason text is the only signal the host gives. Since 2026-10-03 the result event has carried it in `result`, with subtype `success`. The missing-credentials refusal in `prepare_config` uses the same instruction and names the long-lived token as the alternative.

### 5. Placement

The helpers go into a new `harness/host_login.py`: expiry reading, write-back and re-linking, the claim, and the keeper. An `isolated_config(prefix)` context manager goes into `routing.py` beside `prepare_config`. It creates the temporary directory, prepares it, keeps the login while the run is in use, and removes the directory. Both callers switch to it. This replaces two hand-rolled create, prepare and `rmtree` sequences that would otherwise each need the keeper wired in.

## Risks / Trade-offs

- **[The harness now writes the operator's credentials file]** → It writes only when the new credentials expire later, by atomic replace with mode 0600, copying the bytes the host wrote verbatim. It never prints, logs or parses beyond `expiresAt`. L0 tests run entirely on synthetic credentials in `tmp_path`.
- **[The host's refresh margin is unknown and may exceed 300 s]** → A run could then refresh without the claim. Write-back still holds, and only two runs refreshing at the same instant could race.
- **[Race between taking over an abandoned claim and creating a new one]** → The window is microseconds and needs a claim older than 120 s, so it is accepted.
- **[The host stops replacing the link, for example by writing through it]** → The keeper never sees a regular file and does nothing. The behavior is the same as today, minus the bug.
- **[The launching session's environment reaches the child]** → `CLAUDE_CODE_ENTRYPOINT=claude-desktop`, `CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH` and the messaging socket and token all leak through. This is a separate isolation question. The probe refreshed normally with these variables present, and the change leaves them alone.
- **[Windows needs a privilege to create symlinks]** → This constraint already applies to `prepare_config` and is unchanged.

## Migration Plan

None. A stored login that is already stranded needs one re-login (`claude` → `/login`). After that, the keeper keeps it current.
