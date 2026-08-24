# Baseline eval arm

## Why

The harness measures whether a model passes a task with the skill injected, never whether the skill beats the bare model — the Agent Skills evaluation guidance's core with/without comparison. Without that control arm there is no way to see what a skill actually buys, and no way to spot dead assertions that pass regardless of the skill. Timing is similarly absent: cost accounting is deep, wall-clock is nowhere.

## What Changes

- **Without-skill control, both runners.** The dev runner gains `--no-skill` (same fixture staging and request, the skill neither installed nor mentioned); the Inspect path gains a baseline mode that keeps the task's request, files, and scorers but replaces the skill-instruction prompt with a plain agent prompt. Verdict functions are reused unchanged — they judge outputs, not provenance. Metered baseline runs stay cost-gated and on-demand; the default matrix does not grow.
- **Delta reporting.** When baseline logs exist beside with-skill logs, `poe report` renders a delta view per task: pass rate bought versus tokens spent. Scorers passing in both arms are flagged as dead-assertion candidates; scorers failing in both arms as too-hard candidates (the standard's pattern analysis).
- **Duration capture.** `report.py` reads wall-clock duration from the Inspect logs alongside token usage, completing the timing side of the standard's benchmark shape.
- First cut is single-turn tasks only — the multi-turn persona dialogues have no meaningful "without skill" framing (the persona answers a skill-shaped conversation).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities
- `testing-harness`: a new requirement for the baseline comparison arm (both runners, delta reporting, dead-assertion flagging) and duration reported beside token usage.

## Impact

- `harness/skill_evals.py`: baseline prompt variant for single-turn tasks (env- or task-parameter switch).
- `harness/claude_runner.py`: `--no-skill` staging flag.
- `harness/matrix.py`: `--baseline` pass-through, logs landing beside the with-skill logs distinguishably.
- `harness/report.py`: delta view, dead/too-hard assertion flags, duration column.
- `harness/README.md`: how to run a baseline sweep and read the delta.
- L0 tests for the new report logic and runner staging.
