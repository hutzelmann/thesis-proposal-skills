"""L0: user-side scripts write UTF-8 whatever the platform gave their streams
(skill-packaging spec, "Script output encoding"; change utf8-script-output).

On Windows a captured script writes to a pipe, and Python encodes a pipe in the
ANSI code page: cp1252 on a Western-European machine. A name outside it, such
as an author in a CSL-YAML candidate, aborted the run with UnicodeEncodeError.

Three layers. In-process: every entry point's `main()` against cp1252 streams,
which is what coverage sees. Subprocess: one real run per script family with
`PYTHONIOENCODING=cp1252`, which puts a child's streams exactly where the
Windows pipe puts them, on every platform, and runs against a real pipe on the
Windows CI job. Pin: every user-side `main()` makes the switch first, and the
helper is the same in every family. All data is synthetic and built in tmp_path.
"""

from __future__ import annotations

import ast
import contextlib
import io
import os
import subprocess
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import check
import collect
import common
import publish
import pytest
import search
import snowball
import validate_refs
from helpers import CLEAN_DRAFT, FAKE_HOME_UNSET, REPO, fake_home, fake_home_env

import install

# made up, and outside cp1252 twice over: neither `Ł` nor `ő` has a cp1252 byte
GIVEN, FAMILY = "Łucja", "Musterfrau-Kővári"
STEM = f"{GIVEN}-{FAMILY}"
TITLE = "Agents for Synthetic Testing"
DOI = "10.5555/synthetic-0001"
SEED = "10.5555/synthetic-seed"

SCRIPTS = REPO / "skills"
HELPER = "utf8_output"


def candidate() -> dict:
    return common.entry(title=TITLE, source="crossref", doi=DOI, year=2025,
                        authors=[{"family": FAMILY, "given": GIVEN}])


class Source:
    """A literature source module: `search` for search.py, the citation-graph
    edges for snowball.py. Answers offline."""

    def __init__(self, items: list[dict]):
        self.items = items

    def search(self, _query: str, limit: int) -> list[dict]:
        return self.items[:limit]

    def references(self, _doi: str, limit: int) -> list[dict]:
        return self.items[:limit]

    citations = references


# ---------- in-process: every entry point -------------------------------------


def cp1252(errors: str, **kwargs) -> io.TextIOWrapper:
    """A stream as Windows opens it on a pipe: stdout `strict`, stderr
    `backslashreplace`."""
    return io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors=errors, **kwargs)


@dataclass
class Pipe:
    out: io.TextIOWrapper
    err: io.TextIOWrapper

    def written(self, stream: str) -> bytes:
        target = self.out if stream == "out" else self.err
        target.flush()
        return target.buffer.getvalue()


@contextlib.contextmanager
def windows_pipe(stdout_errors: str = "strict", **stdout_options) -> Iterator[Pipe]:
    """Swapped in and out inside the test body: pytest's capture re-installs
    its own streams when the call phase starts, over anything a fixture set."""
    pipe = Pipe(cp1252(stdout_errors, **stdout_options), cp1252("backslashreplace"))
    saved = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = pipe.out, pipe.err
    try:
        yield pipe
    finally:
        sys.stdout, sys.stderr = saved


@dataclass
class Case:
    main: Callable[[list[str]], int]
    argv: list[str]
    code: int
    stream: str  # "out" or "err": where the name shows up
    names: tuple[str, ...]


