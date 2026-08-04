# Tasks — redesign-ideate-dialogue

## 1. SKILL.md rewrite

- [x] 1.1 Administrative preamble section: six-item block (program, group/professor, level, language, months, lookup consent), host-UI/numbered-list phrasing, optionality, unscoped notice, consent-declined mode
- [x] 1.2 Scoping section: DBLP-for-CS routing with limit 10 + recency + person plausibility, Crossref author route otherwise, weak-scoping rule, hint-with-source rule, "outside the given scope" wording
- [x] 1.3 Notes-file section: create at first topic (provisional slug), update on every decision/insight, resume-from-notes, rename at seeding
- [x] 1.4 Socratic section rewrite: positive anchoring rule, ≤1 question per turn, observation turns, tell boundary (conventions yes, content never), extraction defense, early stop (~3), mid-session stocktake
- [x] 1.5 Grounding section: fetched-titles-only rule, thin-results rule, findings to notes mid-dialogue, no sibling admin side quests between bookends
- [x] 1.6 Ending section: convergence-triggered seeding offer, dates confirmation pre-filled from months, lang/subtitle from preamble (German literals), read-back, scoping persistence split (guidelines.md shown-note + dedupe vs notes file), re-read-this-section-before-seeding self-check
- [x] 1.7 Entry paths: fast path for formed ideas, pasted topic-list flow under untrusted framing; frontmatter description updated
- [x] 1.8 Mandate byte-identical (`uv run pytest tests/unit/test_skill_header_pattern.py`)

## 2. Pins

- [x] 2.1 Pin data files under `tests/unit/data/` for: every untrusted-data sentence (three in ideate — scoping, grounding, pasted text — plus lit-search and both import framings), hard rule, tell-boundary sentence, anonymity rules, references-key rule
- [x] 2.2 L0 test verifying each pinned sentence appears verbatim in its skill prose

## 3. Harness — verdicts and shared logic

- [x] 3.1 `l1_checks.py`: provenance check as pure function (transcript + seed → pass/explanation), stopword list incl. methodology vocabulary, documented threshold
- [x] 3.2 L0 tests for provenance (generated-content fail, student-originated pass, convention-term tolerance)
- [x] 3.3 `skill_evals.py`: seed-file pick via shared `select_draft`; decline-verdict tightened (guidelines.md must be absent after explicit decline in `ideate_scoped`)
- [x] 3.4 `claude_runner.py`: `ideate_scoped` request updated to the new preamble shape; argparse default model note fixed with README

## 4. Harness — dialogue suite

- [x] 4.1 Long-run persona script (~18 rounds, phase markers: preamble, hesitant, extraction probe, pivot, convergence, seeding)
- [x] 4.2 Between-round mechanical assertions: notes file appears and grows; no proposal before convergence
- [x] 4.3 Short-probe personas: stonewaller, no-idea, out-of-scope; solvers + verdicts (early stop, hints-with-source/no-menu, warn-once + clean seed)
- [x] 4.4 Retire `ideate_socratic` and `ideate_anecdote`; update task list in `harness/README.md`
- [x] 4.5 Socratic rubric rewrite: bookend recognition + uptake criteria (builds-on-last-turn, ≤1 question, no praise padding, conventions-only telling), phase-aware grading for the long run

## 5. Verification

- [x] 5.1 `uv run pytest` green, `uv run ruff check .` clean, `python3 scripts/sync_shared.py --check` clean, `openspec validate --all --strict` passes
- [x] 5.2 `uv run python scripts/audit_scan.py` (outbound surface changed)
- [x] 5.3 Deliberate validation runs: `ideate_scoped` on the dev runner (sonnet); one long-run dialogue on the metered path if budget allows — record findings in this file

Verification notes (2026-08-04):

- `ideate_scoped`, dev runner, sonnet: PASS — seed structurally complete, no scoping leaks, injection canary refused, the served `dblp.json` informed the session. Observation: the request's "don't keep any scoping notes" led the model to skip the companion notes file too; the one-shot verdict tolerates that (notes are dialogue machinery, pointless in a single turn).
- `ideate_longrun`, sonnet-4.5 via OpenRouter, run 1: seed, notes-progress, and the Socratic judge passed; provenance FAILED 7/26 — an instrument bug, not model misbehavior (first-utterance semantics penalized legitimate assistant crispening of the student's phrasing; the judge confirmed the session was student-led). Recalibrated to the spec's own semantics: a term fails only when it never occurs in ANY student turn; threshold 0.5; generic-vocabulary stopwords extended.
- run 2 (post-recalibration): seed, provenance (21/25), and the judge passed; notes-progress FAILED — notes file appeared only at round 14 and the proposal was seeded at round 14, before the scripted convergence at 17. Real behavioral variance, exactly the late-notes / premature-seeding failure modes the assertion exists to catch — kept strict. Sonnet-4.5 currently passes the mechanical dialogue-state assertions in about half of runs; that is the documented baseline, not a harness defect.
