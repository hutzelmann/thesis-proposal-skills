# Tasks

Drafted 2026-10-13 for the maintainer's review, revised the same day after a critic pass. The maintainer answered Q1–Q8 on 2026-10-14 (design.md, "Maintainer decisions, 2026-10-14"): every recommendation accepted, Q3 dropped, Q5 strict with quote and dash folding, Q8 closed. An implementation review the same day added tasks 2.7–2.10, 4.5 and 5.6 and revised 3.3, 4.3 and 7.1 (design.md, "Implementation review, 2026-10-14"). The maintainer's decisions on that review added task 2.11 (design.md, "Maintainer decisions on the implementation review, 2026-10-14"): the fold extension confirmed, format characters removed, no record in w11.

Built in parallel with `tighten-proposal-family` (#7), on top of `main` at `2f1fa0d`, in its own worktree; never in a session sharing a checkout, since `.githooks/pre-commit` refuses mismatched generated copies. The rebase onto #7 is a landing-time task (7.1). Edit only `skills/proposal-check/scripts/check.py`; the five vendored copies come from `python3 scripts/sync_shared.py`. Placement rules that keep the rebase small (design, "Coordination"): new `check.py` helpers next to `rule_research_questions`, not after `paths_findings`; new `SCENARIOS` entries next to the same skill's scenarios in `harness/claude_runner.py`; new verdicts beside related verdicts in `harness/l1_checks.py`; fixture w16 only. Land as one commit with the archive.

## 1. Baseline

- [x] 1.1 On `main` `2f1fa0d`, before any code: record the baseline counts. Verify: `uv run poe test` green on the untouched tree. Baseline 2026-10-14: 4599 passed, 3 skipped; ruff, drift check and conformance clean.
- [x] 1.2 (Q3 = drop) `openspec/changes/mark-review-currency/specs/skill-write/` deleted by the orchestrator with the maintainer's explicit OK; no OpenSpec command removes a delta. Verify: `openspec validate mark-review-currency --strict` valid, and `openspec show mark-review-currency --json --deltas-only` lists no skill-write delta.

## 2. `check.py` (TDD: red tests first, in `tests/unit/test_check_rules.py` or a new `tests/unit/test_review_currency.py`)

- [x] 2.1 Write the red tests for a shared ordered-item extractor (design D3):
  - one-line items;
  - an indented continuation line, and an unindented lazy continuation, joined;
  - a nested sub-list kept inside its parent item, on the proposal side and on the record side;
  - an item ending at a blank line;
  - `1)` and `1.` markers;
  - bullet markers accepted on the record side only;
  - an indented marker never starting an item.

  Verify: they fail for the missing function.
- [x] 2.2 Implement the extractor and a `normalize_question` helper next to `rule_research_questions`: NFKC, whitespace collapse, then the quote and dash fold of design D3 (single quotes to `'`, double quotes to `"`, hyphen-minus, hyphen, non-breaking hyphen, en dash, em dash and minus sign to `-`; case untouched). Move `rule_research_questions` onto the extractor, keeping its count behaviour. Verify:
  - 2.1 green, plus normalization tests: curly versus straight quotes and en dash versus hyphen-minus equal, a case change unequal;
  - every existing research-question test and `test_fixture_oracles.py` unchanged and green.
- [x] 2.3 (Q7) Add `research-questions-too-many` to `RULE_IDS` and to `COVERED_BY_UNIT_TESTS` in `tests/unit/test_check_rules.py`, and add a unit test that trips it with six questions under the default bound. Verify: `test_every_declared_identifier_is_reachable`, `test_every_emitted_identifier_is_declared` and the new test green.
- [x] 2.4 Write the red tests for the review comparison (skill-check delta, all script scenarios; design D4, D5):
  - RQ4 removed;
  - RQ2 changed, with no question text in the message;
  - RQ3 added;
  - same questions re-wrapped, re-bulleted, with non-breaking spaces: silent;
  - same questions with straight quotes and a hyphen-minus where the proposal has curly quotes and an en dash: silent;
  - RQ1 differing only in letter case: RQ1 changed;
  - a nested sub-bullet copied with its question: silent;
  - German record title beside an English proposal: silent;
  - the last of two record headings wins;
  - silent: no review file, no record, empty record, undecodable bytes, a directory at the review's path, and a proposal without an ordered research-question list;
  - the exit code and digest equal those of the same proposal with no review beside it, in both output modes.

  Verify: they fail.
- [x] 2.5 Implement the review reader and the `review-questions-changed` finding, next to `rule_research_questions`:
  - the record titles as one module constant;
  - the review path behind exactly one function, holding a temporary `-review.md` literal until the rebase onto #7 swaps it to #7's family vocabulary (task 7.1; design D12); no other `-review.md` literal in `check.py`;
  - the read wrapped so that `OSError` and `UnicodeDecodeError` both mean "no finding";
  - the positional diff and the message from design D4;
  - wired into `check_findings` after the rule loop;
  - the identifier added to `RULE_IDS`, in a hunk apart from #7's `# workspace family` group;
  - every text read with `encoding="utf-8"`; `utf8_output()` stays the first statement of `main()`.

  Verify:
  - 2.4 green;
  - `uv run ruff check .` clean, within `max-complexity = 12` without an exemption;
  - `tests/unit/test_repo_conventions.py` and `tests/unit/test_utf8_output.py` green.
- [x] 2.6 Run `python3 scripts/sync_shared.py`; the files it lists are staged at landing. Verify: `python3 scripts/sync_shared.py --check` clean.
- [x] 2.7 (review) The record ends where its first list ends (design D3). Red tests first, each against a record that matches the proposal: a notes paragraph followed by bullets after the record, and `---` then `* * *` after it, all silent; a loose record list (blank line between items) still read whole. Then end the record at the next heading, at a thematic break (tested before the list marker), or at the first line after a blank line that is neither a list item nor indented, and let `without_rq_record` cut the same span. Verify: the new tests green, every existing record and harness-helper test unchanged and green.
- [x] 2.8 (review) `question_changes` returns (position, kind) pairs. The `RQ<n> <kind>` text is formatted only in the finding, and `verdict_review_records_questions` maps the kind without parsing text (design D4). Red test first: `question_changes` returns pairs. Verify: green, and the record verdict's L0 tests unchanged and green.
- [x] 2.9 (review) The warning's message closes on "a fresh review replaces it, so leave the review file as it is" (design D4). Red test first on the message. Verify: green; w16's oracle still passes.
- [x] 2.10 (review) An L0 test stages `My Proposal.md` beside `My Proposal-review.md` with a stale record, and the warning fires (design D10, D12). It guards the rebase (7.1), so it is green on today's `review_path`.
- [x] 2.11 (maintainer decision on the review) `normalize_question` removes every Unicode format character (general category Cf: soft hyphen U+00AD, zero-width space U+200B, word joiner U+2060, U+FEFF, among others) before NFKC, the whitespace collapse and the fold (design D3). Red tests first in `tests/unit/test_review_currency.py`: the normalizer drops each of the four inside a word and between two spaces without leaving a double space, and a record differing from the proposal only by a soft hyphen in one question and a zero-width space in another is silent; the latter warns before the change. Then run `python3 scripts/sync_shared.py`. Verify:
  - the new tests green, every existing normalization and comparison test unchanged and green;
  - the record verdict's L0 tests in `test_readiness_verdicts.py` unchanged and green, since it reuses the same normalizer;
  - `python3 scripts/sync_shared.py --check` clean.

## 3. Fixtures

- [x] 3.1 Create `tests/fixtures/w16-superseded-record/` (design D9):
  - `ci-repair-agent-configurations.md` and `ci-repair-agent-configurations.notes.md`, each byte-identical to w10's;
  - `ci-repair-agent-configurations-review.md`: w10's review, byte for byte, plus a closing `## Research questions reviewed` that lists f28's RQ1–RQ3 verbatim and RQ4 exactly as w10's review quotes it;
  - `expected.json`: exit 0, no errors, `warnings_contain: ["RQ4 removed"]`, `rules.warnings: ["review-questions-changed"]`, and w10's `semantic` list plus the warning.

  Verify: `uv run pytest tests/unit/test_fixture_oracles.py -k w16` green; `cmp` of the proposal and notes file against w10's identical; the review differs from w10's only by the appended section.
- [x] 3.2 Append a matching `## Research questions reviewed` record of f28's three questions, verbatim, to `tests/fixtures/w12-ready-current/ci-repair-agent-configurations-review.md`. Verify: the w12 oracle passes unchanged, and `cmp` of w12's proposal against f28's is still identical.
- [x] 3.3 Document w16 in `tests/fixtures/README.md` as the record half of a minimal pair with w10, its entry directly below w10's line, and say there that w12's review closes on a matching record and is the passing fixture. Leave w12's line untouched, since #7 inserts w13–w15 after it (design, "Coordination"). Verify: `rg -n "w16-superseded-record" tests/fixtures/README.md` finds the entry on the line after w10's; `git diff tests/fixtures/README.md` shows no change to w12's line.

## 4. Skill prose

- [x] 4.1 `skills/proposal-review/SKILL.md`, Output:
  - reword the grammar bullet from "End — …" to "After the three sections — …";
  - add a closing bullet for the record: both titles in backticks, an ordered list of the items of the proposal's numbered research-question list, each copied verbatim in its order and nothing else (no overarching question stated in prose, a nested item kept inside its question), no record when that section numbers none, exactly one record when overwriting, never mentioned in the chat summary.

  Pin the verbatim sentence in `tests/unit/data/pinned_sentences/proposal-review--rq-record.txt`. Verify: `uv run pytest tests/unit/test_pinned_sentences.py` green.
- [x] 4.2 Add the drift test: every title in `check.py`'s record-title constant appears as `` `## <title>` `` inside the record bullet of `skills/proposal-review/SKILL.md`'s `## Output` section, and a failure names the missing title. Verify: green, then red against a temporarily renamed title, then reverted.
- [x] 4.3 `skills/proposal-check/SKILL.md`, status-read paragraph: add one clause. Any `review-questions-changed` warning means the review judged other research questions and is superseded, whatever the size of the difference, and counts as superseded in the routes below; it never names the step, since errors still route to a writing pass first (design D6). Pin it as `tests/unit/data/pinned_sentences/proposal-check--review-currency.txt`. Verify:
  - `uv run pytest tests/unit/test_pinned_sentences.py` green with the new pin;
  - `proposal-check--status-read-only.txt` still matches;
  - `test_handoff_block.py` green (the shared block untouched).
- [x] 4.4 Body sizes and opening structure. Verify: `uv run pytest tests/unit/test_skill_frontmatter.py tests/unit/test_skill_header_pattern.py tests/unit/test_execution_shape.py tests/unit/test_report_offer.py tests/unit/test_handoff_block.py` green; the frontmatter file holds the median body-size cap.
- [x] 4.5 (review) Extend `proposal-review--rq-record.txt` to the whole record clause, from "an ordered list of the items …" through "… exactly one when you overwrite an earlier review.", so the overarching-question and nested-item rule is pinned too. Verify: `uv run pytest tests/unit/test_pinned_sentences.py` green.

## 5. Harness

- [x] 5.1 Write the red L0 tests in `tests/unit/test_harness_helpers.py` for the review-shape verdicts (design D10):
  - a review with bulleted findings and a numbered record fails `verdict_review` with "review not enumerated";
  - an English review closing on f04's German record fails `verdict_review_localized` as not German;
  - a review whose only "delta"/"title" mention sits in its record gains nothing in `verdict_hollow_review` and `verdict_title_alarm`.

  Verify: they fail.
- [x] 5.2 Implement `without_rq_record(review)` in `harness/l1_checks.py`, beside the review verdicts, over `CHECK_SCRIPT`'s record-title constant and section finder, and apply it before `is_enumerated_review` (in `verdict_review` and `verdict_title_alarm`), before the German-signal count, and before the whole-text keyword scans. Verify:
  - 5.1 green, and every existing test in `test_harness_helpers.py` and `test_readiness_verdicts.py` unchanged and green;
  - if a verdict docstring changed, `uv run python harness/eval_export.py` regenerated the projection and `--check` is clean.
- [x] 5.3 Write the red L0 tests in `tests/unit/test_readiness_verdicts.py` for `verdict_review_records_questions`:
  - passes on f28 with a verbatim record (EN title) and with the German title;
  - passes on f04 with its four numbered sub-questions;
  - fails, naming the cause, when the proposal changed, the review is missing, the record is missing, RQ2 is paraphrased, a question is dropped, or f04's overarching prose question is recorded as an extra item.

  Verify: they fail.
- [x] 5.4 Implement the verdict in `harness/l1_checks.py`, beside the related review verdicts, through `CHECK_SCRIPT`'s extractor and normalizer (design D10). Verify:
  - 5.3 green;
  - `test_every_verdict_has_an_l0_test` green.
- [x] 5.5 Add the dev-runner scenario `review_record` in `harness/claude_runner.py` (f28, `READINESS_REVIEW_REQUEST`, `proposal-review`), its `SCENARIOS` entry next to the other `proposal-review` scenarios. Map it in `REVIEW_VERDICTS`, and document it in `harness/README.md` next to `review_converge`. Add no Inspect task. Verify:
  - `uv run python harness/claude_runner.py --help` lists it;
  - `tests/unit/test_handoff_runner.py` and `test_eval_wiring.py` green and unchanged.
- [x] 5.6 (review) One `review_with_record(review, questions, title=…, marker=…)` and one `f04_numbered_questions()` in `tests/helpers.py`, beside `fixture_proposal`. `test_review_currency.py`, `test_harness_helpers.py` and `test_readiness_verdicts.py` use them and drop their local copies. Verify: the three files green; f04's shape is asserted once, in `test_readiness_verdicts.py`, so `test_harness_helpers.py` loses its duplicate.

## 6. Verification

- [x] 6.1 After the review tasks (2.7–2.11, 3.3, 4.3, 4.5, 5.6), verify: `uv run poe test`, `uv run poe specs` and `uv run poe cov` green; `python3 scripts/sync_shared.py --check` clean; `openspec validate mark-review-currency --strict` valid.
- [x] 6.2 From inside each of `tests/fixtures/w16-superseded-record/`, `w10-narrowed-scope/` and `w12-ready-current/`, run the script by its absolute path, as `test_fixture_oracles.py` does: `python3 <worktree>/skills/proposal-check/scripts/check.py ci-repair-agent-configurations.md`. Verify: exactly one `WARNING` naming RQ4 for w16, none about the review for w10 and w12, exit 0 for all three.
- [x] 6.3 At the maintainer's go only: `uv run poe dev review_record --model sonnet --isolated`, on the subscription, plan quota, $0. Record the verdict in this file. A failure is first triaged as a defect in the verdict or the runner versus in the skill prose, before any reword.
  - **Result 2026-10-14 (run once, with `--keep`):** L1 **PASS**, "record lists the proposal's 3 research questions verbatim". Requested `sonnet`, served `claude-sonnet-5-5`, CLI 2.1.296, `config: isolated`, `login: harness`, no billing signal; 7 turns, 66 s, notional $0.23. Advisory: `single_context` PASS (no helper), `handoff` PASS (50 words). The review (`ci-repair-agent-configurations-review.md`, the only file added; the proposal unchanged) opens "Verdict: ready" and closes on `## Research questions reviewed` with RQ1–RQ3 verbatim and in order; `check.py` over the kept workspace prints no `ERROR` or `WARNING`, so no `review-questions-changed`. Kept workspace: `/tmp/devrun-review_record-0lvqj7_k` (stream in `.devrun-events.jsonl`).
  - The run predates task 2.11 and is not repeated: removing format characters can only make two questions equal that differed before, never the reverse, so a record the verdict passed still passes.

## 7. Landing (after #7 has landed on `main`)

- [x] 7.1 Rebase onto `main` after #7. Then, before archiving:
  - Read `openspec/specs/skill-review/spec.md`: if #7 MODIFIED "Grammar hint, never a list", fold its wording into this change's MODIFIED block.
  - Read `openspec/specs/skill-check/spec.md`, requirement "Orphaned companions reported as a warning": confirm its read-only sentence is still scoped to its own finding ("For this finding, the check SHALL open another file only to tell a proposal from a companion…"). If it is stated of the check as a whole, stop and raise it with the maintainer.
  - Confirm `openspec/specs/proposal-file-format/spec.md` holds "Proposal family under one handle", which the skill-check delta references; if #7 named it otherwise, update the reference.
  - Confirm #7 created no w16; w16 stays this change's fixture.
  - Swap the review-path function in `check.py` to #7's family vocabulary: build the name from the `review` entry of #7's role table (`COMPANION_SUFFIXES` in #7's draft), as `proposal.with_name(proposal.stem + suffix + ".md")`, instead of the temporary literal. Never classify through `family_member` or its shape test, which return nothing for a stem that is not kebab-case (design D12).
  - Re-run `python3 scripts/sync_shared.py`; the vendored copies carry `merge=ours`.
  - Re-run the trial merge of `tests/fixtures/README.md` against #7's landed entries (design, "Coordination").

  Verify:
  - `rg -n -- '-review\.md' skills/proposal-check/scripts/check.py` finds no literal;
  - the `My Proposal.md` test (2.10) still green;
  - `uv run poe test`, `uv run poe specs` and `uv run poe cov` green; `python3 scripts/sync_shared.py --check` clean;
  - the body-size cap still holds after #7's block (task 4.4's tests).
  - **Result 2026-10-14:** rebased onto #7's commit `b5d24b5` on branch `tighten-proposal-family`, not yet on `main` and not yet archived, so the three spec reads were made against #7's change deltas. The rebase met no textual conflict; `merge=ours` kept #7's side of the five vendored `check.py` copies, and `python3 scripts/sync_shared.py` regenerated them.
    - skill-review: #7 has no skill-review delta, `openspec/specs/skill-review/spec.md` is unchanged since `2f1fa0d`, and the MODIFIED "Grammar hint, never a list" block still copies its text (one scenario) with only this change's edits.
    - skill-check: #7's "Orphaned companions reported as a warning" still reads "For this finding, the check SHALL open another file only to tell a proposal from a companion, and SHALL change nothing."
    - proposal-file-format: #7 adds "Proposal family under one handle" under that name, so the skill-check delta's reference stands. #7 created w13–w15 only; w16 stays here.
    - `review_path()` now takes the suffix of the `REVIEW` entry of `COMPANION_SUFFIXES` and applies it to the stem whatever its shape; a new L0 test (`test_the_review_path_follows_the_family_role_table`) failed against the literal and passes now. The `rg` finds no `-review.md` literal in `check.py`; the `My Proposal.md` test is green.
    - `tests/fixtures/README.md`: w16 sits on the line after w10, w13–w15 after w12, and w12's line is untouched.
    - Task 6.2 repeated from inside each fixture: w16 exit 0 with exactly one `WARNING`, naming RQ4 removed; w10 and w12 exit 0 with no warning. The w10, w12 and w16 oracles pass.
    - Body sizes (words after the frontmatter): median 3,172 (reverse), ceiling 6,344; largest supervise 5,215 (82 %), ideate 4,819, write 4,111, review 3,494, check 2,636; every body under 500 lines.
    - Gates: `uv run poe test` 4954 passed, 3 skipped; `uv run poe specs` 21 passed; `uv run poe cov` 94.67 %; `python3 scripts/sync_shared.py --check` clean; both changes valid under `--strict`.
- [ ] 7.2 Archive with `openspec archive mark-review-currency` in the same commit as the implementation. Verify: `uv run poe specs` green after the archive.
