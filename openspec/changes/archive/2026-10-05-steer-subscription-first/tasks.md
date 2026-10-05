# Tasks

No task in this change makes a model call, metered or subscription. Every edit is prose. If a reviewer asks for a model run to check the effect of the steering, that run follows the new rule before anything executes. The request must:
- state the estimate and how it was derived;
- name the $0 subscription alternative;
- wait for the user's explicit approval in chat.

## 1. AGENTS.md

- [x] 1.1 Add the **Metered model calls** bullet to `## Hard rules`, after **Credentials**, using the wording in design.md D2. Verify:
  - `rg -n 'Metered model calls' AGENTS.md` returns exactly one bullet;
  - it contains "scratch script", "never metered" and "$0 subscription alternative";
  - it names no poe task other than `poe matrix`.
- [x] 1.2 Rewrite the comments on the `poe dev`, `poe smoke` and `poe matrix` lines (`:66-68`) as in the design.md D3 table. Verify: `rg -n 'metered smoke' AGENTS.md` returns nothing, and the `poe dev` comment contains "default for Anthropic models".
- [x] 1.3 Append to the gate paragraph (`:84`) the pointer to `harness/README.md`'s opening "Which path to use" table, keeping the existing `--yes` sentence word for word. Verify by reading the paragraph.
- [x] 1.4 Rewrite the comment on the raw `inspect eval` line (`:93`) to "metered and ungated — prefer poe matrix --models/--tasks; see "Metered model calls"". Verify: `rg -n 'L1/L2, metered' AGENTS.md` returns nothing.
- [x] 1.5 Rewrite the closing sentence (`:98`) with the quota and extra-usage caveat from design.md D3. Verify that it names both "money (OpenRouter)" and "plan quota (subscription".

## 2. harness/README.md

- [x] 2.1 Insert `## Which path to use` directly after the intro paragraph: the seven-row table and the "subscription" note from design.md D4. Verify:
  - it is the first `##` heading (`rg -n '^## ' harness/README.md | head -1`);
  - the table renders (preview the file);
  - no cell contains an unescaped `|` inside backticks.
- [x] 2.2 Rename the `:5` heading to "Inspect runs (OpenRouter, metered — source of record)". Add the lead sentence that reserves the path, says a bare `inspect eval` is ungated, and recommends `poe matrix --models … --tasks …`. Leave the code block's commands and model IDs untouched (track-model-currency owns `:15`). Verify: `rg -n 'Authoritative runs' harness/README.md` returns nothing.
- [x] 2.3 Rewrite the judge sentence (`:18`) as in design.md D4. Keep `JUDGE_MODEL` and its current default verbatim, and add `PERSONA_MODEL`, "pinned and metered on purpose" and "not an ad-hoc grader … never metered". Verify by reading the paragraph.
- [x] 2.4 In the matrix section:
  - add the source-of-record sentence (`:35`);
  - relabel `poe smoke` (`:38`) to match `AGENTS.md:67`;
  - extend the `--yes` sentence (`:45`) so it is the operator's to type, and an agent passes it only after the user approves that run's estimate in chat.

  Verify: `rg -n '~\$1\)' harness/README.md` returns nothing.
  - Note: design.md D4 gives the `:35` addition as a fragment ("The source of record for …"); it landed as a full sentence with "The matrix is" as its subject. The `--yes` extension landed as a second sentence after "`--yes` skips the prompt", which stays word for word.
- [x] 2.5 Reorder the baseline examples (`:53-57`) so `poe dev … --no-skill` comes first. Label each line: subscription; metered, gated; metered, ungated, needs approval. Verify by reading the block.
- [x] 2.6 Add "the default for Anthropic models" to the dev-runs heading (`:62`). Verify: `rg -n '^## Dev runs' harness/README.md` shows the new heading.
- [x] 2.7 Confirm that `:88`, `:94` and `:104` are unchanged, since add-dev-runner-judge owns them (design.md D7). Verify: `git diff harness/README.md` shows no hunk touching those three sentences.

## 3. .env.example and pyproject.toml

