# Design

## Context

See proposal.md — Why. The location of the imported file is carried by prose alone; the header-pattern rules (AGENTS.md "Skill header pattern") constrain where new sentences may go in `SKILL.md`, and the mandate is pinned in `tests/unit/data/skill_mandates/proposal-import.txt`. The eval harness stages the workspace at `ws/` and its prompt framing already instructs "work there", so no eval distinguishes a SKILL.md that states the location from one that does not.

## Goals / Non-Goals

**Goals**

- One unambiguous statement of the output directory in the import skill's operative prose, early enough that an agent normalizing on behalf of `proposal-supervise` (which follows import's instructions verbatim) inherits it.
- Remove the "use that location" reading of the `${CLAUDE_SKILL_DIR}` fallback: the fallback resolves a script *path*, it never relocates the work.
- Pin the new sentence so a later reword is a reviewed diff.

**Non-Goals**

- No script changes — `check.py` and `validate_refs.py` take the file path as an argument and write nothing.
- No harness change — the `ws/` framing describes the sandbox layout and stays; making an eval catch a missing location sentence would mean deleting the framing, which the sandbox needs. The L0 pin is the regression guard instead.
- No edits to `proposal-write` / `proposal-reverse` (same silence, no observed failure, no pull away from the workspace) and none to `proposal-supervise` (already states the location in SKILL.md and spec).

## Decisions

- **Location sentence lives in the mandate.** The mandate is the first operative paragraph and the one supervise-delegated runs are guaranteed to read; a later section could be skipped by a skimming agent. Cost: the pinned mandate copy must change in the same commit — which is the header-pattern rule working as designed, not an obstacle. Alternative considered: a separate paragraph after the mandate — rejected because "nothing is inserted between a mandate and the paragraph beneath it".
- **Delta is ADDED, not MODIFIED.** No existing requirement in `skill-import/spec.md` speaks about location; this is a new concern, and MODIFIED-with-partial-content loses detail at archive time.
- **Fallback reword keeps the fallback.** Hosts that don't substitute `${CLAUDE_SKILL_DIR}` still need to find the scripts; the reword only adds that the command runs from the workspace with that path. The same fallback phrasing exists in six other skills — out of scope here, tracked as follow-up, because only import both writes files and reads sources that live elsewhere.

## Risks / Trade-offs

- [Agents may still write beside an out-of-workspace source despite the sentence] → the spec scenario names exactly this case, so a future harness task can stage a source outside `ws/` and score the location; not built now to keep the change minimal.
- [Pinned-sentence test wiring differs from mandate pins] → follow the existing `pinned_sentences/` convention (`test_skill_header_pattern.py` / sibling test that consumes that directory) rather than inventing a new mechanism.
