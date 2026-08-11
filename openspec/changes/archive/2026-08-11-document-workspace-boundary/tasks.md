## 1. AGENTS.md

- [x] 1.1 Add a "Portability and the workspace boundary" section stating the principle: defaults must stay usable at any university, and institution-specific settings belong in the user's workspace.
- [x] 1.2 Pin the override-key invariant (mirror the `structure.json` path, no aliases, unresolvable keys are reported) and name `2026-08-11-nest-workspace-overrides`.
- [x] 1.3 Pin the build-delegation invariant (hand over, never fall back) and name `2026-08-11-add-workspace-build-delegation`, saying what a fallback would cost.
- [x] 1.4 Place it next to "Editing guidance content", which is the neighbouring rule about where things belong, and match that section's density.

## 2. README.md

- [x] 2.1 Open "For supervisors" by naming the principle before the mechanisms that follow from it.
- [x] 2.2 Say the same thing from the contributing side in "For contributors", so the boundary is visible before someone opens a pull request.

## 3. Stale spots

- [x] 3.1 Refresh the `proposal-publish` table row: it still reads as pandoc-or-nothing and omits the workspace build handover.
- [x] 3.2 Refresh the `proposal-customize` table row: it names page limits and work plans but not the methodology set.
- [x] 3.3 Refresh the quick-start sentence that presents PDF building as pandoc plus typst only.

## 4. Verify

- [x] 4.1 Confirm no claim in the new text is aspirational — every mechanism named exists and has a fixture or test.
- [x] 4.2 `uv run poe test` green.
- [x] 4.3 `openspec validate --all --strict` green.
