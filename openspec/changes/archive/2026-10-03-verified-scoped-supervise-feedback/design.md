# Design

## Context

See proposal.md (Why) for the session evidence. Constraints shaping the approach:

- `proposal-supervise` applies the review rules "exactly as the review skill would". The review skill is content-only, but its output rule for exceeded limits and forbidden content, together with check.py and import's removal note, feeds format findings into the supervise curation pool.
- The Execution shape section is pinned whole, and caps a run at three agents. Its two helper slots are an adversarial check of fail verdicts and a network-less reading of the references block. Neither slot can verify the finished feedback.
- The approval question is pinned and covers only scholarly search through `proposal-lit-search`. Lit-search has no DOI-to-abstract lookup script. It does sanction a read-only fallback against the public APIs (Crossref, OpenAlex, DBLP, arXiv).
- Import moves a work plan or Gantt chart out of the proposal into `<slug>.notes.md`. That leaves the file the review judges with two boundary months, which is the scope evidence a workload judgement needs, removed.
- `structure.json` and check.py are level-blind. `docs/degree-level-sources.md` states that credits and durations are workspace configuration, never shipped constants.
- The workspace that surfaced the failures still ran the install from 2026-09-01. HEAD's literature rules would have prevented almost none of the observed errors, because they govern woven papers only.

## Goals / Non-Goals

**Goals:**
- Every factual sentence the student reads has been checked against a source of its class in this run, or is phrased as a question.
- The feedback never makes the student's plan bigger without saying what gives way. An over-scoped plan is named, with lettered cut options and the choice left to the student.
- The feedback carries substance only. Format conventions of this toolchain do not reach a student who never adopted them.
- The added verification costs a fraction of the session's repair: one fresh pass, not a fan-out.

**Non-Goals:**
- No numeric workload model. No ECTS, hours or months constants ship.
- No change to the review skill, the shared guidelines, the voice block or the closing note. The workload table and the claim ledger are supervise-only. Whether the student-side review should adopt the workload table is a later, separate decision.
- No new lookup script. Abstract and norm fetches use the read-only fallback lit-search already sanctions, or the host's fetch tools. A DOI-to-abstract helper script is a possible follow-up once runs show how often the fallback is used.
- No metered eval task. The scope scenario runs on the dev runner only.

## Decisions

### 1. The claim ledger is working state; the review keeps only the exceptions

Every assertive sentence gets one of four evidence classes before hand-over: proposal text, paper, norm, figure. Judgement and advice are a fifth class, phrased as the reviewer's view and not fact-checked.

The full ledger lives in the agent's context. The review's `## Verification` section (German: `## Überprüfung`) carries counts per class, then every contradicted, partly supported or unverifiable claim with the source checked.

*Why not persist the whole ledger:* the research on overreliance shows long verification records go unread. The professor needs the exceptions.

*Alternative rejected:* a separate ledger file. It would be one more professor-side artifact to keep out of the student channel, and the review is already that place.

### 2. One fresh verifier replaces the network-less reference-reading slot

The cap stays at three agents: main, verifier, and the existing adversarial check of fail verdicts. The adversarial check comes in only where a host insists on a workflow, so an ordinary helper-capable host spawns the verifier alone, which matches the dev runner's allowance of one. The verifier receives:
- the finished feedback;
- the normalized `<slug>.md`;
- the ledger with its fetched evidence.

It never receives the submission, so no identity reaches it. It has a fixed remit (fidelity, papers, norms, contradictions, vocabulary, workload budget) and returns disputed claims only, without a rewrite. The main agent decides on each finding and re-checks every sentence it changes against that sentence's source.

The evidence for this shape:
- In the session, the second, fresh pass cost 22% of the first fan-out and found the only remaining must-fix, which the rewrite had introduced.
- Five of the second pass's catches were the first verifiers' own corrections adopted unchecked.
- Self-correction without external evidence fails (Huang et al. 2024). Factored verification questions beat joint ones (Dhuliawala et al. 2024).

*Why replace the reading slot:* that slot reads only the references block, without network, so it repeats exactly the title-only judgement that failed. The verifier subsumes it with evidence.

