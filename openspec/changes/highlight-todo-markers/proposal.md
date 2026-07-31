# Highlight TODO Markers in the Compiled Proposal

## Why

`[TODO: …]` markers are the skills' core honesty device — every gap is marked rather than invented or silently left open. In the compiled PDF that device disappears: a marker renders as plain black body text, in the same face and weight as the prose around it. In a justified 11pt column a leftover marker reads as a sentence, which is exactly the failure the marker exists to prevent.

The typst template already anticipated this. `templates/proposal.typ` defines `#let todo(body) = text(fill: orange, weight: "bold")[TODO: #body]` — and nothing has ever called it. The intent was recorded and never wired up.

## What Changes

- Markers render as annotations that cannot be mistaken for prose: a slate field, a navy rule or underline, and a small-caps `TODO n` label. Color carries no information on its own — every cue is duplicated in a form that survives grayscale printing.
- Markers are numbered continuously through the document, so a gap can be named in conversation ("TODO 4") rather than quoted. No index or summary section is generated; nothing is appended to the document, so page limits are unaffected.
- A marker alone on its source line becomes a block-level callout, interrupting the text column. A marker inside a sentence becomes an inline highlight that wraps across lines like a marker pen. Inside list items, headings, and table cells a marker is always inline, so it never conflicts with `rq-filter.lua`'s inline rewriting of research-question items.
- Markers in the `title` and `subtitle` metadata are rendered too, and are numbered ahead of the body so numbering follows reading order. The `references` block is never scanned — a marker inside a reference abstract stays untouched.
- All three output tiers render markers, at graded fidelity: typst is the fidelity reference, LaTeX approximates it with `xcolor` and `soul` only, and docx falls back to a bold `TODO n:` label.
- No configuration is added. There is no flag or override that renders markers quietly: the way to a clean PDF is to resolve the markers, which is what `proposal-check` already reports.

No breaking changes. Marker syntax, the check skill, and every fixture oracle are untouched; only the rendering of an already-legal syntax changes.

## Capabilities

### New Capabilities

None. This change extends existing capabilities.

### Modified Capabilities

- `skill-publish`: gains a TODO-rendering requirement — the visual contract, continuous numbering including metadata, the block-versus-inline rule and its containment exception, graded tier fidelity, and the absence of a suppression switch.
- `proposal-file-format`: the visible-TODO requirement gains the rendered contract (a marker is rendered as a distinguishable annotation, not as prose) and acknowledges that `title` and `subtitle` may carry a marker while the `references` block is out of scope.

## Impact

- New `skills/proposal-publish/templates/todo-filter.lua`, appended to the filter chain in `skills/proposal-publish/scripts/publish.py` after `rq-filter.lua`.
- `skills/proposal-publish/templates/proposal.typ`: the unused `#let todo` is replaced by `#let todo-inline(n, body)` and `#let todo-block(n, body)`.
- `skills/proposal-publish/templates/latex-header.tex`: `xcolor` and `soul` plus two macros for the LaTeX tier.
- `skills/proposal-publish/SKILL.md`: the filter-chain description gains the new filter.
- New L0 tests mirroring `tests/unit/test_rq_filter_citations.py` (real filter chain under pandoc, skipped without pandoc) and `tests/unit/test_rq_filter_drift.py` (the filter's hardcoded regex must not drift from `shared/structure.json`'s `todo_marker`).
- Not touched: `skills/proposal-check/`, `shared/structure.json`, and every fixture `expected.json`. Highlighting a gap and reporting a defect stay separate jobs.
- No new Python dependency; the filter is Lua run by pandoc.
