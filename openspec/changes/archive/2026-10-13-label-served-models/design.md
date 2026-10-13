## Context

The proposal's Why gives the motivation, and `measurement.md` gives the evidence. The current state of the instruments:

- **Dev runner** (`harness/claude_runner.py`). `identity()` writes `model_requested`, `model` and `cli_version` into every run summary. `served_model()` reads the `init` event and checks it against the result's `modelUsage`. `test_summary_records_requested_alias_served_model_and_cli_version` pins the summary. `rejudge_lines()` writes `model` from the kept stream but no `cli_version` for the run under test; the `l2` block's `cli_version` is the judge's.
- **Routing rig** (`harness/routing.py`). `Result` holds `case_id`, `expected`, `kind`, `route` and `error`. The raw log writes `vars(r)` per case plus a run-level `model` (the alias). `--render` rebuilds a report with `Result(**r)`. `init_event()` and `model_usage()` already live here, and `claude_cli` re-exports them. `version_label()` reads `claude_code_version` but is used only in billing messages.
- **Report comparability.** `previous_isolation()` already makes an absent or different isolation line "not comparable" without a flag. For the model, the operator must remember `--conditions-changed`.
- **Model-ID guard** (`tests/unit/test_model_ids.py`, Rule B). Hand-written documentation may name a model only by an ID that resolves to a current roster entry or role. `claude-haiku-5-5` does not resolve: the haiku line is pinned at 4.5. Generated reports such as `docs/model-support.md` are allowlisted. `docs/skill-routing.md` is not, because it has named only aliases so far.
- **Event order.** On 2.1.284 and 2.1.296, `init` precedes every assistant event. A routing case is usually stopped before its `result` event, so `modelUsage` is often absent there.

## Goals / Non-Goals

**Goals:**
- Every alias-driven measurement leaves a record with the served full ID and CLI version.
- The routing report stops treating "same alias" as "same model".
- Docs and records can cite served models without fighting the model-ID guard.

**Non-Goals:**
- Retrofitting dated citations older than 2026-10-13 in `harness/README.md`. The rule applies from now on, plus the two 2026-10-13 citations corrected here.
- Regenerating `docs/skill-routing.md`, re-measuring anything, or changing the roster, matrix or judge pins.
- Recording the requested alias inside kept workspaces.
- Recording the served model in the advisory audit preflight (`harness/audit_llm_preflight.py`). It produces no measurement of record and reads plain-text output.
- Changing the metered-calls rule in `AGENTS.md`. Whether alias runs on the subscription still count as the $0 path for a haiku cell waits on the pending decision about the haiku pin. This change edits only the `poe dev` comment (D9).
- Labelling the routing log's skills revision with the tree it actually measured. It is recorded in `docs/backlog.md` under "Harness" (see "Also observed" in `measurement.md`).

## Decisions

### D1. One `served_model` for both instruments, in `routing.py`

Move `served_model()` from `claude_runner.py` to `routing.py`, beside `init_event()` and `model_usage()`. Its helper `output_tokens()` moves from `claude_cli.py` with it. `claude_runner` imports `served_model` from `routing`, and `claude_cli` imports `output_tokens` from there, as it already imports `init_event`, because `routing` cannot import `claude_cli`. The routing rig reads the served model from `init` first and falls back to the producing model in `modelUsage`. The dev runner keeps the same behaviour, including the discrepancy note. The CLI version is read by one new helper, `routing.host_cli_version()` (`init_event(events).get("claude_code_version")`), which the rig, the dev runner, its re-grade and the judge's `JudgeCall` share; `version_label()` builds on it.

- *Rejected: a second reader in `routing.py`.* Two definitions of "the served model" would drift, and `routing` cannot import `claude_runner`, which imports it.
- *Rejected: `modelUsage` only.* Most routing cases stop before the result event.

### D2. Per-case fields on `Result`, defaulting to none

`Result` gains `served_model: str | None = None` and `cli_version: str | None = None`, filled in `case_result()` from the case's own events.

- `vars(r)` writes them to the raw log.
- `Result(**r)` keeps reading logs that lack them.
- `replace()` in `void()` keeps them, so a voided case still shows what served it.
- A case "not started" after a billing stop has none.

*Rejected: one run-level field.* A sweep can straddle an alias re-point or a host upgrade. The requirement asks for the per-case record, and the header aggregates it.

### D3. Report header and closing line

`render_report()` keeps `- model: \`<alias>\`` as the requested model and adds two lines below it:

- `- served: \`<id>\` (<n>), …`. Measurements whose stream reported no served model are appended as `not reported (<n>)`. The line reads `- served: not recorded` for a report rebuilt from a raw log written before the field existed, which `--render` detects by the field's absence from the logged results; a new log whose streams all reported none reads `not reported (<n>)`.
- `- host CLI: <version> (<n>), …`, with the same `not reported` and `not recorded` rules.

The served IDs are counted over measurements without an error, so the line describes the same measurements as the matrix below it. The rig's closing stdout line names the served IDs too, counted over every result, errored ones included, as the raw log records them.

### D4. Comparability by the set of served IDs

