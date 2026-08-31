# Fix import output location

## Why

A real `proposal-supervise` run ended with the imported student proposal (`<slug>.md`) missing from the workspace. Investigation shows no script writes the proposal — the location is decided entirely by the agent following prose — and the import skill's operative instructions never name a target directory. The only location anchors an agent sees on a real host pull away from the workspace: the unexpanded-`${CLAUDE_SKILL_DIR}` fallback says the scripts live "next to this SKILL.md, so use that location" (inviting a `cd` into the skill install directory, where every bare `<slug>.md` in the documented commands then resolves), and a source document living outside the workspace invites writing the import beside the source. The eval harness cannot catch this because its prompt framing itself supplies the missing instruction ("The workspace is the `ws/` directory (work there)") — an instruction the real host never gives — and scorers read only `ws/*.md`.

## What Changes

- The `skill-import` spec gains an output-location requirement: the produced `<slug>.md` and its `<slug>.notes.md` are written into the workspace the run is working in (the working directory), never into the skill's install directory and never beside a source document that lives elsewhere; shipped scripts are invoked from the workspace, not by changing into the skill directory.
- `skills/proposal-import/SKILL.md` states the location in its mandate ("into one `<slug>.md` in the working directory"), and its two `${CLAUDE_SKILL_DIR}` fallback paragraphs are reworded so the fallback names a script *path*, not a place to work from.
- The pinned mandate copy `tests/unit/data/skill_mandates/proposal-import.txt` is updated in the same change (header-pattern rule), and the new location sentence is pinned under `tests/unit/data/pinned_sentences/` so a later reword shows up under review.
- No script changes: `check.py` and `validate_refs.py` are read-only with respect to the proposal and take the file path as an argument.

Out of scope, recorded for follow-up: `proposal-write` and `proposal-reverse` share the same silence about where a newly created file lands, but their runs start in the workspace with no pull elsewhere; `proposal-supervise` already states the location in both SKILL.md and spec, and inherits the fix on its import-delegated path.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-import`: add an output-location requirement — produced proposal and notes file land in the workspace (working directory of the run); the skill install directory is read-only territory; scripts are run from the workspace via their full path, never after changing into the skill directory.

## Impact

- `openspec/specs/skill-import/spec.md` (via delta)
- `skills/proposal-import/SKILL.md` (mandate + two fallback paragraphs)
- `tests/unit/data/skill_mandates/proposal-import.txt` (pinned mandate, same-change update)
- `tests/unit/data/pinned_sentences/` (new pin for the location sentence) and its L0 test wiring
- No harness or script behavior changes; the harness's `ws/` framing stays, but stops being the only place the location is stated.
