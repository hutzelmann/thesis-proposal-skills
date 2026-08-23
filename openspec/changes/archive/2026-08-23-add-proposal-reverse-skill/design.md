## Context

See proposal.md — Why. Two constraints from this repository shape everything below.

A skill must work installed alone, so anything core to its function ships as a synchronized copy rather than borrowed from a sibling. And no thesis may enter this repository: they are long and they are copyrighted, so the fixture set cannot contain one, and the dev-side design has to work without one.

A third constraint is not a rule but a judgment already made: whether a proposal is *good* is a human assessment. Nothing here may claim to test it.

## Goals / Non-Goals

Goals: a proposal in the standard format from a finished thesis; a dev-side test that needs no thesis; a mechanical leak rule that is also useful to proposals written the ordinary way.

Non-Goals: no drift analysis between an existing proposal and a thesis — that is a plain prompt over two documents and needs no skill. No literature search: reverse is one pass, like import. No automatic verdict on proposal quality.

## Decisions

**A separate skill rather than a branch in `proposal-import`.** Import shares most of the machinery — target shape, canonical section mapping, CSL-YAML conversion, personal-data stripping, the notes file, the check loop — and reverse will point at it where it is installed. But import's mandate is to carry an existing proposal across, and reverse's is to remove what the source knows. A mandate cannot say both, and the opening-structure rules make the mandate the load-bearing sentence of the page. Two skills, one of which reuses the other's rules by reference.

**Reverse ships its own scripts.** The alternative, a sibling fallback on import, is only permitted where the degraded mode still fulfils the skill's purpose. Reverse verifies its own fresh output before reporting, which is the same reason import and write ship `check.py` as synchronized copies. So `check.py`, `validate_refs.py` and the modules it imports, plus `structure.json`, become new destinations in `SYNC_MAP`. Where reverse leans on import for the finer conversion rules, it states the essential ones inline so that a solo install still works, and names import as the fuller source when present.

**The harvest record is the seam, and it is what makes the dev side possible.** Both steps are model behavior, so there is no L0 test for either. The affordable test is an L1 task whose input is a synthetic harvest record of a few kilobytes — small, obviously fake, no copyright, and it exercises every write-step rule: the knowledge cut, scope and validity carried forward, reference survival, the shortfall escalation. Harvesting itself — locating chapters in a PDF — is the least interesting stage and is left to manual verification against a real thesis outside this repository.

The record is not only test scaffolding. It is what the user inspects before any prose is written, which matters most in the case the skill is largely for: a supervisor deriving an exemplar from someone else's thesis wants to see what was taken out of it.

**The leak rule is anchored on citations.** Without that anchor the rule fires on every well-written Contribution section, because reporting what prior work established is that section's job. With it, the rule is cheap and precise, and it is worth having independently of reverse: a student who writes the proposal after starting the work leaks the same way.

The rule stops at surface patterns. A research question that presupposes its answer is only detectable by knowing what the work found, and the document does not carry that. Encoding it would put a semantic quality rule into mechanical data, which this project's formalization boundary forbids.

**Scope and validity replace an earlier idea.** An earlier draft proposed mining the thesis for its scope drift — "we originally intended X but". Theses report results, not process, so that material is usually absent and the rule would have been unsourced. What is reliably present is the delimitation statement and the limitations chapter, and both are legitimate proposal content. The concern that motivated the earlier rule — a reverse-derived proposal reading as suspiciously perfect — is better answered by the knowledge cut applied to specifics, since the real tell is overspecification, not a plan that worked.

## Risks / Trade-offs

**The body-size gate has a floor as well as a ceiling.** The cap is twice the suite median; the median of ten bodies is 1308.5 words and `proposal-ideate` sits at 2598. An eleventh body under roughly 1300 words moves the median down and fails ideate, which would read as an unrelated regression. → The task list states the floor, and the verification step runs the whole offline suite rather than the fast subset.

**The frontmatter budget is nearly spent**: 4102 of 4500 characters, leaving under 400 for the new skill's name and description. → The description is written to that budget. Raising the budget is a separate decision and not part of this change, because the budget exists to bound what every session loads whether or not the skill is used.

**A skill that derives a proposal from a finished thesis can be used to manufacture an ex-ante record.** → The teaching-exemplar case has no such problem, and the retroactive-submission case is the user's own integrity call. The mitigation is one sentence of openness in the output, not machinery: a metadata key or a refusal path would be trivially removable and would buy nothing.

**Harvest quality is unverified offline.** Locating chapters in a real thesis PDF is exactly what no fixture in this repository can exercise. → Accepted, and named: it is verified by hand against real theses outside the repository, and a harvest that reads the wrong chapters is visible to the user in the record before any prose is written.

## Migration Plan

Additive. No existing skill changes behavior; the workflow line gains a name and every page is re-materialized by the existing sync. Rollback is deleting the skill directory, reverting the block, and re-running the sync.
