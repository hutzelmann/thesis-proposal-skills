---
name: proposal-troubleshoot
description: Diagnose a problem with the proposal skills themselves — a script that fails, a rule applied wrongly, output that contradicts the skill's own stated mandate — and assemble a bug report when it turns out to be a real defect. Use when a skill misbehaved, not when the proposal needs improving.
license: MIT
metadata:
  version: 0.9.0
---

# Troubleshooting

Diagnoses a problem with the proposal skills themselves: a failing script, a rule applied wrongly, output that contradicts a stated mandate. Most causes turn out not to be defects and end here; where one is, the outcome is a bug report a maintainer can act on.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → proposal-review → proposal-publish. Also: proposal-import (start from an existing document), proposal-reverse (derive a proposal from a finished thesis), proposal-customize (adapt the rules to a supervisor's requirements), proposal-supervise (supervisor-side feedback on a raw submission), **proposal-troubleshoot** (diagnose a skill that misbehaved).

**Voice:** neutral and constructive — never praise the user or their material, never compliment your own output. Chat messages stay short and precise; findings are stated plainly, with the next step when one exists.

**Work the ladder below before you collect anything, and stop at the first rung that explains the problem.** Most reported problems are not defects: a stale install, a model that cannot do the task, a supervisor's override doing its job, or output the user simply dislikes. Each of those ends the run with an answer and no report. Assemble a report only for a failing script, a violated mandate, or a cause the ladder cannot identify — and transmit nothing: the bundle is written into the user's own workspace, and who sees it is their decision.

Naming the rung is part of the answer. A report that says "it did not work" costs a maintainer a round-trip; a report that says "rung 4, the check skill edited my file" is actionable on sight. When no rung fits, say so and record the cause as unidentified rather than choosing the rung that sounds closest.

## Target

Establish two things before diagnosing: which skill misbehaved, and what the user expected instead. If the problem concerns a proposal file, resolve it the way the other skills do — explicit mention wins; exactly one proposal folder's `<slug>/<slug>.md` ending in a `---` metadata block auto-picks; several candidates means listing them and asking. The search space is the proposal folders in the proposal location (Workspace files below). Never treat a `notes.md` or anything inside `bug-report/` as the proposal.

A problem need not concern a proposal at all. An ideation session that crashed before seeding anything is still reportable.

## The ladder

### Rung 0 — stale install

Ask the user to update and retry before anything else, the same way they installed:

- a `.thesis-proposal-install.json` sits beside the installed skills (in `.agents/skills` or `.claude/skills`, in their home or working directory) — they used the install prompt: paste it again, from https://github.com/hutzelmann/thesis-proposal-skills#quick-start, and answer its question with the record's `scope` (`all` is all projects, `folder` is only this folder)
- their app's plugin page lists **Thesis Proposal** — its update action, **Check for updates**
- they installed from a terminal — `npx skills update`

When you cannot tell which, name all three. Do not try to establish whether their install is current by comparing revisions — the record names the installed one, but you cannot know the newest. The published snapshot can trail the fixed code by weeks, so this rung resolves more reports than every other rung combined. If they confirm they already updated, say so in the report; it saves the maintainer from asking.

### Rung 1 — the model cannot do this task

Read the shipped verdicts at `references/model-support.json` relative to this skill's directory. Look up the model that produced the failure: your own when the failure happened in this session, otherwise the one the user names for that run, which may not be you. Use its exact identifier — the one your host states, or the user's own spelling — not a display name, and not an alias such as `sonnet`, which names no version. When that exact string is absent, compare spellings instead: ignore letter case, everything up to the last `/`, a cloud provider's wrapping such as a leading `us.anthropic.` or a trailing `-v1:0`, a trailing date stamp with year, month and day such as `-20251001` or `-2025-10-01`, and a bracketed suffix such as `[1m]`, and read a dash between two digits as a dot. Claude Code reports `claude-haiku-4-5-20251001` where the data keys the same model as `anthropic/claude-haiku-4.5`. A different version number is a different model: never take the verdict of the nearest version, and when two entries fit equally, treat the model as having no entry.

- `fail` for the skill in question — the model is the cause. Name it, say which models the data records as working, and stop.
- `flaky` — the same run may succeed on retry. Say so before anything heavier.
- `untested`, or no entry for the model at all — say the rung is unevaluated and move on. Absence of measurement is not evidence of support, and must never be reported as "your model is fine".

A failure on a model already recorded as failing is still worth reporting if the user wants to: it is fresh evidence about that model. Offer it as optional, and mark the report as model evidence rather than as a defect.

### Rung 2 — a supervisor's override is responsible

If the workspace holds `guidelines.md`, read it. When the behavior the user objects to is what those overrides ask for — a work plan where the defaults forbid one, a section list that differs, a page limit — the skills are working as designed. Name the override responsible, quote the line, and stop. The override wins over the defaults — whether the user is the student who received it or the supervisor who wrote it; that is the whole point of the file.

### Rung 3 — a script failed

A shipped script exiting non-zero, a missing `python3`, an absent `pandoc` or `typst`, a network refusal. This is a defect or an environment gap, and both are worth a report. Capture the script's output to a file first — the report carries it as evidence:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/check.py <location>/<slug>/<slug>.md > check-output.txt 2>&1
```

This skill ships its own copy of the check script, identical to proposal-check's.

The collector records whether `pandoc` and `typst` are present but never their versions: it runs no other program, which is what keeps a shipped script cheap to audit. When a version is plausibly the cause — a PDF that builds but lays out wrongly, for instance — have the user run `typst --version` or `pandoc --version`, capture that to `version-output.txt`, and pass it in with a second `--script-output`. It then travels as measured evidence rather than as something you asserted.

### Rung 4 — a skill violated its own mandate

The highest-value rung. Each of these contradicts something a skill states about itself:

- a read-only skill changed a file — `proposal-check` reports a digest mismatch when this happens
- a reference appeared that resolves to nothing, or whose title does not match its DOI
- a `[TODO: …]` marker was filled in with invented content instead of being left standing
- a work plan, a phase table, or an expected-results section was written
- personal data was left in after an import
- the proposal was edited during a check or a review

Report these. They are what the project's own tests are built around, so a confirmed one usually becomes a new test case.

### Rung 5 — the output is disliked but broke no rule

Thin argument, a research question that reads flat, a section the user finds weak. This is not a defect. Point them at `proposal-review` for a substance verdict, or at `proposal-customize` if the defaults do not match what their supervisor wants. Assemble no report.

A run that cost many times the usual and produced correct output lands here too: the host's effort or workflow mode fanned the task out into many helper agents, against the execution shape the skill states where it states one. Name that mode and the host's own budget and effort controls as the remedy, and assemble no report.

## Assembling the report

Only for rungs 3 and 4, for an unidentified cause, or for optional model evidence from rung 1.

**1. Show what would leave the workspace, before writing anything.** Run the collector in dry-run mode and put its manifest in front of the user:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/collect.py <location>/<slug>/<slug>.md --dry-run
```

`${CLAUDE_SKILL_DIR}` is substituted by the host with this skill's install directory; on a host that leaves it unexpanded, both scripts really live in `scripts/` next to this SKILL.md, so use that path — but keep running the commands from the workspace root, the working directory, where `<location>` is the proposal location (`.` unless `[paths] proposals` sets another): the report bundle and the captured output are written there, the check measures the proposal's placement and its orphan findings from there, and the fallback changes where a script is found, never where you work or write. If you cannot find a script, say it did not run and name what is therefore unverified — never assemble a report by hand and present it as the collector's output. `python3` stands for any Python 3.11 or newer that answers here (`python`, `py -3`, or a versioned name such as `python3.13`); keep the one that worked for the rest of the conversation.

**2. Take the disclosure decision from the user, not from yourself.** Three levels, and the default is the most protective:

| Level | What the report carries |
|---|---|
| `minimal` (default) | No proposal prose at all: counts, hashes, how many section headings are canonical (the title heading is never counted), the environment, and script output with the user's own wording redacted — the proposal's name too, wherever a path carries it |
| `structure` | Adds section headings, `[TODO: …]` texts and reference DOIs verbatim. The leading `# ` line is the unpublished thesis title — it appears masked, never verbatim. Still no body prose |
| `full` | Adds the proposal text, title included, with names, addresses and numbers removed |

Every level also stores the Log section of the proposal's `notes.md`, with the proposal's name replaced below `full`, and nothing else of that file. State what the chosen level includes and what the next one up would add. The proposal is an unpublished research idea, so never infer consent to a higher level from the user's eagerness to get the bug fixed. `minimal` is enough for most script defects, because the captured script output travels with it.

**3. Write the bundle.**

```
python3 ${CLAUDE_SKILL_DIR}/scripts/collect.py <location>/<slug>/<slug>.md --level minimal --script-output check-output.txt
```

It refuses to overwrite an existing `bug-report/`. If one is there, ask whether it is still needed before passing `--force`. Once the bundle is written it carries the captures, so offer to remove `check-output.txt` and `version-output.txt` from the workspace.

**4. Fill in the `[self-reported]` fields.** The collector leaves them as placeholders because it cannot know them. Edit `bug-report/report.md` and fill in:

- the rung reached and whether it is a defect
- what the user asked for, what happened, what was expected instead, which skill and which step
- your own model identifier exactly as your host states it — not a display name, and not an alias such as `sonnet` — and your harness

Leave the `[measured]` lines exactly as the collector wrote them. The two tags exist so a maintainer can tell what a script established from what you are asserting — you are the subject of this report, and blurring that line makes it worth less. If you do not know your own model identifier, write that you do not know it rather than guessing.

## The reproduction seed

Only when the defect reproduces from a file and a command — a script crash, a check finding that is wrong, a publish failure. Skip it for anything that turns on judgement.

Reduce: copy the proposal, cut sections until the defect stops appearing, restore the last cut. Replace every trace of the user's real content with synthetic material as you go — invented topic, `Erika Musterfrau`, matriculation `00000000` — and confirm the reduced file still triggers the defect. The reproduction is a workspace of its own, shaped like the user's: write the reduced file to `bug-report/repro/input/input.md` — `input` stands in for the slug, so the topic's name never reaches the report — add a copy of `guidelines.md` to `bug-report/repro/` only when the defect depends on it, and write the exact command, run from `bug-report/repro/`, to `bug-report/repro/command.txt`. Confirm the defect from there: run from anywhere else, the check reports the reduced file as misplaced.

If reduction never isolates it, record that the attempt was made and failed. Never construct a reproduction that does not actually reproduce: it sends a maintainer after a mechanism that is not there, which is worse than sending prose alone.

## Delivering it

The bundle is local and nothing has been sent. Tell the user their options and stop:

- open a prefilled issue. Build the URL from the filled `report.md`: start with `https://github.com/hutzelmann/thesis-proposal-skills/issues/new?template=skill-defect.yml`, then append URL-encoded query parameters for the form's short fields — `skill` (which skill misbehaved), `rung` (the exact text of the matching triage-outcome option), `what_happened` (that section of the report), `self_reported` (the `[self-reported]` model and harness lines), `route` (from the report's install-route line: installer → `Install prompt (the installer)`, plugin → `Plugin button in the app`, CLI → `From a terminal (npx skills)`, several → `More than one of these`, unknown → `Not sure`). Give the user the URL and name what is left to do by hand: tick the updated-first box, paste the `[measured]` lines plus `hashes.txt` into the environment field, paste the captured script output, and attach `repro/` if there is one — those are too long to travel in a URL. If the URL itself grows past a few thousand characters, leave `what_happened` out of it and say so.
- email `report.md`, or hand it to their supervisor if the material is sensitive enough that they would rather it not be public
- keep it, and delete `bug-report/` once it has been sent

The URL carries nothing beyond what the chosen disclosure level already put into `report.md` — building it changes no privacy decision. Do not open it, do not offer to file the issue, and do not file it: the user reviews the form and submits it themselves. This skill transmits nothing, has no credentials, and must not acquire either.

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

When a rung resolved the problem, the step is the one the user was on before it. When a report was assembled, the step is the user's own — send it by one of the routes above — and after that, the step they were on. Never file, send or open anything for them.
