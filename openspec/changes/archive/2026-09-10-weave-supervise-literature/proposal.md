## Why

A real supervise run on 2026-09-10 (a literature-free submission) produced the feedback the professor wanted only after two manual rounds: the shipped starter-literature step is offered at the end of the run, only for idea-stage outcomes, and appends a standalone list after the points are written — so the papers can never do work inside the points, and a needs-revision submission with two blog posts as its whole bibliography gets none at all. The professor wants that grounding by default, with one approval up front for the network access it needs.

## What Changes

- **Approval moves to the start of the run.** When the literature-search sibling is installed, the skill asks once, before anything else, in fixed pinned wording that names the read-only network access and that the search is conditional on the findings. An invoking message that itself asks for literature counts as approval. Declined, unanswered, headless, or sibling missing: no search, no repeat, no trace in the feedback.
- **The trigger is the finding, not the tier.** With approval, the search runs at any tier where the review holds a literature-grounding finding (empty or thin references, an unsourced load-bearing claim, a research question the literature already answers, vendor sources carrying weight); a ready-tier feedback carries none.
- **Tier first, search after.** The search runs once the tier is decided and never moves it — the same submission gets the same tier with or without network. Found papers sharpen the wording and evidence of review findings and curated points.
- **Search rule for this purpose.** One query per finding, phrased from the job the paper is to do; snowball from the submission's own references first when any exist; retarget once on drift; a small fixed cap on script runs; degradation notes relayed in one line.
- **Verification bar, pinned.** Nothing enters the feedback, the review, or the notes file without a record returned in this run by the sibling's scripts or its sanctioned read-only fallback — memory-known papers included. Relevance is judged on abstract and metadata.
- **Woven, never listed.** At most three papers, each inside the curated point or the strengths block where it does work; no standalone literature list or block; a paper that fits no point is dropped. First mention: authors, year, title, venue, `https://doi.org/…`; later mentions author and year. Points stay three to five directions.
- **Professor side.** The normalized proposal stays the faithful record of the submission (nothing merged into its references); the notes file records each woven entry as CSL-YAML with the point it serves, rejected candidates under Excluded Literature; the wrap-up names the woven papers.
- **Removes** the standalone "Starter literature" step and its spec requirement and scenario — replaced, nothing kept beside the new rule.
- **Harness.** A new offline-testable verdict checks a produced feedback's literature: every DOI cited sits inside a point or the strengths block rather than a list, is recorded in the notes file, and at most three papers are cited; wired as a separate `supervise_l1_*` scorer and into the dev runner's aggregate; headless runs pre-answer the approval question like the borderline deferral. No new metered task.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-supervise`: "Student-facing feedback with disclosure and steering" loses the end-of-run starter-literature offer and its scenario; a new requirement "Literature grounded by consent" states the up-front approval, the finding-based trigger, the tier-first order, the search and verification rules, the weaving rule, and the professor-side records.
- `testing-harness`: "Supervise feedback coverage" adds the literature verdict (placement, notes record, cap) and the pre-answered approval question for headless runs.

## Impact

- `skills/proposal-supervise/SKILL.md`: new "Ask once about literature" and "Ground the points in literature" sections; "Curate the feedback" step 4 replaced; wrap-up names woven papers and the notes file. Three new pins under `tests/unit/data/pinned_sentences/` (approval wording, verification sentence, fetched-data judgement).
- `harness/l1_checks.py` (`verdict_supervise_literature`, aggregate extended), `harness/skill_evals.py` (scorer + task wiring), `harness/claude_runner.py` (request pre-answer, notes staged into the aggregate, and the dev-runner-only scenario `supervise_literature` with `proposal-lit-search` staged as a sibling and the approval granted in the request), `harness/eval_export.py` (expected output, scorer→verdict map), `harness/README.md` (task line plus the `supervise_literature` paragraph), `skills/proposal-supervise/evals/evals.json` (regenerated).
- `tests/unit/test_supervise_verdicts.py`, `tests/unit/test_eval_wiring.py`.
- `README.md` "For supervisors": one sentence on literature grounding and the approval.
- No `shared/` content, no scripts, no frontmatter, no methodology defaults.
