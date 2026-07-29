# Design: README Demo Storyboard

## Context

The "tool" being demonstrated is a conversation between a student and an AI agent — there is no classic CLI to record. A raw live agent session is minutes long, nondeterministic, and full of spinners/permission prompts; the demo must be graspable in seconds and reproducible. An animated GIF pipeline was fully built first; maintainer QC judged that at this content density stills carry the same information, so the deliverable is a three-shot screenshot storyboard. All user-facing decisions below were settled interactively with the maintainer (see proposal.md).

## Goals / Non-Goals

**Goals:**
- Three polished, regenerable screenshots; every source needed to re-render them lives in `docs/demo/`.
- Content authenticity: everything shown was actually produced by the skills in a real session.

**Non-Goals:**
- Animated demos (GIF/asciinema/player pages) — built, evaluated, and dropped in QC.
- Per-skill screenshots, German demo, GitHub Pages, Git LFS.
- Imitating any specific agent product's TUI.

## Decisions

### 1. Curated replay, not live recording
A real agent session was run once (headless `claude -p`, clean config without the maintainer's personal plugins/instructions), starting from a fictional but naturally phrased student anecdote (a churn model that silently degraded), in the same drift-monitoring area as the `w01-ideate-seed` fixture; its output is harvested and condensed into a transcript. Rendering replays that transcript. The publish turn was re-run in a fresh session after the first attempt surfaced — and fixed — a real bug in `proposal-publish`'s `rq-filter.lua` (citations inside research questions broke the typst build); the fix was ported back into the repo skill. Alternative — screenshotting a live session — rejected: nondeterministic, painful to redo after changes.

### 2. Plain terminal screenshots, no recording tooling
`replay.py --shot N` (stdlib-only Python) prints one storyboard shot into any terminal with role styling: `❯` user prompt, plain agent text, dim tool-activity lines. Regenerating an image = run the command, screenshot the terminal. The *content* is fully deterministic from the committed transcript; exact pixels depend on the contributor's terminal, which is acceptable for stills. Alternatives — a VHS `Screenshot` pipeline (built first, dropped: recording machinery is overkill for static images) and HTML mockups (not authentic) — rejected.

### 3. Structure: transcript owns content, script owns presentation
`transcript.jsonl` (one event per line: role `user|agent|tool`, text, `clear` scene boundaries) is the only file to edit when the story changes; `replay.py` maps roles to styling and selects the scenes per shot. Storyboard shots: ① student anecdote + Socratic ideate reply, ② lit-search request + verified-paper results, ③ check verdict + PDF build.

### 4. Provenance file for the harvested session
The trimmed raw session log is committed as `docs/demo/harvest.log` so the spec's audit requirement (every shown paper/excerpt traces to real output) is checkable in-repo. Alternative — keeping the raw log out of the repo — rejected: the no-fabricated-content claim would rest on trust.

### 5. Plain git storage
Three PNGs total ~a few hundred KB — committed as ordinary blobs. The earlier LFS plan applied to a multi-MB GIF and is moot for stills.

## Risks / Trade-offs

- [Stills convey less "liveness" than animation] → accepted explicitly by maintainer after seeing the rendered GIF.
- [Demo drifts from actual skill behavior after future changes] → transcript is easy to edit and re-screenshot; contributor note says to refresh when the workflow story changes.
- [Contributor terminals differ, so regenerated shots vary in look] → acceptable: content is what the spec pins down, not pixels.

## Migration Plan

Purely additive; rollback = remove the README embed and `docs/demo/`.

## Open Questions

- Exact theme, font size, and shot cropping — tuned visually at render time; does not affect specs or tasks.
