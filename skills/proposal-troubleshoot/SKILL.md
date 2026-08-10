---
name: proposal-troubleshoot
description: Diagnose a problem with the proposal skills themselves — a script that fails, a rule applied wrongly, output that contradicts the skill's own stated mandate — and assemble a bug report when it turns out to be a real defect. Use when a skill misbehaved, not when the proposal needs improving.
---

# Troubleshooting

Diagnoses a problem with the proposal skills themselves: a failing script, a rule applied wrongly, output that contradicts a stated mandate. Most causes turn out not to be defects and end here; where one is, the outcome is a bug report a maintainer can act on.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → proposal-review → proposal-publish. Also: proposal-import (start from an existing document), proposal-customize (adapt the rules to a supervisor's requirements), proposal-supervise (supervisor-side feedback on a raw submission), **proposal-troubleshoot** (diagnose a skill that misbehaved).

**Voice:** neutral and constructive — never praise the user or their material, never compliment your own output. Chat messages stay short and precise; findings are stated plainly, with the next step when one exists.

**Work the ladder below before you collect anything, and stop at the first rung that explains the problem.** Most reported problems are not defects: a stale install, a model that cannot do the task, a supervisor's override doing its job, or output the user simply dislikes. Each of those ends the run with an answer and no report. Assemble a report only for a failing script, a violated mandate, or a cause the ladder cannot identify — and transmit nothing: the bundle is written into the user's own workspace, and who sees it is their decision.

Naming the rung is part of the answer. A report that says "it did not work" costs a maintainer a round-trip; a report that says "rung 4, the check skill edited my file" is actionable on sight. When no rung fits, say so and record the cause as unidentified rather than choosing the rung that sounds closest.

## Target

Establish two things before diagnosing: which skill misbehaved, and what the user expected instead. If the problem concerns a proposal file, resolve it the way the other skills do — explicit mention wins; exactly one markdown file ending in a `---` metadata block auto-picks; several candidates means listing them and asking. Never treat `<slug>.notes.md` or anything inside `bug-report/` as the proposal.

A problem need not concern a proposal at all. An ideation session that crashed before seeding anything is still reportable.

## The ladder

### Rung 0 — stale install

Ask the user to update and retry before anything else:

```
npx skills add hutzelmann/thesis-proposal-skills
```

Do not try to establish whether their install is current by reading a version — the installed skills carry none. The published snapshot can trail the fixed code by weeks, so this rung resolves more reports than every other rung combined. If they confirm they already updated, say so in the report; it saves the maintainer from asking.

### Rung 1 — the model cannot do this task

Read the shipped verdicts at `references/model-support.json` relative to this skill's directory. Find the running model by its identifier, matching on the part after the last `/` when the exact string is absent: an agent reports itself as `claude-opus-5` where the data keys it as `anthropic/claude-opus-5`.

- `fail` for the skill in question — the model is the cause. Name it, say which models the data records as working, and stop.
- `flaky` — the same run may succeed on retry. Say so before anything heavier.
- `untested`, or no entry for the model at all — say the rung is unevaluated and move on. Absence of measurement is not evidence of support, and must never be reported as "your model is fine".

A failure on a model already recorded as failing is still worth reporting if the user wants to: it is fresh evidence about that model. Offer it as optional, and mark the report as model evidence rather than as a defect.

### Rung 2 — a supervisor's override is responsible

If the workspace holds `guidelines.md`, read it. When the behavior the user objects to is what those overrides ask for — a work plan where the defaults forbid one, a section list that differs, a page limit — the skills are working as designed. Name the override responsible, quote the line, and stop. The override wins over the defaults — whether the user is the student who received it or the supervisor who wrote it; that is the whole point of the file.

### Rung 3 — a script failed

A shipped script exiting non-zero, a missing `python3`, an absent `pandoc` or `typst`, a network refusal. This is a defect or an environment gap, and both are worth a report. Capture the script's output to a file first — the report carries it as evidence:

```
python3 .claude/skills/proposal-check/scripts/check.py <proposal.md> > check-output.txt 2>&1
```

The collector records whether `pandoc` and `typst` are present but never their versions: it runs no other program, which is what keeps a shipped script cheap to audit. When a version is plausibly the cause — a PDF that builds but lays out wrongly, for instance — have the user run `typst --version` or `pandoc --version`, capture that to a file too, and pass it in. It then travels as measured evidence rather than as something you asserted.

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

## Assembling the report

Only for rungs 3 and 4, for an unidentified cause, or for optional model evidence from rung 1.

**1. Show what would leave the workspace, before writing anything.** Run the collector in dry-run mode and put its manifest in front of the user:

```
python3 .claude/skills/proposal-troubleshoot/scripts/collect.py <proposal.md> --dry-run
```

Paths are relative to the workspace root for a standard project install; the script really lives in `scripts/` next to this SKILL.md, so use that location if the skill is installed elsewhere. If you cannot find it, say the script did not run and name what is therefore unverified — never assemble a report by hand and present it as the collector's output.

**2. Take the disclosure decision from the user, not from yourself.** Three levels, and the default is the most protective:

| Level | What the report carries |
|---|---|
| `minimal` (default) | No proposal prose at all: counts, hashes, how many headings are canonical, the environment, and script output with the user's own wording redacted |
| `structure` | Adds headings, `[TODO: …]` texts and reference DOIs verbatim. Still no body prose |
| `full` | Adds the proposal text, with names, addresses and numbers removed |

State what the chosen level includes and what the next one up would add. The proposal is an unpublished research idea, so never infer consent to a higher level from the user's eagerness to get the bug fixed. `minimal` is enough for most script defects, because the captured script output travels with it.

**3. Write the bundle.**

```
python3 .claude/skills/proposal-troubleshoot/scripts/collect.py <proposal.md> --level minimal --script-output check-output.txt
```

It refuses to overwrite an existing `bug-report/`. If one is there, ask whether it is still needed before passing `--force`.

**4. Fill in the `[self-reported]` fields.** The collector leaves them as placeholders because it cannot know them. Edit `bug-report/report.md` and fill in:

- the rung reached and whether it is a defect
- what the user asked for, what happened, what was expected instead, which skill and which step
- your own model identifier and harness

Leave the `[measured]` lines exactly as the collector wrote them. The two tags exist so a maintainer can tell what a script established from what you are asserting — you are the subject of this report, and blurring that line makes it worth less. If you do not know your own model identifier, write that you do not know it rather than guessing.

## The reproduction seed

Only when the defect reproduces from a file and a command — a script crash, a check finding that is wrong, a publish failure. Skip it for anything that turns on judgement.

Reduce: copy the proposal, cut sections until the defect stops appearing, restore the last cut. Replace every trace of the user's real content with synthetic material as you go — invented topic, `Erika Musterfrau`, matriculation `00000000` — and confirm the reduced file still triggers the defect. Write it to `bug-report/repro/input.md` with the exact command in `bug-report/repro/command.txt`.

If reduction never isolates it, record that the attempt was made and failed. Never construct a reproduction that does not actually reproduce: it sends a maintainer after a mechanism that is not there, which is worse than sending prose alone.

## Delivering it

The bundle is local and nothing has been sent. Tell the user their options and stop:

- open a prefilled issue. Build the URL from the filled `report.md`: start with `https://github.com/hutzelmann/thesis-proposal-skills/issues/new?template=skill-defect.yml`, then append URL-encoded query parameters for the form's short fields — `skill` (which skill misbehaved), `rung` (the exact text of the matching triage-outcome option), `what_happened` (that section of the report), `self_reported` (the `[self-reported]` model and harness lines). Give the user the URL and name what is left to do by hand: tick the updated-first box, paste the `[measured]` lines plus `hashes.txt` into the environment field, paste the captured script output, and attach `repro/` if there is one — those are too long to travel in a URL. If the URL itself grows past a few thousand characters, leave `what_happened` out of it and say so.
- email `report.md`, or hand it to their supervisor if the material is sensitive enough that they would rather it not be public
- keep it, and delete `bug-report/` once it has been sent

The URL carries nothing beyond what the chosen disclosure level already put into `report.md` — building it changes no privacy decision. Do not open it, do not offer to file the issue, and do not file it: the user reviews the form and submits it themselves. This skill transmits nothing, has no credentials, and must not acquire either.
