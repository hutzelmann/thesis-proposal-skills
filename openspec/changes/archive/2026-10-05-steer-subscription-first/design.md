# Design

## Context

The motivation and the spend figures are in proposal.md under Why. This section covers only what shapes the approach.

- **Nothing in the testing-harness spec has to move.**
  - "Inverted-hybrid runners" makes metered runs the source of record and the subscription CLI the everyday dev loop.
  - "Cost-gated matrix execution" gates `poe matrix`.
  - Both stay as they are. The defect is in the prose around them: it presents the metered path as the normal way to run any Anthropic model, which the spec never asked for.
- **This change lands first of four**, in this order:
  1. steer-subscription-first
  2. track-model-currency
  3. add-dev-runner-judge
  4. fix-openrouter-caching

  So at the time it lands:
  - `poe smoke` is still the metered Inspect command.
  - No subscription judge exists.
  - The judge default still lives in `skill_evals.py`.

  The docs have to be accurate for that state. Every sentence a later change will rewrite is listed under D7, so those changes touch known lines.
- **keep-isolated-login is on `main` (9c106aa).** The dev runner's `--isolated` no longer strands the stored login, so the docs may recommend it for measurement runs.
- **No L0 test pins any sentence touched here.** That covers `AGENTS.md`, `harness/README.md`, `.env.example` and the coverage comment, checked by grepping `tests/` and `scripts/`. Changing the wording cannot break `poe test`, and nothing mechanical holds the new wording in place either (D8).

## Goals / Non-Goals

**Goals:**
- Anyone who reads only `AGENTS.md` or only `harness/README.md` reaches the subscription first for every Anthropic-model job it can do.
- That reader also meets the gate or approval requirement before any metered call on an Anthropic model, including calls outside the poe tasks.
- Every remaining mention of a metered path says it is metered, says whether it is gated, and says what it is reserved for.

**Non-Goals:**
- Changing any routing behaviour. The matrix judge and persona stay `openrouter/anthropic/claude-haiku-4.5` (user decision 1; Change D is deferred).
- Adding a subscription judge or retargeting `poe smoke` (add-dev-runner-judge).
- Bumping model IDs or moving the judge default into the registry (track-model-currency).
- Recalibrating the cost estimate (fix-openrouter-caching).
- Mechanical enforcement of agent conduct (D8).

## Decisions

### D1. Docs-only, `skip_specs: true`

Every edit makes the prose match requirements that already exist.

- A requirement such as "agents SHALL prefer the subscription" would be a requirement on agent conduct. The testing-harness spec specifies harness behaviour, and no harness code would implement such a requirement.
- **Rejected:** an ADDED requirement in testing-harness. It would invent a requirement just to satisfy validation, which the OpenSpec instructions forbid. It would also overlap the requirements owned by add-dev-runner-judge and fix-openrouter-caching.

### D2. The rule is a Hard rules bullet in `AGENTS.md`, written as rule, then why, then enforcement

Proposed wording, which is the text under review:

> - **Metered model calls**: an Anthropic model runs on the Claude subscription wherever the subscription can do the job — dev runs, routing, the audit preflight, and grading output that already exists. Any metered call on an Anthropic model (billed per token through OpenRouter or any other API key) — `poe matrix` or another metered poe task, a bare `inspect eval`, a scratch script, an ad-hoc re-judge — goes through the matrix cost gate or an explicit user approval, and the request states the estimate with its basis and names the $0 subscription alternative, or says why there is none (a non-Anthropic row, a change that targets a shipped verdict). Re-grading recorded artifacts is never metered. Before proposing a metered run, check that the pinned model is still the newest of its family in OpenRouter's public model catalog, since a stale pin pays to measure a model users no longer run. Why: by 2026-10-04 the OpenRouter key had billed $21.07 to traced runs, $20.61 of it on Anthropic models the subscription covers; $2.645 of that re-graded drafts the subscription had already produced, from a scratch script run with `--env-file .env` that no gate saw, after an approval of about $0.70. The gate enforces this only for the poe matrix tasks; a scratch script or a bare `inspect eval` is invisible to every repo check, so this rule is the only guard there — which is why it names them.

