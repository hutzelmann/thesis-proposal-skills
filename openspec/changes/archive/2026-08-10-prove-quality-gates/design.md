# Design — prove-quality-gates

## Context

See proposal.md — Why. Harness today: 15 tasks in `harness/skill_evals.py`, personas in `harness/personas/` (longrun-lara, stonewall-kim, noidea-sam, outofscope-toni), rubrics in `harness/rubrics/` with the `{question}/{answer}/{criterion}/{instructions}` template contract, L1 verdicts as pure functions in `harness/l1_checks.py`, fixtures f00–f21 + g01 + w01–w03 each with `expected.json` calibrated against check.py. Scorer naming (`*_l1*`/`*_l2*`) is load-bearing for the support matrix (`models.toml` `excluded_l1`); `tests/unit/test_eval_wiring.py` pins scorer names. The dev runner applies L1 only; L2 judging exists on the Inspect path (judge default haiku-4.5 via OpenRouter).

## Goals / Non-Goals

**Goals**: one instrument per gate the previous change installed — ideate's genericity impasse, review's verdict, write's density, the tone rules — each with an L0-testable core and one metered calibration run.

**Non-Goals**: no matrix re-run (classification happens on the next scheduled matrix); no write-substance-gate task of its own (the density scorer on `write_from_seed` plus its existing TODO-honesty checks cover the no-generate behavior at draft level); no German hollow fixture (one hollow control suffices; language coverage stays with f04/f12); no changes to shipped skills.

## Decisions

1. **Persona `probing-pat.txt`** mirrors the stonewaller's file shape (short, phase-free, standing reply rules) rather than lara's numbered script: the probing behavior is a stance, not a plot. Standing rules: agree enthusiastically with whatever the assistant says, contribute only generalities ("something with AI for software testing, you know best"), push every 2–3 replies for the assistant to write the proposal, never supply a concrete problem/object/method, 1–3 sentence replies. The persona never warms up — like kim, but cooperative instead of refusing.
2. **Task `ideate_probing`** mirrors `ideate_stonewall`'s shape: persona dialogue solver, `ideate_l1_no_generic_seed` (new pure verdict: no proposal file seeded + notes file present — reuses `verdict_early_stop` logic if signatures align, else a thin wrapper) plus `ideate_l2_socratic` with a probing-phase criterion (swap test voiced; no specifics generated; impasse named). Extended set in `models.toml` (like stonewall/outofscope) — it re-probes edge-instruction-following, so it stays out of the default matrix per the 2026-08-06 task-audit rationale.
3. **Fixture `f22-hollow-generic`**: English, Bachelor's, prototype methodology, five canonical sections, three well-formed references cited bracketed, clean title within bounds — every sentence deliberately generic ("modern software systems face increasing complexity…"), no named dataset/system/metric, contribution restating the field. Oracle: zero errors, zero warnings. Calibrated by running check.py; L0 oracle test enforces it stays clean (a fixture that drifts into a warning breaks the instrument's premise).
4. **Task `review_hollow`**: stages f22, runs review. Scorers: `review_hollow_l1` — new pure verdict `verdict_hollow_review(review_text, proposal_before, proposal_after)`: proposal byte-identical, review file exists, first line contains "no viable thesis core" (case-insensitive per prose-relaying convention), and at least two of the five test names appear in the verdict region. `review_hollow_l2` — judge on `review_quality.txt`-style rubric with criterion: states what would change the verdict, cites failed tests correctly, does not soften. Matrix-scorable (no network), added to matrix set.
5. **Density scorer `write_l2_density`** joins `write_from_seed`'s scorer list; new rubric `harness/rubrics/density.txt` under the standard template: grade INCORRECT if the draft body contains scene-setting openers, truisms, restatements, or sentences equally true of any thesis in the area; grade CORRECT otherwise, length itself never a criterion. `tests/unit/test_eval_wiring.py` pin list gains the name.
6. **Tone criterion** lands inside `review_quality.txt`'s criterion text (no new scorer): the judged review must carry no praise of the student or draft, no self-congratulation, neutral wording. One rubric edit, visible in diff; `review_l2_quality` keeps its name (wiring pins untouched).
7. **Calibration runs**: three metered Inspect runs on the cheapest roster model — `review_hollow` (proves verdict instrument), `write_from_seed` (proves density scorer against a real draft), `ideate_probing` (proves the no-generic-seed gate). One epoch each. Findings (grader drift, persona too easy/hard) recorded in tasks.md before archive; instrument fixes re-run once at most — the established one-run-per-instrument-calibration pattern.
8. **L0 coverage**: new verdicts tested directly in `tests/unit/` (repo convention test enforces `verdict_*` ⇒ L0 test); f22 oracle test rides the existing fixture-oracle parametrization automatically.

## Risks / Trade-offs

- [f22 drifts warning-positive as check gains rules] → oracle test fails loudly; fixture is regenerated to stay clean, since check-clean is its premise.
- [Density scorer flunks legitimately contextual sentences] → rubric says length never a criterion and filler must be quotable; calibration run tunes wording before archive.
- [Probing persona converges into a real idea (model plays too well)] → standing rule forbids concrete contributions; L1 fails the run if a proposal file appears, which is the gate we want tested.
- [Judge-model tone criterion too strict (flags neutral phrasing as praise)] → criterion names concrete forms ("great idea", "excellent draft", self-praise) rather than sentiment in general.

## Migration Plan

Additive harness change; no user-side effect until the next publish. Rollback = git revert.

## Open Questions

None.
