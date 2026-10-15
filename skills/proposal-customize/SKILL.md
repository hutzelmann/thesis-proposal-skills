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

[paths]
proposals = "proposals/"       # the directory holding the proposal folders

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

**`[paths] proposals` moves the proposals, not the config.** It names the directory — relative to the workspace root, where this `guidelines.md` itself stays — holding the proposal folders, each proposal with its family (Workspace files below). `api-keys.env` and `bug-report/` stay at the root too. Validate before writing: the value must be a relative directory inside the workspace — refuse an absolute path, a `~`-anchored one, or anything containing `..`, naming the constraint. When the workspace already holds proposal folders at the old location, say that each must move, whole, to the configured directory and that the check reports a proposal outside it as misplaced until it does; skills look only in the configured location, never in both.

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

## Workspace files

Every proposal lives in a folder of its own in the proposal location: the working directory, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory — then only there, never both, and never in a host's scratch or temporary folder. The working directory is the workspace root: run every script from there, never from inside a proposal folder; never `cd` into a proposal folder, and name its files by their path from the root. A proposal's slug, its file name without the extension, names its folder. Inside the folder, the files that leave it carry the slug, and every other file is matched by its exact name:

| Role | File name in `<slug>/` |
|---|---|
| proposal | `<slug>.md`, leaves the folder |
| notes | `notes.md` |
| harvest record | `harvest.md` |
| review | `review.md` |
| supervisor feedback | `feedback.md` |
| handout | `<slug>.handout.md`, leaves the folder |
| built output | `<slug>.pdf`, `<slug>.typ`, `<slug>.tex` or `<slug>.docx`, each leaves the folder |
| kept file | `<label>.<ext>` |
| figure | `img/<name>.<ext>` |

The slug is derived from the working title when the proposal file is first written, and it stays when the title changes later; a draft from an existing seed goes into that file. A proposal's folder is never named `bug-report` or `img`, nor with a leading dot: a new proposal's slug takes the numeric suffix when a folder of that name exists or the name is reserved, and a new proposal never goes into another proposal's folder. Before a topic phrase exists, ideation works in `idea/` (`idea-2/` and on when taken), renamed to a provisional slug once a topic phrase exists, with the numeric suffix when taken, and to the final slug at seeding; a provisional rename that fails is retried at seeding. The slug changes only by a rename: at seeding, when the settled working title yields a different slug than the provisional one, or when the user asks. Check the target folder first. At seeding, when it is taken, the slug takes the numeric suffix and the whole family moves to it; on request, move nothing, name the collision and propose the suffixed slug. A rename moves the folder `<old>/` to `<new>/` (on PowerShell with `Rename-Item`, which refuses an existing target); verify that `<new>/` holds the files and that no `<new>/<old>/` exists, and stop if it does; then, when the folder holds `<old>.md`, rename it to `<new>.md`. Role-named files, figures and kept files keep their names, so no link changes. When a move fails, stop, overwrite nothing, and say what moved and what did not; when the error names a file another program holds open, name it and offer to retry. Built outputs and the hand-in export under the old slug stay in the folder as previous outputs: name them and offer a rebuild. Say what you renamed.

Besides proposal folders, the workspace holds only: `guidelines.md`, `api-keys.env`, `bug-report/` and `.gitignore` at the root; in a proposal's folder, a workspace build definition (a file named `proposal-build`, with or without an extension, or a `Makefile`, `GNUmakefile` or `justfile` with a `proposal-build` target), the files that build reads and writes, and the `.gitignore` the built-in build adds; the troubleshooting captures `check-output.txt` and `version-output.txt` while a report is assembled; and the installers' `.agents/skills/`, `.claude/skills/`, `.kiro/skills/`, `.opencode/skill/` and `.opencode/skills/`, the record `.thesis-proposal-install.json` and `skills-lock.json`, which you never write or tidy. Nothing else goes there. Script output, candidate lists, raw responses, probes and logs stay in the chat. Read output too large for one piece in slices — a page range, the next lines — or produce it narrower. A temporary folder outside the workspace is a fallback only where one is writable, and a refused one is never a reason to write into the workspace. Keep a file only when the user asks, in the proposal's or the idea's folder: a kept file is `<label>.<ext>` under a free label, never `notes`, `review`, `feedback`, `harvest`, `handout`, `img` or the slug itself.

## Handing over

At a stopping point — a stage finished, a verdict given, or the user asking what now — close the message with a handoff, also when the user said they cannot answer, and do not repeat it unasked while nothing has changed. Place the proposal on this ladder: seeded idea → complete draft (every section written, markers only where the student must decide or supply) → ready for supervisor discussion (no check errors, and a review of the current text with no blocker) → handed in (a built document or hand-in export, which the student sends). Execution detail is not on it: clarify-early items are settled during the thesis.

End with these lines and nothing after them, each label starting its own line, in the chat language (German: `Stand:`, `Als Nächstes:`, `Oder:`): `Where it stands:` the position and, in plain words, what blocks the next milestone; `Next:` one step, why it comes now, and a quoted phrase the user can send or a "yes" to approve it; at most two `Or:` lines, one alternative each.

Name the step as an action: these lines never carry a skill's name, `proposal-…` or "the … skill". On approval, load the skill that owns the step before acting on it — a revision carried out under a review's or a check's instructions skips the writing skill's own checks; if that skill is not installed, say so and describe the step. Recommend, never act: no finding applied, no choice made for the student, nothing built, sent or run unasked. When the next step is a choice only the student can make, the `Next:` line quotes the passage it concerns, says what the choice changes, offers at most three options taken from their own material, and ends with "or something else" — never a bare question, and a recommendation never replaces the options. For example: `Next: RQ2 asks whether the oracles "improve test quality", which no result could prove wrong; your methodology already measures mutation score and faults found — which result would you stand behind? Reply "mutation score", "faults found", "both", or something else.` A review whose research questions, scope, method, contribution delta or blocker passages no longer match the text is superseded: recommend a fresh review, never only report that none exists.

After the workspace `guidelines.md` is written, the step is the one the user was on before, now under the new rules — a check of an existing proposal first, since the overrides change what it reports. A workspace with no proposal yet hands over to developing the idea.

## When this run fails

If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step failed repeatedly with no user edit in between, or the state makes no sense — offer a bug report once, in these words, and do not raise it again in the same session: "Something here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send." Ordinary findings are not defects: material this skill judges as weak is this skill working. Collect nothing unless the user accepts.

An override that another skill then obeys is the system working, even when the user is surprised by the result. Point them back to the file rather than making the offer.
