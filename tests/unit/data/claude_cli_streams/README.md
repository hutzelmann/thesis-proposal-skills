# Subscription text-call stream fixtures

Synthetic `claude -p --output-format stream-json --verbose` events for the dev
runner's subscription judge (`harness/claude_cli.py`), reduced to the events and
fields it reads: the `system/init` event (`model`, `apiKeySource`,
`claude_code_version`), the `rate_limit_event` (`rate_limit_info.status`,
`isUsingOverage`, `rateLimitType`, `utilization`) and the `result` event
(`result`, `is_error`, `total_cost_usd`, `modelUsage[<id>]` with `outputTokens`,
`thinkingTokens` and `provider`). The field names follow a probe stream recorded
on host 2.1.284 on 2026-10-04 (change `add-dev-runner-judge`, design Context);
the recording itself is not committed, because its injected environment block
carries account details. The model IDs are synthetic (`claude-fixture-…`), so the
model-ID guard (`tests/unit/test_model_ids.py`) needs no exemption for them.

Each file isolates one of the fail-closed checks in design D5: everything else in
it is the success shape. `tests/unit/test_claude_cli.py` drives every file
through `parse_stream`. The expired-login case reuses
`../routing_streams/expired-login.jsonl` rather than copying it.

| file | provenance | what it pins |
| --- | --- | --- |
| `success.jsonl` | synthetic | the shape that grades: `apiKeySource: none`, an `allowed` rate limit, one `modelUsage` key with output and thinking tokens and `provider: firstParty`, a `GRADE: C` result |
| `allowed-warning.jsonl` | synthetic, status recorded 2026-10-04 at 0.82 weekly utilization | `allowed_warning` still grades, and its window and utilization are reported |
| `overage.jsonl` | synthetic | `isUsingOverage: true` under an `allowed` status: unavailable, grade discarded |
| `rejected.jsonl` | synthetic | a `rejected` status: unavailable |
| `unknown-status.jsonl` | synthetic | a status outside `allowed`/`allowed_warning`: unavailable (fails closed) |
| `zero-output.jsonl` | synthetic | zero output tokens despite a grade line: unavailable |
| `empty-model-usage.jsonl` | synthetic | an empty `modelUsage`: unavailable |
| `empty-result.jsonl` | synthetic | an empty `result` text: unavailable |
| `api-key-source.jsonl` | synthetic | an `apiKeySource` other than `none`: unavailable, the source named |
| `foreign-provider.jsonl` | synthetic | a `modelUsage` provider other than `firstParty`: unavailable |
| `model-mismatch.jsonl` | synthetic | a different served model produced the output: unavailable, both IDs named |
| `auxiliary-model.jsonl` | synthetic, shape after a recorded full session listing an auxiliary model | an extra `modelUsage` key with zero output beside the requested one: passes |
| `no-grade.jsonl` | synthetic | a limit-style text with no `GRADE:` line: the call parses, `read_grade` returns `None`, and the judge counts it unavailable |
| `no-result.jsonl` | synthetic | the host stopped before its `result` event: unavailable |
| `no-rate-limit.jsonl` | synthetic | the success shape without any `rate_limit_event`: unavailable, because overage cannot be ruled out |
| `no-overage-flag.jsonl` | synthetic | a `rate_limit_event` without `isUsingOverage`: unavailable, because a renamed or dropped flag must not read as "no overage" |
| `no-cost.jsonl` | synthetic | a result without `total_cost_usd`: unavailable, because the notional cap and the batch projection would count the call as $0 |
