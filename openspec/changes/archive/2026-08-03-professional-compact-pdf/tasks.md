# Tasks — professional-compact-pdf

## 1. Headline mechanism

- [x] 1.1 Add narrow `lang` extraction to `publish.py` and pass `-M reference-section-title=References|Literatur` in `pandoc_command` (de → Literatur, default References)
- [x] 1.2 Verify the typst writer renders the headline unnumbered; if numbered, add the fallback show-rule on the `<references>` heading label in `proposal.typ`
- [x] 1.3 Unit-test the lang extraction and the flag's presence in `pandoc_command` output (L0, no pandoc call)

## 2. Typst template

- [x] 2.1 Page setup: 2.2cm uniform margin, New Computer Modern, 9pt centered footer page number
- [x] 2.2 Bibliography: `#show <refs>` rule — 10pt, justified, 2em hanging indent, zero first-line indent, 0.35em entry spacing
- [x] 2.3 Title block: 15pt title, tightened gaps, 0.4pt closing rule; heading spacing −15% (L1 1.1em/0.55em, L2 0.95em/0.5em)

## 3. LaTeX tier parity

- [x] 3.1 Change `-V geometry:margin=1in` to `2.2cm` in `publish.py`
- [x] 3.2 Style `CSLReferences` in `latex-header.tex`: `\small`, hanging indent matching typst, 0.35em-equivalent entry spacing (fallback `\AtBeginDocument` if macro ordering requires)
- [x] 3.3 Verify page numbers and headline render in a xelatex build

## 4. German quote repair (QA finding)

- [x] 4.1 Map literal „ onto `smartquote` inside the typst `<refs>` rule so German titles close with “; verify LaTeX tier already correct

## 5. QA review round 1 (user feedback)

- [x] 5.1 Typst: raise bibliography entry spacing above line leading (0.35em → 1em) so entries separate correctly
- [x] 5.2 Typst: remove the rule under the title block
- [x] 5.3 LaTeX: trim the space below \maketitle via titling hooks

## 6. QA review round 2 (user feedback)

- [x] 6.1 LaTeX: pull the title block up (negative \droptitle vs titling's \null\vskip 2em)
- [x] 6.2 Typst: widen the gap below the title block to match the LaTeX feel (0.6em → 1.2em)
- [x] 6.3 LaTeX: load microtype; document that typst has no protrusion knob (optimized linebreaking already default)
- [x] 6.4 Typst: box the [n] label to a fixed 2em column so all bibliography text lines share one left edge, like the LaTeX tier

## 7. QA review round 3 (user feedback)

- [x] 7.1 LaTeX: set \droptitle from measured positions so the title top matches typst (both 60.6pt from page top, pdftotext -bbox verified)
- [x] 7.2 Typst: leading 0.55em to match LaTeX's 13.6pt baseline distance (measured 13.56 vs 13.55pt after change); par spacing kept equal to leading
- [x] 7.3 Render a TODO-marker example document for review

## 8. QA review round 4 (user feedback)

- [x] 8.1 LaTeX: render research questions as bold "RQn:" indented blocks like typst — rq-filter.lua emits \rqblock for latex, defined in latex-header.tex; latex variant of the citation-survival test added
- [x] 8.2 Typst: title–subtitle gap raised to the LaTeX distance (measured 7.84 vs 7.73pt)
- [x] 8.3 Both tiers: TODO label at body text size (was 8pt / \footnotesize)
- [x] 8.4 Typst: inline TODO highlight fixed to ascender/descender edges — one uniform band, no step

## 9. QA review round 5 (user feedback)

- [x] 9.1 Typst: heading `above` tightened to the LaTeX pre-headline distance (measured 20.21 vs 20.16pt for level 1; level 2 scaled alongside)
- [x] 9.2 LaTeX: RQ item pitch matched to typst (16.34 vs 16.35pt) — \rqblock compensates pandoc's ~6pt \parskip with -4pt

## 10. QA review round 6 (user feedback)

- [x] 10.1 Typst: 1em gap between heading number and text, mirroring the article class's \quad (measured 12.00/11.00pt vs LaTeX 11.96/10.91pt); unnumbered headings unaffected
- [x] 10.2 Typst: TODO label tracking removed — regular small-caps spacing
- [x] 10.3 Typst: page number at body size like the LaTeX footer (was 9pt)

## 11. QA review round 7 (user feedback)

- [x] 11.1 LaTeX: background restored behind the inline TODO label — \colorbox with fboxsep 0 and \strut matches soul's band height (soul still rejects \color inside \hl; verified by build failure before the fallback)

## 12. QA review round 8 (user feedback)

- [x] 12.1 LaTeX: inline label box height matched to soul's exact band (-0.75ex to +1.75ex rule strut instead of \strut)
- [x] 12.2 Both tiers: block TODO field padding balanced — LaTeX bar shrunk to the text's vertical extent, typst top inset reduced to what the baseline-edge leaves below

## 13. QA review round 9 (user feedback)

- [x] 13.1 Typst: inline highlight top edge raised to 0.95em — air above the caps now matches the baseline-to-box-bottom distance
- [x] 13.2 Typst: underline extent matched to the highlight's 1pt so both end flush

## 14. QA review round 10 (user feedback)

- [x] 14.1 Typst: block TODO top inset raised to 3.75pt — same air above the caps as the inline band (LaTeX block already at ~3pt, unchanged)

## 15. Verification and QA

- [x] 15.1 Run `uv run pytest`, `uv run ruff check .`, `python3 scripts/sync_shared.py --check`, `openspec validate --all --strict`
- [x] 15.2 Build QA renders in scratchpad: f00 (en), f12 (de), f04 (ref-heavy), synthetic 12-ref doc (two-digit labels), one xelatex-tier build of f00
- [x] 15.3 Show PDFs to the user; iterate on adjustments until approved
