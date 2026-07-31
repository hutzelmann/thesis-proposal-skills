// thesis-proposal-skills — compact typst template for pandoc
// Port of the legacy compactarticle.cls look: A4, 1in margins, 11pt,
// compact centered title block, tight numbered sections, dash bullets.

#set page(paper: "a4", margin: 1in)
#set text(size: 11pt$if(lang)$, lang: "$lang$"$endif$)
#set par(justify: true, first-line-indent: 1.2em, spacing: 0.65em)

// Tight numbered sections (legacy: titlesec compact,small)
#set heading(numbering: "1.1")
#show heading.where(level: 1): it => block(above: 1.3em, below: 0.65em, text(size: 12pt, weight: "bold", it))
#show heading.where(level: 2): it => block(above: 1.1em, below: 0.55em, text(size: 11pt, weight: "bold", it))

// Compact lists, dash bullet markers (legacy: enumitem nosep, label=--)
#set list(marker: [--], spacing: 0.65em, indent: 0.6em)
#set enum(spacing: 0.65em, indent: 0.6em)

// Research question item, used by rq-filter.lua
#let rq(n, body) = block(above: 0.8em, inset: (left: 1.2em))[#strong[RQ#n:] #body]

// TODO markers, used by todo-filter.lua. Editorial-slate annotation: every cue
// is duplicated non-chromatically (rule, underline, small-caps label) so a
// marker stays distinguishable in a grayscale reproduction.
#let todo-label(n) = text(size: 8pt, fill: rgb("#2B4C7E"), tracking: 0.8pt)[#smallcaps[TODO #n]]
// Inline form: highlight() and underline() both break across lines, which a
// box() would not — real hints run to 100 characters.
#let todo-inline(n, body) = underline(
  stroke: 0.6pt + rgb("#2B4C7E"), offset: 2.5pt,
  highlight(fill: rgb("#DDE5EF"), extent: 1pt)[#todo-label(n) #body],
)
// Block form: deeper cue set for a marker that owns its line. The paragraph
// resumed after this block is not indented (par.first-line-indent defaults to
// all: false), so the split reads as an interrupted paragraph.
#let todo-block(n, body) = block(
  above: 0.65em, below: 0.65em, width: 100%,
  fill: rgb("#EDF1F6"), stroke: (left: 2pt + rgb("#2B4C7E")),
  inset: (left: 8pt, right: 8pt, top: 5pt, bottom: 5pt),
)[#todo-label(n)#h(0.8em)#body]

// Links plain black (legacy: hidelinks)
#show link: set text(fill: black)

// Compact title block (legacy: titling with negative droptitle, italic subtitle, no date)
#align(center)[
  #block(text(size: 16pt, weight: "bold")[$title$])
  $if(subtitle)$#block(above: 0.7em, text(size: 11pt, style: "italic")[$subtitle$])$endif$
  $if(author)$#block(above: 0.8em, text(size: 11pt)[$for(author)$$author$$sep$, $endfor$])$endif$
]
#v(0.6em)

$body$

$if(citations)$$endif$
