# Design

## Context

See proposal.md for the motivation. The research behind the rule is summarised there. The decisions below were settled in a design interview before this change was created (2026-10-03): rule wording, cue-anchored hindsight, scenarios, pass bar, run plan, escalation ladder, synthesis gating, and the pipeline's stops.

Constraints that shape the approach:

- The rule lives once, in `shared/guidelines/guidelines.md` ("Literature and Citations"), and reaches the five skills that ship `references/guidelines.md` through `scripts/sync_shared.py`. `proposal-check`, `proposal-import` and `proposal-reverse` do not ship the guidelines. Their agents meet the rule only through check findings.
- `check.py` is user-side code (stdlib only, cross-platform) and is copied into four other skills. `rule_hindsight_leakage` iterates `prose_sentences`, which splits per line and never resets at paragraphs. The citation-key regex appears in `scan_citations` and, in a reduced form, in the hindsight rule. A third use is due here, so AGENTS.md's extract-at-three applies.
- The harness verdict module (`harness/l1_checks.py`) does not import `check.py`. Its runtime is Inspect and the dev runner, neither of which puts the skill scripts on the path.
- A parallel change (`require-supervise-verifier`) is in flight on `main` and edits `harness/claude_runner.py` and `harness/l1_checks.py`. This change is developed on the branch `scope-citation-attribution` in a worktree and merged later, so its harness edits stay additive and local to minimise conflicts.
- The git stash is shared with other worktrees and sessions, so the before/after measurement cannot use "stash the change".

## Goals / Non-Goals

**Goals:**

- The guidance states the attribution-scope rule with its *how*, and no mechanical check penalises following it.
- A measurement under conditions where the pattern can occur shows the shipped skills produce clean, professionally cited prose, with a baseline that shows whether the change mattered.

**Non-Goals:**

- Review and supervise feedback on a student's citation practice.
- Import's per-occurrence citation conversion (its faithfulness contract is unchanged; cleanup is the writing pass's job).
- A name-only citation form (the old `\citeauthor`). Continuation uses pronouns and noun phrases, and the typed-name ban stays.
- German model runs. German cue handling is covered by L0 tests.
- Workspace configurability of the rule. A program that mandates per-sentence citation is a workspace convention a supervisor states in prose, as with any other semantic rule.

## Decisions

### D1 — Rule text: APA plus German practice, not MLA

The consecutive-citation bullet becomes the four-part rule chosen in the interview:

1. Cite once per continuous use, opened by `@key`, with the attribution carried in words.
2. Cite again at a new paragraph, at a source switch, after an intervening own claim, and wherever a sentence would read as the thesis's own.
3. Never drop a citation without a cue (the Bauernopfer reason).
4. One source in most sentences of a paragraph means a summary, which goes to thematic restructuring (pointer to the contribution section).

**Alternatives considered:**

- MLA's rule (no new citation at a new paragraph unless another source intervened) yields fewer brackets. It contradicts APA §8.23 and every German guide surveyed, which hold that a citation never carries across a paragraph break.
- Only restoring the lost "use author-in-text first" sentence would leave the deletion failure unaddressed.

### D2 — Hindsight: paragraph-scoped, cue-anchored attribution runs

`rule_hindsight_leakage` walks prose **blocks** instead of a flat sentence stream.

- A new helper splits the masked body into blocks at blank lines, headings, list items and table rows, yielding `(sentence, line)` lists.
- Within a block, a sentence is *attributed* if it carries a citation key, or if the previous sentence was attributed and this one opens with a back-reference cue. Any other sentence clears the state.
- A sentence fires only when it is unattributed and matches the existing result-verb or quantity logic.

**Cues are a closed, per-language set, matched within the first three words.** The window admits a leading connective ("However, they …"), a preposition ("In their evaluation …"), and German verb-second order ("Zudem zeigen sie …").

| Language | Cues |
|---|---|
| English | they, their, both, the authors, these authors, the study, the same study, this approach, the approach |
| German | sie, ihr/ihre/ihrem/ihren/ihrer/ihres, deren, dessen, beide, die/den/der Autoren (also Autorinnen, Autor:innen), die/der Studie, dieser Ansatz |

