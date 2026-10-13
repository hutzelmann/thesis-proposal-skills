# Tasks

## 1. Tests first

- [x] 1.1 Write `tests/unit/test_lit_live.py` covering:
  - the D4 verdict table, cell by cell;
  - exit codes for all-ok, busy-only, and any needs-change outcome;
  - `--sources` subset and unknown-name refusal;
  - the OpenAlex key gate, both without a key (`skipped (no key)`, the stub is never called) and with a key (the stub is called, the key value is never printed);
  - no message text from a raised error in the output;
  - `PROBES` covering every name in `search.SEARCH_SOURCES` and `snowball.GRAPH_SOURCES`;
  - the `lit-live` poe task running `harness/lit_live.py` with no `envfile`.

  Verify the file fails, red: `uv run pytest tests/unit/test_lit_live.py` errors on the missing module.

## 2. Implementation

- [x] 2.1 Write `harness/lit_live.py`, following D1–D5:
  - the guarded `sys.path` entry for the lit-search scripts directory;
  - the static `PROBES` table with `QUERY`, `LIMIT` and `SEED_DOI`;
  - the `Verdict` dataclass and the pure classifiers;
  - the key gate through `common.get_key`;
  - `main(argv: list[str] | None = None) -> int`.

  Verify, green: `uv run pytest tests/unit/test_lit_live.py` passes, and `uv run ruff check harness/lit_live.py tests/unit/test_lit_live.py` is clean, at a complexity of 12 or below.
- [x] 2.2 Repoint the `lit-live` task in `pyproject.toml` to `python3 harness/lit_live.py`, and rewrite its comment: one request per source, OpenAlex only with a key, exit 1 means change the code, local only. Verify the poe-task test in 1.1 passes.

## 3. Documentation

- [x] 3.1 Update the `poe lit-live` line in `AGENTS.md` to the new scope and exit meaning. Verify with `git grep -n "poe lit-live"`: no remaining text describes it as a single DBLP query.
- [x] 3.2 Remove the "Live check beyond DBLP" (`widen-lit-live`) entry from `docs/backlog.md`. Verify with `git grep -n widen-lit-live -- docs`, which finds nothing.

## 4. Gates

- [x] 4.1 Run the gates after the final edit and verify that each exits 0: `uv run poe test`, `uv run poe specs`, `uv run poe cov` (78% floor), and `python3 scripts/sync_shared.py --check`.
- [x] 4.2 Run `uv run poe lit-live` once, by hand. It is read-only, makes about six requests, and calls no model. Record its lines and exit code in the hand-over report.
