# Title-as-H1 proposal format

## Why

A proposal's title and subtitle live only in the trailing YAML metadata block, so the one thing a reader wants first is the last thing in the file, and the body carries five H1 headings with no document title above them. Raw-markdown readability is a real use: proposals are read in editors, diffs, and forwarded files long before they are built. Moving the title to a leading `# ` line — the file's only H1 — with the subtitle directly beneath it makes the file read like the document it is, and shrinking the metadata block to the bibliography database alone removes the last reason to scroll to the footer.

## What Changes

- **BREAKING** — new single-file format (all points are one contract):
  - Line 1 is `# <title>`, the file's only H1 and its first content line. It is the sole title source and MAY carry a `[TODO: …]` marker.
  - The first body block after it is the subtitle: one paragraph wrapped entirely in `*…*` emphasis, required, canonical wordings unchanged (`*Master's Thesis Proposal*`, `*Exposé zur Masterarbeit*`, …, TODO fallback).
  - The five canonical sections demote to H2; methodology subsections demote to H3.
  - The body ends with a required, empty, final `## References` (en) / `## Literatur` (de) section — the same titles publish injects today via `-M reference-section-title`, now in the source, rendered unnumbered, with the citeproc bibliography beneath it.
  - The trailing YAML metadata block carries exactly `references` (CSL-YAML). `title`, `subtitle`, and `lang` keys are flagged the way `author` already is; `author` and `lang` remain documented escape hatches for bare-pandoc users (set deliberately, finding expected).
  - Language is no longer declared: it is inferred deterministically (pure Python) — exact subtitle match against the workspace-resolved canonical wordings first, majority of canonical section titles as fallback, `language-undeterminable` finding (English messages) when neither decides.
- `proposal-check` gains guardrail rules: leading H1 must be the first content line and the only H1 (any block above it makes pandoc silently demote it to a paragraph — verified empirically); subtitle line present and emphasized; References section present, last, and empty; retired metadata keys flagged. The title heading is excluded from section, forbidden-pattern, and methodology heading scans. Old-format files produce ordinary findings; there is no migration tooling.
- `proposal-publish` adds `--shift-heading-level-by=-1` to the base pandoc command (byte-identical typst output verified), promotes the emphasized first paragraph to `subtitle` metadata via a new Lua filter, injects `-M lang=<inferred>`, and stops injecting `reference-section-title`.
- `proposal-troubleshoot`'s collector treats the title heading as proposal text, not structure: `structure`-level reports mask it, and `minimal`'s canonical-heading ratio excludes it — otherwise every structure-level bug report would disclose the student's unpublished thesis title.
- All ten skills' format prose, the shared guidelines, the import example, the ideate seed instruction, and the reverse/supervise fallbacks restate the new contract; mandates and pinned copies move together.
- All 31 fixture proposals migrate mechanically and every `expected.json` oracle is recalibrated; drift tests (`test_format_prose_drift`, pins, todo-filter and CI-command guards) retarget the new contract.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `proposal-file-format`: single-file format redefined — leading H1 title, emphasized subtitle paragraph, H2/H3 body levels, required closing References section, metadata block reduced to `references`, language inferred instead of declared, TODO-marker locations restated.
- `guidance-model`: checkable skeleton now anchored to the single leading H1 with sections at H2 and methodology subsections at H3.
- `skill-check`: title tells read the H1 line; new guardrails (leading-H1 position/uniqueness, subtitle shape, References section, retired metadata keys, language inference); title heading excluded from section/forbidden/methodology matching; old-format shapes named as diagnosable defects.
- `skill-publish`: title block sourced from the leading H1 via heading shift, subtitle promoted from the body, inferred `lang` injected, bibliography heading sourced from the body and unnumbered; sample workspace builds updated.
- `skill-write`: chosen title written to the H1 line; the no-TODO-in-headings rule scoped to section headings so the title H1 may carry its marker.
- `skill-ideate`: seed opens with `# <working title>`; metadata list and degree-level TODO rule restated for the subtitle paragraph.
- `skill-review`: the title judged as content is read from the leading H1, with heading markup still out of scope.
- `skill-troubleshoot`: graded-redaction boundary clarified — the title heading counts as proposal text, never as structure.

## Impact

- `skills/proposal-check/scripts/check.py` (canonical; regenerated into import/write/reverse/supervise via `scripts/sync_shared.py`) — parser, title rules, new guardrails, language inference.
- `skills/proposal-publish/scripts/publish.py`, `templates/proposal.typ`, new subtitle-promotion Lua filter, `scripts/ci_typst_build.sh` + its drift test.
- `skills/proposal-troubleshoot/scripts/collect.py` (own script, edited directly).
- All ten `SKILL.md` bodies; `shared/guidelines/guidelines.md` (re-synced into five skills' `references/`); `tests/unit/data/skill_mandates/` and `pinned_sentences/` in lockstep.
- 31 fixture proposals + oracles; inline fixtures across `tests/unit/`; `harness/l1_checks.py` title/provenance verdicts; `evals/evals.json` projections regenerated via `harness/eval_export.py`.
- `docs/demo/harvest.log` stays as a dated historical record of the retired format (note added; f19 provenance caveat in `tests/fixtures/README.md`).
- `structure.json` needs no data change (titles carry no level); the workspace-override surface is untouched.