Why each clause is worded the way it is:

- **"Anthropic model", not "OpenRouter".** The rule follows the model, not the vendor of the key. It also covers the Console API key that decision 3 keeps as a caching fallback, and any cloud-provider key. Non-Anthropic models have no subscription route, so the rule's alternative clause does not apply to them. The existing gate sentence at `AGENTS.md:84` still binds them.
- **"or another metered poe task", not "`poe smoke`".** The bullet must survive add-dev-runner-judge, which moves `poe smoke` to the subscription. Naming the task here would turn into a false statement when that change lands.
- **"states the estimate with its basis".** Both of the 2026-10-04 overruns came from estimates the approver could not check:
  - +26% on the matrix run;
  - 3.8× on the re-grade.

  Stating the basis (token priors, measured history, or a guess) gives the approver what they need to discount the figure.
- **"or says why there is none".** This forces the alternative to be considered every time, not only when it is convenient. It also matches user decision 5.
- **The currency check is manual** and points at the free public catalog. track-model-currency adds a checker and a weekly bump PR. When it lands, it may replace this sentence with the name of its checker; that edit belongs to it.

Placement:

- **Rejected: appending to the gate sentence at `AGENTS.md:84`.** The Commands section is reference material for the poe tasks. The rule's main target is the path no poe task covers (scratch scripts, ad-hoc re-judging), and a sentence about `poe matrix` reads as being scoped to `poe matrix`.
- **Rejected: a new `## Model runs` section.** It would weigh more than the Git and Credentials rules. Those carry comparable consequences as single bullets.

### D3. The Commands blocks are relabelled, not restructured

| Line | Today | Proposed comment |
|---|---|---|
| `:66` `poe dev` | `dev loop, subscription (claude_runner passthrough)` | `default for Anthropic models: real Claude Code on the subscription, $0 (claude_runner passthrough)` |
| `:67` `poe smoke` | `metered smoke: 1 cheap model × core tasks × 1 epoch (cost-gated)` | `metered Inspect-wiring check: haiku × core tasks × 1 epoch via OpenRouter (cost-gated) — a quick check is poe dev` |
| `:68` `poe matrix` | `model-support matrix, cost-gated` | `model-support matrix: metered OpenRouter, cost-gated — the source of record for shipped verdicts` |
| `:93` `inspect eval` | `L1/L2, metered` | `metered and ungated — prefer poe matrix --models/--tasks; see "Metered model calls"` |

- **`:84`** keeps its sentence and adds a pointer: `harness/README.md` opens with a table that says which path each job takes.
- **`:98`** becomes: "Model runs cost money (OpenRouter) or plan quota (subscription: no money while extra usage stays off, but the rolling limits are shared with the user's own Claude use) — run them deliberately, never in loops."

That sentence carries the quota and overage caveats (critique C1 and C2) into the one place that talks about the cost of model runs.

- **Rejected: deleting the `poe smoke` and `inspect eval` lines.** Both commands exist and are legitimate for what they are reserved for. Removing them would hide them rather than label them. add-dev-runner-judge rewrites `:67` when it retargets smoke.

### D4. `harness/README.md` opens with a "Which path to use" table

This table is the steer that does the most work. Today the first command block a reader sees is a metered `inspect eval` on an Anthropic model. Proposed, placed directly after the intro paragraph:

| Job | Path | Cost |
|---|---|---|
| Iterate on a skill with an Anthropic model; quick check after a change | `poe dev <scenario> --model haiku`/`sonnet`/`opus`. Add `--isolated` when the result is cited as a measurement. | subscription |
| Re-grade output that already exists | on the subscription | subscription — never metered |
| Skill selection from the descriptions | `poe routing` | subscription |
| Audit preflight | `harness/audit_llm_preflight.py` | subscription |
| L2 rubric scores, persona dialogues, confirming a change that targets a shipped verdict | `poe matrix --models … --tasks …` (Inspect) | metered, cost-gated |
| Non-Anthropic model under test | `poe matrix --models …` | metered, cost-gated — OpenRouter is the only route |
| The Inspect wiring itself changed | `poe smoke` | metered, cost-gated |

