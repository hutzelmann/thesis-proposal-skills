## 1. README demo

- [x] 1.1 Draft the three beats from `docs/demo/transcript.jsonl` before deleting it: beat 1 = anecdote → Socratic question → the gap nobody closes; beat 2 = literature verified, noise rejected; beat 3 = draft written → check clean → PDF built
- [x] 1.2 Replace the three image lines in `README.md` with three `<details>` blocks, each summary naming its beat, each body a short blockquote attributing answers to the skill that produced them
- [x] 1.3 Verify the markdown: blank line after every `</summary>`, blockquotes render, no image references left in `README.md`

## 2. Retire the render pipeline

- [x] 2.1 Delete `docs/demo/shot1.png`, `docs/demo/shot2.png`, `docs/demo/shot3.png`, `docs/demo/replay.py`, `docs/demo/transcript.jsonl`
- [x] 2.2 Rewrite `docs/demo/README.md` as the audit trail: `harvest.log` is trimmed raw output of a real session on a synthetic topic; the README demo quotes trace back to it; refresh both together when the workflow story changes
- [x] 2.3 Grep the repository for references to the deleted files (`shot1`, `replay.py`, `transcript.jsonl`, `docs/demo/`) and fix any that remain

## 3. Verify

- [x] 3.1 `uv run pytest` green, `uv run ruff check .` clean, `python3 scripts/sync_shared.py --check` clean
- [x] 3.2 `openspec validate --all --strict` passes
- [x] 3.3 Confirm no tracked file still references a deleted demo artifact (`git grep`)
