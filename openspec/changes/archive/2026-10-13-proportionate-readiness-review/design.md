# Design

## Context

Three skills judge or act on proposal readiness: `proposal-review` (the student's verdict), `proposal-supervise` (the professor's feedback, which by its own spec reuses the review rules and "SHALL NOT introduce a separate quality rubric"), and `proposal-write` (which applies a review). All three already read `references/guidelines.md`, the generated copy of `shared/guidelines/guidelines.md`. The six substance tests live there and are cited by name; a drift guard keeps their count consistent across guidance, skills, specs and pins (`2026-10-03-guard-non-serving-material`).

Supervise already has a round ledger (`Resubmission intake`); review has none. The notes file already has an `Open Points` section and write already keeps non-blocking open points out of the proposal ("Proposal TODOs are for submission-blocking gaps only"). The design reuses those seams rather than adding new ones. See proposal.md for the motivation.

## Goals / Non-Goals

**Goals:**
- One readiness rule, stated once, that every judging skill and every student reads.
- A verdict that is a function of an explicit list, so "ready" is reachable by construction.
- Convergence across rounds that is checkable from the artifacts alone.
- Evals that fail on overblocking as reliably as the existing ones fail on underblocking.

**Non-Goals:**
- No seventh substance test, no TOML key, no change to `check.py`.
- No new proposal section, no work plan, no new artifact type.
- No metered run; matrix cells for the new tasks are a later, cost-gated decision.
- No change to the idea-stage evidence bar or the borderline deferral.

## Decisions

**D1 — The rule lives in the shared guidance, not in a SKILL.md.** A `## Readiness` section after `## Substance Tests` in `shared/guidelines/guidelines.md`. Supervise inherits it through its existing "apply the review rules exactly as the review skill would", write through its existing guidelines read, and students learn what a proposal does *not* have to settle. *Alternative:* state it in `proposal-review/SKILL.md` only — supervise would then need a copy (two bars that drift), and write would keep pushing execution detail into the text because nothing it reads says the detail can wait.

**D2 — The verdict is derived from the blocker list.** ready ⇔ no blocker stands (earlier-round open blockers included); needs revision ⇔ at least one, all repairable in place; no viable thesis core unchanged. The stopping rule is then structural rather than a plea for restraint: a reviewer who wants to withhold `ready` must write a blocker, and a blocker must carry its reason. *Alternative:* keep the holistic tier and add "do not overblock" prose — that is the current state plus an exhortation, and the current state is what failed.

**D3 — The deferral record is the proof of deferrability.** A finding is clarify-early only if its five-field record can be filled; the "reasonable way to resolve it" and "would an adverse outcome reopen the proposal" fields are exactly the evidence that the item does not touch the core. A finding whose record cannot be filled is a blocker by elimination. The record does double duty as the early-thesis agenda the request asks for, so the agenda costs nothing extra and cannot drift from the classification. *Alternatives:* (a) require the proposal itself to state a plausible approach — pushes protocol sentences into the text, the creep this change removes; (b) leave it to judgement — unverifiable, and the rubric would have nothing to grade.

**D4 — Blockers are the existing substance tests minus necessity; no new test.** The request's blocker list maps one-to-one: unanswerable question → falsifiability/method-fit, unclear contribution (thin literature included) → delta/swap, method cannot answer → method-fit, implausible scope and doubtful indispensable resource → executability. The executability definition gains one sentence ("a plausible plan, not a finalized protocol") because that test is where execution detail was being demanded. *Alternative:* a seventh "dependency test" — reopens the substance-test-count drift guard, every pin naming "six", and the supervise evidence bar, for a property executability already owns.

**D5 — Text-level findings never block alone.** Necessity, density, title and citation-practice findings become optional refinements; they are still reported in full. This reverses the 2026-10-03 scenario "necessity-only → needs revision", deliberately: a removable neighbouring-field paragraph does not stop a supervisor from judging the core. The guard against the real failure that change targeted stays: material that *obscures* the contribution or the questions is filed as the delta or research-question blocker it causes. The supervise idea-stage bar already excluded necessity failures, so it is unaffected.

**D6 — The agenda is the review's clarify-early section; write moves it to the notes file.** No third review-side artifact and no new notes section: `Open Points` already means "non-blocking open points". Review stays read-only beyond its own file. Because write records the items in the notes and never in the proposal, the next review does not see protocol text it could audit — the escalation loop is cut where it starts. *Alternatives:* a separate `<slug>-agenda.md` (another artifact for troubleshoot and supervise to learn), or review writing the notes directly (a second write target, and the review would lose the evidence behind each deferral).

