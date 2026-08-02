## Context

See `proposal.md` — Why. Three facts about the current state shape the approach.

**The openings are not uniform in kind.** Of the eight, one is a hard prohibition (`proposal-check`), two are role or scope limits (`proposal-ideate`, `proposal-review`), and five are already purpose-shaped declarative prose (`proposal-write`, `proposal-import`, `proposal-customize`, `proposal-publish`, `proposal-lit-search`). Any pattern that only makes sense in front of a prohibition fits three files and stutters on five.

**Mandate position is not the guard.** `harness/README.md` records the measurement: under the autonomous Inspect loop, models edit the proposal during check and review despite escalating prohibitions, and the `chmod` hardening was defeated outright. The recorded conclusion is that the production environment, not prompt text, is the effective guard. Neither eval path can falsify a position regression either — the Inspect scenarios are expected-red, and the dev runner is green because of the environment. So this design cannot buy safety by keeping the mandate at position zero, and cannot measure a loss if it moves.

**The public page truncates by length, not by paragraph count.** Observed fold points on the live pages sit around 1,900 characters — `proposal-review` folds at body line 21 of 28, `proposal-import` at line 83 of 124. The site's generated summary line takes the first purpose-shaped sentence it finds: `proposal-check`'s live summary is its body line 12 verbatim, skipping the bolded mandate at line 8. A purpose paragraph therefore improves the generated summary wherever it sits in the header.

## Goals / Non-Goals

**Goals:**

- One header shape, applied identically to all eight files, with no per-file variants.
- The header is mechanically checkable, so it survives contributors who have not read this document.
- Mandate wording is pinned, so the "verbatim" constraint is enforced rather than trusted.

**Non-Goals:**

- Improving agent compliance with the mandates. This design holds compliance constant; the environment is the guard.
- Controlling the site's generated summary line. It is influenced, not set.
- Restructuring anything below the header. The rest of each `SKILL.md` is untouched.
- A package-level description. The registry has no slot for one.

## Decisions

### Header order: purpose → workflow → mandate

Four orderings were evaluated: purpose→workflow→mandate (chosen), mandate→purpose→workflow, a variant folding the constraint into the purpose sentence, and purpose→mandate→workflow.

Chosen over **mandate-first** because mandate-first leaves the stated problem untouched: the first rendered line stays a prohibition on the page that most needs not to open with one. Its case rests on frame-lock — that an imperative first line tells the model what kind of file this is — which is an unmeasured prior, and one that is vacuous for the five files whose openers are already declarative prose.

Chosen over **purpose→mandate→workflow** on a concrete structural ground rather than a fold-position one. That ordering wedges the seven-skill roster between `proposal-check`'s mandate and the paragraph directly beneath it, whose "verify the mandate mechanically" is anaphoric and points at the paragraph above. Inserting above the mandate keeps mandate and enforcement welded on all eight files with no per-file patching, and does not depend on a claim about where the fold lands.

Chosen over **folding the constraint into the purpose sentence** because whichever statement of a rule lands first fixes that rule's scope. A purpose ending "nothing is changed and nothing is gated" scopes the read-only rule to the proposal file, which makes `proposal-check`'s separate "never write a report file" read as negotiable. The fold also has nothing to fold on `proposal-publish` and `proposal-lit-search`, so it degrades to the chosen shape on two files anyway, and it requires eight hand-written paraphrases of eight different constraint types — eight chances to weaken a rule by rewording, with no auditable invariant.

### The purpose block states a deliverable, never a rule

Direct consequence of rejecting the fold, and the rule that keeps the five purpose-shaped openers from stuttering: where an opener already describes what the skill does, the purpose block adds the user-facing outcome that opener omits, rather than re-saying it in softer words.

### The purpose block avoids second person

Everywhere else in these bodies, "you" is the agent. A purpose paragraph reading "you get the findings" collides with that. Purpose blocks are written impersonally or in the third person, which also reads better on a public page.

### The workflow line is byte-identical, including for the two off-chain skills

