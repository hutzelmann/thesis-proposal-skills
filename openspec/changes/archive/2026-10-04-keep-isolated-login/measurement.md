# Measurement

All checks ran on 2026-10-04 with host 2.1.284 and one haiku `claude -p "Reply with the single word OK."` each. The scripts printed file types, dates and booleans only, never a token value. Each forced refresh rotated the real refresh token, so each script then wrote the refreshed login back to `~/.claude/.credentials.json`. It did so only when that login was newer and the real file had not changed during the check. `claude auth status` reported `loggedIn: true` afterwards.

## The mechanism, before the fix

The script called `prepare_config` with `CLAUDE_REAL_CONFIG_DIR` pointing at a scratch copy of the stored login. In the copy, `expiresAt` was set 60 s into the past. Nothing else changed.

| Observation | Value |
|---|---|
| link before the run | symlink to the scratch source |
| run | rc 0, `OK` |
| link after the run | regular file, mode 0600 |
| scratch source written through the link | no |
| refresh token in the replacement | rotated |

That is the hypothesis, confirmed. The host refreshes by atomic replace, so the link is gone and the source is untouched.

`claude auth status` against the same forced-expired copy did not refresh. The link stayed a symlink and the source was not written. No refresh path exists without a model call.

With `CLAUDE_CODE_OAUTH_TOKEN` set to a placeholder and an empty config directory, `claude auth status` reported `authMethod: oauth_token`. Without the variable it reported `none`. An actual run with a `setup-token` token was not measured, because that token needs an interactive browser login.

## The incident, reconstructed

The stored login had expired at 04:29Z. That was 8 h after the 2026-10-03 `/login`, and the stored file had been written by nothing since. An agent session started five isolated runs between 19:34:13Z and 19:34:57Z:

- **The first run** refreshed and passed.
- **Two runs started 3 to 6 s later** failed at 0 USD.
- **Two runs started 40 s later** also failed at 0 USD.

All four failures read `Failed to authenticate: OAuth session expired and could not be refreshed`. Each run read the stale refresh token through its own link. The first run's rotated token was deleted with its temporary directory.

## The fixed path

The same forced-expired scratch copy was used, this time through `routing.isolated_config`.

| Observation | Value |
|---|---|
| at start | link is a symlink, refresh claim held |
| run | rc 0, `OK` |
| 1.5 s after the run, configuration still in use | link is a symlink again, claim released |
| stored scratch login after exit | rotated refresh token, later expiry, mode 0600 |
| configuration directory after exit | removed |
