# Design

## Context

See proposal.md, Why, for the defect and the evidence. Four facts shape the approach:

- **The prose is the runtime path; the function is not.** `resolve_model` (`skills/proposal-troubleshoot/scripts/collect.py:542-561`) has no caller in the shipped skill. Only `tests/unit/test_troubleshoot_collect.py` imports it. At rung 1 the agent reads `references/model-support.json` itself and follows `SKILL.md:39`. A fix to the function alone would change nothing a user sees.
- **Rung 1 must work without Python.** Rung 3 diagnoses "a missing `python3`". The model rung sits above it on a ladder ordered cheapest-first, and the mandate says to work the ladder "before you collect anything".
- **The shipped keys are generated.** `harness/report.py` writes the roster IDs minus `openrouter/` into `shared/model-support.json`, and `scripts/sync_shared.py` vendors that file into the skill. `track-model-currency` will bump the roster to `anthropic/claude-{sonnet,opus}-5.5`, and `report.py:50` then drops the 5.0 rows. Any test that reads a specific key from the shipped file breaks on that bump.
- **Host spellings were observed, not assumed.** The 2026-10-04 alias probe recorded `claude-haiku-4-5-20251001`, `claude-sonnet-5-5`, `claude-opus-5-5` and `claude-fable-5-1`. Sonnet 5.5 has no dated full ID in Anthropic's model table (critique: full-ID reproducibility). OpenRouter's canonical slugs are dated (`claude-sonnet-5.5-20260928`). A rule therefore has to accept the same model both with and without a date.

The defect was confirmed on 2026-10-05 by calling `resolve_model` in-process, read-only, against the shipped file. `claude-haiku-4.5` resolves to the failing haiku record. `claude-haiku-4-5-20251001` and `claude-haiku-4-5` resolve to nothing. A sketch of the rule below resolved every Claude Code, Bedrock, Vertex and `[1m]` spelling of haiku. It left `claude-opus-5-5`, `claude-haiku-4` and `haiku` unresolved, and found no collisions among the nine shipped keys.

## Goals / Non-Goals

**Goals:**

- The model a host reports finds its verdicts whenever the data holds that model, under any spelling a current host produces.
- A model the data does not hold, including a newer version of one it does hold, stays unevaluated.
- The prose rule and the code rule are the same rule, and a test fails if they drift.
- The tests survive the roster bump in `track-model-currency` without edits.

**Non-Goals:**

- Moving the rung-1 lookup into a script. See D1.
- Matching display names ("Claude Haiku 4.5"), aliases (`haiku`, `opus`) or Bedrock application-inference-profile ARNs. None of these names a version, so all of them stay unevaluated.
- Changing what the shipped data holds or how `report.py` generates it.
- Strengthening `verdict_troubleshoot_model_rung`. See Open Questions.

## Decisions

### D1: The prose stays the runtime path, and the function is its executable statement, pinned by a parity test

Rung 1 keeps the agent doing the lookup. The rewritten sentence states the normalisation and gives one real example pair, and it is pinned in `tests/unit/data/pinned_sentences/proposal-troubleshoot--model-match.txt`. A new L0 test extracts the two backticked identifiers from that pin and asserts that `resolve_model` maps one to the other, using a synthetic support file. If the prose is reworded, the pin has to change in the same diff. If the code changes, the example has to keep resolving.

*Rejected: a read-only lookup mode in `collect.py` (`--model-verdict ID`) that rung 1 runs.* It would make the match deterministic for weak models. But rung 1 would then depend on `python3`, which rung 3 exists to diagnose. It would also put a script call before "collect anything" in a script named for collecting, and add CLI surface to an audited user-side skill. If an eval later shows models misapplying the prose rule, a lookup mode can be added. That would be its own change, with the prose fallback kept.

*Rejected: fixing only the function.* A user would see no difference (Context, first point).

### D2: Symmetric normalisation, then equality

`normalize_model_id(name)` is a pure function in `collect.py`, standard-library `re` only. It applies these steps in order:

1. `strip()` and `lower()`.
2. Drop a trailing bracketed variant (`\[[^\]]*\]$`, for example `[1m]`).
3. Keep only what follows the last `/`.
4. Drop a cloud vendor prefix (`^(?:[a-z]+\.)?anthropic\.`, for example `us.`, `eu.` or `global.` followed by `anthropic.`).
5. Drop a cloud revision, colon form only (`-v\d+:\d+$`, for example `-v1:0`).
6. Drop a trailing date stamp (`[-@]20\d{6}$`, which covers `-20251001` and Vertex's `@20251001`).
7. Replace each dash between two digits with a dot.

`resolve_model` first tries the exact string, after dropping `openrouter/` as today. It then normalises every key and the reported name the same way, and accepts exactly one key whose normalised form equals the reported one.

Order matters. The revision step has to run before the date step, or the date is not trailing. The date step has to run before the digit step, or `4-5-20251001` turns into `4.5.20251001`.

Applying the same normalisation to both sides guarantees that every shipped key resolves to itself. The only failure this rule can produce is a collision, and D4 handles that.

*Rejected: suffix or prefix matching on the normalised form.* `claude-opus-5-5` would then match `claude-opus-5`, which would report a version's predecessor's verdict as the user's own.

*Rejected: fuzzy matching (edit distance).* `claude-opus-5` and `claude-opus-5.5` are one edit apart, so the version guard could not be stated.

*Rejected: an alias table in the shipped data, or emitting Claude Code spellings from `report.py`.* Either one adds a second spelling per key to generated data. It would only ever cover the hosts someone thought of, and it would break the rule that keys mirror registry IDs.

### D3: Cloud wrappers are stripped narrowly

The revision step requires the colon form that Bedrock uses (`-v1:0`). A bare `-v\d+$` would turn `deepseek-v4` and `deepseek-v3` into the same `deepseek`, so a version would match another version. The sketch caught this. An L0 test pins that a `-vN` suffix without the colon survives. The vendor-prefix step only fires on an `anthropic.` segment, the one cloud vendor prefix a Claude model carries.

### D4: Ambiguity resolves to none

If two keys normalise to the same spelling, `resolve_model` returns `(None, {})`, as the suffix rule already does today. The spec's absence rule then applies, and the rung is unevaluated. Choosing one key would report a neighbouring entry's verdict as the user's. No collision exists in the shipped data today, and a property test over the shipped file pins that. If a future roster bump introduces one, that test fails in CI rather than in a user's workspace.

### D5: Tests are decoupled from the shipped keys

The existing tests at `test_troubleshoot_collect.py:307-316` key on `anthropic/claude-opus-5`, which the bump removes. The matching tests move to a `support_file` fixture written into `tmp_path`, and `resolve_model` already accepts `support_path`. The fixture holds the spellings of the roster as `track-model-currency` bumps it, plus two keys kept only as guards:

- `anthropic/claude-haiku-4.5`
- `anthropic/claude-sonnet-5.5`
- `anthropic/claude-opus-5.5`
- `openai/gpt-6-luna`, the non-Anthropic key
- `anthropic/claude-opus-5`, kept for the version guard
- `deepseek/deepseek-v4`, kept for the colon-form revision guard (D3); it is not a roster ID

Two tests still read the shipped file, and both are properties that hold under any roster:

- every key resolves to itself;
- every `anthropic/` key resolves from its Claude Code spelling, both bare and with a date, and the shipped keys produce no collisions.

`test_resolve_model_reports_a_known_failing_skill` keeps reading the shipped haiku record, because it pins the measured fact that the eval relies on. It now resolves the eval prompt's own spelling, `claude-haiku-4-5-20251001`, so the eval's expected outcome and the data cannot drift apart. Haiku stays on the roster (final.md §2). If a later currency bump ever replaces it, this test fails together with the eval prompt it guards, which is the intended pairing.

### D6: Exact identifiers in rung 1 and in the report

Rung 1 and assembling-the-report step 4 both ask for the identifier the host states. The step 4 wording already tells the agent to say "I don't know" rather than guess, and that stays. The issue-template placeholder becomes `claude-sonnet-5-5`, because a maintainer resolves the self-reported line with the same rule. This is the "Measured facts" delta in the spec.

### D7: The eval prompt uses the host's spelling, and the verdict is unchanged

`troubleshoot_model_rung` (`harness/skill_evals.py:1053-1056`) says "I was running claude-haiku-4-5-20251001", and the comment above it is updated. It is an `extended` task, not a matrix task, so no shipped verdict loses comparability. The `evals.json` projection is regenerated with `harness/eval_export.py`, and the drift gate checks it.

The comment at `:1031-1036` also names `claude-haiku-4.5` today. Under the guard's Rule A, comments in `harness/**/*.py` count, and the (path, token) pair exempts one token only. The rewritten comment therefore names no model except the prompt's own `claude-haiku-4-5-20251001`.

### D8: Spec scenarios use synthetic identifiers

The spec delta names no real model. Its scenarios use the synthetic family `lab/example-*`, with host spellings such as `example-4-5-20251001` and `example-5-5`, and the alias `example`. The requirement prose describes the Claude Code spelling in words, not by an ID. The real example stays in three places:

- `SKILL.md`, which the agent needs;
- the pin and the L0 tests, which check it;
- this change record, which is exempt from the guard as a change record.

Archiving syncs the delta into `openspec/specs/skill-troubleshoot/spec.md`. A real ID there would break in two ways:

- **It goes stale in meaning.** "`claude-opus-5-5`, and the data holds no 5.5 entry" is false the moment `track-model-currency` adds the 5.5 rows.
- **It goes stale under the guard.** `track-model-currency`'s Rule B ("current or nothing") flags `anthropic/claude-opus-5` after the bump. A main spec can only be edited through another OpenSpec change, so every weekly bump PR would then fail on a file the PR cannot fix.

Synthetic IDs satisfy the guard however `track-model-currency` scopes it. If it allowlists `openspec/specs/**`, this spec does not use the exemption. If it does not, there is nothing for it to flag. The guard's base pattern covers the Claude, GPT, DeepSeek, Qwen, Kimi and Gemini families plus every registry line, and `example` is none of those.

*Rejected: keep the real IDs and rely on `track-model-currency` allowlisting `openspec/specs/**`.* That allowlist belongs to the other change, and this change cannot depend on how it is resolved. It would also leave the spec making a claim that is false after the bump, namely that no 5.5 entry exists.

*Rejected: real IDs that are current today.* Every Anthropic ID in the scenarios goes stale at some bump. That includes haiku 4.5: it is pinned today, but nothing guarantees it stays pinned.

### Critique dispositions relevant to this change (final.md §7)

- **Full-ID reproducibility (minor, accepted).** That critique asked for resolved IDs to be recorded so a run can be identified. Here it becomes the D6 rule that the agent reports the exact identifier the host states. It is also the reason D2 tolerates a missing date: `claude-sonnet-5-5` has no dated form.
- **Decision 5, the user's policy of no OpenRouter spend on Anthropic models where the subscription can do the job.** The optional behavioural check in tasks.md runs on the subscription. The metered Inspect run is a gated fallback, never a default.
- **The remaining blockers and majors (V1–V6, F1–F5, C1–C5) concern judge, persona and caching routing.** None of them touches this change.

### Review findings on the proposed change set (2026-10-05)

- **Major: concrete IDs in spec deltas sync into `openspec/specs/**` and fail Rule B after the bump. Accepted.** D8 replaces them with synthetic IDs. Task 7.1 re-runs `uv run poe test` after the archive and greps the synced spec. `track-model-currency` owns the decision on allowlisting `openspec/specs/**`, and D8 holds whichever way that goes.
- **Minor: order and guard hand-off contradict `track-model-currency`. Accepted.**
  - This change lands before that change's task 6.1 (§Coordination, order).
  - Task 5.1 edits nothing in the guard: no troubleshoot file is parked, and `track-model-currency` alone swaps the `troubleshoot_model_rung` token pair (§Coordination, guard).
  - The old claim "before or after" is withdrawn.

### Coordination with the parallel changes

- **`track-model-currency`: order.** This change lands on `main` before `track-model-currency` reaches its task 6.1. That change's regeneration removes `anthropic/claude-opus-5` from the shipped file, and today's `test_troubleshoot_collect.py:307-316` keys on that row. Its task 6.1 therefore stops until tasks 1.1–1.2 here have landed, and it does not edit this change's files. This change may land before `track-model-currency` starts or while it is paused at tasks 1–5. It cannot land after that change completes. Once both have landed, its roster bump needs nothing more from this change: after `poe report` and `sync_shared.py` run, the 5.5 rows are matchable from `claude-sonnet-5-5` and `claude-opus-5-5`.
- **`track-model-currency`: guard.** That change adds `tests/unit/test_model_ids.py`, which applies two rules:
  - Rule A: no literal model ID in code or configuration;
  - Rule B: in every other tracked file, a model ID must be current.

  Its design (D6) already carries the entries for the files this change touches. Here is what each file needs once both changes are in one tree:

  | File | Guard rule | What it needs |
  |---|---|---|
  | `tests/unit/test_troubleshoot_collect.py` | permanent whole-file entry (normalisation test data) | nothing |
  | `tests/unit/data/pinned_sentences/proposal-troubleshoot--model-match.txt` | Rule B; haiku 4.5 is current | nothing |
  | `skills/proposal-troubleshoot/SKILL.md`, `scripts/collect.py` | Rule B; before the bump the old `claude-opus-5` example is a current pin, and its replacement `claude-haiku-4-5-20251001` resolves to the unchanged haiku row | nothing; no parked entry exists |
  | `harness/skill_evals.py` | Rule A, plus a (path, token) pair for the prompt | nothing here; `track-model-currency` writes the pair with the spelling it finds and, if that is `claude-haiku-4.5`, swaps it to `claude-haiku-4-5-20251001` in its task 6.1 (D7) |
  | `.github/ISSUE_TEMPLATE/skill-defect.yml` | Rule B; `claude-sonnet-5-5` resolves to the roster pin or to `roles.dev_judge` | nothing |
  | `openspec/specs/skill-troubleshoot/spec.md`, after the archive | names no recognised ID (D8) | nothing |

  The guard never reaches `main` before this change: `track-model-currency` commits once, after its task 6.1 has waited for this change. This change therefore edits nothing in `test_model_ids.py` and adds no entry. The token-pair swap has a single owner, `track-model-currency` task 6.1, and is not needed when that change's task 0.1 already found `normalize_model_id` and wrote the new spelling.
- **`steer-subscription-first`** does not touch the issue template or the troubleshoot skill (checked by grep on 2026-10-05).
- **`add-dev-runner-judge`** reworks `harness/claude_runner.py`. This change deliberately adds no dev-runner scenario, to avoid conflicting with it. See Open Questions.

## Risks / Trade-offs

- [A weak model misapplies the prose rule] → The rule comes with a worked example that is haiku's own identifier, the model most likely to need it. The optional $0 check in tasks.md runs exactly that case. If it fails, the deferred lookup mode (D1) is the follow-up.
- [A future host spelling falls outside the rule, such as an ARN or a new cloud wrapper] → It resolves to nothing, so the rung reads unevaluated, which is the spec's safe failure. It never reports a wrong verdict.
- [The `[1m]` variant shares the base model's verdict although its context window differs] → The weights are the same and the verdicts measure instruction following, not context length. Recorded as an assumption in Open Questions.
- [Ignoring everything before the last `/` lets `someone/gpt-x` match `openai/gpt-x`] → Model names are vendor-specific in practice. If two vendors ever ship the same name, the collision guard (D4) returns none.
- [Changing the eval prompt makes past `troubleshoot_model_rung` logs incomparable] → The task is on-demand and feeds no shipped verdict.
- [A future haiku bump makes the rung-1 example stale] → Rule B fails that bump PR on `SKILL.md` and on the pin, which is the intended prompt to pick the example again. `test_resolve_model_reports_a_known_failing_skill` fails in the same PR (D5). The parity test (D1) uses a synthetic support file, so it keeps passing. The spec does not need touching, because it names no real ID (D8).
- [This change has not landed when `track-model-currency` reaches its task 6.1] → That task is a hard stop, guarded by a grep, so the failure is a paused branch, never a red `main`.

## Migration Plan

There is no data migration. The change ships on `main` with the skill files. Users pick it up on their next `npx skills add`, which rung 0 already tells them to run. Rollback is reverting the commit. The shipped `references/model-support.json` is untouched, so no `sync_shared.py` run is needed beyond the usual check.

## Open Questions

- **A dev-runner scenario for `troubleshoot_model_rung`.** It would make the behavioural check $0 and repeatable. It is deferred until `add-dev-runner-judge` has landed, because that change reworks `claude_runner.py`. This affects neither the spec nor these tasks.
- **A read-only lookup mode (D1, rejected for now).** This becomes a follow-up change only if the optional behavioural check (tasks 6.1/6.2) or a later eval shows a model misapplying the prose rule. Any such change keeps the prose path as the fallback for a workspace without `python3`.
- **Should `verdict_troubleshoot_model_rung` also require that the answer names the recorded failure?** That would let the eval tell "matched" apart from "fell through to unevaluated". It is deferred because phrasing variance risks false FAILs (memory: verify tooling before blaming models). The L0 tests are the decisive coverage for the rule.
- **Assumption: the guard does not read the synthetic `example-*` family, or the bare alias `sonnet` in the requirement prose, as model identifiers.** `track-model-currency` D6 recognises versioned vendor families and registry lines. `example` is neither, and an alias carries no version. The guard is not in this change's tree, so `track-model-currency`'s post-archive gate checks this once both are on one tree. If the guard does flag either one, the fix is a token-level entry with a reason in that change's allowlist, or a reworded scenario in a follow-up change. Weakening the guard is not an option.
- **Assumption: a `[1m]` context variant takes the verdict of the same model without the qualifier.** If the matrix ever measures the variants separately, they become distinct roster keys. The collision guard (D4) then returns none for the shared spelling, the shipped-file property test fails in CI, and the bracket step has to be revisited in that change.
