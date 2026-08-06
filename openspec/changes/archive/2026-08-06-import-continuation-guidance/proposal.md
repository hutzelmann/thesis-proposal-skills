## Why

Import is the only entry path that ends without naming what comes next. It always leaves `[TODO: …]` markers behind by design, and the student who arrived through it never saw the workflow explained — they landed here with a finished PDF, not with a question about where to start. Every other skill closes forward: ideate names the write skill, write names ideation and review, check names review, review names write. Import's `## Wrap-up` reports what happened and stops.

The failure this produces is silent. A student who does not know the markers are a work queue asks for the gap to be filled in the same conversation, and the agent — already holding the file — edits it in place without loading `proposal-write`: no `guidelines.md` authority, no surgical-edit rule, no `check.py` self-verification, no notes-file Log entry for the resolved marker. The output looks the same and is held to none of the rules.

## What Changes

- `skills/proposal-import/SKILL.md` closes its `## Wrap-up` by naming the next step, branching on what the gap actually is: prose gaps go to the write skill, a reference shortfall to the literature-search skill, missing research questions or method to the ideation skill.
- The three-way branch is the point, not decoration: pointing every gap at the write skill would send a student with no research questions into a skill whose stated rule is that it never manufactures them.
- The sentence is pinned in `tests/unit/data/pinned_sentences/`, so rewording it shows up as a paired diff under review — the gate lands with the behavior, not after it.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-import`: gains a requirement that the import summary names the continuation path per gap class. Today the spec's nine requirements cover what import produces and what it strips, and say nothing about what the student is told to do next.

## Impact

- `skills/proposal-import/SKILL.md` — `## Wrap-up` section, prose only.
- `tests/unit/data/pinned_sentences/` — one new pin file; `test_pinned_sentences.py` picks it up by glob, no test code changes.
- No script, schema, or fixture changes. `verdict_import` in `harness/l1_checks.py` judges the produced file and cannot see a chat message, so the L1 import task is unaffected and stays as it is.
