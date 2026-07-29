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

// TODO marker (legacy: orange bold)
#let todo(body) = text(fill: orange, weight: "bold")[TODO: #body]

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
