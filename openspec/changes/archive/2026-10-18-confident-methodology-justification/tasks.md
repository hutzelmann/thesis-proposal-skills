# Tasks

## 1. Fixture openings (before any verdict reads them)

- [x] 1.1 Rewrite the methodology opening of the five standalone fixtures — `f23-controlled-experiment`, `f24-model-evaluation`, `f25-case-study`, `f27-citation-runs`, `w04-methodology-branch` — to the design D2 shape, each from what its own research questions demand: no suitability verdict, no restated branch definition, no feasibility reason, no methods not taken; prose before the first methodology subsection only. Verify with `/usr/bin/git diff --stat`: only those lines changed.
- [x] 1.2 Rewrite the shared `ci-repair-agent-configurations` opening once and apply the identical text to all twelve copies (`f28`–`f32`, `w09`–`w14`, `w16`). Verify that `/usr/bin/git grep -h -A2 "^## Methodology for Research" -- 'tests/fixtures/*/ci-repair-agent-configurations/ci-repair-agent-configurations.md' | sort -u` shows one opening, and that `/usr/bin/git grep -E "fits (these questions |all three questions )?because|fits because" -- 'tests/fixtures/*/*/*.md'` prints nothing.
- [x] 1.4 (added during apply) Give `f00-clean-en` an opening in the D2 shape: it is `CLEAN_DRAFT`, which the dev-runner and host tests use as a passing write draft. Avoid the check's result verbs (one rewritten opening tripped `hindsight-leakage` with "showed"). Verify through task 1.3.
- [x] 1.3 Run `uv run poe test` and verify it is green with no `expected.json` edited: no check oracle, recorded research question or review currency depends on the opening.

## 2. L1 verdict on write output

- [x] 2.1 Add `verdict_methodology_opening(text) -> tuple[bool, str]` to `harness/l1_checks.py` per design D5/D6: methodology section located through `CHECK_SCRIPT` parsing and the `structure.json` title templates in both languages; fail on empty prose before the first subsection, or on a sentence (split by `CHECK_SCRIPT.split_sentences()`) that names the methodology and carries an English or German suitability frame; a draft with no methodology section is left to the check's own `methodology-missing` error. Verify that `uv run ruff check harness/l1_checks.py` passes within `max-complexity = 12`.
- [x] 2.2 Add L0 tests in `tests/unit/test_harness_helpers.py` (or a new `tests/unit/test_methodology_opening.py`, importing through `conftest.py`): EN frame fails, DE frame ("Eine Fallstudie eignet sich, weil …") fails, missing opening fails, a workspace branch title (`Action Research`) is recognized, "the model fits the data" in a sentence not naming the methodology passes, a D2-shaped opening passes, and every tracked fixture opening passes (the "Fixtures model the target" scenario). Verify with `uv run pytest` on the new tests: green, and `tests/unit/test_repo_conventions.py` finds the new verdict tested.
- [x] 2.3 Call `verdict_methodology_opening()` from `verdict_draft()` after the check-errors condition and extend its docstring by the opening condition. Verify that `uv run pytest tests/unit/test_harness_helpers.py tests/unit/test_citation_practice.py` passes: the existing draft, cited-draft and repaired-draft tests still hold with the rewritten `f27`.
- [x] 2.4 Regenerate the projection with `uv run python harness/eval_export.py` and verify that `uv run python harness/eval_export.py --check` exits 0 and only `skills/proposal-write/evals/evals.json` changed.
- [x] 2.5 Document the condition in `harness/README.md` beside the `write_from_seed` / `write_rich_seed` / `write_repair_citations` entries: what fails, that the lexical half alone is checked and the semantic half is review judgement. Verify by reading the rendered section.
- [x] 2.6 Reproduce the defect before the guidance changes: `uv run poe dev write_from_seed --isolated --keep --model sonnet` (subscription, $0). Expected: L1 fails, its explanation naming the methodology opening. Record the result and the drafted opening (synthetic seed, safe to quote) in this change's design under a short "Measurements" heading. If it passes, record that too; the guidance change still stands on the contradiction it removes.

## 3. Guidance and review

- [x] 3.1 In `shared/guidelines/guidelines.md` "Methodology Content", replace the justification paragraph with the D2 rule: the demand and what the methodology does to meet it, in the questions' terms; the four exclusions with the short quoted frames; the classification (missing or verdict-shaped opening = refinement, a justification that does not hold = method-fit); the one synthetic positive example. Keep "A section that starts at its first subsection has skipped its own justification." Verify that the new paragraph contains no full defensive sentence.
- [x] 3.2 In "Degree Level", replace "Neither level requires a statement justifying the methodology choice: … not written as defense." with the same-at-both-levels sentence (design D4). Verify that `/usr/bin/git grep -n -i "neither level requires a statement" -- shared skills` prints nothing.
- [x] 3.3 In `skills/proposal-review/SKILL.md` "Level fit", replace "Methodology fit is judged, never demanded as justification prose: …" with the method-fit judgement of the opening justification and the plan behind it, the same at both levels, keeping the Master's-level limits question. Pin the new sentence as `tests/unit/data/pinned_sentences/proposal-review--methodology-opening.txt`. Verify with `uv run pytest tests/unit/test_pinned_sentences.py tests/unit/test_skill_header_pattern.py`: green.
- [x] 3.4 Run `python3 scripts/sync_shared.py`; the files it lists are staged with the change's commit. Verify that `python3 scripts/sync_shared.py --check` exits 0.
- [x] 3.5 Run the repo-wide wording check `/usr/bin/git grep -n -i -E "justification (prose|statement)|justifying the methodology|never demanded as" -- ':!openspec/changes/archive' ':!openspec/changes/confident-methodology-justification'`. Verify that only `openspec/specs/` lines remain, which the archive replaces.

## 4. Integration

- [x] 4.1 Run `uv run poe test`, `uv run poe cov` and `uv run poe specs`. Verify all three are green: no generated-copy drift, coverage at or above the floor, OpenSpec strict validation clean with the shortened MODIFIED requirements within their recorded lengths.
- [x] 4.2 Re-run `uv run poe dev write_from_seed --isolated --keep --model sonnet` after the guidance edit. Expected: L1 passes and the opening states demand and capability. Then run once on `--model haiku`. Verify by recording both L1 explanations and openings under "Measurements" in design.md and checking that neither draft reuses the guidelines' example sentence.
- [x] 4.3 Run `uv run poe dev review_fixture --isolated --model sonnet` (f05 has no opening). Verify that the review names the missing opening as a refinement at most and that no blocker cites it.

## Workflow follow-up

- Archive with the OpenSpec archive workflow after review; copy the `Changelog:` line under `## [Unreleased]` → Changed, then `python3 scripts/changelog.py check`.
- After archive, run `python3 scripts/validate_specs.py --update-baseline` so `openspec/long-requirements.json` records the shortened "Degree-level guidance" and "Degree-level review lenses".
- Commit on `develop` as one commit for the completed change.
- The next gated `poe matrix` run re-measures the three write tasks under the new L1 condition; nothing is re-labelled before then.
