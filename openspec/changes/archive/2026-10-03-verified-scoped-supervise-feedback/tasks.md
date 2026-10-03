# Tasks

## 1. Harness verdicts first (gate before the skill text)

- [x] 1.1 Add `verdict_supervise_substance_only(feedback)` to `harness/l1_checks.py`. It is a sentence-level pairing of a document-convention subject (name/cover data, Gantt/phase list/work plan, chapter outline/structure, timeline length, page count/limit, reference/proxy link style; English and German) with a remove/shorten/restyle cue. It must pass a sentence that cites the Gantt chart as scope evidence. Verify: L0 tests in `tests/unit/test_supervise_verdicts.py` cover the lecture failing, the evidence use passing, German, and an empty feedback.
- [x] 1.2 Add `verdict_supervise_markup(feedback)`. It fails on heading lines, blockquote lines or backticks and allows bold. Verify: L0 tests cover each failing case, bold passing, and the closing note passing.
- [x] 1.3 Add `verdict_supervise_locators(feedback, proposal)`. Any standard or regulation designation (ISO/IEC/EN/DIN/NIST SP numbers, Directive/Regulation (EU) numbers) absent from the normalized proposal needs a URL in the same paragraph. Verify: L0 tests cover an unlocated new designation failing, a designation already in the proposal passing, a located one passing, and no designation passing.
- [x] 1.4 Add `verdict_supervise_scope_options(feedback)`. It requires at least two distinct lettered options (`A)`/`B)`, `(A)`, `Option A`) and student-choice wording (choose/choice/decide, wählen/entscheiden). Verify: L0 tests cover the pass, one option failing, numbered options failing, and missing choice wording failing.
- [x] 1.5 Add `verdict_supervise_review_sections(review)`. It requires a `## Workload`/`## Arbeitsumfang` section with a markdown table and a scope verdict line (fits/tight/over-scoped; passt/knapp/zu umfangreich), plus a `## Verification`/`## Überprüfung` section. Verify: L0 tests cover each missing piece and both languages.
- [x] 1.6 Extend `verdict_single_context(tool_names, allowed=0)` so it passes up to the allowance and names every call when exceeded. Verify: existing L0 tests unchanged and green, plus new allowance tests (one allowed call passes, two fail).
- [x] 1.7 Add a `feedback_body_words(feedback, closing)` helper that excludes URLs and the closing note. Verify: an L0 test on a sample feedback.
- [x] 1.8 Join verdicts 1.1–1.3 to `verdict_supervise_feedback_contract`. It needs the normalized proposal text to pass to the locator verdict: absent → that verdict is skipped and its report says so. Verify: the aggregate L0 tests are updated and green.

## 2. Over-scoped raw-submission fixture

- [x] 2.1 Verify via Crossref, in this run, the one real paper the fixture cites for the opposite of its abstract. Record the DOI and the abstract's actual finding in the fixture README entry. Verify: the Crossref record resolves and the title matches.
- [x] 2.2 Write `tests/fixtures/s02-overscoped-export/submission-export.txt`: a synthetic Bachelor's proposal export, English, in the web-accessibility domain. It carries:
  - fake identity (Erika Musterfrau, 00000000, supervisor and company placeholders);
  - a chapter outline;
  - a phase table of five chained packages in about fourteen weeks;
  - a requirements catalogue whose size is never stated;
  - a wrong claim about which EU act covers public-sector websites;
  - the paper from 2.1 cited for the opposite of what its abstract says.

  Nothing is taken from any real proposal. Verify: the file exists and a grep finds the fake identity tokens.
- [x] 2.3 Add the `s02-overscoped-export` entry to `tests/fixtures/README.md` (raw submission, no oracle, what each planted defect exercises). Verify: the fixture-corpus L0 tests stay green (the `.txt` stays outside the proposal invariants).

## 3. Dev runner and Inspect wiring

- [x] 3.1 Allow one helper in both supervise scenarios (`helpers: 1`) and pass the allowance to `verdict_single_context` in the summary. Report the feedback body word count in the summary for feedback scenarios. Verify: the L0 runner/summary tests are extended and green.
- [x] 3.2 Add a `supervise_scope` scenario over `s02-overscoped-export`, with import and lit-search as siblings. The request pre-answers both stops: borderline → needs revision, and lookups granted with no further questions. Its verdict is the feedback contract with s02's forbidden tokens, plus scope options and review sections. Generalize `feedback_files`/the verdict dispatch so per-scenario forbidden tokens and the normalized proposal reach the contract. Verify: L0 tests of the dispatch on a synthetic workspace.
- [x] 3.3 Add scorers `supervise_l1_substance_only`, `supervise_l1_markup` and `supervise_l1_locators` to the Inspect `supervise_feedback` task. Update `tests/unit/test_eval_wiring.py` pins and regenerate the projection with `uv run python harness/eval_export.py`. Verify: `tests/unit/test_eval_wiring.py` and `tests/unit/test_eval_projection.py` are green.

