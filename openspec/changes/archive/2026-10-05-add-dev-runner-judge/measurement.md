# Measurement: live subscription checks (tasks 8.1–8.3)

Recorded 2026-10-05 on the working tree of this change (base `138bf62`), from the
maintainer's machine, host **Claude Code 2.1.284**. Every figure is notional
(`total_cost_usd`, plan quota, not money): no metered call was made, and the plan's
extra usage was off. Six subscription runs in all: two judged dev runs, one
re-grade, and the three smoke steps.

Account details from `claude auth status` (email, organization) were never printed or
recorded; only `loggedIn`, `authMethod` and `apiProvider` were read.

## Environment

- The launching session exported `ANTHROPIC_BASE_URL` (pointing at Anthropic's own
  API), `CLAUDE_EFFORT`, `CLAUDECODE` and many `CLAUDE_CODE_*` session variables, and no
  API key. The billing strip removed `ANTHROPIC_BASE_URL` from every model run and the
  judge's allowlist removed all of them from every judge call. No run failed for it.
- 8.2 added `ANTHROPIC_API_KEY=placeholder-not-a-key`, `CLAUDE_EFFORT=max` and
  `OPENROUTER_API_KEY=placeholder-not-a-key`; 8.3 added the placeholder API key.
  Neither run read untested for an API-key source, and no host tried the key.

## 8.1 Judged dev run (`write_from_seed --isolated --judge --keep --model haiku`)

Run with `--max-budget-usd 2` and a scratch `--summary-log` added.

| Attempt | Served model under test | L1 | L2 | Model run | Judge calls |
|---|---|---|---|---|---|
| 1 | `claude-haiku-4-5-20251001` | FAIL: no draft produced (the run stopped to ask the degree level) | both "not judged: no artifact" | $0.096, 7 turns, 24 s | none |
| 2 | `claude-haiku-4-5-20251001` | PASS: draft mechanically sound (seed edited in place) | `write_l2_rq_quality` PASS, `write_l2_density` FAIL | $0.134, 15 turns, 69 s | 2, $0.0441 total |

- Attempt 2's judge: served `claude-sonnet-5-5` = `[roles].dev_judge`, effort `medium`,
  CLI 2.1.284, thinking tokens 0, label "dev-runner L2, not comparable to matrix",
  `self_graded: false`. Exit status 1 (a graded criterion failed), as designed.
- Model-run streams (both kept workspaces): `apiKeySource: none`, exactly one
  `rate_limit_event` each (`allowed_warning`, `seven_day`, utilization 0.87, no
  overage), every `modelUsage` entry `provider: firstParty`. A full agent session does
  emit the event the absent-event rule relies on (design D5, open question closed for
  this host version).

## 8.2 Re-grade of attempt 2's workspace (`--rejudge`)

- Both criteria graded, with the same grades as in 8.1 (`rq_quality` PASS, `density` FAIL).
- Effort recorded `medium`, not the exported `max`; served `claude-sonnet-5-5`;
  `apiKeySource: none` on both calls.
- Projection printed after the warm-up: "2 judge call(s) × $0.0078 ≈ $0.02 (cap $5.00)".
- Cost: warm-up $0.0078, second call $0.0136, total $0.0214; thinking tokens 591.
- `self_graded: false`, read from the kept stream's served model.

## 8.3 `poe smoke` (placeholder API key exported)

| Step | Outcome | Model-run notional | Turns | Duration | vs `--max-budget-usd 2` |
|---|---|---|---|---|---|
| `write_from_seed` (judged) | FAIL: L1 PASS, `write_l2_density` FAIL | $0.118 + judge $0.0424 (2 calls, thinking 0) | 11 | 60 s | 6% (8% with the judge) |
| `import_messy` | FAIL: no ordered-list research questions | $0.088 | 11 | 64 s | 4% |
| `customize_override` | PASS: valid nested override | $0.058 | 6 | 20 s | 3% |

- All three steps ran although the first failed; the closing `--summarize` listed each
  outcome and exited 1, matching its rows; the poe sequence exited non-zero.
- No row untested, none for an API-key source; served model `claude-haiku-4-5-20251001`
  and CLI 2.1.284 on every row. `logs/devrun/smoke.jsonl` was removed by the summary.
- Rate limit throughout: `allowed_warning`, `seven_day`, 0.87, no overage.
- The two FAILs are skill-on-haiku findings, not runner defects: `import_messy` wrote no
  ordered research-question list, and the judge called the drafted proposal's opener and
  one "intersection" sentence filler. They are out of this change's scope.

## Per-call cost against the ~$0.055 assumption

| Source | Calls | Notional per call | Thinking tokens |
|---|---|---|---|
| 8.1 attempt 2 | 2 | $0.022 | 0 |
| 8.2 | 2 | $0.008 (warm-up), $0.014 | 591 |
| 8.3 | 2 | $0.021 | 0 |

The assumption is not confirmed: at `dev_judge_effort = "medium"` a call costs
$0.008–0.022, between 2.5 and 7 times less than assumed, and thinking stays low. That
is the safe side, so **no registry effort edit is proposed**: lowering the effort would
save little quota, and raising it is not warranted by these grades. A judged write
scenario costs about $0.02–0.05 rather than $0.11, and a 48-call re-grade about
$0.5–1.1 rather than $2.6; the default `--max-notional` of $5.00 covers more than 200
calls. Every smoke step stayed below 10% of its $2 cap, so no cap change is proposed
either.
