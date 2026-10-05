# Name the swap test in the README and guard the README's enumeration

## Why

README.md lists the review skill's six substance tests as "(delta, falsifiability, anti-generic, necessity, method-fit, executability)". The guidance, `shared/guidelines/guidelines.md`, names the third one the **Swap test**, and so does every skill body and spec that cites it — a review verdict is required to cite the tests by name. The README is the first page a student or supervisor reads, so it should use the names the reviews they get back will use. The drift guard in `tests/unit/test_substance_tests.py` did not catch it because the README was not one of its sites (`2026-10-05-fix-substance-test-count` recorded this as a non-goal).

## What Changes

- `README.md`: "anti-generic" becomes "swap" in the substance-test enumeration. A search of `README.md`, `docs/`, the `SKILL.md` bodies and `harness/` found no other mention of the test under that name outside archived changes.
- `tests/unit/test_substance_tests.py`: `README.md` joins the guard's sites, so its enumeration and its count ("six named tests") are checked against the guidance like the skill bodies, pins and specs.

## Capabilities

### New Capabilities

(none — `skip_specs: true`)

### Modified Capabilities

(none — the testing-harness requirement "Substance-test names consistent across guidance, skills, specs and pins" requires the set to be cited consistently wherever the guidance's tests are referred to by name or by count; this change fixes one such site and widens the guard to it, under a requirement that stands unchanged)

## Impact

- `README.md` (one word), `tests/unit/test_substance_tests.py` (one site and its docstring).
- No skill text, no scripts, no harness runtime, no spec text.
