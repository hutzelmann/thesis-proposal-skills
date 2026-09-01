# Reword idea-stage plainness instruction

## Why

An idea-stage feedback run produced the opening sentence "aus dem vorliegenden Text lässt sich ein solches Exposé noch nicht durch Überarbeitung gewinnen, weil diese drei Bausteine noch nicht angelegt sind" — a near-literal German rendering of the skill's own instruction ("say plainly that a proposal cannot be built from the material as it stands") plus a count-reference to the instruction's three-item enumeration of the proposal standard. The instruction is phrased as a ready-made sentence, so the model translates it instead of composing one; the student reads rubric language, not a supervisor's voice.

## What Changes

- Reword the idea-stage clause in `skills/proposal-supervise/SKILL.md` (Curate the feedback, item 1) so it states the communicative goal — the student must come away knowing revision alone will not produce a proposal — and requires the statement be composed in the feedback's own words, tied to what this specific submission is missing, never a rendering of the instruction sentence or a reference to the standard's items by count.
- The deliberately fixed phrases are untouched: the tier words (**Ideenphase — noch kein Exposé** etc.) stay verbatim-required, the closing note stays verbatim.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-supervise`: the "Verdict expressed as proposal state" requirement gains a composition constraint on the idea-stage statement — own words, grounded in the specific submission, no instruction-echo, no enumeration-by-count.

## Impact

- `skills/proposal-supervise/SKILL.md` — one clause in the feedback-curation list.
- No script, harness, or test changes: no L1 check, pinned sentence, or mandate pin covers this wording (verified; `SUPERVISE_TIER_PATTERN` matches tier words only).
