# Fix the substance-test count in the guidance and widen its guard

## Why

`shared/guidelines/guidelines.md` opens its Substance Tests section with "Five tests define the substance bar" and then lists six (Delta, Falsifiability, Swap, Necessity, Method-fit, Executability). The guidance is the single source the skills cite the tests from, and every generated `references/guidelines.md` copy ships the same wrong count to users. The guidance-model spec already requires six tests, and the testing-harness requirement "Substance-test names consistent across guidance, skills, specs and pins" already requires a count that disagrees with the set to fail the offline suite. It did not fail, because the count pattern in `tests/unit/test_substance_tests.py` only recognises `<N> substance tests` and `<N> named tests`, so the one count sentence in the source itself was invisible to the guard that exists to catch exactly this.

## What Changes

- `shared/guidelines/guidelines.md`: "Five tests define the substance bar" becomes "Six tests define the substance bar"; the generated `skills/*/references/guidelines.md` copies are re-materialized with `python3 scripts/sync_shared.py`. No other prose states the count wrongly: the guidance has no German counterpart of this sentence, and every other count site (skill bodies, pins, specs, README) already says six.
- `tests/unit/test_substance_tests.py`: the count pattern also recognises a number word followed by `tests` when the same clause goes on to mention the substance bar (`Five tests define the substance bar`), still excluding evidence bars introduced by `at least` or `only` and plain mentions such as "Naming those three tests is a statement about this fixture". A small table-driven test pins which phrasings the pattern treats as a set claim and which it leaves alone, so a later narrowing is visible too.

## Capabilities

### New Capabilities

(none — `skip_specs: true`)

### Modified Capabilities

(none — the guidance-model spec already requires six named substance tests, and the testing-harness spec already requires a disagreeing count to fail the offline suite; this change makes the shipped text and the guard meet requirements that stand unchanged)

## Impact

- `shared/guidelines/guidelines.md` (one word) and its five generated copies under `skills/*/references/guidelines.md`.
- `tests/unit/test_substance_tests.py` (count pattern plus a pattern test).
- No scripts, no harness runtime, no spec text.
