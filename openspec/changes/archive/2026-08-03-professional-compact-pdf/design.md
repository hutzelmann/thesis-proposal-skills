# Design — professional-compact-pdf

## Context

The build is pandoc → citeproc (`compact-numeric.csl`) → engine tier. Pandoc emits the reference list as an unstyled `#block[…] <refs>` in typst (each entry an inner `<ref-…>` block) and as a `CSLReferences` environment in LaTeX. The typst template (`proposal.typ`) sets A4/1in/11pt, no font, no page numbers; the LaTeX tier gets geometry via `-V` flags in `publish.py` and styling via `latex-header.tex`. The LaTeX tier already prints page numbers (plain pagestyle); the typst tier does not — an existing divergence this change removes. No L0 test pins geometry or refs markup.

## Goals / Non-Goals

**Goals:**
- One mechanism for the bibliography headline that serves both PDF tiers.
- Style the reference list where it already lands (pandoc's output), not by re-plumbing citation processing.
- Keep the templates the single place where the look is defined; `publish.py` changes stay minimal.

**Non-Goals:**
- No change to citation processing, CSL entry content, or the author-intext/cite-split filters.
- No docx reference-doc; the word-processor tier changes only by inheriting the headline (see Decisions).
- No configurability: one look, no flags or workspace overrides.

## Decisions

1. **Headline via pandoc `reference-section-title` metadata, set by `publish.py` from the proposal's `lang`.**
   Citeproc then inserts an unnumbered heading before the refs in every writer — typst, LaTeX, and docx get the same headline from one mechanism. `publish.py` extracts `lang` with a narrow regex over the metadata block (allowed: narrow extraction, not YAML parsing) and passes `-M reference-section-title=References|Literatur` (`de` → Literatur, default References, matching template lang handling).
   *Alternative rejected:* injecting the heading in each template (typst show-rule + LaTeX env hook) — two mechanisms to keep in sync, and the LaTeX hook is brittle.
   *Verify during implementation:* pandoc's typst writer must render the `.unnumbered` class as an unnumbered heading; if it does not, add a template show-rule on the heading pandoc labels `<references>` that strips the number — the metadata mechanism stays either way.
   *Side effect accepted:* the docx tier gains the headline too. That is an improvement, not a regression; "docx untouched" means no reference-doc work.

2. **Typst refs styling via a show-rule on the `<refs>` label.**
   `#show <refs>:` scopes `text(size: 10pt)`, `par(justify: true, hanging-indent: 2em, first-line-indent: 0em)`, and inner block spacing to the reference list only. Hanging indent is a fixed 2em — sized to fit a two-digit `[10]` label at 10pt — rather than varying with the label width; a constant indent keeps every proposal identical and costs almost nothing on short lists. Entry spacing is 1em, not the naive 0.35em: the gap between entries must exceed the 0.65em line leading, or a wrapped line visually attaches to the following entry (found in QA review). A second QA round asked for the LaTeX tier's two-column look also in typst: a regex show-rule inside the `<refs>` transform boxes each `[n] ` label to a fixed 2em width, so first lines and hanging-indented wraps share one left edge.

3. **LaTeX refs styling by adjusting the `CSLReferences` environment in `latex-header.tex`.**
   Pandoc's default template defines the CSL macros before `header-includes`, so the header can wrap the environment: `\small`, hanging indent via pandoc's own `\cslhangindent` (set to the matching length), entry spacing via parskip inside the environment. If the definition order turns out otherwise, fall back to `\AtBeginDocument` redefinition.

4. **Geometry and type.**
   Typst: `margin: 2.2cm`, `font: "New Computer Modern"` (bundled in the typst binary — zero install), body stays 11pt. LaTeX: `-V geometry:margin=2.2cm` in `publish.py`; default Latin Modern already matches NCM's look, `fontsize=11pt` unchanged. Line rhythm is measured, not assumed: typst leading is 0.55em so both tiers set 13.55–13.56pt baseline-to-baseline (typst's 0.65em default measured 14.7pt against LaTeX's 13.6pt), and the LaTeX `\droptitle` is sized so both title tops land 60.6pt from the page top (`pdftotext -bbox` on both tiers).

5. **Page numbers.**
   Typst: explicit footer, centered arabic numeral at 9pt (explicit footer rather than `page.numbering` so the size is controlled). LaTeX: plain pagestyle already delivers this; verify size is acceptable, otherwise leave — the spec asks for presence and placement, not identical footers.

6. **Title block and headings (typst).**
   Title 15pt, subtitle/author gaps reduced (~0.55em/0.65em), heading spacing reduced ~15% (L1 above 1.1em / below 0.55em; L2 above 0.95em / below 0.5em). A thin closing rule was tried and removed on user review. On the LaTeX tier the space below `\maketitle` (empty date block plus the class's closing `\vskip 1.5em`) is trimmed via `titling` hooks, and the `\null\vskip 2em` above it is pulled back with a negative `\droptitle` so the title starts near the top margin like the typst tier; typst's own gap below the title block is 1.2em, matched to the LaTeX rhythm on user review. `microtype` is loaded on the LaTeX tier (protrusion under xetex, expansion too on pdf/luatex); typst exposes no protrusion setting — its justified paragraphs already use optimized linebreaking by default, so there is nothing further to enable there. Beyond that, parity is "same structure", not pixel equality.

7. **German close-quote repair (found during QA).**
   Citeproc's German locale quotes reference titles as „…“, but pandoc's typst writer straightens the closing “ to `"` (the character doubles as the English opening mark) while passing „ through literally. Typst's smartquote never sees a matching opener for the straight quote and renders „Titel„. Fix: inside the `<refs>` show-rule, map the literal „ onto a `smartquote(double: true)` element so pairing is restored and the close renders as “. Inert for English (no „ in its refs). The LaTeX writer emits ``` `` ``` for the close, which typesets as “ — already correct, no change there.

8. **Research-question parity on the LaTeX tier (QA round 4).**
   rq-filter.lua originally styled the RQ list for typst only; the LaTeX tier fell back to a plain enumerate. The filter now emits `\rqblock{n}{…}` for latex — same in-place raw-inline wrapping (citeproc-safe) — with the command defined in `latex-header.tex` mirroring typst's `rq()`. TODO labels render at body size on both tiers (the 8pt/`\footnotesize` label caused a visible height step in the inline highlight, which is additionally pinned to ascender/descender edges in typst).

## Risks / Trade-offs

- [Pandoc version differences in how `.unnumbered` reaches the typst writer] → fallback show-rule on the `<references>` heading label, decided at implementation time, covered by the L2 QA renders.
- [Font change reflows every line] → nothing pins line breaks; QA renders (en, de, ref-heavy, xelatex tier) are the safety net.
- [2em hanging indent slightly airy for 3-entry lists] → accepted for cross-document consistency; revisit only if QA shows it ugly.
- [`reference-section-title` alters docx output] → accepted improvement, noted in proposal scope.
- [audit-invariant tests or typst drift guard may exercise the template] → run the full L0 suite plus `sync_shared.py --check` before showing QA renders.

## Open Questions

None — the two verify-points above (pandoc unnumbered emission, LaTeX macro ordering) have decided fallbacks and cannot change specs or task breakdown.
