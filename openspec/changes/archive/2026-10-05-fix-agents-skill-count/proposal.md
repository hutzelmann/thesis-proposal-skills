# Fix the stale skill count in AGENTS.md and the routing rig docstring

## Why

`skills/` holds eleven skills since `proposal-reverse` landed (2026-08-23), and the offline suite already pins eleven (`test_skill_header_pattern.py`). AGENTS.md still describes ten: "ten `proposal-*` agent skills … nine student-side", the workflow line and voice block "byte-identical in all ten files", "the other nine exist", and "not ten files". An agent reading those instructions gets the inventory wrong before it starts, and the "Skill header pattern" section is the one an agent follows when adding a skill. The routing rig's module docstring says the host reads "the ten frontmatter descriptions", while `harness/README.md` already says eleven for the same rig.

## What Changes

- `AGENTS.md`: "eleven `proposal-*` agent skills … ten student-side, plus the supervisor-side `proposal-supervise`"; "byte-identical in all eleven files" (workflow line and voice block); "the other ten exist"; "not eleven files". Nothing else in AGENTS.md changes (the maintainer approved editing AGENTS.md for this count fix only).
- `harness/routing.py` module docstring: "the eleven frontmatter descriptions".
- Swept and found correct or unrelated: `README.md`, `CONTRIBUTING.md`, `docs/`, `harness/README.md` (already eleven), `openspec/specs/`, `shared/blocks/`, test docstrings. `openspec/changes/archive/` describes the set at its time and is left alone.

## Capabilities

### New Capabilities

(none — docs only, `skip_specs: true`)

### Modified Capabilities

(none — no requirement describes the skill count in these files; the packaging spec and the header-pattern test already work from the eleven shipped skills)

## Impact

- `AGENTS.md` (four sentences), `harness/routing.py` (docstring only).
- No skills, no `shared/`, no runtime behaviour.
