"""`scripts/openspec_currency.py`: the OpenSpec pin against npm, the local CLI and the skills.

testing-harness spec, "OpenSpec version kept current". Every source is stubbed:
the registry answer, the local `openspec --version`, and the generated skills
under `.claude/skills/`. The pin is read from a copy of `scripts/validate_specs.py`
in a temporary root, so the write mode never touches the repository.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys

import openspec_currency
import pytest
import validate_specs
from helpers import REPO

PIN = validate_specs.OPENSPEC_VERSION
REAL_LOCAL_CLI = openspec_currency.local_cli_version


def bumped(version: str, part: int = 2) -> str:
    numbers = [int(n) for n in version.split(".")]
    numbers[part] += 1
    return ".".join(str(n) for n in numbers[: part + 1] + [0] * (2 - part))


class World:
    """The four sources, as one test arranges them."""

    def __init__(self, root) -> None:
        self.root = root
        self.answer: object = {"name": validate_specs.PACKAGE, "version": PIN}
        self.local: str | None = PIN
        self.urls: list[str] = []
        self.guard = None

    def fetch(self, url: str, _timeout: float) -> object:
        self.urls.append(url)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer

    def stamp(self, skill: str, line: str | None) -> None:
        skill_md = self.root / ".claude" / "skills" / skill / "SKILL.md"
        skill_md.parent.mkdir(parents=True, exist_ok=True)
        meta = f"metadata:\n  author: openspec\n  {line}\n" if line else "metadata: {}\n"
        skill_md.write_text(f"---\nname: {skill}\n{meta}---\n\nBody.\n", encoding="utf-8")

    @property
    def pin_file(self):
        return self.root / openspec_currency.PIN_FILE

    def run(self, *argv: str) -> int:
        return openspec_currency.main(["--root", str(self.root), *argv])


@pytest.fixture(autouse=True)
def world(monkeypatch, tmp_path) -> World:
    """L0 is offline: the registry fetch and the local CLI are the world's."""
    w = World(tmp_path)
    w.pin_file.parent.mkdir(parents=True)
    w.pin_file.write_bytes((REPO / openspec_currency.PIN_FILE).read_bytes())
    w.stamp("openspec-propose", f'generatedBy: "{PIN}"')
    w.stamp("openspec-apply-change", f'generatedBy: "{PIN}"')
    w.guard = openspec_currency.fetch_json  # tests/conftest.py's, checked below
    monkeypatch.setattr(openspec_currency, "fetch_json", w.fetch)
    monkeypatch.setattr(openspec_currency, "local_cli_version", lambda: w.local)
    return w


def warnings(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith("warning:")]


# ---------- the pin against npm ----------------------------------------------------


def test_a_current_pin_exits_0_without_warnings(world, capsys):
    assert world.run() == 0
    out = capsys.readouterr().out
    assert "current" in out
    assert warnings(out) == []
    assert world.urls == [openspec_currency.REGISTRY_URL]


def test_the_registry_url_is_npms_latest_for_the_pinned_package():
    assert openspec_currency.REGISTRY_URL == "https://registry.npmjs.org/@fission-ai/openspec/latest"


@pytest.mark.parametrize("part", [0, 1, 2])
def test_a_pin_behind_exits_1(world, capsys, part):
    world.answer = {"name": validate_specs.PACKAGE, "version": bumped(PIN, part)}
    assert world.run() == 1
    out = capsys.readouterr().out
    assert "behind" in out
    assert bumped(PIN, part) in out


def test_a_pin_ahead_of_npm_warns_and_exits_0(world, capsys):
    older = "0.9.9"
    world.answer = {"name": validate_specs.PACKAGE, "version": older}
    assert world.run() == 0
    assert any("newer than npm's latest" in line for line in warnings(capsys.readouterr().out))


@pytest.mark.parametrize("answer", [
    OSError("network unreachable"),
    ValueError("not JSON"),
    {"name": "@someone-else/openspec", "version": "9.9.9"},
    {"name": validate_specs.PACKAGE, "version": "2.0.0-beta.1"},
    {"name": validate_specs.PACKAGE, "version": 2},
    {"name": validate_specs.PACKAGE},
    ["2.0.0"],
])
def test_an_unusable_registry_answer_is_unknown_and_writes_nothing(world, capsys, answer):
    world.answer = answer
    before = world.pin_file.read_bytes()
    assert world.run("--write", "--json") == 2
    captured = capsys.readouterr()
    assert "unknown" in captured.err
    assert captured.out == ""
    assert world.pin_file.read_bytes() == before


