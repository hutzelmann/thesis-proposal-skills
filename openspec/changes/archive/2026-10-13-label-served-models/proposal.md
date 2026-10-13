## Why

The Claude Code alias `haiku` moved between hosts: on 2026-10-05 (CLI 2.1.284) it served `claude-haiku-4-5-20251001`, on 2026-10-13 (CLI 2.1.296) `claude-haiku-5-5`. The matrix row and the `judge` and `smoke` roles stay pinned to `openrouter/anthropic/claude-haiku-4.5`. Three changes archived on 2026-10-13 record "haiku" results without a served ID, and every one of those results is haiku 5.5. The dev runner already records the served ID (`model`, `cli_version`); the routing rig records only the alias, so its 2026-10-13 haiku and sonnet sweeps carry no served model at all. The correction belongs in a follow-up change because the archives are edit-denied, and the evidence must be extracted now because part of it sits in `/tmp/devrun-*` workspaces that will be deleted.

## What Changes

- **Errata** (below) for the archived changes, with the served IDs, CLI versions and evidence paths. The evidence is extracted run by run into `measurement.md`.
- **Routing rig**: each case's raw result records the served model ID and the CLI version, read from the stream's `system/init` event. The report header names the requested alias, every served ID with its measurement count, and the CLI version or versions.
- **Comparability**: a change of the served model set invalidates comparison with the outgoing report automatically, in the same way the isolation line does. An outgoing report with no served line counts as not comparable. A CLI version change is recorded but stays the operator's declaration.
- **Dev runner**: the run summary already carries `model_requested`, `model` and `cli_version`, pinned by an L0 test. The gap is a `--rejudge` line, which carries the kept run's served model but not its CLI version. It now reads the CLI version from the kept stream, and it carries no requested alias, because the workspace does not record one.
- **Citation rule**: a cited measurement names the served full model ID and the CLI version, never only the alias. A record that lacks them says so, and an inferred served model is labelled as inferred. Stated in `harness/README.md` and in the testing-harness spec.
- **Docs**: `harness/README.md` and `AGENTS.md` stop implying that `--model haiku` measures the matrix's haiku row. The alias runs the host's current haiku, haiku 5.5 as of 2026-10-13, while the row is pinned to haiku 4.5. `README.md` needs no edit. Its haiku mentions are the generated row, whose routing notes were measured on haiku 4.5, and the supervise remark that Claude Haiku "did not pick it up at all", written on 2026-10-04, before the alias moved.
- **Model-ID guard**: `docs/skill-routing.md` joins the allowlist as a generated report. Its header will carry served IDs, which can be non-roster or outgoing IDs.

## Errata

Labels in archived changes, with what the evidence shows. "Recorded" means the run's own record carries the served ID. "Inferred" means it does not, and the ID is taken from same-day runs on the same machine, CLI and login. Run-by-run detail is in `measurement.md`.

