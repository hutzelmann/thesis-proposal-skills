## Why

`main` is the release channel: the installer, the plugin marketplace and `npx skills add` deliver whatever is on it. Only a sentence in AGENTS.md kept an agent from pushing it, and auto mode would allow `git push`. On 2026-10-13 local main was 56 commits ahead of origin, none of them through CI, so one accidental push would have released six weeks of work at once. The maintainer chose two layers.

## What Changes

- New `.githooks/pre-push` (active through `core.hooksPath`, which `poe setup` already sets): any push needs a confirmation typed at the controlling terminal. A shell without one, which is every agent shell, is refused with a message saying the maintainer pushes from their own terminal. Nothing to push passes silently.
- `.claude/settings.json` denies `git push`, `rtk git push` and `/usr/bin/git push`, each bare and with arguments.
- AGENTS.md's Git rule names both layers and forbids routing around them (a TTY wrapper, `--no-verify`, another spelling).
- L0: `tests/unit/test_push_guard.py` runs the hook without a terminal (refused), with nothing to push (passes), and on a pseudo-terminal answering yes (passes) and anything else (cancelled), and pins the six deny rules.

No skill or harness behavior changes, hence `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `.githooks/pre-push` (new), `.claude/settings.json`, `AGENTS.md`, `tests/unit/test_push_guard.py` (new).
- The maintainer's own pushes ask once at the terminal. A clone without `core.hooksPath` set has no hook; the deny rules still hold for Claude Code sessions there.
