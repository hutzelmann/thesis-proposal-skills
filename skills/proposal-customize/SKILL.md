---
name: proposal-customize
description: Adapt the proposal guidance to a supervisor's or program's requirements by managing the workspace guidelines.md override file. Use when the user says their supervisor wants something different — a required timeline, page limit, more references, different sections.
---

# Proposal Customize

Makes a supervisor's or program's own rules — a page limit, a required timeline, a different section order, more references — into the rules every other proposal skill follows.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → proposal-review → proposal-publish. Also: proposal-import (start from an existing document), **proposal-customize** (adapt the rules to a supervisor's requirements).

You translate supervisor/program requirements into the workspace `guidelines.md` — the override file every other skill honors. The user never edits installed skills; this file is the customization surface.

## File format you maintain

`guidelines.md` in the workspace root: freeform prose (agent-level guidance: tone wishes, focus areas, supervisor quirks) plus one fenced TOML block for the machine-readable part:

```toml
min_references = 8
page_limit = 3
required_sections = ["..."]     # replaces the default required list entirely
forbidden_sections = ["..."]    # replaces the default forbidden list entirely
```

Merge semantics (fixed, explain them when relevant): a user key wins over the default per key; list values **replace** the default list entirely (they do not append); removing an entry from `forbidden_sections` un-forbids it.

## Working through a request

1. Hear the requirement ("supervisor wants a timeline", "max 3 pages", "at least 8 sources").
2. **Check for conflicts with the defaults** (see `references/guidelines.md`): requiring a default-forbidden section, dropping a canonical section, lowering the reference minimum. On conflict: explain what the default is, why it exists, and what the override changes downstream — check will then require/accept it, review will not flag it — and apply only after the user confirms.
3. Edit the TOML block precisely: to un-forbid one section, reproduce the default forbidden list minus that entry (lists replace — a one-entry list would wipe the rest). Put non-mechanical wishes ("more industrial focus") into the prose part instead.
4. Show the resulting `guidelines.md` and summarize in one sentence per change what now applies in this workspace.

## Boundaries

- Never edit installed skill files or `references/` copies — only the workspace `guidelines.md`.
- Requirements that contradict the hard rules (fabricating sources, removing citation consistency) are declined with a short explanation.
- Ensure the file stays parseable: exactly one TOML block, valid TOML (a broken block makes check report a parse error — mention that if the user hand-edits).
