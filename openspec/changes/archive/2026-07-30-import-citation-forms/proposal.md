## Why

Import is the one skill whose input already contains *rendered* citations — a source PDF reads "Smith et al. [1] propose a drift detector". The natural conversion is `Smith et al. [@Smith26Deep] propose …`, which renders correctly and therefore looks fine, but freezes the author name as hand-copied prose: it stops tracking the reference entry the moment that entry is corrected. The writing guidance now forbids exactly this pattern, and `@key` exists to express it, but import has no rule telling it which form to produce and no link to the guidance that does.

## What Changes

- Import converts each in-text citation to the form matching its role in the sentence: where the source names the authors as the actor, the name is removed from the prose and the citation becomes `@key`; where the citation is evidence attached to a claim, it becomes `[@key]`.
- Import never leaves an author name typed in the prose immediately before a bracketed citation.
- The rule applies to numeric sources ("Smith et al. [1] propose"), author-date sources ("Smith et al. (2020) propose", "(Smith et al., 2020)"), and footnote-style sources alike, since all three carry the name in the running text.
- The existing L1 import eval gains an assertion for the forbidden hand-typed-name pattern, using the pasted source it already exercises.

No breaking change: both citation forms were already legal output, and existing imported proposals keep rendering as they do.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-import`: the import requirement set gains a citation-form conversion requirement — which syntax each source citation becomes, and the prohibition on hand-typed author names beside bracketed citations.

## Impact

- `skills/proposal-import/SKILL.md`: the mapping bullet that currently says "convert in-text citations to `[@key]`/`@key`" gains the selection rule, following the file's existing pattern of pointing at `../proposal-write/references/guidelines.md` with an inline fallback for when that skill is not installed.
- `harness/skill_evals.py`: `import_l1()` gains the pattern assertion. The pasted `MESSY_SOURCE` already contains "the survey by Rivera et al. 2023", so no new fixture is needed.
- No L0 coverage is possible for the rule itself: it is a prose judgement with no script behind it, and a corpus-wide regex for "capitalised word before `[@`" false-positives on ordinary sentences ending in a proper noun. The mechanical guard therefore lives in the L1 scorer, which knows its own source text.
