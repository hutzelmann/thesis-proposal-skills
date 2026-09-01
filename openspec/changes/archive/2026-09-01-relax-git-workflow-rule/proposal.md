# Relax the git workflow rule to its invariants

## Why

`AGENTS.md` states "work directly on `main`, no branches or worktrees", and `CONTRIBUTING.md` makes that bind humans the same way. The rule is prose-only — no test, hook, CI job, or permission entry enforces it — and the repository's own machinery already contradicts it: CI triggers on `pull_request`, a `PULL_REQUEST_TEMPLATE.md` ships, a `pr-1` branch exists from the one outside contribution, and the `merge=ours` driver registered by `poe setup` for the 22 generated copies is dead weight on a strictly linear `main`. Every agent session in this repository now runs in a git worktree the host creates, so the first thing an agent reads is a rule its own environment breaks.

The rule also points away from the constraint that matters. `skill-packaging`'s rolling-release requirement makes the default branch the release channel: what lands on `main` is immediately live for `npx skills add`. Working on `main` therefore keeps every half-finished OpenSpec change one `git push` away from students, with nothing but the "do not push" clause in the same bullet standing between them. Branch isolation is the mechanism that removes that coupling, not a mechanism to ban.

## What Changes

- The `AGENTS.md` **Git** bullet drops its two mechanism clauses ("work directly on `main`", "no branches or worktrees") and states the invariant they were standing in for instead: `main` is the release channel, so what lands there is live and unfinished work stays off it — where that work lives (branch, worktree, local commit sequence) is deliberately unspecified.
- The bullet keeps its two load-bearing clauses verbatim in substance: commit per completed OpenSpec change, and no push or skills.sh publish without explicit request.
- The bullet gains the one hazard that allowing merges introduces and no rule currently records: generated copies carry `merge=ours`, so a merge touching `shared/` can leave them stale; re-run `python3 scripts/sync_shared.py` afterwards, with CI's `--check` as the backstop.
- No mechanical enforcement is added. The replaced rule had none, and the invariant that replaces it is already enforced where it counts — the L0 gate on every PR and push, and the publish pipeline's explicit-request rule.

Out of scope: `CONTRIBUTING.md` needs no edit — it delegates the rules to `AGENTS.md` rather than restating them. The `skill-packaging` rolling-release requirement is quoted, not changed; the tagged-release trigger it names (outside users exist) is a separate decision.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none — `skip_specs: true`. The change edits contributor instructions only; no skill, script, or harness behavior changes, and the `skill-packaging` release requirement this rule serves is unchanged.)

## Impact

- `AGENTS.md` — the **Git** bullet under Hard rules, rewritten.
- Nothing else: no script, test, fixture, spec, or generated copy changes; `uv run poe test` and `openspec validate --all --strict` are unaffected except as the standing gate.