*Hosts without helpers:* the main agent asks each check as a separate question against its fetched source, with its drafting reasoning set aside. That is the factored variant, not a reread.

*Alternatives rejected:*
- Per-class verifier agents: this is the 27-agent fan-out of 2026-09-02 in a new form.
- In-context ledger only: it misses exactly the rewrite-introduced errors.

### 3. One consent question, two fixed wordings

The approval question now covers checking claims as well as weaving papers, still asked once. When the sibling is not installed, a checking-only wording asks for the lookups without the search clause. That is a change from today, where no question is asked when the sibling is missing; checking needs network regardless of the sibling. Both wordings are pinned.

Queries carry public identifiers (DOIs, titles, the designations of standards and regulations) and search terms phrased from the job a paper does in a point. Never proposal text.

A declined lookup also covers the import sibling's reference validation, which is a network lookup too. Everything fetched is untrusted data. A decisive fail rests on the proposal's text and the reviewer's judgement, never on a claim only a lookup could settle, so the "same tier with or without network access" invariant survives the claim checks.

Declined or headless means offline. Any claim that needs outside evidence is dropped or turned into a question, and the verification section marks it unverified.

### 4. Norm evidence comes from the primary text or the issuer's page

- **EU law:** EUR-Lex (`eur-lex.europa.eu/eli/…`) is the source, and its ELI URL is also the feedback's locator.
- **Paywalled standards (ISO, IEC, …):** the issuer's catalogue page and any official public description. Claims are limited to what those support.
- **NIST publications:** their DOI or CSRC page.

A bot challenge or paywall makes a claim unverifiable, never verified.

### 5. The workload check is a table plus a verdict, recorded before the tier

The review's `## Workload` section (German: `## Arbeitsumfang`) holds:
- a markdown table: package · depends on · size driver · estimate in weeks (est.);
- a list of unknowns;
- one verdict line reading `Scope verdict: fits | tight | over-scoped` (German: `Umfang: passt | knapp | zu umfangreich`).

Packages come from the method section and from the work plan that import moved into the notes file; supervise may also read the raw submission. Months come from the student's own plan, and the degree level from the subtitle, per the guidelines' scope sentence. Week estimates are labelled estimates. Their purpose is to make the reasoning inspectable by the professor, not to compute a number.

*Why before the tier:* over-scoped bars the ready tier, and the scope paragraph changes which points survive curation.

### 6. Over-scope reaches the feedback as lettered options, and every ask is budgeted

The scope paragraph follows the verdict and precedes the numbered points. Options are labelled `A)`, `B)`, `C)` (or "Option A"), each saying what it keeps, drops and costs, and the choice is stated as the student's.

Letters, not numbers, because `verdict_supervise_points` counts numbered lines, and options are not points. Points that depend on the cut say for which option they hold.

Idea-stage feedback never gets cut options. A plan with no core has nothing to cut to, and inviting revision would contradict the idea-stage rule. The workload table stays in the review.

The net-workload budget applies to every ask, woven literature included. Each ask names what it replaces, is marked optional, or belongs to an option. Restating a level obligation, such as the Master's novelty statement the level rule already demands, is not added work. A final question before hand-over asks whether the plan, with every point followed, still fits.

### 7. The format filter is curation, with prose opt-in

Format and convention findings stay in the review. The rule is stated as curation of what reaches the student, so it does not conflict with "no separate quality rubric".

A workspace that wants format remarks in the feedback says so in its `guidelines.md` prose. That needs no override key: it is a judgement instruction, and the formalization boundary keeps judgement in prose.

The "format issues → proposal-check" pointer mapping goes. Language quality becomes a point only when it blocks understanding.

### 8. Wording rules sit in Curate the feedback, not the voice block

The following are supervise-local:
- reason with every judgement (observation, then why it matters, then direction);
- translated review vocabulary;
- no action items in "What to keep";
- a contradiction check;
- a final self-check against existing rules (direction, not prescribed fix; no praise).

The shared voice block is byte-identical across ten skills and carries no operational rules by design.

