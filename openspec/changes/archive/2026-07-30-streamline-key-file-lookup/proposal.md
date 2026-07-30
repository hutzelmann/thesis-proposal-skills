# Streamline API Key File Lookup

## Why

`common.get_key()` opened `api-keys.env` relative to the current working directory in a single attempt. A script invoked from anywhere other than the workspace root — a skill's own `scripts/` directory, a chapter subfolder — silently saw no key and OpenAlex was skipped, with an error message ("no OPENALEX_API_KEY found in environment or api-keys.env") that named no path and so gave no way to diagnose it. This bit a real session: the key existed, the agent ran from the skill directory, and the only fix was to notice the cwd dependency and re-run from the workspace root.

Students are the target users here. A credential that works or not depending on which directory a script happens to be launched from is a failure mode they cannot be expected to reason about.

## What Changes

- Credential resolution becomes a candidate list, consulted per key rather than per file: environment variable, then `$THESIS_PROPOSAL_KEYS` (explicit file path), then `api-keys.env` in the working directory and each ancestor up to `$HOME`, then `~/.config/thesis-proposal/api-keys.env`.
- Ancestor walking stops at the home directory so a stray `/api-keys.env` outside the user's own tree is never read.
- Per-key resolution means a workspace file holding `OPENALEX_API_KEY` and a global file holding `CONTACT_EMAIL` compose instead of shadowing each other.
- The OpenAlex missing-key error names every location that was consulted, so the next failure is self-diagnosing.
- Documentation (`SKILL.md`, `AGENTS.md`, `docs/getting-started.md`) states the resolution order and points multi-workspace users at the global file.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `skill-lit-search`: the "Keyless baseline, keys as guided upgrades" requirement said keys are "supplied via environment", which never described the file path the skill actually documents and creates. Replaced with an explicit credential-resolution requirement covering search order, the `$HOME` boundary, and per-key composition.

## Impact

- `skills/proposal-lit-search/scripts/common.py` (resolution logic), `openalex.py` (error text); the vendored `skills/proposal-import/scripts/common.py` copy regenerates via `scripts/sync_shared.py`.
- `tests/unit/test_lit_common.py`: two added tests (lookup from a workspace subdirectory, explicit override plus per-key fallthrough).
- Docs: `skills/proposal-lit-search/SKILL.md`, `AGENTS.md`, `docs/getting-started.md`.
- Backwards compatible: a key file in the workspace root with the working directory at the root resolves exactly as before.

## Non-Goals

- Finding a workspace key file from a skill installed outside the workspace tree (e.g. `~/.claude/skills/…`). Ancestor walking cannot reach a directory it is not under; that case is served by `$THESIS_PROPOSAL_KEYS` or the global file.
- A `--keys` flag on each script. Every script would need it, and the environment override covers the same need with one mechanism.
