## 1. Templates

- [x] 1.1 In `skills/proposal-publish/templates/proposal.typ`, replace the unused `#let todo(body)` with `#let todo-inline(n, body)` — `underline(stroke: 0.6pt + rgb("#2B4C7E"), offset: 2.5pt, highlight(fill: rgb("#DDE5EF"), extent: 1pt, [label + body]))` — and `#let todo-block(n, body)` — a full-width `block` with `fill: rgb("#EDF1F6")`, `stroke: (left: 2pt + rgb("#2B4C7E"))`, and the label
- [x] 1.2 Define the shared label form once in the typst template: 8pt, small caps, `#2B4C7E`, reading `TODO n`
- [x] 1.3 In `skills/proposal-publish/templates/latex-header.tex`, add `xcolor` and `soul`, the three colors, and `\todolabel`, `\todoinline`, `\todoblock` — with `\todoinline` placing the label **outside** `\hl`, and a comment recording that `soul` fails on a macro-with-arguments inside `\hl`

## 2. Filter

- [x] 2.1 Add `skills/proposal-publish/templates/todo-filter.lua` returning two filter tables, `{ Meta = … }` then `{ Pandoc = … }`, with a comment stating why one table cannot work (pandoc applies `Meta` after blocks)
- [x] 2.2 Write the inline scanner: over an `Inlines` list, find runs from a token beginning `[TODO:` to the token ending `]`, treating an interior `SoftBreak` as a space; return the hint inlines and the run's index span
- [x] 2.3 Write the own-line test: the run is own-line when bounded on both sides by `SoftBreak`, `LineBreak`, or the list edge
- [x] 2.4 Write the per-format emitters — typst `#todo-inline(n)[…]` / `RawBlock` `#todo-block(n)[…]`, LaTeX `\todoinline{n}{…}` / `\todoblock{n}{…}`, and for every other writer a `Span` with class `mark` carrying a `Strong` label
- [x] 2.5 Guard the LaTeX inline emitter: use `\hl` only when every hint inline is `Str`, `Space`, or `SoftBreak`; otherwise emit the label plus unhighlighted bold text
- [x] 2.6 In the `Meta` table, number markers in `title` and `subtitle` only, and assert by construction that `references` is never visited
- [x] 2.7 In the `Pandoc` table, walk `doc.blocks` with `process(blocks, allow_block)`, passing `allow_block = false` into `BulletList`, `OrderedList`, `Table`, `BlockQuote`, and `Header`, so callouts appear only at top level and numbering follows document order
- [x] 2.8 Emit the callout by splitting the paragraph into `Para(before)`, `RawBlock`, `Para(after)`, dropping either half when empty
- [x] 2.9 Hardcode the marker regex with a comment pointing at `shared/structure.json`'s `todo_marker` as the canonical source, mirroring `rq-filter.lua`

## 3. Pipeline and docs

- [x] 3.1 Append `--lua-filter todo-filter.lua` to the chain in `skills/proposal-publish/scripts/publish.py`, after `rq-filter.lua`, with a comment noting it runs last so it never sees unresolved citations
- [x] 3.2 Update the filter-chain description in `skills/proposal-publish/SKILL.md`

## 4. Tests

- [x] 4.1 Add `tests/unit/test_todo_filter.py` following `tests/unit/test_rq_filter_citations.py`: real chain under pandoc, `skipif` when pandoc is absent
- [x] 4.2 Assert an own-line marker in a prose paragraph produces block output and the prose before and after survives intact
- [x] 4.3 Assert a marker embedded in a sentence produces inline output and the sentence is otherwise unchanged
- [x] 4.4 Assert numbering is continuous across a document mixing both forms, and that a `subtitle` marker takes number one with body markers continuing from two
- [x] 4.5 Assert a bracketed fragment inside a `references` abstract is neither styled nor numbered
- [x] 4.6 Assert a marker inside a research-question list item renders inline and the item keeps its `#rq(n)` styling, with a citation in the same item (the `rq-filter.lua` regression surface)
- [x] 4.7 Assert a marker split across two source lines is joined into one annotation
- [x] 4.8 Assert the LaTeX guard: a hint containing emphasis emits no `\hl`, and a plain hint does
- [x] 4.9 Assert the docx tier emits a highlighted run for a marker
- [x] 4.10 Add `tests/unit/test_todo_filter_drift.py` mirroring `tests/unit/test_rq_filter_drift.py`: fail when the filter's hardcoded marker pattern diverges from `shared/structure.json`'s `todo_marker`
- [x] 4.11 Assert no fixture `expected.json` changed and `skills/proposal-check/` is untouched by this change

## 5. Verification

- [x] 5.1 `uv run pytest` green
- [x] 5.2 `uv run ruff check .` clean
- [x] 5.3 `python3 scripts/sync_shared.py --check` clean
- [x] 5.4 `openspec validate --all --strict` passes
- [x] 5.5 Build `tests/fixtures/f19-drift-alert-validity/drift-alert-validity.md` through `publish.py` on the typst tier and read the PDF: four numbered callouts, prose continuity across each split, no unwanted indent
- [x] 5.6 Build `tests/fixtures/w01-ideate-seed/data-drift-detection.md` and confirm the `subtitle` marker renders as number one in the title block
- [x] 5.7 Build one fixture through the LaTeX tier and confirm the same numbers, no `soul` reconstruction error in the log, and correct wrapping of the longest hint
- [x] 5.8 Convert one built PDF to grayscale and confirm every annotation stays distinguishable from prose
