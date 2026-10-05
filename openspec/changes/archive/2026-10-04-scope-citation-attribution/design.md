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

- A new helper splits the masked body into blocks, yielding `(sentence, line)` lists. A blank line or heading ends a block, a table row is a block of its own, and a list item starts one. For the repetition comparison of ladder step B, consecutive list items stay one block, so bullets do not hide repeats.
- Sentences are split at sentence punctuation **outside citation brackets**: a locator `[@key, S. 12]` never ends a sentence. The lines of a paragraph are joined first, so a hard-wrapped sentence stays one sentence. Abbreviations (et al., e.g., i.e., cf., vgl., z. B., d. h., u. a., S./p./pp. locators, Abb., Kap., Tab., Nr.) and German ordinals after an article or preposition ("im 2. Schritt") do not split.
- Within a block, a sentence is *attributed* if it carries a citation key, or if the previous sentence was attributed and this one opens with a back-reference cue. Any other sentence clears the state.
- A sentence fires only when it is unattributed and matches the existing result-verb or quantity logic.

**Cues are a closed, per-language set, and must open the sentence.** A cue may stand:
- first ("They …", "Ihre Auswertung …");
- after a single connective set off by a comma ("However, they …");
- after a preposition, as a possessive or "the authors" ("In their evaluation …", "According to the authors …", "Laut den Autoren …");
- in German verb-second order, as the subject after the finite verb ("Zudem zeigen sie …").

A cue in object position does not open a sentence. Any sentence containing a first-person pronoun is never a continuation.

The first cut matched the cue anywhere in the first three words. The adversarial review showed that this laundered own-work claims such as "We outperformed **their** baseline …" and "In **both** settings we …", which is why the rule is now positional.

| Language | Cues |
|---|---|
| English | they, their, its, it (unless an expletive follows: "It is/was/seems …"), both, these/both studies, the authors, these authors, the same study |
| German | sie, ihr/ihre/ihrem/ihren/ihrer/ihres, deren, dessen, sein/seine…, beide, diese/beide Studien, die/den/der Autoren (also Autorinnen, Autor:innen) |

A **reporting clause** that names the cited authors counts wherever it stands: "…, they report, …", "they find that …", "so die Autoren", "den Autoren zufolge".

The final run showed why both extensions are needed. A sonnet repair wrote "Most projects, **they report**, merge …", "**It** uses three features …" and "According to **these studies**, …". Each sentence broke the run under the positional cues alone, so the correctly cued sentence that followed warned. That false positive would push the writer back to re-citing, the defect this rule exists to remove. With the extensions, none of the 60 measured drafts carries a hindsight warning. The old check flagged 11 of them.

The German oblique cases are included so that "Laut den Autoren …" counts as attribution, mirroring English "According to the authors …".

Words deliberately excluded:

- **it / es**: expletive use ("It was shown", "Es zeigte sich") would launder unattributed claims.
- **every name a proposal gives the thesis itself**: this study, this work, diese Arbeit, and also **the study / die Studie / the approach**. The guidance prescribes "the study" as the thesis's third-person self-reference, so it cannot double as a back-reference. The first cut listed it; the review caught it.
- **generic "the X" ("the detector")**: unbounded, so it keeps the warning. The fix is "their detector".

**Alternatives considered:**

- Paragraph inheritance (any sentence after a citation is attributed) misses real leaks in paragraphs that cite something, and contradicts the scope rule.
- One-step inheritance without a cue is arbitrary at the third sentence.
- An open noun-phrase recogniser would be fragile parsing in a stdlib-only script.

**Why a list in code is not a formalization-boundary breach.** The cue set lives in `check.py` beside `RESULT_VERBS` and `CHANGE_WORDS`, as matching vocabulary for a warning that admits false positives. It is not structured guidance data. The guidance spec states that the cue list is not encoded in `structure.json`.

The warning message adds the cue as a fix: "attribute the result — cite it, or continue a cited sentence with 'they'/'their …' — or write it as a plan".

### D3 — One citation-key helper in check.py

The key pattern `(?<![\w.\\])@([A-Za-z][\w:.-]*)`, with trailing punctuation stripping, becomes a module-level compiled pattern plus a `citation_keys(text) -> set[str]` helper. `scan_citations`, the hindsight rule and the block walk use it. Behaviour of `scan_citations` is unchanged; existing fixture oracles prove that.

### D4 — L1 verdicts share the check script's splitting

New in `l1_checks.py`:

- `citation_blocks(text)`: the check script's `split_proposal` and `prose_blocks(body, list_items_break=False)`, annotated with each sentence's citation keys.
- `repeated_citation_runs(text)`: returns `(line, keys)` for every adjacent pair in a block with an identical non-empty key set.
- `verdict_citation_runs(text)`: the verdict for the write task.
- `verdict_citation_repair(before, after)`: the repair verdict, which adds "every key the input cites is still cited".
- `verdict_cited_draft` / `verdict_repaired_draft`: these add the existing draft verdict and are shared by both runners.

