# Tasks: README Demo Storyboard

## 1. Harvest session content

- [x] 1.1 Set up a scratch workspace with the skills installed (clean agent config, no personal plugins/instructions)
- [x] 1.2 Run a real agent session through the five beats (ideate → lit-search → write → check → publish) from a naturally phrased synthetic student anecdote, and capture the full output
- [x] 1.3 Trim the raw capture to `docs/demo/harvest.log` (remove noise, keep everything the demo will quote; verify no personal data)

## 2. Build the replay pipeline

- [x] 2.1 Curate `docs/demo/transcript.jsonl` from the harvest: role-tagged events (`user|agent|tool|note`) with scene boundaries
- [x] 2.2 Write `docs/demo/replay.py` (stdlib only): renders transcript with generic agent-chat styling (❯ user prompts, plain agent text, dim tool lines)
- [x] 2.3 Add a stills mode to `replay.py` (render a chosen shot instantly for screenshotting; recording tooling dropped entirely per maintainer)
- [x] 2.4 Tune theme/dimensions until the three shots read well at README width and total a few hundred KB
- [x] 2.5 Remove the dropped animation artifacts (demo.gif, demo.cast, index.html, player/) from the working tree

## 3. Integrate into repository

- [x] 3.1 Embed the three shots in `README.md` directly after the intro line, with meaningful alt text
- [x] 3.2 Update the contributor note (`docs/demo/README.md`): render a shot with `replay.py --shot N`, screenshot the terminal, when to refresh
- [x] 3.3 Verify the audit trail: every paper reference and proposal excerpt in `transcript.jsonl` appears in `harvest.log`
- [x] 3.4 Maintainer QC of the rendered shots, then commit and push; check rendering on GitHub and confirm `uv run pytest` still passes