- [x] 3.1 Replace the comment above `OPENROUTER_API_KEY` in `.env.example` with the D5 text. Verify:
  - `rg -n 'Metered L1/L2' .env.example` returns nothing;
  - the comment names no poe task other than `poe matrix`;
  - the key line is still `OPENROUTER_API_KEY=` with an empty value.
- [x] 3.2 Replace the `[tool.coverage.run] omit` comment in `pyproject.toml` with the D5 text, leaving the two omitted paths unchanged. Verify:
  - `rg -n 'metered-only|neither executes' pyproject.toml` returns nothing;
  - `rg -l 'claude_runner' tests/unit` lists at least one test file, so the comment's claim that L0 runs part of the runner still holds;
  - the comment names add-dev-runner-judge as the owner of the `claude_runner.py` entry;
  - `git diff pyproject.toml` touches comment lines only.
- [x] 3.3 Run `uv run poe cov`. Verify: the 78% floor holds and the TOTAL is unchanged from before the edit, since the omit list did not change.
  - Result 2026-10-05: before and after the edit both report TOTAL 4268 statements, 654 missed, 84.68% (1993 passed).

## 4. Sweep and gate

- [x] 4.1 Run `rg -n -i 'metered' AGENTS.md harness/README.md .env.example pyproject.toml` and check every hit. Each must:
  - label a path as gated or ungated;
  - state what the path is reserved for; or
  - be history (dated measurements, Known limitations), or one of the three D7 lines left to add-dev-runner-judge.

  No hit may present a metered path as the default for an Anthropic model.
- [x] 4.2 Run `git diff --stat` and confirm that only `AGENTS.md`, `harness/README.md`, `.env.example`, `pyproject.toml` and this change folder changed. No code, test, fixture, spec or generated copy should appear.
- [x] 4.3 `uv run poe test` is green. That is the full L0 chain: pytest including the private-directory guard, ruff, drift check and conform. `poe test-fast` does not count.
- [x] 4.4 `uv run poe specs` is green. `openspec validate --all --strict` accepts this zero-delta change through `skip_specs: true`.
- [x] 4.5 Gated measurement: none. This change makes no model call, so no estimate or approval is needed. Record that in the commit body. If a run is nonetheless requested, follow the preamble above: estimate, the $0 alternative named, explicit approval, then run.

## 5. Archive and commit

- [ ] 5.1 Archive through the `openspec-archive-change` skill (`openspec archive steer-subscription-first`). Never move the folder by hand. Verify that the folder lands under `openspec/changes/archive/` with a date prefix, and that `openspec/specs/` is unchanged, since there is no spec sync under `skip_specs`.
- [ ] 5.2 Make one commit for the completed change, ending with the session's attribution line. Commit on the working branch, merge to `main` only once complete, and do not push. Verify: `git log -1 --stat` lists the four files plus the archived change folder.
- [x] 5.3 Handoff check. Confirm that the in-flight track-model-currency and add-dev-runner-judge proposals list the lines design.md D7 assigns to them. For add-dev-runner-judge, that includes the `claude_runner.py` coverage-omit entry: it either drops the entry, with `claude_runner.py` shown in its 7.2 floor check, or records why the entry stays. Where one does not, note it in that change rather than editing it from here.
  - Result 2026-10-05 (checked before archiving): both changes cover every D7 line, so no note was added to either.
    - add-dev-runner-judge: the path table's L2, smoke and re-grade rows, the model-support `poe smoke` line, the citation-scenario paragraph ("Inspect twins"), the "no L2 judging" sentence and the "cannot hold the dialogue" sentence (task 6.1); the `AGENTS.md` smoke line (6.2); the `claude_runner.py:8` docstring line (5.6); the omit entry, dropped in 1.4 with `harness/claude_runner.py` listed in the 7.2 floor check.
    - track-model-currency: the `deepseek-v4-flash` example and the judge sentence's default source, keeping the `JUDGE_MODEL`/`PERSONA_MODEL` wording (4.2); the `skill_evals.py:8-13` docstring; the currency sentence of the "Metered model calls" bullet, replaced by `uv run poe models` with the rest kept verbatim.
