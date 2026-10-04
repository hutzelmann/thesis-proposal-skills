"""L0: the install-prompt probe's verdicts and staging (testing-harness spec:
Install prompt probed on the dev runner). No model call: the verdicts run on
synthetic outcomes, and the staging is checked against the real prompt and
installer, so a reworded prompt or a moved URL fails here rather than in a
subscription run.
"""

from __future__ import annotations

import zipfile

import claude_runner
import pytest
from helpers import REPO
from l1_checks import verdict_install_prompt_asks_scope, verdict_install_prompt_installed

import install

ASKED = ("Python 3.12 is installed. Install for all your projects (recommended), "
         "or only for this folder?")
SKILLS = {"proposal-a": {"SKILL.md": b"a"}, "proposal-b": {"SKILL.md": b"b", "x.py": b"1"}}
RECORD = {"revision": "1" * 40}
RECORDINGS = REPO / "tests" / "unit" / "data" / "install_probe"


# ---------- unanswered run --------------------------------------------------------


def test_asked_and_nothing_installed_passes():
    passed, why = verdict_install_prompt_asks_scope(ASKED, [])
    assert passed, why


def test_reworded_question_still_counts():
    assert verdict_install_prompt_asks_scope(
        "Should I install it for all projects, or just the current folder?", [])[0]


def test_no_question_fails():
    passed, why = verdict_install_prompt_asks_scope("Installed everything for you.", [])
    assert not passed
    assert "scope question" in why


def test_installing_before_the_answer_fails():
    passed, why = verdict_install_prompt_asks_scope(ASKED, ["/h/.claude/skills/proposal-a"])
    assert not passed
    assert "installed before the answer" in why


# ---------- answered run ----------------------------------------------------------


def targets(**override):
    found = {".agents/skills": SKILLS, ".claude/skills": SKILLS}
    return {**found, **override}


def test_full_byte_identical_install_with_records_passes():
    passed, why = verdict_install_prompt_installed(
        SKILLS, targets(), {".agents/skills": RECORD, ".claude/skills": RECORD}, [])
    assert passed, why


def test_missing_skill_fails():
    passed, why = verdict_install_prompt_installed(
        SKILLS, targets(**{".claude/skills": {"proposal-a": SKILLS["proposal-a"]}}),
        {".agents/skills": RECORD, ".claude/skills": RECORD}, [])
    assert not passed
    assert ".claude/skills: skills" in why


def test_hand_edited_copy_fails():
    edited = {**SKILLS, "proposal-b": {"SKILL.md": b"b rewritten", "x.py": b"1"}}
    passed, why = verdict_install_prompt_installed(
        SKILLS, targets(**{".agents/skills": edited}),
        {".agents/skills": RECORD, ".claude/skills": RECORD}, [])
    assert not passed
    assert "differ" in why


def test_missing_record_fails():
    passed, why = verdict_install_prompt_installed(
        SKILLS, targets(), {".agents/skills": RECORD, ".claude/skills": None}, [])
    assert not passed
    assert "no install record" in why


def test_copy_outside_the_targets_fails():
    passed, why = verdict_install_prompt_installed(
        SKILLS, targets(), {".agents/skills": RECORD, ".claude/skills": RECORD},
        ["/h/.codex/skills/proposal-a"])
    assert not passed
    assert "outside the installer's targets" in why


# ---------- staging ----------------------------------------------------------------


def test_request_is_the_shared_prompt_pointed_at_the_local_installer():
    request = claude_runner.install_request("http://127.0.0.1:9", answered=False)
    assert "http://127.0.0.1:9/install.py" in request
    assert claude_runner.RAW_INSTALLER_URL not in request
    assert claude_runner.ANSWER not in request
    assert claude_runner.install_request("http://x", answered=True).endswith(claude_runner.ANSWER)


def test_served_installer_points_at_the_local_archive(tmp_path):
    claude_runner.stage_install_source(tmp_path, "http://127.0.0.1:9")
    served = (tmp_path / "install.py").read_text(encoding="utf-8")
    assert "http://127.0.0.1:9/main.zip" in served
    assert claude_runner.DEFAULT_ARCHIVE_URL not in served
    assert claude_runner.DEFAULT_ARCHIVE_URL == install.DEFAULT_SOURCE
    with zipfile.ZipFile(tmp_path / "main.zip") as archive:
        assert archive.comment.decode() == claude_runner.PROBE_REVISION
        names = archive.namelist()
    assert "thesis-proposal-skills-main/skills/proposal-check/SKILL.md" in names


def test_targets_are_the_installers_all_projects_directories():
    assert claude_runner.INSTALL_TARGETS == install.SHARED_DIRS


# ---------- recorded outcomes and the glue that reads a real home -----------


def test_recorded_unanswered_runs_pass():
    """The final messages of the 2026-10-03 subscription runs (tasks.md notes)."""
    for name in ("sonnet-unanswered.txt", "haiku-unanswered.txt"):
        chat = (RECORDINGS / name).read_text(encoding="utf-8")
        passed, why = verdict_install_prompt_asks_scope(chat, [])
        assert passed, f"{name}: {why}"


def test_a_recorded_install_report_is_no_scope_question():
    chat = (RECORDINGS / "sonnet-answered.txt").read_text(encoding="utf-8")
    assert not verdict_install_prompt_asks_scope(chat, [])[0]


@pytest.fixture
def installed_home(tmp_path, monkeypatch):
    """A home the real installer filled from the probe's own staged archive."""
    served, home, ws = tmp_path / "served", tmp_path / "home", tmp_path / "ws"
    for d in (served, home, ws):
        d.mkdir()
    claude_runner.stage_install_source(served, "http://unused")
    for var in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(var, str(home))
    monkeypatch.setenv("APPDATA", str(home / "AppData"))
    monkeypatch.chdir(ws)
    assert install.main(["--scope", "all", "--source", str(served / "main.zip")]) == 0
    return home, ws


# the glue reads skills/ twice, and test_sync.py's tamper cases rewrite files there
@pytest.mark.xdist_group("sync_shared_tree")
def test_a_home_the_installer_filled_passes(installed_home):
    home, ws = installed_home
    passed, why = claude_runner.install_probe_verdict(True, home, ws, "")
    assert passed, why


@pytest.mark.xdist_group("sync_shared_tree")
def test_a_hand_copied_skill_fails(installed_home):
    home, ws = installed_home
    stray = home / ".codex" / "skills" / "proposal-check"
    stray.mkdir(parents=True)
    (stray / "SKILL.md").write_text("copied by hand", encoding="utf-8")
    passed, why = claude_runner.install_probe_verdict(True, home, ws, "")
    assert not passed
    assert "outside the installer's targets" in why


@pytest.mark.xdist_group("sync_shared_tree")
def test_an_unanswered_run_that_installed_fails(installed_home):
    home, ws = installed_home
    passed, why = claude_runner.install_probe_verdict(
        False, home, ws, (RECORDINGS / "sonnet-unanswered.txt").read_text(encoding="utf-8"))
    assert not passed
    assert "installed before the answer" in why