# ---------- the write mode -----------------------------------------------------------


def test_the_write_mode_changes_the_pin_and_no_other_line(world):
    newer = bumped(PIN)
    world.answer = {"name": validate_specs.PACKAGE, "version": newer}
    before = world.pin_file.read_text(encoding="utf-8").splitlines(keepends=True)
    assert world.run("--write") == 1
    after = world.pin_file.read_text(encoding="utf-8").splitlines(keepends=True)
    changed = [(old, new) for old, new in zip(before, after, strict=True) if old != new]
    assert changed == [(f'OPENSPEC_VERSION = "{PIN}"\n', f'OPENSPEC_VERSION = "{newer}"\n')]


def test_the_write_mode_keeps_crlf_line_endings(world):
    """A Windows checkout keeps its line endings: the pin line is rewritten in place."""
    text = world.pin_file.read_text(encoding="utf-8")
    world.pin_file.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    newer = bumped(PIN)
    world.answer = {"name": validate_specs.PACKAGE, "version": newer}
    assert world.run("--write") == 1
    data = world.pin_file.read_bytes()
    assert f'OPENSPEC_VERSION = "{newer}"\r\n'.encode() in data
    assert data.count(b"\r\n") == text.count("\n")
    assert b"\n" not in data.replace(b"\r\n", b"")


def test_the_write_mode_is_idempotent(world):
    world.answer = {"name": validate_specs.PACKAGE, "version": bumped(PIN)}
    world.run("--write")
    once = world.pin_file.read_bytes()
    assert world.run("--write") == 0  # now current
    assert world.pin_file.read_bytes() == once


def test_a_current_pin_is_never_rewritten(world):
    before = world.pin_file.stat().st_mtime_ns
    assert world.run("--write") == 0
    assert world.pin_file.stat().st_mtime_ns == before


@pytest.mark.parametrize("text", [
    "OPENSPEC_VERSION = None\n",
    f'OPENSPEC_VERSION = "{PIN}"\nOPENSPEC_VERSION = "{PIN}"\n',
    f'OPENSPEC_VERSION = "v{PIN}"\n',
])
def test_a_pin_line_it_cannot_read_exits_3_and_writes_nothing(world, capsys, text):
    world.pin_file.write_text(text, encoding="utf-8")
    world.answer = {"name": validate_specs.PACKAGE, "version": "99.0.0"}
    assert world.run("--write") == 3
    assert "nothing written" in capsys.readouterr().err
    assert world.pin_file.read_text(encoding="utf-8") == text


def test_a_missing_pin_file_exits_3(world, capsys):
    world.pin_file.unlink()
    assert world.run("--write") == 3
    assert "nothing written" in capsys.readouterr().err
    assert world.urls == []


def test_the_pin_is_read_from_the_gate_itself():
    text = (REPO / openspec_currency.PIN_FILE).read_text(encoding="utf-8")
    assert openspec_currency.read_pin(text) == validate_specs.OPENSPEC_VERSION


# ---------- the local CLI and the generated skills ------------------------------------------


def test_a_local_cli_off_the_pin_warns_and_names_the_action(world, capsys):
    world.local = "1.13.1" if PIN != "1.13.1" else "1.12.0"
    assert world.run() == 0
    found = warnings(capsys.readouterr().out)
    assert len(found) == 1
    assert world.local in found[0]
    assert "update the openspec package" in found[0]


def test_skills_generated_by_another_version_warn_and_name_the_action(world, capsys):
    world.stamp("openspec-propose", 'generatedBy: "1.7.0"')
    world.stamp("openspec-explore", "generatedBy: 1.7.0")
    assert world.run() == 0
    found = warnings(capsys.readouterr().out)
    assert len(found) == 1
    assert "1.7.0" in found[0]
    assert "openspec update" in found[0]
    assert "2 " in found[0]


def test_a_skill_without_a_stamp_warns(world, capsys):
    world.stamp("openspec-sync-specs", None)
    assert world.run() == 0
    found = warnings(capsys.readouterr().out)
    assert len(found) == 1
    assert "no generatedBy" in found[0]


def test_local_tooling_never_changes_the_exit_status(world):
    world.local = "0.1.0"
    world.stamp("openspec-propose", 'generatedBy: "0.1.0"')
    world.answer = {"name": validate_specs.PACKAGE, "version": bumped(PIN)}
    assert world.run() == 1


