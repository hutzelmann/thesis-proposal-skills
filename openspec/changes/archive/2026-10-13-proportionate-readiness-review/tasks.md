# Tasks

## 1. Shared guidance

- [x] 1.1 Add the `## Readiness` section to `shared/guidelines/guidelines.md` after `## Substance Tests` (three classes, blocker = delta/falsifiability/swap/method-fit/executability failure, deferral record, optional-part test, dependency safeguard, selection-rule sentence, stopping rule, monotone rounds); verify every spec scenario of "Readiness classification" is answerable from the prose
- [x] 1.2 Add the plausible-plan sentence to the executability test and the selection-rule sentence to Methodology Content; verify the substance-test-name drift guard still passes (`uv run pytest -k substance`)
- [x] 1.3 Run `python3 scripts/sync_shared.py` and verify `python3 scripts/sync_shared.py --check` reports no drift; stage only the regenerated `references/guidelines.md` copies

## 2. proposal-review

- [x] 2.1 Rewrite the review's assessment scope: replace "missing information a supervisor would ask about" with what the substance tests need; move title, density and necessity findings to refinements; verify the pinned level-bar sentence and execution-shape pin still match (`uv run pytest tests/unit/test_execution_shape.py`)
- [x] 2.2 Add the earlier-round step (read the previous review before overwriting, monotone classification, missed-earlier label, old-format reviews classified fresh) and verify against the "Review rounds converge" scenarios
- [x] 2.3 Rewrite `## Output`: derived verdict with the not-an-execution-protocol sentence, the four sections with their English and German titles, blocker reasons, deferral records, agenda named in the chat summary; verify the header-pattern and mandate tests pass (`uv run pytest tests/unit/test_skill_header_pattern.py`)

## 3. proposal-supervise

- [x] 3.1 Update "Find the issues" and "Check the workload" so the review classifies findings and workload unknowns split into questions vs clarify-early items; verify against the modified "Workload volume check" scenarios
- [x] 3.2 Update "Decide the tier" and "Curate the feedback": points are blockers only (0–5), the labelled clarify-early block (≤ 5 one-line items, both tiers, never at idea stage, no meeting), placement order; fix the "Three to five points" wording; verify the bilingual-terminology guard passes
- [x] 3.3 Update the earlier-round paragraph with the monotone rule and the missed-earlier record; update `references/verifier-brief.md` so the verifier treats the block's items as not-conditions and checks no meeting is promised; verify supervise pins still pass

## 4. proposal-write

- [x] 4.1 Update "Refining" and "The notes file": applying a review works blockers and refinements into the proposal and records clarify-early items with their records under Open Points; the notes file may be created for them; verify the write pins still pass

## 5. Fixtures

- [x] 5.1 Write `tests/fixtures/f28-open-decisions/` (check-clean MSc Empirical Model Evaluation proposal with unnamed model versions, optional expert ratings no RQ depends on, pilot-fixed audit size) with `expected.json`; verify `check.py` matches the oracle
- [x] 5.2 Write `tests/fixtures/f29-doubtful-dependency/` (f28 with one paragraph changed so RQ2 depends on partner access still to be negotiated) with `expected.json`; verify the oracle and that the diff to f28 is confined to that paragraph
- [x] 5.3 Write `tests/fixtures/w09-revised-round/` (f28's text, an earlier-round `-review.md` with two blockers the text resolves and one clarify-early bait item about an unchanged passage) with `expected.json`; verify the corpus invariants (oracle, build, notes/review exclusion) pass — the four corpus walkers now share `helpers.is_fixture_proposal`, which recognises a review by the proposal beside it (a bare `-review.md` suffix would have excluded f00's `ml-code-review.md`)
- [x] 5.4 Add the three fixtures to `tests/fixtures/README.md`; verify any README-listing guard passes

## 6. Harness

- [x] 6.1 Add `verdict_review_ready`, `verdict_review_dependency`, `verdict_review_converged`, and the section parser to `harness/l1_checks.py`, each with L0 tests on crafted review texts (English and German); verify `uv run pytest tests/unit -k verdict`
- [x] 6.2 Relax `verdict_supervise_points` (zero points only with the ready tier) and add `verdict_supervise_ready_block` (ready tier, no numbered point, labelled block of at most five items, no meeting promise), with L0 tests; verify existing supervise verdict tests still pass
- [x] 6.3 Add `harness/rubrics/readiness.txt` following the rubric-template contract; verify the rubric-wiring tests pass — golden prompt recorded under `tests/unit/data/l2_prompts/readiness.txt`
- [x] 6.4 Add dev-runner scenarios `review_ready`, `review_dependency`, `review_converge`, `supervise_ready` to `harness/claude_runner.py` and wire their verdicts and judge rubric; verify `uv run poe dev --help` lists them and the runner's L0 tests pass
- [x] 6.5 Register the four Inspect tasks in `harness/skill_evals.py` with `*_l1`/`*_l2` scorer names and CRITERIA entries; regenerate the `evals/evals.json` projections; verify `tests/unit/test_eval_wiring.py` and the projection drift check pass — on-demand `extended` set; not in `excluded_l1`, which the registry admits only for matrix tasks, so their L1 keeps the byte-identity probe (documented in `models.toml`)
- [x] 6.6 Document the scenarios in `harness/README.md`; verify the README's scenario list matches the runner

