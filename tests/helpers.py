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

# markdown that sits beside a fixture proposal without being one: the corpus
# README and workspace overrides by name; by suffix, a handout and a harvest
# record (w06) — inputs to a skill, never documents to check or build
NON_PROPOSAL_MARKDOWN = {"README.md", "guidelines.md"}
# .notes.md: the companion working file (w10 is the first fixture to carry one)
NON_PROPOSAL_SUFFIXES = ("-handout.md", ".harvest.md", ".notes.md")
REVIEW_SUFFIX = "-review.md"
# the draft the dev-runner tests place in a workspace as a run's produced draft
CLEAN_DRAFT = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text(encoding="utf-8")
# the Copilot host's synthetic fixtures (README there) and the synthetic token
# every Copilot test writes into a token file or hands to a child
COPILOT_STREAMS = REPO / "tests" / "unit" / "data" / "copilot_streams"
COPILOT_TOKEN = "github_pat_SYNTHETIC_TEST_ONLY"


def is_fixture_proposal(path: Path) -> bool:
    """Whether a markdown file in the fixture corpus is a proposal. One
    predicate for every corpus walker, so a new kind of companion file is
    excluded everywhere at once rather than wherever someone remembered.

    An earlier round's review (w09) is `<slug>-review.md` beside `<slug>.md`;
    the suffix alone would also match a proposal slugged `…-review`
    (f00's `ml-code-review.md`), so the sibling decides."""
    name = path.name
    if name in NON_PROPOSAL_MARKDOWN or name.endswith(NON_PROPOSAL_SUFFIXES):
        return False
    stem = name.removesuffix(REVIEW_SUFFIX)
    return stem == name or not path.with_name(f"{stem}.md").is_file()


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
    return next(p for p in sorted((FIXTURES / fixture).glob("*.md")) if is_fixture_proposal(p))


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


def json_path(path: Path | str) -> str:
    """`path` as it is written inside a JSON string. A raw Windows path put
    into JSON text turns its backslashes into escapes JSON rejects
    ("Invalid \\escape"), so every in-process `__WS__` substitution goes
    through here; the fake host scripts, which cannot import this module,
    spell out the same `json.dumps(...)[1:-1]`."""
    return json.dumps(str(path))[1:-1]


def saved_stream(path: Path, ws: Path | str | None = None) -> list[dict]:
    """A saved JSON-lines event list, its `__WS__` placeholder replaced by `ws`
    (JSON-escaped, `json_path`) when one is given."""
    text = path.read_text(encoding="utf-8")
    if ws is not None:
        text = text.replace("__WS__", json_path(ws))
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def copilot_stream(name: str, ws: Path | str | None = None) -> list[dict]:
    """A saved Copilot event list from COPILOT_STREAMS, its `__WS__` placeholder
    replaced by `ws` when one is given."""
    return saved_stream(COPILOT_STREAMS / f"{name}.jsonl", ws)


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
