"""L0: the dev runner's host seam (`harness/hosts.py`, `claude_runner.HOSTS`;
testing-harness spec: Dev-runner host adapters, Subscription text roles).

The Codex host is driven end to end with `codex_cli.run_codex` replaced by a
fake that returns a synthetic saved event list (`data/codex_streams/`), and its
preflight stubbed: no test starts `codex`, and no test needs a ChatGPT login.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import claude_cli
import claude_runner
import codex_cli
import host_login
import pytest
from claude_cli import Grade, JudgeCall, JudgeRun, RateLimit
from claude_runner import (
    EVENTS_FILE,
    EXIT_RUNNER,
    EXIT_UNTESTED,
    EXIT_USAGE,
    HOSTS,
    SCENARIOS,
    main,
    save_events,
    stage,
    summary,
)
from helpers import FIXTURES, REPO
from host_login import CLAUDE, CODEX, CREDENTIALS, STATE_VAR, LoginProblem, refusal

STREAMS = Path(__file__).resolve().parent / "data" / "codex_streams"
CLAUDE_STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"
CLEAN_DRAFT = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text(encoding="utf-8")
LABEL = "dev-runner (codex), not comparable to matrix"


def stream(name: str, ws: Path) -> list[dict]:
    text = (STREAMS / f"{name}.jsonl").read_text(encoding="utf-8").replace("__WS__", str(ws))
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def logged(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def refuse_staging(monkeypatch):
    def no_workspace(*_args, **_kwargs):
        raise AssertionError("staged before the usage error")

    monkeypatch.setattr(claude_runner.tempfile, "mkdtemp", no_workspace)


def no_codex(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("a Codex process was started")

    for name in ("run_codex", "spawn", "run", "probe", "read_quota"):
        monkeypatch.setattr(codex_cli, name, refuse)


@pytest.fixture
def codex_home(tmp_path, monkeypatch):
    """A seeded Codex harness home under a state root in `tmp_path`; the
    preflight that would run the client is stubbed."""
    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    monkeypatch.setattr(host_login, "system_tempdir", lambda: str(tmp_path / "system-tmp"))
    home = host_login.home(CODEX)
    host_login.seed(CODEX, home)
    monkeypatch.setattr(codex_cli, "preflight", lambda _environ=None: None)
    return home


def fake_codex_run(monkeypatch, name="success", produce=None, raises=None) -> list[dict]:
    runs: list[dict] = []

    def run_codex(ws, request, **kwargs):
        skills = ws / ".agents" / "skills"
        runs.append({"ws": ws, "request": request, **kwargs,
                     "staged": sorted(p.name for p in skills.iterdir()) if skills.is_dir()
                     else []})
        if raises is not None:
            raise raises
        if produce:
            produce(ws)
        return stream(name, ws)

    monkeypatch.setattr(codex_cli, "run_codex", run_codex)
    return runs


def write_draft(ws: Path) -> None:
    (ws / "drift-detection-proposal.md").write_text(CLEAN_DRAFT, encoding="utf-8")


# ---------- the default host -----------------------------------------------------------


def test_the_hosts_are_claude_and_codex():
    assert set(HOSTS) == {"claude", "codex"}
    assert HOSTS["claude"].skill_dir == (".claude", "skills")
    assert HOSTS["codex"].skill_dir == (".agents", "skills")
    assert HOSTS["claude"].login is CLAUDE
    assert HOSTS["codex"].login is CODEX
    assert claude_runner.host_for(argparse.Namespace()) is HOSTS["claude"]


def test_a_run_without_a_host_is_labelled_claude():
    """testing-harness spec: Claude stays the default host."""
    events = [json.loads(line) for line in (CLAUDE_STREAMS / "recorded-result.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    args = argparse.Namespace(scenario="check_report", model="haiku", no_skill=False)
    out = summary(args, True, "fine", events, None)
    assert out["host"] == "claude"
    assert out["label"] == "dev-runner (claude), not comparable to matrix"
    assert out["config"] == "ambient"


# ---------- usage errors ---------------------------------------------------------------

CODEX_RUN = ["check_report", "--host", "codex", "--model", "gpt-fixture-a"]


@pytest.mark.parametrize(("argv", "named"), [
    (["check_report", "--host", "codex"], "--model"),
    (["check_report", "--host", "codex", "--model", "openai/gpt-fixture-a"], "provider"),
    ([*CODEX_RUN, "--max-budget-usd", "1"], "budget cap"),
    (["install_prompt", "--host", "codex", "--model", "gpt-fixture-a"], "install"),
    (["check_report", "--effort", "high"], "--effort"),
    ([*CODEX_RUN, "--effort", "ultra"], "ultra"),
])
def test_codex_usage_errors_stage_nothing_and_start_nothing(argv, named, monkeypatch, capsys):
    """testing-harness spec: Codex run without a model; Install scenario on Codex;
    Budget cap refused on Codex."""
    refuse_staging(monkeypatch)
    no_codex(monkeypatch)
    with pytest.raises(SystemExit) as usage:
        main(argv)
    assert usage.value.code == EXIT_USAGE
    assert named in capsys.readouterr().err


@pytest.mark.parametrize("host", sorted(HOSTS))
@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
def test_a_summary_log_where_the_support_report_reads_is_refused(host, relative, monkeypatch,
                                                                capsys):
    """testing-harness spec: Summary log where the support report reads."""
    refuse_staging(monkeypatch)
    no_codex(monkeypatch)
    monkeypatch.chdir(REPO)
    target = Path("logs/evals/x.jsonl") if relative else REPO / "logs" / "evals" / "x.jsonl"
    argv = ["check_report", "--host", host, "--model",
            "gpt-fixture-a" if host == "codex" else "haiku", "--summary-log", str(target)]
    with pytest.raises(SystemExit) as usage:
        main(argv)
    assert usage.value.code == EXIT_USAGE
    assert "logs/evals" in capsys.readouterr().err
    assert not (REPO / "logs" / "evals" / "x.jsonl").exists()


# ---------- staging ----------------------------------------------------------------------


def test_codex_stages_the_skill_where_codex_discovers_it(tmp_path):
    """testing-harness spec: Codex skill staged where Codex discovers it; Codex dev
    run stages a skill."""
    stage(SCENARIOS["supervise_scope"], tmp_path, skill_dir=(".agents", "skills"))
    root = tmp_path / ".agents" / "skills"
    assert sorted(p.name for p in root.iterdir()) == [
        "proposal-import", "proposal-lit-search", "proposal-supervise"]
    assert (root / "proposal-supervise" / "SKILL.md").is_file()
    assert not list(root.rglob("evals"))
    assert not (tmp_path / ".claude").exists()


# ---------- end to end on Codex ---------------------------------------------------------


def test_a_codex_run_is_summarized_and_labelled(codex_home, tmp_path, monkeypatch):
    """testing-harness spec: Codex dev run labelled by host; Codex run reports no cost."""
    runs = fake_codex_run(monkeypatch)
    log = tmp_path / "log.jsonl"
    main([*CODEX_RUN, "--summary-log", str(log)])
    [line] = logged(log)
    assert (line["host"], line["label"]) == ("codex", LABEL)
    assert (line["config"], line["config_dir"]) == ("isolated", str(codex_home))
    assert (line["login"], line["login_dir"]) == ("harness", str(codex_home))
    assert line["cost_usd"] is None
    assert line["notional_basis"] == "unpriced"
    assert (line["model_requested"], line["model"], line["cli_version"]) == (
        "gpt-fixture-a", "unreported", "0.160.0")
    assert line["quota_before"]["primary"]["used_percent"] == 12.0
    assert line["quota_after"]["primary"]["used_percent"] == 14.0
    [run] = runs
    assert run["home"] == codex_home
    assert run["model"] == "gpt-fixture-a"
    assert run["staged"] == ["proposal-check"]
    assert run["scenario"] is SCENARIOS["check_report"]
    assert "outcome" in line


@pytest.mark.usefixtures("codex_home")
def test_the_isolated_flag_is_implied_on_codex(tmp_path, monkeypatch):
    fake_codex_run(monkeypatch)
    log = tmp_path / "log.jsonl"
    main([*CODEX_RUN, "--isolated", "--summary-log", str(log)])
    assert logged(log)[0]["config"] == "isolated"


@pytest.mark.parametrize(("raises", "stream_name", "effort", "named"), [
    (host_login.RunLockBusy(LoginProblem(
        "another Codex run holds the harness home (/fake/codex/.harness-run.lock)",
        "rerun after it ends", "codex")), None, None, ".harness-run.lock"),
    (codex_cli.CodexRefused(refusal(codex_cli.features_problem(
        (STREAMS / "features-extra-on.txt").read_text(encoding="utf-8"),
        codex_cli.ALLOWED_FEATURES)), "precondition"), None, None, "realtime_conversation"),
    (None, "effort-dropped", "xhigh", "xhigh"),
])
@pytest.mark.usefixtures("codex_home")
def test_a_codex_precondition_is_untested_not_a_runner_failure(raises, stream_name, effort,
                                                              named, tmp_path, monkeypatch):
    """testing-harness spec: Codex precondition is untested, not a runner failure."""
    fake_codex_run(monkeypatch, name=stream_name or "success", raises=raises)
    log = tmp_path / "log.jsonl"
    argv = [*CODEX_RUN, "--summary-log", str(log), *(["--effort", effort] if effort else [])]
    assert main(argv) == EXIT_UNTESTED
    [line] = logged(log)
    assert line["exit_status"] == EXIT_UNTESTED != EXIT_RUNNER
    assert named in line["why"]
    if stream_name:
        assert "medium" in line["why"]


@pytest.mark.usefixtures("codex_home")
def test_a_codex_billing_refusal_is_untested_and_records_billing(tmp_path, monkeypatch):
    fake_codex_run(monkeypatch, name="credits-drawn")
    log = tmp_path / "log.jsonl"
    assert main([*CODEX_RUN, "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert "credits" in line["billing"]
    assert "Empty the Codex credit balance" in line["why"]


def test_a_codex_preflight_refusal_is_untested_and_starts_no_run(tmp_path, monkeypatch):
    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    monkeypatch.setattr(host_login, "system_tempdir", lambda: str(tmp_path / "system-tmp"))
    problem = LoginProblem("the installed Codex CLI is 0.133.0, older than the pinned minimum "
                           "0.160.0", "update the Codex CLI through your package manager",
                           "codex")
    monkeypatch.setattr(codex_cli, "preflight", lambda _environ=None: problem)
    no_codex(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main([*CODEX_RUN, "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert line["why"] == refusal(problem)
    assert (line["host"], line["config"], line["login"]) == ("codex", "isolated", "harness")


def test_the_default_codex_preflight_refuses_a_home_in_the_temporary_directory(tmp_path,
                                                                             monkeypatch):
    """testing-harness spec: Codex home in the temporary directory — the real
    preflight, with the state root under the real temporary directory."""
    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    no_codex(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main([*CODEX_RUN, "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert "temporary directory" in line["why"]
    assert not (tmp_path / "state").exists()


# ---------- the judge's isolation belongs to the judge (the L0 pin) -----------------------


@pytest.fixture
def claude_home(tmp_path, monkeypatch):
    """The Claude harness home with a placeholder login, its preflight stubbed."""
    home = host_login.home(CLAUDE)
    home.mkdir(parents=True)
    (home / CREDENTIALS).write_text('{"placeholder": true}', encoding="utf-8")
    monkeypatch.setattr(host_login, "preflight", lambda *_a, **_k: None)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    for name in ("CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_REAL_CONFIG_DIR", "DEV_JUDGE_MODEL"):
        monkeypatch.delenv(name, raising=False)
    return home


def test_a_codex_run_is_graded_in_a_fresh_claude_isolation(codex_home, claude_home, tmp_path,
                                                           monkeypatch):
    """testing-harness spec: Codex run graded by the Claude judge."""
    monkeypatch.setenv("CODEX_HOME", str(codex_home))  # the operator's, inherited
    order: list[str] = []
    seen: dict = {}

    def produce(ws):
        order.append("codex run")
        write_draft(ws)

    fake_codex_run(monkeypatch, produce=produce)

    async def judge_all(criteria, *, model, effort, config, source, **_options):
        order.append("judge")
        link = config / CREDENTIALS
        seen.update(config=config, link=link.resolve(), source=source,
                    env=host_login.allowlisted_env(CLAUDE, config, os.environ))
        call = JudgeCall("GRADE: C", model, "2.1.284", effort, 10, 0.01,
                         RateLimit("allowed", "five_hour", 0.1))
        return JudgeRun(tuple(Grade(c.name, True, "ok", call) for c in criteria), 0.02)

    monkeypatch.setattr(claude_cli, "judge_all", judge_all)
    log = tmp_path / "log.jsonl"
    argv = ["write_from_seed", "--host", "codex", "--model", "gpt-fixture-a", "--judge",
            "--summary-log", str(log)]
    assert main(argv) == 0
    assert order == ["codex run", "judge"]
    config = seen["config"]
    assert seen["link"] == (claude_home / CREDENTIALS).resolve()
    assert seen["source"] == host_login.LoginSource.HARNESS
    assert str(codex_home) not in str(config)
    assert "CODEX_HOME" not in seen["env"]
    assert str(codex_home) not in json.dumps(seen["env"])
    assert seen["env"]["CLAUDE_CONFIG_DIR"] == str(config)
    [line] = logged(log)
    assert line["l2_label"] == claude_runner.JUDGE_LABEL
    assert line["self_graded"] is False
    assert line["label"] == LABEL


def test_rejudging_a_codex_workspace_reads_it_with_the_codex_reader(tmp_path, monkeypatch):
    """testing-harness spec: Codex workspace re-graded."""
    no_codex(monkeypatch)
    ws = tmp_path / "kept"
    ws.mkdir()
    write_draft(ws)
    save_events(stream("model-rerouted", ws), ws)
    assert (ws / EVENTS_FILE).is_file()
    configs: list[Path] = []

    async def judge_all(criteria, *, model, effort, config, **_options):
        configs.append(config)
        call = JudgeCall("GRADE: C", model, "2.1.284", effort, 10, 0.01,
                         RateLimit("allowed", "five_hour", 0.1))
        return JudgeRun(tuple(Grade(c.name, True, "ok", call) for c in criteria), 0.02)

    monkeypatch.setattr(claude_cli, "judge_all", judge_all)
    isolated = tmp_path / "devjudge-config"
    isolated.mkdir()
    monkeypatch.setattr(claude_runner, "enter_isolation", lambda _stack, prefix: (
        isolated if prefix == "devjudge-config-" else pytest.fail(prefix)))
    log = tmp_path / "log.jsonl"
    assert main(["write_from_seed", "--host", "codex", "--rejudge", str(ws),
                 "--summary-log", str(log)]) == 0
    [line] = logged(log)
    assert line["model"] == "gpt-fixture-b"  # the Codex reader: the reroute target
    assert configs == [isolated]
