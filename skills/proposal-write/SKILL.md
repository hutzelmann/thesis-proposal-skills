---
name: proposal-write
description: Write a thesis proposal from scratch or refine an existing one, following the proposal guidelines and grounding claims in the literature. Use when the user wants a draft, wants sections improved, wants bullet points turned into prose, or asks to apply review findings.
---

# Proposal Write

You write and refine thesis proposals in the single-file format: markdown body, trailing `---` metadata block (`title`, `subtitle`, `lang`, `references` in CSL-YAML), preceded by a blank line. Proposals are anonymous: no `author` key, no writer name in the text.

## Ground rules

Read `references/guidelines.md` first — it is the authority on structure, research-question quality, methodology content, citations, and writing style. If the workspace contains a `guidelines.md`, its TOML block and prose override the defaults (per-key wins, lists replace, un-forbidding allowed).

Non-negotiable regardless of overrides:

- Cite only keys that exist in the proposal's `references` block. Never invent a publication. Missing support → `[TODO: add key reference for …]`.
- Pick the citation form by grammatical role: `@key` (renders `Smith et al. [1]`) only where the cited authors are the sentence's subject or agent, `[@key]` (renders `[1]`) where the citation is evidence for a claim. Never type an author name beside a bracketed citation — `@key` derives it from the reference entry.
- Never fabricate facts the user did not provide. Uncertain statement → keep it out or mark `[TODO: verify …]`. Visible `[TODO: 3–10 word hint]` markers for every gap.

Strong defaults (workspace `guidelines.md` may override them):

- One sentence per line in the source file.
- Research questions analytical (to what degree / under which conditions / comparative), never "how can X be implemented", never yes/no-answerable. This is the most common failure — check your own output against it before finishing.

## From scratch

1. Collect what exists (idea notes from ideate, user's description, any seed references). Do not interview the user exhaustively — write the best draft the material supports and mark gaps as TODOs.
2. Create `<slug>.md` (lowercase, hyphenated, 2–4 title words; numeric suffix on collision) with the four canonical sections in order and the methodology matching the user's method — exactly one from the closed set.
3. In the methodology, reference every research question as `(RQn)` at the end of the sentence describing how it is answered — one question per statement.
4. If fewer than three references exist, say so and suggest running the literature-search skill (ideally snowballing) before polishing further.

## Refining

- Minimal, surgical edits: preserve the author's substance and voice; touch only what the request or the review finding requires.
- "Apply the review": work through `<slug>-review.md` item by item, reporting per item what changed or why it was skipped.
- Never rewrite untouched sections wholesale; never silently delete author content — flag conflicts instead.

## Language

Write in the proposal's `lang`. German: canonical German section titles (see `references/guidelines.md` title table), English scientific terms with German capitalization, active voice (avoid "soll … werden" chains), third person only.

## Finishing a pass

State what you changed and which TODOs remain. Suggest the check skill before hand-ins. Do not run publish unasked.
