# Professional Compact PDF

## Why

The built PDF renders the bibliography as unlabeled body paragraphs — no headline, no hanging indent, body-size text running straight on after the last section — and the page itself wastes space (1in margins, tall title block, no page numbers). The document a student hands to a supervisor should look professionally typeset; today it looks like a draft.

## What Changes

- Bibliography gets an unnumbered, language-aware headline ("References" / "Literatur") and reference-list typesetting: one step below body size, hanging indent so the `[n]` labels stand flush left and wrapped lines align, small uniform gap between entries, justified.
- Page geometry tightens from 1in to a uniform 2.2cm margin; pages carry a plain bottom-center page number.
- Body font becomes New Computer Modern (bundled with typst — zero install), giving the typst tier visual parity with the LaTeX tier's Latin Modern.
- Title block tightens moderately: 15pt title, less vertical air, thin rule closing the block; heading spacing trimmed ~15%. Body stays 11pt.
- Scope: typst template (fidelity reference) and LaTeX header parity. The word-processor tier is untouched.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `skill-publish`: The "Compact output and citation style" requirement gains concrete page-economy behavior (tighter margins, page numbers, title block); a new requirement covers bibliography presentation (localized headline, hanging-indent reference list, reduced size). Typst remains the fidelity reference; the LaTeX tier approximates without extra packages.

## Impact

- `skills/proposal-publish/templates/proposal.typ` — page setup, font, title block, headings, new `<refs>` styling and headline.
- `skills/proposal-publish/templates/latex-header.tex` — matching geometry, bibliography environment styling, page numbers.
- `skills/proposal-publish/scripts/publish.py` — only if the headline is injected via pandoc metadata rather than the templates (design decision).
- Tests pinning build output (`test_export_matrix.py`, `test_publish.py`, `test_ci_typst_drift.py`) — verify none pin the old geometry; extend where the new behavior is cheaply checkable at L0.
- No fixture or `shared/structure.json` changes: the headline is build-generated, not student-written content.
