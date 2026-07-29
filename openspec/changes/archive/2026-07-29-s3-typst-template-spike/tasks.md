# Tasks: s3-typst-template-spike

## 1. Fixture vehicle

- [x] 1.1 Convert Jane Doe `proposal.tex` + `literature.bib` to `tests/fixtures/f00-clean-en/ml-code-review.md` (single-file format, `[@key]` citations, trailing CSL-YAML)

## 2. Template port

- [x] 2.1 Write `skills/proposal-publish/templates/proposal.typ`: A4, 1in margins, 11pt, compact centered title block (subtitle italic, no date), numbered compact sections, dash bullets, justified text
- [x] 2.2 Write `skills/proposal-publish/templates/rq-filter.lua`: ordered list following the research-questions heading (en/de) → bold `RQ n:` styled blocks

## 3. Build and verify

- [x] 3.1 Build PDF: pandoc → citeproc → lua filter → typst; must compile without errors
- [x] 3.2 Verify rendered output: title block, section numbering, RQ labels, resolved citations + bibliography; compare against legacy `build/proposal.pdf`
- [x] 3.3 Record findings in design.md notes; commit
