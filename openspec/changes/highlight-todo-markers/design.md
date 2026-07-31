# Highlight TODO Markers — Design

## Context

See proposal.md — Why. Everything below was verified empirically against pandoc 3.10, typst 0.15.1, and TeX Live (pdflatex, xelatex, lualatex) on the fixtures this repo already ships.

**How a marker reaches the filter.** `[TODO: name the dataset]` has no link target, so pandoc parses it as ordinary text, split across a run of inlines with the brackets fused to the outer words:

```
Str "[TODO:", Space, Str "name", Space, Str "the", Space, Str "dataset]"
```

Detection therefore cannot key on a single `Str`; it must scan an `Inlines` list and rebuild the run. The `SoftBreak` on either side is what distinguishes an own-line marker from one embedded in a sentence — in markdown both live inside the same `Para`.

**Where markers actually occur.** Across `f19`, `w01`, and `f15`, five of six body markers sit alone on their source line but *inside* a paragraph of prose (before it, after it, or both). Only `w01` has a paragraph consisting solely of markers. A rule keyed on "the whole paragraph is a marker" would therefore almost never fire; the rule must key on source-line position.

**Hint content.** Real hints reach the LaTeX writer as `e.g.~River`, `dataset(s)`, `` ``performance decay'' ``, `---`. They are plain text by contract (`[TODO: <3–10 word hint>]`), never emphasis or citations.

**Existing pipeline.** `publish.py` runs `author-intext.lua` → `cite-split.lua` → `--citeproc` → `rq-filter.lua`, shared by all three tiers. `rq-filter.lua` rebuilds research-question list items as `pandoc.Plain(inlines)` and so accepts only inline content inside them.

**Hard constraints.** User-side code is Python ≥ 3.11 stdlib only; a Lua filter adds no dependency. The typst template is the fidelity reference; the LaTeX tier may not require packages beyond a standard TeX installation.

## Goals / Non-Goals

**Goals:**

- One filter owns detection and numbering, so every tier shows the same number for the same gap.
- Every cue is duplicated in a non-chromatic form, verified by inspecting the rendered page rather than by assertion.
- Zero churn in the check skill, `shared/structure.json`, and every fixture `expected.json`.

**Non-Goals:**

- Recovering markers whose hint contains a `]`. The canonical regex is `\[TODO:[^\]]*\]`; a hint containing a closing bracket truncates in check and will truncate here identically. Parity with check is worth more than a cleverer scanner.
- Rendering markers in the `--handout` markdown export. That path never invokes pandoc, and the raw `[TODO: …]` form is already visible in plain text.
- A TODO index, summary, or count. Nothing is appended to the document (see proposal.md).

## Decisions

### One Lua filter with an explicit recursive walk, not a `Para` handler

The filter is `templates/todo-filter.lua`, returning two filter tables:

1. `{ Meta = ... }` — numbers markers in `title` and `subtitle` only.
2. `{ Pandoc = ... }` — walks `doc.blocks` recursively and numbers everything else.

Two tables are required because pandoc applies `Meta` *after* blocks within a single table, which would number the subtitle last. Running `Meta` as its own earlier table makes metadata numbers precede body numbers. `author-intext.lua` already establishes this two-table shape in this repo.

The body pass is a hand-written recursion (`process(blocks, allow_block)`) rather than a `Para` handler, for two reasons that a handler cannot satisfy at once:

- **Containment.** A `Para` handler fires identically for a top-level paragraph and for a paragraph inside a list item; the handler cannot tell which it is. The recursion passes `allow_block = false` when descending into `BulletList`, `OrderedList`, `Table`, `BlockQuote`, and `Header`, which is exactly the containment rule.
- **Numbering order.** Handling containers in one filter table and top-level paragraphs in another would number a research-question list in section 3 before a paragraph in section 1. A single depth-first walk in document order cannot get this wrong.

*Alternative considered:* `traverse = 'topdown'` with a `Blocks` handler. It preserves document order but still cannot distinguish nesting depth without threading state through the traversal, which is the recursion by another name.

### Own-line detection by `SoftBreak` neighbourhood

Within an `Inlines` list, a marker is *own-line* when the inline before its first token is a `SoftBreak`, `LineBreak`, or the start of the list, and the inline after its last token is likewise a break or the end of the list. Own-line plus `allow_block` yields a callout: the paragraph is emitted as `Para(before)`, `RawBlock(callout)`, `Para(after)`, with empty halves dropped. Every other case yields an inline annotation.

Splitting the paragraph turned out to be free of visual cost. Typst's `first-line-indent` defaults to `all: false`, so the resumed half is *not* indented while a genuinely new paragraph still is — the split reads as an interrupted paragraph, which is what it is. Verified by rendering; no indent suppression is needed.

### Per-format emission, with a guard on the LaTeX tier

