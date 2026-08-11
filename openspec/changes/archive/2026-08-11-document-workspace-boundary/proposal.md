## Why

The repository has spent a dozen changes making guidance, methodologies and the build pipeline configurable per workspace, and the reason behind all of it is the same: these skills must stay usable at any university, by any supervisor, so anything institution-specific belongs in the student's folder rather than in the shipped defaults.

That principle is currently written down nowhere. `README.md` demonstrates it three times in "For supervisors" without naming it, and its "For contributors" section — the one somebody reads before opening a pull request — does not mention it at all. `AGENTS.md` mentions "workspace" once, only to say that proposals do not live in this repository, and never mentions overrides, customization, or portability.

The cost is not hypothetical. An external contributor retargeted the shipped defaults to their own lab and opened a 116-file pull request, which was the reasonable reading of the contributing guidance as written. The reply explaining the boundary was posted to a closed pull request; the boundary itself still is not stated anywhere either a contributor or an agent would look.

Two invariants are undocumented in the same way, and both are the kind a well-meaning change would quietly undo:

- Workspace override keys mirror their `structure.json` key path, with no aliases, and a key that resolves to nothing is reported rather than ignored (`2026-08-11-nest-workspace-overrides`). A convenience alias added later would cost exactly the property that migration bought.
- Publish hands over to a workspace build definition and never falls back to the built-in layout (`2026-08-11-add-workspace-build-delegation`). A fallback added while fixing an unrelated bug would silently reintroduce the failure the design exists to prevent: a student sending a document in the wrong template.

## What Changes

- `AGENTS.md` gains a "Portability and the workspace boundary" section stating the principle and pinning both invariants, each naming the archived change that established it.
- `README.md` names the principle where a supervisor meets it, and states it from the contributing side in "For contributors".
- Three stale spots in `README.md` are refreshed: the `proposal-publish` and `proposal-customize` table rows, and the quick-start sentence that still frames publishing as pandoc-or-nothing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — `skip_specs: true`. Documentation only; no behavior changes, and every mechanism described already exists and is tested.

## Impact

- `AGENTS.md`, `README.md`.
- No skill file, no generated copy, no fixture, no script.