Under the table, one line: "subscription" means no money while the plan's extra usage stays off. It does draw the rolling plan limits, which are shared with the operator's own Claude use. Any metered call on an Anthropic model follows the `AGENTS.md` rule "Metered model calls".

The rest of the file:

- **`:5`**: the heading becomes "Inspect runs (OpenRouter, metered — source of record)". Its lead sentence:
  - reserves the path for what the table sends there;
  - says a bare `inspect eval` has no cost gate;
  - recommends `poe matrix --models … --tasks …` for any task the registry admits (matrix or extended set, `support.select_tasks`).
- **`:18`**: the judge sentence keeps the env var and its current default, and adds three points:
  - the default is the matrix L2 judge, and also the persona's default through `PERSONA_MODEL`;
  - it is pinned and metered on purpose, so shipped L2 verdicts stay comparable (decision 1);
  - it is not an ad-hoc grader.
- **`:35`** gains: "The source of record for the verdicts the README ships, and the only place an Anthropic model under test needs OpenRouter."
- **`:38`** carries the same `poe smoke` label as `AGENTS.md:67`.
- **`:45`**: "`--yes` skips the prompt" gains: it is for the operator to type, and an agent passes it only after the user approved that run's estimate in chat.
- **`:53-57` (baseline examples)**:
  - reordered so `poe dev … --no-skill` comes first and is labelled subscription;
  - `poe matrix --baseline` labelled metered and gated;
  - the bare `inspect eval` labelled metered, ungated, approval needed.
- **`:62`**: the heading gains "the default for Anthropic models".

Routing wording (critique C4): the table says nothing about how routing isolates itself. In particular it does not repeat the dropped "never `prepare_config`" line. Routing builds its isolated config by design, and that has been safe since keep-isolated-login.

Rejected alternatives:

- **Moving the Dev runs section to the top of the file.** This is the largest diff for the same effect. Line shifts are not the reason: the chosen table shifts every later line too, which is why D7 and the later changes anchor by quoted text, not by line number.
- **Putting the table only in `AGENTS.md`.** `harness/README.md` is where a reader goes to run something.

### D5. `.env.example` and the coverage comment

Proposed `.env.example` comment above `OPENROUTER_API_KEY`:

```
# Metered OpenRouter runs only: `poe matrix` and the other cost-gated Inspect
# tasks, or a bare `inspect eval` — the cross-vendor rows and the source of
# record. Dev runs, routing and grading use your Claude subscription and need
# no key here. A metered call on an Anthropic model needs the gate or an
# explicit approval (AGENTS.md, "Metered model calls"). A key with a low
# monthly limit caps mistakes. Key: https://openrouter.ai/settings/keys
```

- It names no poe task other than `matrix`, so add-dev-runner-judge's smoke retarget leaves it true.
- The low-limit suggestion is critique C5's fix. Setting the limit is the user's action.
- **Rejected: mentioning the Console API key.** That fallback exists only if fix-openrouter-caching's gated probe fails (decision 3), so documenting it now would point at a path nobody has set up.

Proposed coverage comment:

```
    # skill_evals.py runs only under `inspect eval` (metered), never at L0.
    # claude_runner.py drives the real host on the subscription, but L0 tests
    # run its staging, parsing and verdict code; the entry stays until
    # add-dev-runner-judge removes it or records why it stays
```

- **Only `skill_evals.py` is unreachable at L0.** `claude_runner.py` is not. `tests/unit/test_dev_runner_probe.py`, `test_citation_practice.py` and `test_measurement_isolation.py` import it and run `stage`, `verdict`, `parse_events`, `telemetry`, `summary`, `host_command` and more.
  - Measured on 2026-10-05 at 9c106aa, using a scratch coverage config that omits only `skill_evals.py` and the full L0 suite (1993 passed, no model calls). `claude_runner.py` was 65% covered: 79 of its 228 statements missed, mostly `run_claude`, `main` and the host paths. The total was 84% with the file counted and 85% with it omitted, so the 78% floor holds either way.
  - Omitting a file whose code L0 does run hides that tested code from the floor. AGENTS.md names this failure mode. A comment saying "neither executes at L0" would hide it a second time.