The German oblique cases are included so that "Laut den Autoren …" counts as attribution, mirroring English "According to the authors …".

Words deliberately excluded:

- **it / es**: expletive use ("It was shown", "Es zeigte sich") would launder unattributed claims.
- **this study / diese Arbeit / this work**: proposals use them for the thesis itself.
- **generic "the X" ("the detector")**: unbounded, so it keeps the warning. The fix is "their detector".

**Alternatives considered:**

- Paragraph inheritance (any sentence after a citation is attributed) misses real leaks in paragraphs that cite something, and contradicts the scope rule.
- One-step inheritance without a cue is arbitrary at the third sentence.
- An open noun-phrase recogniser would be fragile parsing in a stdlib-only script.

**Why a list in code is not a formalization-boundary breach.** The cue set lives in `check.py` beside `RESULT_VERBS` and `CHANGE_WORDS`, as matching vocabulary for a warning that admits false positives. It is not structured guidance data. The guidance spec states that the cue list is not encoded in `structure.json`.

The warning message adds the cue as a fix: "attribute the result — cite it, or continue a cited sentence with 'they'/'their …' — or write it as a plan".

### D3 — One citation-key helper in check.py

The key pattern `(?<![\w.\\])@([A-Za-z][\w:.-]*)`, with trailing punctuation stripping, becomes a module-level compiled pattern plus a `citation_keys(text) -> set[str]` helper. `scan_citations`, the hindsight rule and the block walk use it. Behaviour of `scan_citations` is unchanged; existing fixture oracles prove that.

### D4 — L1 verdicts are self-contained in l1_checks.py

New in `l1_checks.py`:

- `citation_blocks(text)`: strips the trailing metadata block, splits into blocks with the same boundaries as D2, splits lines into sentences, and guards common abbreviations ("et al.", "e.g.", "i.e.", "cf.", "vs.", "z. B.", "d. h.", "vgl.") against false sentence ends.
- `repeated_citation_runs(text)`: returns `(line, keys)` for every adjacent pair in a block with an identical non-empty key set.
- `verdict_citation_runs(text)`: the verdict for the write task.
- `verdict_citation_repair(before, after)`: the repair verdict, which adds "every key the input cites is still cited".

The splitting is duplicated from `check.py`'s semantics rather than imported, because the harness runtime cannot import skill scripts. The duplication is two short regexes, documented as mirroring D2. L0 tests pin both on shared crafted inputs, so drift shows up as a failing test.

### D5 — Fixtures

Both fixtures are synthetic, use fresh topics unrelated to the illustrative proposal, and use fake DOIs in the `10.xxxx/…` style of f26.

- **`w08-rich-seed`**: an ideate-style seed (Idea Notes, candidate RQ directions, Literature Anchors) with eleven references. The anchors give one central source three or four distinct findings in note form. That is the material from which a writer produces `[@k]. [@k]. [@k].` or a one-source paragraph. Its oracle records the seed's expected incomplete-seed check state, like w01.
- **`f27-citation-runs`**: a complete, check-clean proposal (all canonical sections, one methodology, timeline) carrying:
  - one key on four consecutive sentences of the introduction;
  - a two-key group repeated on three adjacent sentences;
  - a contribution paragraph that summarises one source sentence by sentence.

  Result verbs ("reduced … by 40 %", "showed") sit in the repeated-citation sentences on purpose. Smoothing them with cues is the case where the current hindsight rule pushes the writer back to repetition, so the baseline measures exactly the defect D2 removes. The oracle records the check state; the pattern itself has no mechanical finding until and unless ladder step B lands.

### D6 — Scenarios and tasks

**Dev runner** (`harness/claude_runner.py`) gets two scenarios:

- `write_rich_seed`: draft from w08. Judged by `verdict_draft` (structural completeness, via `select_draft`) and `verdict_citation_runs`.
- `write_repair_citations`: writing pass over f27. Judged by `verdict_citation_repair` and `verdict_draft`. The request mirrors `write_offtopic_reference`: no questions possible, decide and report.

