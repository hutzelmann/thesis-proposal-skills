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
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import check as check_script
import support
from routing import Followed

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"
MODEL_CATALOG = REPO / "tests" / "unit" / "data" / "model_catalog"
REGISTRY_PATH = REPO / "harness" / "models.toml"

# markdown that sits beside a fixture proposal without being one
NON_PROPOSAL_MARKDOWN = {"README.md", "guidelines.md"}
# the draft the dev-runner tests place in a workspace as a run's produced draft
CLEAN_DRAFT = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text(encoding="utf-8")
# the Copilot host's synthetic fixtures (README there) and the synthetic token
# every Copilot test writes into a token file or hands to a child
COPILOT_STREAMS = REPO / "tests" / "unit" / "data" / "copilot_streams"
COPILOT_TOKEN = "github_pat_SYNTHETIC_TEST_ONLY"


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


def shipped_registry() -> support.Registry:
    """The registry the harness ships, parsed afresh on every call so that no
    test can see another's mutation of it."""
    return support.parse_registry(REGISTRY_PATH.read_text(encoding="utf-8"))


def followed(events: list[dict], stop: Callable[[list[dict]], bool], *, returncode: int = 0,
             stderr: str = "", timed_out: bool = False) -> Followed:
    """What `routing.follow_stream` returns for a host that wrote `events`: the
    caller's stop condition applied event by event, as the real reader applies
    it, so a fake host still exercises the stop the dev runner hands over. A
    stopped host's exit status is the harness's own (-15, terminated)."""
    seen: list[dict] = []
    for event in events:
        seen.append(event)
        if stop(seen):
            return Followed(seen, -15, "", stopped=True, timed_out=False)
    return Followed(seen, returncode, stderr, stopped=False, timed_out=timed_out)


def copilot_stream(name: str, ws: Path | str | None = None) -> list[dict]:
    """A saved Copilot event list from COPILOT_STREAMS, its `__WS__` placeholder
    replaced by `ws` when one is given."""
    text = (COPILOT_STREAMS / f"{name}.jsonl").read_text(encoding="utf-8")
    if ws is not None:
        text = text.replace("__WS__", str(ws))
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def copilot_reply(name: str) -> object:
    """A Copilot JSON fixture from COPILOT_STREAMS: a status reply, a model
    listing, a roster or a probe."""
    return json.loads((COPILOT_STREAMS / f"{name}.json").read_text(encoding="utf-8"))


def failing_fetch(message: str):
    """A stand-in for `model_currency.fetch_json` whose every read fails the
    way an unreachable catalog does (an OSError carrying `message`)."""
    def fetch(*_request: object) -> object:
        raise OSError(message)

    return fetch