| Tier | Inline form | Block form |
|---|---|---|
| typst | `#todo-inline(n)[hint]` → `underline(highlight(…))` | `#todo-block(n)[hint]` → `block` with left rule |
| LaTeX | `\todoinline{n}{hint}` → label, then `\hl{hint}` | `\todoblock{n}{hint}` → `colorbox` + `minipage` + rule |
| other (docx) | `Span {.mark}` carrying a `Strong` label | same, as its own `Para` |

Typst gets both cues on the inline form (fill plus a 0.6pt underline); `highlight()` and `underline()` both break across lines correctly, verified on the longest real hint.

The LaTeX inline form puts the label **outside** `\hl`. This is not stylistic: `soul` re-scans its argument token by token and fails with `Package soul Error: Reconstruction failed.` when it contains a macro taking arguments. With the label outside, `\hl` handles every real hint — `~`, `---`, `` `` '' ``, parens, hyphens, umlauts, ß — under pdflatex, xelatex, and lualatex alike, and wraps across lines. The LaTeX tier therefore carries fill plus a small-caps navy label, and no underline (`soul` cannot nest `\ul` inside `\hl`). That is the graded-fidelity gap, and it is the only one.

`soul` remains brittle against content it was not designed for: a literal U+2014 in the hint was silently *dropped* under lualatex. Pandoc emits `---` rather than the literal character, so the real pipeline never hits this — but the filter guards anyway: `\hl` is used only when every inline in the hint is `Str`, `Space`, or `SoftBreak`. Anything else falls back to the label plus unhighlighted bold text, which is ugly but never corrupts.

docx needed no fallback. Pandoc maps `Span {.mark}` to a real Word `<w:highlight w:val="yellow"/>` run, so the word-processor tier gets a genuine highlight rather than the bold-only degradation originally assumed. The colour is fixed by Word's highlight enumeration and cannot be slate; that is accepted.

### Editorial-slate palette, cues duplicated non-chromatically

| Element | Value |
|---|---|
| Callout field | `#EDF1F6` |
| Callout rule | `#2B4C7E`, 2pt, left edge |
| Inline field | `#DDE5EF` (deeper — the inline form has no rule to carry a second cue) |
| Inline underline | `#2B4C7E`, 0.6pt, 2.5pt offset (typst only) |
| Label | `#2B4C7E`, 8pt, small caps, `TODO n` |

The palette reads as a reviewer's annotation rather than an error, which suits a document that is deliberately shown to a supervisor with its gaps marked. It is also already low-chroma, so grayscale reproduction changes it least of the options considered — a loud amber highlighter would have depended on colour more, not less. In every form the shape cues (rule, underline, small-caps label) carry the signal on their own.

### Numbering is unconditional and continuous

One counter, incremented in walk order, starting at 1, never reset, always rendered — including when the document contains exactly one marker, so that the annotation's shape does not change with document content. Markers inside the `references` metadata are never visited, so a bracketed fragment inside a reference abstract can neither be styled nor consume a number.

### The regex is hardcoded in Lua and guarded by a drift test

Lua cannot read `shared/structure.json` without a JSON dependency. `rq-filter.lua` faces the same problem for heading titles and solves it by hardcoding plus `tests/unit/test_rq_filter_drift.py`, which fails if the Lua and the canonical value diverge. This change follows that precedent exactly rather than inventing a second mechanism.

## Risks / Trade-offs

- **`soul` fragility on unexpected inline content** → `\hl` is applied only to `Str`/`Space`/`SoftBreak` runs; anything else degrades to an unhighlighted labelled form. Covered by a test using a hint containing emphasis.
- **A marker split across source lines** arrives with a `SoftBreak` inside it → the scanner treats a `SoftBreak` between the opening `[TODO:` and the closing `]` as a space and joins the run. Covered by a test.
- **docx highlight colour is fixed to yellow** by Word's enumeration → accepted; the docx tier already opts out of the compact layout and is documented as a last resort.
- **A hint containing `]` truncates** → identical to the check skill's behaviour today, so the two skills stay consistent rather than one being subtly cleverer. Not mitigated deliberately.
- **The LaTeX tier loses the underline cue** → it retains fill plus the small-caps label, satisfying the two-cue requirement; the typst tier remains the fidelity reference as the spec already states.
- **Two filters now both rewrite research-question items** (`rq-filter.lua` and this one) → this filter never emits block content inside a list item, so `rq-filter.lua`'s `pandoc.Plain(inlines)` reconstruction stays valid. Covered by a test placing a marker inside a research-question item alongside a citation.

## Migration Plan

Additive and reversible. The filter is appended to the chain after `rq-filter.lua`; removing that one line restores today's output exactly. No proposal file, fixture, or workspace file changes format, and no existing output other than marker rendering is touched.
