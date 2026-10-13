# Design

## Context

Three pieces of guidance already touch named tools, and none of them asks whether the research depends on the name:

- **The swap test** (`shared/guidelines/guidelines.md`, `## Substance Tests`) judges prose: "Text that stays plausible after swapping the topic noun fails as generic." A named framework makes text look specific, so the test as worded lets it through.
- **The title alarm** (`## The Thesis Title`) separates the *object* of a study from its *instrument*. It looks at the title only, it is "raised, never enforced", and `## Readiness` lists title findings among those that "never block on their own".
- **The paper-foundation entry path** of `proposal-ideate` already asks the same question of a domain: "what about the new setting changes what is at stake?" A transfer whose answer stays "nothing" is treated as a re-run. That is the precedent: the question works, it is Socratic, and it never names the alternative.

Swap-test failures already block: `## Readiness` makes every substance-test failure except necessity a proposal blocker. So once the swap test covers names, the blocker follows, and the readiness model needs no new class.

The constraints this change works under:

- **Header pattern.** The purpose, workflow, voice and mandate blocks stay byte-identical.
- **Pins.** Execution-shape and other pinned sentences stay as they are; new pins are added only for new load-bearing sentences.
- **Body size.** The body-size cap is twice the median: about 5,200 words today, against 4,663 for supervise and 4,151 for ideate.
- **Substance-test drift guard.** The guard fails any site that changes the number of tests, so this change keeps six.
- **Formalization boundary.** Semantic rules stay prose. Nothing goes into `structure.json`.

## Goals / Non-Goals

**Goals:**

- Make the check checkable. It has four parts: a fixed scope, four pass anchors, one replacement question, and two repairs. A judge applying it to the same text reaches the same verdict.
- Reconcile the swap test with the title alarm, so that one name is never reported twice and the non-blocking alarm stays non-blocking.
- Measure both directions: a decorative name blocks, and an anchored name does not.

**Non-Goals:**

- A mechanical check. A proper-noun matcher cannot tell an object of study from a convenience. That is the same reason the title alarm's instrument class is judgement only.
- Judging implementation choices in the method, or domains named only in the motivation. The necessity test already decides whether those belong.
- Changing the degree-level calibration. A decorative name fails at Bachelor's and Master's level alike, because the question is what the thesis studies, not how novel it is. A Bachelor's close that claims its result for the named setting passes, since the setting is then what the claim is about; it fails only when it claims a result for the class while the setting stays incidental (adversarial-review finding 4; rule choice user-confirmed 2026-10-13).
- Metered runs, Inspect tasks, routing changes.

## Decisions

### D1 — Extend the swap test, no seventh test (Q-S1)

A decorative name answers the swap test's own question, "could this describe ten other theses?", with "yes" while looking specific. Extending the test keeps all of the following intact:

- the six-test drift guard;
- every site that enumerates the tests: README, skill bodies, specs and pins;
- the supervise evidence bar ("three of the six");
- the necessity mirror sentence, which is still true. The swap test catches text that could belong to any thesis in the area; a decorative name is such text.

*Alternative: a separate "anchor test"* — rejected. It would change the count at every enumerating site for a check that is the swap test's question applied to nouns.

### D2 — Scope: the thesis's own claims (Q-S2)

The maintainer's scope was "title, research questions, contribution, objectives". In the guidelines' own vocabulary that becomes:

- the title;
- the purpose statement that closes the introduction (the introduction is otherwise the motivation, which is out of scope);
- the research focus paragraph and the research questions;
- the contribution section's statements of what the thesis adds: its goals, gap, significance and deliverable kind. "Objectives" maps onto the purpose statement and the construction goals, which already live there.

Names of *prior work* inside the contribution section are out of scope. They are not the thesis's claims, and a related-work cluster that names three tools is not decorative.

### D3 — Pass anchors, and the replacement check

Taken literally, replacing a name always changes a noun. What the check compares is the *claim*. A name is an **object of study** when the expected contribution is a claim about it rather than about its class. The other three anchors are:

