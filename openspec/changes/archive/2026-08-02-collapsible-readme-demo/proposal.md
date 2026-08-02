## Why

The README opens with three stacked 1000px screenshots (~500 KB) that push every word of explanation below the fold, and the demo they show is unreachable on skills.sh — that site renders each `SKILL.md`, never the repository README, and shows no images anywhere. The screenshots therefore cost the GitHub reader a lot of vertical space and buy no reach, while the story they tell (anecdote → sharpened research question → verified literature → draft → check → PDF) is worth keeping in a form every markdown renderer can show.

## What Changes

- Replace the three screenshots in `README.md` with three collapsed `<details>` blocks, one per workflow beat, each holding a short speaker-labelled blockquote naming the skill that spoke (`proposal-ideate`, `proposal-lit-search`, `proposal-write`, `proposal-check`, `proposal-publish`). Collapsed, the three summary lines read as a table of contents of the workflow.
- Cover `proposal-write` in the demo, which the current three screenshots skip entirely.
- Delete `docs/demo/shot1.png`, `shot2.png`, `shot3.png`, `replay.py`, and `transcript.jsonl`. With no derived images, there is nothing to render and nothing to keep in sync — the README prose becomes the demo artifact itself.
- Keep `docs/demo/harvest.log` and rewrite `docs/demo/README.md` as the audit trail: every quote and paper in the README traces back to real harvested session output on a synthetic topic.
- **BREAKING** (docs only): the documented `python3 docs/demo/replay.py --shot N` regeneration workflow disappears.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `user-onboarding`: the "Visual workflow demo in README" requirement becomes a condensed-session demo requirement — plain markdown, collapsible, near the top, no images — and absorbs the surviving authenticity rule (content curated from a real session on a synthetic topic, no personal data, no fabricated references).
- `demo-recording`: removed. Its purpose is a reproducible image-render pipeline that ceases to exist; its authenticity requirement moves to `user-onboarding`, and its image-size, reproducibility, and agent-neutrality requirements no longer describe anything the repository does.

## Impact

- `README.md` — demo section rewritten.
- `docs/demo/` — three PNGs, `replay.py`, `transcript.jsonl` deleted; `README.md` rewritten; `harvest.log` untouched.
- `openspec/specs/user-onboarding/spec.md` — one requirement rewritten, one added.
- `openspec/specs/demo-recording/` — capability removed.
- No skill, script, test, or eval touches the demo files; `uv run pytest`, `ruff`, and `sync_shared.py --check` are unaffected.
- skills.sh presentation is explicitly out of scope: the README never renders there.
