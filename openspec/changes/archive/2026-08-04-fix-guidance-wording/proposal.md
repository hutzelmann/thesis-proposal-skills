## Why

The guidance uses a word that does not exist in English. "Neglectable" appears twice in `guidelines.md` as the term for requirements a thesis deliberately leaves out, and the nearest real word — "negligible" — means something else, namely *too small to matter* rather than *deliberately excluded*.

This is not a cosmetic problem, because guidance vocabulary propagates. Agents copy the term straight into student proposals: it has already reached six fixtures, and it reached them the same way it would reach a real student's document. It was surfaced by a model rather than by review — a Sonnet session asked to fix what the check reported rewrote "neglectable" to "out of scope" unprompted, judging it non-standard English. A model that silently edits the wording is the good case; the bad case is a supervisor reading it.

The term is a calque of German `vernachlässigbar`, which is idiomatic in German for scope a thesis deliberately omits. The German guidance and the German fixtures are therefore correct as they stand; only the English borrowing broke.

Auditing the rest of the user-facing surface for the same class of defect found two more German-interference errors and three consistency problems worth fixing in the same pass.

## What Changes

- **`neglectable` → `out of scope`** in `guidelines.md` (Prototype Implementation and Theoretical Analysis methodology content), in the `proposal-import` TODO template, and in the six fixtures that inherited it.
- **`decide for one` → `decide on one`** — a direct calque of *sich entscheiden für*.
- **`Especially the introduction and the contribution section must …` → `The introduction and the contribution section in particular must …`** — German fronting of *besonders*; English places the qualifier after the subject.
- **`un-forbid` → `allow again`** across guidance, skills, and the `guidance-model` spec prose. The coinage is precise but is invented vocabulary in a document students read.
- **`Handover` → `hand-in`** in the guidelines checklist heading, so it matches the term every other file already uses, with the cross-reference in `proposal-write` updated in step.
- **`the channel you hand the proposal in through` → `the channel you submit it through`** — grammatical but clumsy.

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

<!-- None: `skip_specs: true`. No requirement changes — every rule keeps exactly
     the meaning it already had, and only the words carrying it change. The
     `guidance-model` spec's prose mentions `un-forbid`, so that one term is
     renamed in the main spec text as part of the sweep; the requirement itself,
     its scenarios, and its behavior are untouched. -->

## Impact

- **Guidance**: `shared/guidelines/guidelines.md`, materialized into four skill copies by `scripts/sync_shared.py`.
- **Skills**: `proposal-import` (TODO template), `proposal-customize` and `proposal-write` (the `un-forbid` term).
- **Spec prose**: `openspec/specs/guidance-model/spec.md` — the `un-forbid` term only.
- **Fixtures**: six proposals carrying `neglectable`, seven occurrences — `f06`, `f07`, `f16`, `f19` (twice), `f20`, `w03`. No oracle changes: the term appears in body prose, never in a pinned error.
- **Not touched**: `docs/demo/harvest.log`. It is an audit trail of real sessions and records both the original wording and the model's correction of it; editing it would falsify the record.
