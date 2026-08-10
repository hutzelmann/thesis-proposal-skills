# Design: model-support-matrix

## Context

See proposal.md — Why. Constraints that shape the design: Inspect AI is the metered engine (spec: inverted-hybrid runners); every L1 verdict already lives in `l1_checks.py`; AGENTS.md demands minimal handwritten code and established libraries; metered spend needs an explicit human gate (user directive 2026-08-06); the Inspect-path expected-red probes documented in `harness/README.md` must not pollute per-model verdicts.

## Goals / Non-Goals

**Goals:** one registry file as the single roster source; one pure-logic module so every rule is L0-testable; matrix and report runnable independently (run today, regenerate report tomorrow); estimates honest about being estimates.

**Non-Goals:** no CI-triggered matrix runs (metered stays manual); no dashboard/HTML output; no dev-runner (claude_runner) matrix — Claude-only subscription path cannot compare across vendors; no auto-upgrade of pinned models; SKILL.md pages untouched.

## Decisions

1. **Drive Inspect through its Python API** (`inspect_ai.eval()` with model list, epochs, log dir), not by shelling out to the CLI. Rationale: returns `EvalLog` objects directly — token usage for actual-cost, scores for classification — no log-path guessing; same engine either way. Alternative (subprocess + CLI) rejected: string-assembled argv and a second parse of what the API hands us for free.
2. **One registry file `harness/models.toml`, parsed with stdlib `tomllib`.** `[[models]]` entries: `id` (pinned OpenRouter ID), `family`, `tier` (cheap|mid|frontier), `input_price`, `output_price` ($/Mtok, cached from the catalog at pin time), `enabled`. A `[tasks]` table declares the scorable set: `core` (smoke subset), `heavy` (reduced to 1 epoch on frontier tier), `excluded_l1` (env-fidelity probes whose structural score never counts), `excluded` (network-dependent, never run in matrix). Alternative (separate tasks file) rejected: one file, one parse, the exclusions version together with the roster they qualify.
3. **All decision logic in a pure module `harness/support.py`**: registry parsing, cell classification (pass-rate → solid/flaky/fail), per-model verdict derivation, epoch plan (task × tier → epochs), cost estimate arithmetic, actual-cost from usage dicts, README marker splicing. `harness/matrix.py` and `harness/report.py` stay thin shells (argparse + Inspect calls + file IO). Rationale: the spec requires every rule L0-testable without model calls; purity is the mechanism the existing `l1_checks.py` already uses.
4. **Cost estimate from static per-task token priors, refined by history.** `models.toml` carries conservative token priors per task class; after each run `matrix.py` writes actual per-cell usage to `logs/evals/matrix-usage.json`, which later estimates prefer over priors. The gate prints the estimate with its basis ("priors" vs "last run") and waits for `y` unless `--yes`. Alternative (no history, priors only) rejected: estimates would never improve; alternative (Inspect token limits as hard cap) adopted additionally — `token_limit` per sample as backstop against runaway agents.
5. **Report reads logs via `inspect_ai.log` API** (`list_eval_logs` + `read_eval_log`), selects the newest log per model×task, classifies via `support.py`, and writes both outputs. README region delimited by `<!-- model-support:start -->` / `<!-- model-support:end -->`; splice is a pure string function. Timestamp = newest contributing log's start time (UTC date), shown once in the summary header. Reduced-epoch and untested cells are marked, not hidden.
6. **Judge model pinned** to the existing `JUDGE_MODEL` default (haiku-4.5) for every matrix run so L2 scores are comparable across models under test.
7. **poe wiring:** `smoke` = matrix with `--models <first enabled cheap>` `--tasks core` `--epochs 1`; `matrix` = full passthrough; `report` = report generator. No new entry-point mechanism beyond change 1's table.

## Risks / Trade-offs

- [Estimate misses badly on first run] → conservative priors, the gate says "estimate", per-sample `token_limit` backstop, history replaces priors after one run.
- [OpenRouter transient failures mid-matrix] → Inspect's built-in retry; failed samples score as errors, classification treats an errored epoch as a fail and the report shows the pass rate, so one flaky provider outage reads as flaky, not supported.
- [Model deprecations break pinned IDs] → run aborts at the failing model after the gate; fix is a one-line registry edit; report keeps showing the last successful data with its timestamp.
- [Two artifacts (README + grid) drift] → both regenerate from the same logs in one `report` invocation; neither is hand-edited.

## Open Questions

None.
