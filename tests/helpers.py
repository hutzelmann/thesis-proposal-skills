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
import os
import re
import shutil
import stat
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import check as check_script
import support
import sync_shared
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
    (f00's `ml-code-review.md`), and a review whose proposal was renamed away
    (w13) has no sibling. So the check's own listing classifier decides
    (`family_members`): a `-review` or `-feedback` file whose base slug has no
    proposal is one only when it ends in a metadata block, and a kept
    `<slug>.<label>.md` (w15) is never one."""
    name = path.name
    if name in NON_PROPOSAL_MARKDOWN or name.endswith(NON_PROPOSAL_SUFFIXES):
        return False
    listing = [p.name + "/" if p.is_dir() else p.name for p in path.parent.iterdir()]

    def ends_in_block(other: str) -> bool:
        text = (path.parent / other).read_text(encoding="utf-8")
        return check_script.split_proposal(text)[1].found

    member = check_script.family_members(listing, ends_in_block).get(name)
    return member == (name.removesuffix(".md"), check_script.PROPOSAL)


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


# cleared beside fake_home_env: collect.py looks there first for the skills CLI's lock
FAKE_HOME_UNSET = ("XDG_STATE_HOME",)


def fake_home_env(home: Path) -> dict[str, str]:
    """The variables `install.py` and `collect.py` read to find the user's home
    and apps, every one pointing into `home`. For a child's environment as
    well as for `fake_home`."""
    return {"HOME": str(home), "USERPROFILE": str(home),
            "APPDATA": str(home / "AppData" / "Roaming")}


def fake_home(monkeypatch, home: Path) -> None:
    """Make `home` the user's home for this test: `fake_home_env` set,
    `FAKE_HOME_UNSET` cleared."""
    for name, value in fake_home_env(home).items():
        monkeypatch.setenv(name, value)
    for name in FAKE_HOME_UNSET:
        monkeypatch.delenv(name, raising=False)


def fixture_proposal(fixture: str) -> Path:
    """The one proposal markdown file in a fixture directory."""
    return next(p for p in sorted((FIXTURES / fixture).glob("*.md")) if is_fixture_proposal(p))


def review_with_record(review: str, questions: list[str],
                       title: str = "## Research questions reviewed",
                       marker: str = "{n}.") -> str:
    """`review` closing on a record of the research questions it judged, each
    behind `marker` (`{n}` is its position): the shape the review skill writes
    (skill-review spec: research questions recorded in the review)."""
    lines = "".join(f"{marker.format(n=n)} {question}\n" for n, question in enumerate(questions, 1))
    return f"{review}\n{title}\n\n{lines}"


def f04_numbered_questions() -> list[str]:
    """f04's four numbered sub-questions, markers removed. f04 states an
    overarching question in prose before them, so it is the shape a loose
    record gets wrong."""
    text = fixture_proposal("f04-dsr-vendor-heavy").read_text(encoding="utf-8")
    return [line[3:] for line in text.splitlines() if re.match(r"[1-9]\. Wie ", line)]


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


WINGET_INSTALL_RE = re.compile(r"winget install\b([^\n`]*)")
WINGET_VALUE_OPTIONS = {"--source", "-s"}


def winget_problems(text: str) -> list[str]:
    """One problem per `winget install` command in `text` that does not select
    exactly one package by exact id. winget turns a lone positional into the
    query and filters it by `--id`, so `--id A B` matches nothing and installs
    nothing; two positionals refuse `--id` outright (winget-cli
    `MoveMultiQueryToSingleQueryIfNeeded`, `ArgumentForSinglePackage…`). A
    command ends at a backtick or a line end — the shapes the publish skill,
    its install hint and the install guide use."""
    problems = []
    for match in WINGET_INSTALL_RE.finditer(text):
        tokens = match.group(1).split()
        ids, positionals = [], []
        exact = False
        rest = iter(tokens)
        for token in rest:
            if token == "--id":
                ids.append(next(rest, ""))
            elif token in ("-e", "--exact"):
                exact = True
            elif token in WINGET_VALUE_OPTIONS:
                next(rest, None)
            else:
                positionals.append(token)
        command = match.group(0).strip()
        if len(ids) != 1 or not ids[0]:
            problems.append(f"{command!r}: needs exactly one --id")
        if positionals:
            problems.append(f"{command!r}: stray arguments {positionals} beside --id")
        if not exact:
            problems.append(f"{command!r}: no -e/--exact")
    return problems


def json_path(path: Path | str) -> str:
    """`path` as it is written inside a JSON string. A raw Windows path put
    into JSON text turns its backslashes into escapes JSON rejects
    ("Invalid \\escape"), so every in-process `__WS__` substitution goes
    through here; the fake host scripts, which cannot import this module,
    spell out the same `json.dumps(...)[1:-1]`."""
    return json.dumps(str(path))[1:-1]


def saved_stream(path: Path, ws: Path | str | None = None,
                 home_skills: Path | str | None = None) -> list[dict]:
    """A saved JSON-lines event list, its `__WS__` placeholder replaced by `ws`
    and its `__HOME_SKILLS__` placeholder (a user-scope skill directory
    outside the workspace) by `home_skills`, each JSON-escaped (`json_path`)
    when given: native absolute paths on every platform."""
    text = path.read_text(encoding="utf-8")
    if ws is not None:
        text = text.replace("__WS__", json_path(ws))
    if home_skills is not None:
        text = text.replace("__HOME_SKILLS__", json_path(home_skills))
    return [json.loads(line) for line in text.splitlines() if line.strip()]


REAL_LSTAT = os.lstat
# this process's descriptors, where Linux lists them; PROC_FDS: whether it does here
PROC_FD_DIR = "/proc/self/fd"
PROC_FDS = os.name == "posix" and Path(PROC_FD_DIR).is_dir()


def reusing_lstat(ws: Path, start: tuple[int, int]) -> Callable[..., os.stat_result]:
    """`os.lstat` as on a filesystem that hands a removed directory's inode
    number to the next directory at once (ext4 does; tmpfs and btrfs, where
    the suite usually runs, do not): `ws`, once it is a directory other than
    the start's, reports the start's number while no descriptor of this
    process keeps the start's inode alive (`PROC_FD_DIR`). Only for a start
    that was removed: a start renamed away is alive without one."""
    def alive() -> bool:
        for entry in Path(PROC_FD_DIR).iterdir():
            with contextlib.suppress(OSError):
                info = os.fstat(int(entry.name))
                if (info.st_dev, info.st_ino) == start:
                    return True
        return False

    def lstat(path, *args, **kwargs) -> os.stat_result:
        info = REAL_LSTAT(path, *args, **kwargs)
        if (Path(path) == ws and stat.S_ISDIR(info.st_mode)
                and (info.st_dev, info.st_ino) != start and not alive()):
            fields = list(info)
            fields[stat.ST_INO] = start[1]
            return os.stat_result(fields)
        return info

    return lstat


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


def tracked_files() -> list[str]:
    """Every tracked path, repo-relative. Repository-wide scans walk this list,
    never the directory tree: the tree also holds the private proposals
    directory, which no test may read."""
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True,
        encoding="utf-8",
    ).stdout
    return out.splitlines()


# Everything scripts/sync_shared.py reads or writes, and the script itself.
SYNC_TREE = ("shared", "skills", ".gitattributes", "scripts/sync_shared.py",
             *sync_shared.PROMPT_DOCS)


def copy_sync_tree(dest: Path) -> Path:
    """Copy the sync's whole world into `dest`, so a test that writes — a real
    sync, a commit through the pre-commit hook — never touches the tracked
    tree that other tests (and other sessions) are reading."""
    for rel in SYNC_TREE:
        source, target = REPO / rel, dest / rel
        if source.is_dir():
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return dest
