## Why

The guidance forbids typing an author name next to a bracketed citation (`Smith et al. [@Smith26Deep]`), because the name is then a copy that stops tracking the reference entry. Nothing detects it. The pattern renders correctly, so neither the author nor a supervisor sees a problem — it only surfaces later, as a name that disagrees with its own bibliography entry.

The rule currently reaches only the skills that write prose, and only as instruction. Import now states it explicitly, but a proposal can acquire the pattern from any source: a hand edit, a paste, an older draft, or an agent that ignored the guidance.

A general detector for this is not viable — "capitalised word immediately before a citation" false-positives on ordinary sentences ending in a proper noun ("Deployments in Germany [@Okafor24Carbon]"). The check skill can do better than a general detector, because it already parses the reference entries: it can compare the typed word against the surnames of *that specific* reference and flag only a genuine match.

## What Changes

- The check skill warns when the text immediately before a citation is an author surname of the reference being cited, in either citation form:
  - `Smith et al. [@Smith26Deep]` — the name is a frozen copy; `@Smith26Deep` is the form that keeps it live.
  - `Smith et al. @Smith26Deep` — worse, this renders the name twice ("Smith et al. Smith et al. [1]").
- Detection is anchored to the cited reference's own authors, so a sentence ending in an unrelated proper noun is not flagged.
- The warning names the key, the line, and the replacement form.

Warning class, never an error: the guidance calls the pattern wrong, but a proposal carrying it still builds and still reads correctly.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-check`: the warning-class check set gains the typed-author-name detection, specified as anchored to the cited reference's authors rather than to a general capitalisation pattern.
- `skill-write`: the citation-form rule widens from "grammatical subject or agent" to also cover the possessor case ("the detector of @key"). The corpus sweep surfaced this: `f19-drift-alert-validity` wrote "the detector of Tan et al. [@Tan25Flexibl]", which the narrow rule would have forced into a bracketed citation with the name deleted, losing meaning. The author-in-text form renders that sentence unchanged.

## Impact

- `skills/proposal-check/scripts/check.py`: per-reference author surnames added to the narrow metadata extraction (alongside the existing author/editor presence flags), plus the detection over both citation forms.
- `skills/proposal-check/SKILL.md`: unchanged — it relays the script's two buckets verbatim and does not enumerate individual checks.
- `tests/unit/test_check.py`: cases for both citation forms, for the unrelated-proper-noun non-match, and for the correct author-in-text form staying silent.
- Fixture oracles re-verified; the one fixture carrying the pattern (`f19-drift-alert-validity`) is fixed rather than pinned.
- `shared/guidelines/guidelines.md` and `skills/proposal-write/SKILL.md` carry the widened wording; `scripts/sync_shared.py` re-materializes the generated copies.
