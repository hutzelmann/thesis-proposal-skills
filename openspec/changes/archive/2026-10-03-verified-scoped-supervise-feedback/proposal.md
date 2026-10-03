# Proposal

## Why

A real supervise run on 2026-10-03, on a Bachelor's proposal that builds a prioritization model over an existing framework mapping, produced feedback the professor could not send. It took six minutes and made no lookup of an abstract or a standard's text. Fresh verifiers later confirmed about 45 distinct problems in it:

- claims about standards and regulations stated from memory (9)
- claims about the student's own cited papers judged from their titles (10)
- planned work reported as missing, and a quote cut so that it dropped the answer to the question the point then asked (13)
- contradictions between the opening and the strengths (5)
- review vocabulary reaching the student ("sound", "delta", "by construction") (8)

Rewrites introduced 13 more, five of them verifier corrections adopted word for word. The only remaining legal must-fix was caught by a second fresh pass.

Two further failures had nothing to do with facts:

- **Workload.** The plan was six chained work packages in about fourteen weeks, with the size of its main input unknown. The skill passed the executability test object by object, treated the Gantt chart as forbidden format content rather than as evidence, and then added about eighteen asks of its own. The professor had to ask whether the plan was too big. The answer — cut to one core, offer two options, leave the choice to the student — came from the conversation, not the skill.
- **Format remarks.** A paragraph on the student's name, Gantt chart, chapter outline and timeline length reached the student's feedback. The professor removed it as beside the point. The same complaint had already been made on 2026-09-01 about the earlier version of the same proposal.

The skill has no rule against any of this. HEAD's "no paper from memory" rule covers woven papers only; standards, regulations, the student's own references and the student's own text are unverified by construction. The verification evidence is consistent: rereading one's own draft does not catch these errors; checking claim by claim against fetched sources and an independent pass does.

## What Changes

- **Claim ledger.** Every assertive sentence in the feedback, and every review finding that feeds a point or a fail verdict, is checked against its evidence class before the feedback is handed over:
  - the student's text: an exact quote, or a search before any "the proposal lacks X";
  - a paper: its fetched abstract, including the student's own references before anything is said about them;
  - a norm: primary or issuer text, never a clause from memory;
  - a figure: computed.

  A claim that cannot be verified is cut or turned into a question for the student. The review carries a short Verification section; the wrap-up names what stayed unverified.
- **One fresh verifier of the final text.** A single helper with a fixed remit — fidelity, papers, norms, contradictions, jargon, workload — checks the finished feedback. The main agent applies its findings and re-checks every changed sentence. The execution-shape cap stays at three agents. The verifier replaces the network-less reference-reading slot, and the adversarial check of fail verdicts is added only where a host insists on a workflow; a host without helpers runs the same checks in context as separate questions. **BREAKING** for the pinned execution-shape section and its spec.
- **One combined consent question.** The pinned approval question now covers verification lookups as well as weaving literature, still asked once. Declined or headless means offline: claims that need outside evidence are cut or turned into questions.
- **Workload check before the tier.** The review carries a work-package table: dependencies, size drivers, unknown sizes, coarse week estimates labelled as estimates, and the Gantt or work plan read as evidence. The total is set against the student's own months and the degree-level bar. The verdict is fits, tight or over-scoped.
  - Over-scoped: the feedback opens its body with a scope paragraph offering two or three lettered cut options, the choice left to the student, and the points become conditional on the option.
  - Net-workload budget: every ask that adds work names what it replaces, is marked optional, or belongs to an option.
- **Substance-only feedback.** Format and convention findings stay in the review unless the workspace guidelines ask for them. The "format issues → proposal-check" point type is removed. Language quality becomes a point only when it blocks understanding.
- **Student-facing wording:**
  - every point runs observation (located) → why it matters → direction;
  - review jargon is translated;
  - no action items in "What to keep";
  - a contradiction check runs across the opening, the points and the strengths;
  - a final self-check runs against rules that already exist.
- **A locator for every source not in the proposal.** Papers get a DOI URL; standards and regulations get their issuer's official page. Each locator must resolve in this run. Papers stay capped at three.
- **Shape:**
  - soft length target of about 1,200 words, excluding locators and the closing note;
  - light markup only (bold allowed; no headings, backticks or blockquotes);
  - the proposal's language, with the other language offered when the student's message differs.
- **Resubmission intake.** An earlier review or feedback of the same idea, matched by content and never by identity, yields an "Earlier round" status table in the review and one line after the verdict. An existing notes file is extended rather than recreated.
- **Offline and idea-stage boundaries.**
  - A declined lookup also skips the import sibling's reference validation.
  - Fetched pages are untrusted data.
  - A decisive fail never rests on a claim only a lookup could settle, so the tier does not depend on network access.
  - Idea-stage feedback gets no cut options.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-supervise`: the following requirements change:
  - findings curation: substance only, net-workload budget, reasons and translated wording;
  - student-facing feedback: markup, length, language offer, locators;
  - single-context execution: the verifier slot replaces the reference-reading slot;
  - literature consent: one combined question, offline behaviour.

  New requirements: claim verification, workload check, resubmission intake.
- `testing-harness`: supervise feedback coverage gains substance-only, markup and locator verdicts, an over-scoped raw-submission fixture with a scope scenario, and a per-scenario helper allowance in the dev runner's advisory probe.

## Impact

- **Skill:** `skills/proposal-supervise/SKILL.md`, which gains new sections and edited ones, including the pinned Execution shape and the approval question.
- **Pins:** `tests/unit/data/pinned_sentences/proposal-supervise--execution-shape.txt` and `proposal-supervise--literature-approval.txt` are edited, and `proposal-supervise--literature-verification.txt` is extended. New pins cover the claim-ledger and workload sentences.
- **Harness:**
  - `harness/l1_checks.py`: new verdicts;
  - `harness/claude_runner.py`: a `supervise_scope` scenario and a helper allowance;
  - `harness/skill_evals.py`: new scorers on the existing supervise task;
  - `tests/unit/test_eval_wiring.py` and the generated `evals/evals.json` projection.
- **Fixtures:** a new `tests/fixtures/s02-overscoped-export/`, a synthetic raw export with a Gantt plan, an unstated input size and claims about public regulations.
- **Docs:** a new `docs/supervisor-feedback-sources.md` evidence base, and a `harness/README.md` note.
- **Cost:** one dev-runner scenario on the subscription. No metered task is added.
- **Not touched:** the shared voice block, `shared/guidelines/guidelines.md`, the review skill and the closing note.
