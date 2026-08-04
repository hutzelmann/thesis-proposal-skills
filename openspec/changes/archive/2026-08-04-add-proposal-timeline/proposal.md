## Why

Supervisors need to know when a thesis starts and when it lands, and today the guidance forbids that information outright — `timeline` and `zeitplan` are forbidden heading patterns, and the must-not list names "work plans, timelines or milestones" in one breath. That blanket ban was aimed at the real problem, which is the multi-page Gantt chart with five work packages, not at the single sentence a supervisor actually reads. The ban is also the most frequently overridden default: the `proposal-customize` skill, the getting-started guide, the README, and three separate spec scenarios all use "my supervisor wants a timeline" as their worked example of fighting the defaults, which is strong evidence that the default is wrong rather than that students are.

## What Changes

- **BREAKING** A fifth canonical section, `Timeline` / `Zeitplan`, becomes required and last. It holds one short sentence naming the start month and the submission month, or stating that the work begins as soon as possible. Missing it is an error.
- **BREAKING** Canonical section order becomes enforced for all five sections. Order has never been checked; a proposal that opens with its methodology passes today and will not after this change.
- **BREAKING** `timeline` and `zeitplan` are removed from the forbidden heading patterns — they are now canonical titles. `gantt`, `workpackage`, and `arbeitspaket` join the forbidden list in their place; `schedule`, `time plan`, `work plan`, `workplan`, `milestones`, `arbeitsplan`, and `meilensteine` stay forbidden.
- A mechanical body guard keeps the new section small: no table rows, no list items, no subsections, at most three non-empty lines. This is what replaces the deleted forbidden patterns as the barrier against Gantt charts.
- An agent-side check confirms the section actually states a timeframe. It tolerates phrasings no regex would survive (`SoSe 2027`, `WS 2026/27`, `Q3`, "winter semester") and catches a Gantt chart pasted as an image, which the mechanical guard cannot see at all.
- A new workspace override key, `timeline_detail = "simple" | "detailed"`, restores the escape hatch that un-forbidding a heading used to provide. Under `detailed` the body guard is off and the work-plan heading patterns drop out of the forbidden list, so a supervisor who genuinely demands a phase table gets one.
- The writing skills learn the section: `proposal-write` emits it and marks unknown dates as a TODO rather than asserting a timeframe the student never stated; `proposal-ideate` asks for timing once while seeding; `proposal-import` distills the first and last month out of a source Gantt chart instead of discarding it, and reorders sections now that order is checked.
- Every place that describes the structure as four sections, or the timeline as forbidden, is corrected: five `SKILL.md` files, the README (including its demo excerpt), the getting-started guide, the fixture catalogue, and one metered eval task whose scorer currently treats a still-forbidden timeline as a failure.

## Capabilities

### New Capabilities

<!-- None. The timeline is a property of the existing guidance model and the
     existing skills, not a new capability. -->

### Modified Capabilities

- `guidance-model`: the default forbidden-content list no longer bans timelines; the canonical structure gains a fifth section with enforced order; the workspace override block gains `timeline_detail`.
- `skill-check`: the deterministic pass gains section-order verification and the Timeline body guard; the agent pass gains the positive timeframe check.
- `skill-write`: written output must carry the Timeline section, with an unknown timeframe recorded as a TODO rather than invented.
- `skill-import`: imported proposals distill a source timeline instead of stripping it, and are reordered into canonical order.
- `skill-customize`: the skill documents `timeline_detail`; its worked example moves from "requires a timeline" to "requires a detailed work plan".
- `skill-ideate`: the seeding step captures the timeframe as a body note.

## Impact

- **Guidance data**: `shared/structure.json` (section order, titles, forbidden patterns, override keys), `shared/guidelines/guidelines.md` (structure section, must-not list, canonical-titles table). Seven generated copies follow via `scripts/sync_shared.py`.
- **Check script**: `skills/proposal-check/scripts/check.py` and its two vendored copies under `proposal-write` and `proposal-import`.
- **Skills**: `proposal-write`, `proposal-check`, `proposal-import`, `proposal-customize`, `proposal-ideate`. `proposal-review` and `proposal-publish` are untouched.
- **Docs**: `README.md` (skill table, "For supervisors", demo block 3), `docs/getting-started.md`, `docs/demo/harvest.log`, `tests/fixtures/README.md`.
- **Tests**: three clean fixtures gain the section, roughly seventeen broken-fixture oracles gain the missing-section error, one new fixture covers the body guard, `w02-override-workspace` is repurposed to `timeline_detail`, and `tests/unit/test_check.py` plus `tests/unit/test_harness_helpers.py` lose their timeline-is-forbidden assumptions.
- **Harness**: `harness/skill_evals.py` customize task and its scorer, `harness/sources.py`.
- **Metered work**: one demo session re-run, because `docs/demo/README.md` binds the README excerpt to real session output; and one L1/L2 run to confirm the rewritten eval task.
