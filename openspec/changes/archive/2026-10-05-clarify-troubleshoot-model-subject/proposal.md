# Proposal

## Why

`fix-troubleshoot-model-match` synced the sentence "The running model SHALL be looked up by the exact identifier its host states" into `skill-troubleshoot`. Read plainly, "running model" is the troubleshooting agent's own model. The failing model often comes from the user instead: a run on a weak model in an earlier session, troubleshot now on a stronger one. That is exactly the case `troubleshoot_model_rung` poses. The review follow-up (68ded53) already fixed `SKILL.md` rung 1 and widened `normalize_model_id`, but the spec still names the wrong subject, has no scenario for a user-named model, and calls any trailing date a date stamp although the code deliberately keeps a short suffix such as `-2411`, which can be a version.

## What Changes

- The "Support verdicts shipped as skill data" requirement defines the running model as the model that produced the failure: the agent's own when the failure happened in the current session, otherwise the model the user names for that run. Its identifier is taken as the host states it or as the user spells it.
- A new scenario covers a failure from an earlier session on a model other than the agent's own, in the synthetic `lab/example-*` family.
- The ignored date stamp is stated as one carrying year, month and day, compact or dashed. A new scenario shows that a shorter numeric suffix is kept, so the spelling stays unevaluated rather than borrowing another key's verdict.
- design.md records the accepted assumption already noted in `collect.py`: a dated snapshot takes the verdict of an undated key with the same version.
- One L0 test pins the boundaries of that assumption, which no test pins today.

No **BREAKING** change. `SKILL.md`, `collect.py` and the pins already behave as the delta states.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-troubleshoot`: "Support verdicts shipped as skill data" names the lookup subject as the model that produced the failure, accepts the user's spelling of it, and narrows the ignored date stamp to year, month and day.

## Impact

- `openspec/specs/skill-troubleshoot/spec.md`, through the archive sync only.
- `tests/unit/test_troubleshoot_collect.py`: one new test for the snapshot boundaries.
- No change to `skills/proposal-troubleshoot/SKILL.md`, `scripts/collect.py`, the pins, the shipped verdict data, or `harness/skill_evals.py`. No model call, metered or subscription.
