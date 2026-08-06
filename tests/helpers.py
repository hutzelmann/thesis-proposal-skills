"""Plain callables shared by the L0 tests.

Split from `conftest.py` on one line: pytest fixtures live there, ordinary
functions live here. A fixture would force `run_check` into the signature of
every test that calls it — around forty of them — for no gain, since it needs
nothing pytest provides.

Import roots come from `[tool.pytest.ini_options] pythonpath`; nothing here or
in any test may touch `sys.path` (`tests/unit/test_repo_conventions.py`
enforces it).
"""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from pathlib import Path

import check as check_script

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"

# markdown that sits beside a fixture proposal without being one
NON_PROPOSAL_MARKDOWN = {"README.md", "guidelines.md"}


@dataclass(frozen=True)
class CheckRun:
    """Mirrors the `CompletedProcess` shape these tests used when every check
    ran as a subprocess, so the call sites read the same after moving
    in-process."""

    returncode: int
    stdout: str


def run_check(proposal: Path, *extra: str) -> CheckRun:
    """Run the shipped check script in-process and capture its report.

    In-process is what makes `check.py` visible to coverage: as a subprocess it
    contributed nothing at all, despite being the most-asserted script in the
    repository. The subprocess path stays covered by `test_fixture_oracles.py`,
    which exists to exercise the script exactly as a user invokes it.
    """
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = check_script.main([str(proposal), *extra])
    return CheckRun(returncode=code, stdout=buffer.getvalue())


def fixture_proposal(fixture: str) -> Path:
    """The one proposal markdown file in a fixture directory."""
    return next(
        p for p in sorted((FIXTURES / fixture).glob("*.md"))
        if p.name not in NON_PROPOSAL_MARKDOWN and not p.name.endswith("-handout.md")
    )
