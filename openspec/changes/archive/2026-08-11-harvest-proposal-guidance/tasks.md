## 1. Research questions

- [x] 1.1 In the Research Questions section of `shared/guidelines/guidelines.md`, state the goal-versus-question distinction and name the contribution section as where a construction goal belongs.
- [x] 1.2 Keep the existing analytical-phrasing bullet intact; the new text explains where the rejected phrasing goes, it does not restate the rejection.

## 2. Contribution section

- [x] 2.1 Add thematic-cluster, synthesis, and closing-gap guidance to the proposal-structure description of the contribution section.
- [x] 2.2 Tie the gap statement to the research questions explicitly.

## 3. Literature

- [x] 3.1 Add the standards-as-sources bullet to Literature and Citations, including the limit that a standard never establishes that an approach works.
- [x] 3.2 Reword the `min_references` bullet so the floor and the working range are visibly different things.

## 4. Methodology content

- [x] 4.1 Add the human-participants advisory block after the methodology bullets, marked explicitly as guidance rather than a required section or a check.
- [x] 4.2 Add the expectations-not-results and named-limitations rule, phrased so it does not conflict with expected-results remaining forbidden content.

## 5. Sync and verify

- [x] 5.1 Run `python3 scripts/sync_shared.py` and confirm the five generated `guidelines.md` copies update.
- [x] 5.2 Confirm the structured-data/prose drift test still passes — no canonical title changed.
- [x] 5.3 `uv run poe test` green.
- [x] 5.4 `openspec validate --all --strict` green.
