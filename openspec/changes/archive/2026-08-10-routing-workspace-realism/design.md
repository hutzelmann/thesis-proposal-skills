## Context

See proposal.md — Why. The rig and its dataset are `harness/routing.py` and `harness/routing_cases.toml`; the run being corrected is `docs/skill-routing.md` at 55/60.

`stage_workspace()` currently copies the union of `WORKSPACE_FIXTURES` into every measurement. That was the cheap way to let any utterance name any file, and it silently converted "the user's proposal" into an ambiguous phrase for every case that does not name one.

## Goals / Non-Goals

**Goals:**

- Each case measured in the workspace its own sentence implies.
- Failures reported as rates, so noise is visible as noise.
- A report that cannot be misread as a like-for-like comparison across a rig change.

**Non-Goals:**

- Editing any skill description. Whether the remaining failures are description defects is the question this change makes answerable; answering it is the next change if the answer is yes.
- Editing case utterances. The dataset stays fixed so that the only variable is the staging.

## Decisions

**Derive the staging from the utterance, not from a per-case field.** Alternative considered: a `files = [...]` key on each case. Rejected — it duplicates what the sentence already says, and the two would drift, with the drift invisible until a case mysteriously stopped routing. The existing L0 test already asserts that every filename appearing in an utterance is one the suite can stage; deriving from the same source makes that test load-bearing instead of advisory.

**One default proposal when the utterance names nothing.** Alternatives: an empty workspace (rejected — "I need something I can email tomorrow" against an empty directory invites a clarifying question of a different kind, trading one artifact for another), or the case's own expected skill deciding (rejected — that leaks the answer into the setup). A single English proposal is what a student who has been working here for a week has.

**Uniform epochs, defaulting to three.** The collision-only epoch policy was justified when contested cases were assumed to be the doubtful ones; the evidence since is that any case can be flaky. Cost is 120 measurements per sweep against 60, roughly ten minutes — acceptable for the only instrument that reads this surface. `COLLISION_EPOCHS` disappears rather than being retained as a special case nobody can justify.

**A conditions marker instead of a comparison.** `previous_score()` stays, but the report distinguishes "supersedes" from "measured under different conditions". The alternative — deleting the previous score — throws away the history a reader wants; the risk is not that the old number is present but that it is presented as comparable.

## Risks / Trade-offs

- **The default proposal biases cases that name no file** toward whatever that proposal is about → it is a plain, well-formed English proposal, and the German cases all name their file explicitly.
- **Sweeps take twice as long** → the run is on-demand and parallel; ten minutes is not a loop-breaking cost.
- **Fewer files staged may expose cases that only passed because a file happened to be present** → that is the point; a case passing for the wrong reason is worse than a case failing honestly.
- **The new number may be worse than 55/60** → then the descriptions have a real problem the old staging was masking, which is a finding rather than a setback.

## Migration Plan

Internal to the harness. `docs/skill-routing.md` is regenerated; the previous figure survives in git history and in the archived changes that produced it.
