# Design: title-as-H1 proposal format

## Context

See proposal.md — Why. Current mechanics that constrain the approach:

- `check.py` already matches sections by exact text at any heading level (`headings()` is level-agnostic, `section_text()` is relative), so demotion to H2/H3 costs nothing there. The whole cost sits in title sourcing (`split_proposal` → `meta.title` → `rule_title`), in excluding the new title heading from `head_texts`/`meth_heads`, and in new guardrails.
- The publish pipeline builds via `pandoc_command()` in `publish.py`; filter chain order is load-bearing. Empirically verified (pandoc 3.10, repo templates): adding exactly `--shift-heading-level-by=-1` to the `base` list reproduces today's typst output byte-identically for a body with a lone leading H1 and H2 sections, promotes the H1 (first block only) into `meta.title` including a `[TODO: …]` marker, and citeproc inserts its bibliography at the matching level. The single load-bearing precondition: the H1 must be the file's first block, else pandoc silently demotes it to a paragraph — hence the first-content-line guardrail.
- The bibliography headline is injected today via `-M reference-section-title=` (`publish.py:142,206`); the body's new closing `## References`/`## Literatur` replaces the injection.
- `collect.py` (troubleshoot) prints headings verbatim at `structure` level and tallies canonical headings at `minimal` — the title heading must be masked/excluded (privacy).
- Sync machinery: `check.py` + `structure.json` + `guidelines.md` are vendored into sibling skills by `scripts/sync_shared.py` (guidelines into five skills, incl. review and customize). Mandates and pinned sentences are byte-pinned under `tests/unit/data/`.

## Goals / Non-Goals

**Goals**
- Raw-markdown readability: the file reads top-down as a document (title, subtitle, sections, bibliography marker).
- Rendered output unchanged: PDFs, docx, and handout byte-equivalent to today for equivalent content.
- One source of truth per fact: title in the H1, subtitle in the emphasized paragraph, language inferred, bibliography in the metadata block.

**Non-Goals**
- No migration tooling and no dual-format support: old-format files get findings, nothing rewrites them automatically.
- No `structure.json` schema change: canonical titles carry no level field; levels are contract prose + check logic (formalization boundary holds).
- No workspace-override surface change.

## Decisions

1. **Subtitle = emphasized first paragraph, promoted by a Lua filter.** Alternatives: second YAML block after the title (native pandoc merge, but reintroduces YAML at the top); plain paragraph (indistinguishable from an opening sentence). `*…*` reads as a subtitle in every renderer and is mechanically unambiguous. Exactly `*…*` (not `_…_`): one spelling, mirroring the no-aliases override rule. Promotion: a new small `subtitle-filter.lua` placed at the head of the filter chain (before citeproc; todo-filter still sees `meta.subtitle` afterwards, so marker numbering keeps working). Pandoc applies `--shift-heading-level-by` before Lua filters, so the filter sees the title already in `meta.title` and the subtitle as the first body block.
2. **Language inference is one pure function in `check.py`, mirrored in `publish.py`.** Order: exact subtitle match against workspace-resolved canonical wordings → majority count of canonical section-title matches → undeterminable (finding, English messages). Deterministic Python, no model judgement. `publish.py` injects `-M lang=<inferred>` so pandoc/citeproc/typst localization is unchanged. Duplication between check.py and publish.py is accepted (publish must not import from a sibling skill — vendoring rule); both implementations are pinned by the same L0 cases.
3. **References heading in the body, unnumbered mechanically.** The build drops `-M reference-section-title` and instead marks the body's final References/Literatur heading unnumbered inside `subtitle-filter.lua` (same pass; it already walks meta + first blocks). No `{.unnumbered}` noise in source files. Canonical headline wordings move from `publish.py:143` into `structure.json` (they are canonical titles — same class as section titles; `reference_section_title()` reads them from the vendored copy).
4. **Retired keys flagged, not ignored.** `title`/`subtitle`/`lang` reuse the `author` mechanism: a finding names the key and the new location. Old-format files additionally get a named document-shape defect (title-in-metadata + H1 sections) so the cascade of section findings is explained.
5. **Title heading excluded from heading scans.** `build_context` drops the first heading iff it is the leading H1, before `head_texts`/`meth_heads` are formed; `rule_heading_style`'s early-return ignores it too. `rule_title` sources from that H1.
6. **collect.py masks the title.** `structure` level prints `# [title masked]`; `minimal`'s canonical ratio excludes the title heading from numerator and denominator.
7. **Fixtures migrate mechanically, oracles recalibrate by running check.** f09 stays title-less (missing-title finding), f15 keeps its glued-block guardrail with the title moved out, f21's bad title moves verbatim into the H1 (rubric `title_alarm.txt` stays in sync). `docs/demo/harvest.log` stays old-format as a dated historical record with a note; f19's provenance line in `tests/fixtures/README.md` gains the caveat.
8. **Rule ids:** `metadata-title-missing` is retired; new ids (`title-line-missing`, `title-not-first`, `multiple-h1`, `subtitle-missing`, `subtitle-not-emphasized`, `references-section-missing`, `references-section-not-last`, `references-section-not-empty`, `retired-metadata-key`, `language-undeterminable`, `legacy-format`) join `RULE_IDS`; exact names fixed at implementation, each with tripped-and-passed fixtures per testing-harness spec.

## Risks / Trade-offs

- [Non-initial H1 silently unbuilds the title] → first-content-line guardrail in check (error class), named document-shape defect, `$if(title)$` guard in `proposal.typ`.
- [Atomic-corpus break: 31 fixtures + oracles + check.py must move together] → single implementation task edits check.py first, then migrates fixtures, then recalibrates oracles; `poe test` gates the whole set at once.
- [Byte-parity claim covers shift only; subtitle promotion and lang injection are new] → `test_todo_filter`/`test_export_matrix` extended: build the new-format fixture and pin title block + subtitle + locale-sensitive strings; German fixture covers „…“ quotes and "Literatur".
- [Bare-pandoc users lose German locale without `lang`] → documented escape hatch: setting `lang:` deliberately is allowed, finding expected (same posture as `author`).
- [Mandate/pin lockstep] → every SKILL.md reword lands with its `skill_mandates`/`pinned_sentences` update in the same task; `eval_export` rerun after l1_checks docstring rewords (`test_eval_projection` gates).
- [Workspace builds receive a new shape with no fallback] → publish SKILL.md sample build definitions updated with the shift flag and a format note; w05 fixture migrated. Breaking, accepted: format is spec'd as one contract.

## Migration Plan

Repo-internal only (no user migration by decision): implement, migrate fixtures, recalibrate oracles, regenerate vendored copies + evals.json, `uv run poe test` green, archive. Rollback = revert the change commit; no persistent state outside git.

## Open Questions

None.
