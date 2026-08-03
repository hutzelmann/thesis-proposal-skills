// thesis-proposal-skills — compact typst template for pandoc
// Successor of the legacy compactarticle.cls look: A4, 2.2cm margins, 11pt
// New Computer Modern, compact centered title block, tight numbered sections,
// dash bullets, hanging-indent reference list.

#set page(
  paper: "a4", margin: 2.2cm,
  footer: context align(center, counter(page).display("1")),
)
#set text(font: "New Computer Modern", size: 11pt$if(lang)$, lang: "$lang$"$endif$)
// leading 0.55em matches the LaTeX tier's 13.6pt baseline distance at 11pt
// (default 0.65em measures 14.7pt); spacing = leading keeps paragraphs
// continuous — the first-line indent alone marks the break, like parskip 0pt.
#set par(justify: true, first-line-indent: 1.2em, leading: 0.55em, spacing: 0.55em)

// Tight numbered sections (legacy: titlesec compact,small)
#set heading(numbering: "1.1")
// above values measured against the LaTeX tier's titlesec spacing (20.2pt
// body-baseline to heading-baseline for level 1). The 1em number–text gap
// mirrors the article class's \quad after the section number.
#let heading-line(it, size) = text(size: size, weight: "bold",
  if it.numbering == none { it.body }
  else [#counter(heading).display(it.numbering)#h(1em)#it.body],
)
#show heading.where(level: 1): it => block(above: 0.83em, below: 0.55em, heading-line(it, 12pt))
#show heading.where(level: 2): it => block(above: 0.68em, below: 0.5em, heading-line(it, 11pt))

// Reference list: citeproc labels its container block <refs>. One step below
// body size, [n] flush left with wrapped lines aligned, small uniform gap.
#show <refs>: set text(size: 10pt)
#show <refs>: set par(justify: true, hanging-indent: 2em, first-line-indent: 0em)
// Entry gap must exceed the 0.65em line leading, or a wrapped line reads as
// belonging to the following entry. 1em ≈ leading + a visible 0.35em.
#show <refs>: set block(spacing: 1em)
// German titles arrive as a literal „ plus a straight closing " (pandoc's typst
// writer straightens the closing “ because it doubles as the English opening
// mark), which smartquote then mispairs as „Titel„. Mapping the literal „ onto
// a smartquote element restores the pairing, so the close renders as “ again.
// Inert for English references: those carry only straight quotes.
#show <refs>: it => {
  show "„": smartquote(double: true)
  // Two-column look matching the LaTeX tier: the label sits in a fixed 2em
  // box, so every text line — first and wrapped alike — shares one left edge
  // (wraps via par.hanging-indent above).
  show regex("\[\d+\] "): m => box(width: 2em, m.text.trim())
  it
}

// Compact lists, dash bullet markers (legacy: enumitem nosep, label=--)
#set list(marker: [--], spacing: 0.65em, indent: 0.6em)
#set enum(spacing: 0.65em, indent: 0.6em)

// Research question item, used by rq-filter.lua
#let rq(n, body) = block(above: 0.8em, inset: (left: 1.2em))[#strong[RQ#n:] #body]

// TODO markers, used by todo-filter.lua. Editorial-slate annotation: every cue
// is duplicated non-chromatically (rule, underline, small-caps label) so a
// marker stays distinguishable in a grayscale reproduction.
#let todo-label(n) = text(fill: rgb("#2B4C7E"))[#smallcaps[TODO #n]]
// Inline form: highlight() and underline() both break across lines, which a
// box() would not — real hints run to 100 characters.
// Fixed edges keep the highlight one uniform band — glyph bounds would step
// down over the small-caps label. The 0.95em top edge leaves as much air
// above the cap height as the descender edge leaves below the baseline; the
// underline extent matches the highlight's so both end flush.
#let todo-inline(n, body) = underline(
  stroke: 0.6pt + rgb("#2B4C7E"), offset: 2.5pt, extent: 1pt,
  highlight(
    fill: rgb("#DDE5EF"), extent: 1pt,
    top-edge: 0.95em, bottom-edge: "descender",
  )[#todo-label(n) #body],
)
// Block form: deeper cue set for a marker that owns its line. The paragraph
// resumed after this block is not indented (par.first-line-indent defaults to
// all: false), so the split reads as an interrupted paragraph.
// Top inset is smaller than bottom on purpose: the last line's box ends at
// the baseline, so descenders eat into the bottom inset. 3.75pt matches the
// air the inline marker's band leaves above the cap height.
#let todo-block(n, body) = block(
  above: 0.65em, below: 0.65em, width: 100%,
  fill: rgb("#EDF1F6"), stroke: (left: 2pt + rgb("#2B4C7E")),
  inset: (left: 8pt, right: 8pt, top: 3.75pt, bottom: 5pt),
)[#todo-label(n)#h(0.8em)#body]

// Links plain black (legacy: hidelinks)
#show link: set text(fill: black)

// Compact title block (legacy: titling with negative droptitle, italic subtitle, no date)
#align(center)[
  #block(text(size: 15pt, weight: "bold")[$title$])
  $if(subtitle)$#block(above: 1.1em, text(size: 11pt, style: "italic")[$subtitle$])$endif$
  $if(author)$#block(above: 0.65em, text(size: 11pt)[$for(author)$$author$$sep$, $endfor$])$endif$
]
#v(1.2em)

$body$

$if(citations)$$endif$
