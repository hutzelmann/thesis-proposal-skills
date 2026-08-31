# Design

## Context

See proposal.md. Current usage already conforms; the change adds the spec statement and an L0 gate. The guarded surfaces are hand-maintained prose: the blurb snippet (`skills/proposal-supervise/references/getting-started.md`), the German tier phrase line in `skills/proposal-supervise/SKILL.md`, and the subtitle strings in `skills/proposal-ideate/SKILL.md`.

## Goals / Non-Goals

**Goals**: one statement of the rule in the guidance-model spec; one test file that fails with file and term named.

**Non-Goals**: no repo-wide prose scanner — agent-facing SKILL.md bodies legitimately mix languages when quoting both tier renderings; the gate covers the shipped bilingual user-facing surfaces only. No lint rule: this is content, not code shape.

## Decisions

- **Narrow extraction, no markdown parser.** The test splits the blurb file on its `## English` / `## Deutsch` headings and checks the quoted blockquote lines — same narrow-extraction stance the repo applies to YAML. Identifier exemption by stripping URLs (`https://\S+`), backtick spans, and the hyphenated names `thesis-proposal-skills` / `proposal-<word>` before matching.
- **Case-insensitive match for the crossed terms** ("exposé" in English, standalone "proposal" in German after stripping); German check also requires the accented form — "Expose" without the accent is a misspelling the guard flags.
- **Tier phrases and subtitles pinned where they live**: the test asserts the German tier line in supervise SKILL.md contains "Exposé" and the ideate subtitle strings match "Exposé zur Bachelorarbeit/Masterarbeit" — anchored greps, not new pinned-copy files, since `test_skill_header_pattern.py` already demonstrates the pattern of asserting against live files.

## Risks / Trade-offs

- [Blurb headings renamed later → sections not found] → the test fails loudly on a missing section rather than passing on empty input (explicit assert that both sections were found and non-empty).