**D7 — Monotone rounds, decided from the artifacts.** Review reads the previous `<slug>-review.md` before overwriting it (as supervise already does). "Unchanged" is decided by whether the passage the earlier finding quoted or located is still present as it was — not by git, which a student's workspace may not use. A finding about unchanged text keeps or lowers its class. A new blocker needs changed text or the label "missed in the earlier round" with the flaw stated, and the chat summary counts those labels so a supervisor sees reviewer churn rather than inheriting it. *Alternatives:* changed-text-only (a genuine flaw missed in round one could never block — underblocking); any new blocker with an explanation (no structural brake; an explanation can always be produced).

**D8 — Supervise: points are blockers, plus one labelled block.** Numbered points: zero to five, blockers only — a ready feedback has none. A fixed run-in label ("Clarify early in the thesis" / "Früh in der Arbeit zu klären") introduces at most five one-line items after the points and before the strengths, in ready and needs-revision feedback, stated as settled once the thesis starts and not as resubmission conditions. The fixed label serves the paste channel (bold run-in, no heading) and makes the block checkable. Placement order: verdict → earlier-round sentence → scope paragraph → points → clarify-early block → what to keep → closing note. Workload unknowns split by whether they can move the scope verdict: those that can stay questions; those the plan absorbs become clarify-early items.

**D9 — Section titles are fixed per language and parsed by the verdicts.** Review sections: `## Proposal blockers` / `## Vor der Annahme zu klären`, `## Clarify early in the thesis` / `## Früh in der Arbeit zu klären`, `## Optional refinements` / `## Optionale Verbesserungen`, `## Earlier round` / `## Frühere Runde` (the last already used by supervise). The L1 verdicts accept both languages, case-insensitively, and read "empty" as "no enumerated item under the heading" so a section that says "none" passes.

**D10 — Minimal-pair fixtures.** f28 and f29 share every sentence except the paragraph that makes RQ2's evidence depend on a partner's engineers; w09 carries f28's text plus a hand-written earlier review. The pair isolates the one judgement under test: if f28 fails, the reviewer overblocks; if f29 passes as ready, it underblocks; the text cannot be the confound. The topic (agent configurations for repairing failing CI builds, evaluated on a public benchmark) exercises the acceptance criteria directly — unnamed model versions, optional expert ratings — and is written from scratch with obviously fictitious references, like f24.

**D11 — Execution-shape pins stay untouched.** The helper contracts in review and supervise return findings "with severity"; the class is the severity. Rewording the pins would churn two verbatim pins for no behavioural gain.

**D12 — Inspect tasks registered, not run.** The four scenarios exist as dev-runner scenarios (verified now, on the subscription) and as Inspect tasks so `poe matrix` can measure them later behind its cost gate; `harness/eval_export.py` regenerates the `evals/evals.json` projections.

## Risks / Trade-offs

- [Underblocking regression: reviewers defer genuine gaps under the new licence] → the dependency safeguard and the record's "would an adverse outcome reopen the proposal" field; f29, `review_hollow` and `review_fixture` re-run in verification.
- [Flimsy deferral records — a blocker dressed as clarify-early] → the readiness rubric grades every record; a record whose resolution would change a research question fails it.
- [An early misclassification persists under monotone rounds] → the missed-in-the-earlier-round label is the escape hatch, and its count in the chat summary keeps it visible.
- [Feedback length grows by the block] → at most five one-line items inside the existing ~1,200-word target; refinements stay review-side.
- [Smaller models drop the three-section structure] → measured on haiku in verification; a failure becomes a model-support note, not a weaker rule.
- [Concurrent session editing the same checkout (`pass-source-verification`)] → disjoint footprints agreed, explicit-path staging only, "committing now" handshake; a sync run that regenerates the other change's script copies leaves them unstaged.

## Migration Plan

Existing review files carry one severity-ordered list. On the first run after this change, an old-format review is still an earlier round: the new review marks each earlier finding resolved, partly resolved or open and classifies it fresh, because an unclassified finding has no class for the monotone rule to preserve. No user action is needed; the next review run produces the new structure. Rollback is a revert of the change's commit; no data format outside the review file changes.
