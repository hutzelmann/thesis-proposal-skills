## Why

Three defects in our own tooling were fixed this session: skills addressed their scripts by a path that could not resolve from the agent's working directory, a verdict matched relayed prose case-sensitively, and the dev runner left the child's stdin open. Each produced failures that were attributed to the skills or the models before the cause was found.

Two kinds of debt remain from working around them.

The import skill accumulated rules written to compensate for a check it could not run. It is now 128 lines against 40–44 for its siblings, one rule appears twice, and five of its eight "non-negotiable" bullets state things the check enforces — the same check the skill now runs on every import. Guidance that duplicates a mechanical check is worse than absent: it is a second source of truth that drifts.

The harness documentation is accurate about the Inspect path but silent about the dev runner, which is where all three defects surfaced. That silence let a real dev-runner failure be read as the documented, expected one.

## What Changes

- The import skill states only what the check cannot verify, and points at the check for the rest. The duplicated research-question rule goes.
- The harness documentation records that a dev-runner failure is a real signal rather than an instance of the documented Inspect-path limitation, and that the previously red `check_report` now passes on both models tested.
- The archived change documents are left untouched. They record wrong turns as well as right ones, and a tidied history would lose what the session actually established.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-import`: the standard-format requirement drops its enumeration of shapes the mechanical check already enforces, keeping the obligation itself and the shapes the check cannot see.

## Impact

- `skills/proposal-import/SKILL.md`: the non-negotiables list contracts to the check-invisible rules; the worked example stays, because showing the target shape is what a source document cannot supply.
- `harness/README.md`: scope of the known limitation clarified, current dev-runner status recorded.
- Measured after the trim: the import scenario must still pass on the dev runner, or the trimmed rules were load-bearing and go back.
