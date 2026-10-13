## Why

A repo-wide audit on 2026-10-13 found twelve deferred follow-ups (eleven entries: citation support and the unmet citation-scope bar share one) that existed only in agent memory notes and session transcripts. Nobody reading the repository could see them, and one (the judge environment's allowlist) had already been done without the note being updated. The maintainer chose a tracked file over GitHub issues or memory.

## What Changes

- Add `docs/backlog.md`: one line per deferred follow-up, grouped as evaluation, harness and skills, each naming where its evidence lives. Picking an item up means proposing an OpenSpec change; an item whose change lands, or that turns out obsolete, is removed in the same commit.
- Drop the judge-allowlist unification from the list of open items: `harness/claude_cli.py` already builds the judge's environment with `host_login.allowlisted_env` (landed with 526a1bf).

No skill, harness or spec behavior changes, hence `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `docs/backlog.md` (new). It is not part of any installed skill: the installers copy `skills/` only.
