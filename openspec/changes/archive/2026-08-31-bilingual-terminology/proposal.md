# Bilingual terminology: proposal / Exposé

## Why

The document has one name per language — "proposal" in English, "Exposé" in German — but nothing states or enforces that, so a future edit can introduce "Exposé" into English student-facing text or an anglicism into German, and every bilingual surface (the supervise blurb, the verdict tiers, the subtitles) can drift independently. The convention is real today by accident; unchecked, it is documentation, not a gate.

## What Changes

- The guidance model gains a terminology requirement: user-facing English text calls the document a proposal; user-facing German text calls it an Exposé; neither term crosses into the other language's text. URLs, repository names, and skill names (`thesis-proposal-skills`, `proposal-*`) are exempt — they are identifiers, not prose.
- An L0 test guards the shipped bilingual surfaces: the supervise getting-started blurb (English section carries "proposal" and no "Exposé"; German section carries "Exposé" and no prose "proposal" outside identifiers/URLs), the German verdict-tier phrases, and the German subtitle strings.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `guidance-model`: new requirement fixing the per-language document term for user-facing text and its identifier exemption.
- `testing-harness`: the L0 suite covers the terminology guard over the shipped bilingual snippets.

## Impact

- `openspec/specs/guidance-model/spec.md`, `openspec/specs/testing-harness/spec.md` — new requirements via deltas.
- New `tests/unit/test_bilingual_terminology.py` — guards `skills/proposal-supervise/references/getting-started.md` sections, the German tier phrases in `skills/proposal-supervise/SKILL.md`, and the subtitle strings in `skills/proposal-ideate/SKILL.md`.
- No shipped prose changes expected — current usage already conforms; the change adds the statement and the gate.
