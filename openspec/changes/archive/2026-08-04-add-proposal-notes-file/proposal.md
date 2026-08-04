# Add Proposal Notes File

## Why

All working knowledge of a proposal today lives in two bad places: TODO markers crammed into the buildable document, and chat history that dies with the session. Decisions, rejected alternatives, excluded literature, and "what to do next" have no durable home, so every session restarts from an impoverished state and the proposal fills with non-blocking clutter. A paired knowledge file gives that state a home, keeps the buildable proposal lean, and survives session loss.

## What Changes

- **New file kind**: every proposal `<slug>.md` may have a companion `<slug>.notes.md` — a working-knowledge file with five light canonical sections: Decisions, Open Points, Next Focus, Excluded Literature, Log. The sections are named in the file-format spec for predictable agent access but carry no mechanical checks (formalization boundary: content stays prose).
- **TODO split rule**: the proposal file keeps only submission-blocking content gaps as `[TODO: …]` markers (the readiness signal check.py counts); everything else — decisions with rationale, rejected alternatives, open non-blocking points, next steps — lives in the notes file. Completed TODOs move to the notes Log as done entries instead of being deleted, preserving the work record.
- **Write adoption**: proposal-write reads the notes file before drafting (decisions and Next Focus steer the draft), records new decisions there, and moves resolved proposal TODOs into the Log.
- **Lit-search adoption**: proposal-lit-search records rejected candidates in Excluded Literature (id, one-line reason) so later searches do not re-propose them, and keeps accepted-entry bookkeeping unchanged.
- **Import adoption**: proposal-import seeds the notes file at import time with unmapped source content (e.g. dropped work-plan phase detail), the gap list, and an initial Next Focus — content it today reports only in chat.
- **Ignored everywhere else**: check, review, publish, customize do not read or write notes files; the notes file is never built, never submitted, and never carries the anonymity-relevant identity of the author.
- **Harness**: draft selection treats `*.notes.md` as non-proposal markdown (suffix rule beside the existing `guidelines.md` name rule); fixtures may ship notes files without oracles.

## Capabilities

### New Capabilities

None — the notes file is an extension of the proposal file format, not a standalone capability.

### Modified Capabilities

- `proposal-file-format`: gains the companion-file requirement — naming, the five canonical sections, the blocking-TODO split, and the not-built/not-submitted status.
- `skill-write`: gains read-notes-before-drafting, record-decisions, and move-done-TODOs-to-Log requirements.
- `skill-lit-search`: gains the Excluded Literature recording requirement and the do-not-re-propose rule.
- `skill-import`: gains the seed-notes-at-import requirement (unmapped content, gap list, initial Next Focus).
- `testing-harness`: draft selection excludes `*.notes.md` alongside `guidelines.md`.

## Impact

- `skills/proposal-write/SKILL.md`, `skills/proposal-lit-search/SKILL.md`, `skills/proposal-import/SKILL.md` — prose additions; mandates expected to stay byte-identical (pinned copies untouched).
- `harness/l1_checks.py` — `select_draft` suffix exclusion; matching unit test.
- `shared/guidelines/guidelines.md` — no change: the notes file is workflow machinery, not proposal guidance; the formalization boundary keeps it out of the checkable skeleton.
- `tests/` — unit coverage for the selection rule; existing fixture oracles unaffected (no fixture gains a notes file in this change).
- Downstream: `redesign-ideate-dialogue` (follow-up change) makes ideate the notes file's primary producer; this change deliberately lands the format and the consumers first so that change can build on it.
