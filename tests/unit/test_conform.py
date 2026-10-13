"""`scripts/conform.py`: the canary is the standard's own validator, pinned.

standard-conformance spec, "External conformance validator as a canary": the
reference validator is the one the standard's maintainers publish in the
standard's repository, pinned by an identifier that cannot move, with the
dependencies that decide what it accepts pinned beside it. Until 2026-10-13
the pin named `skills-ref` on npm, an unrelated third-party port. These tests
start no validator; `poe conform` is where it runs.
"""

import re
import subprocess
from pathlib import Path

import conform
import pytest
from helpers import REPO, tracked_files

REFERENCE = "https://github.com/agentskills/agentskills"
# assembled, so this file does not match its own scan
NPM_SPELLINGS = ("skills-ref" + "@", "npx -y " + "skills-ref")


def option_values(argv: list[str], option: str) -> list[str]:
    return [argv[i + 1] for i, arg in enumerate(argv) if arg == option]


def test_the_pin_is_a_full_commit_id():
    assert re.fullmatch(r"[0-9a-f]{40}", conform.SKILLS_REF_COMMIT), conform.SKILLS_REF_COMMIT


def test_the_validator_comes_from_the_standards_own_repository():
    argv = conform.command(Path("skills/proposal-check"))
    assert option_values(argv, "--from") == [
        f"git+{REFERENCE}@{conform.SKILLS_REF_COMMIT}#subdirectory=skills-ref"
    ]
    assert argv[-3:] == ["skills-ref", "validate", str(Path("skills/proposal-check"))]
    assert "npx" not in " ".join(argv)


def test_every_deciding_dependency_is_pinned_exactly():
    pins = option_values(conform.command(Path("x")), "--with")
    assert {pin.split("==")[0] for pin in pins} == {"strictyaml", "click"}
    for pin in pins:
        assert re.fullmatch(r"[a-z0-9_.-]+==\d[\w.+-]*", pin), pin


def completed(returncode: int, out: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], returncode, stdout=out, stderr="")


@pytest.fixture
def validator(monkeypatch):
    """A stand-in for uvx: records each call and fails the skills named in
    `failing`, the way the real validator reports a violation."""
    calls: list[tuple[list[str], dict]] = []
    failing: set[str] = set()

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        name = Path(argv[-1]).name
        if name in failing:
            return completed(1, f"Validation failed for {argv[-1]}:\n  - something")
        return completed(0, f"Valid skill: {argv[-1]}")

    monkeypatch.setattr(conform.shutil, "which", lambda _name: "/opt/uv/bin/uvx")
    monkeypatch.setattr(conform.subprocess, "run", run)
    return calls, failing


def test_every_skill_is_validated_and_a_clean_run_names_the_pin(validator, capsys):
    calls, _ = validator
    assert conform.main([]) == 0
    validated = sorted(Path(argv[-1]).name for argv, _ in calls)
    assert validated == sorted(d.name for d in (REPO / "skills").glob("proposal-*") if d.is_dir())
    assert all(argv[0] == "/opt/uv/bin/uvx" for argv, _ in calls)
    assert conform.SKILLS_REF_COMMIT[:7] in capsys.readouterr().out


def test_the_validator_reads_files_as_utf8(validator):
    """The reference reads SKILL.md with the locale codec; on Windows that is
    cp1252, where an em dash counts three characters toward the limits."""
    calls, _ = validator
    conform.main([])
    assert calls
    assert all(kwargs["env"]["PYTHONUTF8"] == "1" for _, kwargs in calls)


def test_a_failing_skill_fails_the_run_and_is_named(validator, capsys):
    _, failing = validator
    failing.add("proposal-review")
    assert conform.main([]) == 1
    assert "proposal-review" in capsys.readouterr().out.splitlines()[-1]


def test_missing_uvx_is_reported_with_install_guidance(monkeypatch, capsys):
    monkeypatch.setattr(conform.shutil, "which", lambda _name: None)
    monkeypatch.setattr(conform.subprocess, "run",
                        lambda *_a, **_k: pytest.fail("no validator may start without uvx"))
    assert conform.main([]) == 2
    assert "https://docs.astral.sh/uv/" in capsys.readouterr().err


def test_no_tracked_file_runs_the_npm_port():
    """Change folders keep the history of the switch; everything else must not
    name the port as the thing to run."""
    offenders = []
    for rel in tracked_files():
        if rel.startswith("openspec/changes/") or rel == "tests/unit/test_conform.py":
            continue
        try:
            text = (REPO / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        offenders.extend(f"{rel}: {s}" for s in NPM_SPELLINGS if s in text)
    assert not offenders, "\n".join(offenders)
