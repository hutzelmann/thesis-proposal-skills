# Proposal: s3-typst-template-spike

## Why

The skill-publish spec requires compact output with the legacy template's look, typst-first. Whether the `compactarticle.cls` layout (compact title, tight numbered sections, bold `RQ n:` list styling without a LaTeX environment) can be reproduced in a pandoc→typst pipeline is spike S3 from the rewrite plan — the last unresolved feasibility question before skill implementation.

## What Changes

- Port the `compactarticle.cls` layout to `skills/proposal-publish/templates/proposal.typ` (pandoc typst template).
- Solve RQ styling markdown-natively: plain ordered list under the research-questions section, restyled to bold `RQ n:` labels by a pandoc Lua filter (`rq-filter.lua`).
- Create the first fixture (`tests/fixtures/f00-clean-en/`) by converting the legacy Jane Doe `proposal.tex` + `literature.bib` to the single-file format — spike vehicle and migration-step-3 head start in one.
- Build the PDF end to end (pandoc → citeproc → lua filter → typst) and compare against the legacy `build/proposal.pdf`.
- `skip_specs: true`: implements existing skill-publish/proposal-file-format requirements; no behavior contract changes.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- New: `skills/proposal-publish/templates/{proposal.typ, rq-filter.lua}`, `tests/fixtures/f00-clean-en/ml-code-review.md`.
- Starts the target `skills/` and `tests/fixtures/` trees.
- No spend, local tools only (pandoc 3.10, typst 0.15).
