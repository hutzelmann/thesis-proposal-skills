## Context

See proposal.md — Why. The constraint that shapes every decision below: the whole fixture corpus must report exactly what it reported before. A false-positive removal that changes any oracle is not a false-positive removal; it is a rule change wearing one's clothes.

## Goals / Non-Goals

**Goals.** Remove five false positives without weakening the finding each belongs to. Give the write skill a rule that survives a wrong finding. Leave the report byte-identical on all 30 fixtures.

**Non-Goals.** No markdown parser. No new dependency — the script stays stdlib-only, and the masking below is regex over lines, not a CommonMark implementation. No re-litigation of which findings are errors and which are warnings.

## Decisions

**Masking over stripping.** `mask_code` replaces code spans and fenced blocks with spaces of the same width rather than deleting them, so line numbers and the prefix the typed-author-name check reads stay the file's own. Deleting would have shifted every subsequent finding's location by the length of the removed span, trading one wrong report for another. Fence lines collapse to empty strings: nothing inside a fence is scanned, so their width never matters.

**The bare `@Word` stays an error.** Alternatives considered: recognise a list of known annotations (unbounded, and wrong for every language but Java); require a citation key to match the documented key shape before reporting it undefined (this would swallow a mistyped key, which is exactly the defect the rule exists for). Unmarked in prose, `@Override` and a mistyped `@Dyer14Minning` are the same string to any rule that does not read English. What changes is that there is now a remedy the student can apply to the markup — and the write skill is told, in its own must-not-fix list, that the remedy is never the prose.

**Roman-numeral labels by shape, not by word list.** `\b[A-Z][a-z]+ I\b` covers `Type I`, `Phase I`, `Study I` without enumerating them. It costs the pronoun in "Study I conducted", which is a warning missed in a class that already tolerates both directions, and buys not firing on the vocabulary this project's own Controlled Experiment contract requires. A word list would have needed extending on every new false positive.

**Setext headings are diagnosed, not parsed.** Recognising them in `headings()` alone would find the sections but not their bodies — `section_text` slices on `#`, so the timeline, research-question and subsection rules would all read empty sections and fall silent, which is a second wrong report rather than a fix. Making the whole heading model setext-aware is a rewrite of the document model for a shape that arrives only from a broken export. The rule fires only when the body has no `#` heading at all, so it cannot misread a well-formed document, and it says which titles it saw so the student knows the sections were found.

**A YAML key is never a setext heading.** The closing `---` of a metadata block underlines the line above it. The rule skips a `key:`-shaped line for that reason, and is additionally gated on the document having no `#` headings anywhere.

**`heading-style-setext` is covered by an L0 unit test, not a fixture.** Thirty identifiers already sit in `COVERED_BY_UNIT_TESTS`. This one would need a permanent corpus document with no `#` headings, built on every tier by the export matrix, to assert a rule that fires only on documents nobody should keep. The identifier-reachability gate covers it either way.

## Risks / Trade-offs

- **A citation on a fenced line is now invisible** → fence lines carry no prose; a citation there would not have rendered either.
- **"Study I conducted" loses its pronoun warning** → warning class, both directions tolerated; the alternative was a false positive on required vocabulary.
- **Message text changed on four findings** → the `expected.json` oracles match on prefixes, and the added text is appended; the full L0 run confirms no oracle moved.
- **The write skill's new rule could be read as licence to dismiss inconvenient findings** → the rule requires the finding be *demonstrably* wrong, names the markup fix as the first resort, forbids deletion outright, and requires the skill to say which finding it left standing.

## Migration Plan

None. No user-visible format changes, no workspace file changes, no new configuration. A workspace that never hit one of these false positives sees a line number added to four warning messages.
