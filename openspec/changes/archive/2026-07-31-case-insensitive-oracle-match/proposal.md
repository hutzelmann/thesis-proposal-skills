## Why

The `check_report` verdict counts how many of the fixture's oracle errors the skill relayed into chat, by substring match. The match is case-sensitive, and the task it judges is prose relaying — so a model that reports every error correctly scores 1/5 because it began its sentences with capitals:

| oracle needle | relayed as | matched |
|---|---|---|
| `duplicate reference id` | "**D**uplicate reference id `Lee24Index`" | no |
| `cited key` | "**C**ited key `@Ghost99Missing` not defined" | no |
| `boolean literal` | "is YAML boolean literal" | yes |

Both models tested relay all five errors and score 0–1 of 5. The scenario therefore reads red while the skill is working, which is worse than no signal: it trains the reader to ignore the result. The defect predates the current work — the pre-session baseline fails identically — and is distinct from the Inspect-path redness already documented, which has a different cause.

## What Changes

- Oracle-needle matching in the check-report verdict becomes case-insensitive. Nothing else about the assertion changes: the same needles, the same threshold, the same requirement that the proposal stay byte-identical.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: the shared-verdict rules gain the constraint that a verdict judging relayed prose matches without regard to case, so sentence capitalisation cannot fail a correct relay.

## Impact

- `harness/l1_checks.py`: one comparison in `verdict_check_report`.
- `tests/unit/test_harness_helpers.py`: coverage for a differently-capitalised relay passing and a genuinely incomplete relay still failing.
- Expected effect on the dev runner: `check_report` moves from 0–1/5 to at least 3/5 on both models tested, which clears the threshold. Two needles stay unmatched by design — "Trailing `---` has no blank line before it" and "Only 2 unique references" are paraphrases, and tolerating those would mean matching on tokens rather than phrases, which detects less.
