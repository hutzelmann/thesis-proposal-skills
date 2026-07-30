## Why

Import output is judged by the mechanical check, but import never runs it. Every conformance defect therefore has to be anticipated in prose and written into the skill one rule at a time — three rounds of that took the dev-runner pass rate from 0/4 to 2/4, and the remaining failure is a rule already stated in the instructions and still missed. Guessing which rules to spell out does not converge.

Running the check closes the whole rule set at once, including rules nobody thought to emphasize. It also addresses a failure mode instruction cannot touch: on some runs the skill reports a proposal file it never wrote. A skill whose last act is to read its own output back cannot make that claim silently — a missing file becomes an error it has to handle rather than a confident false report to the user.

## What Changes

- Import runs the mechanical check over the file it just wrote, fixes what the check reports, and only then reports completion. Findings that follow from what the source did not carry — too few references above all — are reported to the user rather than fixed by inventing content.
- The check script and the structured skeleton it reads become synchronized copies inside the import skill, so import stays functional installed alone. The packaging rules require exactly this for an asset a skill's core function depends on.
- The eval scorer stops staging its own hidden copy of the check script and uses the skill's, because the skill now genuinely ships one — the earlier hiding existed to avoid handing the model a tool it would not really have, and that reason is gone.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-import`: the standard-format requirement gains the obligation to verify the produced file against the mechanical check before reporting, and to distinguish findings it must fix from findings that reflect a thin source.

## Impact

- `scripts/sync_shared.py`: two new entries in the sync map — the check script into `skills/proposal-import/scripts/`, the structured skeleton into `skills/proposal-import/references/` (the script resolves it relative to its own location).
- `skills/proposal-import/SKILL.md`: the wrap-up step runs the check and fixes findings. It must state plainly that this is import fixing its own fresh output, not the check skill running — that skill is read-only and must never edit.
- `harness/skill_evals.py`: the scorer runs the skill's own copy instead of a staged `tools/` path.
- No change to the check script itself, and no new dependency: it is already stdlib-only and cross-platform.
