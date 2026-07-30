## Why

The proposal file format promises two citation syntaxes — `[@key]` (bracketed) and `@key` (author-in-text) — but the publish pipeline renders both identically as a bare `[1]`. The author name silently disappears, so a sentence written as "@Duarte24Human show that human labeling improves precision" renders as "[1] show that human labeling improves precision", which is ungrammatical. Two shipped fixtures already contain this defect. Locators (`[@key, p. 5]`) are dropped by the same mechanism.

Author-in-text citations are the standard device for keeping prose fluent when the cited researchers are the subject of the sentence. Numeric-only citation forces every such sentence into an awkward "[1] show that…" shape.

## What Changes

- Author-in-text citations (`@key`) render as `Smith et al. [1]` — the author label derived from the proposal's own `references` entries, never hand-typed. Bracketed citations (`[@key]`) keep rendering as bare `[1]`. Both forms coexist in one document.
- Author-label form by author count: one author `Smith`; two `Smith and Klein`; three or more `Smith et al.` The conjunction is localized for `lang: de` (`und`); `et al.` stays Latin, matching computer-science convention.
- References without an `author` fall back to `editor` with an `(ed.)` / `(Hrsg.)` marker, then to the quoted title. Publish never fails on this; the check skill warns instead.
- Locators render in both syntaxes: `[@key, p. 5]` → `[1, p. 5]`, `@key [p. 5]` → `Smith et al. [1, p. 5]`. Previously dropped entirely.
- The author label and its citation bracket are joined by a non-breaking space so they never split across a line break.
- Writing guidance gains the rule that decides between the two forms: use `@key` only when the cited authors are the grammatical subject or agent of the sentence; use `[@key]` when the citation is evidence attached to a claim.
- Author-in-text citations carrying a suffix that contains a further citation (`@key [see also @other]`) render as the author label, its own bracket, and the suffix bracket.
- The check skill gains one rule: a warning for `@key` pointing at a reference that declares neither an author nor an editor, since it renders as a quoted title inside the sentence.

No breaking changes: both syntaxes were already legal, and `[@key]` output is unchanged.

## Capabilities

### New Capabilities

None. This change fixes and extends existing capabilities.

### Modified Capabilities

- `skill-publish`: the citation-style requirement gains author-in-text rendering, the author-label form rules including German localization, the authorless fallback chain, and locator rendering.
- `proposal-file-format`: the citation-syntax requirement gains the rendered contract for each syntax — what `@key` and `[@key]` actually produce — so the promise is verifiable rather than nominal.
- `skill-write`: bilingual writing conventions gain the author-as-subject rule that selects between the two citation forms.
- `skill-check`: mechanical and warning-class checks gain the multi-key author-in-text error and the authorless author-in-text warning.

## Impact

- New `skills/proposal-publish/templates/author-intext.lua`, added to the filter chain in `skills/proposal-publish/scripts/publish.py` ahead of `cite-split.lua` and citeproc.
- `skills/proposal-publish/templates/compact-numeric.csl`: citation layout extended with a locator group.
- `shared/guidelines/guidelines.md` gains the citation-form rule; `scripts/sync_shared.py` re-materializes the generated copies in the write, review, customize, and ideate skills.
- `skills/proposal-check/scripts/check.py` gains two rules; fixture `expected.json` oracles are re-verified (the two fixtures that use `@key` cite authored references, so no new findings are expected).
- New L0 regression test mirroring `tests/unit/test_rq_filter_citations.py`: runs the real filter chain under pandoc, skipped when pandoc is absent.
- User-side constraint respected: the filter is Lua run by pandoc, and no Python dependency is added.
