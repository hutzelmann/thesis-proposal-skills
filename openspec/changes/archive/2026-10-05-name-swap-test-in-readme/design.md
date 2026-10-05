# Design

## Context

`tests/unit/test_substance_tests.py` parses the set from the guidance's Substance Tests section (`delta`, `falsifiability`, `swap`, `necessity`, `method-fit`, `executability`) and checks two things on each site: every comma-joined run holding at least two canonical names holds exactly the set, and every number word in a set claim (`six named tests`, `Six tests define the substance bar`) matches its size. Its sites were the guidance, the `SKILL.md` bodies, the pinned sentences and, with no change in flight, the main specs. `README.md` carries both constructs in one sentence — "six named tests (delta, falsifiability, anti-generic, …)" — and was not scanned.

## Goals / Non-Goals

**Goals:** the README uses the canonical name, and the guard fails if its enumeration or count drifts again.

**Non-Goals:** scanning `docs/` or `harness/`. A search found no enumeration or count of the set there (`harness/rubrics/density.txt` says "the swap test" for the density judge's own criterion, which is a single name, not the set), so adding them would widen the scanned text with nothing to guard.

## Decisions

**Add `README.md` as a plain site, not a special case.** Both checks already apply to it as written: the run check treats "anti-generic" as an unknown word in a run of five canonical names and reports the missing `swap`, and the count check reads "six named tests". A dry run with the README added and still unfixed failed exactly one test, `test_enumerations_name_the_whole_set[README.md]`, so the README produces no other match — no false positive to exclude.

- *Alternative: a dedicated README test with a literal expected sentence.* Rejected — a literal would be a second place the set is decided, which the module docstring rules out for the same reason the set is parsed rather than restated.

**`skip_specs: true`.** The testing-harness requirement "Substance-test names consistent across guidance, skills, specs and pins" requires consistency wherever the guidance's tests are referred to by name or by count; the README is such a place. Fixing it and guarding it meets a requirement that stands unchanged.

## Risks / Trade-offs

- [The README is long and prose-heavy, so a future comma list could hold two canonical words by accident, e.g. "delta" and "necessity" in an unrelated sentence] → the run must hold at least two of the names to be read as an enumeration, the same threshold the skill bodies have lived with; a false positive would fail loudly with the run quoted, and `at least` marks a deliberate subset.
