---
name: proposal-write
description: Write a thesis proposal from scratch or refine an existing one, following the proposal guidelines and grounding claims in the literature. Use when the user wants a draft, wants sections improved, wants bullet points turned into prose, or asks to apply review findings.
---

# Proposal Write

Produces the actual proposal text — a first draft from a seed file, sharper prose from bullet points, or a revision that works through a review's findings one by one, with every claim tied to something in the literature.

**Workflow:** proposal-ideate → proposal-lit-search → **proposal-write** → proposal-check → proposal-review → proposal-publish. Also: proposal-import (start from an existing document), proposal-customize (adapt the rules to a supervisor's requirements).

You write and refine thesis proposals in the single-file format: markdown body, trailing `---` metadata block (`title`, `subtitle`, `lang`, `references` in CSL-YAML), preceded by a blank line. Proposals are anonymous: no `author` key, no writer name in the text.

## Ground rules

Read `references/guidelines.md` first — it is the authority on structure, research-question quality, methodology content, citations, and writing style. If the workspace contains a `guidelines.md`, its TOML block and prose override the defaults (per-key wins, lists replace, forbidden sections may be allowed again).

Non-negotiable regardless of overrides:

- Cite only keys that exist in the proposal's `references` block. Never invent a publication. Missing support → `[TODO: add key reference for …]`.
- Pick the citation form by grammatical role: `@key` (renders `Smith et al. [1]`) wherever the authors belong in the running text — as the sentence's subject, or as the possessor of the thing discussed ("the detector of @key") — and `[@key]` (renders `[1]`) where the citation is evidence for a claim. Never type an author name beside a bracketed citation; `@key` derives it from the reference entry.
- Never fabricate facts the user did not provide. Uncertain statement → keep it out or mark `[TODO: verify …]`. Visible `[TODO: 3–10 word hint]` markers for every gap — in body text, never inside a section heading: a heading that carries a marker no longer parses as the section it names.

Strong defaults (workspace `guidelines.md` may override them):

- One sentence per line in the source file.
- Research questions analytical (to what degree / under which conditions / comparative), never "how can X be implemented", never yes/no-answerable. This is the most common failure — check your own output against it before finishing.

## From scratch

1. Collect what exists (idea notes from ideate, user's description, any seed references). Do not interview the user exhaustively — write the best draft the material supports and mark gaps as TODOs.
2. Create `<slug>.md` (lowercase, hyphenated, 2–4 title words; numeric suffix on collision) with the five canonical sections in order and the methodology matching the user's method — exactly one from the closed set. The order is checked, not just the presence of each section. If the material defers or leaves open the methodology choice, deciding is your job — never defer it to the heading: pick the methodology the research questions best support, write its canonical heading, and record the open confirmation as `[TODO: confirm methodology choice]` in the section body.
3. In the methodology, reference every research question as `(RQn)` at the end of the sentence describing how it is answered — one question per statement.
4. Close with the timeline: one sentence naming the start month and the submission month. If the material does not say and the user is there to ask, ask once; otherwise write `[TODO: state start month and submission month, or "as soon as possible"]`. Write "as soon as possible" only when the user has actually said so — it is their claim to make, and a user with a registered submission date would be misrepresented by it. Never a table, never phases: that is forbidden work-plan content, not a fuller timeline.
5. If the check reports a reference shortfall, say so and suggest running the literature-search skill (ideally snowballing) before polishing further.

## Refining

- Minimal, surgical edits: preserve the author's substance and voice; touch only what the request or the review finding requires.
- "Apply the review": work through `<slug>-review.md` item by item, reporting per item what changed or why it was skipped.
- Never rewrite untouched sections wholesale; never silently delete author content — flag conflicts instead.

## Language

Write in the proposal's `lang`. German: canonical German section titles (see `references/guidelines.md` title table), English scientific terms with German capitalization, active voice (avoid "soll … werden" chains), third person only.

## Verify before you report

Never report a writing pass you have not checked. Run (Windows: `py` instead of `python3`):

```
python3 .claude/skills/proposal-write/scripts/check.py <slug>.md
```

Paths are relative to the workspace root for a standard project install; the script really lives in `scripts/` next to this SKILL.md, so use that location if the skill is installed elsewhere. If you cannot find it, say the script did not run and name what is therefore unverified — never present your own reading of the file as the script's result.

Fix every error it reports — except the two findings below, the first of which the script counts as an error — then run it again, until the only findings left are the ones the source material caused. The script's closing line calls the check advisory; that describes the standalone check skill's role, not yours: for a writing pass the error list is binding, and a finished pass may still end with the script exiting non-zero on the tolerated shortfall. This is you checking your own fresh output — not the check skill, which is read-only and never edits. Drafts fail the same handful of rules over and over — a drifted section title, an unterminated metadata block, a cited key missing from `references`, a forgotten `(RQn)` reference — and the script names them precisely, so this is faster than re-reading the file yourself.

Two findings you must **not** "fix":

- **Too few references.** Inventing a publication is the one unforgivable error — and so is padding the list with placeholder entries. Report the shortfall and suggest the literature-search skill.
- **Open `[TODO: …]` markers.** They are the honest record of what the material did not supply. The guidelines' hand-in checklist ("no TODO markers remain") is satisfied by obtaining the missing material, never by deleting a marker.

## Finishing a pass

State what you changed, what the check still reports, and which TODOs remain. Do not run publish unasked.