- **The omit list still does not change here.** The decision goes to add-dev-runner-judge (D7):
  - Its task 2.6 adds in-process `main(argv)` tests of the runner's new exit-status, summary and rejudge logic. Those are the tests the entry would hide.
  - Its task 7.2 already runs the floor check.
  - It either drops the entry and extends 7.2 to show `claude_runner.py` in the report, or records why the entry stays. Either way it rewrites the comment's last clause.
- **Rejected: dropping the entry in this change.** The measurement says the floor would hold. But the change would move a coverage-config decision into a docs change and settle it ahead of the change that owns the runner's tests.
- **Rejected: putting the measured percentages in the comment.** They go stale with the next test, and design.md is where they are recorded.

The new `harness/claude_cli.py` from add-dev-runner-judge stays off the list; that is its own decision.

### D6. Re-grading recorded artifacts is never metered, with no exception

Re-grading is a text job over artifacts that already exist. The model under test is not involved, so nothing about it needs Inspect or a metered provider.

- **Until add-dev-runner-judge ships `--rejudge`,** re-grading happens on the subscription by whatever means is at hand: the agent's own session, or a `claude -p` call.
- **Rejected: "never metered unless approved".** The 2026-10-04 re-grade was approved. The fix is to take the metered option away for this job, not to ask about it more carefully.
- **The matrix's own L2 grading is not re-grading.** It runs inside a gated matrix run and stays metered until Change D.

### D7. Lines left to later changes

Each line below is left untouched here. The owning change rewrites it. Line numbers are those of the file before this change; the D4 table shifts every later `harness/README.md` line, so the owning changes locate each line by its quoted text or section, not by number.

| Line | Owner | Why |
|---|---|---|
| `harness/README.md:88` "a one-shot `claude -p` cannot hold the dialogue" | add-dev-runner-judge | It describes the subscription's limits next to `--judge`. |
| `harness/README.md:94` "Inspect twins … add two L2 rubric scorers" | add-dev-runner-judge | It becomes untrue once `--judge` grades on the dev runner. |
| `harness/README.md:104` "no L2 judging … not the source of record" | add-dev-runner-judge | Its "no L2 judging" half depends on `--judge`. |
| The table's L2 row (D4) | add-dev-runner-judge | It splits into "L2 iteration: `poe dev --judge --isolated`" and "L2 of record: matrix". |
| `AGENTS.md:67`, `harness/README.md:38`, the table's smoke row | add-dev-runner-judge | `smoke` moves to the subscription and the metered command becomes `smoke-inspect`. |
| `harness/claude_runner.py:8` "No judge/L2 (use Inspect for that)" | add-dev-runner-judge | It is code, and it is the `--judge` docstring. |
| `pyproject.toml` omit entry `"harness/claude_runner.py"` and the comment's last clause (D5) | add-dev-runner-judge | Its in-process `main(argv)` tests (task 2.6) are the code the entry hides. It drops the entry, with `claude_runner.py` shown in its 7.2 floor check, or records why the entry stays. |
| `harness/README.md:15` `deepseek-v4-flash` example ID, the source of the `:18` default, `skill_evals.py:8-13` docstring | track-model-currency | Model currency and the `[roles]` registry. |
| The currency-check sentence in the D2 rule | track-model-currency | It may name its checker. |

Reviewed and left as is: `README.md:187` ("`harness/` holds the L1/L2 model evals") is neutral. `docs/getting-started.md:7` is user-facing and neutral.

### D8. No mechanical enforcement is added

The existing enforcement covers the poe tasks: the matrix gate (`matrix.confirm_spend`, held by `test_matrix_gate_declined_makes_no_metered_call`). The rule's "Enforcement" clause says honestly that nothing in the repository sees a scratch script. The Git rule took the same stance (2026-09-01-relax-git-workflow-rule).

