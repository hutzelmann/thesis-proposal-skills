# Proposal: implement-remaining-skills

## Why

Six of eight skills lack their SKILL.md (write, review, ideate, import, customize, publish); publish also needs its build script. With guidance, structure data, and lit-search scripts already synced into the skill trees, these are now authorable as pure instruction files plus one stdlib script — completing the installable skill set.

## What Changes

- `SKILL.md` for proposal-write, proposal-review, proposal-ideate, proposal-import, proposal-customize, proposal-publish — each implementing its seeded capability spec (frontmatter `name` with `proposal-` prefix per packaging spec).
- `skills/proposal-publish/scripts/publish.py`: engine resolution (typst → LaTeX → docx), pandoc invocation with template/filter/citeproc, hand-in export (abstracts stripped), workspace `.gitignore` maintenance, missing-tool guidance.
- L0 tests for publish.py's offline logic (engine resolution, handout stripping, gitignore ensure).
- Adversarial spec-compliance verification: each SKILL.md checked against its capability spec; findings fixed before archive.
- `skip_specs: true` — implements existing capability specs.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- Completes `skills/` to the full eight; package becomes installable end to end.
- No new dependencies; publish.py is stdlib-only per D7.
