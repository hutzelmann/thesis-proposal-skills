## Why

Nothing in this repository measures whether the right skill is invoked in the first place. Every L1/L2 task injects the SKILL.md body directly (`skill_prompt()` in `harness/skill_evals.py`), so the frontmatter `description` — the only text a host agent reads when deciding which skill to load — is never exercised. A probe run on 2026-08-10 (headless `claude -p`, haiku, three skills installed) routed "Please review my proposal … is it ready for my supervisor?" to `proposal-check` instead of `proposal-review`, because both descriptions claim the supervisor-handoff moment. The suite therefore ships a known trigger collision that no gate can see.

Fixing the descriptions without an instrument would be a blind edit: we would have no baseline to compare against and no way to tell a real improvement from a lucky sample. This change builds the instrument first and records the red baseline; the description rewrite and its enforcement follow in `skill-trigger-contract`.

## What Changes

- New harness rig `harness/routing.py`: stages an isolated Claude Code configuration plus a workspace with all ten skills installed, runs headless `claude -p` with one user utterance, reads the streamed events, and records the first `Skill` invocation naming a `proposal-*` skill as that utterance's route.
- New dataset `harness/routing_cases.toml`: 40 cases — ten skills × (canonical / oblique / collision) phrasings, four negatives that no `proposal-*` skill should claim, six German cases on the highest-traffic skills.
- Verdict is the first `Skill` call; the run is terminated as soon as it is observed, and a case that produces three non-`Skill` tool calls or exceeds the per-case timeout is recorded as unrouted.
- Route extraction and matrix classification are pure functions over event data, covered by L0 tests against recorded stream fixtures, so the rig is testable without model calls.
- New poe task `routing`; raw results under the gitignored `logs/routing/`, generated report committed at `docs/skill-routing.md`.
- Records the baseline confusion matrix for the current descriptions. No skill file changes: this change measures, it does not fix.

## Capabilities

### New Capabilities

<!-- none: the routing rig is a testing-harness concern -->

### Modified Capabilities

- `testing-harness`: adds skill-selection (routing) as a measured layer — which skill the real host selector invokes for an utterance, distinct from the existing layers that measure how a skill behaves once selected.

## Impact

- New: `harness/routing.py`, `harness/routing_cases.toml`, `tests/unit/test_routing.py`, `tests/unit/data/routing_streams/`, `docs/skill-routing.md`.
- Modified: `pyproject.toml` (poe task), `harness/README.md` (rig documentation), `.gitignore` is already sufficient (`logs/`).
- Requires the `claude` binary and a logged-in subscription; the rig is a local/on-demand instrument and is not part of the CI gate. Its pure functions and dataset integrity are.
- Needs an isolated `CLAUDE_CONFIG_DIR` whose credentials are reachable; a fresh config directory alone reports `Not logged in`.