def case_check(tmp_path: Path, monkeypatch) -> Case:
    (tmp_path / f"{STEM}.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return Case(check.main, [f"{STEM}.md"], 0, "out", (STEM,))


def case_search(_tmp_path: Path, monkeypatch) -> Case:
    monkeypatch.setattr(search, "SEARCH_SOURCES", {"crossref": Source([candidate()])})
    return Case(search.main, ["agents", "--sources", "crossref"], 0, "out", (GIVEN, FAMILY))


def case_snowball(_tmp_path: Path, monkeypatch) -> Case:
    monkeypatch.setattr(snowball, "GRAPH_SOURCES", {"openalex": Source([candidate()])})
    return Case(snowball.main, [SEED], 0, "out", (GIVEN, FAMILY))


def case_validate_refs(tmp_path: Path, monkeypatch) -> Case:
    proposal = tmp_path / "agents.md"
    proposal.write_text(
        "Body [@Musterfrau25Agents].\n\n---\nreferences:\n- id: Musterfrau25Agents\n"
        f"  type: article-journal\n  title: {TITLE}\n  DOI: {DOI}\n---\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(validate_refs, "lookup_doi", lambda _doi: candidate())
    return Case(validate_refs.main, [str(proposal)], 0, "out", (GIVEN, FAMILY))


def case_publish(tmp_path: Path, _monkeypatch) -> Case:
    proposal = tmp_path / f"{STEM}.md"
    proposal.write_text(CLEAN_DRAFT, encoding="utf-8")
    return Case(publish.main, [str(proposal), "--handout"], 0, "out", (f"{STEM}-handout.md",))


def case_collect(tmp_path: Path, monkeypatch) -> Case:
    fake_home(monkeypatch, tmp_path / "home")
    monkeypatch.chdir(tmp_path)
    return Case(collect.main, ["--dry-run", "--out", str(tmp_path / STEM)], 0, "out", (STEM,))


def case_install(tmp_path: Path, monkeypatch) -> Case:
    """The installer's stdout never carries user text (paths are shown home-
    or folder-relative); a diagnostic naming the user's own argument does."""
    fake_home(monkeypatch, tmp_path / "home")
    monkeypatch.chdir(tmp_path)
    argv = ["--scope", "all", "--source", str(tmp_path / f"{STEM}.zip")]
    return Case(install.main, argv, install.EXIT_ENV, "err", (STEM,))


CASES = {
    "check": case_check,
    "search": case_search,
    "snowball": case_snowball,
    "validate_refs": case_validate_refs,
    "publish": case_publish,
    "collect": case_collect,
    "install": case_install,
}


@pytest.mark.parametrize("entry", CASES)
def test_entry_point_writes_utf8_into_a_cp1252_pipe(entry, tmp_path, monkeypatch):
    case = CASES[entry](tmp_path, monkeypatch)
    with windows_pipe() as pipe:
        code = case.main(case.argv)
    assert code == case.code
    written = pipe.written(case.stream)
    for name in case.names:
        assert name.encode("utf-8") in written, written.decode("utf-8", errors="replace")


# ---------- subprocess: one real run per family -----------------------------------


@dataclass
class Run:
    script: Path
    argv: list[str]
    code: int
    stream: str
    name: str


def check_family(work: Path) -> Run:
    (work / f"{STEM}.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    return Run(SCRIPTS / "proposal-check/scripts/check.py", [f"{STEM}.md"], 0, "out", STEM)


def common_family(work: Path) -> Run:
    """Through validate_refs.py: search.py and snowball.py reach their output
    only over the network. A reference with neither DOI nor title is reported
    without a request, so this path is offline."""
    (work / "agents.md").write_text(
        f"Body [@{STEM}].\n\n---\nreferences:\n- id: {STEM}\n  type: article-journal\n---\n",
        encoding="utf-8",
    )
    return Run(SCRIPTS / "proposal-import/scripts/validate_refs.py", ["agents.md"], 0, "out",
               STEM)


def publish_family(work: Path) -> Run:
    (work / f"{STEM}.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    return Run(SCRIPTS / "proposal-publish/scripts/publish.py", [f"{STEM}.md", "--handout"], 0,
               "out", f"{STEM}-handout.md")


def collect_family(work: Path) -> Run:
    return Run(SCRIPTS / "proposal-troubleshoot/scripts/collect.py",
               ["--dry-run", "--out", str(work / STEM)], 0, "out", STEM)


def install_family(work: Path) -> Run:
    return Run(REPO / "install.py", ["--scope", "all", "--source", str(work / f"{STEM}.zip")],
               install.EXIT_ENV, "err", STEM)


RUNS = {
    "check": check_family,
    "common": common_family,
    "publish": publish_family,
    "collect": collect_family,
    "install": install_family,
}


def child_env(home: Path) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in FAKE_HOME_UNSET}
    return {**env, **fake_home_env(home), "PYTHONIOENCODING": "cp1252"}


@pytest.mark.parametrize("family", RUNS)
def test_script_family_writes_utf8_through_a_cp1252_pipe(family, tmp_path):
    work, home = tmp_path / "work", tmp_path / "home"
    work.mkdir()
    home.mkdir()
    run = RUNS[family](work)
    done = subprocess.run([sys.executable, str(run.script), *run.argv], cwd=work,
                          env=child_env(home), capture_output=True, check=False)
    written = done.stdout if run.stream == "out" else done.stderr
    assert done.returncode == run.code, done.stderr.decode("utf-8", errors="replace")
    assert run.name.encode("utf-8") in written, written.decode("utf-8", errors="replace")


# ---------- the helper ----------------------------------------------------------------

FAMILIES = {"check": check, "common": common, "publish": publish, "collect": collect,
            "install": install}


@pytest.mark.parametrize("family", FAMILIES)
def test_helper_switches_to_utf8_and_keeps_handlers_and_newlines(family):
    """Both handlers non-default, since reconfigure(encoding=...) alone resets
    either to strict: stdout as a POSIX C locale opens it (surrogateescape),
    stderr as every platform opens it (backslashreplace)."""
    with windows_pipe("surrogateescape", newline="\r\n", line_buffering=True) as pipe:
        getattr(FAMILIES[family], HELPER)()
        print("\udcff" + GIVEN)  # a file name's undecodable byte, written back as it came
        print("\udcff", end="", file=sys.stderr)  # a lone surrogate: escaped, never raised
    out, err = pipe.out, pipe.err
    assert (out.encoding, out.errors, out.line_buffering) == ("utf-8", "surrogateescape", True)
    assert (err.encoding, err.errors) == ("utf-8", "backslashreplace")
    assert pipe.written("out") == b"\xff" + f"{GIVEN}\r\n".encode()
    assert pipe.written("err") == b"\\udcff"


@pytest.mark.parametrize("family", FAMILIES)
def test_helper_leaves_streams_without_reconfigure_alone(family, monkeypatch):
    """A caller's StringIO (tests/helpers.py's run_check), and the None a
    windowless interpreter gives."""
    buffer = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buffer)
    monkeypatch.setattr(sys, "stderr", None)
    getattr(FAMILIES[family], HELPER)()
    print(GIVEN)
    assert sys.stdout is buffer
    assert sys.stderr is None
    assert buffer.getvalue() == f"{GIVEN}\n"


# ---------- captured tool output: UTF-8, never the code page -----------------------------

# what pandoc and typst write, UTF-8 on every platform. `Ł` is C5 81, and cp1252
# has no character for 0x81; the trailing 0xFF is no UTF-8 at all. Either
# aborted a text-mode capture on decoding, whatever the tool's exit code.
TOOL_MESSAGE = f"[WARNING] Citeproc: citation {GIVEN}2025 not found"


def tool(code: int) -> list[str]:
    said = TOOL_MESSAGE.encode() + b" \xff\n"
    script = f"import sys; sys.stderr.buffer.write({said!r}); sys.exit({code})"
    return [sys.executable, "-c", script]


def test_publish_reads_a_succeeding_tools_message_without_decoding_it_away():
    assert publish.run(tool(0)) is None


def test_publish_quotes_a_failing_tools_message_intact():
    with pytest.raises(SystemExit) as failed:
        publish.run(tool(1))
    assert f"{TOOL_MESSAGE} �" in str(failed.value.code)


# ---------- pin: every user-side main() switches first ----------------------------------

USER_SIDE = [*sorted(SCRIPTS.glob("*/scripts/*.py")), REPO / "install.py"]


def parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def top_level(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    return next((node for node in tree.body
                 if isinstance(node, ast.FunctionDef) and node.name == name), None)


ENTRY_POINTS = [(path, main) for path in USER_SIDE
                if (main := top_level(parsed(path), "main")) is not None]


def label(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def entry_id(value: object) -> str:
    return label(value) if isinstance(value, Path) else "main"


def is_docstring(node: ast.stmt) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)


def is_version_gate(node: ast.stmt) -> bool:
    return isinstance(node, ast.If) and any(
        isinstance(n, ast.Attribute) and n.attr == "version_info" for n in ast.walk(node.test))


def test_the_pin_found_every_entry_point():
    """Guards the guard: check.py six times, validate_refs.py twice, search,
    snowball, publish, collect, install."""
    assert len(ENTRY_POINTS) >= 13


@pytest.mark.parametrize(("path", "main"), ENTRY_POINTS, ids=entry_id)
def test_main_switches_to_utf8_first(path, main):
    """Before argument parsing, so usage errors are UTF-8 too. The installer
    keeps its version gate first, so an old interpreter still gets its sentence."""
    body = [node for node in main.body[:1] if not is_docstring(node)] + main.body[1:]
    if path.name == "install.py":
        assert is_version_gate(body[0]), f"{label(path)}: the version gate is no longer first"
        body = body[1:]
    own = top_level(parsed(path), HELPER) is not None
    expected = HELPER if own else f"common.{HELPER}"
    first = ast.unparse(body[0])
    assert first == f"{expected}()", (
        f"{label(path)}: main() starts with `{first.splitlines()[0]}`, not {expected}()")
    if not own:
        assert top_level(parsed(path.with_name("common.py")), HELPER) is not None, (
            f"{label(path)}: the common.py beside it defines no {HELPER}()")


CHILD_CALLS = {"run", "Popen", "call", "check_call", "check_output"}


def child_calls(tree: ast.Module) -> list[ast.Call]:
    return [node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"
            and node.func.attr in CHILD_CALLS]


def decodes_with_the_locale(call: ast.Call) -> bool:
    """Text mode (`text=`, `universal_newlines=` or `errors=`) with no
    `encoding=`: the child's output is then decoded in the platform's default
    encoding, the ANSI code page on Windows, which UTF-8 bytes can abort."""
    given = {keyword.arg: keyword.value for keyword in call.keywords}
    off = [name for name in ("text", "universal_newlines")
           if isinstance(given.get(name), ast.Constant) and given[name].value is False]
    text_mode = bool({"text", "universal_newlines", "errors"} & given.keys() - set(off))
    return text_mode and "encoding" not in given


def test_no_user_side_script_decodes_a_childs_output_with_the_code_page():
    calls = [(path, call) for path in USER_SIDE for call in child_calls(parsed(path))]
    assert len(calls) >= 2, "the scan no longer sees publish.py's and install.py's children"
    assert [f"{label(path)}:{call.lineno}" for path, call in calls
            if decodes_with_the_locale(call)] == []


def test_every_family_carries_the_same_helper():
    """A skill never imports from a sibling, so each family keeps its own
    copy; this pin keeps the copies one function."""
    helpers = {label(path): ast.dump(node) for path in USER_SIDE
               if (node := top_level(parsed(path), HELPER)) is not None}
    families = {"skills/proposal-check/scripts/check.py",
                "skills/proposal-lit-search/scripts/common.py",
                "skills/proposal-publish/scripts/publish.py",
                "skills/proposal-troubleshoot/scripts/collect.py", "install.py"}
    assert families <= set(helpers), f"missing: {sorted(families - set(helpers))}"
    reference = helpers["skills/proposal-check/scripts/check.py"]
    assert [p for p, dump in helpers.items() if dump != reference] == []
