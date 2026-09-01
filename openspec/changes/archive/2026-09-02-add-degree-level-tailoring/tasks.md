# Tasks

## 1. Guidelines

- [x] 1.1 Add the `## Degree Level` section to `shared/guidelines/guidelines.md` after "Proposal Structure": framing sentence (everything else identical by design, provenance `docs/degree-level-sources.md`), the four dimensions in ~2 sentences each, the both-directions bar sentence, the Bachelor-phrasing rule (never a prohibition), and the no-justification statement (one methodology, the proposal as a whole is its support; fit is review judgement).
- [x] 1.2 Pin the both-directions bar sentence in `tests/unit/data/pinned_sentences/` following the existing file convention; confirm the pinned-sentence test discovers it.

## 2. Skill bodies

- [x] 2.1 proposal-ideate: add level steering to the Socratic/scoping guidance (Bachelor → bounded application/evaluation, group-derived topics level-appropriate; Master → push for the gap), body section only.
- [x] 2.2 proposal-write: contribution-close and RQ drafting honor the subtitle level; TODO subtitle → ask once at the contribution close, write the canonical subtitle on answer, proceed neutrally on decline.
- [x] 2.3 proposal-review: replace the generic "scope risks for the thesis level (Bachelor vs Master)" clause with the four lenses plus the fit lens; unknown level → neutral core plus one line.
- [x] 2.4 proposal-supervise: calibrate the letter bar (Master missing delta → always asked; Bachelor → never asked, stated novelty engaged); unknown level → neutral bar plus one student-facing line.
- [x] 2.5 proposal-lit-search: add the single self-contained literature-stance sentence; no reference wiring.

## 3. Propagation and docs

- [x] 3.1 Run `python3 scripts/sync_shared.py`; verify the five `references/guidelines.md` copies updated and no materialized block changed.
- [x] 3.2 Update `docs/degree-level-sources.md` "The design consequence": level read from the subtitle, surfacing as graded judgement in the five skills, never as structure; keep the workspace-override closing thought.

## 4. Verify

- [x] 4.1 `uv run poe test` green (header pattern, mandates, pinned sentences, sync drift, conform all pass); `openspec validate --all --strict` green.
- [x] 4.2 Adversarial wording check of the diff against the contract: no prohibition-shaped Bachelor phrasing, no justification requirement anywhere, no mandate or materialized-block edits, tailoring defers to guidelines rather than restating.
