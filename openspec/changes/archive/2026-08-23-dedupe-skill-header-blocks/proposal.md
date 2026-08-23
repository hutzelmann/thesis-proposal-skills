## Why

Three blocks are byte-identical across the shipped skills by requirement: the workflow line
(10 copies), the voice block (10 copies), and the failure-path report offer (9 copies).
Twenty-nine copies are maintained by hand and defended by two offline tests that compare the
copies against each other and against literals embedded in the test sources.

That arrangement makes the cheapest correct edit expensive. Rewording the voice block means
editing ten files identically; adding an eleventh skill means editing the workflow line in
ten files before the new one is even written, and the requirement that each page names the
whole set makes that a permanent tax rather than a one-off.

Nothing about the requirement is wrong — every page must name the set, and the offer's
wording is the requirement. What is wrong is that identity is *asserted* twenty-nine times
and *verified* by comparison, when it could be *produced* once. The repository already has
the mechanism: `scripts/sync_shared.py` materializes sixteen file copies from `shared/`
sources and fails CI on drift. These three blocks are the same problem at region granularity
rather than file granularity.

## What Changes

- Add `shared/blocks/workflow.md`, `shared/blocks/voice.md`, and `shared/blocks/report-offer.md`
  as the single source for each block. The workflow source carries a placeholder for the
  containing skill's name; the renderer marks the owning skill.
- Extend `scripts/sync_shared.py` to materialize those three blocks into each `SKILL.md`
  in place, and to report a region that differs from its source as drift under `--check`.
- Anchor the regions by the positions the spec already fixes — the workflow line and voice
  block at their required indices in the opening structure, the offer inside its required
  closing section — rather than by inserted markers. A rendered `SKILL.md` gains no marker,
  comment, or banner: it is byte-for-byte what it is today.
- Move the identity assertions in `tests/unit/test_skill_header_pattern.py` and
  `tests/unit/test_report_offer.py` from literals embedded in the test source to the shared
  sources. Every structural assertion those tests make is kept.
- Leave all per-skill pinned copies untouched: mandates, mandate successors, and load-bearing
  sentences stay hand-maintained. Their pinning exists to force a deliberate paired diff for
  skill-specific wording, and generating them would silently bless a rogue reword.

No user-facing behavior changes. The shipped `SKILL.md` files are byte-identical before and
after; the first run of the extended sync is required to produce an empty diff.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-packaging`: synchronized copies extend from whole files to regions inside a
  `SKILL.md`, with the generated-file marker waived for that case; identity of the workflow
  line, voice block, and report offer is established by materialization from a single source
  and verified by the drift check, instead of by cross-file comparison against test literals.

## Impact

- `shared/blocks/` (new): three sources.
- `scripts/sync_shared.py`: region materialization pass, covered by `--check`.
- `skills/*/SKILL.md`: no content change; the three regions become generated.
- `tests/unit/test_skill_header_pattern.py`, `tests/unit/test_report_offer.py`,
  `tests/unit/test_sync.py`: assertions re-pointed, new coverage for the region pass.
- Not affected: `openspec/specs/skill-packaging` requirements on mandates and load-bearing
  sentences; every skill's installed content; anything `npx skills add` materializes.
