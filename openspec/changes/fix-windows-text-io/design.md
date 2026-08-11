## Context

See proposal.md — Why. Two design-level questions have to be settled before any line is
edited: what exactly the new gate scans for, and how the identify-release tests can agree
with git's object naming on a host whose defaults differ from the developer's.

Constraints that shape both answers:

- The Windows job is the only faithful oracle. `LC_ALL=C` on Linux reproduces the encoding
  class (it turns the locale default into ASCII) but is a strict superset: it also breaks
  subprocess stdout decoding in 47 tests that Windows handles fine, so it cannot be a gate.
  `os.linesep` is compiled in, so the CRLF class cannot be reproduced on Linux at all.
- `AGENTS.md`: every convention is paired with the linter rule or L0 test that enforces it,
  and `[tool.ruff.lint]` carries no per-file-ignores.

## Goals / Non-Goals

**Goals:**

- The two failing test modules produce identical bytes on every host.
- A future test that writes non-ASCII without an encoding fails on the author's machine,
  not three weeks later in a Windows job.

**Non-Goals:**

- Changing how the shipped skill scripts do text I/O. They already fix an encoding
  everywhere, and the collector already hashes bytes.
- Pinning newline translation. `write_text` still emits CRLF on Windows; every reader in
  this repository opens in text mode and universal newlines makes that transparent. Only
  the code that hashes bytes needs byte control, and that code is named explicitly below.

## Decisions

**A source-level AST test, not a ruff rule.** `PLW1514` is the obvious candidate and does
not work: it is preview-only, and it resolves a receiver only when it is a literal
`Path(...)`. Against this repository it reports zero violations while an AST walk finds 98.
The gate therefore joins the existing scans in `test_repo_conventions.py`, which already
walk `PATH_FILES` for the `relative_to`/`as_posix` rule and can reuse that file list.
Alternative considered and rejected: a regex over source lines — the calls wrap across
lines, so a line-based scan misses roughly a third of them.

**The gate covers `tests/` and the script directories, not the whole tree.** `PATH_FILES`
is already that list. Fixtures and generated copies are excluded by construction, which is
correct: a fixture is data, not a caller.

**Binary pipe rather than a hand-rolled blob hash in the identify-release tests.** The
module docstring states why the fixture history is a real git repository: the thing under
test is agreement with git's own object naming, and computing the hash in Python would
assert that the code matches itself. That argument survives the fix, so `git hash-object
--stdin` stays and only the pipe changes from text to bytes. The alternative — importing
`git_blob_hash` from the shipped collector — would make the test agree with the
implementation instead of with git.

**`core.autocrlf=false` on the fixture repo, in addition to writing bytes.** Writing bytes
alone is sufficient today (`autocrlf=true` normalizes CRLF to LF on add and leaves LF
alone), but the pairing is what makes the fixture's stored bytes independent of the host's
git configuration, which is the property the test needs and the one a reader has to be able
to check locally.

## Risks / Trade-offs

- **The fix cannot be verified where it is written** → the L0 suite passing on Linux proves
  only that nothing regressed. Confirmation is the `l0-windows` job on the next push, and
  the change is not archived before that job is green.
- **A 98-site mechanical sweep buries the two real fixes in the diff** → tasks order the
  sweep after the gate, so review reads the gate and the two fixes first and the sweep as
  what the gate forced.
- **The gate will flag a future call that deliberately reads with the locale encoding** →
  no such call exists, and `encoding=locale.getencoding()` states that intent explicitly
  while still satisfying the gate.
