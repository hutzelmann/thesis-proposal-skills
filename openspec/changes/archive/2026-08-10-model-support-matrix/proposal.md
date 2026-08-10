# Proposal: model-support-matrix

## Why

The skills claim to work on "all currently used main models", but the harness only ever ran ad-hoc single-model evals — there is no systematic evidence, no published statement of which models are supported, flaky, or broken, and no cost control around wide runs. Users picking an agent model get no guidance; regressions against non-Anthropic models go unnoticed.

## What Changes

- **Pinned model registry** `harness/models.toml`: nine OpenRouter models — Anthropic (claude-haiku-4.5, claude-sonnet-5, claude-opus-5), OpenAI (gpt-5.6-luna, gpt-5.6-terra, gpt-5.6-sol), open-weight (deepseek-v4-pro, qwen3.8-max, kimi-k3) — each with family, price tier (cheap/mid/frontier), cached $/Mtok pricing, and an enabled flag. Version upgrades are deliberate one-line edits.
- **Matrix runner** (`harness/matrix.py`): drives Inspect over registry-selected models × scorable tasks with per-cell epochs. Prints a cost estimate before any metered call and requires explicit confirmation (`--yes` to skip); reports actual cost per model and total after the run from Inspect token usage × registry pricing.
- **Support classification**: 3 epochs per model×task, pass-rate bands → solid/flaky/fail per cell; per-model verdict supported / flaky-on-named-skills / warning. Inspect-path environment-fidelity probes (L1 of check_report and title_alarm, review byte-identity) and network-dependent tasks are excluded from scoring; title_alarm L2 still counts. Frontier-tier models run heavy dialogue tasks at 1 epoch (budget tuning).
- **Report generator** (`harness/report.py`): aggregates the newest Inspect logs into (1) a README summary table between generated markers — pinned model ID (version visible), verdict, warnings, run timestamp — and (2) `docs/model-support.md`, the full model×task grid with pass rates and per-model run cost.
- **poe tasks**: `smoke` (one cheap model × core tasks), `matrix` (`--tier`/`--models`/`--tasks`/`--epochs`/`--yes` passthrough), `report`.
- L0 tests for all new pure logic (registry parsing, classification bands, estimate arithmetic, README marker splicing).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: adds requirements for the pinned model registry, cost-gated matrix runs with post-run cost reporting, epoch-based support classification with explicit scoring exclusions, and the generated support report (README summary + full grid).

## Impact

- New: `harness/models.toml`, `harness/matrix.py`, `harness/report.py`, `docs/model-support.md` (generated), README generated section, L0 tests.
- Modified: `pyproject.toml` (poe tasks), `harness/README.md`, AGENTS.md commands.
- Spend: metered OpenRouter runs, gated at ~$30–60 per full matrix, always behind the confirmation prompt.
- No user-side skill files touched; nothing ships to skills.sh.