`previous_served()` parses the backticked IDs from the outgoing report's `- served:` line, and returns none when the line is absent or reads "not recorded". `write_report()` treats the earlier score as not comparable when that set is none or differs from the new run's set. This mirrors `previous_isolation()`. Counts are ignored, because the case set is the operator's declaration.

- *Rejected: comparing the alias.* Alias equality is the false sameness this change removes.
- *Rejected: including the CLI version.* The host updates every few days, so nearly every report would read "not comparable", and readers would learn to ignore the line. A CLI change that alters the rig, like 2.1.207 → 2.1.284 moving the rate-limit report, stays an operator declaration with `--conditions-changed`.

Consequence: the next sweep will mark 171/174 as "measured under different conditions, not comparable", because today's report has no served line. That is accurate, since its served model is only inferred, and the earlier score is still printed.

### D5. Re-grade line: served model and CLI version, no alias

`rejudge_lines()` adds `cli_version` from the kept stream's `init` (empty when there is none). The lines a crashed re-grade writes carry the same two fields, read the same way, and empty when the saved stream cannot be read. It writes no `model_requested`. The workspace does not record one, and `args.model` defaults to `haiku`, so it would mislabel a re-grade of a sonnet run. The judge's own `cli_version` stays inside `l2`.

### D6. Citations versus the model-ID guard

Served IDs are historical facts. Rule B treats any non-roster ID in documentation as a stale example. The resolution:

- Full served IDs live in records the guard exempts: change records (`measurement.md`, `tasks.md`), generated reports (`docs/skill-routing.md`, D7), and the gitignored logs.
- Hand-written guarded docs name a served model by its full ID only when that ID resolves to a current pin, as `claude-sonnet-5-5` does today. Otherwise they name it in prose by version ("haiku 5.5"), which the guard's identifier shapes do not match, with the CLI version and a pointer to the change record.

- *Rejected: a single-token allowlist entry per cited ID.* Such an entry is exhaustible. It fails the suite once the roster pins that ID, and the citation fails again after the next bump, so every bump would churn dated history.
- *Rejected: teaching the guard a dated-citation syntax.* That means parsing prose claims to enforce a rule that review already covers.

### D7. `docs/skill-routing.md` joins the allowlist as a generated report

This is a category entry: "generated by `uv run poe routing`; records the served model as measured". It stays even while the file names only current models, as `docs/model-support.md` does. It applies the spec's existing exemption for generated report outputs, so it needs no spec delta.

### D8. No L0 check of prose citations

A test cannot tell a citation from an instruction in prose. The enforcement is that every instrument now records the served ID and CLI version, so a citation always has a field to copy, and review catches an alias-only claim. `harness/README.md` states the rule beside the instruments.

### D9. Documentation edits

`harness/README.md`:

- an "Aliases are not pins" paragraph under "Which path to use", dated: on 2026-10-13 (CLI 2.1.296) `haiku` served haiku 5.5, while the matrix row, `judge` and `smoke` stay pinned to haiku 4.5. A subscription run is therefore not a $0 rerun of a haiku matrix cell. The paragraph also states the citation rule (D6, D8);
- the `check_report` "$0 run" comment and the baseline example, each saying the alias runs the host's current haiku;
- the `poe smoke` sentence, saying it runs the runner's default alias;
- the routing paragraphs: the per-case fields, the header lines, and the served model joining isolation as an automatic condition, with CLI and the rest still declared;
- the two 2026-10-13 citations, which gain served model and CLI version per D6.

`AGENTS.md`: the `poe dev … --model haiku` comment gains "the alias runs the host's current haiku, not the matrix row". `README.md` is unchanged.

## Review decisions (2026-10-13)

The maintainer approved the design with these answers. None is left open.

1. **D4 stands.** A change of the served model set marks the earlier routing score not comparable automatically. A CLI version change stays the operator's declaration.
2. **D6 stands.** Guarded docs name a served model that no pin covers in prose ("haiku 5.5"), with the CLI version and a pointer to the change record. No per-ID allowlist entry is added.
3. **The `AGENTS.md` metered-calls rule is unchanged** in this change and waits on the maintainer's matrix decision. Only the `poe dev` comment is edited (task 5.2).
4. **No re-grade alias file.** D5 stands as designed: the re-grade line carries the kept run's served model and CLI version, and no requested alias.
5. **Skills-revision labelling is out of scope.** The existing "Routing report labels" entry in `docs/backlog.md` is extended with the finding and a pointer to `measurement.md`, and `measurement.md` points at that entry (task 5.3).
6. **The "about 7/30" figure** is corrected by its errata entry alone.

## Risks / Trade-offs

- [The inferred IDs in the errata could be wrong] → They are labelled inferred, with their basis. The rule forbids presenting them as recorded, and the next recorded sweep settles the question for new data.
- [A future host drops `claude_code_version` or `model` from `init`] → Served falls back to `modelUsage`. Anything still missing is counted visibly as "not reported" or "not recorded" rather than filled from the alias.
- [Prose versions in docs ("haiku 5.5") age] → Each one sits beside a date and describes a measurement, not a recommendation.
- [Moving `served_model` breaks an import] → Update its importers in the same task, and let the L0 suite find any missed one.
