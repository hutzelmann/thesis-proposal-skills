## 1. Simplify the import skill

- [x] 1.1 Drop the non-negotiables the check enforces — closed metadata block, references as a list, methodology from the closed set, research questions ordered — and point at the check instead
- [x] 1.2 Remove the duplicated research-question rule, which the same list states twice
- [x] 1.3 Keep the three the check cannot see: reference-key shape, one person per author entry, TODO markers as bare lines in the metadata block
- [x] 1.4 Keep the worked example; showing the target shape is what a source document cannot supply

## 2. Correct the documentation

- [x] 2.1 Scope the harness known-limitation to the Inspect path explicitly, and state that a dev-runner failure is a real signal
- [x] 2.2 Record that `check_report` now passes 5/5 on both models tested, and why it was previously red

## 3. Verification

- [x] 3.1 `uv run pytest` green
- [x] 3.2 `uv run ruff check .` clean
- [x] 3.3 `python3 scripts/sync_shared.py --check` clean
- [x] 3.4 `openspec validate --all --strict` passes
- [x] 3.5 Re-ran after the trim: **4/4 pass**. The removed rules were not load-bearing — the check catches them, which is why restating them was duplication rather than reinforcement