| Archived change | Where | Says | Served model | CLI | Basis |
|---|---|---|---|---|---|
| 2026-10-13-proportionate-readiness-review | tasks 7.2; proposal Impact (Cost); design Risks | haiku | `claude-haiku-5-5` | 2.1.296 | recorded: all 7 haiku run lines and the haiku re-grade line in `logs/devrun/readiness.jsonl`, all 3 haiku lines in `readiness-final.jsonl` |
| same | tasks 7.2 | sonnet | `claude-sonnet-5-5` | 2.1.296 | recorded: 4 + 5 lines in the same logs |
| same | tasks 7.2 (subscription judge) | judge | `claude-sonnet-5-5` | 2.1.296 | recorded: `judge_served` on every judged line |
| same | tasks 7.2, "Final state" list | haiku `review_hollow` as final state | `claude-haiku-5-5` | 2.1.296 | the run appears only in the iteration log (`readiness.jsonl` line 8, workspace written 08:06), before the final-state reruns (08:19–08:21). It is an iteration result, not a final-state one |
| 2026-10-13-add-stage-handoffs | tasks 6.2, rounds 1–4 | haiku | `claude-haiku-5-5` | 2.1.296 | recorded: 16 of 16 kept event streams (`/tmp/devrun-handoff_*`, extracted) |
| same | tasks 6.2, rounds 1–4 and regression guards | sonnet | `claude-sonnet-5-5` | 2.1.296 | recorded: 16 of 16 round streams and 3 of 4 guards. The `check_report` guard kept no workspace, so its served model is not recorded |
| same | tasks 6.3, routing: haiku 27/33 and 43/54 | haiku | not recorded; inferred `claude-haiku-5-5` | inferred 2.1.296 | `logs/routing/from-stage-handoffs-2026-10-13/20261013-094341.json` and `-094912.json` carry `"model": "haiku"` and no streams |
| same | tasks 6.3 and `docs/skill-routing.md`: sonnet 171/174 and 54/54 | sonnet | not recorded; inferred `claude-sonnet-5-5` | inferred 2.1.296 | `-094559.json` and `-094758.json`, same limitation |
| same | tasks 6.3, "no regression" against the 2026-10-05 baseline, "about 7/30 then, 22/30 now" | haiku vs haiku | 2026-10-05: `claude-haiku-4-5-20251001`; 2026-10-13: inferred `claude-haiku-5-5` | 2.1.284 vs 2.1.296 | The two sides were served by different models, so the comparison cannot isolate the description tweak. The kept 2026-10-05 runs score **19/30** on the same ten cases (both runs, `from-vigorous-raman-2026-10-05/20261005-234338.json` and `-234728.json`), not about 7/30 |
| 2026-10-13-sharpen-handoff-choices | tasks 3.2; proposal Impact (Cost) | sonnet | `claude-sonnet-5-5` | 2.1.296 | recorded: 5 of 5 kept streams. Haiku was not run |
| 2026-10-05-route-bug-reports-to-troubleshoot | measurement.md, runs 1–5; haiku 0/33 | haiku, sonnet | `claude-haiku-4-5-20251001`, `claude-sonnet-5-5` | 2.1.284 | **confirmed, no correction.** Runs 1, 2 and 4 already name the served ID. The kept streams of run 3 (haiku) and run 5 (sonnet) show the same IDs. The rig keeps one stream per case (the last epoch), so 1 of every 3 epochs is recorded |

What follows from the table:

- Every haiku result in the 2026-10-13 archives describes haiku 5.5. No matrix row, registry note or shipped verdict covers that model.
- The haiku-4.5 row's two routing notes, polish 0/3 and troubleshoot 0/33, were both measured on haiku 4.5 on 2026-10-05, so they stay correctly attributed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`:
  - "Routing reported as a confusion matrix": each case records its served model and CLI version, and the report header names them.
  - "A conditions change invalidates comparison": the served model is detected automatically, as isolation is.
  - New requirement "Measurements name the served model": the re-grade line and the citation rule.

## Impact

- `harness/routing.py`:
  - `Result` gains the served model and CLI version, defaulting to none, so `--render` of older logs still works;
  - the report header and the comparability check use them;
  - `served_model` moves here from `claude_runner.py`, and its helper `output_tokens` from `claude_cli.py`, so both instruments share one reader; a new `host_cli_version` reads the CLI version for all of them.
- `harness/claude_runner.py`: imports `served_model` from `routing`; the re-grade line, a crashed one included, gains the kept run's `cli_version`. `harness/claude_cli.py`: imports `output_tokens` and `host_cli_version` from `routing`.
- `tests/unit/test_routing.py`, `tests/unit/test_dev_runner_probe.py`: L0 coverage.
- `tests/unit/test_model_ids.py`: allowlist entry for `docs/skill-routing.md`.
- `harness/README.md` (aliases are not pins; the citation rule; the routing header; the two 2026-10-13 citations), `AGENTS.md` (the `poe dev` comment only; its metered-calls rule waits on the matrix decision).
- `docs/backlog.md`: the "Routing report labels" entry gains the skills-revision finding from `measurement.md`, which stays out of this change's scope.
- No model calls, no re-measurement, and no change to the roster, matrix or judge pins. Whether to bump the haiku pin is a separate, pending decision.
- `docs/skill-routing.md` is not regenerated now. Its header changes at the next sweep.
