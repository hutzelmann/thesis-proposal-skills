## 1. The two failures

- [x] 1.1 `tests/unit/test_title_tells.py`: fix `encoding="utf-8"` on the `structure.json`
      read, the fixture read in `with_title`, and the `write_text` that produces the victim
      proposal.
- [x] 1.2 `tests/unit/test_identify_release.py`: make `blob()` feed `git hash-object
      --stdin` encoded bytes on a binary pipe, decoding the result, with a comment naming
      why text mode is wrong (`os.linesep` translation on write).
- [x] 1.3 `tests/unit/test_identify_release.py`: build the `history` fixture from
      `write_bytes` and set `core.autocrlf=false` on the fixture repo, with a comment
      naming the runner default that made this necessary.
- [x] 1.4 Run `uv run poe test-fast` — still green on Linux, no behavior moved.

## 2. The gate

- [x] 2.1 Add a `text I/O encoding` section to `tests/unit/test_repo_conventions.py`: an
      AST helper returning the line numbers of `read_text` / `write_text` / text-mode
      `open` calls with no `encoding` keyword, parametrized over `PATH_FILES` like the
      existing path rule, with a failure message that names the file, the lines and the
      fix.
- [x] 2.2 Exclude binary `open` modes (a mode argument containing `b`) so the rule does not
      demand an encoding where one is illegal.
- [x] 2.3 Docstring states the cost that bought the rule: the Windows job found this class
      only after it had already shipped, and ruff cannot express it.
- [x] 2.4 Run the new test alone and confirm it fails, listing the 98 known sites — a gate
      that passes before the sweep is not measuring anything.

## 3. The sweep

- [x] 3.1 Add `encoding="utf-8"` to every call the gate reports, file by file, starting
      with `tests/unit/test_check.py` (70 sites).
- [x] 3.2 Clear the remaining files the gate names.
- [x] 3.3 `uv run poe test` green, including ruff (line length 100 — reflow any call the
      keyword pushes over).
- [x] 3.4 `uv run poe cov` still above the floor.

## 4. Verification

- [x] 4.1 `openspec validate --all --strict`.
- [ ] 4.2 Commit, and confirm the `l0-windows` job is green before archiving the change.
