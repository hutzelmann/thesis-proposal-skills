"""L0: the install-prompt probe's verdicts, staging and plumbing (testing-harness
spec: Install prompt probed on the dev runner). No model call: the verdicts run
on synthetic outcomes, the staging is checked against the real prompt and
installer, so a reworded prompt or a moved URL fails here rather than in a
subscription run, and `main` runs with the host and the isolation faked, so the
child's environment and the summary line are pinned without a model.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from urllib.parse import urlsplit

import claude_runner
import pytest
from claude_cli import parse_events
from claude_runner import (
    EXIT_FAIL,
    EXIT_PASS,
    EXIT_RUNNER,
    EXIT_UNTESTED,
    OUTCOMES,
    RunnerFailure,
    main,
)
from helpers import REPO, followed
from l1_checks import (
    verdict_install_prompt_asks_scope,
    verdict_install_prompt_found_python,
    verdict_install_prompt_installed,
)

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


def test_a_prompt_that_no_longer_names_the_installer_is_a_runner_failure(monkeypatch):
    monkeypatch.setattr(claude_runner, "RAW_INSTALLER_URL", "https://moved.invalid/install.py")
    with pytest.raises(RunnerFailure, match="install prompt no longer names") as failure:
        claude_runner.install_request("http://x", answered=False)
    assert failure.value.status == EXIT_RUNNER


def test_an_installer_that_no_longer_names_the_archive_is_a_runner_failure(monkeypatch,
                                                                           tmp_path):
    monkeypatch.setattr(claude_runner, "DEFAULT_ARCHIVE_URL", "https://moved.invalid/main.zip")
    with pytest.raises(RunnerFailure, match=r"install\.py no longer names") as failure:
        claude_runner.stage_install_source(tmp_path, "http://x")
    assert failure.value.status == EXIT_RUNNER
    assert not list(tmp_path.iterdir())  # refused before anything was staged


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


# ---------- main(argv): the run's plumbing, host and isolation faked ------------
#
# The assertions read the environment the host was handed, never how it was
# built: whatever model_env starts from, the probe's HOME, USERPROFILE and
# isolated config must be what the child finally sees.

BILLING = {"ANTHROPIC_API_KEY": "placeholder-not-a-key",
           "ANTHROPIC_BASE_URL": "https://gateway.invalid",
           "CLAUDE_CODE_USE_BEDROCK": "1", "CLAUDE_CODE_USE_VERTEX": "1"}
LOCAL_INSTALLER = re.compile(r"http://127\.0\.0\.1:\d+/install\.py")


def fetch(url: str) -> str:
    """GET from the probe's local server directly, past any proxy the
    environment configures."""
    parts = urlsplit(url)
    connection = HTTPConnection(parts.hostname, parts.port, timeout=5)
    try:
        connection.request("GET", parts.path)
        return connection.getresponse().read().decode("utf-8")
    finally:
        connection.close()


def host_stdout(text: str, overage: bool = False) -> str:
    """A finished host run in the stream-json shape the dev runner reads."""
    model = "claude-fixture-1-0"
    events = [
        {"type": "system", "subtype": "init", "model": model, "apiKeySource": "none",
         "claude_code_version": "2.1.284"},
        {"type": "rate_limit_event", "rate_limit_info": {
            "status": "allowed", "rateLimitType": "five_hour", "utilization": 0.2,
            "isUsingOverage": overage}},
        {"type": "result", "subtype": "success", "is_error": False, "result": text,
         "total_cost_usd": 0.1, "num_turns": 4, "duration_ms": 9000,
         "usage": {"input_tokens": 10, "output_tokens": 80},
         "modelUsage": {model: {"outputTokens": 80, "provider": "firstParty"}}},
    ]
    return "".join(json.dumps(e) + "\n" for e in events)


@pytest.fixture
def probe(monkeypatch, tmp_path):
    """`main` up to the host: a launching environment that carries the
    operator's HOME and billing variables, a plain directory for the isolated
    config, temp directories under `tmp_path`, and a host that records what it
    was handed — including the installer the local server serves at the URL
    the request names. Set `stdout` or `raises` to choose how the host ends."""
    config, temp = tmp_path / "isolated-config", tmp_path / "tmp"
    config.mkdir()
    temp.mkdir()
    operator = tmp_path / "operator"
    for name, value in {**BILLING, "HOME": str(operator), "USERPROFILE": str(operator),
                        "CLAUDE_CONFIG_DIR": str(operator / ".claude")}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(tempfile, "tempdir", str(temp))
    # a tiny archive: these tests pin plumbing, and skills/ is rewritten by test_sync
    monkeypatch.setattr(claude_runner, "working_tree_skills", lambda: SKILLS)

    @contextmanager
    def fake_isolated_config(_prefix):
        yield config

    monkeypatch.setattr(claude_runner, "isolated_config", fake_isolated_config)
    host = {"config": config, "temp": temp, "calls": [], "stdout": host_stdout(ASKED),
            "timed_out": False}

    def follow(command, **kwargs):
        request = command[2]
        url = LOCAL_INSTALLER.search(request).group(0)
        host["calls"].append({"request": request, "url": url,
                              "served": fetch(url), "cwd": kwargs["cwd"], "env": kwargs["env"],
                              "home_empty": not any(Path(kwargs["env"]["HOME"]).iterdir())})
        return followed(parse_events(host["stdout"]), kwargs["stop"],
                        timed_out=host["timed_out"])

    monkeypatch.setattr(claude_runner, "follow_stream", follow)
    return host


def logged(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_the_host_runs_in_the_probe_home_under_the_isolated_config(probe, tmp_path):
    log = tmp_path / "log.jsonl"
    assert main(["install_prompt", "--summary-log", str(log)]) == EXIT_PASS
    [call] = probe["calls"]
    env, ws = call["env"], Path(call["cwd"])
    home = ws.parent / "home"
    assert ws.parent.parent == probe["temp"]
    assert env["HOME"] == env["USERPROFILE"] == str(home)
    assert call["home_empty"]
    assert env["CLAUDE_CONFIG_DIR"] == str(probe["config"])
    assert not [k for k in env if k.startswith("CLAUDE_CODE_USE_")]
    # the only `ANTHROPIC_` name is the empty profile directory the harness sets
    assert [k for k in env if k.startswith("ANTHROPIC_")] == ["ANTHROPIC_CONFIG_DIR"]
    assert env["ANTHROPIC_CONFIG_DIR"] == str(probe["config"] / "anthropic-empty")
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    # the request names the local installer, which points at the local archive
    assert claude_runner.RAW_INSTALLER_URL not in call["request"]
    assert claude_runner.ANSWER not in call["request"]
    assert call["url"].replace("/install.py", "/main.zip") in call["served"]
    assert claude_runner.DEFAULT_ARCHIVE_URL not in call["served"]
    [line] = logged(log)
    assert (line["outcome"], line["exit_status"]) == ("PASS", EXIT_PASS)
    assert (line["config"], line["config_dir"]) == ("isolated", str(probe["config"]))
    assert not list(probe["temp"].iterdir())  # the probe directory is removed


def test_the_answered_variant_appends_the_answer(probe, tmp_path):
    probe["stdout"] = host_stdout("Installed.")
    main(["install_prompt_answered", "--summary-log", str(tmp_path / "log.jsonl")])
    [call] = probe["calls"]
    assert call["request"].endswith(claude_runner.ANSWER)


@pytest.mark.parametrize(("scenario", "stdout", "timed_out", "status"), [
    ("install_prompt", host_stdout(ASKED), False, EXIT_PASS),
    ("install_prompt", host_stdout("Installed everything for you."), False, EXIT_FAIL),
    # nothing landed in the probe home, so the answered verdict fails
    ("install_prompt_answered", host_stdout("Installed."), False, EXIT_FAIL),
    ("install_prompt", host_stdout(ASKED, overage=True), False, EXIT_UNTESTED),
    ("install_prompt", "", True, EXIT_RUNNER),
])
def test_each_outcome_exits_with_its_status_and_logs_one_line(
        scenario, stdout, timed_out, status, probe, tmp_path):
    probe["stdout"], probe["timed_out"] = stdout, timed_out
    log = tmp_path / "log.jsonl"
    assert main([scenario, "--summary-log", str(log)]) == status
    [line] = logged(log)
    assert (line["outcome"], line["exit_status"]) == (OUTCOMES[status], status)
    assert line["config"] == "isolated"


def test_a_refused_isolation_is_untested_and_never_runs_the_host(probe, monkeypatch, tmp_path):
    @contextmanager
    def refusing_isolated_config(_prefix):
        raise SystemExit("no stored login to link")
        yield  # a generator, as the real context manager is

    monkeypatch.setattr(claude_runner, "isolated_config", refusing_isolated_config)
    log = tmp_path / "log.jsonl"
    assert main(["install_prompt", "--summary-log", str(log)]) == EXIT_UNTESTED
    assert probe["calls"] == []
    [line] = logged(log)
    assert (line["outcome"], line["why"]) == ("UNTESTED", "no stored login to link")
    assert (line["config"], line["config_dir"]) == ("isolated", None)
    # the probe always isolates: the login it would have linked, never "ambient"
    assert (line["login"], line["login_dir"]) == ("harness", None)


def test_a_drifted_prompt_is_a_runner_failure_with_its_line(probe, monkeypatch, tmp_path):
    monkeypatch.setattr(claude_runner, "RAW_INSTALLER_URL", "https://moved.invalid/install.py")
    log = tmp_path / "log.jsonl"
    assert main(["install_prompt", "--summary-log", str(log)]) == EXIT_RUNNER
    assert probe["calls"] == []
    [line] = logged(log)
    assert line["outcome"] == "RUNNER FAILURE"
    assert "install prompt no longer names" in line["why"]
    assert line["config"] == "isolated"


def test_a_crash_is_a_runner_failure_with_its_line(probe, monkeypatch, tmp_path, capsys):
    def crash(*_args):
        raise RuntimeError("verdict crashed")

    monkeypatch.setattr(claude_runner, "install_probe_verdict", crash)
    log = tmp_path / "log.jsonl"
    assert main(["install_prompt", "--summary-log", str(log)]) == EXIT_RUNNER
    assert len(probe["calls"]) == 1
    [line] = logged(log)
    assert (line["outcome"], line["exit_status"]) == ("RUNNER FAILURE", EXIT_RUNNER)
    assert line["why"] == "runner crashed: RuntimeError('verdict crashed')"
    assert line["config"] == "isolated"
    assert "Traceback" in capsys.readouterr().err


# ---------- the versioned-interpreter variant (design D10, D12) ----------------

INSTALLED = (True, "11 skills byte-identical with a record in 2 directories, no stray copies")


def test_found_python_passes_when_installed_without_install_advice():
    passed, why = verdict_install_prompt_found_python(
        INSTALLED, "Found Python 3.13 as python3.13 and installed the skills for all your "
                   "projects. No need to install Python. Start a new chat to use them.")
    assert passed, why


@pytest.mark.parametrize("chat", [
    "No Python 3.11 was found. Install it from python.org, then tell me.",
    "Please install Python with the Python install manager from the Microsoft Store.",
    "You need to install a newer Python first: sudo apt install python3.12",
    "I could not find Python. Install Python, then run Install Certificates.command.",
])
def test_found_python_fails_when_the_student_is_sent_to_install_python(chat):
    passed, why = verdict_install_prompt_found_python(INSTALLED, chat)
    assert not passed
    assert "install Python" in why


def test_found_python_fails_on_an_incomplete_install():
    passed, why = verdict_install_prompt_found_python(
        (False, ".agents/skills: no install record"), "Installed with python3.13.")
    assert not passed
    assert why.startswith("install incomplete: .agents/skills")


def executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\n", encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.mark.skipif(sys.platform == "win32", reason="the variant is Linux only")
def test_the_path_builder_leaves_no_python_name_but_the_versioned_one(tmp_path):
    first, second = tmp_path / "usr-bin", tmp_path / "local-bin"
    hidden = ["python", "python3", "python3.12", "python3.12-config", "python3-config",
              "pythonw", "pip", "pip3", "pip3.12", "pydoc3", "py", "uv", "uvx"]
    for name in [*hidden, "ls", "node", "claude"]:
        executable(first / name)
    executable(second / "python3.13")
    executable(second / "ls")  # a later folder's duplicate: the first one wins
    (first / "notes.txt").write_text("not executable", encoding="utf-8")
    interpreter = executable(tmp_path / "real" / "python3.14")
    path = claude_runner.versioned_python_path(
        tmp_path / "bin", os.pathsep.join([str(first), "", str(second), str(tmp_path / "gone")]),
        interpreter, (3, 14))
    assert path == str(tmp_path / "bin")
    names = sorted(p.name for p in (tmp_path / "bin").iterdir())
    assert names == ["claude", "ls", "node", "python3.14"]
    assert [n for n in names if claude_runner.HIDDEN_PYTHON_RE.match(n)] == ["python3.14"]
    assert (tmp_path / "bin" / "python3.14").resolve() == interpreter.resolve()
    assert (tmp_path / "bin" / "ls").resolve() == (first / "ls").resolve()


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="the variant is Linux only")
def test_the_versioned_variant_hands_the_host_the_scratch_path(probe, tmp_path):
    probe["stdout"] = host_stdout("Installed.")
    log = tmp_path / "log.jsonl"
    # nothing landed in the probe home, so the verdict fails; the PATH is what is pinned
    assert main(["install_prompt_versioned_python", "--summary-log", str(log)]) == EXIT_FAIL
    [call] = probe["calls"]
    assert call["request"].endswith(claude_runner.ANSWER)
    folder = Path(call["env"]["PATH"])
    assert folder.name == "bin"
    assert folder.parent == Path(call["cwd"]).parent
    [line] = logged(log)
    assert "install incomplete" in line["why"]