## 7. Verification

- [x] 7.1 Run `uv run poe test` and `uv run poe specs` green (failures from the concurrent `pass-source-verification` work reported separately, not fixed here) — 3156 passed, ruff clean, copies in sync, 11 skills conform; specs 20/20 (after `pass-source-verification` landed as d1bfdaa)
- [x] 7.2 Dev runs on the subscription, haiku and sonnet: `review_ready`, `review_dependency`, `review_converge`, `supervise_ready`, plus `review_hollow` and `review_fixture` as underblocking guards, with `--judge`; record outcomes in this file. All runs were isolated with `--judge`; nothing was metered. Logs: `logs/devrun/readiness.jsonl` (iteration) and `logs/devrun/readiness-final.jsonl` (final state).
  - **Final state, all PASS L1 and L2:**
    - sonnet: `review_ready` (ready, 0 blockers, 6 clarify-early items, and the verdict says it is not an execution protocol), `review_dependency` (access blocker under executability), `review_converge` (3 earlier items resolved, nothing promoted), `supervise_ready` (ready, 0 points, 5 clarify-early items, no meeting, fresh verifier, 394-word body), `review_fixture` (guard: f05's mixed methodology is still a blocker, needs revision);
    - haiku: `review_ready` (5 clarify-early items), `review_dependency`, `review_converge`, `review_hollow` (guard: no viable thesis core, five tests cited).
  - **Iteration findings.** Before the final state, L2 failed seven times and the supervise L1 once; most of these were instrument errors, recorded here rather than hidden (see `verify-tooling-before-blaming-models`):
    1. The L2 criteria demanded that specific items be *listed* as clarify-early, where the rule only forbids them as blockers. The criteria and oracles now read "not a blocker; whatever is deferred carries its record".
    2. The converge criterion forbade settling an unchanged clarify-early item, which the monotone rule allows (same or lower class). The criterion was fixed and the kept workspace re-graded via `--rejudge`.
    3. The rubric's tone bullet counted a verdict naming the passing tests as praise. It now matches `review_quality.txt`, which allows plain statements of what is fine.
    4. The supervise pointers verdict demanded a skill name on a ready feedback with no points. A pointer is now owed per point, and the kept workspace was re-scored offline.
    5. Fixture confounds in f28: five references (below the working range), no compute budget for about 7,200 runs, an unstated configuration source, an uncited prior-work claim, an absolute gap sentence, and two internal inconsistencies. All were fixed in the three copies; the pair still differs in exactly two lines.
  - **Genuine model findings, kept:**
    - Haiku praised a sentence ("is strong and should stay").
    - Haiku gave an ethics item a fallback that narrowed RQ3 and told the student to add proposal text for a clarify-early item. The guidelines now say the fallback leaves every research question "answerable as asked" and the resolution happens "during the thesis".
    - Haiku hedged a conditional blocker. The guidelines now say a finding sits in one class only.
    - Sonnet abbreviated two deferral records. The review skill now asks for the whole record "however small".

    After these wording fixes both models pass.
- [x] 7.3 Adversarial review of the full diff against the specs; fix confirmed findings and re-run 7.1 — one fresh read-only reviewer, 16 findings, all verified and fixed:
  - **Unedited prose that still assumed the old model:**
    - the guidelines' "fails them is not ready" now excepts necessity;
    - supervise's "ready review over an over-scoped plan becomes needs revision" now records over-scope as an executability blocker, so the review is never ready over it;
    - supervise's "the six tests decide the verdict" now reads "every one but necessity can block";
    - the review's "where tests fail" now reads "where blocking tests fail";
    - "missing information the substance tests need" now adds "or the applicable guidelines";
    - "citation findings" now reads "citation-practice findings";
    - the root README's supervise feedback list now has up to five blocking points and up to five early-thesis decisions.
  - **Spec gaps:** MODIFIED deltas for "Student-facing feedback with disclosure and steering" (the dash list is admitted markup; a ready feedback owes no skill pointer) and "Level-calibrated feedback bar" (an unset level is one line outside the points). The Workload delta records over-scope as a blocker that the scope paragraph may carry alone.
  - **Verdict bugs:**
    - tier detection skips negated phrases ("not yet ready", "keine Überarbeitung erforderlich");
    - the earlier round counts each item by its first status word (no word counting; German "gelöst/behoben"; `open-weight` is not "open");
    - bullets and bold numbers count as items, and numbered section titles parse;
    - the clarify-early label must open its line, and wrapped items fold;
    - the meeting pattern matches promise constructions only ("meet the window" and "Entscheidungen treffen" pass; "our first conversation" and "Termin" fail);
    - zero points are allowed when lettered scope options carry the only blocker.

    Each case is an L0 regression in `test_readiness_verdicts.py`.
  - **Fixture:** f28/f29/w09 baseline "without log access" now reads "with the truncated log excerpt"; RQ3's "the two configurations" now reads "the two architectures".
  - **Kept as designed:** `verdict_review_ready` still requires at least one clarify-early item, since the agenda is part of the design goal; the testing-harness delta now says so.
