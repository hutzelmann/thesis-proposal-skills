# Redesign Ideate Dialogue

## Why

A six-lens review of the ideation skill (2026-08-04) found the Socratic core under-specified in exactly the places LLM tutoring is documented to fail: no convergence criterion or detectable ending (both harnesses inject artificial "enough" cues to make it seed at all), no defense against answer-extraction pressure or stonewalling, a hard rule that bans a question's surface form rather than its function, admin facts (language, level, time budget) guessed or learned too late, DBLP queried for non-CS programs with confident wrong results, and everything before the final turn lost if the session dies. The evals only reinforce the surface rule: cooperative 5-round personas, graded on "never asks directly".

## What Changes

- **Administrative preamble block**: the one scoping question becomes one administrative block at session start — study program, research group/professor (name or URL), degree level, proposal language, available months (approximate), and a one-line lookup-consent question — multiple choice where the host offers a question UI, else a compact numbered list, all parts still optional. The ending keeps only the exact start/submission dates, pre-filled from the months estimate. Declined lookup consent means no outbound queries: ideation runs on the user's words alone, stated plainly.
- **Notes file from first topic**: ideate becomes the primary producer of the companion `<slug>.notes.md` (format per `add-proposal-notes-file`): created as soon as a topic phrase exists (provisional slug, renamed at seeding if the working title diverged), updated whenever a decision, rejected direction, or insight lands. Session dies mid-way → the notes survive and a later session resumes from them. The proposal file is seeded at convergence or on "enough" — a stonewalled session leaves only notes, never a hollow proposal.
- **Scoping persistence split**: proposal-invariant facts (study program, degree level) go to workspace `guidelines.md` — offered once, the composed note shown before appending, duplicates checked; proposal-specific context (interests, candidate group when the student is still shopping) goes to the notes file. A group the student is committed to across proposals may go to `guidelines.md` on the same shown-note terms.
- **Convergence via coverage slots**: the dialogue holds an internal coverage model — problem, why-it-matters (significance), candidate RQ directions, plausible method, feasibility within the stated months — used to pick the next provocation and to trigger a seeding offer when the slots are filled. Never voiced as a checklist or question script. A mid-session stocktake (one-breath "standing / open" mirror) replaces the invisible-progress drift.
- **Tell boundary**: conventions yes, content never. The skill may state the rules of the game — the closed methodology set, canonical sections, the analytical-RQ convention — once the student's own thinking has surfaced the need. It never supplies idea content (topics, research questions, the method choice for their problem). On extraction pressure ("just give me three research questions") it declines and offers the next scaffolded step instead. The hard rule is restated positively: every provocation anchors in something the student already said; at least one exemplar is an observation, not a question.
- **Early stop**: after about three successive exchanges that produce no student contribution, the skill names the impasse plainly, saves the state to the notes file, suggests concrete offline steps (read the group's page, talk to the supervisor), and ends without seeding a proposal.
- **Fetch routing by program**: DBLP only for computer-science-adjacent programs, with an explicit result limit of 10, recency judged from the returned years, and a sanity check that hits plausibly belong to the named person; other programs use the already-documented Crossref endpoint with an author query. Mixed or thin results are said to be weak scoping, never silently trusted. Only fetched titles may be named as literature — a paper that did not appear in a fetch result is never cited to the student, and empty-but-successful responses count as thin, not as license to recall from memory.
- **Entry paths**: a student with an already-solid idea gets a fast path — literature check, convergence confirmation, seed — instead of pushback theater; a student who brings a supervisor's topic list (pasted text or document) discusses that list freely — the no-menu rule constrains the skill's own hints, not the student's material, and pasted third-party text falls under the same untrusted-data framing as fetched pages.
- **Bilingual seeding**: German subtitle literals ("Exposé zur Bachelorarbeit" / "Exposé zur Masterarbeit") defined beside the English pair; `lang` comes from the preamble answer, never inferred from chat language.
- **Eval rewrite**: the two 5-round cooperative dialogue tasks are retired. New: one long composite run (~18 rounds: preamble → hesitant phase → extraction probe → pivot → convergence → seeding) with notes-file growth asserted between rounds, and three short probes — stonewaller (early stop fires), no-idea (hints, no menu), out-of-scope idea (warn once, chat only). Two pedagogy instruments: a provenance check (content terms of seeded RQ candidates must first appear in student turns — pure function, L0-tested) and an uptake criterion in the L2 rubric (builds on the student's last turn, at most one question per turn, no praise padding, telling only for conventions). Small harness fixes ride along: the Socratic rubric learns the two administrative bookends, the Inspect seed-file pick goes through the shared selection function, the README example stops running the documented-failing model, and the runner verdict fails a scoping note written after an explicit decline.
- **L0 pins for load-bearing sentences**: the untrusted-data framings, the hard rule, the tell-boundary sentence, the anonymity rules, and the references-key rule get pinned copies enforced offline, like mandates.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-ideate`: Socratic interaction style (positive anchoring rule, tell boundary, extraction defense, early stop), Research-group scoping (preamble block, consent, routing, persistence split), Literature-grounded ideation (fetched-titles-only, thin-results rule), Seeds the proposal file (convergence trigger, notes-file lifecycle, bilingual subtitles, dates pre-fill) — plus new requirements for the notes-file working memory, coverage-slot convergence, and entry paths.
- `testing-harness`: Multi-turn ideation testing rewritten — long composite run, adversarial probes, provenance and uptake instruments, retirement of the cooperative-only tasks.
- `skill-packaging`: load-bearing sentences pinned offline alongside mandates.

## Impact

- `skills/proposal-ideate/SKILL.md` — substantial rewrite (mandate paragraph unchanged; if review forces a reword, its pinned copy moves in the same change).
- `harness/skill_evals.py`, `harness/l1_checks.py`, `harness/rubrics/`, `harness/personas/` — task replacement, new personas (stonewaller, no-idea, formed-idea), provenance verdict, rubric updates, shared seed-file selection.
- `harness/claude_runner.py`, `harness/README.md` — scenario updates, decline-verdict tightening, example/default model fix.
- `tests/unit/` — pinned-sentence test + data files, provenance-function tests, selection tests.
- `tests/fixtures/g01-research-group/` — reused; `dblp.json` finally exercised.
- Depends on `add-proposal-notes-file` (file format and selection exclusion land there).
- Security: outbound surface changes shape (Crossref author queries added, DBLP restricted); `scripts/audit_scan.py` runs after implementation. Consent gate reduces silent outbound traffic.
