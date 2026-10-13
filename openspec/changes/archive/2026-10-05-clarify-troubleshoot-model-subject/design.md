# Design

## Context

See proposal.md, Why. Three facts shape the approach:

- **The runtime path already behaves as the delta states.** Commit 68ded53 reworded rung 1 in `skills/proposal-troubleshoot/SKILL.md` to look up "the model that produced the failure", pinned in `tests/unit/data/pinned_sentences/proposal-troubleshoot--model-subject.txt`. It also narrowed the date stamp in the rung-1 comparison sentence, pinned in `proposal-troubleshoot--model-rule.txt`, and in `MODEL_DATE_RE` in `scripts/collect.py`. The archived change folder could not record that follow-up, because edits under `openspec/changes/archive/` are denied. This change brings the spec level with the code.
- **"Running model" is used outside the requirement this change modifies.** The "Non-defect causes named as such" scenario "Known-weak model on a task it fails" speaks of "the running model as failing". In the cross-session case that phrase already means the model that ran the failing task, never the troubleshooting agent.
- **The archived design D8 still binds.** Scenarios use the synthetic `lab/example-*` family only. The requirement prose describes host spellings in words.

## Goals / Non-Goals

**Goals:**

- The spec names the lookup subject as the model that produced the failure, and a scenario covers a model the user names for an earlier session.
- The spec's date stamp has the shape the code strips: year, month and day, compact or dashed.
- The snapshot assumption that the narrowing leaves in place is written down, and an L0 test pins where it stops.

**Non-Goals:**

- Editing `SKILL.md`, `collect.py`, the pins, the shipped verdict data, or `harness/skill_evals.py`. All of them already match (D2).
- The report's self-reported model identity. "Measured facts distinguished from self-reported ones" still asks for the agent's own identifier. For optional model evidence about a failure from an earlier session on another model, the report therefore carries the troubleshooting agent's model as its self-reported identity. The failing model appears only if the agent writes it into its account of the exchange. Closing that gap changes a different requirement and the report template, so it is left to a follow-up change rather than widened into this one.
- Strengthening `verdict_troubleshoot_model_rung` so that it tells a matched lookup from a fall-through. This stays deferred, as in the archived design's Open Questions.

## Decisions

### D1: Keep the term "running model" and define it

The modified requirement defines the running model as the model that produced the failure: the agent's own when the failure happened in the current session, otherwise the one the user names for that run. Every existing use of the term then reads correctly, including the one in "Non-defect causes named as such", without a second MODIFIED block.

*Rejected: replace the term throughout with "the model that produced the failure".* That puts a second requirement into the delta for a wording change in one scenario, and the long form makes the scenarios harder to read.

*Rejected: "the failing model".* It collides with the `fail` verdict. "The failing model's verdict is `pass`" would be a sentence the spec has to allow.

### D2: The spec follows the shipped code; nothing under `skills/` changes

The delta restates what 68ded53 shipped, so the implementation tasks are verification plus one test. Re-editing the skill to match the spec's new wording would churn two pins for no change in behavior. The prose in `SKILL.md` and the spec now say the same thing in different registers: the skill speaks to the agent ("your own", "the one the user names"), and the spec speaks about it.

The user's spelling is accepted as the exact identifier because it is the only identifier available for a run the agent did not see. It goes through the same normalisation as a host's spelling. A user who writes an alias such as `haiku` therefore gets "unevaluated", as a host alias would.

### D3: A date stamp carries year, month and day

`MODEL_DATE_RE` strips `[-@]20YYMMDD` and `-20YY-MM-DD` at the end of the name and nothing shorter. A four-digit suffix such as `-2411` reads as year and month, but some vendors number versions that way. Stripping it would let two versions share a spelling, and one would inherit the other's verdict, which the requirement forbids. The test `test_wrappings_are_stripped_no_wider_than_a_host_spells_them` already keeps `large-2411`. The new scenario states the same rule in the synthetic family.

The `@` form (Vertex) is not named in the requirement. "Written compact" covers it, since the separator is not part of the stamp, and the code's comment lists it.

### D4: Accepted assumption — a dated snapshot takes the verdict of an undated key with the same version

Ignoring the date means a host spelling `example-4-5-20251001` takes the verdict recorded under `lab/example-4.5`. An undated key and a dated spelling of it resolve to each other in either direction. This is the defect the archived change fixed, and the assumption is what makes the fix work. The roster keys registry IDs, which carry no year-month-day date, while Claude Code and Vertex append one.

The assumption is wrong when a vendor ships two snapshots of one version that behave differently and the user ran the one the matrix did not measure. That cannot be detected from the shipped data, because the data does not record which snapshot an undated alias pointed at during the matrix run. It is accepted for three reasons:

- **Its reach is bounded.** It only applies where the data holds exactly one entry for the version.
- **Two snapshots in the data resolve to none.** If the roster ever keys two dated snapshots of one version, both normalise to the same spelling. The collision rule then chooses neither, and `test_every_shipped_key_resolves_to_itself_without_collisions` fails in CI before a user sees it.
- **A short snapshot token stays.** Some roster keys carry a token shorter than a full date, such as a trailing `-0813`. D3 keeps that token, so a host spelling without it resolves to no key and reads as unevaluated. That is the safe direction: missing a verdict, never borrowing one.

*Rejected: treat the date as part of the version and require an exact dated key.* That reinstates the defect: the Claude Code spelling of haiku would never match the undated roster key.

*Rejected: record the measured snapshot in the shipped data and compare dates.* It changes the generated data and `harness/report.py`, and it needs the snapshot each matrix run actually hit, which the report pipeline does not carry today. It is out of proportion to a risk no observed case has realised.

### D5: One L0 test pins the assumption's boundaries

The existing tests pin the forward direction: a dated host spelling resolves to an undated key. The new test in `tests/unit/test_troubleshoot_collect.py` pins the rest of D4 on a synthetic support file:

- an undated host spelling resolves to a single dated key of the same version;
- two dated keys of one version resolve to none;
- a key with a short snapshot token resolves from its own spelling but not from the spelling without the token.

It uses `lab/example-*` keys, so it is independent of the roster and needs no guard entry.

## Risks / Trade-offs

- [A reader still takes "running model" to mean the agent's own] → The definition sits in the requirement that consults the verdicts, and the new scenario shows the cross-session case with two distinct models.
- [The snapshot assumption reports a verdict measured on another snapshot] → Bounded as D4 sets out. The only failure that reports a wrong verdict needs an unrecorded behavioral difference between snapshots of one version.
- [The delta and `SKILL.md` drift apart later] → The pins guard the `SKILL.md` side. Any reword of either needs a change that shows both in one diff. The spec scenarios are synthetic, so a roster bump never touches them.

## Migration Plan

Nothing ships to users: the skill files do not change. Archiving syncs the delta into `openspec/specs/skill-troubleshoot/spec.md`. Rollback means reverting the commit.
