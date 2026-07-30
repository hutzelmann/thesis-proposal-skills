## 1. Publish pipeline

- [x] 1.1 Add `skills/proposal-publish/templates/author-intext.lua`: a two-pass filter returning `{ Meta = collect }` then `{ Cite = expand }`, with a comment stating why one pass cannot work (pandoc applies `Meta` after inlines)
- [x] 1.2 In `collect`, read `lang` and build the key → author-label map from `meta.references`: surname with non-dropping particle, `literal` names verbatim, one/two/three-or-more forms, `and`/`und` by language, `et al.` unlocalized
- [x] 1.3 In `collect`, add the fallback chain: author → editor with `(ed.)` / `(Hrsg.)` → title in quotation marks
- [x] 1.4 In `expand`, rewrite every `Cite` whose first citation is author-in-text into the label, U+00A0, and the same `Cite` with that citation flipped to normal mode; leave all other `Cite` elements untouched
- [x] 1.5 Extend the `<citation>` layout in `skills/proposal-publish/templates/compact-numeric.csl` with a locator group (`label` short form plus `locator`), keeping the brackets as layout prefix/suffix and `collapse="citation-number"`
- [x] 1.6 Insert `--lua-filter author-intext.lua` into the chain in `skills/proposal-publish/scripts/publish.py` ahead of `cite-split.lua`, with a comment noting the order is load-bearing for the suffix form
- [x] 1.7 Update `skills/proposal-publish/SKILL.md` where it describes the filter chain

## 2. Guidance

- [x] 2.1 Add the citation-form rule to `shared/guidelines/guidelines.md`: author-in-text only where the cited authors are the sentence's grammatical subject or agent, bracketed where the citation is evidence; never hand-type an author name next to a bracketed citation
- [x] 2.2 Document the rendered contract of each syntax in the same place, so a writer knows what each form produces
- [x] 2.3 Run `python3 scripts/sync_shared.py` and confirm `--check` is clean

## 3. Check skill

- [x] 3.1 Extend the metadata extraction in `skills/proposal-check/scripts/check.py` to record, per reference id, whether an `author` or `editor` key is present — narrow extraction only, no general YAML parsing
- [x] 3.2 Distinguish author-in-text from bracketed occurrences in the existing citation scan, keeping the current key-consistency behavior unchanged
- [x] 3.3 Emit a warning for each author-in-text citation of a reference declaring neither author nor editor, naming the key and line and suggesting the bracketed form
- [x] 3.4 Update `skills/proposal-check/SKILL.md`'s check inventory

## 4. Tests

- [x] 4.1 Add `tests/unit/test_author_intext.py` following the pattern of `tests/unit/test_rq_filter_citations.py`: real filter chain under pandoc, `skipif` when pandoc is absent
- [x] 4.2 Cover the label forms — one, two, three, and six authors; `literal` author; non-dropping particle; editor-only; title-only — in English
- [x] 4.3 Cover `lang: de`: `und` for two authors, `et al.` still Latin, `(Hrsg.)` for editor-only
- [x] 4.4 Assert `[@key]` renders bare and collapsed runs are unchanged, so the CSL edit is proven non-regressive
- [x] 4.5 Cover locators in both syntaxes, and the suffix form `@a [see also @b]` through the full chain including `cite-split.lua`
- [x] 4.6 Cover an author-in-text citation inside a research-question list item, so the `rq-filter.lua` interaction stays covered
- [x] 4.7 Assert the non-breaking space survives the typst writer
- [x] 4.8 Add unit tests for the two new check behaviors: warning on an authorless author-in-text citation, silence on editor-only and on bracketed citations of authorless references
- [x] 4.9 Add or extend a fixture exercising both syntaxes and re-verify every `expected.json` oracle against `check.py`

## 5. Verification

- [x] 5.1 `uv run pytest` green
- [x] 5.2 `uv run ruff check .` clean
- [x] 5.3 `python3 scripts/sync_shared.py --check` clean
- [x] 5.4 `openspec validate --all --strict` passes
- [x] 5.5 Build one real fixture proposal through `publish.py` and read the PDF to confirm both citation forms and a locator render as specified
