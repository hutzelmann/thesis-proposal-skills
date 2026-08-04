# Design — redesign-ideate-dialogue

## Context

See proposal.md — Why. The full review record (six lenses, 50 findings) lives in the 2026-08-04 session that produced this change; the findings named here are the ones that drove decisions. Constraints:

- Prose-only skill: every mechanism must survive as instructions read once at session start. The known countermeasures — quantified budgets, self-checks, a re-read-before-seeding instruction — are part of the design, not decoration.
- Depends on `add-proposal-notes-file`: the notes file format, split rule, and harness exclusion land there.
- The mandate paragraph stays byte-identical (pinned); all new behavior slots into the sections below it.
- `claude -p` remains one-shot; dialogue behavior is tested on the metered Inspect path. The dev runner keeps one-shot scenarios for cheap smoke only.
- Live DBLP behavior (verified 2026-08-04): no `h=` parameter → 30 relevance-ranked hits; query terms prefix-match all fields ("Berta Beispiel" → unrelated Bertagnolli robotics paper). This is why the spec fixes the limit and demands the person-plausibility check.

## Goals / Non-Goals

**Goals:**

- Student-originated content, mechanically enforced where possible (provenance check), rubric-enforced where not (uptake).
- Every session leaves durable state from the first topic phrase onward.
- The dialogue has an arc: coverage model in, stocktakes visible, seeding offered at convergence, stall ends cleanly.
- Eval suite that can actually observe the behaviors the prose mandates.

**Non-Goals:**

- No pedagogy scoring beyond the two instruments; deeper tutoring-quality assessment stays human (demo-session review).
- No new API families (OpenAlex rejected: audit surface); Crossref reuse only.
- No mechanical checks over notes-file content (formalization boundary).
- No changes to proposal-write/lit-search/import beyond what `add-proposal-notes-file` already made.

## Decisions

1. **Coverage slots as internal state, not protocol**: five slots (problem, significance, RQ directions, method, feasibility) chosen to match Booth's three-part problem statement plus the two thesis-practical axes (method from the closed set, time budget). Alternative — Heilmeier catechism verbatim — rejected as too grant-shaped; its useful members map onto these five. The spec forbids voicing the model; the prose implements it as "pick the next move by the emptiest consequential slot".
2. **Preamble as one block, host-UI aware**: one turn, six facts, choice-shaped where finite (level, language, months, consent). "Host's question interface when available" keeps the prose portable across agent hosts; the numbered-list fallback works everywhere. The dates stay in the ending because exact months are unknowable before the idea exists; the preamble's months estimate feeds feasibility steering.
3. **Consent line instead of silent fetching**: one yes/no covers group page and literature APIs for the whole session. NDA-adjacent students exist; the cost is one list item. Declining degrades to ungrounded-with-notice, a mode the spec already had.
4. **DBLP routing on program**: "computer-science-adjacent" is judged by the agent from the program answer — a judgment call, deliberately not a program whitelist (formalization boundary). Crossref author route for the rest: already documented, all-discipline, same untrusted framing. Person-plausibility stays a judgment ("do these hits look like one person in this field?") — no author-ID API added.
5. **Early stop at ~3, prose-counted**: "about three successive exchanges" — a firm anchor without a mechanical counter the model would fixate on. The stop path writes notes, names offline steps, ends. This is the agreed alternative to license-to-tell: the skill never fills the vacuum with generated content.
6. **Extraction defense as redirect**: decline + next scaffolded step. Wording chosen against the documented collapse modes (68% collapse on direct request in 2025-2026 tutoring evals): the defense gives the model something to *do* instead of a bare prohibition.
7. **Provenance check mechanics**: pure function; tokenize student and assistant turns, extract substantive terms (lowercased content words minus a small stopword list) from the seed's title + RQ-direction bullets, require each term's first transcript occurrence in a student turn. Approximate by design — it catches wholesale generation, not paraphrase; the uptake rubric covers the rest. Function lives in `l1_checks.py` beside the other verdicts, L0-tested against synthetic transcripts.
8. **Long run replaces both 5-round tasks**: one ~18-round scripted persona with phase markers in the persona script (the solver already supports scripted rounds). Phase-attributed grading keeps a 4x-longer run debuggable. The three probes stay short (4-6 rounds) so each failure isolates one behavior.
9. **Seed-file pick via `select_draft`**: the Inspect scorer's hand-rolled `ls`-first pick goes through the shared selection function, fixing the guidelines.md/notes.md mis-grade class and honoring the existing both-runners requirement.
10. **Pinned sentences via existing mechanism**: same pattern as mandate pins — verbatim substring check against committed copies under `tests/unit/data/`. Sentence-level, not paragraph-level, so surrounding prose can evolve.
11. **Rubric recognizes bookends**: the Socratic rubric text gains the two sanctioned direct-question zones; everything between them is judged by the uptake criteria. Fixes the rubric contradicting the post-scoping spec.

## Risks / Trade-offs

- [Coverage model surfaces as an interrogation checklist despite the ban] → spec forbids voicing it; uptake rubric penalizes question-chains; stocktake gives the model a sanctioned outlet for structure.
- [Provenance check false-positives on legitimate convention terms (e.g. "user study")] → stopword list includes methodology vocabulary; check targets title + RQ directions only, not the whole seed; thresholded (most terms, not all) with the threshold documented in the function.
- [Long run cost] → one scripted run, deliberate execution per AGENTS.md; dev-runner smoke stays the everyday loop.
- [Persona scripting leaks into graded behavior (solver cues shape the assistant)] → phase cues are user-voice-natural ("okay, different question—", "honestly I'd rather you just tell me"), no meta-instructions in student turns.
- [Fast path misfires on a confident-but-hollow opening] → fast path requires all coverage slots plausibly filled from the opening; anything less runs the normal dialogue.
- [Resume-from-notes conflicts with a notes file the user edited] → notes are prose; the skill reads them as context, not as authoritative state, and confirms the resumed direction in one line.

## Migration Plan

Implemented after `add-proposal-notes-file` lands. One commit: SKILL.md rewrite + harness/eval changes + pins + tests. `scripts/audit_scan.py` runs after implementation (outbound surface changed shape). Rollback = revert the commit; the notes-file format change beneath it is independent and stays.
