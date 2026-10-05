# Design

## Context

See proposal.md, Why. The dev runner starts two kinds of isolated children: the model under test (`run_claude`, environment from `model_env`, which returns `routing.isolated_env`) and the dev judge (`claude_cli.call` and `preflight`, environment from `claude_cli.child_env`). Before this change, only the first followed the requirement "Isolated child environment" as written.

## Goals / Non-Goals

- Goal: the spec describes what the code does, with no behaviour change.
- Non-goal: unifying the two allowlists. That is the open follow-up recorded in the proposal. It touches the judge's tested environment and deserves its own change.

## Decisions

- **Carve the judge out instead of unifying now.** The judge's allowlist is already specified, in "Subscription text roles (dev runner)", and covered by its own L0 tests. Narrowing the newer requirement is a wording change. Unifying would change the judge's runtime environment, and that should go through review on its own.

## Risks / Trade-offs

- [Risk] The two allowlists keep drifting. → Mitigation: the follow-up is recorded in this proposal and in the archived isolate-child-environment design.
