## 1. Contract tests (gate before rewrite)

- [x] 1.1 `tests/unit/test_skill_frontmatter.py`: name equals directory, `proposal-` prefix, ≤64 chars; frontmatter carries no keys outside `{name, description}`
- [x] 1.2 Description contract: ≤500 chars repo budget (format allows 1024), no first/second-person pronouns, contains both a what-clause and a "Use when" trigger clause
- [x] 1.3 Combined metadata of all skills ≤4500 chars, with the current total in the failure message so the next writer sees the headroom they are spending
- [x] 1.4 Body size guards: ≤500 lines (cited to the skill-authoring guidance) and ≤2× the suite median body, with the current median and ratios in a comment
- [x] 1.5 Owned-trigger table `tests/unit/data/trigger_terms.json` (`owned` map + `shared` list) seeded from the measured collisions
- [x] 1.6 Test that a non-owner using an owned term fails and names both skills and the term; that a term listed as shared is allowed; that every owner names an installed skill

## 2. Description rewrite

- [x] 2.1 `proposal-lit-search` (1/5 in the baseline): thin bibliography, "has anyone worked on it before", needing sources or papers
- [x] 2.2 `proposal-ideate` (3/6): "talk a topic through", "weigh whether it is worth pursuing", "does not know what to write about"
- [x] 2.3 `proposal-import` (4/5): Word, LaTeX, Overleaf, pasted text of an older proposal — not only "PDF"
- [x] 2.4 `proposal-publish` (5/6): something to email, print or hand over; "out of markdown" — not only "build a PDF"
- [x] 2.5 `proposal-check` and `proposal-review`: the supervisor-handoff collision — `check` drops the handoff clause and names `proposal-review` for content feedback; `review` takes the moment
- [x] 2.6 ~~Release the word "supervisor" from `proposal-customize` and `proposal-publish`~~ — superseded during implementation. Ownership is over *phrases*, not words: "supervisor" is listed as shared, because four skills legitimately need the noun and the collision is over the moment ("is it ready for the supervisor"). Both descriptions keep it.
- [x] 2.7 ~~German cues in six descriptions~~ — superseded. All six German cases passed in the baseline, so there is no measured gap; adding German phrases would spend always-loaded metadata against no evidence.
- [x] 2.8 Whole set re-read together: every description is still prose a skills.sh visitor can read, none became a keyword list

## 3. Verification

- [x] 3.1 `uv run poe test` green — the new contract passes on the rewritten descriptions
- [x] 3.2 Routing sweep re-run on sonnet with the baseline's flags; `docs/skill-routing.md` regenerated, carrying `supersedes: 51/60`
- [x] 3.3 Negatives still pass — no skill claims the non-proposal utterances
- [x] 3.4 Movement reported per skill, including the two skills that did not move and why (recorded in `harness/README.md`)
- [x] 3.5 `openspec validate --all --strict` green
