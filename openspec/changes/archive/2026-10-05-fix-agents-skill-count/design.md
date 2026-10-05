# Design

## Context

Docs-only correction; see proposal.md for the stale sentences. The shipped set is the eleven directories under `skills/`, of which `proposal-supervise` is the one written for supervisors; `tests/unit/test_skill_header_pattern.py` already asserts eleven.

## Goals / Non-Goals

**Goals:** every sentence in AGENTS.md and in harness docstrings that states how many skills ship says eleven (ten student-side plus `proposal-supervise`).

**Non-Goals:** rewording anything else in AGENTS.md; touching `openspec/changes/archive/`, whose counts are true of the set at the time each change was written; adding an offline guard over prose skill counts.

## Decisions

**Fix by hand, no new guard.** A count guard over AGENTS.md would have to parse free prose for skill counts the way `test_substance_tests.py` does for substance tests. The count changes only when a skill is added, which already forces a reviewed edit of `shared/blocks/workflow.md`, the header-pattern roster and the packaging spec; the cost of a parser that has to tell "eleven skills" from "eleven references" outweighs a drift this rare. Alternative considered: extending `test_skill_header_pattern.py` to grep AGENTS.md for number words — rejected for the same false-positive reason, and because AGENTS.md is agent instructions, not a shipped artifact.

**"Ten student-side" counts `proposal-troubleshoot` and `proposal-reverse` with the student side**, matching how the original sentence counted every non-supervise skill as student-side.

## Risks / Trade-offs

- [The next added skill leaves AGENTS.md stale again] → the "Skill header pattern" section already tells whoever adds a skill to edit the workflow block; the count sentences sit in the same file.
