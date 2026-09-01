# Add workspace proposal-location override (`[paths] proposals`)

## Why

Every skill hard-codes where proposals live: flat in the workspace root, sidecars and generated outputs beside them. A workspace that wants its proposals in a subdirectory — a supervisor collecting many submissions, a student keeping the root clean — has no supported way to say so, and the guidance file that would say so is itself found by a rule (`guidelines.md` beside the proposal) that only works because proposals sit in the root. The customization surface exists precisely so "our workspace needs X" is a file in a folder; file layout is the one dimension it does not yet cover.

## What Changes

- New `[paths]` node in `shared/structure.json` with a single leaf, `proposals` (default `"."`), overridable from the workspace `guidelines.md` TOML block under the existing one-rule key-path naming. Defaults reproduce current behavior exactly; an unset key changes nothing.
- The workspace root is anchored at the directory containing the governing `guidelines.md` — the working directory skills already pin. `paths.proposals` is resolved relative to it.
- `check.py` resolves the override file through a fixed two-step chain (explicit flag, then beside the proposal, then the working directory) — same shape as the credential chain, still no ancestor search. Behavior with proposals in the root is byte-identical to today.
- The proposal's whole family follows it into the configured directory: `<slug>.md`, `<slug>.notes.md`, `<slug>.harvest.md`, `img/`, `<slug>-review.md`, `<slug>-feedback.md`, and publish outputs (which already land beside the proposal — no publish change). `guidelines.md`, `api-keys.env`, and `bug-report/` stay at the workspace root.
- Skills honor only the configured location — no fallback search. `check.py` reports a proposal found outside the configured directory as an error instead of skills silently ignoring it.
- `[paths] proposals` values are validated (string, relative, inside the workspace — no `..`, no absolute path, no `~`); an invalid value is an error finding that falls back to the default, and unresolvable `[paths]` keys stay `override-key-unknown` errors, per the existing rule.
- `proposal-customize` documents and manages the namespace; SKILL.md location wording across the affected skills is updated, including `proposal-reverse`'s currently unstated proposal location and `proposal-import`'s pinned output-location sentence (pinned copy edited in the same change).

Deliberately out of scope (decided during design review): no `paths.derived` (review/feedback always sit beside the proposal), no `paths.archive` (no skill consumes an archive location today). Either can be added later as its own change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the workspace override file's overridable set gains the proposal-location path; the override model gains the workspace-root anchor, the family-follows-proposal location rule, and the no-fallback discovery rule.
- `skill-check`: guidelines resolution becomes the fixed two-step chain; new value validation for `[paths] proposals`; new misplacement error when a governing configuration sets a proposal directory and the checked proposal lives elsewhere.
- `skill-customize`: the dialog covers the `[paths]` namespace and validates values before writing them.
- `skill-import`: the imported proposal's destination changes from "the working directory" to the workspace's configured proposal location (default unchanged).

## Impact

- `shared/structure.json` (+ the 7 generated per-skill copies via `scripts/sync_shared.py`).
- `skills/proposal-check/scripts/check.py` (+ 4 generated copies in import/write/reverse/supervise): `load_overrides` chain, `OVERRIDABLE` addition, `[paths]` value validation, misplacement finding.
- SKILL.md prose in check, import, write, reverse, supervise, review, ideate, customize, troubleshoot (target-resolution and output-location wording); `tests/unit/data/pinned_sentences/proposal-import--output-location.txt`.
- Docs: README, `docs/getting-started.md`, customize skill page.
- Tests: new workspace fixture demonstrating the override (w-series), L0 tests for the chain, validation, and misplacement finding; existing location-pinning tests updated. L0 suite only — no metered eval runs.
