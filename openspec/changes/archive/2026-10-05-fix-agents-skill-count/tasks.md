# Tasks

## 1. Correct the counts

- [x] 1.1 AGENTS.md "What this repo is": "eleven `proposal-*` agent skills … ten student-side, plus the supervisor-side `proposal-supervise`"; verify `ls skills/` lists eleven `proposal-*` directories.
- [x] 1.2 AGENTS.md "Skill header pattern": workflow line and voice block "byte-identical in all eleven files", "the other ten exist", "not eleven files"; verify `grep -n -E '\b(nine|ten)\b' AGENTS.md` returns only the corrected "ten student-side" and "the other ten" (no "nine", no "all ten").
- [x] 1.3 `harness/routing.py` module docstring: "the eleven frontmatter descriptions"; verify `git diff` on the file touches the docstring only.

## 2. Sweep

- [x] 2.1 Grep `README.md`, `CONTRIBUTING.md`, `docs/`, `harness/`, `shared/blocks/`, `openspec/specs/`, `skills/` and `tests/` for stale skill counts (`nine`/`ten`/`9`/`10` next to skill, student-side, files, or "the other"/"all"); verify the only hits outside `openspec/changes/archive/` were the five fixed above (`harness/README.md` already says eleven twice; `test_skill_header_pattern.py` asserts 11).

## 3. Verify

- [x] 3.1 `uv run poe test` and `uv run poe specs` green.
