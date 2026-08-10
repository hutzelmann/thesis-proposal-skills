## Why

The ideation skill's guidance-awareness block names a reference count — "three-plus scientific references" — as part of the shape it steers toward. That count is the finished proposal's bar, not the ideation session's, and stating it inside a Socratic dialogue turns it into a target the agent can chase. Grounding searches then get run to reach a number rather than to test whether the idea is already solved, and the seed file arrives carrying three loosely-related citations that the write skill reasonably treats as the beginning of a literature base.

The skill already knows the correct division of labour: grounding tests the idea, and the literature-search sibling builds the bibliography. Naming a count in the ideation skill contradicts that division.

## What Changes

- Remove the reference count from the ideation skill's guidance-awareness block, and name the sibling skill that owns the bibliography instead.
- Keep everything the block does say about shape — an analytical research focus, one methodology from the closed set — and add the research-question count bound now that one exists.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-ideate`: literature grounding is explicitly not bibliography-building, and the skill states no reference-count target.

## Impact

- `skills/proposal-ideate/SKILL.md` — one paragraph.
- No script, no structured data, no fixture changes. The seeding requirement already says `references: []` is a valid seed, so nothing downstream assumed a count.
