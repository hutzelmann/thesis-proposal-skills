# Design

## Context

Two request tables describe the same seed-to-draft job: the dev runner's `SCENARIOS["write_from_seed"]` (subscription, one headless turn, `poe smoke` / `poe dev`) and the Inspect `@task write_from_seed` (metered model-support matrix, projected into `skills/proposal-write/evals/evals.json`). They already differ in wording — the Inspect prompt says "The file is ws/data-drift-detection.md" because Inspect stages the workspace under `ws/` — and nothing asserts they are equal.

## Goals / Non-Goals

**Goals:** the dev runner's seed scenario cannot end in a clarifying question for want of being told no one will answer.

**Non-Goals:** touching the Inspect task or its projection; changing what the skill itself does when information is missing (the skill is right to ask a real student).

## Decisions

**Copy the sibling sentence verbatim** — "I cannot answer any questions — decide and tell me what you did." — rather than a seed-specific variant ("assume a Master's thesis"). Naming the missing answer would hand the run a fact the fixture does not contain and hide whether the skill marks unknowns as TODO, which is what the seed scenario checks. The verbatim sentence keeps the three dev-runner write scenarios uniform, so a difference between their outcomes is not a difference in their instructions.

**Leave the Inspect `write_from_seed` prompt alone.** The matrix's shipped verdicts are built from the newest log per cell and read as movement against earlier runs; a prompt change would silently re-baseline every `write_from_seed` cell. If the matrix ever needs the sentence, that is its own change, made with the history break stated.

## Risks / Trade-offs

- [The two requests drift further apart] → they were never equal, and the design states why this difference is deliberate; the dev runner is the instrument that needs the cue because it is single-turn and unattended.
