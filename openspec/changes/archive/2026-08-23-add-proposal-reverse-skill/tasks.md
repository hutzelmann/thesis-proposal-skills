## 1. Check rule first

- [x] 1.1 Add the hindsight-leakage warning to `skills/proposal-check/scripts/check.py`: result verbs with the work as subject and quantitative outcomes stated as findings, firing only on sentences that carry no citation, each finding carrying its line and quoting the matched text. Register its stable id alongside the other warning ids.
- [x] 1.2 Add L0 tests for the rule, including the negative cases the spec names: the same claim attributed to a cited reference, and a planned measurement.
- [x] 1.3 Add the matching verdict function to `harness/l1_checks.py` with its L0 test.
- [x] 1.4 Run `python3 scripts/sync_shared.py` so the existing `check.py` copies pick the rule up.

## 2. Skill scaffold

- [x] 2.1 Create `skills/proposal-reverse/SKILL.md` with frontmatter within the remaining metadata budget (under 400 characters for name and description together) and the four opening blocks in order; leave the three materialized regions to the sync.
- [x] 2.2 Add `skills/proposal-reverse/references` and `skills/proposal-reverse/scripts` as destinations in `SYNC_MAP` for `shared/structure.json`, `skills/proposal-check/scripts/check.py`, `skills/proposal-lit-search/scripts/validate_refs.py` and the modules it imports.
- [x] 2.3 Add the new skill's name to `shared/blocks/workflow.md` in the "Also:" group, then run `python3 scripts/sync_shared.py` to re-materialize all eleven pages.
- [x] 2.4 Pin the mandate in `tests/unit/data/skill_mandates/proposal-reverse.txt`.

## 3. Skill body

- [x] 3.1 Write the reading contract: which parts of the thesis are read, that the rest is left unread and why, what is said about what was read, the no-PDF fallback, and the untrusted-input framing.
- [x] 3.2 Write the harvest step: the record's fields including citation positions, that it is written and offered for inspection before any prose, that it is the source for the write step, and that it is workspace-internal.
- [x] 3.3 Write the four write-step rules — knowledge cut including specifics, scope and validity carried forward, reference survival, mark rather than invent — and the target shape, stating inline the conversion rules a solo install needs and naming `proposal-import` as the fuller source when installed.
- [x] 3.4 Write the reference-shortfall escalation in its three ordered steps, reading the minimum from the configured structure.
- [x] 3.5 Write the bounded-output section: candidate research questions marked as candidates, methodology outside the closed set reported, timeline from the thesis's own months or marked, third-party personal data stripped with survival treated as a defect, the derivation stated once, the check run before reporting, and the review skill named as the next step.
- [x] 3.6 Keep the body above roughly 1400 words and under the line limit — a shorter body lowers the suite median and fails `proposal-ideate` on the size gate.

## 4. Eval wiring

- [x] 4.1 Add a synthetic harvest-record fixture (obviously fake personal data, few kilobytes) carrying the material every write-step rule needs: an execution-residue specific, a pre-settled specific, a delimitation, a limitation, references cited in framing chapters and in results only, and a bibliography thin enough to exercise the shortfall escalation.
- [x] 4.2 Add the L1 task and scorer to `harness/skill_evals.py` as an adapter over the `l1_checks.py` verdicts, and extend `tests/unit/test_eval_wiring.py` for the new scorer name.

## 5. Documentation

- [x] 5.1 Add the skill to the README skill list and anywhere the set is enumerated for users.

## 6. Verify

- [x] 6.1 Run `uv run poe test` — the full offline chain, not `test-fast`: header pattern, mandate pins, report offer, frontmatter budget, body size, and sync drift all gate this change.
- [x] 6.2 Run `uv run poe cov` and confirm the coverage floor still holds.
- [x] 6.3 Run `uv run poe specs`.
