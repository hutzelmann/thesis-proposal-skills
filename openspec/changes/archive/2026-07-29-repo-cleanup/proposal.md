# Proposal: repo-cleanup

## Why

Migration leftovers clutter the repo: the historical plan (rewrite.md) and fixture blueprint duplicate what openspec/specs/ and the archives now own; untracked reminders (ai-feedback.md, expose.pdf, review.pdf) served their purpose during fixture design; the S1 spike example task is superseded by skill_evals.

## What Changes

- fixtures-blueprint.md moves to tests/fixtures/README.md (the living corpus reference the testing-harness spec's "fixture blueprint" points to).
- rewrite.md deleted (git history + legacy-latex-template tag + archived changes preserve everything).
- Untracked leftovers deleted from disk; .git/info/exclude reduced to confidential/.
- harness/rq_quality_task.py deleted; README mention removed.
- AGENTS.md history note simplified; .gitignore LaTeX remnants dropped.
- skip_specs: true — housekeeping, no behavior change.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

Smaller root, single home per document; no code paths affected.
