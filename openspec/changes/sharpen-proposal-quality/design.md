# Design — sharpen-proposal-quality

## Context

See proposal.md — Why. Current state, verified: check.py reads no prose meaning; review renders findings but no verdict; write drafts "the best draft the material supports"; ideate converges on presence of contributions, not their concreteness; no skill carries a tone rule; `page_limit` is a documented override key nothing consumes. The header pattern (purpose / workflow line / mandate) is enforced by `tests/unit/test_skill_header_pattern.py` with pinned mandates under `tests/unit/data/skill_mandates/`.

## Goals / Non-Goals

**Goals**: install the five substance tests and the density rule as prose authority in `shared/guidelines/guidelines.md`; give every judgment surface (ideate convergence, write self-audit, review verdict) the same named tests; make "clean" honest; make tone uniform and test-enforced.

**Non-Goals**: no harness/eval work (follow-up change `prove-quality-gates`); no hard gates anywhere — the advisory philosophy stands; no new skill; no semantic rule encoded as structured data; no change to fixtures or `expected.json` oracles (check gains only a new warning class, and fixtures are re-oracled only if a fixture actually overruns the limit).

## Decisions

1. **Voice block sits between workflow line and mandate (block 3 of 4).** The packaging spec forbids separating a mandate from the paragraph beneath it, so nothing can follow the mandate; before the purpose block it would lead the rendered page with agent-facing tone rules. Byte-identical across all eight files, enforced by extending `test_skill_header_pattern.py` (same mechanism as the workflow line — no per-skill pinned copies needed).
2. **Voice block wording** (exact bytes fixed at implementation, ~2 sentences): neutral and constructive; never praise the user or their material; never compliment your own output; chat messages short and precise, findings stated plainly. It constrains chat conduct only — deliberately no operational rules, so it cannot collide with any mandate.
3. **Page estimate lives in check.py, constants in structure.json.** `structure.json` gains `page_limit: 5` and `words_per_page: 500` (realistic for the rendered A4 template; the estimate is warning-labeled, so precision is not load-bearing). Words counted over body text only — metadata block and headings excluded — so references never inflate the estimate. Override merge reuses the existing TOML-block path that already handles `min_references`.
4. **Substance tests are one new guidelines section** ("Substance tests", after the research-questions rules), each test a bolded name plus one operational question — the same vocabulary review, write, and ideate cite. Density rule joins the existing writing-rules section. The five test names are prose, not structured data: the formalization boundary holds.
5. **check.py verdict line** appends its scope: `mechanically clean, N warnings — substance not judged; the review skill renders that verdict`. One-line change to the report footer plus SKILL.md wording; the "advisory, gates nothing" sentence stays.
6. **Review verdict is the file's first line** (`Verdict: …` in the proposal's language) and the chat summary's opener. Three fixed tiers; failed substance tests cited by name in the verdict sentence. No numeric scores.
7. **Write's density pass binds only its own prose.** Fresh drafts: delete filler before reporting. Refine mode: untouched sections get chat suggestions only — the surgical-edit rule wins. This keeps the pass from silently eating author content.
8. **Ideate genericity handling reuses existing machinery**: the aspect tracker gains a concreteness bar (specifics, not generalities), the swap test becomes a named Socratic move, and persistent genericity routes into the existing impasse ending. No new session states.
9. **Mandate churn minimized.** New rules land in body sections; a mandate is reworded only where its opening paragraph states the old behavior (review's output paragraph). Every touched mandate's pinned copy updates in the same change, per the enforcement spec.

## Risks / Trade-offs

- [Density pass deletes legitimate substance in fresh drafts] → rule scoped to sentences the skill itself can identify as thesis-unspecific; swap-test phrasing gives a concrete test, not a length target.
- [Swap-test move harasses hesitant-but-genuine students] → voiced once, Socratically; impasse still requires ~3 further contribution-free exchanges after it.
- [Page estimate wrong on German compounds / heavy citation text] → warning-labeled estimate, generous default, override available.
- [Voice block reads as boilerplate on skills.sh pages] → two sentences, placed after the workflow line where repetition across pages is already the pattern.
- [Fourth block breaks header test mid-implementation] → all eight files + test updated in one task; L0 gate runs at the end of the change, not per file.
- [Review verdict "no viable thesis core" discourages a salvageable idea] → verdict must state what would change it; ideation pointer mandatory.

## Migration Plan

Pure content/tooling change inside the repo: edit shared sources, run `scripts/sync_shared.py`, update tests, `uv run poe test`. No user-side migration; installed skills pick the change up at next publish (explicit-request only). Rollback = git revert of the change commit.

## Open Questions

None.
