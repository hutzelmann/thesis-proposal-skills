---
name: proposal-publish
description: Build a PDF (or docx fallback) from a proposal file via pandoc — compact layout, typst-first, with install guidance when tools are missing. Also offers a stripped hand-in export, and hands over to a workspace build script where one exists. Use when the user wants a PDF or something to email, print or hand to their supervisor, wants the proposal out of markdown, has a faculty document template to build with, or asks how to install the build tools.
license: MIT
compatibility: Building documents needs pandoc plus typst or a LaTeX engine; the skill guides installation when they are missing.
metadata:
  version: 0.9.0
---

# Proposal Publish

Builds a PDF from a proposal file — compact layout, typst first, pandoc as the fallback — and can also produce a stripped hand-in export.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → proposal-review → **proposal-publish**. Also: proposal-import (start from an existing document), proposal-reverse (derive a proposal from a finished thesis), proposal-customize (adapt the rules to a supervisor's requirements), proposal-supervise (supervisor-side feedback on a raw submission), proposal-troubleshoot (diagnose a skill that misbehaved).

**Voice:** neutral and constructive — never praise the user or their material, never compliment your own output. Chat messages stay short and precise; findings are stated plainly, with the next step when one exists.

Publishing is optional — a proposal markdown file is an acceptable hand-in on its own. Never pressure the user into installing anything; offer the paths and their costs.

## Build

Run the build script (stdlib-only, ≥3.11):

```
python3 ${CLAUDE_SKILL_DIR}/scripts/publish.py <location>/<slug>/<slug>.md            # PDF via best available engine
python3 ${CLAUDE_SKILL_DIR}/scripts/publish.py <location>/<slug>/<slug>.md --handout  # stripped markdown export instead
```

`${CLAUDE_SKILL_DIR}` is substituted by the host with this skill's install directory; on a host that leaves it unexpanded, the script really lives in `scripts/` next to this SKILL.md, so use that path — but keep running the command from the workspace root, the working directory: the fallback changes where the script is found, never where you work or write. `<location>` is the workspace's proposal location — `.`, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory — and the proposal's outputs and any workspace build definition sit beside it in its folder. If you cannot find it, say the script did not run and name what is therefore unverified — never present your own reading of the file as the script's result. `python3` stands for any Python 3.11 or newer that answers here (`python`, `py -3`, or a versioned name such as `python3.13`); keep the one that worked for the rest of the conversation.

The script resolves the best pipeline automatically: **typst** (preferred) → **LaTeX engine** → **docx** (last resort, no PDF), using the skill's `templates/` (compact layout, `RQ n:` styling, citeproc). Outputs land next to the proposal in its folder; the script also ensures the `.gitignore` in that folder covers build artifacts (shared rule: whichever skill first creates an ignorable artifact adds the entry). Figures linked as `img/<name>.<ext>` are found in the proposal's folder whatever directory the build runs from. On a build that succeeds, pandoc's warnings come through — a figure it could not find, for instance: relay them.

The proposal source carries its title as the leading `# ` line and its subtitle as the emphasized paragraph beneath it. The build maps that frame onto the rendered title block itself — pandoc's `--shift-heading-level-by=-1` plus `subtitle-filter.lua` — and infers the language from the canonical subtitle and section wordings, so `##` sections render as numbered top-level sections and the closing references heading renders unnumbered with the bibliography beneath it.

Citations render in two forms, both usable in one document: `[@key]` becomes `[1]`, and `@key` becomes `Smith et al. [1]` — the author name derived from the proposal's own reference entry, so it never has to be typed. The filter chain producing this is order-dependent (`subtitle-filter.lua` → `author-intext.lua` → `cite-split.lua` → citeproc → `rq-filter.lua` → `todo-filter.lua`); don't reorder it.

`[TODO: …]` markers render as numbered annotations rather than prose — a marker alone on its line becomes a callout block, one inside a sentence becomes a highlight, and a marker carried by the title or subtitle is numbered ahead of the body. There is deliberately no option to render them quietly: the way to a marker-free PDF is to resolve the markers, which `proposal-check` already lists.

## Workspace build script

A workspace can replace this pipeline with a build of its own — a faculty title page, a mandated cover sheet, a house style. The script looks for one **in the proposal's folder**, never in a directory above it — one at the workspace root is never used, so a faculty build goes into each proposal's folder — in either form:

- a file named `proposal-build` with any suffix, or none;
- a `Makefile` or `justfile` declaring a `proposal-build` target. A recipe file without that target is ignored, so an unrelated build system in the workspace changes nothing.

When one is found, publish **builds nothing** and exits 3, naming what it found. Run that definition and relay its output. It receives exactly one thing: the proposal's absolute path, in `PROPOSAL_PATH`, and — for a build file — as its first argument. The proposal's folder is the output directory.

**Exit 3 is a handover, not a failure.** Nothing went wrong: do not offer a bug report for it.

**Never fall back to the built-in pipeline when a workspace build fails.** Report the failure and stop. Producing the default layout for a workspace that asked for a different one is the worst outcome available — it succeeds visibly and is wrong invisibly. `--builtin` exists so the user can ask for the built-in document deliberately, for instance to tell a template problem from a content problem; it is never your recovery move. Two definitions in one proposal's folder are refused rather than chosen between — relay the refusal.

Whenever you report a built document, say which pipeline produced it. `--handout` is never delegated: it is a transform of the proposal source, not a rendered document.

A minimal build script, as `proposal-build.sh` in the proposal's folder (the shift flag matters: the source carries its title as a leading `# ` line and its sections at `##`, so a build without it renders an empty title above off-by-one heading levels):

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

- **pandoc + typst** (recommended, two single binaries): `winget install --id JohnMacFarlane.Pandoc -e` and `winget install --id Typst.Typst -e` / `brew install pandoc typst` / distro packages. Smallest install, fastest builds.
- No package manager, or one that fails with an error about its sources (winget `0x8a15000f`, for example): point the user to the install guide's PDF-export section, https://github.com/hutzelmann/thesis-proposal-skills/blob/main/docs/install.md#pdf-export, rather than repairing the package manager.
- Existing **TeX Live/MiKTeX** works as the LaTeX fallback — nothing extra needed besides pandoc.
- Nothing installable? → `--handout` produces a clean markdown for hand-in, or suggest the user's institution machines / a colleague's setup for the final PDF.

Relay the script's messages rather than re-diagnosing.

## Hand-in guidance

- `--handout` writes `<slug>.handout.md` beside the proposal and strips abstracts from the references block (supervisor-facing file should not be half bibliography database) — citations and entries stay intact. The handout is a deliverable meant to be kept and sent, so it is deliberately **not** gitignored.
- Because it is not gitignored, the handout is the one output a user may have edited by hand. The script refuses to replace an edited one and says so; relay that refusal instead of resolving it — renaming the file or discarding the edits is the user's decision, not yours. `--force` is for when they have decided.
- docx output uses pandoc's default styling (acceptable last resort; the compact look exists for the typst and LaTeX tiers).
- If check hasn't run recently, offer it first — but publishing proceeds on user confirmation regardless (check is advisory).

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

After a build or a hand-in export, name the pipeline that produced it, then route by where the proposal stands. No open markers and a review of the current text with no blocker: it is handed in, and the step is the student's own — send it; supervisor feedback, once it arrives, becomes the next revision. Whichever route ends in sending, say to rename the document to carry the student's name first (supervisors receive many); a hand-in export keeps its `.handout.md` ending, as the script's hint says, since under a plain `.md` name it would read as a second proposal. Open markers in the document: resolving them, with sending it as a draft for discussion as the alternative. No current review: a review before sending, with sending it as it is as the alternative. A failed or refused build ends with its report, never with a handoff to another pipeline.

## When this run fails

If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step failed repeatedly with no user edit in between, or the state makes no sense — offer a bug report once, in these words, and do not raise it again in the same session: "Something here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send." Ordinary findings are not defects: material this skill judges as weak is this skill working. Collect nothing unless the user accepts.

A missing `pandoc` or `typst` is not a defect either — it is a toolchain the user has not installed, and the install guidance above is the answer. Make the offer only when the toolchain is present and the build still fails.
