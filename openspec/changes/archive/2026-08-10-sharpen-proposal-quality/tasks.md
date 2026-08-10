# Tasks — sharpen-proposal-quality

## 1. Shared guidance sources

- [x] 1.1 Add "Substance tests" section to `shared/guidelines/guidelines.md`: five bolded test names (delta, falsifiability, swap, method-fit, executability), each with its one-line operational question; executability names objects of study, concrete evaluation, feasibility in stated months, and the first-week criterion
- [x] 1.2 Add the information-density rule to the writing-rules section: every sentence carries information essential to this thesis; scene-setting, truisms, restated-obvious are removable filler; deletion is the length instrument
- [x] 1.3 Add page-limit prose: default five pages, generous, warning-level, `page_limit` override; estimate-from-word-count caveat
- [x] 1.4 Add `page_limit: 5` and `words_per_page: 500` to `shared/structure.json` with a boundary comment (estimation constants, not semantic data)

## 2. check

- [x] 2.1 Implement estimated-pages warning in `skills/proposal-check/scripts/check.py`: body-word count (metadata block and headings excluded) / `words_per_page`, judged against effective `page_limit` (TOML override-aware), warning names estimate + limit + estimate caveat
- [x] 2.2 Scope the verdict line: mechanically clean result states substance not judged, points to review; align `skills/proposal-check/SKILL.md` step text
- [x] 2.3 Unit tests: estimate math, override respected, warning (never error), clean-verdict wording

## 3. Voice block across all eight skills

- [x] 3.1 Fix the voice block's exact bytes (two sentences: no praise of user/material, no self-praise, neutral constructive, short precise messages, findings plain) and insert as block 3 (workflow line → voice → mandate) in all eight `skills/*/SKILL.md`
- [x] 3.2 Extend `tests/unit/test_skill_header_pattern.py`: four blocks, voice byte-identical across skills, order enforced
- [x] 3.3 Update AGENTS.md header-pattern description (three blocks → four)

## 4. write

- [x] 4.1 Add substance gate to `skills/proposal-write/SKILL.md`: hollow material → TODO or omission, never generic filler; closing report names thin sections, points to ideate/review
- [x] 4.2 Add binding density pass: fresh-draft filler deleted before reporting; refine mode reports untouched-section filler as suggestions only
- [x] 4.3 Update pinned mandate copy if the mandate paragraph changed

## 5. review

- [x] 5.1 Add three-tier verdict to `skills/proposal-review/SKILL.md`: first line of review file + chat opener; tiers ready / needs revision / no viable thesis core; failed substance tests cited by name; no-viable-core states what would change it; advisory
- [x] 5.2 Add concreteness/executability to judgment areas; sentence-level filler findings (quote or locate each)
- [x] 5.3 Update pinned mandate copy if the mandate paragraph changed

## 6. ideate

- [x] 6.1 Raise convergence bar in `skills/proposal-ideate/SKILL.md`: aspects count only with concrete student-contributed specifics; swap test as named Socratic move; genericity after swap test routes to impasse; no generated specifics
- [x] 6.2 Update pinned mandate copy if the mandate paragraph changed

## 7. Sync, verify, close

- [x] 7.1 Run `python3 scripts/sync_shared.py`; confirm generated copies (references/, vendored check.py) updated
- [x] 7.2 `uv run poe test` green (pytest + ruff + drift check); fix fallout, re-oracle any fixture that now trips the length warning
- [x] 7.3 `openspec validate --all --strict` green
- [x] 7.4 Adversarial verify workflow over the full diff; fix confirmed findings
