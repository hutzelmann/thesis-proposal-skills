# Model support grid

Generated from the newest eval logs on 2026-08-10. Cells show passed/total epochs; `*` marks budget-reduced epochs; `—` marks untested cells.

| Model | write_from_seed | review_fixture | review_fixture_de | review_hollow | title_alarm | ideate_longrun | customize_override | publish_build | import_messy | reverse_from_harvest | run cost | runtime |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `anthropic/claude-haiku-4.5` | 0/1* | 0/3 | 1/1* | 0/1* | 1/1* | — | 0/1* | 1/1* | 1/1* | — | $2.22 | 921s |
| `anthropic/claude-sonnet-5` | — | — | — | — | — | — | — | — | — | — | — | — |
| `anthropic/claude-opus-5` | — | — | — | — | — | — | — | — | — | — | — | — |
| `openai/gpt-5.6-luna` | — | — | — | — | — | — | — | — | — | — | — | — |
| `openai/gpt-5.6-terra` | — | — | — | — | — | — | — | — | — | — | — | — |
| `openai/gpt-5.6-sol` | — | — | — | — | — | — | — | — | — | — | — | — |
| `deepseek/deepseek-v4-pro` | 1/1* | — | — | — | — | — | — | — | — | — | $0.03 | 268s |
| `qwen/qwen3.8-max` | — | — | — | — | — | — | — | — | — | — | — | — |
| `moonshotai/kimi-k3` | 1/1* | — | — | — | — | — | — | — | — | — | $0.42 | 472s |

## Baseline delta

With-skill vs without-skill, from the newest log of each arm (baseline runs are on-demand — missing rows were simply not run):

| Model | Task | Pass rate (with / without / Δ) | Tokens (with / without / Δ) | Runtime s (with / without) |
|---|---|---|---|---|
| `anthropic/claude-haiku-4.5` | customize_override | 0.00 / 0.00 / +0.00 | 120782 / 530151 / -409369 | 53 / 77 |
| `anthropic/claude-haiku-4.5` | import_messy | 1.00 / 0.00 / +1.00 | 145466 / 492925 / -347459 | 64 / 228 |
| `anthropic/claude-haiku-4.5` | write_from_seed | 0.00 / 0.00 / +0.00 | 242200 / 753873 / -511673 | 112 / 234 |

Assertion flags for `anthropic/claude-haiku-4.5` on proposal-customize:
- `customize_l1` fails in both arms — too-hard candidate
