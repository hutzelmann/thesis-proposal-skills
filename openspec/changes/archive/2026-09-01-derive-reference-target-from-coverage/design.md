# Design

## Context

See proposal.md — Why. Mechanics that shape the approach:

- `rule_length` (`skills/proposal-check/scripts/check.py`) already computes body words (non-blank, non-heading lines of `ctx.body`) and demonstrates the degradation pattern for a bad numeric override (`page-limit-invalid`: report error, fall back to default, never crash or silently disable).
- `rule_min_references` owns the floor error and its own degradation (`min-references-invalid`).
- `RULE_IDS` is a closed set; `tests/unit/test_check_rules.py::test_every_declared_identifier_is_reachable` requires every id to be produced by a fixture oracle or listed in `COVERED_BY_UNIT_TESTS` with real unit coverage.
- Fixture survey (2026-09-01, all 31 proposal fixtures): body words 76–995; every fixture defines at least as many references as `ceil(words × 4 / 1000)` expects (f19: 15 against an expectation of 4), so the advisory never fires in the corpus. No oracle changes.
- `scripts/sync_shared.py` materializes `shared/structure.json` and `shared/guidelines/guidelines.md` into skill `references/` copies and vendors `check.py` where siblings use it.

## Goals / Non-Goals

- Goal: the shipped target is justified by rules the guidance already carries, and the mechanical expectation scales with actual document length.
- Goal: zero behavior change for short drafts and for every shipped fixture.
- Non-Goal: judging source quality or relevance mechanically — that stays with `proposal-review` (formalization boundary).
- Non-Goal: calibrating the constant against the private corpus (see proposal.md — out of scope).

## Decisions

- **Key name `min_per_1000_words`, sibling of `min_count`.** It is a lower bound like `min_count`, and the unit is in the name so a workspace author cannot misread it as a count. Alternative `target_per_1000_words` rejected: the check enforces a lower edge, not a target; the 10–15 *range* stays prose.
- **Default 4, warning fires below `ceil(words × 4 / 1000)`.** 4/1000 is the lower edge of the derived 4–6 range; at the default 2500-word length it reproduces the prose's "ten" exactly. The upper edge stays prose — a check that also warned above 6/1000 would punish well-grounded proposals.
- **Expectation from actual words, not from `page_limit`.** A half-length draft gets a half-size expectation without any override; a program that raises `page_limit` gets the scaled expectation for free. Reuses the exact `rule_length` word count (extracted as a shared helper) so the two estimates can never disagree about what "body words" means.
- **Suppress while the floor error fires.** One defect, one finding: a two-reference proposal gets `min-references` only. Implemented by comparing against the effective floor inside the density rule, not by inter-rule coupling in the runner.
- **`0` disables; invalid degrades.** Mirrors `page_limit` degradation (`error` + default) except that 0 is valid here — "no density expectation" is a legitimate program stance, whereas a zero page limit is nonsense.
- **Comment in `structure.json` marks it an estimation constant** beside `_length_comment`, with its derivation (coverage rules → 10–15 at default length) in one line, so the next reader sees provenance instead of a magic number.
- **Degrade-never-crash is hardened against the values TOML can actually express** (adversarial review findings, 2026-09-01): `isfinite` only sees floats (a huge TOML integer would overflow the conversion), the effective density is capped at one reference per word so a finite-but-absurd `1e308` cannot overflow the ceil, an epsilon round keeps IEEE noise from demanding one reference beyond an exactly-met fractional density, and structured data predating the constant disables the advisory instead of crashing on the missing default. The warning text states the coverage rationale, not an observed norm — the framing this change removes from the prose must not reappear in the finding.

## Risks / Trade-offs

- [Fixtures never reach the new warning, so a regression in it is invisible to the oracle suite] → both ids join `COVERED_BY_UNIT_TESTS` with direct unit tests for fire/suppress/override/disable/degrade; the reachability test keeps that honest.
- [Word-count estimate counts reference-key mentions and TODO markers as words] → acceptable: same tolerance the page estimate already accepts, and the finding says "estimate" by construction (it names words and density).
- [A workspace that raised `min_count` above the density expectation gets floor-only reporting] → intended: the stricter constraint wins, and the suppression rule keeps the report single-voiced.

## Migration Plan

Purely additive: absent key cannot occur in practice (shipped `structure.json` carries the default; old workspace files simply don't override it and keep today's behavior plus the new advisory). No retired keys, no oracle churn. Rollback = revert the change commit.