def test_absent_cli_and_skills_are_noted_not_warned(world, capsys):
    world.local = None
    for skill_md in (world.root / ".claude" / "skills").glob("*/SKILL.md"):
        skill_md.unlink()
    assert world.run() == 0
    out = capsys.readouterr().out
    assert warnings(out) == []
    notes = [line for line in out.splitlines() if line.startswith("note:")]
    assert len(notes) == 2


def test_other_skills_are_not_read(world, capsys):
    skill_md = world.root / ".claude" / "skills" / "proposal-check" / "SKILL.md"
    skill_md.parent.mkdir(parents=True)
    skill_md.write_text("---\nmetadata:\n  generatedBy: \"0.0.1\"\n---\n", encoding="utf-8")
    assert world.run() == 0
    assert warnings(capsys.readouterr().out) == []


def test_the_local_cli_is_asked_quietly(monkeypatch):
    seen = []

    def run(argv, **kwargs):
        seen.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, stdout="1.13.1\n", stderr="")

    monkeypatch.setattr(openspec_currency.shutil, "which", lambda _name: "/usr/bin/openspec")
    monkeypatch.setattr(openspec_currency.subprocess, "run", run)
    assert REAL_LOCAL_CLI() == "1.13.1"
    (argv, kwargs), = seen
    assert argv == ["/usr/bin/openspec", "--version"]
    assert kwargs["env"]["OPENSPEC_TELEMETRY"] == "0"
    assert kwargs["env"]["OPENSPEC_NO_UPDATE_CHECK"] == "1"


@pytest.mark.parametrize(("which", "result"), [
    (None, None),
    ("/usr/bin/openspec", subprocess.CompletedProcess([], 1, stdout="", stderr="boom")),
    ("/usr/bin/openspec", subprocess.CompletedProcess([], 0, stdout="openspec\n", stderr="")),
    ("/usr/bin/openspec", OSError("exec format error")),
])
def test_a_local_cli_that_gives_no_version_reads_as_absent(monkeypatch, which, result):
    def run(*_a, **_k):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(openspec_currency.shutil, "which", lambda _name: which)
    monkeypatch.setattr(openspec_currency.subprocess, "run", run)
    assert REAL_LOCAL_CLI() is None


# ---------- what the workflow reads ------------------------------------------------------


def test_the_json_report_carries_what_the_workflow_checks(world, capsys):
    world.local = None
    world.answer = {"name": validate_specs.PACKAGE, "version": bumped(PIN)}
    assert world.run("--json", "--write") == 1
    report = json.loads(capsys.readouterr().out)
    assert isinstance(report["status"], str)
    assert isinstance(report["warnings"], list)
    assert report["status"] == "behind"
    assert report["pin"] == PIN
    assert report["latest"] == bumped(PIN)
    assert report["written"] is True
    assert report["local_cli"] is None
    assert report["skills_stamps"] == {"openspec-apply-change": PIN, "openspec-propose": PIN}
    assert report["source"] == openspec_currency.REGISTRY_URL


def test_the_pr_body_names_the_bump_and_the_maintainers_steps(world, tmp_path):
    newer = bumped(PIN)
    world.answer = {"name": validate_specs.PACKAGE, "version": newer}
    body_path = tmp_path / "body.md"
    world.run("--write", "--pr-body", str(body_path))
    body = body_path.read_text(encoding="utf-8")
    for needle in (f"`{PIN}`", f"`{newer}`", openspec_currency.RELEASES_URL, "uv run poe specs",
                   "openspec/long-requirements.json", "openspec update",
                   "still waits for approval"):
        assert needle in body, needle


# ---------- the "plain python3" property and L0's offline guard ---------------------------


@pytest.mark.parametrize("script", ["openspec_currency.py", "validate_specs.py"])
def test_the_checker_imports_only_the_standard_library(script):
    """The weekly workflow runs the check with plain python3, outside the uv
    environment, and the check imports the gate's module for its pin."""
    tree = ast.parse((REPO / "scripts" / script).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module.split(".")[0])
    allowed = set(sys.stdlib_module_names) | {"validate_specs"}
    assert imported <= allowed, f"{script}: non-stdlib imports {sorted(imported - allowed)}"


def test_the_registry_fetch_is_refused_inside_l0(world):
    """What this file's world replaced: the suite-wide guard, so a test
    elsewhere that reaches the check reads "unknown" instead of npm."""
    with pytest.raises(OSError, match="network disabled in L0 tests"):
        world.guard(openspec_currency.REGISTRY_URL, 1.0)
