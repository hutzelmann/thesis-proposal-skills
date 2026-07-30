## Context

See proposal.md — Why. The findings below were established empirically against pandoc 3.10 with the repo's own `compact-numeric.csl`, and shape every decision here.

**Why `@key` renders nameless today.** Citeproc implements an author-in-text citation as *author-only* plus *suppress-author*. The author-only half renders the `names` element found in the style's `<citation>` layout. `compact-numeric.csl`'s citation layout contains only `citation-number`, so the author-only half renders empty and `@key` collapses to `[1]`. The same document under the default `chicago-author-date` style renders `Smith et al. (2020)` correctly, so pandoc is not the limitation — the style is.

**Locators die the same way.** The citation layout emits no `label`/`locator`, so `[@key, p. 5]` and `@key [p. 5]` both render as `[1]` with the locator discarded.

**Existing pipeline.** `publish.py` runs `--lua-filter cite-split.lua` (splits multi-key citations so each reference gets its own bracket) → `--csl compact-numeric.csl --citeproc` → `--lua-filter rq-filter.lua` (post-citeproc, re-serializes research-question list items). Three output tiers share the chain: typst, LaTeX, docx.

**Hard constraints.** User-side code is Python ≥ 3.11 stdlib only, so nothing may be added to the Python dependency surface; a pandoc Lua filter adds none. `shared/guidelines/guidelines.md` is the single source for guidance prose and is materialized into four skills by `scripts/sync_shared.py`.

## Goals / Non-Goals

**Goals:**

- One implementation path that serves all three output tiers identically.
- The in-text author label is a function of the reference entry, so it cannot drift from the bibliography.
- `[@key]` output is byte-identical to today's, so existing fixtures and expected outputs do not churn.

**Non-Goals:**

- Sentence-initial capitalization of lowercase surname particles (`van der Aalst` → `Van der Aalst`). A pre-citeproc filter sees the citation but not cheaply its sentence position. Deferred; the lowercase form is acceptable in English prose.
- Changing how the raw markdown source reads. `@key` stays visible as `@key` in an unbuilt hand-in, exactly as `[@key]` does.
- Any change to the bibliography's own name formatting (`et-al-min=6`, initials, `name-as-sort-order`). That is a separate concern from the in-text label and stays as shipped.

## Decisions

### Expand author-in-text citations in a Lua filter before citeproc

The filter reads `meta.references`, builds a key → author-label map, and rewrites every `Cite` whose *first* citation is author-in-text into `Str(label .. U+00A0)` followed by the same `Cite` with that citation flipped to normal mode. Citeproc then numbers it like any other.

The trigger is the first citation's mode, not a single-citation guard. Pandoc parses `@a [see @b]` into **one** `Cite` holding two citations, `[AuthorInText, NormalCitation]` — verified in the AST. A `#citations == 1` guard would therefore skip that form and leave it rendering nameless, which is the defect being fixed. Handling it needs nothing extra and produces `Smith et al. [1] [see also 2]`.

*Alternatives considered.*

**Author names in the CSL `<citation>` layout.** Tested: `[@key]` becomes `Smith et al. [1]` and `@key` becomes `Smith et al. ; [1]` — the composite delimiter leaks into the output. It also inverts the defaults, making `[-@key]` the only way to get a bare `[1]`, which would force a relearn across every skill, guideline, and fixture. Rejected on both counts.

**CSL 1.0.2 `<intext>` element.** This is the standards-track answer to exactly this problem. Tested: pandoc 3.10 ignores it — output unchanged. Rejected as non-functional.

**Author types the name: `Smith et al. [@smith2020]`.** Zero machinery, but the name is hand-copied, so it drifts when a reference is edited, and the writing skill is a language model that will get the et-al threshold wrong. It would also force `@key` to be banned outright, since it would otherwise keep misrendering silently. Rejected.

### Two filter passes in one file

Pandoc applies a filter's `Meta` function *after* its inline functions, so a single-pass filter that populates the name map in `Meta` and consumes it in `Cite` sees an empty map — verified by a prototype that produced no names at all. The filter therefore returns a list of two filter tables: `{ Meta = collect }` then `{ Cite = expand }`. This is a pandoc semantic, not a preference; the file needs a comment saying so or it will be "simplified" back into one pass.

### Extend the CSL citation layout with a locator group

The citation layout becomes a group of `citation-number` and a locator group (`label` short form plus `locator`), delimited by a comma, with the brackets kept as the layout's prefix/suffix. Verified output: `[1, p. 5]`, and `[1]` unchanged when no locator is present. `collapse="citation-number"` is retained and still collapses runs.

### Label rules

One author → surname; two → surname *and* surname; three or more → surname *et al.* Non-dropping particles are prepended to the surname; a `literal` author name is used verbatim. Fallback chain author → editor (with `(ed.)` / `(Hrsg.)`) → quoted title. `lang` selects the conjunction only; `et al.` stays Latin, matching computer-science convention and the existing CSL, which hardcodes the `et-al` term for the English locale.

### Non-breaking space, emitted as U+00A0

Verified through the typst writer, which converts it to typst's own `~`. Nothing writer-specific is needed.

### Filter order: author-intext before cite-split

Load-bearing, not cosmetic. The suffix form `@a [see @b]` reaches the chain as one two-citation `Cite`; `author-intext` emits the label and hands that `Cite` on, and `cite-split` then splits it so each reference gets its own bracket — yielding `Smith et al. [1] [see also 2]`. Reversing the order would split first, leaving `author-intext` a bare single-citation `Cite` and dropping the suffix's association. Both must still run before citeproc.

## Risks / Trade-offs

- **`rq-filter.lua` runs post-citeproc and re-serializes research-question list items, which previously broke citations inside them (commit a8127ef).** → By the time `rq-filter` runs, an expanded label is ordinary text and the citation is already resolved, so it is strictly less fragile than the case that broke before. The new regression test covers an author-in-text citation inside a research-question item to keep it that way.
- **The CSL citation-layout change touches every rendered citation.** → Locator-free citations were verified byte-identical (`[1]`, and collapsed runs unchanged). The test asserts both the unchanged and the new form.
- **A model writing prose may overuse the author-in-text form, turning fluency into noise.** → Addressed by rule rather than by a cap: the author-as-subject rule in the guidance is judgeable sentence-by-sentence by the review skill. A density cap was considered and rejected, since a legitimate related-work section names many authors in a row.
- **Two shipped fixtures already use `@key` and will change rendered output.** → Intended; that is the defect being fixed. Both cite authored references, so `check.py`'s new warning does not fire and the `expected.json` oracles should be unaffected — to be confirmed, not assumed.
- **The label logic partially duplicates name formatting that CSL already knows how to do.** → Accepted. The CSL route was tested and produces wrong output; a ~60-line Lua function with a pinned test suite is the cheaper correct path.
