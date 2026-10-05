# Proposal

## Why

An independent review of `2026-10-05-isolate-child-environment` found two problems.

First, the requirement it added, "Isolated child environment", covers "every dev-runner run in isolated mode". Read strictly, that includes the dev judge's child, which also runs in the isolated configuration. But the judge's environment is built by `claude_cli.child_env`, a separate allowlist governed by "Subscription text roles (dev runner)". That allowlist admits every `XDG_*` variable, `XDG_SESSION_*` included, where this requirement admits only the XDG base directories. So the current code violates the requirement as written.

Second, the harness README still said an isolated dev run keeps the operator's effort and session settings.

The archived change folder is write-protected, so its own wording can only be corrected here.

## What Changes

- **Scope the requirement.** "Isolated child environment" now covers the routing rig's children and the dev runner's model-under-test child. It states that the dev judge's child is governed by "Subscription text roles (dev runner)". No code changes: this is what the code already does.
- **Harness README, "Billing, exit statuses and the smoke".** An ambient run keeps the operator's effort and session settings; an isolated run gets `routing.isolated_env` instead. The smoke's "billing strip" becomes the isolated allowlist, since the smoke always runs isolated.
- **Corrections recorded here for the archived change, which cannot be edited:**
  - Its design.md says in "Where it lives…" and in "Tests" that an ambient run passes `env=None`. Since the reconciliation, an ambient run passes the operator's environment minus the billing variables; the reconciliation paragraph in the same file is the current statement.
  - Its last risk says the spec delta is ADDED only. It also MODIFIES "Dev-runner cost and helper-agent telemetry".
  - Its follow-up note says `child_env` admits fewer machine variables than `ADMITTED_ENV`. It also admits more: every `XDG_*` variable, which `isolated_env` drops on purpose. The follow-up stays open: build the judge's environment from `isolated_env` too.
  - Its proposal names the touched requirement "Isolated measurement environment". The requirements actually touched are "Isolated child environment" (ADDED) and "Dev-runner cost and helper-agent telemetry" (MODIFIED). Its Impact list omits AGENTS.md, where one sentence of "Metered model calls" changed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: "Isolated child environment" is scoped to the routing rig's children and the dev runner's model-under-test child. The dev judge's child stays with "Subscription text roles (dev runner)".

## Impact

- `openspec/specs/testing-harness/spec.md`: one requirement reworded, plus one scenario.
- `harness/README.md`: two sentences.
- No code or test changes.