The canonical line, with the containing skill's own name wrapped in `**`:

```
**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → proposal-review → proposal-publish. Also: proposal-import (start from an existing document), proposal-customize (adapt the rules to a supervisor's requirements).
```

`proposal-import` and `proposal-customize` sit off the main chain and bold their own name inside the `Also:` clause. They get no variant sentence and the chain arrows are not redrawn to include them. The parenthetical glosses already read as entry point and configuration; a second template would buy marginal expressiveness and cost the invariant, because a contributor adding a ninth skill would face two shapes and no rule for choosing between them. Byte-identity is the only version of this line a test can enforce.

### No per-skill exceptions, including `proposal-review`

`proposal-review` is the design's weakest point: its content-only rule is stated exactly once, has no heading, sits on the shortest file in the set, and is the mandate the evals assert most directly — yet it moves to third position behind a line that names `proposal-check`.

Giving that paragraph its own heading was considered as a mitigation and rejected. A heading above the mandate places it after the file's first section heading, which gives `proposal-review` a block order no other skill has and leaves the drift guard with an optional slot instead of one shape. Uniformity is the requirement, and an exception used by one file in eight is the shape contributors copy wrongly.

The exposure is therefore carried as a measured risk rather than pre-empted: the after-run reads the review scenario's structural-complaint assertion specifically, and a heading is added only if that assertion regresses. Adding it later costs one line and one spec amendment; adding it now costs the invariant permanently.

### The drift guard pins mandates by fixture, not by regex

`tests/unit/test_format_prose_drift.py` and `test_audit_invariants.py::test_lit_search_keeps_no_hand_through_rule` are the precedent — this repository already pins `SKILL.md` prose literally. The new test parses each body into blank-line-separated blocks up to the first `##` heading and asserts workflow-line identity across the set, self-bolding against the directory name, block order with exactly one paragraph before the workflow line, adjacency after the mandate, and mandate equality against one fixture file per skill.

Pinning the mandate by fixture rather than by pattern is the load-bearing choice. It is what turns "the mandate stays verbatim" from a review-time hope into a test failure, and it costs one small text file per skill.

### `proposal-lit-search`'s description is trimmed

It enumerates five scholarly databases by name. Discovery-time routing does not need them, and the body already documents which sources are queried.

## Risks / Trade-offs

- **`proposal-review` is the real exposure** — a once-stated, unheaded mandate moves to third position behind a line that names `proposal-check`, and `review_quality.txt` asserts that review makes no structural complaints → deliberately unmitigated at build time; read the review scenario's scores specifically in the after-run rather than only the aggregate, and add a heading as a follow-up change only if that assertion regresses.
- **The safety argument generalizes from two environments** — the Inspect loop and the dev runner, not the arbitrary third-party hosts where installed skills run → accepted knowingly; no available measurement can close it, and the recorded evidence says prompt position was not providing the guard in the first place.
- **A third unlinked copy of "what this skill does"** now exists per skill, after the frontmatter `description` and the README roster table → only the workflow line and the mandates are guarded; the purpose blocks are not, and can drift from the description.
- **Preamble-to-content ratio on the shortest file** — `proposal-review` grows about 17% → absolute growth across the set is roughly 32 lines against a 500-line-per-file ceiling, so this is cosmetic.
- **The generated summary is not ours** — the observation that it takes the first purpose-shaped sentence came from published pages and can change without notice → we are influencing an output we do not control, and the change is still worth making for the fold content alone.
- **The workflow line is eight-way-identical boilerplate in the second block** — a summarizer weighting the second paragraph could produce eight similar one-liners → the distinctive text is in block one, which is where the generator has been observed to read.

## Migration Plan

Single commit, no staged rollout: the skills are shipped as files and the default branch is the release channel. Rollback is `git revert`. Nothing user-side needs migrating — installed copies are replaced wholesale on the next `npx skills add`.

Order matters only in that the drift test lands with the eight edits, not before them, so the suite is never red on `main`.
