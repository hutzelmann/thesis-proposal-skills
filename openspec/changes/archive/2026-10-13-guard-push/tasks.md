# Tasks

## 1. Guard

- [x] 1.1 Write `.githooks/pre-push` (mode 755): read the refs on stdin, pass when there is nothing to push, refuse when `/dev/tty` cannot be opened, otherwise ask `[y/N]` at the terminal and pass only on yes. The terminal check runs in a subshell, because a failed redirection on the special built-in `:` would end the hook silently. Verify: in an agent shell, piping one ref into the hook prints the refusal and exits 1.
- [x] 1.2 Add the six deny rules to `.claude/settings.json`: `git push`, `rtk git push`, `/usr/bin/git push`, each bare and with ` *`.
- [x] 1.3 Name both layers in AGENTS.md's Git rule and forbid routing around them.

## 2. Tests and gate

- [x] 2.1 `tests/unit/test_push_guard.py`: refused without a terminal, nothing to push passes, a pseudo-terminal answering `y` passes, an empty line, `n` and `no` cancel, the deny rules are present. POSIX only.
- [x] 2.2 `uv run pytest tests/unit/test_push_guard.py tests/unit/test_repo_conventions.py`, `uv run ruff check`, `openspec validate guard-push --strict`. The full `poe test` runs once more after the concurrent `label-served-models` change lands.
