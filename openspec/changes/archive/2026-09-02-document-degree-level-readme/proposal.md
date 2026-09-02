# Document degree-level tailoring in the README

## Why

`2026-09-02-add-degree-level-tailoring` made five skills grade their expectations by the degree level the subtitle states, on the evidence recorded by `2026-09-01-document-degree-level-sources` — and the README, the page a student lands on from skills.sh and the page a supervisor reads before recommending the skills, still says nothing about it beyond "Bachelor's or Master's" in its first line. The feature is invisible to exactly the readers it was built for, and the "For supervisors" section still states the contribution expectation as a single unconditional bar.

## What Changes

- README.md gains coverage of the degree-level feature, in the README's own register and placed where its readers would look: the level is read from the subtitle only, four expectations grade with it (contribution close, research-question origin, literature stance, scope for the months), the bar runs in both directions, and structure and checks stay level-blind by design.
- "For supervisors" links `docs/degree-level-sources.md` the way it already links `docs/methodology-sources.md`, and its "explicit contribution over the state of the art" clause is reconciled with the graded expectation.
- No skill, script, shared content, fixture, or spec changes. The README's model-support marker block, install command, session excerpts, and divergence table are untouched.

## Capabilities

### New Capabilities

None — documentation only.

### Modified Capabilities

None. No spec-level behavior changes; `skip_specs: true` is set in `.openspec.yaml`.

## Impact

- `README.md` only.
- `tests/unit/test_install_check.py` reads the README's install command and `harness/support.py` its model-support marker pair; both regions stay untouched, so no test or generated copy is affected.
