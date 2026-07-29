# Add README Demo Storyboard

## Why

The README explains the skills in text only; a visitor cannot see what a session with the tool feels like before installing anything. A short visual storyboard at the top of the README gives a graspable impression of the workflow in seconds — the strongest possible answer to "what does this actually do?". (An animated GIF was built first and rejected in maintainer QC: at this content density, stills carry the same information with far less setup.)

## What Changes

- Add a three-shot screenshot storyboard at the top of the README (directly after the intro line, before the skills table): ① vague idea → Socratic `proposal-ideate` exchange, ② `proposal-lit-search` surfacing real papers, ③ `proposal-check` verdict + published PDF.
- Content is a curated replay harvested from a real agent session on the synthetic `w01-ideate-seed` data-drift-detection topic (English only, generic agent-chat look, no specific agent TUI imitated).
- Add a reproducible content source under `docs/demo/`: curated transcript plus a small stdlib-only script that prints each shot into any terminal; regenerating an image is a plain terminal screenshot — no recording tooling.
- Screenshots are small PNGs committed normally (no Git LFS needed).
- Add a contributor note documenting how to regenerate the storyboard.

## Capabilities

### New Capabilities

- `demo-recording`: Reproducible pipeline that renders the README demo images from committed, synthetic-content sources (transcript + replay script + VHS tape).

### Modified Capabilities

- `user-onboarding`: README gains a requirement to show a visual, time-condensed impression of the workflow before the textual explanation.

## Impact

- `README.md`: three-shot storyboard near the top; contributor section gains a one-line regen note.
- New directory `docs/demo/` with `replay.py`, `transcript.jsonl`, `harvest.log`, and the generated `shot1..3.png`.
- No new dependencies, no LFS, no GitHub Pages, no third-party services.
- No skill behavior, shared guidance, or test harness changes.
