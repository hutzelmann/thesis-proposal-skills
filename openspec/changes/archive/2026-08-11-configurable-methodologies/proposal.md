## Why

The methodology set is a closed set of four. That closure is load-bearing — it is what forces a student to decide what kind of evidence the thesis produces instead of hedging — but the *contents* of the set are not a property of thesis writing. They are a property of a department. An external contributor's proposal added four branches their lab needs; a different lab would add case study and design science; a third would find two of the current four irrelevant.

There is no version of this set that is finished. Every future request to add a branch is a request we cannot evaluate, because the answer depends on a supervisor's field rather than on anything visible from here — and each one taken permanently costs a subsection contract, a fixture, and an oracle.

The closure should stay and the contents should move. A workspace declares the set its supervisor accepts; the shipped set remains the default for a workspace that declares nothing.

## What Changes

- `methodologies` becomes overridable in the workspace `guidelines.md`, as a table keyed by branch id, mirroring the structure key path exactly like every other override.
- A workspace branch id matching a shipped branch replaces it; a new id adds a branch; `enabled = false` drops a shipped branch, which is how a supervisor says a methodology is unacceptable for their students.
- A workspace branch SHALL declare `guidance` per subsection. The shipped branches carry their content contract as prose in `guidelines.md`; a workspace branch has no prose file to carry it, so without this the write skill would invent what belongs under a heading it has never seen. A branch that cannot say what goes inside it is rejected as a configuration error.
- The shipped set stays at four. Which branches the defaults *should* contain is a separate question that needs literature rather than preference, and it is deliberately not answered here.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the methodology set becomes workspace-configurable, and the single-methodology rule is restated as closure-per-workspace.
- `skill-check`: the check validates a workspace methodology declaration and applies the merged set.
- `skill-customize`: the skill writes methodology branches and refuses one without per-subsection guidance.
- `skill-write`: the write skill takes the methodology set from the merged data rather than the shipped defaults.

## Impact

- `shared/structure.json` — no value changes; the shipped branches keep their shape, which is what a workspace branch mirrors.
- `skills/proposal-check/scripts/check.py` and its three vendored copies — merge, validation, and the methodology rule.
- `skills/proposal-customize/SKILL.md`, `skills/proposal-write/SKILL.md`, `shared/guidelines/guidelines.md` and its copies.
- A new `w04-methodology-branch` fixture: a workspace declaring its own branch, plus a proposal using it.
- Existing workspaces are unaffected — a file that declares no methodologies gets the shipped four.
