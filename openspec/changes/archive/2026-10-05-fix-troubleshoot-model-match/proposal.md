# Proposal

## Why

Rung 1 of `proposal-troubleshoot` cannot find the model that Claude Code is running. Claude Code reports dashed, sometimes dated identifiers. On 2026-10-04 its `haiku`, `sonnet` and `opus` aliases resolved to `claude-haiku-4-5-20251001`, `claude-sonnet-5-5` and `claude-opus-5-5` (spend-analysis dossier, alias probe). The shipped verdicts in `references/model-support.json` use OpenRouter's dotted keys, such as `anthropic/claude-haiku-4.5`. The rule at `SKILL.md:39` says to match on "the part after the last `/`", and `resolve_model` in `scripts/collect.py:542-561` does the same. Neither ever reaches the dotted key.

We first found this by reading the code, so it was run against the shipped data on 2026-10-05 to confirm it:

| Reported | `resolve_model` today | Should be |
|---|---|---|
| `claude-haiku-4.5` | `anthropic/claude-haiku-4.5`, failing | (unchanged) |
| `claude-haiku-4-5-20251001` | none | `anthropic/claude-haiku-4.5`, failing |
| `claude-haiku-4-5` | none | `anthropic/claude-haiku-4.5`, failing |
| `claude-opus-5-5` | none | none: no 5.5 row exists yet, so the rung is unevaluated |

The defect is real, but only half of it is in the script. `resolve_model` has no caller in the shipped skill: `main` never calls it, and only the L0 tests import it. At runtime the agent does the matching itself, following the prose at `SKILL.md:39`. That prose is what fails for a Claude Code user. The result is that a user on haiku gets "unevaluated, move on". Haiku is the only model whose verdicts include `fail` (`proposal-write`, `proposal-review`, `proposal-customize`). The answer the spec requires is "the model is the cause". The same miss will hit sonnet and opus once `track-model-currency` adds the `anthropic/claude-*-5.5` rows, because Claude Code reports them as `claude-sonnet-5-5` and `claude-opus-5-5`.

The tests that pin the current behaviour (`tests/unit/test_troubleshoot_collect.py:307-316`) read the shipped verdict file and key on `anthropic/claude-opus-5`. They break as soon as the roster bump and `poe report` drop that row (`harness/report.py:50`). No money is involved. What goes wrong is the answer the user gets.

## What Changes

- **One matching rule, stated in prose and implemented in code.** The prose rule is what the agent follows at runtime. The code is the executable statement that L0 tests pin. The agent first looks up the model's exact identifier. If that string is absent, it compares the two spellings after normalising both sides the same way:
  - case and surrounding whitespace are ignored;
  - everything up to the last `/` is ignored, which covers routing and vendor prefixes;
  - a cloud provider's wrapping is ignored: a leading `anthropic.` with an optional region segment, such as `us.anthropic.`, and a trailing revision, such as `-v1:0`;
  - a trailing date stamp (`-20251001` or `@20251001`) is ignored;
  - a trailing bracketed variant (`[1m]`) is ignored;
  - a dash between two digits reads as a dot.
- **A different version is a different model.** Matching is equality of normalised spellings, never a prefix test. `claude-opus-5-5` never takes the verdict recorded for `claude-opus-5`. When two entries normalise to the same spelling, no entry is chosen and the rung reports as unevaluated.
- **The agent uses its exact identifier.** Rung 1 and the report's self-reported model line ask for the identifier the host states, never a display name or an alias such as `sonnet`. An alias names no version, so it cannot be matched to a verdict.
- `skills/proposal-troubleshoot/SKILL.md` rung 1 is rewritten with a current example: `claude-haiku-4-5-20251001` is keyed as `anthropic/claude-haiku-4.5`. The sentence carrying the rule is pinned in `tests/unit/data/pinned_sentences/`, and a parity test checks that the example pair in that sentence resolves through `resolve_model`.
- `skills/proposal-troubleshoot/scripts/collect.py`: a new pure `normalize_model_id`; `resolve_model` matches on it. This is user-side code: standard library only, no new CLI surface.
- `tests/unit/test_troubleshoot_collect.py`:
  - The matching tests move to a synthetic support file that uses the current IDs, so a roster bump cannot break them.
  - A property test over the shipped file checks that every key resolves to itself and every `anthropic/` key resolves from its Claude Code spelling.
  - New tests cover the version-distinctness and ambiguity guards.
- The `troubleshoot_model_rung` eval prompt (`harness/skill_evals.py`) states the model the way Claude Code reports it (`claude-haiku-4-5-20251001`), so the on-demand eval exercises the rule. The `evals.json` projection is regenerated.
- `.github/ISSUE_TEMPLATE/skill-defect.yml:71`: the placeholder becomes `claude-sonnet-5-5`, the ID Claude Code reports.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-troubleshoot`:
  - *Support verdicts shipped as skill data* gains the matching rule:
    - exact identifier first;
    - then normalised spelling equality;
    - a different version never matches;
    - ambiguity resolves to unevaluated.
  - *Measured facts distinguished from self-reported ones* gains the rule that the self-reported model identity is the exact identifier the host states, not a display name or alias.
  - The scenarios use synthetic identifiers (`lab/example-4.5`, `example-4-5-20251001`). Archiving syncs them into `openspec/specs/`, and a real model ID there would go stale at the next roster bump (design D8).

## Impact

- **User-side, shipped**:
  - `skills/proposal-troubleshoot/SKILL.md` (rung 1, assembling-the-report step 4);
  - `skills/proposal-troubleshoot/scripts/collect.py` (`normalize_model_id`, `resolve_model`, docstring).
  - Python ≥ 3.11 standard library (`re`), cross-platform.
  - No header-pattern block, mandate or existing pinned sentence changes.
  - `references/model-support.json` is untouched, because it is generated.
- **Dev-side**:
  - `tests/unit/test_troubleshoot_collect.py`;
  - a new pin `tests/unit/data/pinned_sentences/proposal-troubleshoot--model-match.txt`;
  - `harness/skill_evals.py` (one prompt string and its comment);
  - the regenerated `skills/proposal-troubleshoot/evals/evals.json`;
  - `.github/ISSUE_TEMPLATE/skill-defect.yml`.
- **Ordering: lands before `track-model-currency` task 6.1.** It is independent of the other three changes. `track-model-currency`'s regeneration drops `anthropic/claude-opus-5` from the shipped data. That breaks today's `test_troubleshoot_collect.py:307-316`, so its task 6.1 stops until this change's tests have moved to the synthetic file. This change may land before `track-model-currency` starts, or while it is in progress at tasks 1–5, but not after it.
- **Guard hand-off.** This change edits nothing in `track-model-currency`'s hardcoded-model-ID guard (`tests/unit/test_model_ids.py`). That guard never reaches `main` before this change, because `track-model-currency` commits once, after its task 6.1 has waited for this one. No troubleshoot file needs a parked entry, because the `claude-opus-5` example names a current roster pin until the bump. `track-model-currency` alone writes the `troubleshoot_model_rung` (path, token) pair in `harness/skill_evals.py`, and swaps it to `claude-haiku-4-5-20251001` in its task 6.1 if it wrote the old spelling (design.md §Coordination, task 5.1).
- **No metered run is required.** The matching rule is decided by pure functions under L0. An optional behavioural check of the prose is listed in tasks.md:
  - preferred: $0 on the subscription;
  - an Inspect run of `troubleshoot_model_rung` only behind an estimate and explicit approval.
