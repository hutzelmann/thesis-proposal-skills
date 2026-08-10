## 1. Merge and validate

- [x] 1.1 Add a merge in `check.py` that applies a workspace `methodologies` table over the shipped set: matching id replaces, new id adds, `enabled = false` drops.
- [x] 1.2 Validate each declared branch — title in both languages, at least one subsection, each subsection with both titles and a non-empty `guidance` — and report a configuration error per invalid branch without dropping the rest of the run.
- [x] 1.3 Reject unknown keys inside a branch, matching how unknown override keys are handled elsewhere.
- [x] 1.4 Add the new rule identifier to the closed set and to the unit-test coverage set.
- [x] 1.5 Carry the merged set on the check context so every methodology rule reads one value.

## 2. Wire the rules

- [x] 2.1 `rule_methodology` uses the merged set for the accepted names, the subsection requirements, and the unknown-methodology message.
- [x] 2.2 Confirm the single-methodology and multiple-section rules are untouched by the merge.

## 3. Documentation

- [x] 3.1 Document the branch declaration format and its merge semantics in `skills/proposal-customize/SKILL.md`, including `enabled = false` and the refusal to invent guidance.
- [x] 3.2 State in `shared/guidelines/guidelines.md` that the shipped set is a default a workspace may replace, and that the closure itself is not negotiable.
- [x] 3.3 Tell `skills/proposal-write/SKILL.md` to take the set and the per-subsection guidance from the merged data.

## 4. Fixture

- [x] 4.1 Add `w04-methodology-branch`: a workspace `guidelines.md` declaring one branch with guidance, and a proposal using it.
- [x] 4.2 Calibrate its `expected.json` against the check script.
- [x] 4.3 Document it in `tests/fixtures/README.md`.

## 5. Tests

- [x] 5.1 L0: a proposal using a workspace branch passes; omitting one of its subsections reports that subsection.
- [x] 5.2 L0: a disabled shipped branch becomes an unknown methodology, and the message lists the remaining set.
- [x] 5.3 L0: a branch without per-subsection guidance is a configuration error and is not applied.
- [x] 5.4 L0: a branch with an unknown key is reported.
- [x] 5.5 L0: a workspace declaring nothing still gets the shipped four.

## 6. Verify

- [x] 6.1 `python3 scripts/sync_shared.py`.
- [x] 6.2 `uv run poe test` green.
- [x] 6.3 `uv run poe cov` holds the floor.
- [x] 6.4 `openspec validate --all --strict` green.
