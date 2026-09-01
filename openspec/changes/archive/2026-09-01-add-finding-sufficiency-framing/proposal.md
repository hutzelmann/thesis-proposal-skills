# Add finding sufficiency framing

## Why

Review findings about exceeded limits copy the guidelines' prohibition framing straight into reader-facing tone: a real run rendered the timeline rule as "the phase/Gantt plan do not belong in it" — accurate, but it tells the writer only what is forbidden, not what suffices or where the surplus work goes. The guidelines' prohibition framing is correct where it lives (document rules the check and write skills enforce); a finding addressed to a person should instead lead with what is enough and salvage the surplus, the way the import skill already treats work plans (months into the timeline sentence, phase detail into notes).

## What Changes

- The review skill's finding format gains a framing rule: a finding about an exceeded limit or forbidden content phrases its suggestion as what suffices and where the surplus content goes — never only that the content does not belong.
- No change to the guidelines themselves: prohibition framing stays correct for document rules.
- No duplicate rule in the supervise skill: supervise curates its student-facing points from the review rules, so the framing arrives there through reuse, and its own "direction, not a prescribed fix" rule already governs the final rephrasing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-review`: the persisted-output requirement gains a framing constraint for limit/forbidden-content findings — suggestion states what suffices and where surplus content goes.

## Impact

- `skills/proposal-review/SKILL.md` — one sentence in the Output section's finding format.
- `openspec/specs/skill-review/spec.md` — delta on the persisted, actionable output requirement.
- No script, harness, or shared-content changes; no sync needed (SKILL.md bodies are hand-maintained outside the materialized blocks).