- **constraints** that shape the method;
- **data or access** no comparable alternative offers;
- **the argued case**: the case the proposal argues suits its research questions — typical, critical or revelatory, the selection the Case Study contract already demands ("why this case suits the research questions"). An earlier draft said "the necessary case"; that was stricter than the contract, since a typical case is by definition replaceable by another typical one, and was aligned with it after the adversarial review (task 5.3).

The guidance states the claim comparison in the text itself ("compare the claims, not the nouns"), and the review lists the pass anchors before the replacement verdict, so an agent never reaches "decorative" before it has read the exceptions. A Bachelor's close that promises an application or evaluation in a named setting claims its result for that setting, so the setting is its object and passes; the guidance says so beside the examples, which keeps the Degree Level section and the swap test from pointing opposite ways.

**A comparison of named tools passes by design.** One worked example per kind, a tool and a domain, makes the rule checkable without a table.

### D4 — The title is in scope, and a decorative title name blocks

Q-S2 includes the title, and the maintainer's request asks for a blocker. That changes part of the 2026-08-05 title-quality stance: a decorative tool name in a title used to be an optional refinement and now blocks. The change is deliberate, and the rest of the stance stays. One name is judged by two lenses, and each case produces exactly one finding:

| Case | Swap test | Title alarm | Reported as |
|---|---|---|---|
| Nothing in the research depends on the name | fails | instrument | **one swap-test blocker**, which carries the certificate consequence and 1–3 alternatives |
| The name shapes the method, supplies data or access, or is the argued case, but is not what is studied | passes | instrument | title item among the optional refinements, as today |
| The name is the object of study | passes | — | nothing |

What still holds of the 2026-08-05 stance:

- the title alarm itself never blocks;
- the title is never silently rewritten;
- the student's decision stands, and a review blocks nothing.

What changes is that a decorative name keeps the verdict from reading "ready". `## Readiness` now says that a title name failing the swap test blocks as that test's failure, not as a title finding. A justification given only in chat counts once the proposal's text carries it. Otherwise the review, which reads only the file, could never see it.

### D5 — Why it cannot wait

The deferral record requires a resolution that leaves the research questions and the contribution intact. Both repairs change one of them:

- stating the dependence changes the contribution;
- generalizing changes the title and the research questions.

So the record cannot be filled, and the finding is a blocker by the existing rule. The review's blocker sentence says exactly that.

A name only the title carries is the exception: generalizing it changes the title alone, which leaves the research questions and the contribution intact. Its reason is the title itself — what the thesis is usually registered under and what the certificate prints — so the proposal, not the thesis, is where it is settled. The guidance's Thesis Title section and the review bullet give that reason for the title-only case. Where the title carries further tells (an employer name, an implementation opener), they stay one title refinement that names them, points to the blocker's alternatives and does not repeat the name, so the `title_alarm` rubric's "finding of its own" still holds and the alternatives are offered once.

### D6 — Supervise: the professor sees the test, the student sees a question (Q-S3)

The review file names the swap test. The feedback point asks a question instead: "what in your thesis would change if a comparable framework stood in its place?" It then gives both directions. This follows the existing rule, "no substance-test names" in the feedback. The verifier brief already flags substance-test names, so `references/verifier-brief.md` does not change. A decorative-name blocker competes for the five points by how much it blocks. Since it is repairable in place, it usually ranks below a missing delta and above wording issues. When it is outranked, it stays in the review.

### D7 — Ideate: ask once, never name the alternative

Naming a particular alternative ("what if you used X instead?") would supply idea content. That is the same line the paper-foundation path draws at "never a particular domain, dataset, or method". The skill asks the contrast with a class phrase ("a comparable framework") and asks it once per name. A name that is not yet anchored does not make an aspect concrete. It never blocks seeding on its own, because the seed is a sketch and the write skill and the review pick the question up. The open question goes to the notes file's open points, which the write skill reads.

### D8 — Write: introduce no decorative names, keep the author's, and record reasons

The write skill never introduces a name the material gives no dependence for. When the author's material carries one, the skill keeps it, because the surgical-edit rule forbids silent removal, and marks the gap with `[TODO: state why this thesis needs <name>, or generalize]` where the contribution would say it. A reason the student gives in the session is written into the contribution or the research questions. This also closes the title-negotiation gap from D4: the "object of study" reason now reaches the file the review reads.

