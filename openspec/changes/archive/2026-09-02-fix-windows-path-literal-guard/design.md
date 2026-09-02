## Context

See proposal.md — Why. The constraint that shapes the rule: `tests/unit/test_repo_conventions.py` already owns one cross-platform rule (`test_relative_paths_render_as_posix`), scanning `PATH_FILES` — every Python file under the script directories and `tests/` — with an AST walk and no dependency beyond `ast`. The new rule joins that section and reuses that file list, so the "guard the guard" test (`test_path_scan_covers_the_tree`) covers it too.

## Goals / Non-Goals

**Goals:**

- Make the failing class observable on a Linux clone, where the work happens.
- Keep the rule narrow enough that its first run reports exactly the one line that is red in CI.

**Non-Goals:**

- Teaching the rule about Windows-shaped literals (`Path("C:\\…")`). None exist, and a rule with no subject is documentation.
- Changing `summary()` or any other producer. `config_dir` stays a native-separator string; see proposal.md.
- Retiring the `l0-windows` job. A source rule catches literal-shaped mistakes; line endings, encodings and `tmp_path` semantics still need a real Windows host.

## Decisions

**Flag the literal, not the comparison.** The bug is visible in two places: `Path("/tmp/cfg")` and `== "/tmp/cfg"`. Matching the comparison means deciding whether an arbitrary string literal is path-shaped, which is a heuristic with a false-positive rate. Matching the constructor is exact: an absolute POSIX literal handed to `Path(...)` either becomes text that will not match a POSIX expectation on Windows, or names a directory that does not exist there. Both are defects, and the constructor is the source, which is where `root-cause` says to fix.

**Match `Path` by name, with a single string constant starting with `/`.** `PurePosixPath("/…")` is deliberate and stays legal — the author who writes it has chosen POSIX semantics explicitly. An f-string or a joined value is not a literal and is not matched; those carry their platform from whatever produced them.

**No inline exemption mechanism.** If a genuinely POSIX-only path literal is ever needed, the reviewed step is a named constant in the rule with a comment saying which change introduced it — the same shape `[tool.ruff.lint.per-file-ignores]` uses in `pyproject.toml`. A `# noqa`-style escape would let the next writer opt out silently, which is how this class got here.

**The rule lands with the fix, in the same change.** The rule fails on `main` today. Landing it alone would leave the tree red; landing the fix alone would leave the class unguarded until the next Windows CI round-trip. Order inside the change: rule first, watch it report the line, then fix (see tasks.md).

## Risks / Trade-offs

- **A future legitimate POSIX-absolute literal is blocked** → the exemption route is a named constant in the rule, reviewed like any other test edit; the rule's failure message names it.
- **The rule reads as broader than its subject (one line today)** → its docstring names the run it comes from, as the sibling rule names the `sync_shared.py` breakage, so a later reader can judge whether it still earns its place.
- **False sense of coverage** → non-goals say it plainly, and `harness/README.md` is not touched: the Windows job remains the backstop for everything a source rule cannot see.
