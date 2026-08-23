## Why

A finished thesis ends with a Future Work chapter, and that chapter is the most common real-world source of the next student's topic. Today a student arriving with the previous thesis as a PDF has no entry path: `proposal-ideate` recognises a supervisor's topic list but not this one, so the session either starts from nothing or the agent reads the whole thesis and becomes the party with the ideas — the one thing the skill's hard rule forbids.

## What Changes

- `proposal-ideate` gains a third entry path: the student brings another finished thesis, usually as a PDF, and the skill seeds from its future work.
- The path is bounded by a reading rule: only the closing chapters (Future Work, Limitations, Conclusion) are read, located via the table of contents or a heading scan, and the rest of the thesis is left unread. A thesis read end to end turns the skill into the source of ideas.
- What the reading finds is then handled under the existing supervisor's-topic-list treatment — the student's own material, so the no-menu rule does not bind it — with three path-specific Socratic differences: unvetted items get pressure-tested for whether they carry a thesis or a paragraph; grounding runs early because the source thesis is the closest prior work and a two-year-old suggestion is often already done; and a proposal reading as the previous thesis's leftover task list has a scope rather than a research focus.
- Fallback when PDF reading is unavailable in the environment: ask for those sections as text and say why.
- At seeding, the source thesis becomes a starter reference entry when it is publicly accessible, and is named in the notes file only when it is not.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-ideate`: "Entry paths for prepared students" gains the future-work path and its selective-reading bound; "Seeds the proposal file" gains the rule for recording the source thesis.

## Impact

- `skills/proposal-ideate/SKILL.md` — one bullet in `## Entry paths`, one clause in `## Ending — seeding`.
- No script, no fixture, no shared-block change: the path is instruction only, and PDF reading is the agent's own capability (shipped scripts are standard-library-only and carry no PDF reader).
- `proposal-reverse`, proposed separately, keeps full-thesis harvesting; this path deliberately reads a slice.
