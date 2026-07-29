---
name: proposal-check
description: Low-level check of a thesis proposal — required sections, citation consistency, forbidden content, format guardrails, typos. Use when the user asks to check their proposal, before handing it to a supervisor, or as a quick gate before review or publish. Advisory only.
---

# Proposal Check

Deterministic low-level checks plus a language pass for one proposal file. Results go to chat only — never write a report file. This check is advisory: it gates nothing; other skills may run it first but proceed on user confirmation.

## Target

Resolve the proposal file: explicit user mention wins; exactly one markdown file ending in a `---` metadata block → auto-pick; several candidates → list them and ask.

## Step 1 — deterministic script

Run (use `py` instead of `python3` on Windows if needed):

```
python3 scripts/check.py <proposal.md>
```

- Requires Python ≥ 3.11. If Python is missing, tell the user how to install it (python.org, or `winget install Python.Python.3.12` / `brew install python`) and perform the script's checks yourself as well as possible, stating that determinism is reduced.
- The script reads `references/structure.json` (canonical skeleton) and the workspace `guidelines.md` TOML override automatically.
- Relay its two buckets verbatim: mechanical errors, mechanical warnings (possible false positives — say so). Never claim semantic rules passed.

## Step 2 — agent pass

After the script, check yourself and report findings in the same chat message:

- Typos, grammar, and wording issues (full list — this is the exhaustive pass; the review skill only hints).
- Content-level forbidden material regexes cannot catch: expected results asserted in prose, personal data in unusual forms, supervisor references, confidentiality phrasing.
- Do NOT judge semantic quality here (analytical RQs, argument soundness, literature fit) — point the user to the review skill for that.

## Reporting

One chat message: script buckets first, agent findings second, then a one-line verdict ("mechanically clean, N warnings, M language issues"). No file output. **Never edit the proposal during a check run** — not even obvious fixes; report only. Editing happens in a separate step, only after the user explicitly asks, following the write skill's conventions (minimal surgical edits).
