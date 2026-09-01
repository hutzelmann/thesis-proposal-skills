---
name: proposal-customize
description: Adapt the proposal guidance to a supervisor's or program's requirements by managing the workspace guidelines.md override file. Use when the user says their supervisor wants something different — a detailed work plan, page limit, more references, different sections.
license: MIT
---

# Proposal Customize

Makes a supervisor's or program's own rules — a page limit, a required work plan, a different section order, more references — into the rules every other proposal skill follows.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → proposal-review → proposal-publish. Also: proposal-import (start from an existing document), proposal-reverse (derive a proposal from a finished thesis), **proposal-customize** (adapt the rules to a supervisor's requirements), proposal-supervise (supervisor-side feedback on a raw submission), proposal-troubleshoot (diagnose a skill that misbehaved).

**Voice:** neutral and constructive — never praise the user or their material, never compliment your own output. Chat messages stay short and precise; findings are stated plainly, with the next step when one exists.

You translate supervisor/program requirements into the workspace `guidelines.md` — the override file every other skill honors. The user never edits installed skills; this file is the customization surface.

## File format you maintain

`guidelines.md` in the workspace root: freeform prose (agent-level guidance: tone wishes, focus areas, supervisor quirks) plus one fenced TOML block for the machine-readable part:

```toml
[references]
min_count = 8
min_per_1000_words = 4         # density advisory scales with length; 0 disables it

[length]
page_limit = 3

[research_questions]
min_count = 1
max_count = 5

[sections]
required = ["..."]              # replaces the default required list entirely, and its order is the enforced order

[forbidden]
heading_patterns = ["..."]      # replaces the default forbidden list entirely

[timeline]
detail = "detailed"             # default "simple": one sentence, no table, no phases
```

The methodology set is configurable the same way, and is the one override with an entry per branch rather than a single leaf:

```toml
[methodologies.case_study.title]
en = "Case Study"
de = "Fallstudie"

[[methodologies.case_study.subsections]]
en = "Case and Context"
de = "Fall und Kontext"
guidance = "The organisation or system studied, why it suits the research questions, what access exists."

[methodologies.theoretical]
enabled = false                 # a shipped branch this program does not accept
```

A branch id matching a shipped one replaces it; a new id adds one; `enabled = false` removes one. **`guidance` per subsection is required and you may not invent it**: the shipped branches carry their content contract as prose in `references/guidelines.md`, and a workspace branch has nowhere else to put one — without it the write skill fills a heading it has never seen. If the user cannot say what belongs in a subsection, stop and say the branch cannot be written yet; do not guess. Before disabling a shipped branch, say plainly that any existing proposal declaring it starts failing the check.

What stays fixed is the closure, not the contents: a proposal still declares exactly one methodology, from whatever set this workspace ends up with.

**Every key is the key path it has in `references/structure.json`.** That is the whole naming rule — there are no short forms, and a key that does not resolve to an overridable leaf is reported by the check as an error rather than quietly ignored. If you meet a workspace file written before this shape (`min_references = 8`, `timeline_detail = "detailed"`, and the other flat keys), migrate it in place and tell the user which keys you moved; leaving it costs them their overrides.

Merge semantics (fixed, explain them when relevant): a user key wins over the default per key; list values **replace** the default list entirely (they do not append); removing an entry from `[forbidden] heading_patterns` allows that section again. The proposal's leading `# ` title line is exempt from both section lists — it is the thesis title, not a section, so neither `[sections] required` nor `[forbidden] heading_patterns` ever matches it. `[timeline] detail = "detailed"` is the one switch that governs the timeline section: it lifts the one-sentence size limit and stops work-plan headings (work plan, milestones, Gantt, work packages) being forbidden. Leave the forbidden list alone for that — the switch does the whole job.

## Working through a request

1. Hear the requirement ("supervisor wants a detailed work plan", "max 3 pages", "at least 8 sources").
2. **Check for conflicts with the defaults** (see `references/guidelines.md`): requiring a default-forbidden section, dropping a canonical section, loosening the timeline to a full work plan, lowering the reference minimum. On conflict: explain what the default is, why it exists, and what the override changes downstream — check will then require/accept it, review will not flag it — and apply only after the user confirms. A program that wants no timeline at all is also a conflict: the timeline is required by default, and dropping it means an explicit `[sections] required` list without it.
3. Edit the TOML block precisely: to allow one forbidden section again, reproduce the default forbidden list minus that entry (lists replace — a one-entry list would wipe the rest). Put non-mechanical wishes ("more industrial focus") into the prose part instead.
4. Show the resulting `guidelines.md` and summarize in one sentence per change what now applies in this workspace.

## Boundaries

- Never edit installed skill files or `references/` copies — only the workspace `guidelines.md`.
- Requirements that contradict the hard rules (fabricating sources, removing citation consistency) are declined with a short explanation.
- Ensure the file stays parseable: exactly one TOML block, valid TOML (a broken block makes check report a parse error — mention that if the user hand-edits).

## When this run fails

If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step failed repeatedly with no user edit in between, or the state makes no sense — offer a bug report once, in these words, and do not raise it again in the same session: "Something here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send." Ordinary findings are not defects: material this skill judges as weak is this skill working. Collect nothing unless the user accepts.

An override that another skill then obeys is the system working, even when the user is surprised by the result. Point them back to the file rather than making the offer.
