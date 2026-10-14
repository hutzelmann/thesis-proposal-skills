## Why

A review describes the text it judged. Today nothing on disk says which text that was. `<slug>-review.md` keeps its verdict and findings after the student narrows the scope or rewrites a research question, and only an agent's reading at a stopping point notices that the review is out of date. The check's status read and the writing skill's handoff both make that judgement from the review's quotes. A student who opens the folder, a writing pass asked to "apply the review", or a later session sees a review that looks current. The layout prompt behind this change asked to "distinguish current artifacts from historical or superseded ones, particularly reviews that no longer apply after a scope change". The maintainer chose to build that now as a small change rather than leave it in the backlog.

The research questions are the part of a review's subject that can be compared mechanically. The proposal already declares them as an ordered list that `check.py` parses. A review that records them verbatim lets the check say, deterministically and without judging substance, that the questions have changed since the review was written.

## What Changes

- **The review records what it judged.** `proposal-review` closes `<slug>-review.md` with a section `## Research questions reviewed` (German: `## Begutachtete Forschungsfragen`). It holds the items of the proposal's numbered research-question list, copied verbatim and nothing else: an overarching question the section states in prose stays out, and a nested item stays inside its question. The section is plain, visible markdown at the end of the file, after the findings and the grammar hint, so a student can read it, edit around it, or delete it. It needs no front matter, no hidden comment and no YAML.
- **`check.py` warns when the questions changed.** The script reads the proposal's review file. If the review carries the record, the script compares it with the proposal's current ordered-list research questions, after removing invisible format characters such as soft hyphens, normalizing Unicode compatibility forms, collapsing whitespace, and folding the typographic variants of single quotes, double quotes and dashes to one form each. Letter case and wording still count. On a mismatch it reports one warning, `review-questions-changed`. The warning names which positions changed, were added or were removed, never quotes a question, says that the review may describe an earlier version, and says that a fresh review replaces it while the review file is left as it is. It is a warning, never an error, and it does not change the exit code or the digest. A review without a record, including every review written before this change, gives no finding, and so does a review the script cannot read.
- **The status read uses it.** When the user asks where the proposal stands, the check skill takes the warning as settling the research-question part of its existing currency judgement: any `review-questions-changed` warning means the review is superseded, and the existing routes treat it so: a fresh review once no mechanical error or open decision comes first. This is what the shared handoff block and the writing skill's route already say about changed research questions, so neither changes.
- **Coverage.** A new fixture `w16-superseded-record` holds w10's proposal, notes file and review, byte for byte, plus a record of the broader predecessor, and the check warns. `w10-narrowed-scope` stays unmarked, and the check stays silent, so the pair differs only in the record. `w12-ready-current`'s review gains a matching record, and the check stays silent. L0 tests cover extraction and normalization. A drift test ties the two titles to the review SKILL.md. One pure verdict function and one subscription dev-runner scenario check that a review writes the record verbatim.
- **Shipped review verdicts keep their meaning.** The record is a numbered list and can hold German function words, so the L1 gates that judge a review's own shape (findings enumerated, review written in German, keyword scans of the hollow and title-alarm verdicts) judge the review without it. Without this, they would quietly accept reviews they reject today.
- **Adjacent fix.** `research-questions-too-many` is emitted by `check.py` but missing from its closed `RULE_IDS` set. That breaks the existing requirement "Findings carry stable identifiers". It is declared and unit-tested here, because this change refactors the same function (maintainer decision Q7).
- **Unchanged:**
  - `proposal-write`. Its route already treats a pass that changed the research questions as superseding the review, and its scenario "Blockers applied" already leaves the review file unchanged. A guard before applying a review was considered and dropped (maintainer decision Q3).
  - `proposal-supervise`. Its feedback letter never carries the record, and its professor-side review gets none (maintainer decision Q2).
  - The shared stage-handoff block, the proposal file format, every existing finding's wording, exit codes and the digest.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-review`:
  - ADDED "Research questions recorded in the review".
  - MODIFIED "Grammar hint, never a list": the hint closes the findings rather than the file, so the record can follow it.
- `skill-check`: ADDED "Review currency warning", covering both the script's warning and how the status read uses it.
- `testing-harness`: ADDED "Review-currency coverage", including the record-free reading of the review-shape verdicts.

No requirement owned by `desktop-first-install`, `utf8-script-output` (#6) or the stage-handoff block (skill-packaging) is touched. This change modifies one requirement, the small `skill-review` "Grammar hint, never a list"; neither #6 nor `tighten-proposal-family` (#7) touches skill-review in its current draft. #7's draft scopes the read-only sentence of its added skill-check requirement to its own finding, so this change's review read stays allowed (design, "Coordination").

## Impact

- `skills/proposal-check/scripts/check.py`: a shared ordered-item extractor for the research-question count rule and the record; the review reader and comparison; one rule identifier (plus the missing `research-questions-too-many`). The review's path sits behind one function, with a temporary `-review.md` literal until the rebase onto #7 swaps it to #7's family vocabulary. It is regenerated into the five vendored copies (import, reverse, supervise, troubleshoot, write) by `scripts/sync_shared.py`.
- `skills/proposal-review/SKILL.md`: one Output bullet for the record, and the grammar bullet reworded to "after the three sections".
- `skills/proposal-check/SKILL.md`: one clause in the status-read paragraph.
- Pins: `tests/unit/data/pinned_sentences/proposal-review--rq-record.txt` and `proposal-check--review-currency.txt`.
- Tests: `tests/unit/test_check_rules.py` (or a new `tests/unit/test_review_currency.py`), `tests/unit/test_readiness_verdicts.py`, `tests/unit/test_harness_helpers.py`, `tests/unit/test_fixture_oracles.py` (unchanged, picks up w16).
- Fixtures: new `tests/fixtures/w16-superseded-record/` (#7 owns w13–w15); `tests/fixtures/w12-ready-current/ci-repair-agent-configurations-review.md` gains the record; `tests/fixtures/README.md`.
- Harness: `harness/l1_checks.py` (a record-stripping helper used by the review-shape verdicts, and `verdict_review_records_questions`), `harness/claude_runner.py` (scenario `review_record`), `harness/README.md`; the skills' `evals/evals.json` projection if a verdict docstring changes.
- No model call is needed to land it. The dev-runner scenario runs on the subscription, on the maintainer's go. No Inspect task is added and no matrix cell is re-run.
