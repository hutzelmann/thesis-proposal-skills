## Context

See proposal.md — Why. Two existing mechanisms constrain the approach:

- `scripts/sync_shared.py` materializes sixteen whole-file copies from `shared/` sources,
  runs in the `poe test` chain and from the pre-commit hook, and reports drift under
  `--check`.
- `tests/unit/test_skill_header_pattern.py` already fixes the opening blocks to positions
  (`PURPOSE_INDEX = 1`, `WORKFLOW_INDEX = 2`, `VOICE_INDEX = 3`, `MANDATE_INDEX = 4`, blocks
  being blank-line-separated paragraphs from the title to the first `##`), and
  `tests/unit/test_report_offer.py` fixes the offer to the first paragraph of a closing
  `## When this run fails` section.

A `SKILL.md` is also a rendered page on skills.sh, showing frontmatter and body and nothing
else. Nine of the ten carry the closing section; six of those nine follow the offer with one
skill-specific paragraph.

## Goals / Non-Goals

**Goals:**

- One place to edit each cross-skill identical block.
- Shipped `SKILL.md` files byte-identical on adoption.
- Enforcement no weaker than today's.

**Non-Goals:**

- Touching per-skill pins. Explicitly out of scope, see the spec delta.
- Reducing whole-file copies under `skills/`. Impossible under skills.sh's install model.
- A general templating language for `SKILL.md`. Three blocks, not a template engine.

## Decisions

**Materialize regions in place; do not introduce `SKILL.md.in` sources.** A `.in` shadow
file makes the published artifact a build output and the editable file something else, which
means every contributor must learn which of two files to edit and every `grep` hits the wrong
one. Editing `SKILL.md` directly keeps one file that is simultaneously the source for its
own prose, the reviewed artifact, and the shipped page. Alternative considered: full-file
generation from a template. Rejected — it would put ninety percent hand-written prose behind
a build step to deduplicate three blocks.

**Anchor regions by position, not by inserted markers.** The obvious mechanism is a sentinel
comment pair around each block. Rejected on two grounds: an HTML comment is part of the
rendered page's source and a contributor can move or delete one, silently relocating a
generated block; and the positions are *already* normative and already enforced, so anchoring
to them adds no new invariant to maintain. The renderer locates block index 2 and 3 of the
opening region and the first paragraph of the `## When this run fails` section — exactly what
the two tests locate today. Where the anchor does not resolve, the sync fails loudly rather
than guessing an insertion point.

**Workflow line source carries a placeholder, not ten variants.** `shared/blocks/workflow.md`
holds the line with each skill name in plain form; the renderer wraps the owning skill's name
in `**`. This keeps "the set" stated once — the thing that actually changes when a skill is
added — and makes the per-skill difference mechanical rather than authored.

**The report offer is skipped for `proposal-troubleshoot`, and its trailing paragraph is out
of region.** The offer occupies the first paragraph of the closing section; anything after it
is per-skill and untouched. The assembling skill has no such section and is excluded from
the destination list, so its absence is not drift.

**Tests keep every structural assertion and give up only the literals.** `VOICE_BLOCK` in
the header test and the offer literal in the report-offer test are replaced by reads of the
shared sources. Position, count, uniqueness, marked-name correctness, purpose length bound,
mandate pinning, mandate adjacency, and the reporter-does-not-offer-itself rule all stay. The
guarantee those literals provided — "this wording was consciously chosen" — moves to the
source file, where it is one reviewable diff instead of ten identical ones.

**Byte-identical adoption is the acceptance gate, not a nice-to-have.** The three sources are
extracted from the current files, and the first run of the extended sync must produce an
empty `git diff` across all ten `SKILL.md`. A non-empty diff means the extraction was
inexact, and the fix is the source, never the skill file.

## Risks / Trade-offs

- **A position-anchored rewrite writes a block into the wrong place** → The anchors are the
  ones the offline suite already enforces, so a file whose structure would mislocate a block
  fails the suite before the sync is trusted; and the sync refuses to write when an anchor
  does not resolve rather than inserting at a guess.
- **Generation makes a rogue reword invisible** → It does not: the wording moves to a source
  file whose diff is the review surface. What it removes is nine *duplicate* diffs of the
  same reword, which is noise, not scrutiny.
- **`--check` and the pre-commit hook now rewrite files people are editing** → Same contract
  as today's copies, and the hook already runs the sync at commit time. The added test for
  idempotency ensures a second run is a no-op.
- **A future block wants per-skill variation** → Then it is not an identical block and does
  not belong in `shared/blocks/`. The spec draws that line at "identical across skills by
  requirement".

## Migration Plan

Single change: extract sources, extend the sync, re-point tests, run the sync, confirm the
empty diff. Rollback is reverting the commit; the `SKILL.md` files carry no marker and would
be left exactly as they are today.
