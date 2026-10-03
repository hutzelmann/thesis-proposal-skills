# Proposal

## Why

The model check on 2026-10-03 ran the over-scoped supervise scenario three times on haiku through the dev runner. Haiku never loaded the skill. It wrote feedback of its own and published it three times as claude.ai artifacts, using the host's Artifact tool.

The dev runner starts the host with `--dangerously-skip-permissions`. The isolated configuration empties settings but leaves the host's outward-facing tools available: publishing, messaging, scheduling. The artifacts held only synthetic fixture data, were private, and were deleted the same day. Still, a test run must not be able to publish, send or schedule anything, whatever the model decides.

The same check measured which models the supervise skill works on:

| Model | Skill invoked | Verifier ran | Both planted errors caught |
|---|---|---|---|
| sonnet | yes, in every run that day | 6/6 | yes |
| opus | 3/3 | 3/3 | 3/3 |
| haiku | 0/3 | — | — |

The README's supervisor section says nothing about model choice, and it still describes the skill as it was before the verification and workload changes. It also says the review applies five substance tests, which has been six since `guard-non-serving-material`.

## What Changes

- **Dev runs cannot reach outward tools.** The dev runner passes `--disallowed-tools` for the host's outward-facing tools: Artifact and its comment and data tools, cross-session messaging, push notifications, remote triggers, scheduling and design sync. The routing rig's existing deny list gains the same tools, which makes its restriction explicit rather than a side effect of prompting. One shared constant feeds both.
- **README "For supervisors" is brought up to date:**
  - claim checks against sources, with the fresh verifier;
  - the workload check with cut options;
  - format remarks staying in the review;
  - the one lookup question;
  - a measured model note: sonnet and opus work; haiku did not pick the skill up;
  - six substance tests instead of five.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: Dev-runner cost and helper-agent telemetry. The runner denies the host's outward-facing tools.

## Impact

- `harness/routing.py`: `OUTWARD_TOOLS`, plus the deny list.
- `harness/claude_runner.py`: `host_command`.
- `tests/unit/test_dev_runner_probe.py` and the routing tests.
- `README.md`.
- No skill text changes. No metered spend.