### 9. Locators, markup, length, language

- **Locators:** first mention of every source the proposal does not cite. A paper gets its DOI URL (existing rule). A standard or regulation gets its issuer's official page, resolved in this run. Locators do not count toward length.
- **Markup:** bold and plain lists only. No heading lines, blockquote lines or backticks, so skill names appear as plain words. The closing note stays markup-free, as before.
- **Length:** soft target of about 1,200 words for the body. Detail moves into the review first. The wrap-up reports the count, and the dev runner reports it as information.
- **Language:** the proposal's language. If the student's message uses another, the wrap-up offers a version in that language.

### 10. Resubmission by content, earlier points carried before overwrite

Intake looks for an existing `<slug>-review.md` or `<slug>-feedback.md` for the same idea in the proposal location and in any workspace-routed professor-side location. Same title, research questions or method count as a match; identity never does.

When a match is found:
- The earlier curated points go into the new review's `## Earlier round` section (German: `## Frühere Runde`), with resolved, partly resolved or open per point, before any file is overwritten.
- The feedback gains one sentence after the verdict.
- New points are marked new, and settled points are not raised again.

### 11. Harness

New verdicts in `harness/l1_checks.py`, each with L0 tests:

| Verdict | Fails on |
|---|---|
| `verdict_supervise_substance_only` | a sentence that pairs a document-convention subject with a removal, shortening or restyling cue; using the Gantt chart as evidence passes |
| `verdict_supervise_markup` | heading, blockquote or backtick lines |
| `verdict_supervise_locators` | a standard or regulation designation absent from the normalized proposal with no URL in its paragraph |
| `verdict_supervise_scope_options` | fewer than two lettered options, or no student-choice wording |
| `verdict_supervise_review_sections` | a missing workload table with its verdict line, or a missing verification section |

`verdict_single_context` gains an allowance argument, defaulting to zero, and the supervise scenarios allow one helper. The runner reports the feedback body's word count.

The first three verdicts join the aggregate contract and the Inspect task's scorers. Supervise is outside the model-support baseline, so new scorer names only need the eval-wiring pins and the regenerated projection.

The new fixture `s02-overscoped-export` is a synthetic raw text export of a Bachelor's proposal, with:
- a chained five-package plan in about fourteen weeks;
- a requirements catalogue whose size is never stated;
- a phase table and a chapter outline;
- fake identity data;
- a wrong claim about which EU act covers public-sector websites;
- a real, verified paper cited for the opposite of what its abstract says.

It is invented from scratch in a different domain (web accessibility) and copies nothing from the real session.

## Risks / Trade-offs

- **Token cost rises:** lookups plus one verifier, estimated at 150–250k tokens. → One verifier, never one per class. Claims that are neither load-bearing nor cheap to verify are deleted, not verified. The dev run measures the actual cost.
- **The verifier is fallible too:** about 72–88% agreement with humans in published automated fact-checking. → The main agent decides each finding and re-checks every changed sentence against its source. The verifier informs the decision and never writes.
- **Paywalls and bot challenges make many norm and paper claims unverifiable.** → An unverifiable claim becomes a question or disappears; the wrap-up lists it. That is the intended degradation.
- **The format verdict may misfire** on a sentence that uses the Gantt chart as scope evidence. → It requires a removal or restyling cue in the same sentence, and L0 tests pin the evidence case as passing.
- **The scope judgement is subjective.** → The table makes it inspectable and the estimates are labelled. The feedback offers options rather than a ruling, and the professor edits the draft.
- **A smaller model may skip the new steps.** → The dev scenario measures it on sonnet. The memory of earlier runs says haiku fails supervise already, so the matrix decision stays deferred.
- **This change and the running citation-smoothing work touch neighbouring surfaces** (`harness/l1_checks.py`, `harness/claude_runner.py`). → Stage exact paths only and re-check the working tree before committing.

## Migration Plan

Nothing migrates. Existing reviews and feedback files stay valid. A professor gets the new behaviour after the repository is published and the workspace re-runs `npx skills add`. Both steps are explicit-request only. Rollback is reverting the change's commit.