### D9 — A minimal pair built from f28

`f28-open-decisions` is the readiness control. `proportionate-readiness-review` calibrated it to *ready* through five rounds of confound fixes; the runs are recorded with their logs in that change's archived `tasks.md`, task 7.2. The pair reuses its text so that the name is the only variable.

| | `f31-decorative-tool` | `f32-tool-as-object` |
|---|---|---|
| File | `ci-repair-agent-configurations.md` | same name, so the dev-runner request is identical |
| Title | `Effects of Mendwright Agent Configurations on Automated Repair of Failing Continuous Integration Builds` | identical |
| Purpose statement, research focus | f28's, with "Mendwright's agent configuration" | identical |
| RQ1 | "…between Mendwright's single-agent and planner–executor configurations when both run on the same model?" | identical |
| RQ2 | "…change the repair rate of either Mendwright configuration?" | identical |
| RQ3 | f28's unchanged | identical |
| Method | "Both architectures are taken from Mendwright, an open-source agent framework that implements them [@Moreau25Planner]…" (an implementation choice; out of scope for the check) | identical |
| Contribution close | f28's three closing sentences, unchanged: significance from leaderboard adoption; "what will be new is a within-model estimate of configuration effects on build repair, for teams and tool builders who choose between configurations rather than between models"; deliverable an evaluation. **The claim is about configurations in general, so the name is decorative.** | Replaced by three sentences, sketched below. **The claim is about Mendwright itself, so the name is the object of study.** |
| References, timeline, everything else | f28's | identical |

The f32 contribution close is sketched as:

> Mendwright exposes exactly these four configurations and ships the planner–executor architecture with the truncated log excerpt as its default [@Moreau25Planner], and teams that adopt it run that default unless evidence tells them otherwise. The thesis therefore evaluates Mendwright itself: what will be new is a within-model estimate of how Mendwright's four configurations, its default among them, differ on build repair, for the teams that run Mendwright. The deliverable is an evaluation of a specific instance: a controlled comparison of Mendwright's four configurations on a public benchmark of reproducible build failures.

Design notes on the pair:

- **The name.** "Mendwright" is a placeholder. A fictitious name avoids factual claims a model could dispute from memory, and the corpus already uses fictitious tools ("Lintfox", "Codegull") and fictitious references.
- **No new goal in f32.** The f32 close adds no goal the research questions do not touch: "its default among them" is one of the four configurations RQ1 and RQ2 already compare. This avoids a "two proposals in one document" finding.
- **f28 is the third control.** It names no tool, and its existing `review_ready` and `supervise_ready` scenarios guard against overblocking. Together the three give a no-name / decorative-name / anchored-name triple.
- **Oracles.** Both oracles' `check` blocks equal f28's (exit 0, no errors, no warnings). The title stays under the 20-word bound and opens with no implementation opener. That is verified against `check.py` at implementation.

*Alternatives considered:*

- **f31 named, f32 = f28 unnamed.** Rejected. That pair tests "is a name present", not "does the research depend on the name", which is the judgement the maintainer asked for.
- **A fresh topic**, for example a user study of one IDE feature. Rejected: uncalibrated text brings the confounds that cost the readiness change five iterations.

### D10 — Narrow verdicts, attributable to the anchor

The new verdict functions in `harness/l1_checks.py` reuse `review_sections`, `enumerated_items`, `review_tier`, `supervise_opening_tier` and the closing-note stripping. The tool name is a parameter, like the `terms` argument of `verdict_review_dependency`.

- `swap_failure_cited(item)`: a sentence of the item mentions "swap" and is neither negated ("no swap-test finding", "does not fail") nor a pass statement ("passes the swap test") without an unnegated failure cue. A bare mention ("Swap test — Mendwright") counts. Added after the adversarial review (task 5.3), because the review bullet asks for each name explicitly and a refinement may say the name passes.
- `verdict_review_swap_decorative`: tier is needs revision, and some blocker item cites the swap test as failed (`swap_failure_cited`) and names the tool, case-insensitive.
- `verdict_review_swap_anchored`: no enumerated item in the blocker, clarify-early or refinement section cites the swap test as failed. The verdict line is excluded, because a ready verdict may list the tests that pass. The tier and any blockers are reported in the explanation and not asserted.
  - *Why not also match the tool name:* f32's title and research questions carry the name, so any blocker quoting RQ1 would contain it. Matching on the name would turn ordinary readiness noise into a false anchor failure.
  - *Who judges the rest:* the L2 criterion judges whether a finding treats the name as replaceable under another test's name, and the oracle expects ready.
