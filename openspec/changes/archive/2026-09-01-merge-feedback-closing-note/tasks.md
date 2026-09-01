## 1. Gates first

- [x] 1.1 Add `tests/unit/test_closing_note.py`: for each of the `## English` / `## Deutsch` sections of `skills/proposal-supervise/references/closing-note.md`, assert exactly one paragraph, no line starting with `>`, `#`, `-`, `*`, or a digit-dot list marker, and no `*`/`_` emphasis markers anywhere in the section; assert the English section opens with `Note:`, the German section opens with `Hinweis:` and contains `Rückmeldung`. Failures name the section and the offending construct.
- [x] 1.2 Confirm 1.1 fails against the current `getting-started.md` content (blockquote + bold run-in), so the guard is known to bite before the content is fixed.

## 2. Shared snippet

- [x] 2.1 `git mv skills/proposal-supervise/references/getting-started.md skills/proposal-supervise/references/closing-note.md`.
- [x] 2.2 Rewrite the file: header prose describing the closing note (one paragraph per language, quoted whole into the feedback, markup-free because the professor pastes into a plain-text channel), then the two sections with the agreed English and German paragraphs — `Note:` / `Hinweis:` run-in, availability bridge, repository URL, no markup.
- [x] 2.3 Re-run 1.1 and `uv run pytest tests/unit/test_bilingual_terminology.py`: both green.

## 3. Skill body

- [x] 3.1 In `skills/proposal-supervise/SKILL.md`, collapse curated-feedback items 5 (**Disclosure**) and 6 (**Getting started**) into one item: close with the language-matching section of `references/closing-note.md`, quoted verbatim, unmodified, as the feedback's last paragraph.
- [x] 3.2 Verify the renumbering leaves the starter-literature item and its ordering intact, and that no other line in `SKILL.md` still says `getting-started.md`.
- [x] 3.3 Run `uv run pytest tests/unit/test_skill_header_pattern.py tests/unit/test_skill_frontmatter.py tests/unit/test_report_offer.py` — the mandate, header blocks, and report offer are untouched and must stay green.

## 4. Harness verdict

- [x] 4.1 Add `verdict_supervise_closing(feedback, closing_sections)` to `harness/l1_checks.py`: pick the section matching the feedback's language, compare whitespace-normalized, return `(passed, explanation)` naming paraphrase vs wrong-language vs missing.
- [x] 4.2 Wire it into `verdict_supervise_feedback_contract` alongside the existing five verdicts.
- [x] 4.3 Add the scorer adapter in `harness/skill_evals.py` and the separate scorer entry for the supervise Inspect task.
- [x] 4.4 Pin the new scorer name in `tests/unit/test_eval_wiring.py`.
- [x] 4.5 Add L0 coverage in `tests/unit/test_supervise_verdicts.py`: verbatim pass, paraphrase fail, wrong-language fail, missing fail, and a differently-wrapped-but-identical text passing.

## 5. Specs

- [x] 5.1 Apply the `skill-supervise` delta to `openspec/specs/skill-supervise/spec.md`.
- [x] 5.2 Apply the `testing-harness` delta to `openspec/specs/testing-harness/spec.md` (modified supervise-coverage and bilingual-terminology requirements, added closing-note shape guard).
- [x] 5.3 `uv run poe specs` green.

## 6. Projection and full gate

- [x] 6.1 Regenerate `skills/proposal-supervise/evals/evals.json` via the harness exporter; never hand-edit the projection.
- [x] 6.2 `python3 scripts/sync_shared.py --check` clean (the renamed file is not a sync destination; confirm no drift was introduced).
- [x] 6.3 `uv run poe test` green — full chain, not `test-fast`.
- [x] 6.4 `uv run poe cov` at or above the floor.
- [x] 6.5 Grep the tree once more for `getting-started` and confirm the only remaining hits are `docs/getting-started.md` and the README links to it.
