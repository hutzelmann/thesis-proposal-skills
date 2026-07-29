# README demo

The three screenshots in the top-level README are a **curated replay of a real agent session** — condensed, never invented. `harvest.log` is the trimmed raw output of that session; every paper and excerpt shown traces back to it.

## Files

| File | Role |
|---|---|
| `transcript.jsonl` | Single source of truth: condensed session, one role-tagged event per line (`user`/`agent`/`tool`; `clear` marks scene boundaries) |
| `replay.py` | Prints one storyboard shot into the terminal (stdlib only) |
| `shot1..3.png` | The rendered screenshots embedded in the README |
| `harvest.log` | Audit trail: trimmed raw session output |

## Regenerate after editing `transcript.jsonl`

```sh
python3 docs/demo/replay.py --shot 1   # then screenshot the terminal
```

Same for `--shot 2` and `--shot 3`. Any terminal and screenshot method works (the current PNGs came from a dark-themed terminal at ~80 columns). Keep the images small — a couple hundred KB total.

Refresh the demo whenever the workflow story changes (skills renamed, beats added or removed). Keep content traceable to a real session: if you show new agent output, run a real session and extend `harvest.log` — never invent papers or results.