- `verdict_supervise_swap_question`: the feedback opens with needs revision; some numbered point contains the tool and a question sentence carrying a contrast cue ("comparable", "another", "instead", "in its place", "replace", "alternative", German equivalents), since f31's RQ1 and RQ2 both name the tool and end in "?", so a point quoting them would otherwise pass; and `swap[- ]test` does not occur in the feedback with the closing note stripped.
  - *Direct or indirect:* the question may be direct (a sentence ending in "?") or indirect, an imperative to consider it ("ask yourself what … would change if …", "consider whether …", "überlegen Sie, was …", "fragen Sie sich, ob …"); either way the contrast cue must sit in the same sentence. Widened after the 5.2 dev run, user-confirmed 2026-10-13: sonnet asked "Please ask yourself what in the thesis would change if another framework … stood in its place." with no "?", which the pinned skill sentence ("ask what in the thesis would change if a comparable one stood in its place") reads as, and the spec never required the direct form. Tightening the skill and spec to the direct form was the rejected alternative: it would grade wording, not the question.
- `verdict_supervise_swap_quiet`: the feedback opens with the ready tier and carries no numbered point. This matches the skill-supervise scenario, and f28's `supervise_ready` already reaches ready on the same text without the name.

### D11 — L2: two criteria on `readiness.txt`, no new rubric file

`readiness.txt` already grades what matters here: blockers name their test and why they cannot wait, nothing beyond the guidelines is required, and tone. The scenario-specific part travels in the `CRITERIA` text and the oracle `semantic` list, the same way `review_dependency` does it. Reusing the file means no new golden prompt. The criteria are drafted below and are dev-runner L2 only.

### D12 — Dev runner only, no Inspect registration

Q-S4 asks for dev-runner scenarios. The readiness change registered Inspect twins; the handoff change did not, which kept `models.toml` and the `evals.json` projections unchanged. This change follows the handoff precedent. A later, cost-gated matrix decision can add twins without touching the verdicts.

### D13 — Pins

The change adds one pinned sentence per touched skill. Each pin is the sentence that carries the rule, so that a reword shows up as a diff:

- `proposal-review--swap-names.txt`;
- `proposal-supervise--swap-question.txt`;
- `proposal-ideate--swap-names.txt`;
- `proposal-write--decorative-names.txt`.

Execution-shape pins do not change. A review helper already returns a swap verdict per test, and title findings stay with the main agent.

## Wording drafts

These drafts are to be sharpened at implementation. Their substance is what the specs fix.

### `shared/guidelines/guidelines.md`

**Substance Tests: the swap bullet.** It currently reads "…Text that stays plausible after swapping the topic noun fails as generic." It becomes:

> - **Swap test** — the proposal's core statements could not equally describe ten other theses in the area. Text that stays plausible after swapping the topic noun fails as generic, and so does a named tool or domain the research does not depend on.

**Substance Tests: a new paragraph** after the citation paragraph ("A citation does not satisfy the necessity test…"):

> A name does not satisfy the swap test either. Every tool, system, platform or application domain the thesis names in its own claims — the title, the purpose that closes the introduction, the research focus and questions, and what the contribution section says the thesis adds — must be something the research depends on: the object of study, so that the expected contribution is a claim about it rather than about its kind; a source of constraints that shape the method; the source of data or access no comparable alternative offers; or the instance the proposal argues is the necessary case. To check a name, replace it with a comparable alternative, or drop it. If the research questions, the method and the expected contribution read the same, the name is decorative and the proposal fails the swap test: state the dependence, or generalize the claim to the name's class. A comparison of named tools passes by design, because the tools are what it studies. A build-failure classifier evaluated on one CI service's logs fails when any service's logs would do; a study of how that service's own retry policy hides failures passes. A domain works the same way: a code-summarization thesis set in banking fails unless banking contributes something — regulation that constrains the summaries, a codebase only a bank provides. Names of prior work, tools chosen to carry out the method, and domains named only to motivate the topic are not judged here; the necessity test decides whether they belong.