Dispatch goes through a small table keyed by scenario name, so `verdict()` does not grow past the complexity cap.

**Inspect** (`harness/skill_evals.py`) gets two tasks with the same staging, each with three scorers:

| Scorer | Kind |
|---|---|
| `<task>_l1` | L1 verdict |
| `<task>_l2_citation_scope` | model-graded |
| `<task>_l2_synthesis` | model-graded |

- One new rubric, `harness/rubrics/citation_practice.txt`, with per-scorer criteria in `CRITERIA`.
- The `proposal-write` `evals/evals.json` projection is regenerated.
- `test_eval_wiring.py` learns the new scorer names.
- The tasks are not added to the default matrix. They join the registry's `extended` set, which holds on-demand probes that run through `--tasks`, because they measure one guidance rule rather than a model's general support for a skill. The registry-coverage test requires every Inspect task to be accounted for somewhere.

### D7 — Measurement protocol (recorded in `measurement.md` in this change)

1. **Instruments commit.** Fixtures, verdicts, scenarios, tasks and rubric land as the first commit on the branch, with no guidance or check behaviour change.
2. **Baseline.** Dev runner (subscription): sonnet and haiku × both scenarios × 3 runs, on the instruments commit. This is the before state, measured without stashing.
3. **Stage A commit.** Rule text, hindsight change, sync, tests.
4. **After.** Same 12 dev runs.
5. **L2.** Inspect, after-state only: sonnet and haiku × 2 tasks × 2 epochs. The cost gate shows the estimate and waits for approval (pipeline stop 1).
6. **Bar.**
   - L1 cell solid (3/3) on both models.
   - L2 citation-scope passes on both epochs, both models.
   - L2 synthesis passes on both epochs for sonnet; reported for haiku.
   - 2–3 before/after paragraphs go to the user for the final "professional" call (pipeline stop 2, before archive and commit).
7. **Ladder, routed by the failing criterion.**
   - L1 repetition or L2 overcitation fails → **B**: `citation-repeated` warning in `check.py`. It fires on an identical key set on adjacent sentences in a block, is warning-class, quotes the line, and needs f27 oracle recalibration plus deltas for skill-check "Warning-class pattern checks" and guidance-model "Formalization boundary". Then re-measure L1.
   - L2 scope or synthesis fails on sonnet → **C**: a drafting clause in `proposal-write`'s SKILL.md (draft prior work concept-first; cite once per continuous use), pinned under `tests/unit/data/pinned_sentences/`, with a skill-write delta. Then re-measure.
   - After C there is no further escalation. The pipeline stops with the measurement as it stands.

   Ladder steps change specs, so they enter this change through `openspec-update-change` before implementation.

## Risks / Trade-offs

- [The cue set has false negatives and positives] → Warning-class only, false positives acknowledged by spec. Excluding it/es and "this study" chooses missed attribution over laundered claims; the fix the warning names ("their …") is always available.
- [German verb-second order defeats an opening-only cue] → The three-word window covers "Zudem zeigen sie" and "In ihrer Auswertung". German behaviour is L0-tested, not model-measured.
- [Duplicated splitting in harness and check drifts] → Shared crafted inputs in L0 tests for both.
- [The repair task rewards keeping every key, but a writer could legitimately drop a reference] → f27 is built so that every reference supports a claim, so dropping one is never correct here (stated in its oracle).
- [Baseline and after differ in more than the change] → Same scenarios, models, runner, and host version; only the instruments-vs-stage-A commit differs. Host-version drift is recorded in `measurement.md`.
- [Haiku fails the synthesis bar regardless] → Reported, not gating (interview decision); consistent with the 2026-08-10 substance bars.
- [Merge conflict with `require-supervise-verifier` in the harness] → Additive edits in separate functions and table entries; after merging, re-run `python3 scripts/sync_shared.py` and `uv run poe test`.

## Migration Plan

- Develop on the branch in the worktree.
- Commit order: the instruments commit, then stage A (and ladder steps if triggered).
- After the user's review at stop 2: archive the change, commit, merge into `main` (re-sync generated copies after the merge), and no push.
- Rollback is reverting the merge. No workspace or file-format migration is involved.