- [x] 3.4 (Found during 6.4.) An expired host login ends as subtype `success` with `errors` null, and the runner reported "no detail". Make `host_failure` fall back to `terminal_reason` and the result text. Verify: an L0 test against the recorded shape.

## 4. Skill text

- [x] 4.1 Rewrite the `## Execution shape` section of `skills/proposal-supervise/SKILL.md` to the verifier design (cap three: main, one fresh verifier of the finished feedback, one adversarial check; no-helper hosts ask the checks separately) and update `tests/unit/data/pinned_sentences/proposal-supervise--execution-shape.txt` in the same edit. Verify: `tests/unit/test_execution_shape.py` and `test_substance_tests.py` are green.
- [x] 4.2 Rewrite the approval section into one combined question, with a checking-only wording when the sibling is missing and the offline consequence stated. Update `proposal-supervise--literature-approval.txt` to pin both wordings. Verify: `tests/unit/test_pinned_sentences.py` is green.
- [x] 4.3 In Normalize the submission, add resubmission intake: content matching only, earlier points carried into the new review before overwrite, a one-line chat note when an indicated earlier round is absent, and the notes file extended rather than reseeded. (A drafted "location error is expected" exemption was removed in review, because it disarmed the guard against writing to the wrong directory.) Verify: by reading the section against the spec's Resubmission intake scenarios.
- [x] 4.4 Add a `## Check the workload` section between Find the issues and Decide the tier: work-package table, unknowns as questions, Gantt/work plan from notes as evidence, no shipped constants, the three verdicts with their review headings, and over-scoped barring ready without counting toward the idea-stage bar. Pin its load-bearing sentence as `proposal-supervise--workload.txt`. Verify: the pinned-sentence test is green.
- [x] 4.5 In Curate the feedback:
  - substance-only curation with the workspace prose opt-in, and remove "format issues → proposal-check";
  - each point as observation → why → direction;
  - translated vocabulary; no action items in What to keep; contradiction check;
  - the scope paragraph with lettered options and option-conditional points;
  - the net-workload budget, woven literature included;
  - light markup with plain skill names;
  - locators for standards and regulations at their issuer pages;
  - the ~1,200-word soft target with detail moving into the review;
  - the language offer.

  Verify: by reading the section against the spec scenarios. `test_skill_header_pattern.py` and `test_report_offer.py` are green.
- [x] 4.6 Add a `## Verify before hand-over` section after Curate the feedback. It covers:
  - the claim ledger classes and their evidence rules (exact quotes, absence after search, paper abstracts including the student's own references, norm primary or issuer text, computed figures);
  - unverifiable claims becoming questions;
  - corrections re-checked;
  - the review's verification section, exceptions first;
  - the refuted premise reopening the tier;
  - the final self-check against existing rules;
  - the post-points workload re-check.

  Pin the claim-ledger sentence as `proposal-supervise--claim-ledger.txt`. Verify: the pinned-sentence test is green.
- [x] 4.7 Update the literature section for the budget sentence and the combined consent, and the Wrap-up for unverified claims, the scope verdict, the feedback length and the language offer. Verify: `test_pinned_sentences.py` is green, with the literature-verification pin still matching.

## 5. Evidence base and docs

- [x] 5.1 Write `docs/supervisor-feedback-sources.md` with the sources verified in this change's research (feedback pedagogy, scope and workload, AI-feedback verification), each with its DOI or URL and the design decision it backs, plus the stated evidence gaps. Verify: every DOI resolves through Crossref in this run.
- [x] 5.2 Note the `supervise_scope` scenario and the helper allowance in `harness/README.md`. Verify: by reading it; the README tests stay green.

## 6. Verify and close

- [x] 6.0 Adversarial review of the diff: three lenses, one refuter per finding. It confirmed 30 findings, all fixed in this change:
  - verdict false positives and false negatives;
  - idea-stage cut options;
  - the import validation running offline;
  - the untrusted-data rule;
  - tier independence from lookups;
  - the misplaced-file exemption;
  - an institution-specific registration rule;
  - dropped clauses;
  - s01 requests that did not decline the checks;
  - the fixture subtitle;
  - one source misdescribed.

  Verify: a regression test per verdict case in `tests/unit/test_supervise_verdicts.py`, and the gate green.
- [x] 6.1 `uv run poe test` green: all L0 tests, ruff, drift, conform.
- [x] 6.2 `uv run poe specs` green.
- [x] 6.3 `uv run poe cov` at or above the floor.
- [x] 6.4 Run `uv run poe dev supervise_scope --model sonnet` on the subscription. Record the verdict, helper calls, cost, tokens and feedback word count in `measurement.md` in the change folder, and read the produced review and feedback by hand: were the planted regulation claim and the misused paper caught?
- [x] 6.5 Run `uv run poe dev supervise_feedback --model sonnet` as the regression arm on s01 and record it the same way.
