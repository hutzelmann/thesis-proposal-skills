# Design — baseline-eval-arm

## Context

See proposal.md. Constraints: Inspect tasks are built by argless-by-convention `@task` functions the matrix invokes by name; scorer registry names feed the support classifier and must not change; `verdict_scorer` names carry `_l1`/`_l2` markers that the classifier reads.

## Goals / Non-Goals

**Goals:** with/without comparison at minimal surface — no new frameworks, no scorer changes, no matrix growth by default.

**Non-Goals:** baselines for persona-dialogue tasks; baseline data in the model-support verdicts (a baseline run must never count toward "supported"); routing changes.

## Decisions

**D1 — Baseline is a task parameter, not a task family.**
Single-turn task builders accept `baseline: bool = False` (Inspect `-T baseline=true`); `proposal_task` swaps `skill_prompt(...)` for a plain prompt carrying the same workspace framing and user request. Staging stays fully identical — `skill/` carries the check script and references the verdicts need in either arm; what the baseline removes is the skill instructions, not the files (revised from "skip skill/ staging" during implementation: without those files the scorers cannot run). Ten `*_baseline` task clones were rejected: they would double the registry and the wiring test for zero information. The wiring test pins that multi-turn tasks reject the parameter (they simply do not accept it — `TypeError` is the rejection, surfaced cleanly by the runner).

**D2 — Logs distinguish arms by recorded task args.**
Inspect logs carry `eval.task_args`; `report.py` buckets a log as baseline when `task_args.baseline` is true. No filename conventions, no separate log dir — the log is the record. A baseline log never enters support classification (`report.py` filters it out of verdict computation before anything else).

**D3 — Delta view is additive and conditional.**
`poe report` renders the existing grid unchanged; a delta section appears only for (model, task) cells having both arms, listing pass-rate delta, token delta, duration delta, and the dead/too-hard assertion flags per scorer. Missing baselines are not an error — the arm is on-demand.

**D4 — Duration from log timing fields.**
`report.py` reads the run's wall-clock span from each Inspect log's stats timestamps (started/completed); no new instrumentation, no timing in the harness itself. Dev-runner duration is out of scope (its verdicts are printed, not logged).

**D5 — Dev runner `--no-skill`.**
Stages the fixture workspace as usual, does not install the skill, and sends the task's bare user request. Exists for cheap eyeballing of the same contrast on the subscription; produces no logs the report consumes.

## Risks / Trade-offs

- [Judge costs double when running both arms on L2 tasks] → the arm is on-demand and estimated by the existing cost gate; nothing runs unprompted.
- [A baseline log slipping into support classification would corrupt verdicts] → filtered at the single entry point where logs are read; L0 test pins it.
- [`-T baseline=true` on a persona task would silently build a wrong control] → those builders take no such parameter; the invocation fails loudly.
