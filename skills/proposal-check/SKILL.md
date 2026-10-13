---
name: proposal-check
description: Low-level check of a thesis proposal — required sections, citation consistency, forbidden content, format guardrails, typos — closing with where it stands and the next step. Use when the user asks to check their proposal, suspects a section or citation is missing or malformed, wants a quick gate before publishing, or asks where their proposal stands or what to do next. Not content feedback — for whether the argument holds, use proposal-review. Advisory only.
license: MIT
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

Resolve the proposal file: explicit user mention wins; exactly one markdown file ending in a `---` metadata block → auto-pick; several candidates → list them and ask. The search space is the workspace's proposal location: the working directory, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory — then look only there, never in both. A `<slug>.notes.md` is never a candidate, and neither is anything under `bug-report/`: a reduced reproduction left there by the troubleshoot skill is a structurally valid proposal, so it would otherwise win the pick and quietly redirect the check away from the real draft.

## Step 1 — deterministic script

Run (use `py` instead of `python3` on Windows if needed):

```
python3 ${CLAUDE_SKILL_DIR}/scripts/check.py <proposal.md>
```

`${CLAUDE_SKILL_DIR}` is substituted by the host with this skill's install directory; on a host that leaves it unexpanded, the script really lives in `scripts/` next to this SKILL.md. If you cannot find it, say the script did not run and name what is therefore unverified — never present your own reading of the file as the script's result.

- Requires Python ≥ 3.11. If Python is missing, tell the user how to install it (python.org, or `winget install Python.Python.3.12` / `brew install python`) and perform the script's checks yourself as well as possible, stating that determinism is reduced.
- The script reads `references/structure.json` (canonical skeleton) and the workspace `guidelines.md` TOML override automatically — first beside the proposal, else in the working directory (the workspace root when proposals live in a configured subdirectory). Run it from the workspace root so that second position resolves.
- Relay its two buckets verbatim: mechanical errors, mechanical warnings (possible false positives — say so). Never claim semantic rules passed.

## Step 2 — agent pass

After the script, check yourself and report findings in the same chat message:

- Typos, grammar, and wording issues (full list — this is the exhaustive pass; the review skill only hints).
- Content-level forbidden material regexes cannot catch: expected results asserted in prose as though already obtained (an outcome phrased as an expectation — "the thesis expects", "it is hypothesized" — is the guidelines' required form, not a finding), personal data in unusual forms, the writer's own name in body text (the script only flags the `author:` metadata key), supervisor references, confidentiality phrasing.
- Whether the timeline section names a real timeframe. The script only measures its shape — that it holds no table, list or subsection and stays within three lines — so read it and say whether it actually states when the thesis starts and ends. Accept the phrasings students really use: month names in either language, `SoSe 2027`, `WS 2026/27`, `Q3 2027`, "winter semester", or a plain "as soon as possible". Flag it only when no timeframe is stated at all, or when a `[TODO: …]` marker is still standing in for one.
- Work plans the script cannot see. A Gantt chart or phase table pasted in as an image passes every structural rule, so an image or figure inside the timeline section is a finding, and so is a phase narrative crammed onto one line.
- The thesis title, in the parts no pattern reaches. The script matches implementation openers, a fixed buzzword list, question form and length; it cannot know that a proper noun names a tool, a product, a platform, a vendor or the company the thesis is written at, and it cannot tell a whole research field from a thesis. Read the title — the leading `# ` line — and say which it is. When you flag it, say that the title is printed on the study certificate, and offer one to three abstracted alternatives naming the contribution and its object. A named technology that is the object of the proposal's own research questions — a literature review of one platform, a user study of one specific environment — is correct as written and gets no finding.
- Do NOT judge semantic quality here (analytical RQs, argument soundness, literature fit) — that is a review's, which the handoff recommends when no current review covers the text. The title bullet above is the single exception, and it stops at the title: it exists because a title finding is cheapest to act on before anyone reads the draft, and because the script raises half of it already.

## Reporting

One chat message: script buckets first, agent findings second, then a one-line verdict that scopes its own claim ("mechanically clean, N warnings, M language issues — substance not judged"), then the handoff lines from Handing over below — `Where it stands:`, `Next:`, at most two `Or:`. No file output. **Never edit the proposal during a check run** — not even obvious fixes; report only. Editing happens in a separate step, only after the user explicitly asks, following the write skill's conventions (minimal surgical edits).

## Handing over

At a stopping point — a stage finished, a verdict given, or the user asking what now — close the message with a handoff, also when the user said they cannot answer, and do not repeat it unasked while nothing has changed. Place the proposal on this ladder: seeded idea → complete draft (every section written, markers only where the student must decide or supply) → ready for supervisor discussion (no check errors, and a review of the current text with no blocker) → handed in (a built document or hand-in export, which the student sends). Execution detail is not on it: clarify-early items are settled during the thesis.

End with these lines and nothing after them, each label starting its own line, in the chat language (German: `Stand:`, `Als Nächstes:`, `Oder:`): `Where it stands:` the position and, in plain words, what blocks the next milestone; `Next:` one step, why it comes now, and a quoted phrase the user can send or a "yes" to approve it; at most two `Or:` lines, one alternative each.

Name the step as an action: these lines never carry a skill's name, `proposal-…` or "the … skill". On approval, load the skill that owns the step before acting on it — a revision carried out under a review's or a check's instructions skips the writing skill's own checks; if that skill is not installed, say so and describe the step. Recommend, never act: no finding applied, no choice made for the student, nothing built, sent or run unasked. A choice only the student can make quotes their own text, says what the choice changes, and offers at most three options their material supports plus a way out ("or something else") — never a bare question. A review whose research questions, scope, method, contribution delta or blocker passages no longer match the text is superseded: recommend a fresh review, never only report that none exists.

A user who asks only where the proposal stands, or what to do next, gets this same run, ending here. Before handing over, read what sits beside the proposal — `<slug>-review.md` and `<slug>.notes.md`, where they exist — and nothing else. Judge only whether the review still covers the text: its research questions, scope, method, contribution delta and the passages its blockers cite, set against the current file. That is information for the handoff, never a substance verdict, and the read-only mandate holds throughout.

Routes, first match wins: errors → a writing pass that fixes them; open markers that are decisions the student owes the proposal → those decisions, put as anchored choices, since a review would only raise them again; clean, with no review or a superseded one → a fresh review; clean, with a current review that has blockers → revising those blockers; clean, with a current review and no blocker → the hand-in build, with this pass's language findings fixed on the way — never a reason for another review. Sort open `[TODO: …]` markers: decisions the student owes the proposal — a research question, the method, the timeframe, an indispensable dependency — block the next milestone; a marker whose answer the text already constrains — a stated selection rule, a pilot that fixes it, a format or tooling choice — is an execution detail whose deferral record (the guidelines' Readiness section) can be filled: propose moving those to the notes file in an `Or:` line — a writing step the user approves, never part of this run.

## When this run fails

If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step failed repeatedly with no user edit in between, or the state makes no sense — offer a bug report once, in these words, and do not raise it again in the same session: "Something here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send." Ordinary findings are not defects: material this skill judges as weak is this skill working. Collect nothing unless the user accepts.

A digest mismatch is the one finding here that is always a defect: it means the file changed during a read-only run. Report it as such and make the offer.
