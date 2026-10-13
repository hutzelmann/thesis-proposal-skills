## Why

A student and supervisor ran successive reviews over one proposal and watched the requirements grow each round — exact model identifiers, capture conventions, audit sample sizes, company arrangements for an expert assessment that had already been made optional — until acceptance felt unattainable. The cause is in the skills, not in that session:

- **No stopping rule.** The review's `ready` tier means "no substantial findings remain", so any finding blocks it; nothing separates "this needs a decision before execution" from "this proposal cannot be judged".
- **No memory between review rounds.** `proposal-review` overwrites `<slug>-review.md` without reading it, so every rerun is a fresh audit that finds something new. `proposal-supervise` reads its earlier round but admits any number of new points.
- **An open licence to add requirements.** The review asks for "missing information a supervisor would ask about" — and a supervisor eventually asks about everything.
- **Methodology contracts read as checklists.** "Models, features, and infrastructure", "what access exists": nothing says a stated selection rule satisfies a contract element, so an unnamed model version reads as a gap.
- **Revision feeds escalation.** "Apply the review" works every item into the proposal text; the text grows into a protocol, and the next review audits the protocol.
- **Evals test one direction.** Every review eval checks that defects are found (f05, f21, f22). None checks that a sound proposal reaches `ready`.

The design goal: judge whether the proposal supports an informed decision to supervise the thesis — not whether the thesis could begin tomorrow without the student making another methodological decision. Proportionate review, not lower standards.

## What Changes

- **A readiness rule in the shared guidance.** `shared/guidelines/guidelines.md` gains a `Readiness` section that every judging skill and every student reads:
  - three finding classes — **proposal blockers**, **clarify early in the thesis**, **optional refinements**;
  - a blocker is a failure of the delta, falsifiability, swap, method-fit or executability test, and nothing else — necessity, density, title and citation-practice findings never block on their own;
  - a **deferral record** (what needs deciding, why it matters, when it is settled, a reasonable resolution, whether an adverse outcome would reopen the proposal) is the proof that a finding can wait; a finding whose record cannot be filled is a blocker and carries a sentence naming its test and why it must be settled before approval — "not specified" alone never is one;
  - the **optional-part test**: strike an element the proposal calls optional; if every research question survives, its arrangements never block;
  - the **dependency safeguard**: an indispensable permission, ethics approval or data access whose availability is doubtful still blocks; routine organisational detail and arrangements for optional evidence do not;
  - the **stopping rule**: no blockers means ready, however many early-thesis items remain, and nothing beyond the applicable guidelines is required;
  - **monotone rounds**: a finding about unchanged text never moves up a class; a new blocker in a later round needs changed text or an explicit "missed in the earlier round" with the flaw stated.
- **Executability is a plausible plan, not a finalized protocol** — one sentence in the test's definition, and one in Methodology Content: a contract element is met by a stated selection rule or candidate set.
- **`proposal-review`**: findings in three sections (plus `Earlier round` when an earlier review exists); the verdict is derived — ready exactly when no blocker stands; the ready verdict states that it is not an execution protocol; the previous review is read before it is overwritten; the "a supervisor would ask about" licence is replaced by "information the substance tests need"; title, density and necessity findings move to refinements. **BREAKING** for readers of the review file: the single severity-ordered list becomes three sections.
- **`proposal-supervise`**: numbered points are blockers only, zero to five — a ready feedback carries none; a short unnumbered block names up to five early-thesis items in ready and needs-revision feedback as not conditions for resubmission, never promising a meeting; resubmission intake follows the monotone-rounds rule.
- **`proposal-write`**: "apply the review" works blockers and refinements into the proposal and records early-thesis items in the notes file's `Open Points`, never in the proposal text.
- **Evals for both directions**: a minimal fixture pair (f28 ready despite open execution decisions; f29 the same text with one indispensable, doubtful dependency), a convergence workspace (w09: f28's text with an earlier review whose blockers it resolves and an early-thesis bait item), a supervise scenario over f28, deterministic verdicts with L0 tests, and a readiness rubric.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: new requirement "Readiness classification" (classes, deferral record, optional-part test, dependency safeguard, stopping rule, monotone rounds); "Substance tests" executability definition gains the plausible-plan sentence.
- `skill-review`: "Three-tier substance verdict" derives the tier from the blocker list and the necessity-only scenario becomes ready-with-refinement; "Persisted, actionable output" gains the three-section structure and the deferral records; new requirement "Review rounds converge"; "Content-level review scope" loses the open licence.
- `skill-supervise`: "Findings reused from check and review, curated to pressing points" — points are blockers only, zero to five, plus the early-thesis block; "Verdict expressed as proposal state" — the ready tier carries no points; "Resubmission intake" adopts monotone rounds.
- `skill-write`: "Refinement preserves author content" — applying a review routes early-thesis items to the notes file.
- `testing-harness`: new requirement "Readiness coverage" (overblocking, underblocking and convergence fixtures with deterministic verdicts and a rubric); "Supervise feedback coverage" — the points verdict accepts zero points on a ready feedback, and the early-thesis block is asserted.

## Impact

- **Guidance**: `shared/guidelines/guidelines.md` (new Readiness section; Substance Tests executability line; Methodology Content selection-rule sentence), regenerated into every skill's `references/guidelines.md` by `scripts/sync_shared.py`.
- **Skills**: `skills/proposal-review/SKILL.md`, `skills/proposal-supervise/SKILL.md` and its `references/verifier-brief.md`, `skills/proposal-write/SKILL.md`; the execution-shape pins stay unchanged (a helper's "severity" is the finding's class).
- **Harness**: `harness/l1_checks.py` (new verdicts, relaxed points verdict), `harness/claude_runner.py` (four dev-runner scenarios), `harness/skill_evals.py` (four Inspect tasks — registered, not run metered), `harness/rubrics/readiness.txt`, `harness/README.md`; regenerated `skills/*/evals/evals.json`.
- **Fixtures**: `tests/fixtures/f28-open-decisions/`, `f29-doubtful-dependency/`, `w09-revised-round/`, each with `expected.json`; `tests/fixtures/README.md`.
- **Tests**: L0 tests for every new `verdict_*`.
- **Cost**: verification runs on the subscription dev runner (haiku, sonnet) with the subscription judge. No metered run; matrix cells for the new tasks are a separate, cost-gated decision.