`l1_checks.py` loads the sync source `skills/proposal-check/scripts/check.py` by file path (`importlib`). The verdict and the `citation-repeated` warning a writer sees therefore share one implementation and cannot disagree about what a sentence is.

The first cut duplicated the splitting regexes and pinned them by shared inputs. The review showed that most alternatives were unpinned, which is why it was replaced. Both runners judge on the host, where the script is a file away. An L0 test asserts that the loaded module is the shipped file.

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
   - L1 repetition or L2 overcitation fails → **B**: `citation-repeated` warning in `check.py`. It fires on an identical key set on adjacent sentences in a block, is warning-class, quotes the line, and needs f27 oracle recalibration. The deltas are a new skill-check requirement ("Repeated citations reported as a warning") and an amendment to this change's guidance-model "Citation scope". "Formalization boundary" stays untouched, because no structured guidance data is added. Then re-measure L1.
   - L2 scope or synthesis fails on sonnet → **C**: a drafting clause in `proposal-write`'s SKILL.md (draft prior work concept-first; cite once per continuous use), pinned under `tests/unit/data/pinned_sentences/`, with a skill-write delta. Then re-measure.
   - After C there is no further escalation. The pipeline stops with the measurement as it stands.

   Ladder steps change specs, so they enter this change through `openspec-update-change` before implementation. The ladder is sequential (A → B → C, as agreed in the interview). The routing only decides where it enters: a repetition that survives B goes on to C.

   **Outcome after stage A: B triggered.** `write_repair_citations` reached L1 1/3 on sonnet, and each failure was one genuine same-key repeat. Haiku reached 0/3 there, but every failure was a structurally broken draft, not a citation defect, so neither B nor C addresses it; it is reported (see `measurement.md`). One caveat governs what B can achieve. `proposal-write` treats only check *errors* as binding ("Fix every error it reports"); warnings are reported, not mandated. Whether a warning changes a polishing pass is therefore exactly what the re-measurement shows.

**Outcome after B: C triggered.** Sonnet repair became solid (3/3), but haiku's one structurally intact repair still left seven repeats. The warning does not reach a model that treats warnings as optional. C therefore does two things in `proposal-write`'s SKILL.md, each pinned:

- a drafting clause among the strong defaults (prior work concept-first; cite once per continuous use, carried on in words; cite again on the guidance's full set of triggers);
- a paragraph in "Verify before you report" that makes `citation-repeated` binding in text the pass wrote or was asked to improve, resolved by restructuring and never by deletion. In untouched sections the findings become suggestions, as the density pass does, and the warning yields to a workspace that requires per-sentence citation.

Both land with a skill-write delta ("Citation scope in writing passes").

**Review fixes after C.** The pre-commit adversarial review (task 6.1: four dimensions, each finding verified by a refuting agent) confirmed eleven findings:

- the cue window laundered own-work claims;
- "the study" doubled as a cue;
- locators, ordinals and wrapped lines split sentences;
- the lone-letter rule merged a sentence ending in a variable;
- the write clause said "only" and sat under "non-negotiable";
- the exported L1 wording overstated the verdict;
- the duplicated splitter was mostly unpinned;
- two recording gaps (no "et al." test, no workspace paths).

All are fixed (see D2, D4, Risks). They change shipped behaviour, so the dev runs were repeated on the fixed state. That final state is the one L2 grades.

## Risks / Trade-offs

- [The cue set has false negatives and positives] → Warning-class only, false positives acknowledged by spec. Excluding it/es and the thesis's own names chooses missed attribution over laundered claims; the fix the warning names ("their …") is always available.
- [A referential "it" after a cited sentence is read as the cited work] → Accepted. "It outperformed their scheduler by 20 %" passes as attributed. Excluding "it" made every "It uses …" continuation break the run and warn the cued sentence after it, a false positive in measured output. Expletive "It is/was …" stays excluded.
- [German `sie` is also the pronoun for feminine nouns, and the thesis's own work often is one: die Arbeit, die Analyse] → Accepted. "Sie erreichte 95 %" after a sentence whose subject is the thesis's own analysis passes as attributed. English "they" has the same ambiguity for plural nouns. Dropping bare `sie` would refuse the most natural German continuation. The precondition, a cited sentence whose subject is the thesis's own feminine noun, is narrow.
- [A writing pass that saves a stray or backup `.md` beside an in-place repair is judged on the new file (`select_draft` prefers new files)] → Accepted and unobserved. The write skill keeps the filename. Reading `ws/<proposal>` directly would misjudge a model that writes its revision to a new file instead.
- [A program requires a citation on every sentence] → The write skill places the citation-scope drafting rule among its strong defaults that a workspace `guidelines.md` may override, and the binding warning yields to such a workspace. The first cut had put it under "non-negotiable"; the review caught it.
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
