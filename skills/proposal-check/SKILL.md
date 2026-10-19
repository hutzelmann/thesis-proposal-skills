---
name: proposal-check
description: Low-level check of a thesis proposal — required sections, citation consistency, forbidden content, format guardrails, typos — closing with where it stands and the next step. Use when the user asks to check their proposal, suspects a section or citation is missing or malformed, wants a quick gate before publishing, or asks where their proposal stands or what to do next. Not content feedback — for whether the argument holds, use proposal-review. Advisory only.
license: MIT
metadata:
  version: 0.9.0
---

# Proposal Check

Checks a thesis proposal before hand-in: required sections, citations that do not resolve, content that must not appear, format guardrails, and typos. Findings come back as one list in chat, in time to fix them before a supervisor sees them.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → **proposal-check** → proposal-review → proposal-publish. Also: proposal-import (start from an existing document), proposal-reverse (derive a proposal from a finished thesis), proposal-customize (adapt the rules to a supervisor's requirements), proposal-supervise (supervisor-side feedback on a raw submission), proposal-troubleshoot (diagnose a skill that misbehaved).

**Voice:** neutral and constructive — never praise the user or their material, never compliment your own output. Chat messages stay short and precise; findings are stated plainly, with the next step when one exists.

**Read-only skill: you MUST NOT modify any file during a check run — no fixes, no edits, however obvious. You diagnose and report; nothing else.** Editing happens in a separate step, only after the user explicitly asks, via the write skill. A request that asks for both at once — "check it and fix what it reports" — is two steps rather than an exception to this one: the check ends at the report, and the fixes are the write skill's step, bound by its rules on which findings must not be "fixed".

The script prints a `digest:` line — the SHA-256 of the exact content it checked. If you are running non-interactively (no user watching the conversation), verify the mandate mechanically: re-run the script once more as the last step of the check — before any edit, including one the user has already asked for — and compare the two `digest:` lines. If they differ, the file changed during the check — report that prominently as a violation of the read-only mandate instead of presenting the results as a clean run. Never change file permissions or touch the file in any way to enforce this; the unchanged digest is the proof.

Deterministic low-level checks plus a language pass for one proposal file. Results go to chat only — never write a report file. This check is advisory: it gates nothing; other skills may run it first but proceed on user confirmation.

## Execution shape

Two steps, one agent: the script runs once — a second time only for the digest comparison the read-only mandate requires of a non-interactive run — and the agent pass below is one reading of the file by you. Nothing here is handed to helper agents, not per finding category, per section, or per finding, and both steps report in the one chat message. When Python is missing and you perform the script's checks yourself, that is the same single reading.

## Target

Resolve the proposal file: explicit user mention wins, and a file named that way is checked where it lies; otherwise a candidate is a proposal folder's own `<slug>/<slug>.md` ending in a `---` metadata block — exactly one → auto-pick; several → list them and ask. The search space is the proposal folders in the proposal location (Workspace files below); look only there. A `notes.md` is never a candidate, and neither is anything under `bug-report/`: a reduced reproduction left there by the troubleshoot skill is a structurally valid proposal, so it would otherwise win the pick and quietly redirect the check away from the real draft.

## Step 1 — deterministic script

Run:

```
python3 <skill-dir>/scripts/check.py <location>/<slug>/<slug>.md
```

`<skill-dir>` stands for this skill's own folder, the one holding this SKILL.md, which the host names when it loads the skill (as its base directory, or as the path of this SKILL.md); replace it with that folder's path. Run the command from the workspace root, the working directory, where `<location>` is the proposal location (`.` unless `[paths] proposals` sets another), and pass a file the user named by its path from there: the script measures the proposal's placement and its orphan findings from the working directory, so a run from inside a proposal folder reports a misplaced proposal. If you cannot find it, say the script did not run and name what is therefore unverified — never present your own reading of the file as the script's result. `python3` stands for any Python 3.11 or newer that answers here (`python`, `py -3`, or a versioned name such as `python3.13`); keep the one that worked for the rest of the conversation.

- Requires Python ≥ 3.11. If none answers, say so, point the user to https://github.com/hutzelmann/thesis-proposal-skills/blob/main/docs/install.md#no-python-yet and perform the script's checks yourself as well as possible, stating that determinism is reduced.
- The script reads `references/structure.json` (canonical skeleton) and the workspace `guidelines.md` TOML override automatically — first in the proposal's folder, else in the working directory. Its `guidelines:` line names which position governed, never a path: `none (defaults)` where the workspace has a `guidelines.md` means the run did not start at the workspace root — say so.
- Relay its two buckets verbatim: mechanical errors, mechanical warnings (possible false positives — say so). Never claim semantic rules passed.
- A `proposal-misplaced` error means the proposal is not at `<location>/<slug>/<slug>.md` from where the run started: when the run started elsewhere, say so and put a rerun from the workspace root in the handoff's `Next:` line; otherwise offer moving the proposal and its family into its folder as an anchored choice in the handoff. A `proposal-folder-mismatch` error is a rename that stopped halfway, with the folder and the proposal file named differently: offer finishing it as Workspace files below describes.
- A `companion-orphaned` warning names a family file outside its proposal's folder — at a root, in a folder that holds no proposal, notes file or harvest record, or a second proposal or a proposal folder inside this one — usually left by a rename or a move that stopped halfway: relay it; for files that belong to this proposal, offer moving them into its folder, under the names Workspace files below gives them, as an anchored choice in the handoff, and leave a file the user placed there on purpose where it is; never rename or move a file during the check.
- A `build-definition-unused` warning names a build definition at a root, where the publish step never looks: relay it, and offer copying it into each proposal folder that should be built with it.

## Step 2 — agent pass

After the script, check yourself and report findings in the same chat message:

- Typos, grammar, and wording issues (full list — this is the exhaustive pass; the review skill only hints).
- Content-level forbidden material regexes cannot catch: expected results asserted in prose as though already obtained (an outcome phrased as an expectation — "the thesis expects", "it is hypothesized" — is the guidelines' required form, not a finding), personal data in unusual forms, the writer's own name in body text (the script only flags the `author:` metadata key), supervisor references, confidentiality phrasing.
- Whether the timeline section names a real timeframe. The script only measures its shape — that it holds no table, list or subsection and stays within three lines — so read it and say whether it actually states when the thesis starts and ends. Accept the phrasings students really use: month names in either language, `SoSe 2027`, `WS 2026/27`, `Q3 2027`, "winter semester", or a plain "as soon as possible". Flag it only when no timeframe is stated at all, or when a `[TODO: …]` marker is still standing in for one.
- Work plans the script cannot see. A Gantt chart or phase table pasted in as an image passes every structural rule, so an image or figure inside the timeline section is a finding, and so is a phase narrative crammed onto one line.
- The thesis title, in the parts no pattern reaches. The script matches implementation openers, a fixed buzzword list, question form and length; it cannot know that a proper noun names a tool, a product, a platform, a vendor or the company the thesis is written at, and it cannot tell a whole research field from a thesis. Read the title — the leading `# ` line — and say which it is. When you flag it, say that the title is printed on the study certificate, and offer one to three abstracted alternatives naming the contribution and its object. A named technology that is the object of the proposal's own research questions — a literature review of one platform, a user study of one specific environment — gets no title finding here; whether the research depends on it is the review's swap test.
- Do NOT judge semantic quality here (analytical RQs, argument soundness, literature fit) — that is a review's, which the handoff recommends when no current review covers the text. The title bullet above is the single exception, and it stops at the title: it exists because a title finding is cheapest to act on before anyone reads the draft, and because the script raises half of it already.

## Reporting

One chat message: script buckets first, agent findings second, then a one-line verdict that scopes its own claim ("mechanically clean, N warnings, M language issues — substance not judged"), then the handoff lines from Handing over below — `Where it stands:`, `Next:`, at most two `Or:`. No file output. **Never edit the proposal during a check run** — not even obvious fixes; report only. Editing happens in a separate step, only after the user explicitly asks, following the write skill's conventions (minimal surgical edits).

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

A user who asks only where the proposal stands, or what to do next, gets this same run, ending here. Before handing over, read what sits beside the proposal in its folder — `review.md` and `notes.md`, where they exist — and nothing else. Judge only whether the review still covers the text: its research questions, scope, method, contribution delta and the passages its blockers cite, set against the current file. A `review-questions-changed` warning from the script settles the research questions: the review judged other ones and is superseded, whatever the size of the difference, and counts as superseded in the routes below. That is information for the handoff, never a substance verdict, and the read-only mandate holds throughout.

Routes, first match wins: errors → a writing pass that fixes them, or for a placement error the move from Step 1; open markers that are decisions the student owes the proposal → those decisions, put as anchored choices, since a review would only raise them again; clean, with no review or a superseded one → a fresh review; clean, with a current review that has blockers → revising those blockers; clean, with a current review and no blocker → the hand-in build, with this pass's language findings fixed on the way — never a reason for another review. Sort open `[TODO: …]` markers: decisions the student owes the proposal — a research question, the method, the timeframe, an indispensable dependency — block the next milestone; a marker whose answer the text already constrains — a stated selection rule, a pilot that fixes it, a format or tooling choice — is an execution detail whose deferral record (the guidelines' Readiness section) can be filled: propose moving those to the notes file in an `Or:` line — a writing step the user approves, never part of this run.

## When this run fails

If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step failed repeatedly with no user edit in between, or the state makes no sense — offer a bug report once, in these words, and do not raise it again in the same session: "Something here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send." Ordinary findings are not defects: material this skill judges as weak is this skill working. Collect nothing unless the user accepts.

A digest mismatch is the one finding here that is always a defect: it means the file changed during a read-only run. Report it as such and make the offer.
