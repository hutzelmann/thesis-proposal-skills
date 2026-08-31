# Tasks: title-as-H1 proposal format

## 1. Shared data and check script (source of truth first)

- [x] 1.1 `shared/structure.json`: add the canonical references-section titles ("References" / "Literatur") beside the section titles; no other schema change. Extend `shared/guidelines/guidelines.md` where the contract surfaces (title chapter: title lives in the leading `# ` line; anonymity paragraph re-checked; quality checklist bullet gains the leading H1 + subtitle + references section; references heading appears verbatim for the structure-drift test).
- [x] 1.2 `skills/proposal-check/scripts/check.py` — parsing: source the title from the leading `# ` line (first content line, only H1); parse the subtitle paragraph (`*…*` after the title); exclude the title heading from `head_texts`/`meth_heads` and from `rule_heading_style`'s early return; keep trailing-block parsing for `references`.
- [x] 1.3 `check.py` — language inference: one pure function (subtitle exact match → section-title majority → undeterminable), used for message locale and title bounds; `language-undeterminable` finding.
- [x] 1.4 `check.py` — rules: retire `metadata-title-missing`; add the new rules from design decision 8 (title line missing/not-first/multiple H1, subtitle missing/not-emphasized, references section missing/not-last/not-empty, retired metadata keys `title`/`subtitle`/`lang` via the `author` mechanism, legacy-format document shape); update `RULE_IDS`; title tells now read the H1 (drop the block-scalar guard).
- [x] 1.5 L0 for 1.2–1.4: rewrite `tests/unit/test_check.py`, `test_check_rules.py`, `test_title_tells.py`, `test_timeline_section.py` inline fixtures to the new format; add tripped-and-passed cases for every new rule id; language-inference unit cases (en, de, TODO subtitle, undeterminable).

## 2. Publish pipeline

- [x] 2.1 `publish.py`: add `--shift-heading-level-by=-1` to `base`; replace `proposal_lang()` metadata extraction with the same deterministic inference (subtitle → section majority → en default + note) and inject `-M lang=<inferred>`; drop `-M reference-section-title`; read the references-headline wordings from the vendored `structure.json`.
- [x] 2.2 New `skills/proposal-publish/templates/subtitle-filter.lua` at the head of the filter chain: promote the emphasized first paragraph to `meta.subtitle`; mark the final References/Literatur heading unnumbered. Guard `proposal.typ` title line with `$if(title)$`.
- [x] 2.3 `scripts/ci_typst_build.sh` + `tests/unit/test_ci_typst_drift.py`: add the shift flag and the new filter to the restated command and assert both.
- [x] 2.4 L0 for 2.1–2.3: `test_publish.py` (inference cases, no doc-level `title:` in fixtures), `test_todo_filter.py` (new-format harness; title-marker-in-H1 numbered first; subtitle-marker pin kept), `test_export_matrix.py` fixtures on the new format; German build pins „…“ quotes + "Literatur"; single-bibliography-headline assertion.

## 3. Troubleshoot collector

- [x] 3.1 `skills/proposal-troubleshoot/scripts/collect.py`: mask the title heading at `structure` level (`# [title masked]`), exclude it from `minimal`'s canonical tally; update `tests/unit/test_troubleshoot_collect.py` (fixture + expectations, incl. the "2 of 3" ratio).

## 4. Fixtures and oracles

- [x] 4.1 Migrate all 31 fixture proposals mechanically (title → leading `# `, subtitle → `*…*`, drop `title:`/`subtitle:`/`lang:` keys, sections H1→H2, subsections H2→H3, append the closing references section). Special cases: f09 stays title-less; f15 keeps the glued-block + author guardrails re-expressed; f21's bad title verbatim into the H1 (keep `harness/rubrics/title_alarm.txt` in sync); w01 seed shape; w06/s01/g01 untouched.
- [x] 4.2 Recalibrate every `expected.json` against the updated check (`test_fixture_oracles.py` green); update `tests/fixtures/README.md` rows (f09, f15) and add the f19 provenance caveat.
- [x] 4.3 `docs/demo/harvest.log`: add a dated note that it records the retired pre-H1 format.

## 5. Skill prose, mandates, pins

- [x] 5.1 Reword format prose in all affected `SKILL.md` bodies: write (mandate + lines 25/43/61), import (mandate + example + TODO-key rules + mapping), ideate (seed opens with `# <working title>`, subtitle paragraph, line 99 metadata list), reverse (target shape + fallback essentials), check (title source), review (mandate title-location sentence), publish (build docs, sample workspace builds with shift flag + format note, line 33 marker sentence), supervise (shape recognizer + inline fallback), customize (title-H1 exempt from section lists), troubleshoot (redaction description).
- [x] 5.2 Update pinned copies in the same commit: `tests/unit/data/skill_mandates/*.txt` and affected `tests/unit/data/pinned_sentences/*`; keep header-pattern block order (sync anchors are positional).
- [x] 5.3 `tests/unit/test_format_prose_drift.py`: contract becomes leading-H1 + subtitle paragraph + `references` key + trailing/blank-line; recalibrate the describer-discovery threshold.

## 6. Harness and projections

- [x] 6.1 `harness/l1_checks.py`: title extraction from the leading H1 (`title_line()`, `verdict_title_alarm`, TODO shapes, seed completeness, provenance term source); reword messages; update `tests/unit/test_harness_helpers.py` inline fixtures (fix the no-op replace at line 262).
- [x] 6.2 Regenerate vendored copies (`python3 scripts/sync_shared.py`) and eval projections (`uv run python harness/eval_export.py`); `test_eval_projection.py` and drift checks green.

## 7. Verify and close

- [x] 7.1 `uv run poe test` and `uv run poe cov` green; `openspec validate --all --strict` green.
- [x] 7.2 End-to-end render sanity: build f00 (en) and f12 (de) through the typst tier; confirm title block, subtitle, unnumbered bibliography headline under the body heading, German locale — compare against pre-change builds.
