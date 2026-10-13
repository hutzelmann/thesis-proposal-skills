# Route bug-report questions to proposal-troubleshoot

## Why

Task 6.1 of the archived `2026-10-05-fix-troubleshoot-model-match` asked haiku (`claude -p`, subscription, one call) the `troubleshoot_model_rung` request: "The write skill produced a draft that ignored half of what I told it. … Is this a bug I should report?" It failed before the rule under test could run:

- `proposal-troubleshoot` was listed in `init.skills`;
- haiku made no `Skill` and no `Read` call (`num_turns` 1);
- it answered from general knowledge, and rung 1 was never reached.

That is a routing failure, not a misapplied matching rule. The archived design (Risks, Open Questions) still names the D1 read-only lookup mode in `collect.py` as the follow-up. That follow-up cannot help, because a lookup mode also needs the skill loaded. The archive is edit-denied by `.claude/settings.json`, so this change carries the correction.

The same pattern was measured for `proposal-write` on 2026-10-04: haiku made 0/3 `Skill` calls on polishing requests, and the lever was the description (`route-polish-to-write`, branch of that name). `proposal-troubleshoot`'s description has the same gap. Its whole trigger clause is "Use when a skill misbehaved", which carries none of the words a user brings: a bug, reporting it, a skill that crashed or ignored what it was told. No routing case asks "is this a bug I should report?", so the routing rig cannot see the gap.

## What Changes

- **Routing cases** (`harness/routing_cases.toml`):
  - `troubleshoot-report-collision`: the current `troubleshoot_model_rung` request without its model identifier, expected `proposal-troubleshoot`. Since `desktop-first-install`, its reinstall sentence names the install prompt rather than `npx skills add`; otherwise it is the 6.1 request. It names "the write skill" and "a draft", so it is parked in `proposal-write`'s zone. The identifier is dropped because Rule A of `tests/unit/test_model_ids.py` admits no model ID in `harness/*.toml` other than the registry; the routing decision does not depend on it.
  - `troubleshoot-report-oblique`: a short question with no skill named, "I asked the proposal assistant to leave my research questions exactly as they are, and it rewrote them anyway — twice now. Is that a bug I should report?", expected `proposal-troubleshoot`.
    - It was first worded "This is the second time the tool did the opposite of what I asked. …". That pointed at an event a fresh session cannot see, and during measurement both models answered by saying so.
    - It was rewritten to carry its own context (measurement.md, Run 5).
- **Description, conditional on measurement** (`skills/proposal-troubleshoot/SKILL.md`). The trigger clause is widened to the situations a user names:

  > Use when a skill misbehaved — crashed, ignored the user's instructions, flagged something plainly there — or the user asks whether something is a bug they should report. Not for improving the proposal.

  The what-clause is unchanged. The description grows from 291 to 425 characters, within the 500 budget. If the edit is kept, `tests/unit/data/trigger_terms.json` assigns "a bug they should report" to `proposal-troubleshoot`, so the boundary is visible in review. "a skill misbehaved" stays owned and stays in the text.
- **Measurement, subscription only** (routing rig; no dev runner, OpenRouter, Inspect or matrix call), recorded in `measurement.md`:
  - haiku, before and after the edit, on the five troubleshoot cases plus every `review-*` and `write-*` case as the theft guard;
  - sonnet, the full set at 1 epoch on the final state, as a theft scan over every skill's cases. It runs with `--no-report`, because `docs/skill-routing.md` holds a 3-epoch sweep (138/138, fefeced) that a 1-epoch run must not replace.
- **Decision** (design.md D3): keep the edit only if haiku moves on the two new cases, the existing troubleshoot cases do not drop, and no measurement of another skill's case on either model selects `proposal-troubleshoot`. Otherwise revert it. The new cases stay as the record of the gap, and haiku's `note` in `harness/models.toml` says that bug-report questions do not reliably reach `proposal-troubleshoot` and that naming the skill does. `poe report` carries that note into the README.
- **Record correction.** `measurement.md` states that the archived D1 follow-up is superseded: the 6.1 miss is routing, and a lookup mode is not the next step.
- **Docs.** `harness/README.md` updates the routing case count from 46 to 48.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none. `skip_specs: true`.)

No requirement pins which situations a given description names, or the routing case list:

- `skill-packaging` constrains the form of descriptions (third person, what and when clauses, budgets) and the trigger-ownership mechanism. The edit stays inside both.
- `testing-harness` constrains the dataset's composition (three kinds per skill, negatives, German cases) and workspace staging. Both stay satisfied: the new cases name no file, so the default proposal is staged.
- `skill-troubleshoot` specifies the ladder and the report, not how the skill is selected.

## Impact

- `harness/routing_cases.toml`: two cases.
- `skills/proposal-troubleshoot/SKILL.md` frontmatter and `tests/unit/data/trigger_terms.json`, only if the edit is kept. The combined metadata rises by 134 characters, from 4338 to 4472 of 4500 on `main` (a4e1b68).
- `harness/models.toml` haiku `note`, joined to the polish note already there, and the README model-support row it generates, only if the edit is reverted.
- `harness/README.md` (case count). `docs/skill-routing.md` stays as it is; the two new cases enter it at the next 3-epoch sonnet sweep.
- Built on `main` at a4e1b68. It carries:
  - `route-polish-to-write` (c3c1b72) and `record-polish-routing-boundary` (0f1e8b3), which touch the same files;
  - `isolate-child-environment` (7d9fcae, c997e72);
  - `close-claudeai-surfaces` (a4e1b68), which keeps the account's synced claude.ai skills and connectors out of rig runs.
- Model calls: at most five routing-rig runs on the Claude subscription (design.md D4). No metered call.