**Readiness: the blocker bullet.** The new phrases are shown in **bold**:

> - **Proposal blockers** — problems that prevent judging the thesis core, and only those: failures of a substance test other than the necessity test. That covers no answerable research question, an unclear contribution — including literature too thin to show what the thesis adds — **a named tool or domain the research does not depend on**, a method that cannot answer a question, a scope that cannot fit the stated months at the declared level, and an indispensable resource whose availability is doubtful. Nothing else blocks. Necessity, density, title and citation-practice findings are reported but never block on their own; material that obscures what the thesis contributes or asks is reported as the contribution or research-question blocker it causes, **and a name in the title that fails the swap test as the swap-test blocker**.

**The Thesis Title: an addition** after "…not because changing the title is inconvenient.":

> One case goes beyond the alarm: a name your research does not depend on fails the swap test under Substance Tests, in the title as anywhere else in the thesis's own claims, and that failure blocks readiness until the proposal states what depends on it or the title names its class instead. A reason you give in conversation counts once the proposal carries it.

### `skills/proposal-review/SKILL.md`, `## What to assess`

**The title bullet.** Its middle sentence becomes:

> Flag it as an enumerated refinement — unless a name in it fails the swap test (next item), which makes it that blocker — say that it reaches the study certificate, and suggest one to three abstracted alternatives.

**A new bullet** after the title bullet. The pinned sentence is the replacement question.

> - **Named tools and domains** — hold every tool, system, platform or application domain that the title, the introduction's closing purpose, the research questions or the contribution names to the swap test, and say so for each: replace it with a comparable one, or drop it — do the research questions, the method and the expected contribution read the same? Then the name is decorative: one blocker that cites the swap test, lists where the name stands, says what stays unchanged, and offers both repairs — state what the research depends on in it, or generalize the claim to its class; either repair changes a research question or the contribution, which is why it cannot wait. A name passes when it is the object of study, imposes constraints that shape the method, supplies data or access no alternative offers, or the proposal argues it is the necessary case; a comparison of named tools passes by design. A failing name in the title is this blocker, with the certificate consequence and alternatives — never a second title item. Prior work, tools that only carry out the method, and domains named only in the motivation are not checked here.

### `skills/proposal-supervise/SKILL.md`

**`## Find the issues`**, after "…sentence-level density are the dimensions.":

> Named tools, systems, platforms and domains in the thesis's own claims are held to the swap test exactly as the review skill does; the review names the test for each failure.

**`## Curate the feedback`, point 3**, after "…without what they mean here.". The pinned sentence is the question.

> A decorative name — a swap-test blocker — becomes a question: locate the name, ask what in the thesis would change if a comparable one stood in its place, and give the direction — say what the research depends on in it, or state the claim for its class.

### `skills/proposal-ideate/SKILL.md`, `## Session arc`

A new paragraph after the swap-test paragraph:

> A name is not yet a specific. When the student's idea names a tool, system, platform or domain — in the working title, the problem, a research-question direction or a goal — ask once, as a Socratic move, what about the thesis would change if a comparable one stood in its place, without naming the alternative yourself. Until the student says what depends on it, the name makes no aspect concrete; if they leave it open, record the question among the notes file's open points and move on — it never blocks seeding on its own, and you never supply the dependence.

### `skills/proposal-write/SKILL.md`, `## Substance and density`

A new bullet after "Never manufacture substance":

> - **No decorative names.** Never put a tool, system, platform or domain into the title, the purpose statement, the research questions or the contribution unless the material says what the research depends on in it — the guidelines' swap test applied to names. A name the author's material carries without that dependence stays, with `[TODO: state why this thesis needs <name>, or generalize]` where the contribution would say it, and the closing report names it as an open swap-test blocker with both repairs. A reason the student gives in the session — for keeping a named technology in the title, say — goes into the contribution or the research questions, not only into the chat.

