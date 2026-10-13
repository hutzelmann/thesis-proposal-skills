## 1. Evidence

- [x] 1.1 Extract the served-model evidence for the errata into `measurement.md` before `/tmp/devrun-*` is deleted: run directory, scenario, requested alias, served model, CLI version and verdicts where recorded. Done at proposal time (2026-10-13), with no model call. The 19 readiness lines are matched to their workspaces by `duration_ms`. The 40 handoff and guard workspaces are read from their `init` events. The routing logs of 2026-10-05 and 2026-10-13 are tabulated.

## 2. Shared reader

- [x] 2.1 Move `served_model()` from `harness/claude_runner.py` and `output_tokens()` from `harness/claude_cli.py` into `harness/routing.py`, and import both from there (design D1). Verify that `uv run pytest tests/unit/test_dev_runner_probe.py tests/unit/test_claude_cli.py tests/unit/test_routing.py` passes unchanged. The summary pin `test_summary_records_requested_alias_served_model_and_cli_version` and the `modelUsage` note test must stay green.

## 3. Routing rig

- [x] 3.1 Add `served_model` and `cli_version` to `Result`, defaulting to none, and fill them in `case_result()` from the case's own events (D2). Add L0 tests:
  - the recorded `route-before-report.jsonl` yields `claude-sonnet-5-5` and `2.1.284`;
  - a stream without `init` yields none;
  - a voided result keeps both;
  - `Result(**r)` reads a raw-log entry without the fields;
  - the raw log written by `main()` carries both per case.

  Verify `uv run pytest tests/unit/test_routing.py`.
- [x] 3.2 Add the `- served:` and `- host CLI:` header lines to `render_report()`, counted over error-free measurements, with `not reported (n)` and `not recorded`. Name the served IDs in the rig's closing stdout line too (D3). Add L0 tests for one served ID, two IDs in one sweep, streams that report none, and `--render` of a log without the fields. Verify `uv run pytest tests/unit/test_routing.py`.
- [x] 3.3 Add `previous_served()` and the served-set comparison in `write_report()` (D4). Add one L0 test per scenario of "A conditions change invalidates comparison":
  - alias resolves to a different model;
  - earlier report records no served model;
  - same isolation and served set, which supersedes;
  - same served set on a newer CLI, which supersedes.

  The existing staging and isolation cases must still pass. Verify `uv run pytest tests/unit/test_routing.py`.
- [x] 3.4 Add `docs/skill-routing.md` to `ALLOWLIST` in `tests/unit/test_model_ids.py` as a category entry for a generated report (D7). Add two L0 cases: a header line naming `claude-haiku-5-5` in that file is a violation that the entry exempts, and the prose spellings "haiku 5.5" and "haiku-4.5" yield no token, which D6 relies on. Verify `uv run pytest tests/unit/test_model_ids.py`.

## 4. Dev runner

- [x] 4.1 Make `rejudge_lines()` write the kept run's `cli_version` from the workspace stream's `init`, empty when there is none, and no `model_requested` (D5). Add L0 tests:
  - a re-grade of a workspace holding `model_stream()` carries `model` and `cli_version` `2.1.284` at top level, beside `l2.cli_version`, and has no `model_requested` key;
  - a stream without `init` records `cli_version` as none.

  Verify `uv run pytest tests/unit/test_dev_runner_probe.py -k rejudge`.

## 5. Documentation

- [x] 5.1 Edit `harness/README.md` per D9:
  - the dated "Aliases are not pins" paragraph with the citation rule (D6, D8);
  - the `check_report` "$0 run" comment and the baseline example;
  - the `poe smoke` sentence;
  - the routing paragraphs and "Measurement conditions": per-case fields, header lines, and the served model as an automatic condition;
  - the dev-run probe paragraph: the re-grade line's `cli_version`;
  - the two 2026-10-13 citations: sonnet as `claude-sonnet-5-5`, haiku as "haiku 5.5", with CLI 2.1.296 and a pointer to this change's `measurement.md`.

  Verify `uv run pytest tests/unit/test_model_ids.py`, and check that every `--model haiku` occurrence in `grep -n "model haiku" harness/README.md` is covered by the paragraph or by a note of its own.
- [x] 5.2 Edit `AGENTS.md`: the `poe dev … --model haiku` comment says the alias runs the host's current haiku, not the matrix row. Verify that `uv run pytest tests/unit/test_model_ids.py` passes and that `/usr/bin/git diff --stat README.md docs/skill-routing.md` shows no change.

- [x] 5.3 Extend the "Routing report labels" entry under "Harness" in `docs/backlog.md`: the routing log's `skills_revision` is the committed `HEAD:skills` even when the working tree changed between sweeps, with a pointer to this change's `measurement.md`. Reword the last paragraph of `measurement.md` ("Also observed") to point at that backlog entry instead of calling it an open question (review decision 5).

## 6. Verification

- [x] 6.1 Run `uv run poe test` and `uv run poe specs` green. Make no model call of any kind: no `claude -p`, `poe dev`, `poe smoke`, `poe routing` or `poe matrix`.
- [x] 6.2 Have one fresh read-only reviewer check the full diff adversarially against the specs. Fix confirmed findings, re-run 6.1, and record the findings in this file.

  Review findings (2026-10-13, one read-only reviewer; no bug on the main code paths, every routing, comparability and re-grade scenario has an L0 test that fails for the right reason). All ten were confirmed and fixed:
  1. The citation SHALLs had no start date, so the archived spec would have been violated by older alias-only citations in `harness/README.md`. The spec now applies them from the requirement on, matching the design Non-Goal.
  2. A crashed re-grade's lines carried neither field. They now carry both through `kept_identity()`, which falls back to none for an unreadable stream; a new scenario, "Re-grade that crashed", and two L0 tests pin it.
  3. "Every measurement … by an alias" also reached the advisory audit preflight. The requirement now names the dev runner and the routing rig, and the design lists the preflight as a Non-Goal.
  4. The spec's "not recorded" wording also matched a new log whose streams all reported none. It now names a raw log written before the field existed, as D3 does.
  5. "Alias re-pointed within a sweep" was tested on the report side only. A new L0 test checks the per-case raw results too.
  6. The proposal called the generated row the top-level README's only haiku mention. It now also names the supervise remark of 2026-10-04, written before the alias moved.
  7. A garbled parenthetical in the citation rule of `harness/README.md` was reworded.
  8. D1 did not say which module imports what, or name `host_cli_version()`. D1 and the proposal's Impact now do.
  9. The rig's closing line read "not recorded" for an all-errored sweep. It now counts every result, as the raw log records them, with an L0 test.
  10. `previous_served()` and `recorded_conditions_changed()` bound the report path at import. The path is now a required argument.
