"""L0: the Python conventions in AGENTS.md, enforced.

A convention nothing checks is documentation, not a gate — and this repository
learned that the expensive way: twelve test files each grew the same `sys.path`
preamble, and two eval scorers shipped with verdict logic no test could reach.
Each rule below failed silently for months before it was measured.

Signatures are read with `ast` rather than by importing: importing every skill
script would run whatever it does at module scope, and a parse gives a precise
file and function to name in the failure.
"""

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TESTS = REPO / "tests"
SCRIPT_DIRS = [REPO / "harness", REPO / "scripts", *sorted((REPO / "skills").glob("*/scripts"))]


def python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def scripts_with_main() -> list[tuple[Path, ast.FunctionDef]]:
    """Every module that defines a top-level `main`, with that definition."""
    found = []
    for directory in SCRIPT_DIRS:
        for path in python_files(directory):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == "main":
                    found.append((path, node))
    return found


# ---------- imports ----------------------------------------------------------


@pytest.mark.parametrize("path", python_files(TESTS), ids=lambda p: p.name)
def test_no_test_file_manipulates_sys_path(path):
    """Import roots belong in `[tool.pytest.ini_options] pythonpath`.

    The preamble is self-propagating: a file that adjusts `sys.path` teaches
    every test file written after it to do the same. `tests/conftest.py` holds
    the fixtures and `tests/helpers.py` the plain callables.
    """
    source = path.read_text(encoding="utf-8")
    offending = [
        line for line in source.splitlines()
        if "sys.path" in line and not line.lstrip().startswith("#")
        and not line.lstrip().startswith(("\"", "'"))
    ]
    # the docstrings of conftest/helpers name the rule; only real code counts
    tree = ast.parse(source)
    calls_syspath = any(
        isinstance(node, ast.Attribute) and node.attr == "path"
        and isinstance(node.value, ast.Name) and node.value.id == "sys"
        for node in ast.walk(tree)
    )
    assert not calls_syspath, (
        f"{path.relative_to(REPO).as_posix()} manipulates sys.path ({offending[:1]}) — add "
        "the import root to `[tool.pytest.ini_options] pythonpath` in pyproject.toml instead"
    )


# ---------- script entry points ----------------------------------------------


def test_every_script_directory_was_scanned():
    """Guards the guard: a typo'd glob would make the next test vacuous."""
    assert len(SCRIPT_DIRS) >= 6
    assert scripts_with_main(), "no script defines main() — the ast scan found nothing"


@pytest.mark.parametrize(
    ("path", "node"), scripts_with_main(),
    ids=lambda v: v.name if isinstance(v, Path) else "main",
)
def test_main_takes_argv(path, node):
    """`main(argv=None)` is what lets a test call a script in-process.

    A script reachable only as a subprocess is invisible to coverage: `check.py`
    was the most-asserted script in the repository and measured 0% until its
    tests stopped spawning an interpreter.
    """
    names = [arg.arg for arg in node.args.args]
    assert names[:1] == ["argv"], (
        f"{path.relative_to(REPO).as_posix()}: main{tuple(names)} does not take `argv` — use "
        "`def main(argv: list[str] | None = None) -> int` and pass it to parse_args()"
    )
    assert node.args.defaults, (
        f"{path.relative_to(REPO).as_posix()}: `argv` needs a `None` default"
    )


# ---------- cross-platform paths ----------------------------------------------


def stringified_relative_to(tree: ast.AST) -> list[int]:
    """Line numbers where a `relative_to(...)` result is turned into a string
    without `.as_posix()`.

    Only stringified uses are flagged: `a.relative_to(b)` compared as a `Path`
    is correct, and demanding `.as_posix()` there would be wrong. A string,
    though, is either written into a committed file, used as a dict key, or
    compared against a POSIX literal — all three break on Windows.
    """
    def unposixed(expr: ast.AST) -> list[int]:
        wrapped = {
            id(node.func.value) for node in ast.walk(expr)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "as_posix"
        }
        return [
            node.lineno for node in ast.walk(expr)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "relative_to" and id(node) not in wrapped
        ]

    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FormattedValue):          # inside an f-string
            hits += unposixed(node.value)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
              and node.func.id == "str" and node.args):   # str(path.relative_to(...))
            hits += unposixed(node.args[0])
    return sorted(set(hits))


PATH_FILES = [p for root in [*SCRIPT_DIRS, TESTS] for p in python_files(root)]


def test_path_scan_covers_the_tree():
    """Guards the guard: a broken root list would make the next test vacuous."""
    assert len(PATH_FILES) >= 20


@pytest.mark.parametrize("path", PATH_FILES, ids=lambda p: p.name)
def test_relative_paths_render_as_posix(path):
    """`sync_shared.py` wrote `skills\\proposal-check\\references` into every
    generated header on Windows, so the drift check — a CI gate and a pre-commit
    hook — failed on every Windows clone, and a sync there would have rewritten
    the committed headers. An external contributor found it in one of the two
    header sites; the second was added later, and nothing noticed either.
    """
    lines = stringified_relative_to(ast.parse(path.read_text(encoding="utf-8")))
    assert not lines, (
        f"{path.relative_to(REPO).as_posix()}:{lines} stringifies relative_to() without "
        "`.as_posix()` — a repository-relative path that becomes text must render "
        "the same on every host"
    )


# ---------- verdict coverage --------------------------------------------------


def verdict_names() -> list[str]:
    tree = ast.parse((REPO / "harness" / "l1_checks.py").read_text(encoding="utf-8"))
    return sorted(
        node.name for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("verdict_")
    )


@pytest.mark.parametrize("verdict", verdict_names())
def test_every_verdict_has_an_l0_test(verdict):
    """`customize_l1` and `publish_l1` shipped with no L0 coverage because their
    logic sat in a scorer, where nothing looked for it. Verdicts live in
    `l1_checks.py` so they are testable; this checks that they are tested."""
    unit = REPO / "tests" / "unit"
    referenced = any(
        verdict in path.read_text(encoding="utf-8") for path in python_files(unit)
    )
    assert referenced, (
        f"{verdict} has no test under tests/unit/ — a verdict without one is "
        "logic that only a metered eval run can exercise"
    )


def test_private_local_paths_stay_unnamed():
    """The paths in `.git/info/exclude` are private by definition — a committed
    file naming one advertises where sensitive local material lives. The
    entries are read at runtime so this test never has to name them either.
    Skips off this machine (fresh clones and CI have an empty exclude file);
    the immutable archive under openspec/changes/archive/ is exempt as history.
    """
    exclude = REPO / ".git" / "info" / "exclude"
    if not exclude.exists():
        pytest.skip("no .git/info/exclude here")
    private = [
        line.strip().strip("/")
        for line in exclude.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if not private:
        pytest.skip("no private local paths declared")
    import subprocess

    tracked = subprocess.run(
        ["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    offenders = []
    for rel in tracked:
        if rel.startswith("openspec/changes/archive/"):
            continue
        try:
            text = (REPO / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            continue
        offenders.extend(f"{rel}: names `{name}/`" for name in private if name + "/" in text)
    assert not offenders, "\n".join(offenders)