Rejected alternatives:

- **An L0 test that bans phrases such as "metered smoke".** It tests wording, not conduct. It breaks on the next honest rewrite, and any paraphrase gets past it.
- **Permission `ask` rules** for `--env-file .env` or `inspect eval` in `.claude/settings.json`.
  - These commands already prompt, because no allow entry covers them.
  - The 2026-10-04 re-grade was prompted and approved. What went wrong was the content of the request: no alternative was named and the estimate was off by 3.8×. The rule addresses exactly that.
  - Pattern rules also cannot see a key exported into the shell.
- **A harness guard that refuses `openrouter/anthropic/*` outside the matrix.** That is a behaviour change on the metered path, which fix-openrouter-caching owns, and it needs a spec delta. It is outside a docs change.

### Critique dispositions relevant to this change (final.md §7)

- **C5** (steering outside the repo docs: memory, worktrees, scratch scripts).
  - This change adds the `AGENTS.md` rule that names scratch scripts and ad-hoc re-judging (D2), and the low-limit key suggestion (D5).
  - Memory files, the worktree `.env` symlink and the key limit are step 0 in final.md §4. They live outside the repository and are not part of this change.
- **C4** (routing row contradicts itself). The D4 table makes no "never `prepare_config`" claim.
- **C1 / C2** (quota draw; "$0" only while overage is off). Both are carried into `AGENTS.md:98` and the note under the table (D3, D4).
- **V6 / F5** (the dev runner measures a different system; ambient runs are contaminated). Partly carried:
  - The table recommends `--isolated` when a dev-runner result is cited as a measurement.
  - The matrix stays the path for shipped verdicts.
  - Making `--isolated` mandatory for `--judge` and for smoke belongs to add-dev-runner-judge.
- **V1** (mixed judges in shipped verdicts). The `:18` rewrite states that the matrix judge is pinned on purpose (decision 1) and must not be replaced ad hoc.

## Risks / Trade-offs

- **[Risk] Agents never re-read the rule. They act on auto-memory, which still says OpenRouter is authoritative.** → Mitigation: memory is corrected under final.md step 0, outside this change. The rule's wording ("scratch script, ad-hoc re-judge") is written to match the shape of the 2026-10-04 incident, so it triggers on the next one.
- **[Risk] Between this change and add-dev-runner-judge, L2 iteration on an Anthropic model has no subscription path.** The rule then turns every such run into an approval request. → Accepted. The request must name the $0 alternative, which for now is the L1-only dev run. That is the point: the user decides with both options in front of them.
- **[Risk] The labels in D3 and D4 go stale when later changes land.** → Mitigation: D7 lists every line a later change must rewrite. The rule names no task that changes backend.
- **[Trade-off] The rule is longer than the other Hard rules.** → Accepted. Rule, why and enforcement is the house style, and the why carries the figures that make the rule credible to the next agent.
- **[Trade-off] No mechanical guard (D8).** → Accepted, and the rule says so explicitly.

## Migration Plan

No migration is needed. These are prose edits only, and a revert restores the previous text exactly. The change lands before track-model-currency. Each later change rebases onto it and rewrites the lines D7 assigns to it.

## Open Questions

The user's decisions are final. These are the assumptions this design makes in their place:

- **Non-Anthropic metered calls stay under the existing gate sentence only.** Decision 5 is about Anthropic models, and OpenRouter is the only route for the others.
- **The currency check stays manual until track-model-currency lands.** The catalog URL is enough guidance for that window.
- **add-dev-runner-judge takes up the `claude_runner.py` omit entry (D5, D7) — resolved.** Its task 1.4 drops the entry and rewrites the comment, and its 7.2 floor check lists `harness/claude_runner.py`. Task 5.3 still confirms the handoff. Until that change lands, the comment's last clause names it as the owner of the decision.
- **Step 0 of final.md is handled outside this change by the orchestrating session or the user.** That covers the memory files, the worktree `.env` symlink, the key limit and the overage setting. The change does not depend on it.
