# Steer agents to the subscription first

## Why

The OpenRouter key has billed $21.31 in total. $21.07 of that traces to individual runs, and $20.61 of it (97.8%) went to Anthropic models that the Claude Max subscription already covers. The repository's own text sent agents there. Each sentence below presents a metered path as the normal way to run an Anthropic model, and none names the $0 route:

- `AGENTS.md:67` calls `poe smoke` a "metered smoke". An agent asked for a quick check picks it, although `poe dev` is the quick check.
- `AGENTS.md:93` lists a bare `inspect eval … --model openrouter/...` as "L1/L2, metered". That command has no cost gate.
- `harness/README.md:5` heads its first section "Authoritative runs (Inspect + OpenRouter, metered)". `:18` gives an OpenRouter judge as the only grader. `:38` and `:54-56` show metered commands first.
- `.env.example:10-12` describes the key as the one for "Metered L1/L2 evals".
- The coverage comment at `pyproject.toml:95-98` calls `claude_runner.py` "metered-only" and says it never runs at L0. It runs on the subscription, and L0 tests already cover 65% of its statements.

On 2026-10-04 that steering cost $7.885, approved by the user both times:

- **$5.2374, a matrix run** on haiku-4.5 and sonnet-5. Both tasks already had dev-runner scenarios on the subscription. The estimate was $4.16, so the actual cost was 26% higher.
- **$2.645, a re-grade.** Drafts the subscription had already produced were re-graded through a scratch script started with `--env-file .env`. No cost gate saw that run. It was approved at about $0.70 and cost 3.8× as much.

September cost $0 because every run that month used the subscription. The route works whenever the job fits it. No rule says that it should be the default, and no rule covers the paths the gate cannot see.

## What Changes

- **New `AGENTS.md` hard rule, "Metered model calls".**
  - Rule:
    - An Anthropic model runs on the subscription wherever the subscription can do the job.
    - Any metered call on an Anthropic model goes through the matrix cost gate or an explicit user approval. This covers `poe matrix`, any other metered poe task, a bare `inspect eval`, a scratch script and an ad-hoc re-judge.
    - The approval request states the estimate and how it was derived, and names the $0 subscription alternative, or says why there is none.
    - Re-grading recorded artifacts is never metered.
    - Before proposing a metered run, check that the pinned model is still current.
  - Why: the spend figures above.
  - Enforcement: the gate covers only the poe matrix tasks. The rule is the only guard for everything else, which is why it names scratch scripts.
- **`AGENTS.md` Commands block (`:66-68`, `:84`, `:93`, `:98`).**
  - `poe dev` is labelled as the default, $0 loop for Anthropic models.
  - `poe smoke` is labelled as a metered check of the Inspect wiring, not a quick check.
  - `poe matrix` is labelled as the metered source of record.
  - The bare `inspect eval` line is labelled metered and ungated, pointing to `poe matrix --models … --tasks …`.
  - The closing sentence explains that subscription runs cost plan quota, not money, and only while extra usage stays off.
- **`harness/README.md`.**
  - A short "Which path to use" table opens the file: job, then path, then cost.
  - The heading at `:5` and its lead sentence now say that the Inspect path is reserved for what the subscription cannot do, and that a bare `inspect eval` is ungated.
  - `:18` says the OpenRouter judge is the pinned matrix judge, not an ad-hoc grader.
  - The matrix section (`:35`, `:38`, `:45`) and the baseline examples (`:53-57`) name the gate, put the subscription command first, and limit `--yes` to the operator.
  - The dev-runs heading (`:62`) names the subscription as the default.
- **`.env.example:10-12`.** The key is described as serving only the metered OpenRouter runs. It is not needed for dev runs, routing or grading. A low monthly limit is suggested.
- **`pyproject.toml:95-98`.** The coverage-omit comment says what each omitted file actually runs on. It also says that only `skill_evals.py` is unreachable at L0, while L0 tests run part of `claude_runner.py`. The omit list itself does not change.

Not in this change:
- **Wording that depends on the subscription judge (`--judge`)** lands with `add-dev-runner-judge`: `harness/README.md:88`, `:94`, `:104`, the table's L2 row and `claude_runner.py:8`. So does the retarget of `poe smoke`. So does the decision whether `claude_runner.py` stays on the coverage omit list: that change adds the in-process runner tests the entry would hide (design.md D5).
- **Model IDs and where the judge default comes from** are handled by `track-model-currency`.
- **Steering outside the repository** is handled outside the change: auto-memory, the worktree `.env` symlink, the key's monthly limit, overage settings.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none. `skip_specs: true`. The change edits contributor instructions, harness documentation, a credentials template comment and a coverage comment. No script, harness or skill behaviour changes. The testing-harness requirements stay as they are. The matrix remains the metered source of record, and the subscription dev runner remains the everyday loop. This change makes the docs say so, where today they present the metered path as the default.)

## Impact

- `AGENTS.md`: one new Hard rules bullet, and rewritten comments in both Commands blocks plus the sentence at `:98`.
- `harness/README.md`: a new opening table, and rewritten sentences in the Inspect, matrix, baseline and dev-runs sections.
- `.env.example`: the comment above `OPENROUTER_API_KEY`.
- `pyproject.toml`: the comment above `[tool.coverage.run] omit`.
- No code, test, fixture, spec, generated copy or poe task changes. No model call, metered or subscription, is part of this change.
- Order: this is the first of four sequential changes, followed by `track-model-currency`, `add-dev-runner-judge` and `fix-openrouter-caching`. `add-dev-runner-judge` rewrites the smoke lines and the L2 table row it inherits from here.
