---
name: proposal-publish
description: Build a PDF (or docx fallback) from a proposal file via pandoc — compact layout, typst-first, with install guidance when tools are missing. Also offers a stripped hand-in export, and hands over to a workspace build script where one exists. Use when the user wants a PDF or something to email, print or hand to their supervisor, wants the proposal out of markdown, has a faculty document template to build with, or asks how to install the build tools.
license: MIT
compatibility: Building documents needs pandoc plus typst or a LaTeX engine; the skill guides installation when they are missing.
---

# Proposal Publish

Builds a PDF from a proposal file — compact layout, typst first, pandoc as the fallback — and can also produce a stripped hand-in export.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → proposal-review → **proposal-publish**. Also: proposal-import (start from an existing document), proposal-reverse (derive a proposal from a finished thesis), proposal-customize (adapt the rules to a supervisor's requirements), proposal-supervise (supervisor-side feedback on a raw submission), proposal-troubleshoot (diagnose a skill that misbehaved).

**Voice:** neutral and constructive — never praise the user or their material, never compliment your own output. Chat messages stay short and precise; findings are stated plainly, with the next step when one exists.

Publishing is optional — a proposal markdown file is an acceptable hand-in on its own. Never pressure the user into installing anything; offer the paths and their costs.

## Build

Run the build script (stdlib-only, ≥3.11):

```
python3 ${CLAUDE_SKILL_DIR}/scripts/publish.py <proposal.md>            # PDF via best available engine
python3 ${CLAUDE_SKILL_DIR}/scripts/publish.py <proposal.md> --handout  # stripped markdown export instead
```

`${CLAUDE_SKILL_DIR}` is substituted by the host with this skill's install directory; on a host that leaves it unexpanded, the script really lives in `scripts/` next to this SKILL.md, so use that path — but keep running the command from the working directory: the fallback changes where the script is found, never where you work or write. The proposal lives in the workspace's proposal location — the working directory, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory — and its outputs and any workspace build definition sit beside it. If you cannot find it, say the script did not run and name what is therefore unverified — never present your own reading of the file as the script's result.

The script resolves the best pipeline automatically: **typst** (preferred) → **LaTeX engine** → **docx** (last resort, no PDF), using the skill's `templates/` (compact layout, `RQ n:` styling, citeproc). Outputs land next to the proposal; the script also ensures the workspace `.gitignore` covers build artifacts (shared rule: whichever skill first creates an ignorable artifact adds the entry).

The proposal source carries its title as the leading `# ` line and its subtitle as the emphasized paragraph beneath it. The build maps that frame onto the rendered title block itself — pandoc's `--shift-heading-level-by=-1` plus `subtitle-filter.lua` — and infers the language from the canonical subtitle and section wordings, so `##` sections render as numbered top-level sections and the closing references heading renders unnumbered with the bibliography beneath it.

Citations render in two forms, both usable in one document: `[@key]` becomes `[1]`, and `@key` becomes `Smith et al. [1]` — the author name derived from the proposal's own reference entry, so it never has to be typed. The filter chain producing this is order-dependent (`subtitle-filter.lua` → `author-intext.lua` → `cite-split.lua` → citeproc → `rq-filter.lua` → `todo-filter.lua`); don't reorder it.

`[TODO: …]` markers render as numbered annotations rather than prose — a marker alone on its line becomes a callout block, one inside a sentence becomes a highlight, and a marker carried by the title or subtitle is numbered ahead of the body. There is deliberately no option to render them quietly: the way to a marker-free PDF is to resolve the markers, which `proposal-check` already lists.

## Workspace build script

A workspace can replace this pipeline with a build of its own — a faculty title page, a mandated cover sheet, a house style. The script looks for one **beside the proposal**, never in a directory above it, in either form:

- a file named `proposal-build` with any suffix, or none;
- a `Makefile` or `justfile` declaring a `proposal-build` target. A recipe file without that target is ignored, so an unrelated build system in the workspace changes nothing.

When one is found, publish **builds nothing** and exits 3, naming what it found. Run that definition and relay its output. It receives exactly one thing: the proposal's absolute path, in `PROPOSAL_PATH`, and — for a build file — as its first argument. The proposal's directory is the output directory.

**Exit 3 is a handover, not a failure.** Nothing went wrong: do not offer a bug report for it.

**Never fall back to the built-in pipeline when a workspace build fails.** Report the failure and stop. Producing the default layout for a workspace that asked for a different one is the worst outcome available — it succeeds visibly and is wrong invisibly. `--builtin` exists so the user can ask for the built-in document deliberately, for instance to tell a template problem from a content problem; it is never your recovery move. Two definitions beside one proposal are refused rather than chosen between — relay the refusal.

Whenever you report a built document, say which pipeline produced it. `--handout` is never delegated: it is a transform of the proposal source, not a rendered document.

A minimal build script, as `proposal-build.sh` beside the proposal (the shift flag matters: the source carries its title as a leading `# ` line and its sections at `##`, so a build without it renders an empty title above off-by-one heading levels):

```sh
#!/bin/sh
pandoc "$PROPOSAL_PATH" --shift-heading-level-by=-1 --template faculty.typ -o proposal.pdf
echo "built proposal.pdf with the faculty template"
```

The same thing as a `Makefile` target, for a workspace that already has one:

```make
proposal-build:
	pandoc "$(PROPOSAL_PATH)" --shift-heading-level-by=-1 --template faculty.typ -o proposal.pdf
```

## When tools are missing

The script reports what is missing and what it would unlock. Guide concretely, best first:

- **pandoc + typst** (recommended, two single binaries): `winget install --id JohnMacFarlane.Pandoc Typst.Typst` / `brew install pandoc typst` / distro packages. Smallest install, fastest builds.
- Existing **TeX Live/MiKTeX** works as the LaTeX fallback — nothing extra needed besides pandoc.
- Nothing installable? → `--handout` produces a clean markdown for hand-in, or suggest the user's institution machines / a colleague's setup for the final PDF.

Relay the script's messages rather than re-diagnosing; on Windows use `py` if `python3` is absent.

## Hand-in guidance

- `--handout` strips abstracts from the references block (supervisor-facing file should not be half bibliography database) — citations and entries stay intact. The handout is a deliverable meant to be kept and sent, so it is deliberately **not** gitignored.
- Because it is not gitignored, the handout is the one output a user may have edited by hand. The script refuses to replace an edited one and says so; relay that refusal instead of resolving it — renaming the file or discarding the edits is the user's decision, not yours. `--force` is for when they have decided.
- docx output uses pandoc's default styling (acceptable last resort; the compact look exists for the typst and LaTeX tiers).
- If check hasn't run recently, offer it first — but publishing proceeds on user confirmation regardless (check is advisory).

## Handing over

At a stopping point — a stage finished, a verdict given, or the user asking what now — close the message with a handoff, also when the user said they cannot answer, and do not repeat it unasked while nothing has changed. Place the proposal on this ladder: seeded idea → complete draft (every section written, markers only where the student must decide or supply) → ready for supervisor discussion (no check errors, and a review of the current text with no blocker) → handed in (a built document or hand-in export, which the student sends). Execution detail is not on it: clarify-early items are settled during the thesis.

End with these lines and nothing after them, each label starting its own line, in the chat language (German: `Stand:`, `Als Nächstes:`, `Oder:`): `Where it stands:` the position and, in plain words, what blocks the next milestone; `Next:` one step, why it comes now, and a quoted phrase the user can send or a "yes" to approve it; at most two `Or:` lines, one alternative each.

Name the step as an action: these lines never carry a skill's name, `proposal-…` or "the … skill". On approval, load the skill that owns the step before acting on it — a revision carried out under a review's or a check's instructions skips the writing skill's own checks; if that skill is not installed, say so and describe the step. Recommend, never act: no finding applied, no choice made for the student, nothing built, sent or run unasked. A choice only the student can make quotes their own text, says what the choice changes, and offers at most three options their material supports plus a way out ("or something else") — never a bare question. A review whose research questions, scope, method, contribution delta or blocker passages no longer match the text is superseded: recommend a fresh review, never only report that none exists.

After a build or a hand-in export, name the pipeline that produced it, then route by where the proposal stands. No open markers and a review of the current text with no blocker: it is handed in, and the step is the student's own — send it; supervisor feedback, once it arrives, becomes the next revision. Whichever route ends in sending, say to rename the document to carry the student's name first (supervisors receive many). Open markers in the document: resolving them, with sending it as a draft for discussion as the alternative. No current review: a review before sending, with sending it as it is as the alternative. A failed or refused build ends with its report, never with a handoff to another pipeline.

## When this run fails

If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step failed repeatedly with no user edit in between, or the state makes no sense — offer a bug report once, in these words, and do not raise it again in the same session: "Something here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send." Ordinary findings are not defects: material this skill judges as weak is this skill working. Collect nothing unless the user accepts.

A missing `pandoc` or `typst` is not a defect either — it is a toolchain the user has not installed, and the install guidance above is the answer. Make the offer only when the toolchain is present and the build still fails.