### L2 criteria (`harness/l2_rubrics.py`, on `readiness.txt`)

- `("review_swap_decorative", "review_swap_decorative_l2")`: "Opens with needs revision and carries one swap-test blocker on the named framework that lists where it stands, states that a comparable framework would leave the research questions, the method and the contribution unchanged, gives both repairs (state what the research depends on in it, or generalize), and says why it cannot wait; the title's naming of it is not reported again as a separate item; every other blocker is a genuine substance-test failure with its reason."
- `("review_swap_anchored", "review_swap_anchored_l2")`: "Raises no finding, under any test's name, that treats the named framework as replaceable or decorative, because the contribution makes the framework's own configurations the object of the evaluation; opens ready, and every blocker it raises is a genuine substance-test failure with its reason."

## Risks / Trade-offs

- **[Overblocking]** A judge may start treating every proper noun as suspect, for example "continuous integration builds", the microservices of f05, or the SMEs of f04. → *Mitigation:*
  - the scope is limited to the thesis's own claims;
  - the four anchors and the "claim about it, not about its class" test are stated, along with the worked examples;
  - the guard runs `review_ready` (f28) on both models;
  - the anchored-side verdict and the L2 criterion catch any swap finding on f32.
- **[Underblocking on haiku]** Haiku may read "Mendwright's configurations" in the research questions as anchoring by itself. → *Mitigation:* this is measured by `review_swap_decorative` on haiku. Wording iteration follows the readiness change's practice: instrument errors are fixed first and recorded, model findings are kept.
- **[Confound in f32's close]** The rewritten close may draw a level-fit or delta finding of its own. → *Mitigation:* the research questions stay identical, and the close adds no goal they do not touch. The anchored verdict asserts only the absence of a swap or tool blocker. If the f32 runs show the confound, the close is reworded before anything else is changed.
- **[Changed title stance]** Students who kept a tool-named title on a reason given only in chat will now see a blocker until the reason is in the text. → *Mitigation:* this is intended (D4). The write skill writes the reason into the proposal (D8), and the README clause tells readers that the swap test covers names.
- **[Earlier rounds]** A proposal reviewed before this change can draw a new swap-test blocker on unchanged text. → *Mitigation:* this is allowed under monotone rounds only as "missed in the earlier round", with the flaw stated. The common case — an earlier round that reported the title name as a title refinement without holding it to the swap test — is decided explicitly in the Rounds paragraph: it counts as such a miss, returns as the swap-test blocker with the label and the missing dependence stated, and the earlier title refinement is not repeated beside it. The alternative, keeping it a refinement for that proposal, was rejected because it would leave a decorative name ready on exactly the proposals this change was asked for; the rule choice was user-confirmed on 2026-10-13. The guidance-model delta carries both cases as scenarios. `w09` names no tool, so it is unaffected.
- **[A supervise point outranked]** With five stronger blockers, a decorative name never reaches the student. → *Mitigation:* this is by design (curation), and it stays in the review file.
- **[Body-size cap]** The supervise body sits at about 90 % of the ceiling. → *Mitigation:* about 70 words are added to supervise and about 100 or fewer to each other skill, and the size test runs in the verification step.

## Migration Plan

There is no data migration. The guidance change lands in `shared/` and is materialized by `scripts/sync_shared.py`. The fixtures and scenarios are additive. Rollback is a revert of the change's commit followed by a sync.

## Open Questions

- **The fictitious framework name.** "Mendwright" is a placeholder; the final name is chosen at implementation and checked against obvious collisions with real products.
- **Domain-anchor measurement.** The pair measures a tool only. A domain pair is worth adding only if dev runs or user reports show domain names judged inconsistently. The guidance and the skills cover domains either way.
- **Inspect twins and matrix cells** for the four scenarios. This is a separate, cost-gated decision.
- **Which existing oracles change.** The audit decides. Its candidates are f21 (a platform in the title that the research questions never use, so a likely blocker), f02 (a comparison, which passes by design), f04, f05, f06, f16, f25 and the raw submissions s01 and s02.
