# Design: s3-typst-template-spike

## Context

See proposal.md. Legacy look source: `compactarticle.cls` (A4, 1in, 11pt, kpfonts light, compact titling, titlesec compact/small, enumitem nosep with dash bullets, custom RQs enumerate with bold `RQ n:` labels, orange TODO).

## Decisions

- **D-S3-1 — RQ styling via Lua filter, not markup.** Proposals keep a plain markdown ordered list under the research-questions heading (en: "Research Questions", de: "Forschungsfragen"); `rq-filter.lua` converts it to `#rq(n)[…]` template calls for typst output only. Other output formats keep the plain list. Rationale: zero format-specific markup in user files (proposal-file-format spec holds).
- **D-S3-2 — Fonts.** Typst default (Libertinus Serif) instead of a kpfonts clone: professional, always available, no font-install burden. Fidelity target is "compact and clean", not glyph-identical.
- **D-S3-3 — Template owns layout, citeproc owns citations.** The template does not use typst's native bibliography; citeproc output flows through (already verified in S2).

## Spike Results

Build `pandoc <fixture> --citeproc --lua-filter rq-filter.lua --template proposal.typ --pdf-engine=typst` compiles first try; rendered PDF compared against legacy `build/proposal.pdf`:

- Title block (bold title, italic subtitle, author, no date, compact spacing) ✓
- Numbered compact sections and subsections ✓
- Bold `RQ n:` labels with indent — visually equivalent to the LaTeX RQs environment ✓
- Justified body, first-line indent ✓
- Known gaps (planned follow-ups, not spike failures): citation style is author-date pending the compact numeric `.csl` (migration step 4); bibliography needs a References heading + hanging-indent styling in the template.

**S3 resolved: typst-first pipeline is viable with full layout fidelity; RQ styling works without any LaTeX environment.**

## Risks / Trade-offs

- Lua filter keys on heading text (en/de canonical titles) — must stay in sync with `structure.json` once it exists; add an L0 test then.
