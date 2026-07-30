## Why

The guidance forbids personal data in a proposal — matriculation number, address, email, study program, supervisor names — yet the file format *mandates* an `author` key and the publish template prints it on the title page. A student who does not fill it in gets the placeholder rendered instead: a real run of the skills produced a proposal PDF with **TODO: add author** in the title block. The name adds nothing a reviewer needs, it is the one piece of personal data the format actively asks for, and proposal files are routinely handed to agents and shared as PDFs.

## What Changes

- The canonical metadata contract becomes `title`, `subtitle`, `lang`, `references`. `author` is no longer part of it, is no longer seeded, and is no longer described by any skill.
- The rendered title block therefore carries title and subtitle only: nothing sets `author`, so nothing prints. Publish itself is unchanged — its conditional author block stays, and it renders whatever `author` holds.
- A workspace `guidelines.md` may reinstate a named title page in prose, for a program that demands one. The user sets `author` deliberately and publish prints it; no new flag, no new override key.
- A file that still declares `author:` (legacy, imported, or deliberate override) produces a check **warning**, never an error, worded so the override case is not treated as a defect: ``author: found — proposals are anonymous by default; remove it unless your program requires a named cover page``. Since publish renders any `author` value verbatim, this warning is the only thing standing between a stale `[TODO: add author]` and a title page — hence a warning on the key itself, not on its value.
- The default guidance forbids the author's own name, alongside supervisor names and the other personal data. Identification of the student happens outside the document — hand-in email, upload form, filename — and the guidance says so in one sentence.
- Import strips the cover-page author name along with the personal data it already removes.
- No person-name detection in prose: the check skill gains exactly one rule, on the metadata key. Name-shaped regexes over body text fire on every cited researcher and are not implementable at acceptable precision.

Not breaking for existing files: `author:` stays legal YAML and stays renderable under an override; it merely stops being required, seeded, or default-rendered.

## Capabilities

### New Capabilities

None. This change removes a key from an existing contract and adjusts the skills that read it.

### Modified Capabilities

- `proposal-file-format`: the metadata-block requirement drops `author` from the required keys and states that a proposal carries no author identity; the format-drift requirement polices the shortened key list.
- `skill-check`: the warning-class checks gain the `author:` metadata-key warning.
- `skill-import`: the personal-data stripping requirement names the author/student name explicitly.
- `guidance-model`: the forbidden-content requirement gains the author's own name.

## Impact

- `shared/structure.json` / `shared/guidelines/guidelines.md`: forbidden-content list gains the author's own name plus the one-sentence note on where identification belongs; `scripts/sync_shared.py` re-materializes the generated copies in write, review, customize, and ideate.
- `skills/proposal-ideate/SKILL.md`: stops seeding `author` and the `[TODO: add author]` placeholder — the source of the reported defect.
- Format prose in every skill that states the metadata contract loses the `author` key; the existing L0 drift test enforces the shortened list.
- `skills/proposal-check/scripts/check.py`: one warning rule.
- `skills/proposal-import/SKILL.md`: author name added to the strip list.
- `skills/proposal-publish/`: no change. `proposal.typ` keeps `$if(author)$` so the override path works; the defect disappears because nothing sets the key.
- Fixtures: `author:` removed from every fixture except `f15-format-broken`, kept as the deliberate tripwire for the new warning; its `expected.json` gains the warning, the other oracles are re-verified against `check.py`.
- Two L0 tests, no pandoc, no model calls: the oracle-driven warning test, and a guard asserting no skill prose, template, or fixture except the tripwire declares a top-level `author:`.
- **Sequencing**: implementation waits for `render-author-in-text-citations` (10/28 tasks) to be archived — its delta modifies the same `skill-check` requirement, so this change's `skill-check` delta is re-baselined against the archived result before any code is touched. The two changes use "author" in opposite senses (cited researcher vs. proposal writer) and must not be implemented concurrently.
