## 1. Gate: substance-test name consistency

- [x] 1.1 Add `tests/unit/test_substance_tests.py` asserting the substance-test set named in `shared/guidelines/guidelines.md` is exactly the set named wherever the tests are referred to by name or count: the SKILL.md bodies of `proposal-write`, `proposal-review`, `proposal-supervise`, `proposal-ideate`; `openspec/specs/guidance-model/spec.md`, `skill-review/spec.md`, `skill-supervise/spec.md`; and the pins under `tests/unit/data/pinned_sentences/`.
- [x] 1.2 Confirm the guard fails on a deliberate mutation — rename one test in one SKILL.md, watch it fail, revert — and record in the task notes which site the failure named.
- [x] 1.3 `uv run poe test` green with the guard in place and the set still at five.

## 2. The necessity test

- [x] 2.1 Add the necessity test to the Substance Tests section of `shared/guidelines/guidelines.md`, placed after the swap test, with the mirror sentence relating the two; add the paragraph stating that a citation does not satisfy it.
- [x] 2.2 Rewrite the Writing Rules line on technical detail irrelevant to the research questions as a cross-reference to the necessity test, so the rule is stated once.
- [x] 2.3 Run `uv run poe test` and confirm task 1's guard now fails, naming every site still enumerating five tests. This failure is the gate working.
- [x] 2.4 Update the dependent sites the guard names: the four SKILL.md bodies, `openspec/specs/guidance-model/spec.md`, `skill-review/spec.md`, `skill-supervise/spec.md`, and the pins `proposal-review--execution-shape.txt` and `proposal-supervise--execution-shape.txt`.
- [x] 2.5 `python3 scripts/sync_shared.py` — `guidelines.md` is a synced source, so the generated `references/guidelines.md` copies must be regenerated, not edited.
- [x] 2.6 `uv run poe test` green: guard passes at six, skill-header and pinned-sentence suites pass.

## 3. Open the reference ratchet

- [x] 3.1 In `skills/proposal-write/SKILL.md`, scope the existing "Never delete a reference, a citation or a sentence to silence a finding" sentence to findings the skill judges wrong, and add the two admissible resolutions for an uncited-reference finding, including the bar on writing a sentence whose purpose is to carry the citation.
- [x] 3.2 Update `tests/unit/data/pinned_sentences/proposal-write--false-positive.txt` if the reword touches the pinned sentence, so the change is visible under review.
- [x] 3.3 In `skills/proposal-lit-search/SKILL.md` step 3, make naming the claim an entry will support a precondition for merging into `references:`; a candidate with no such claim goes to Excluded Literature.
- [x] 3.4 Extend the `reference-uncited` message in `skills/proposal-check/scripts/check.py` to name both resolutions.
- [x] 3.5 `python3 scripts/sync_shared.py` for the vendored `check.py` copies; `uv run poe test` green.

## 4. Fence the scoping profile

- [x] 4.1 In `skills/proposal-ideate/SKILL.md` Scoping section, add the filter-not-a-source paragraph: scoping-only terminology stays out of the seed file, the proposal text, and literature queries unless a student turn voiced it; no reframing to improve apparent fit; the no-idea hint path is the single bounded exception.
- [x] 4.2 Extend the Ending section's seed-file exclusion so it covers terminology traceable only to the scoping lookup, alongside the supervisor's name, the research group, and the study program.
- [x] 4.3 `uv run poe test` green.

## 5. Containment instrument

- [x] 5.1 In `harness/l1_checks.py`, split the scoping vocabulary: keep a visibility set proving the fetch happened, add a containment set of the g01 research vocabulary, each with a comment naming `tests/fixtures/g01-research-group` as its source.
- [x] 5.2 Add `verdict_scoping_containment(transcript, files, queries)` — fails on any containment term absent from every student turn but present in a produced file or an issued query; prefix-stemmed at six characters, per `verdict_provenance`.
- [x] 5.3 Add its L0 test in `tests/unit/`, covering: a clean run, a term leaked to the seed, a term leaked to a query only, and a term the student voiced first (must pass). Required by `tests/unit/test_repo_conventions.py` for every `verdict_*`.
- [x] 5.4 Keep `verdict_ideate_scoped` unchanged and compose the two in the runner, so each failure message stays attributable.

## 6. Scoping scenarios

- [x] 6.1 Add `ideate_scoped_adjacent` to `SCENARIOS` in `harness/claude_runner.py`: same g01 fixture and pre-answered preamble as `ideate_scoped`, student idea orthogonal to all four research areas and plausible for the program.
- [x] 6.2 Add `ideate_scoped_partial`: student idea overlapping exactly one research area.
- [x] 6.3 Wire both into the `verdict()` dispatch, passing the transcript and the tool-call inputs from `routing.tool_calls` as the query source.
- [x] 6.4 Run `uv run poe dev ideate_scoped_adjacent --model haiku` and record the result.
- [x] 6.5 Run the same scenario with `--no-skill` as the negative control. Record both arms. If neither arm leaks, say so in the task notes and do not report the scenario as evidence of containment.
- [x] 6.6 Confirm `ideate_scoped` still passes — the visibility set must still be satisfied by the original scenario.

## 7. Off-topic reference fixture and writing scenario

- [x] 7.1 Add `tests/fixtures/f26-offtopic-reference/` — a synthetic proposal whose `references:` carries one well-formed, academically legitimate, topically adjacent entry that no research question, delta, or method step needs.
- [x] 7.2 Write its `expected.json` oracle, calibrated against `skills/proposal-check/scripts/check.py`: the entry is reported uncited, and nothing is reported about its relevance.
- [x] 7.3 Add a `write_offtopic_reference` dev-runner scenario staging the fixture and requesting a writing pass.
- [x] 7.4 Add the verdict: fail when a new sentence citing the entry appears without a research question, delta, or method step depending on it; pass on removal with a recorded reason, and on leaving it uncited with a stated reason. Add its L0 test.
- [x] 7.5 Run the scenario against the **pre-edit** `proposal-write` wording as the negative control and record whether it fails there. Then run it against the edited skill and record the result.

## 8. Verify and close

- [x] 8.1 `uv run poe test` green, including the drift guard at six tests and every new L0 test.
- [x] 8.2 `python3 scripts/sync_shared.py --check` clean.
- [x] 8.3 `openspec validate --all --strict` clean.
- [x] 8.4 `uv run poe cov` above the floor.
- [x] 8.5 Write the measurement summary into the change folder: for each new scenario, which arms ran, what each reported, and whether a negative control was observed failing. A scenario with no observed failure is reported as unproven, not as a passing guard.
