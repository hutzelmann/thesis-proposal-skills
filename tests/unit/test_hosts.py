"""L0: the dev runner's host seam (`harness/hosts.py`, `claude_runner.HOSTS`;
testing-harness spec: Dev-runner host adapters, Subscription text roles).

The Codex host is driven end to end with `codex_cli.run_codex` replaced by a
fake that returns a synthetic saved event list (`data/codex_streams/`), and its
preflight stubbed: no test starts `codex`, and no test needs a ChatGPT login.
A `--host codex` run is a usage error without POSIX file locks (the Windows CI
job), so the end-to-end runs carry `LOCKS`; the usage errors and the re-grade
run everywhere.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import claude_cli
import claude_runner
import codex_cli
import copilot_cli
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
from helpers import CLEAN_DRAFT, COPILOT_TOKEN, REPO, copilot_stream
from host_login import CLAUDE, CODEX, CREDENTIALS, STATE_VAR, LoginProblem, refusal

STREAMS = Path(__file__).resolve().parent / "data" / "codex_streams"
CLAUDE_STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"
LABEL = "dev-runner (codex), not comparable to matrix"
LOCKS = pytest.mark.skipif(host_login.fcntl is None,
                           reason="a --host codex run needs POSIX file locks")


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


def test_the_hosts_are_claude_codex_and_copilot():
    assert set(HOSTS) == {"claude", "codex", "copilot"}
    assert HOSTS["claude"].skill_dir == (".claude", "skills")
    assert HOSTS["codex"].skill_dir == (".agents", "skills")
    assert HOSTS["copilot"].skill_dir == (".agents", "skills")
    assert HOSTS["claude"].login is CLAUDE
    assert HOSTS["codex"].login is CODEX
    assert HOSTS["copilot"].login is host_login.COPILOT
    assert HOSTS["copilot"].always_isolated
    assert HOSTS["copilot"].run_label == "dev-runner (copilot), not comparable to matrix"
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


@pytest.mark.parametrize("locks", [True, False], ids=["file-locks", "no-file-locks"])
@pytest.mark.parametrize(("argv", "named"), [
    (["check_report", "--host", "codex"], "requires --model"),
    (["check_report", "--host", "codex", "--model", "openai/gpt-fixture-a"], "provider"),
    ([*CODEX_RUN, "--max-budget-usd", "1"], "budget cap"),
    (["install_prompt", "--host", "codex", "--model", "gpt-fixture-a"], "install-prompt"),
    (["check_report", "--effort", "high"], "--effort applies"),
    ([*CODEX_RUN, "--effort", "ultra"], "ultra"),
])
def test_codex_usage_errors_stage_nothing_and_start_nothing(argv, named, locks, monkeypatch,
                                                           capsys):
    """testing-harness spec: Codex run without a model; Install scenario on Codex;
    Budget cap refused on Codex. Each reads the same without POSIX file locks:
    that rule comes last."""
    refuse_staging(monkeypatch)
    no_codex(monkeypatch)
    if not locks:
        monkeypatch.setattr(host_login, "fcntl", None)
    with pytest.raises(SystemExit) as usage:
        main(argv)
    assert usage.value.code == EXIT_USAGE
    err = capsys.readouterr().err
    assert named in err
    assert "POSIX file locks" not in err


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


@LOCKS
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
        "gpt-fixture-a", "gpt-fixture-a", "0.160.0")  # the session record's turn model
    assert "model_check" not in line
    assert line["quota_before"]["primary"]["used_percent"] == 12.0
    assert line["quota_after"]["primary"]["used_percent"] == 14.0
    [run] = runs
    assert run["home"] == codex_home
    assert run["model"] == "gpt-fixture-a"
    assert run["staged"] == ["proposal-check"]
    assert run["scenario"] is SCENARIOS["check_report"]
    assert "outcome" in line


@LOCKS
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
@LOCKS
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


@LOCKS
@pytest.mark.usefixtures("codex_home")
def test_a_codex_billing_refusal_is_untested_and_records_billing(tmp_path, monkeypatch):
    fake_codex_run(monkeypatch, name="credits-drawn")
    log = tmp_path / "log.jsonl"
    assert main([*CODEX_RUN, "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert "credits" in line["billing"]
    assert "Empty the Codex credit balance" in line["why"]


LIMIT = "codex did not finish within 600s"


@LOCKS
@pytest.mark.parametrize(("name", "status", "billing", "named"), [
    ("success", EXIT_RUNNER, False, LIMIT),
    ("credits-drawn", EXIT_UNTESTED, True, "Empty the Codex credit balance"),
    ("provider-leak", EXIT_UNTESTED, True, "openrouter"),
    ("plan-free", EXIT_UNTESTED, True, "free"),
    ("limit-reached", EXIT_UNTESTED, True, "reached"),
    ("mcp-call", EXIT_UNTESTED, False, "mcp__docs__publish"),
])
@pytest.mark.usefixtures("codex_home")
def test_a_codex_run_at_its_limit_is_checked_like_any_other(name, status, billing, named,
                                                            tmp_path, monkeypatch):
    """testing-harness spec: Codex interrupted before kill (a runner failure
    naming the limit), and the after-run billing and isolation checks, which
    hold for a timed-out run too: its captured session record decides."""
    def timed_out(ws, _request, **_kwargs):
        raise codex_cli.CodexRunFailed(LIMIT, stream(name, ws))

    monkeypatch.setattr(codex_cli, "run_codex", timed_out)
    log = tmp_path / "log.jsonl"
    assert main([*CODEX_RUN, "--summary-log", str(log)]) == status
    [line] = logged(log)
    assert line["exit_status"] == status
    assert line["why"].startswith(LIMIT)
    assert named in line["why"]
    assert bool(line.get("billing")) is billing


@LOCKS
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


@LOCKS
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


JUDGE_STREAM = (Path(__file__).resolve().parent / "data" / "claude_cli_streams"
                / "success.jsonl").read_text(encoding="utf-8")
JUDGE_STATUS = json.dumps({"loggedIn": True, "authMethod": "claude.ai",
                           "apiProvider": "firstParty"})


@LOCKS
def test_a_codex_run_is_graded_in_a_fresh_claude_isolation(codex_home, claude_home, tmp_path,
                                                           monkeypatch):
    """testing-harness spec: Codex run graded by the Claude judge. The real
    judge path builds the judge children's environments (`allowlisted_env`,
    recorded); only the child start (`claude_cli.run_child`) is faked."""
    monkeypatch.setenv("CODEX_HOME", str(codex_home))  # the operator's, inherited
    order: list[str] = []
    built: list[tuple] = []
    children: list[dict] = []

    def produce(ws):
        order.append("codex run")
        write_draft(ws)

    fake_codex_run(monkeypatch, produce=produce)
    real = host_login.allowlisted_env

    def recording(record, config, environ=None):
        built.append((record, config, environ))
        return real(record, config, environ)

    async def run_child(command, _stdin, env, _cwd, _timeout):
        order.append("judge")
        link = Path(env["CLAUDE_CONFIG_DIR"]) / CREDENTIALS  # gone once the judge is done
        children.append({"command": command, "env": dict(env), "link": link.resolve()})
        if command[1:3] == ["auth", "status"]:
            return 0, JUDGE_STATUS, ""
        model = command[command.index("--model") + 1]
        return 0, JUDGE_STREAM.replace("claude-fixture-1-0", model), ""

    monkeypatch.setattr(host_login, "allowlisted_env", recording)
    monkeypatch.setattr(claude_cli, "run_child", run_child)
    log = tmp_path / "log.jsonl"
    argv = ["write_from_seed", "--host", "codex", "--model", "gpt-fixture-a", "--judge",
            "--summary-log", str(log)]
    assert main(argv) == 0
    assert order[0] == "codex run"
    assert set(order[1:]) == {"judge"}
    assert children[0]["command"][1:3] == ["auth", "status"]  # the judge's preflight first
    assert len(children) > 1
    [config] = {config for _, config, _ in built}
    assert all(record is CLAUDE for record, _, _ in built)
    assert len(built) == len(children)
    assert str(codex_home) not in str(config)
    for child in children:
        assert child["link"] == (claude_home / CREDENTIALS).resolve()
        assert "CODEX_HOME" not in child["env"]
        assert str(codex_home) not in json.dumps(child["env"])
        assert child["env"]["CLAUDE_CONFIG_DIR"] == str(config)
    [line] = logged(log)
    assert line["l2_label"] == claude_runner.JUDGE_LABEL
    assert line["self_graded"] is False
    assert line["label"] == LABEL
    assert {c["grade"] for c in line["l2"]["criteria"].values()} == {"PASS"}


@pytest.mark.parametrize("locks", [True, False], ids=["file-locks", "no-file-locks"])
def test_rejudging_a_codex_workspace_reads_it_with_the_codex_reader(locks, tmp_path,
                                                                    monkeypatch):
    """testing-harness spec: Codex workspace re-graded; Inverted-hybrid runners
    (the re-grade carries the host's not-comparable label). A re-grade takes no
    lock, so it runs without POSIX file locks too."""
    no_codex(monkeypatch)
    if not locks:
        monkeypatch.setattr(host_login, "fcntl", None)
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
    assert (line["host"], line["label"]) == ("codex", LABEL)
    assert line["l2_label"] == claude_runner.JUDGE_LABEL
    assert configs == [isolated]


# ---------- the Copilot host (add-copilot-dev-runner) ------------------------------------

COPILOT_LABEL = "dev-runner (copilot), not comparable to matrix"
COPILOT_RUN = ["check_report", "--host", "copilot", "--model", "copilot-fixture-a",
               "--max-ai-credits", "30"]


def no_copilot(monkeypatch):
    def refuse(*_args, **_kwargs):
        raise AssertionError("a Copilot process was started")

    for name in ("run_copilot", "spawn", "start", "read_status", "short", "preflight_report",
                 "confinement_probe"):
        monkeypatch.setattr(copilot_cli, name, refuse)


@pytest.fixture
def copilot_home(copilot_home, monkeypatch):
    """The shared seeded Copilot harness home (conftest), with the checks
    before the lock that would start the client stubbed."""
    monkeypatch.setattr(copilot_cli, "installed_version", lambda *_a: (1, 0, 91))
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    return copilot_home


def fake_copilot_run(monkeypatch, name="success", produce=None, raises=None) -> list[dict]:
    runs: list[dict] = []

    def run_copilot(ws, request, **kwargs):
        runs.append({"ws": ws, "request": request, **kwargs,
                     "staged": sorted(p.name for p in (ws / ".agents" / "skills").iterdir())})
        if raises is not None:
            raise raises
        if produce:
            produce(ws)
        return copilot_stream(name, ws)

    monkeypatch.setattr(copilot_cli, "run_copilot", run_copilot)
    return runs


@pytest.mark.parametrize(("argv", "named"), [
    (["check_report", "--host", "copilot", "--max-ai-credits", "30"], "requires --model"),
    (["check_report", "--host", "copilot", "--model", "auto", "--max-ai-credits", "30"],
     "--model auto"),
    (["check_report", "--host", "copilot", "--model", "github/copilot-fixture-a",
      "--max-ai-credits", "30"], "provider-qualified"),
    (["check_report", "--host", "copilot", "--model", "copilot-fixture-a"], "--max-ai-credits"),
    ([*COPILOT_RUN[:-1], "29"], "below the minimum 30"),
    ([*COPILOT_RUN, "--max-budget-usd", "1"], "credit cap"),
    (["install_prompt", "--host", "copilot", "--model", "copilot-fixture-a",
      "--max-ai-credits", "30"], "install-prompt"),
    (["check_report", "--preflight-only"], "--preflight-only applies"),
    (["check_report", "--host", "codex", "--model", "gpt-fixture-a", "--preflight-only"],
     "--preflight-only applies"),
    (["check_report", "--max-ai-credits", "30"], "--max-ai-credits applies"),
    ([*COPILOT_RUN, "--effort", "ultra"], "ultra"),
    ([*COPILOT_RUN, "--summary-log", "logs/evals/x.jsonl"], "lies inside logs/evals"),
    ([*COPILOT_RUN, "--preflight-only", "--keep"], "--preflight-only takes no --keep"),
    (["write_from_seed", *COPILOT_RUN[1:], "--preflight-only", "--judge"],
     "--preflight-only takes no --judge"),
    (["write_from_seed", "--host", "copilot", "--rejudge", "/tmp/devrun-x", "--preflight-only"],
     "--preflight-only takes no --rejudge"),
])
def test_copilot_usage_errors_stage_nothing_and_start_nothing(argv, named, monkeypatch, capsys):
    """testing-harness spec: Copilot run without a pinned model; Credit cap required;
    Dollar budget cap refused on Copilot; Install scenario on Copilot."""
    refuse_staging(monkeypatch)
    no_copilot(monkeypatch)
    with pytest.raises(SystemExit) as usage:
        main(argv)
    assert usage.value.code == EXIT_USAGE
    assert named in capsys.readouterr().err


def test_a_codex_effort_outside_its_levels_is_a_usage_error(monkeypatch, capsys):
    refuse_staging(monkeypatch)
    with pytest.raises(SystemExit):
        main([*CODEX_RUN, "--effort", "minimal"])
    assert "not a Codex effort" in capsys.readouterr().err


def test_copilot_stages_where_a_folder_install_puts_the_skills(tmp_path):
    """testing-harness spec: Copilot skill staged where a folder install puts it."""
    stage(SCENARIOS["supervise_feedback"], tmp_path, skill_dir=HOSTS["copilot"].skill_dir)
    root = tmp_path / ".agents" / "skills"
    assert sorted(p.name for p in root.iterdir()) == ["proposal-import", "proposal-supervise"]
    assert not list(root.rglob("evals"))
    assert not (tmp_path / ".claude").exists()


@LOCKS
def test_a_copilot_run_is_summarized_and_labelled(copilot_home, tmp_path, monkeypatch):
    """testing-harness spec: Copilot dev run labelled by host; Copilot run reports
    credits, not cost."""
    monkeypatch.setattr(copilot_cli, "read_stop", lambda _home: None)
    runs = fake_copilot_run(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main([*COPILOT_RUN, "--summary-log", str(log)]) in (0, 1)  # a verdict, either way
    [line] = logged(log)
    assert line["l1"] in ("PASS", "FAIL")
    assert (line["host"], line["label"]) == ("copilot", COPILOT_LABEL)
    assert (line["config"], line["config_dir"]) == ("isolated", str(copilot_home))
    assert (line["login"], line["login_dir"]) == ("harness", str(copilot_home))
    assert line["cost_usd"] is None
    assert line["ai_credits"] == 12.0
    assert line["notional_basis"] == "copilot credits, not billed"
    assert (line["cap_credits"], line["overage_before"], line["overage_after"]) == (30, 0, 0)
    assert (line["remaining_before"], line["remaining_after"]) == (80.0, 79.2)
    assert (line["model_requested"], line["model"], line["cli_version"]) == (
        "copilot-fixture-a", "copilot-fixture-a", "1.0.91")
    [run] = runs
    assert (run["home"], run["model"], run["cap"]) == (copilot_home, "copilot-fixture-a", 30)
    assert run["staged"] == ["proposal-check"]
    assert not (REPO / "logs" / "evals" / "x.jsonl").exists()


@LOCKS
@pytest.mark.parametrize(("raises", "stream_name", "named"), [
    (host_login.RunLockBusy(LoginProblem(
        "another Copilot run holds the harness home (/fake/copilot/.harness-run.lock)",
        "rerun after it ends", "copilot", "precondition")), None, ".harness-run.lock"),
    (None, "model-differs", "copilot-fixture-b"),
    (None, "effort-unapplied", "left unapplied"),
    (None, "unknown-tool", "frobnicate"),
])
@pytest.mark.usefixtures("copilot_home")
def test_a_copilot_precondition_is_untested_not_a_runner_failure(raises, stream_name, named,
                                                                tmp_path, monkeypatch):
    """testing-harness spec: Copilot precondition is untested, not a runner failure."""
    monkeypatch.setattr(copilot_cli, "read_stop", lambda _home: None)
    fake_copilot_run(monkeypatch, name=stream_name or "success", raises=raises)
    log = tmp_path / "log.jsonl"
    assert main([*COPILOT_RUN, "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert line["exit_status"] == EXIT_UNTESTED != EXIT_RUNNER
    assert named in line["why"]


@LOCKS
@pytest.mark.parametrize(("problem", "named"), [
    (LoginProblem("the installed Copilot CLI is 1.0.92, not the pinned 1.0.91",
                  "install the Copilot CLI 1.0.91", "copilot", "precondition"), "1.0.92"),
    (LoginProblem("the Copilot sandbox needs slirp4netns on PATH", "install slirp4netns",
                  "copilot", "precondition"), "slirp4netns"),
    (LoginProblem("the client's model listing offers under the policy 'disabled' "
                  "copilot-fixture-a", "enable the model", "copilot", "precondition"),
     "'disabled'"),
])
@pytest.mark.usefixtures("copilot_home")
def test_a_copilot_preflight_refusal_is_untested(problem, named, tmp_path, monkeypatch):
    monkeypatch.setattr(copilot_cli, "isolated_home", lambda *_a, **_k: (_ for _ in ()).throw(
        copilot_cli.CopilotRefused.of(problem)))
    no_copilot(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main([*COPILOT_RUN, "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert named in line["why"]
    assert line["host"] == "copilot"


@LOCKS
def test_the_approval_stop_refuses_the_run_as_untested(copilot_home, tmp_path, monkeypatch):
    copilot_cli.record_stop(copilot_home, "approval", "first run not yet approved")
    no_copilot(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main([*COPILOT_RUN, "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert "approval stop" in line["why"]
    assert "--clear-stop" in line["why"]


@LOCKS
@pytest.mark.usefixtures("copilot_home")
def test_a_copilot_session_without_shutdown_is_a_runner_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(copilot_cli, "read_stop", lambda _home: None)
    fake_copilot_run(monkeypatch, name="no-shutdown")
    log = tmp_path / "log.jsonl"
    assert main([*COPILOT_RUN, "--summary-log", str(log)]) == EXIT_RUNNER
    assert "consumption cannot be read" in logged(log)[0]["why"]


@LOCKS
def test_a_copilot_run_is_graded_without_the_token_or_the_home(copilot_home, claude_home,
                                                               tmp_path, monkeypatch):
    """testing-harness spec: Token never reaches another child — the judge's child
    and its login check carry neither COPILOT_GITHUB_TOKEN, its value, nor the
    Copilot home."""
    assert claude_home.parent == copilot_home.parent  # both harness homes, one state root
    monkeypatch.setattr(copilot_cli, "read_stop", lambda _home: None)
    monkeypatch.setenv("COPILOT_GITHUB_TOKEN", "github_pat_EXPORTED_PLACEHOLDER")
    children: list[dict] = []
    fake_copilot_run(monkeypatch, produce=write_draft)

    async def run_child(command, _stdin, env, _cwd, _timeout):
        children.append({"command": command, "env": dict(env)})
        if command[1:3] == ["auth", "status"]:
            return 0, JUDGE_STATUS, ""
        model = command[command.index("--model") + 1]
        return 0, JUDGE_STREAM.replace("claude-fixture-1-0", model), ""

    monkeypatch.setattr(claude_cli, "run_child", run_child)
    log = tmp_path / "log.jsonl"
    argv = ["write_from_seed", "--host", "copilot", "--model", "copilot-fixture-a",
            "--max-ai-credits", "30", "--judge", "--summary-log", str(log)]
    assert main(argv) == 0
    assert len(children) > 1
    for child in children:
        dumped = json.dumps(child)
        assert "COPILOT_GITHUB_TOKEN" not in child["env"]
        assert COPILOT_TOKEN not in dumped
        assert "EXPORTED_PLACEHOLDER" not in dumped
        assert str(copilot_home) not in dumped
    assert logged(log)[0]["label"] == COPILOT_LABEL


def test_rejudging_a_copilot_workspace_starts_no_copilot_process(tmp_path, monkeypatch):
    no_copilot(monkeypatch)
    ws = tmp_path / "kept"
    ws.mkdir()
    write_draft(ws)
    save_events(copilot_stream("model-differs", ws), ws)

    async def judge_all(criteria, *, model, effort, **_options):
        call = JudgeCall("GRADE: C", model, "2.1.284", effort, 10, 0.01,
                         RateLimit("allowed", "five_hour", 0.1))
        return JudgeRun(tuple(Grade(c.name, True, "ok", call) for c in criteria), 0.02)

    monkeypatch.setattr(claude_cli, "judge_all", judge_all)
    isolated = tmp_path / "devjudge-config"
    isolated.mkdir()
    monkeypatch.setattr(claude_runner, "enter_isolation", lambda _stack, _prefix: isolated)
    log = tmp_path / "log.jsonl"
    assert main(["write_from_seed", "--host", "copilot", "--rejudge", str(ws),
                 "--summary-log", str(log)]) == 0
    [line] = logged(log)
    assert line["model"] == "copilot-fixture-a, copilot-fixture-b"  # the Copilot reader
    assert (line["host"], line["label"]) == ("copilot", COPILOT_LABEL)


@LOCKS
@pytest.mark.usefixtures("copilot_home")
def test_preflight_only_prints_each_check_and_starts_no_run(monkeypatch, capsys):
    """testing-harness spec: Copilot preflight only."""
    seen: list[str] = []

    def report(ws, _scenario, **_options):
        seen.append(str(ws))
        assert (ws / ".agents" / "skills" / "proposal-check" / "SKILL.md").is_file()
        stop = LoginProblem("an approval stop is recorded", "clear it", "copilot", "precondition")
        return [copilot_cli.Check("location"), copilot_cli.Check("stop", stop, "approval (x)"),
                copilot_cli.Check("confinement_probe")], True

    monkeypatch.setattr(copilot_cli, "preflight_report", report)
    monkeypatch.setattr(copilot_cli, "run_copilot",
                        lambda *_a, **_k: pytest.fail("a prompt-mode child started"))
    assert main([*COPILOT_RUN, "--preflight-only"]) == 0
    out = capsys.readouterr().out
    assert "stop: recorded — approval (x)" in out
    assert "preflight: ready" in out
    assert not Path(seen[0]).exists()  # the workspace is deleted


@LOCKS
@pytest.mark.usefixtures("copilot_home")
@pytest.mark.parametrize("raised", [
    host_login.RunLockBusy(LoginProblem("another Copilot run holds the harness home",
                                        "rerun after it ends", "copilot", "precondition")),
    copilot_cli.BillingEnvError(["GH_TOKEN"]),
])
def test_a_preflight_only_refusal_is_untested_not_a_runner_failure(raised, monkeypatch, capsys):
    def report(*_args, **_kwargs):
        raise raised

    monkeypatch.setattr(copilot_cli, "preflight_report", report)
    assert main([*COPILOT_RUN, "--preflight-only"]) == EXIT_UNTESTED
    assert capsys.readouterr().err.startswith("untested: ")
