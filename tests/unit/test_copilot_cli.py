"""L0: the GitHub Copilot host of the dev runner (`harness/copilot_cli.py`;
testing-harness spec: Copilot plan billing guard, Dev-runner host adapters,
Harness-owned host logins, Isolated child environment).

No test starts the real `copilot`: the conftest points the binary seam
(`copilot_cli.binary`) at a sentinel that raises, and a test that needs a child
points it at a Python script written under `tmp_path` (`fake_copilot`), which
answers `--version`, `skill list`, `mcp list`, the headless server's
Content-Length JSON-RPC and a prompt-mode run from the synthetic fixtures in
`data/copilot_streams/` (README there: every file synthetic, from the 1.0.91
package). The fake records which token-shaped variables it received, by name.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from argparse import Namespace
from contextlib import contextmanager, suppress
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import claude_cli
import claude_runner
import copilot_cli
import host_login
import pytest
import routing
from claude_cli import Grade, JudgeCall, JudgeRun, RateLimit
from copilot_cli import Check, ProbeResult, RunProblem
from helpers import CLEAN_DRAFT, COPILOT_STREAMS, REPO, copilot_stream
from helpers import COPILOT_TOKEN as TOKEN
from helpers import copilot_reply as load
from host_login import COPILOT, LoginProblem, refusal
from l1_checks import verdict_single_context, verdict_supervise_verifier

STREAMS = COPILOT_STREAMS
WS = Path(tempfile.gettempdir()) / "devrun-check_report-copilot"  # never created
SKILL_ROOT = WS / ".agents" / "skills"
NOTE = "Your own Copilot login is not affected"
POSIX = pytest.mark.skipif(os.name != "posix" or host_login.fcntl is None,
                           reason="POSIX file locks and signals")
# taken at import, before the conftest replaces the seam (no test writes under /run/user)
REAL_RUNTIME_DIR = copilot_cli.runtime_dir


def stream(name: str, ws: Path = WS) -> list[dict]:
    """A saved stream with this file's default workspace path filled in."""
    return copilot_stream(name, ws)


def status_of(name: str, models: bool = True) -> copilot_cli.Status:
    replies = dict(load(name))  # type: ignore[arg-type]
    if models:
        replies["models"] = load("models")
    return copilot_cli.parse_status(replies)


def stdout_part(events: list[dict]) -> list[dict]:
    return [e for e in events if not str(e.get("type")).startswith("copilot.")]


def records_part(events: list[dict]) -> list[dict]:
    return [e for e in events if str(e.get("type")).startswith("copilot.")
            and e["type"] != "copilot.harness"]


# ---------- the fake client ------------------------------------------------------------------

FAKE = r'''
import json, os, pathlib, signal, sys, time
CONFIG = json.loads(pathlib.Path(__file__).with_suffix(".json").read_text(encoding="utf-8"))
ARGS = sys.argv[1:]
LOG = pathlib.Path(CONFIG["log"])

def subcommand(args):
    # a short command takes the credential flags before its subcommand, where
    # 1.0.91 parses them as global options
    while args[:1] in (["--no-auto-login"], ["--auth-token-env"]):
        args = args[2:] if args[0] == "--auth-token-env" else args[1:]
    return args

CMD = subcommand(ARGS)
HEADER = "// User settings belong in settings.json.\n// This file is managed automatically.\n"

def start_writes():
    # what the 1.0.91 client writes when it starts (task 7.4a, measured): its
    # state file with the comment header and `firstLaunchAt`, and an empty
    # process log under `--log-dir`, or under `<COPILOT_HOME>/logs` without it
    home = pathlib.Path(os.environ["COPILOT_HOME"])
    if not (home / "config.json").exists():
        (home / "config.json").write_text(
            HEADER + json.dumps({"firstLaunchAt": "2026-01-01T00:00:00.000Z"}), encoding="utf-8")
    logs = pathlib.Path(ARGS[ARGS.index("--log-dir") + 1]) if "--log-dir" in ARGS else home / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / f"process-{int(time.time() * 1000)}-{os.getpid()}.log").write_text(
        "", encoding="utf-8")
    for name, text in CONFIG.get("home_writes", {}).items():  # e.g. a cache file
        (home / name).write_text(text, encoding="utf-8")

def record(kind):
    names = sorted(n for n, v in os.environ.items()
                   if n.endswith(("_TOKEN", "_API_KEY")) or v.startswith("github_pat_"))
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": kind, "argv": ARGS, "token_names": names,
                             "token_ok": os.environ.get("COPILOT_GITHUB_TOKEN") == CONFIG["token"],
                             "home": os.environ.get("HOME"),
                             "copilot_home": os.environ.get("COPILOT_HOME"),
                             "cwd": os.getcwd()}) + "\n")

def frame(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, _, value = line.decode().partition(":")
        headers[name.strip().lower()] = value.strip()
    return json.loads(stream.read(int(headers["content-length"])))

def send(message):
    body = json.dumps(message).encode()
    sys.stdout.buffer.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    sys.stdout.buffer.flush()

PROBES = ((f"/proc/{os.getpid()}/environ", "client_environ"),  # this server's own pid
          (f"/proc/{os.getppid()}/environ", "harness_environ"),  # the harness that started it
          # git's row names the operator's GitHub CLI directory too, so it comes first
          ("git credential", "git_credential"), (".ssh", "ssh_dir"), (".config/gh", "gh_config"),
          ("gh auth token", "gh_token"), ("python3 -c", "python"), ("--help", "skill_script"),
          ("copilot.token", "token_file"), ("ns/net", "net_ns"), ("devrun-probe-tmp-", "host_tmp"),
          ("devrun-probe-write-", "tmp_write"))

def probe_name(command):
    return next(name for needle, name in PROBES if needle in command)

HOME = pathlib.Path(os.environ.get("COPILOT_HOME", "."))
SANDBOXED = set()  # the sessions `session.options.update` put in the home's sandbox block
UNCONFINED = {"gh_token": "0", "git_credential": "128", "python": "0", "skill_script": "0",
              "net_ns": "shared", "tmp_write": "0"}

def home_sandbox():
    return json.loads((HOME / "settings.json").read_text(encoding="utf-8")).get("sandbox")

def note_rpc(method, params):
    with open(CONFIG["log"] + ".rpc", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"method": method, "params": params}) + "\n")

def options_update(params):
    mode = CONFIG.get("options_update", "ok")
    if mode == "error":
        return {"error": {"code": -32000, "message": "managed_sandbox_policy_conflict"}}
    if mode == "no-result":
        return {}
    if params.get("sandboxConfig") == home_sandbox():
        SANDBOXED.add(params["sessionId"])
    return {"result": {"success": mode == "ok"}}

def shell(params, calls):
    # 1.0.91 (K6, 2026-10-06): a session the server created runs its shell
    # unconfined and reports no `sandboxed`, until `session.options.update`
    # gives it the home's sandbox block
    name = probe_name(params["command"])
    ident = f"probe-{len(calls)}"
    calls.append(name)
    if name == "tmp_write" and CONFIG.get("tmp_reaches_host"):  # a host /tmp left writable
        target = params["command"].split(": > ", 1)[1].split(" 2>", 1)[0].strip("'")
        pathlib.Path(target).write_text("", encoding="utf-8")
    if params["sessionId"] in SANDBOXED:
        found = next(r for r in CONFIG["probe"]["results"] if r["name"] == name)
        data = {"toolCallId": ident, "success": True, "sandboxed": found["sandboxed"]}
        output = found["output"]
    else:
        data, output = {"toolCallId": ident, "success": True}, UNCONFINED.get(name, "readable")
    send({"jsonrpc": "2.0", "method": "session.event", "params": {
        "sessionId": params["sessionId"], "event": {"type": "tool.execution_complete",
                                                    "data": data}}})
    return {"result": {"toolCallId": ident, "success": True, "output": output + "\n",
                       "exitCode": 0}}

def answer(message, calls):
    method, params = message.get("method"), message.get("params") or {}
    note_rpc(method, params)
    if method == "connect":
        return {"result": CONFIG["status"].get("connect", {}).get("result", {"protocolVersion": 3})}
    if method == "account.getCurrentAuth":
        # 1.0.91, measured (task 7.4b): under `--no-auto-login` the server reads
        # only the variable `--auth-token-env` names, and answers `{}` without it
        named = ARGS[ARGS.index("--auth-token-env") + 1] if "--auth-token-env" in ARGS else None
        if "--no-auto-login" in ARGS and named is None:
            return {"result": {}}
        token = os.environ.get(named or "COPILOT_GITHUB_TOKEN")
        return (CONFIG["status"] if token else CONFIG["status_no_token"])["auth"]
    if method == "models.list":
        return CONFIG["models"]
    if method == "sandbox.getHostSupport":
        return {"result": CONFIG["probe"]["host_support"]}
    if method == "user.settings.get":
        block = CONFIG["client_sandbox"] if "client_sandbox" in CONFIG else home_sandbox()
        return {"result": {"settings": {"sandbox": {"value": block, "default": None,
                                                    "isDefault": False}}}}
    if method == "session.create":
        # 1.0.91 (K3, 2026-10-06): creating a session also makes an empty
        # `installed-plugins/` in the home
        (HOME / "session-state" / params["sessionId"]).mkdir(parents=True)
        (HOME / "installed-plugins").mkdir(exist_ok=True)
        return {"result": {"sessionId": params["sessionId"]}}
    if method == "session.options.update":
        return options_update(params)
    if method == "session.shell.executeUserRequested":
        return shell(params, calls)
    if method == "session.delete":
        # 1.0.91 (K3): deleting it leaves an empty lock file named after it
        locks = HOME / "session-state" / ".session-operation-locks"
        locks.mkdir(parents=True, exist_ok=True)
        (locks / (params["sessionId"] + ".lock")).write_text("", encoding="utf-8")
        return {"result": {"success": True}}
    return {"error": {"code": -32601, "message": "unknown"}}

def serve():
    marker = pathlib.Path(CONFIG["log"] + ".served")
    mode = CONFIG.get("mode", "answer")
    if mode == "silent" or (mode == "once" and marker.exists()):
        time.sleep(60)
        return
    marker.touch()
    calls = []
    while (message := frame(sys.stdin.buffer)) is not None:
        reply = answer(message, calls)
        reply = {k: v for k, v in reply.items() if k in ("result", "error")}
        send({"jsonrpc": "2.0", "id": message["id"], **reply})

def run():
    session = next(a.split("=", 1)[1] for a in ARGS if a.startswith("--session-id="))
    folder = pathlib.Path(os.environ["COPILOT_HOME"], "session-state", session)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "events.jsonl").write_text(CONFIG["session"].replace("__WS__", os.getcwd()),
                                         encoding="utf-8")
    for name in CONFIG.get("write", []):  # a relative name lands in the workspace
        pathlib.Path(name).write_text(CONFIG.get("write_body", "") + CONFIG["token"],
                                      encoding="utf-8")
    for name, target in CONFIG.get("links", {}).items():  # what a sandboxed shell may plant
        pathlib.Path(name).unlink(missing_ok=True)
        pathlib.Path(name).symlink_to(target)
    if CONFIG.get("background"):  # a process the run leaves behind in its group
        import subprocess
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pathlib.Path(CONFIG["background"]).write_text(str(child.pid), encoding="utf-8")
    sys.stdout.write(CONFIG["stream"].replace("__WS__", os.getcwd())
                     .replace("11111111-1111-4111-8111-111111111111", session))
    sys.stdout.flush()
    sys.stderr.write(CONFIG.get("stderr", ""))
    if CONFIG.get("hang"):
        signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
        time.sleep(60)
    sys.exit(CONFIG.get("exit", 0))

if CMD[:1] == ["--version"]:
    record("version")
    print(CONFIG.get("version", "GitHub Copilot CLI 1.0.91."))
elif CMD[:2] == ["skill", "list"]:
    record("skills")
    print(json.dumps(CONFIG["skills"]).replace("__WS__", os.getcwd()))
elif CMD[:2] == ["mcp", "list"]:
    record("mcp")
    print(json.dumps(CONFIG["mcp"]))
elif "--headless" in ARGS:
    record("headless")
    start_writes()
    serve()
elif "-p" in ARGS:
    record("run")
    start_writes()
    run()
'''


def session_text(name: str, ws: Path = WS) -> str:
    """The raw session file a run would write, rebuilt from a stream's records."""
    lines = []
    for record in records_part(stream(name, ws)):
        kind = record["type"]
        data = {k: v for k, v in record.items() if k != "type"}
        if kind == "copilot.session_start":
            lines.append({"type": "session.start", "data": {**data, "sessionId": "x"}})
        elif kind == "copilot.skill_invoked":
            lines.append({"type": "skill.invoked", "data": {**data, "content": "body"}})
        elif kind == "copilot.shutdown":
            lines.append({"type": "session.shutdown", "data": data})
        elif kind == "copilot.model_change":
            lines.append({"type": "session.model_change", "data": data})
        elif kind == "copilot.hook":
            lines.append({"type": data["event"], "data": {}})
    return "".join(json.dumps(line) + "\n" for line in lines)


def fake_copilot(tmp_path: Path, monkeypatch, *, status: str = "status-ok", probe: str = "probe-ok",
                 skills: str | list = "skills-ok", mcp: str = "mcp-ok", run: str = "success",
                 **extra) -> Path:
    """Point the binary seam at a fake `copilot`; returns the call log. `skills`
    names a roster fixture, or is the roster itself."""
    script = tmp_path / "fake-copilot.py"
    log = tmp_path / "fake-copilot.log"
    stdout = "".join(json.dumps(e) + "\n" for e in stdout_part(stream(run, Path("__WS__"))))
    roster = load(skills) if isinstance(skills, str) else skills
    config = {"log": str(log), "token": TOKEN, "status": load(status),
              "status_no_token": load("status-auth-error"), "models": load("models"),
              "probe": load(probe), "skills": roster, "mcp": load(mcp),
              "stream": stdout, "session": session_text(run, Path("__WS__")), **extra}
    script.with_suffix(".json").write_text(json.dumps(config), encoding="utf-8")
    script.write_text(f"#!{sys.executable}\n" + textwrap.dedent(FAKE), encoding="utf-8")
    script.chmod(0o755)
    monkeypatch.setattr(copilot_cli, "binary", lambda: str(script))
    return log


def calls(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]


def rpc_calls(log: Path) -> list[dict]:
    """Every JSON-RPC request the fake server answered, in order: method and params."""
    return calls(Path(f"{log}.rpc"))


def sessions(home: Path) -> list[str]:
    """The session folders in the home: `session-state/` minus the empty
    session locks 1.0.91 leaves behind (K3)."""
    state = home / copilot_cli.SESSION_STATE
    return sorted(p.name for p in state.iterdir()
                  if p.name != host_login.SESSION_LOCKS) if state.is_dir() else []


@pytest.fixture
def home(copilot_home):
    """This file's name for the shared seeded Copilot home (conftest)."""
    return copilot_home


# ---------- 3.3: the environment and the pre-spawn assertion ----------------------------------

LAUNCH = {
    "PATH": "/usr/bin", "HOME": "/fake/account", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
    "TZ": "UTC", "HTTPS_PROXY": "http://proxy.invalid:3128", "SHELL": "/bin/bash",
    "GH_TOKEN": "ghp_LAUNCHING_SHELL_PLACEHOLDER",
    "GITHUB_TOKEN": "gho_LAUNCHING_SHELL_PLACEHOLDER",
    "COPILOT_GITHUB_TOKEN": "github_pat_EXPORTED_PLACEHOLDER",
    "COPILOT_PROVIDER_BASE_URL": "https://provider.invalid",
    "OTEL_EXPORTER_OTLP_ENDPOINT": "https://otel.invalid",
    "BASH_ENV": "/fake/account/.bashenv", "SSH_AUTH_SOCK": "/run/user/1000/ssh-agent",
    "CLAUDE_CODE_OAUTH_TOKEN": "placeholder-claude-token",
    "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
    "XDG_RUNTIME_DIR": "/run/user/1000", "GH_CONFIG_DIR": "/fake/account/.config/gh",
    "OPENAI_API_KEY": "placeholder-openai", "ANTHROPIC_API_KEY": "placeholder-anthropic",
}
HOME = Path(tempfile.gettempdir()) / "state" / "hosts" / "copilot"


def built(scratch: Path, token: str | None = TOKEN) -> dict[str, str]:
    return copilot_cli.child_env(HOME, LAUNCH, scratch, token)


def test_the_child_environment_is_the_builder_plus_scratch_plus_the_token(tmp_path):
    """testing-harness spec: Token variables in the launching environment;
    Token added after the builder."""
    builder = host_login.allowlisted_env(COPILOT, HOME, LAUNCH)
    assert COPILOT.token_env not in builder
    assert TOKEN not in json.dumps(builder)
    env = built(tmp_path)
    assert env["HOME"] == str(tmp_path)
    for name in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME",
                 "XDG_RUNTIME_DIR"):
        assert env[name].startswith(str(tmp_path)), name
    assert env["XDG_RUNTIME_DIR"] == str(tmp_path / "run")
    assert env["DBUS_SESSION_BUS_ADDRESS"] == "disabled:"
    assert env["GH_CONFIG_DIR"] == str(HOME / "gh")
    assert env["COPILOT_HOME"] == str(HOME)
    assert env["COPILOT_CACHE_HOME"] == str(HOME.parent.parent / "cache" / "copilot")
    assert (env["COPILOT_AUTO_UPDATE"], env["TERM"], env["NO_COLOR"]) == ("false", "dumb", "1")
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in env
    token_shaped = [n for n, v in env.items() if n.endswith(("_TOKEN", "_API_KEY"))
                    or v.startswith(copilot_cli.GITHUB_TOKEN_PREFIXES)]
    assert token_shaped == [COPILOT.token_env]
    assert env[COPILOT.token_env] == TOKEN
    for name in ("PATH", "LANG", "LC_ALL", "HTTPS_PROXY", "SHELL"):
        assert env[name] == LAUNCH[name]
    copilot_cli.assert_copilot_env(env, HOME)  # the record's names plus the token pass


def test_child_vars_keep_their_signature_and_set_no_scratch_or_token():
    names = COPILOT.child_vars(HOME)
    assert set(names) == {"COPILOT_HOME", "COPILOT_CACHE_HOME", "COPILOT_AUTO_UPDATE", "TERM",
                          "NO_COLOR", "DBUS_SESSION_BUS_ADDRESS", "GH_CONFIG_DIR"}
    assert host_login.CODEX.child_vars(HOME) == {"CODEX_HOME": str(HOME)}


def test_ignored_env_names_the_dropped_variables_by_name_only():
    names = copilot_cli.ignored_env(LAUNCH)
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "COPILOT_PROVIDER_BASE_URL",
                 "OTEL_EXPORTER_OTLP_ENDPOINT", "BASH_ENV", "SSH_AUTH_SOCK"):
        assert name in names
    assert not any(value in json.dumps(names) for value in LAUNCH.values() if len(value) > 8)


class Recorder:
    def __init__(self):
        self.calls: list[list[str]] = []

    def __call__(self, argv, **_kwargs):
        self.calls.append(list(argv))
        raise AssertionError("Popen reached")


@pytest.mark.parametrize(("leak", "named"), [
    ({"GH_TOKEN": "ghp_LEAK_PLACEHOLDER"}, "GH_TOKEN"),
    ({"COPILOT_PROVIDER_BASE_URL": "https://provider.invalid"}, "COPILOT_PROVIDER_BASE_URL"),
    ({"XYZ": "github_pat_SECOND_PLACEHOLDER"}, "XYZ"),
])
def test_a_leaking_builder_starts_no_process(leak, named, tmp_path, monkeypatch):
    """testing-harness spec: Leaked GitHub token stopped before the spawn; Only the
    record's own names are exempt."""
    real = host_login.allowlisted_env
    monkeypatch.setattr(host_login, "allowlisted_env",
                        lambda record, config, environ=None: {**real(record, config, environ),
                                                              **leak})
    popen = Recorder()
    monkeypatch.setattr(copilot_cli.subprocess, "Popen", popen)
    monkeypatch.setattr(copilot_cli, "binary", lambda: "/nonexistent/copilot")
    with pytest.raises(copilot_cli.BillingEnvError) as refused:
        copilot_cli.spawn(["copilot", "--version"], home=HOME, cwd=tmp_path, scratch=tmp_path,
                          token=TOKEN, environ=LAUNCH)
    assert popen.calls == []
    assert named in refused.value.message
    assert all(v not in refused.value.message for v in leak.values())
    assert TOKEN not in refused.value.message
    assert refused.value.kind == "subscription"


def test_run_env_adding_a_token_variable_still_fires_the_assertion(tmp_path, monkeypatch):
    monkeypatch.setattr(copilot_cli, "run_env", lambda env, scratch: {
        **env, "HOME": str(scratch), "GITHUB_TOKEN": "gho_RUN_ENV_PLACEHOLDER"})
    popen = Recorder()
    monkeypatch.setattr(copilot_cli.subprocess, "Popen", popen)
    with pytest.raises(copilot_cli.BillingEnvError, match="GITHUB_TOKEN"):
        copilot_cli.spawn(["copilot", "--version"], home=HOME, cwd=tmp_path, scratch=tmp_path,
                          token=TOKEN, environ=LAUNCH)
    assert popen.calls == []


def test_a_foreign_copilot_home_is_refused(tmp_path):
    env = {**built(tmp_path), "COPILOT_HOME": "/fake/account/.copilot"}
    with pytest.raises(copilot_cli.BillingEnvError, match="COPILOT_HOME"):
        copilot_cli.assert_copilot_env(env, HOME)


def test_scrub_replaces_every_occurrence_and_reports_it():
    text = f"a {TOKEN} b {TOKEN}"
    cleaned, hit = copilot_cli.scrub(text, TOKEN)
    assert hit
    assert TOKEN not in cleaned
    assert cleaned.count(copilot_cli.SCRUBBED) == 2
    assert copilot_cli.scrub("nothing here", TOKEN) == ("nothing here", False)
    assert copilot_cli.scrub("x", None) == ("x", False)


def test_scrubbed_events_carry_no_part_of_the_token():
    """testing-harness spec: Token value scrubbed from a child's output."""
    raw = stream("token-in-output")
    assert TOKEN in json.dumps(raw)
    events, hit = copilot_cli.scrub_events(raw, TOKEN)
    assert hit
    assert TOKEN not in json.dumps(events)
    harness = copilot_cli.harness_record(events)
    harness["scrub_hit"] = True
    assessment = copilot_cli.assess(events)
    assert assessment.problem.untested
    assert assessment.problem.kind == "isolation"
    assert TOKEN not in assessment.problem.message
    assert ("isolation", "the token's value appeared in a child's output") in assessment.stops
    clean, none = copilot_cli.scrub_events(stream("success"), TOKEN)
    assert not none
    assert clean == stream("success")


def test_scrub_tree_rewrites_workspace_files(tmp_path):
    (tmp_path / "draft.md").write_text(f"token {TOKEN}", encoding="utf-8")
    (tmp_path / "clean.md").write_text("clean", encoding="utf-8")
    assert copilot_cli.scrub_tree(tmp_path, TOKEN) == ["draft.md"]
    assert TOKEN not in (tmp_path / "draft.md").read_text(encoding="utf-8")


def _planted(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A workspace as a sandboxed shell could leave it: links to files outside
    it, a link to a directory outside it, a FIFO and a hard link — beside the
    run's real files. Returns the workspace, the outside file and directory."""
    ws, outside = tmp_path / "ws", tmp_path / "outside"
    (ws / "sub").mkdir(parents=True)
    outside.mkdir()
    victim = outside / "victim"
    victim.write_text(f"victim {TOKEN}", encoding="utf-8")
    (outside / "inner.md").write_text(f"inner {TOKEN}", encoding="utf-8")
    (ws / "draft.md").write_text(f"draft {TOKEN}", encoding="utf-8")
    (ws / "proposal.md").symlink_to(victim)
    (ws / "sub" / "dir-link").symlink_to(outside)
    (ws / "dangling.md").symlink_to(outside / "missing")
    os.mkfifo(ws / "pipe.md")
    os.link(victim, ws / "hard.md")
    return ws, victim, outside


@POSIX
def test_scrub_tree_follows_no_link_and_writes_no_hard_link(tmp_path):
    """Decision 13, the workspace after the run: the scrub reads and writes
    only singly linked regular files in the workspace — a link, a link to a
    directory, a FIFO (whose read would block) and a hard link (whose content
    is another file's) are passed over, so nothing outside changes."""
    ws, victim, outside = _planted(tmp_path)
    assert copilot_cli.scrub_tree(ws, TOKEN) == ["draft.md"]
    assert victim.read_text(encoding="utf-8") == f"victim {TOKEN}"
    assert (outside / "inner.md").read_text(encoding="utf-8") == f"inner {TOKEN}"
    link = tmp_path / "ws-link"
    link.symlink_to(ws)
    assert copilot_cli.scrub_tree(link, TOKEN) == []  # a root that is a link is not walked


@POSIX
def test_the_workspace_check_removes_what_the_harness_must_not_follow(tmp_path):
    """Decision 13: after the run, before anything in the workspace is read,
    scrubbed or written, every link, FIFO, socket, device or hard link in it is
    named and unlinked without being followed; the run's own files and every
    target outside stay as they were."""
    ws, victim, outside = _planted(tmp_path)
    identity = copilot_cli.workspace_identity(ws)
    found = copilot_cli.workspace_breach(ws, identity, TOKEN)
    for name in ("proposal.md (a link)", "sub/dir-link (a link)", "dangling.md (a link)",
                 "pipe.md (not a regular file)", "hard.md (a hard link)"):
        assert name in found, name
    assert "removed unread" in found
    remaining = sorted(p.relative_to(ws).as_posix() for p in ws.rglob("*"))
    assert remaining == ["draft.md", "sub"]
    assert victim.read_text(encoding="utf-8") == f"victim {TOKEN}"
    assert sorted(p.name for p in outside.iterdir()) == ["inner.md", "victim"]
    assert copilot_cli.workspace_breach(ws, identity, TOKEN) is None  # nothing left


@POSIX
def test_the_workspace_check_names_at_most_a_few_entries_and_scrubs_them(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    for index in range(copilot_cli.SHOWN_ENTRIES + 2):
        (ws / f"{TOKEN}-{index}").symlink_to(tmp_path)
    found = copilot_cli.workspace_breach(ws, copilot_cli.workspace_identity(ws), TOKEN)
    assert found.endswith(" and 2 more")
    assert TOKEN not in found
    assert copilot_cli.SCRUBBED in found
    assert list(ws.iterdir()) == []


@POSIX
def test_a_replaced_workspace_is_read_by_nothing(tmp_path):
    """A workspace swapped for a link (or for another directory) is not the one
    the run started in: the link is removed, never followed, and nothing in
    its target is walked or scrubbed."""
    ws, outside = tmp_path / "ws", tmp_path / "outside"
    ws.mkdir()
    outside.mkdir()
    (outside / "keep.md").write_text(f"keep {TOKEN}", encoding="utf-8")
    identity = copilot_cli.workspace_identity(ws)
    ws.rmdir()
    ws.symlink_to(outside)
    assert copilot_cli.workspace_breach(ws, identity, TOKEN) == copilot_cli.WORKSPACE_REPLACED
    assert not ws.is_symlink()
    assert not ws.exists()
    assert (outside / "keep.md").read_text(encoding="utf-8") == f"keep {TOKEN}"
    ws.mkdir()  # another directory under the same name
    assert copilot_cli.workspace_breach(ws, identity, TOKEN) == copilot_cli.WORKSPACE_REPLACED
    assert ws.is_dir()
    ws.rmdir()
    assert copilot_cli.workspace_breach(ws, identity, TOKEN) == copilot_cli.WORKSPACE_REPLACED


def test_a_workspace_breach_is_untested_for_isolation_and_stops():
    events = stream("success")
    copilot_cli.harness_record(events)["workspace_breach"] = copilot_cli.WORKSPACE_REPLACED
    assessment = copilot_cli.assess(events)
    assert assessment.problem.untested
    assert assessment.problem.kind == "isolation"
    assert copilot_cli.WORKSPACE_REPLACED in assessment.problem.message
    assert ("isolation", copilot_cli.WORKSPACE_REPLACED) in assessment.stops


@POSIX
def test_an_unpatched_run_or_status_read_raises_rather_than_spawns(home, tmp_path, monkeypatch):
    """design Decision 14: the conftest sentinel stops every real start."""
    popen = Recorder()
    monkeypatch.setattr(copilot_cli.subprocess, "Popen", popen)
    sentinel = "never starts the real copilot"
    with pytest.raises(AssertionError, match=sentinel):
        copilot_cli.read_status(home, token=TOKEN)
    ws = tmp_path / "ws"
    (ws / ".agents" / "skills").mkdir(parents=True)
    monkeypatch.setattr(copilot_cli, "scan_problem", lambda _ws: None)
    with pytest.raises(AssertionError, match=sentinel):
        copilot_cli.run_copilot(ws, "check", model="copilot-fixture-a", effort=None, cap=30,
                                timeout=5, home=home, scenario={"skill": "proposal-check"})
    assert popen.calls == []


def test_the_token_reader_refuses_a_missing_or_classic_token(home):
    path = host_login.token_path(home)
    assert copilot_cli.token_env(home) == {COPILOT.token_env: TOKEN}
    path.write_text("ghp_CLASSIC_PLACEHOLDER\n", encoding="utf-8")
    with pytest.raises(copilot_cli.CopilotRefused) as classic:
        copilot_cli.token_env(home)
    assert "fine-grained" in classic.value.message
    assert "ghp_" not in classic.value.message
    path.unlink()
    problem = copilot_cli.token_env(home, strict=False)
    assert isinstance(problem, LoginProblem)
    assert "missing" in problem.cause


def test_the_token_line_follows_the_token_file_not_the_wording_of_its_cause(tmp_path,
                                                                           monkeypatch):
    """`host-status copilot`'s `token_present` reads the token file's state, so a
    state root whose path holds "fine-grained" still reports a missing token."""
    monkeypatch.setenv(host_login.STATE_VAR, str(tmp_path / "fine-grained-check" / "state"))
    home = host_login.home(COPILOT)
    home.mkdir(parents=True)

    def line() -> str:
        return copilot_cli.status(home, {}, run_probes=False)[0]["token_present"]

    assert line() == "no"
    host_login.token_path(home).write_text("ghp_CLASSIC_PLACEHOLDER\n", encoding="utf-8")
    assert line() == "not fine-grained"
    host_login.token_path(home).write_text(TOKEN + "\n", encoding="utf-8")
    assert line() == "yes"


# ---------- 3.4: the status read and the billing guard ----------------------------------------

KEPT = {"error", "logged_in", "auth_type", "host", "auth_errors", "has_user", "plan", "sku",
        "token_based_billing", "reset_date", "snapshot", "models"}


def test_parse_status_keeps_exactly_the_listed_values():
    """testing-harness spec: Copilot status reveals no account details."""
    status = status_of("status-ok")
    assert set(status.__dataclass_fields__) == KEPT
    assert (status.auth_type, status.host, status.auth_errors) == ("token", "https://github.com",
                                                                   0)
    assert status.token_based_billing is True
    snap = status.snapshot
    assert (snap.name, snap.overage_permitted, snap.overage_count, snap.overage_entitlement,
            snap.percent_remaining) == ("premium_interactions", False, 0, 0, 80.0)
    dumped = repr(status)
    for secret in ("fixture-login-octocat", "fixture-org", "FIXTURE_REPLY_ONLY",
                   "fixture-tracking-id"):
        assert secret not in dumped
    assert status_of("status-ok").models[0].id == "copilot-fixture-a"
    assert copilot_cli.status_problem(status, "copilot-fixture-a", "high") is None


def test_choose_snapshot_reads_chat_for_the_free_limited_plan():
    """testing-harness spec: Snapshot chosen as the client chooses it."""
    status = status_of("status-free-chat")
    assert status.snapshot.name == "chat"
    assert status.snapshot.percent_remaining == 64.0
    assert copilot_cli.status_problem(status) is None
    assert status_of("status-ok").snapshot.name == "premium_interactions"


STOP_USAGE = 'a $0 budget with "Stop usage" on "All AI Credit SKUs"'


@pytest.mark.parametrize(("fixture", "named", "remedy", "billing"), [
    ("status-no-overage-field", "overage permission is missing", STOP_USAGE, True),
    ("status-no-entitlement-field", "overage entitlement is missing", STOP_USAGE, True),
    ("status-budget", "overage is permitted", STOP_USAGE, True),
    ("status-entitlement", "overage entitlement is 50", STOP_USAGE, True),
    ("status-overage-drawn", "overage count 3", "reset date 2026-11-01", True),
    ("status-legacy", "consumption in credits", "report it", True),
    ("status-low", "8.0% remaining", "reset date 2026-11-01", True),
    ("status-no-user", "without a Copilot user record", "does not match the pinned", False),
    ("status-auth-error", "auth error", "fine-grained token", False),
    ("status-gh-cli", "'gh-cli'", "another credential", False),
    ("status-enterprise", "fixture.ghe.com", "report it", False),
    ("status-error", "JSON-RPC error -32603", "does not match the pinned", False),
])
def test_status_problem_refuses_with_the_spec_remedy(fixture, named, remedy, billing):
    """testing-harness spec: Missing overage field refuses; Budget present; Missing
    entitlement field refuses; Overage already drawn; Legacy billing refused; Quota
    low; Status read unavailable; Copilot token rejected; Wrong auth source."""
    status = status_of(fixture)
    problem, is_billing = copilot_cli.status_rows(status)
    assert problem is not None
    assert is_billing is billing
    assert named in problem.cause
    message = refusal(problem)
    assert remedy.lower() in message.lower()
    assert message.endswith(f"{NOTE}.")
    for secret in ("fixture-login-octocat", "fixture-org", "FIXTURE_REPLY_ONLY"):
        assert secret not in message


def test_a_deleted_budget_reads_as_possible_overage_and_the_remedy_never_deletes():
    """testing-harness spec: Budget present; Deleted budget reads as possible
    overage. With every budget deleted, K2 read `overage_permitted: true`
    (GitHub: no budget means unlimited usage), so the remedy is the $0 budget
    that stops usage (D-a, 2026-10-06), and no wording tells the operator to
    delete one."""
    problem = copilot_cli.status_problem(status_of("status-budget"))
    message = refusal(problem)
    assert "overage is permitted" in problem.cause
    assert STOP_USAGE in message
    assert "never deleting it" in message
    assert "delete the" not in message.lower()
    assert "delete" not in copilot_cli.STOP_BUDGET.replace("deleting", "")


def _with_auth_type(kind: str) -> copilot_cli.Status:
    replies = json.loads(json.dumps(load("status-ok")))
    replies["auth"]["result"]["authInfo"]["type"] = kind
    return copilot_cli.parse_status({**replies, "models": load("models")})


def test_the_named_token_passes_as_the_sdk_token_k1_recorded():
    """testing-harness spec: Wrong auth source on Copilot — the token read from
    the named variable comes back as `token` at 1.0.91 (K1, task 7.5), and the
    set holds that type alone."""
    assert copilot_cli.TOKEN_AUTH_TYPES == ("token",)
    assert copilot_cli.status_problem(_with_auth_type("token")) is None


@pytest.mark.parametrize("kind", ["env", "user", "gh-cli", "token-provider", "copilot-api-token"])
def test_any_other_auth_type_is_another_credential(kind):
    """`env` included: automatic detection of an environment token, which
    `--no-auto-login` rules out (task 7.5's narrowing)."""
    problem = copilot_cli.status_problem(_with_auth_type(kind))
    assert problem is not None
    assert repr(kind) in problem.cause
    assert "another credential" in problem.remedy


@pytest.mark.parametrize(("status", "line"), [
    (None, "unknown"),
    (copilot_cli.Status(error="connect gave no answer in time"), "unavailable"),
    (copilot_cli.parse_status({"connect": {"result": {}}, "auth": {"result": {}}}), "none"),
])
def test_the_auth_type_line_tells_no_read_a_failed_read_and_no_login_apart(status, line):
    """The first login's `-` stood for both a failed read and a read without a
    login (2026-10-06); the line now names which."""
    assert copilot_cli._auth_line(status) == line
    assert copilot_cli._auth_line(status_of("status-ok")) == "token"


@pytest.mark.parametrize(("model", "effort", "named"), [
    ("copilot-fixture-x", None, "does not offer"),
    ("copilot-fixture-c", None, "'disabled'"),
    ("copilot-fixture-d", None, "'unconfigured'"),
    ("copilot-fixture-b", "high", "no effort 'high'"),
])
def test_the_model_listing_decides_model_and_effort(model, effort, named):
    problem = copilot_cli.status_problem(status_of("status-ok"), model, effort)
    assert named in problem.cause
    assert problem.kind == "precondition"


def test_a_status_without_a_model_listing_is_unavailable_for_a_run():
    problem = copilot_cli.status_problem(status_of("status-ok", models=False), "copilot-fixture-a")
    assert "model listing" in problem.cause


@POSIX
def test_read_status_against_a_silent_server_is_unavailable_and_stopped(home, tmp_path,
                                                                       monkeypatch):
    monkeypatch.setattr(copilot_cli, "STATUS_TIMEOUT_S", 0.5)
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 2)
    log = fake_copilot(tmp_path, monkeypatch, mode="silent")
    status = copilot_cli.read_status(home, token=TOKEN)
    assert status.error == "connect gave no answer in time"
    assert copilot_cli.status_problem(status).cause.startswith(
        "the Copilot status read is unavailable")
    [call] = calls(log)
    assert call["kind"] == "headless"
    assert call["token_ok"]
    assert call["token_names"] == [COPILOT.token_env]


@POSIX
def test_read_status_speaks_the_headless_protocol(home, tmp_path, monkeypatch):
    log = fake_copilot(tmp_path, monkeypatch)
    status = copilot_cli.read_status(home, token=TOKEN, models=True)
    assert status.error is None
    assert status.snapshot.percent_remaining == 80.0
    assert [m.id for m in status.models][:2] == ["copilot-fixture-a", "copilot-fixture-b"]
    bare = copilot_cli.read_status(home, token=None)
    assert not bare.logged_in
    token_call, no_token_call = calls(log)
    assert no_token_call["token_names"] == []
    assert not no_token_call["token_ok"]
    flags = list(copilot_cli.TOKEN_FLAGS)
    assert flags == ["--auth-token-env", COPILOT.token_env]
    assert "--no-auto-login" in token_call["argv"]
    assert _contains(token_call["argv"], flags)
    assert "--auth-token-env" not in no_token_call["argv"]


def _contains(argv: list[str], part: list[str]) -> bool:
    return any(argv[i:i + len(part)] == part for i in range(len(argv)))


@POSIX
def test_a_read_that_does_not_name_the_token_reports_no_login(home, tmp_path, monkeypatch):
    """The first login (2026-10-06): under `--no-auto-login` the 1.0.91 server
    leaves an unnamed COPILOT_GITHUB_TOKEN unread, the read reports no login,
    and the line read `-`; the fake answers as the client was measured to."""
    fake_copilot(tmp_path, monkeypatch)
    monkeypatch.setattr(copilot_cli, "TOKEN_FLAGS", ())
    status = copilot_cli.read_status(home, token=TOKEN)
    assert (status.error, status.logged_in, status.auth_type) == (None, False, None)
    assert copilot_cli._auth_line(status) == "none"
    assert "no login" in copilot_cli.status_problem(status).cause


@POSIX
def test_the_status_read_logs_to_its_scratch_and_leaves_the_home_clean(home, tmp_path,
                                                                       monkeypatch):
    """testing-harness spec: Copilot state file written by the client — the
    server's process log goes under the call's scratch, deleted with it; the
    state file it writes on start (header, `firstLaunchAt`) keeps the home clean."""
    log = fake_copilot(tmp_path, monkeypatch)
    copilot_cli.read_status(home, token=TOKEN)
    [call] = calls(log)
    scratch = Path(call["home"])
    assert call["argv"][call["argv"].index("--log-dir") + 1] == str(scratch / "logs")
    assert not scratch.exists()  # the log went with the call's scratch
    assert not (home / "logs").exists()
    assert (home / "config.json").read_text(encoding="utf-8").startswith("//")
    assert host_login.copilot_offenders(home) == []


def test_the_status_snapshot_holds_no_secret(home):
    """testing-harness spec: Status snapshot holds no secret."""
    copilot_cli.write_snapshot(home, status_of("status-ok"))
    copilot_cli.record_stop(home, "approval", "first run not yet approved")
    data = json.loads((home / copilot_cli.QUOTA_FILE).read_text(encoding="utf-8"))
    assert set(data) == {"plan_class", "token_based_billing", "snapshot", "overage_permitted",
                         "overage_count", "overage_entitlement", "remaining_pct", "reset_date",
                         "stop"}
    text = json.dumps(data)
    for secret in ("fixture-login-octocat", "fixture-org", "FIXTURE_REPLY_ONLY", TOKEN):
        assert secret not in text
    copilot_cli.write_snapshot(home, status_of("status-low"))  # a new snapshot keeps the stop
    assert copilot_cli.read_stop(home)["kind"] == "approval"


def h(events: list[dict]) -> dict:
    return copilot_cli.harness_record(events)


@pytest.mark.parametrize(("name", "named"), [
    ("over-cap", "more than twice its cap"),
    ("zero-nano", "zero consumption"),
    ("soft-cap", "reached limit"),
    ("session-limits", "reached limit"),
])
def test_billing_after_flags_and_stops(name, named):
    """testing-harness spec: Consumption out of bounds; Soft cap reached records a stop."""
    events = stream(name)
    problem, stop = copilot_cli.billing_after(h(events)["before"], h(events)["after"], events, 30)
    assert stop
    assert problem.untested
    assert named in problem.message
    assert problem.billing
    assert problem.message.endswith(f"{NOTE}.")


def test_a_reached_soft_cap_is_reported_in_the_template_and_its_stop_names_the_cap():
    """testing-harness spec: Soft cap reached records a stop — a billing stop
    naming the cap, and the result in the one refusal template."""
    assessment = copilot_cli.assess(stream("soft-cap"))
    message = assessment.problem.message
    assert assessment.problem.untested
    assert "limit reached, not a result" in message
    assert "credit cap 30" in message
    assert "31.4 of 30 credits" in message
    assert message.endswith(f"{NOTE}.")
    [cause] = [cause for kind, cause in assessment.stops if kind == "billing"]
    assert "credit cap 30" in cause
    assert "31.4 of 30 credits" in cause
    limit = copilot_cli.assess(stream("quota-error")).problem.message
    assert limit.startswith("untested: ")
    assert limit.endswith(f"{NOTE}.")


def test_a_shutdown_without_readable_consumption_stops_and_reports_no_credits():
    """A shutdown record whose `totalNanoAiu` is missing leaves the consumption
    unreadable: untested with a billing stop, and the credits read as absent,
    never as zero."""
    events = stream("success")
    shutdown = next(e for e in events if e["type"] == "copilot.shutdown")
    del shutdown["totalNanoAiu"], shutdown["modelMetrics"]
    assert copilot_cli.credits_used(events) is None
    problem, stop = copilot_cli.billing_after(h(events)["before"], h(events)["after"], events, 30)
    assert stop
    assert problem.untested
    assert "no readable consumption" in problem.message
    assert copilot_cli.assess(events).stops[0][0] == "billing"
    telemetry = copilot_cli.copilot_read(events, Namespace(model="copilot-fixture-a",
                                                           effort=None)).telemetry
    assert (telemetry["ai_credits"], telemetry["notional_usd"]) == (None, None)


def test_billing_after_overage_growth_and_an_unavailable_read_stop():
    """testing-harness spec: Overage grew during a run; Status read after the run
    unavailable."""
    events = stream("success")
    grown = {**h(events)["after"], "overage_count": 2}
    problem, stop = copilot_cli.billing_after(h(events)["before"], grown, events, 30)
    assert stop
    assert "grew from 0 to 2" in problem.message
    problem, stop = copilot_cli.billing_after(h(events)["before"], None, events, 30)
    assert stop
    assert "cannot be ruled out" in problem.message
    assert copilot_cli.billing_after(h(events)["before"], h(events)["after"], events, 30) == (
        None, False)


def test_a_missing_shutdown_is_a_runner_failure_with_a_billing_stop():
    """testing-harness spec: Copilot session without a shutdown record."""
    events = stream("no-shutdown")
    problem, stop = copilot_cli.billing_after(h(events)["before"], h(events)["after"], events, 30)
    assert stop
    assert not problem.untested
    assert problem.final
    assessment = copilot_cli.assess(events)
    assert not assessment.problem.untested
    assert "consumption cannot be read" in assessment.problem.message
    assert assessment.stops[0][0] == "billing"


def test_a_quota_error_is_untested_without_a_stop():
    """testing-harness spec: Copilot limit reached is not a result."""
    assessment = copilot_cli.assess(stream("quota-error"))
    assert assessment.problem.untested
    assert "limit reached, not a result" in (
        assessment.problem.message)
    assert not [kind for kind, _ in assessment.stops if kind == "billing"]


class Spy:
    """`subprocess.Popen` that records each start and then starts it for real."""

    def __init__(self):
        self.calls: list[list[str]] = []
        self.real = subprocess.Popen

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        return self.real(argv, **kwargs)


@POSIX
@pytest.mark.parametrize(("kind", "untested_kind", "remedy"), [
    ("billing", "subscription", "github.com/settings/billing"),
    ("isolation", "isolation", "read the run's findings"),
    ("approval", "precondition", "approve the next run"),
])
def test_a_recorded_stop_refuses_the_next_run_before_any_child(kind, untested_kind, remedy,
                                                              home, tmp_path, monkeypatch):
    """testing-harness spec: Recorded stop refuses later runs; First run after a
    login waits for approval. Measured against a fake client that would answer
    `--version`: no Copilot process starts at all, the version check's included."""
    copilot_cli.record_stop(home, kind, f"a synthetic {kind} cause")
    log = fake_copilot(tmp_path, monkeypatch)
    popen = Spy()
    monkeypatch.setattr(copilot_cli.subprocess, "Popen", popen)
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.isolated_home(None, Namespace())
    assert refused.value.kind == untested_kind
    assert f"a synthetic {kind} cause" in refused.value.message
    assert remedy.lower() in refused.value.message.lower()
    assert host_login.CLEAR_STOP_COMMAND in refused.value.message
    assert popen.calls == []
    assert calls(log) == []


def held_then(action):
    """`host_login.run_lock` that runs `action` once the lock is taken: what a
    login or another run did while this run waited on the lock."""
    real = host_login.run_lock

    @contextmanager
    def run_lock(home_dir, *args, **kwargs):
        with real(home_dir, *args, **kwargs) as fd:
            action()
            yield fd

    return run_lock


@POSIX
@pytest.mark.parametrize(("kind", "untested_kind"), [
    ("billing", "subscription"), ("isolation", "isolation"), ("approval", "precondition")])
def test_a_stop_recorded_while_the_run_waited_on_the_lock_refuses_it(kind, untested_kind, home,
                                                                     tmp_path, monkeypatch):
    """testing-harness spec: Recorded stop refuses later runs — a stop another
    run or a login recorded after this run's checks before the lock is read
    again under the lock, before any child."""
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch)
    monkeypatch.setattr(host_login, "run_lock", held_then(
        lambda: copilot_cli.record_stop(home, kind, f"a synthetic {kind} cause")))
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                effort=None, cap=30, timeout=30, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    assert refused.value.kind == untested_kind
    assert f"a synthetic {kind} cause" in refused.value.message
    assert calls(log) == []


@POSIX
def test_the_token_is_read_under_the_lock(home, tmp_path, monkeypatch):
    """A login that replaced the token while the run waited on the lock: every
    child carries the new token, never the one read before the lock."""
    skip_scan(monkeypatch)
    second = "github_pat_SECOND_SYNTHETIC_TEST_ONLY"
    log = fake_copilot(tmp_path, monkeypatch, token=second)
    monkeypatch.setattr(host_login, "run_lock", held_then(
        lambda: host_login.token_path(home).write_text(second + "\n", encoding="utf-8")))
    events = copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                     effort=None, cap=30, timeout=30, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    assert calls(log)
    assert all(c["token_ok"] for c in calls(log))
    assert copilot_cli.run_problem(events) is None


@pytest.mark.parametrize("text", ["{not json", "[1, 2]", '{"stop": "billing"}', '{"stop": {}}',
                                  '{"stop": null}'])
def test_an_unreadable_stop_record_refuses_rather_than_reads_as_none(text, home):
    """A damaged stop record is a stop: it refuses with the clear-stop remedy, a
    new snapshot keeps it, and the clear option removes it."""
    (home / copilot_cli.QUOTA_FILE).write_text(text, encoding="utf-8")
    problem = copilot_cli.stop_problem(copilot_cli.read_stop(home))
    assert problem is not None
    assert "cannot be read" in problem.cause
    assert host_login.CLEAR_STOP_COMMAND in problem.remedy
    copilot_cli.write_snapshot(home, status_of("status-ok"))
    assert copilot_cli.read_stop(home)["kind"] == "billing"
    assert copilot_cli.clear_stop(home) is not None
    assert copilot_cli.read_stop(home) is None
    assert copilot_cli.stop_problem(copilot_cli.read_stop(home)) is None


def test_a_stop_record_that_is_no_file_refuses(home):
    (home / copilot_cli.QUOTA_FILE).mkdir()
    assert "cannot be read" in copilot_cli.stop_problem(copilot_cli.read_stop(home)).cause


def test_stops_append_causes_and_keep_the_stronger_kind(home):
    copilot_cli.record_stop(home, "approval", "first")
    copilot_cli.record_stop(home, "billing", "second")
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "billing"
    assert stop["cause"] == "first; second"
    assert copilot_cli.clear_stop(home)["kind"] == "billing"
    assert copilot_cli.read_stop(home) is None
    assert copilot_cli.clear_stop(home) is None


@pytest.mark.parametrize("cap", [None, 29, 20])
def test_the_credit_cap_is_required_and_at_least_thirty(cap, monkeypatch, capsys):
    """testing-harness spec: Credit cap required."""
    monkeypatch.setattr(claude_runner.tempfile, "mkdtemp",
                        lambda *_a, **_k: pytest.fail("staged before the usage error"))
    argv = ["check_report", "--host", "copilot", "--model", "copilot-fixture-a"]
    with pytest.raises(SystemExit) as usage:
        claude_runner.main([*argv, *(["--max-ai-credits", str(cap)] if cap is not None else [])])
    assert usage.value.code == claude_runner.EXIT_USAGE
    assert "--max-ai-credits" in capsys.readouterr().err


# ---------- 3.5: the command, the scan, the rosters, the sandbox ------------------------------

FORBIDDEN_FLAGS = ("--allow-all-urls", "--add-dir", "--plugin-dir", "--allow-all-paths",
                   "--enable-memory", "--share", "--agent", "--resume", "--continue")


def flag_values(argv: list[str], prefix: str) -> list[str]:
    return [a.split("=", 1)[1] for a in argv if a.startswith(prefix + "=")]


@pytest.mark.parametrize("name", sorted(claude_runner.SCENARIOS))
def test_the_command_matches_decision_8_for_every_scenario(name):
    """testing-harness spec: Copilot tools by scenario."""
    scenario = claude_runner.SCENARIOS[name]
    argv = copilot_cli.command(scenario, "a request", model="copilot-fixture-a", effort=None,
                               session_id="s-1", log_dir=PurePosixPath("/scratch/logs"),
                               cap=30)
    [tools] = flag_values(argv, "--available-tools")
    offered = tools.split(",")
    assert ("task" in offered) is bool(scenario.get("helpers"))
    network = copilot_cli.needs_network(scenario)
    assert ("web_fetch" in offered) is network
    hosts = flag_values(argv, "--allow-url")
    assert hosts == copilot_cli.url_hosts(scenario)
    assert bool(hosts) is network
    if scenario.get("serve"):
        assert "127.0.0.1" in hosts
    for flag in FORBIDDEN_FLAGS:
        assert not any(a == flag or a.startswith(flag + "=") for a in argv), flag
    for flag in ("--no-auto-login", "--sandbox", f"--secret-env-vars={COPILOT.token_env}",
                 "--disable-builtin-mcps", "--no-custom-instructions", "--no-remote",
                 "--no-remote-export", "--no-auto-update"):
        assert flag in argv
    assert argv[argv.index("--auth-token-env") + 1] == COPILOT.token_env  # task 7.4b
    assert argv[argv.index("--max-ai-credits") + 1] == "30"
    assert flag_values(argv, "--deny-tool") == list(copilot_cli.DENIED_TOOLS)
    assert "--reasoning-effort" not in argv
    assert "--effort" not in argv
    assert argv[argv.index("--model") + 1] == "copilot-fixture-a"
    assert "--session-id=s-1" in argv
    assert argv[argv.index("-p") + 1] == "a request"


def test_the_effort_appears_only_when_requested():
    argv = copilot_cli.command({"skill": "proposal-check"}, "r", model="m", effort="high",
                               session_id="s", log_dir=PurePosixPath("/l"), cap=40)
    assert argv[argv.index("--reasoning-effort") + 1] == "high"


def test_the_three_scenarios_of_the_spec():
    """testing-harness spec: Copilot tools by scenario — none, supervise, served fixture."""
    plain, supervise, served = (claude_runner.SCENARIOS[n] for n in (
        "check_report", "supervise_feedback", "ideate_scoped"))
    tools = {name: flag_values(copilot_cli.command(s, "r", model="m", effort=None, session_id="s",
                                                   log_dir=PurePosixPath("/l"), cap=30),
                               "--available-tools")[0].split(",")
             for name, s in (("plain", plain), ("supervise", supervise), ("served", served))}
    assert "task" not in tools["plain"]
    assert "web_fetch" not in tools["plain"]
    assert "task" in tools["supervise"]
    assert "web_fetch" in tools["served"]
    assert copilot_cli.url_hosts(served) == ["127.0.0.1"]


_HOST = re.compile(r"https?://([A-Za-z0-9.-]+)")


def test_every_host_in_the_network_skills_scripts_is_in_the_table():
    tabled = {h for hosts in copilot_cli.SKILL_HOSTS.values() for h in hosts}
    tabled |= set(copilot_cli.NOT_CONTACTED)
    for skill in ("proposal-import", "proposal-lit-search", "proposal-reverse"):
        for path in sorted((REPO / "skills" / skill / "scripts").glob("*.py")):
            for host in _HOST.findall(path.read_text(encoding="utf-8")):
                assert host in tabled, f"{path.name}: {host}"


ACCOUNT = PurePosixPath("/home/operator")
REPO_P = PurePosixPath("/home/operator/src/thesis-proposal-skills")
WS_P = PurePosixPath("/tmp/devrun-x")


@pytest.mark.parametrize("rel", copilot_cli.SCAN_PATHS)
def test_scan_parents_reports_each_listed_file_at_parent_and_workspace(rel):
    """testing-harness spec: Instruction file above the workspace."""
    parent = PurePosixPath("/tmp") / rel
    assert copilot_cli.scan_parents(WS_P, lambda p: p == parent, account=ACCOUNT,
                                    repo=REPO_P) == [str(parent)]
    inside = WS_P / rel
    found = copilot_cli.scan_parents(WS_P, lambda p: p == inside, account=ACCOUNT, repo=REPO_P)
    assert found == ([] if rel == copilot_cli.STAGED_DIR else [str(inside)])


def test_scan_parents_refuses_a_workspace_in_the_home_or_the_repository():
    for ws in (ACCOUNT / "work", REPO_P / "tmp"):
        found = copilot_cli.scan_parents(ws, lambda _p: False, account=ACCOUNT, repo=REPO_P)
        assert found
        assert "lies inside" in found[0]
    assert copilot_cli.scan_parents(WS_P, lambda _p: False, account=ACCOUNT, repo=REPO_P) == []


def test_scan_problem_names_a_real_parent_file(tmp_path):
    ws = tmp_path / "parent" / "ws"
    (ws / ".agents" / "skills" / "proposal-check").mkdir(parents=True)
    assert copilot_cli.scan_problem(ws, account=tmp_path / "account", repo=REPO) is None
    (tmp_path / "parent" / "AGENTS.md").write_text("instructions", encoding="utf-8")
    problem = copilot_cli.scan_problem(ws, account=tmp_path / "account", repo=REPO)
    assert problem.kind == "isolation"
    assert "AGENTS.md" in problem.cause


def test_scan_refuses_a_workspace_in_a_temporary_directory(tmp_path):
    """testing-harness spec: Copilot workspace outside the system temporary
    directory — the scan is the backstop for the work directory (D-b)."""
    found = copilot_cli.scan_parents(WS_P, lambda _p: False, account=ACCOUNT, repo=REPO_P,
                                     temps=[PurePosixPath("/tmp")])
    assert found == [f"the workspace {WS_P} lies inside /tmp"]
    ws = tmp_path / "ws"
    ws.mkdir()
    problem = copilot_cli.scan_problem(ws, account=tmp_path / "account", repo=REPO,
                                       temps=[tmp_path])
    assert problem.kind == "isolation"
    assert f"lies inside {tmp_path.resolve()}" in problem.cause


# ---------- the work directory (Decision 7, the user's decision D-b) ---------------------------

STATE_P = PurePosixPath("/srv/devrun/state")
RUNTIME_P = PurePosixPath("/run/user/1000")
RUNTIME_WORK = RUNTIME_P / "thesis-proposal-dev" / "work" / "copilot"
AVOID = [ACCOUNT, REPO_P, PurePosixPath("/tmp")]


@pytest.mark.parametrize(("state", "runtime", "expected"), [
    (STATE_P, RUNTIME_P, STATE_P / "work" / "copilot"),  # the state root, where it may
    (ACCOUNT / ".local/state/thesis-proposal-dev", RUNTIME_P, RUNTIME_WORK),  # the default
    (PurePosixPath("/tmp/state"), RUNTIME_P, RUNTIME_WORK),
    (REPO_P / "state", RUNTIME_P, RUNTIME_WORK),
    (ACCOUNT / ".local/state/thesis-proposal-dev", None, None),  # nowhere
])
def test_choose_work_root_keeps_out_of_the_home_the_repository_and_temp(state, runtime, expected):
    """Pure: under the state root where it lies outside the operator's home
    (whose own skills the client's parent walk lists), the repository and the
    temporary directories; otherwise under the per-user runtime directory."""
    assert copilot_cli.choose_work_root(state, runtime, avoid=AVOID) == expected


def _mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


@POSIX
def test_work_root_under_the_state_root_is_made_owner_only(tmp_path, monkeypatch):
    state = tmp_path / "state"
    monkeypatch.setenv(host_login.STATE_VAR, str(state))
    root = copilot_cli.work_root()
    assert root == state.resolve() / "work" / "copilot"
    assert [_mode(p) for p in (state, state / "work", root)] == [0o700, 0o700, 0o700]
    assert copilot_cli.work_root() == root  # an existing one is reused
    assert copilot_cli.work_problem() is None


@POSIX
def test_work_root_falls_back_to_the_runtime_directory(tmp_path, monkeypatch):
    """The default layout: the state root lies in the account home, so the
    work directory is the per-user runtime directory's."""
    account = tmp_path / "account"
    state = account / ".local" / "state" / "thesis-proposal-dev"
    runtime = tmp_path / "run-user-1000"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv(host_login.STATE_VAR, str(state))
    monkeypatch.setattr(host_login, "account_home", lambda _uid=None: account)
    monkeypatch.setattr(copilot_cli, "runtime_dir", lambda _uid=None: runtime)
    root = copilot_cli.work_root()
    assert root == runtime / "thesis-proposal-dev" / "work" / "copilot"
    assert _mode(runtime / "thesis-proposal-dev") == 0o700
    assert not state.exists()  # nothing made under the home


def test_without_a_work_directory_nothing_is_made_and_the_run_is_refused(tmp_path, monkeypatch):
    """testing-harness spec: No Copilot work directory."""
    account = tmp_path / "account"
    state = account / ".local" / "state" / "thesis-proposal-dev"
    monkeypatch.setenv(host_login.STATE_VAR, str(state))
    monkeypatch.setattr(host_login, "account_home", lambda _uid=None: account)
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.work_root()
    assert refused.value.kind == "precondition"
    assert str(state) in refused.value.message
    assert "/run/user/<uid>" in refused.value.message
    assert copilot_cli.work_problem().kind == "precondition"
    assert not account.exists()


def test_a_refused_state_root_gets_no_work_directory(monkeypatch):
    """The location check comes first: an override inside the repository is
    refused with its own remedy, and nothing is created there."""
    state = REPO / ".devrun-test-state-never-made"
    monkeypatch.setenv(host_login.STATE_VAR, str(state))
    problem = copilot_cli.work_problem()
    assert "inside the repository" in problem.cause
    assert not state.exists()


def test_runtime_dir_is_only_a_private_directory_of_the_user(monkeypatch):
    uid = 4242

    def lstat(mode: int, owner: int = uid):
        return lambda _path: os.stat_result((mode, 0, 0, 1, owner, 0, 0, 0, 0, 0))

    monkeypatch.setattr(copilot_cli.os, "lstat", lstat(0o040700))
    assert REAL_RUNTIME_DIR(uid) == Path(f"/run/user/{uid}")
    for wrong in (lstat(0o040755), lstat(0o040700, owner=0), lstat(0o120777)):
        monkeypatch.setattr(copilot_cli.os, "lstat", wrong)
        assert REAL_RUNTIME_DIR(uid) is None

    def missing(_path):
        raise FileNotFoundError

    monkeypatch.setattr(copilot_cli.os, "lstat", missing)
    assert REAL_RUNTIME_DIR(uid) is None


def test_the_copilot_workspace_is_made_in_the_work_directory(tmp_path, monkeypatch):
    """testing-harness spec: Copilot workspace outside the system temporary
    directory — a run's (and `--preflight-only`'s) workspace comes from the
    host's work directory; Claude's and Codex's stay where they were."""
    monkeypatch.setenv(host_login.STATE_VAR, str(tmp_path / "state"))
    ws = claude_runner.new_workspace(claude_runner.HOSTS["copilot"], "check_report")
    assert ws.parent == copilot_cli.work_root()
    assert ws.name.startswith("devrun-check_report-")
    assert _mode(ws) & 0o077 == 0
    other = claude_runner.new_workspace(claude_runner.HOSTS["codex"], "check_report")
    try:
        assert other.parent == Path(tempfile.gettempdir())
    finally:
        shutil.rmtree(other)


@pytest.mark.parametrize("preflight", [False, True])
def test_a_run_without_a_work_directory_is_untested_and_makes_nothing(preflight, tmp_path,
                                                                      monkeypatch):
    account = tmp_path / "account"
    state = account / ".local" / "state" / "thesis-proposal-dev"
    monkeypatch.setenv(host_login.STATE_VAR, str(state))
    monkeypatch.setattr(host_login, "account_home", lambda _uid=None: account)
    monkeypatch.setattr(claude_runner.tempfile, "mkdtemp",
                        lambda *_a, **_k: pytest.fail("a workspace was made"))
    argv = ["check_report", "--host", "copilot", "--model", "copilot-fixture-a",
            "--max-ai-credits", "30", *(["--preflight-only"] if preflight else [])]
    assert claude_runner.main(argv) == claude_runner.EXIT_UNTESTED
    assert not account.exists()


def test_the_status_command_without_a_work_directory_reads_nothing(home, monkeypatch):
    gap = LoginProblem("no work directory", "fix it", COPILOT.name, "precondition")
    monkeypatch.setattr(copilot_cli, "work_problem", lambda _environ=None: gap)
    monkeypatch.setattr(copilot_cli, "installed_version",
                        lambda *_a: pytest.fail("a child started"))
    monkeypatch.setattr(copilot_cli, "read_status", lambda *_a, **_k: pytest.fail("a read ran"))
    lines, problem = copilot_cli.status(home, os.environ)
    assert problem is gap
    assert lines["auth_type"] == "unknown"


def test_roster_problem_names_the_extra_skill_and_server():
    """testing-harness spec: Skill roster off."""
    staged = ["proposal-check"]
    assert copilot_cli.roster_problem(load("skills-ok"), load("mcp-ok"), staged) is None
    extra = copilot_cli.roster_problem(load("skills-extra"), load("mcp-ok"), staged)
    assert extra.kind == "isolation"
    assert "parent-notes (source inherited)" in extra.cause
    server = copilot_cli.roster_problem(load("skills-ok"), load("mcp-extra"), staged)
    assert server.kind == "isolation"
    assert "docs" in server.cause
    missing = copilot_cli.roster_problem(load("skills-ok"), load("mcp-ok"),
                                         ["proposal-check", "proposal-import"])
    assert missing.kind == "precondition"
    assert "proposal-import" in missing.cause
    assert copilot_cli.roster_problem("not json", load("mcp-ok"), staged).kind == "precondition"


def test_windows_is_a_usage_error(monkeypatch, capsys):
    """testing-harness spec: Copilot on Windows."""
    monkeypatch.setattr(claude_runner.sys, "platform", "win32")
    monkeypatch.setattr(claude_runner.tempfile, "mkdtemp",
                        lambda *_a, **_k: pytest.fail("staged before the usage error"))
    with pytest.raises(SystemExit) as usage:
        claude_runner.main(["check_report", "--host", "copilot", "--model", "copilot-fixture-a",
                            "--max-ai-credits", "30"])
    assert usage.value.code == claude_runner.EXIT_USAGE
    assert "Windows" in capsys.readouterr().err


@pytest.mark.parametrize("tool", copilot_cli.SANDBOX_TOOLS)
def test_a_missing_sandbox_tool_is_an_untested_precondition(tool):
    """testing-harness spec: Sandbox tool missing."""
    problem = copilot_cli.sandbox_problem(lambda name: None if name == tool else f"/usr/bin/{name}",
                                          platform="linux")
    assert problem.kind == "precondition"
    assert f"install {tool}" in problem.remedy
    assert copilot_cli.sandbox_problem(lambda _name: "/usr/bin/x", platform="linux") is None
    assert copilot_cli.sandbox_problem(lambda _name: None, platform="darwin") is None


@pytest.mark.parametrize("name", ["sandbox-ignored", "sandbox-unreported"])
def test_a_sandbox_not_reported_active_is_untested_and_stops(name):
    """testing-harness spec: Sandbox ignored."""
    assessment = copilot_cli.assess(stream(name))
    assert assessment.problem.untested
    assert assessment.problem.kind == "isolation"
    assert "sandbox" in assessment.problem.message
    assert ("isolation", "the sandbox was ignored or not reported active") in assessment.stops


@pytest.mark.parametrize(("name", "named"), [("auth-error", "fine-grained token"),
                                             ("quota-error", "limit reached")])
def test_a_run_with_no_shell_call_records_an_isolation_stop_whatever_ended_it(name, named):
    """testing-harness spec: Sandbox ignored — a run that lacks the client's
    report that the sandbox is active stops, a run a session error ended
    included; the error still leads the message."""
    assessment = copilot_cli.assess(stream(name))
    assert ("isolation", "the sandbox was ignored or not reported active") in assessment.stops
    assert named in assessment.problem.message


def probe(name: str) -> tuple[object, list[ProbeResult]]:
    data = load(name)
    return data["host_support"]["supported"], [ProbeResult(**r) for r in data["results"]]


@pytest.mark.parametrize(("name", "target", "kind"), [
    ("probe-token-readable", "the token file", "isolation"),
    ("probe-environ-readable", "the client process's environment", "isolation"),
    ("probe-harness-environ-readable", "the harness process's environment", "isolation"),
    ("probe-gh-token", "the GitHub CLI's token", "isolation"),
    ("probe-git-credential", "git's stored credential", "isolation"),
    ("probe-skill-fails", "a staged skill script", "precondition"),
])
def test_probe_problem_refuses_naming_the_target(name, target, kind):
    """testing-harness spec: Confinement probe reaches a credential."""
    supported, results = probe(name)
    problem = copilot_cli.probe_problem(results, supported)
    assert problem.kind == kind
    assert target in problem.cause
    assert not re.search(r"\breadable\b|\bdenied\b", refusal(problem))  # no probe output


def test_probe_problem_passes_a_clean_probe_and_refuses_unsandboxed_or_missing():
    supported, results = probe("probe-ok")
    assert copilot_cli.probe_problem(results, supported) is None
    loose = [ProbeResult(r.name, r.output, None if r.name == "python" else True) for r in results]
    assert "not report the probe's commands as sandboxed" in copilot_cli.probe_problem(
        loose).cause
    assert copilot_cli.probe_problem(results[:2]).kind == "precondition"
    assert copilot_cli.probe_problem(results, False).kind == "precondition"
    # a sandbox not applied refuses for isolation, whatever rows came back
    unapplied = copilot_cli.probe_problem(results, True, "session.options.update gave no answer")
    assert unapplied.kind == "isolation"
    assert "session.options.update gave no answer" in unapplied.cause


def test_the_measured_row_is_printed_not_refused_but_must_be_sandboxed():
    """Decision 13, network: the namespace row is recorded for K6, not yet a
    rule — whatever it reads, it refuses nothing — but a measured command the
    client did not report as sandboxed still refuses."""
    supported, results = probe("probe-ok")
    assert set(copilot_cli.MEASURED_TARGETS) == {"net_ns"}
    assert set(copilot_cli.MEASURED_TARGETS) <= {r.name for r in results}
    widened = [ProbeResult(r.name, "shared" if r.name == "net_ns" else r.output, r.sandboxed)
               for r in results]
    assert copilot_cli.probe_problem(widened, supported) is None
    loose = [ProbeResult(r.name, r.output, None if r.name == "net_ns" else True) for r in results]
    assert "(net_ns)" in copilot_cli.probe_problem(loose, supported).cause


@pytest.mark.parametrize(("row", "word", "named"), [
    ("host_tmp", "readable", "a file in the host's /tmp"),
    ("tmp_write", "writable", "a write into the host's /tmp"),
    ("host_tmp", "unknown", "a file in the host's /tmp"),
])
def test_the_host_tmp_rows_refuse_unless_denied(row, word, named):
    """testing-harness spec: Host temporary directory denied to the sandboxed
    shell (the user's decision D-b): K6 read `host_tmp readable` and
    `tmp_write writable`, which now refuse for isolation, naming the
    directory and never any output; a missing row is a probe without an
    answer."""
    supported, results = probe("probe-ok")
    assert set(copilot_cli.TMP_TARGETS) <= set(copilot_cli.REQUIRED_PROBES)
    opened = [ProbeResult(r.name, word if r.name == row else r.output, r.sandboxed)
              for r in results]
    problem = copilot_cli.probe_problem(opened, supported)
    assert problem.kind == "isolation"
    assert named in problem.cause
    assert word not in refusal(problem).replace(named, "")
    missing = copilot_cli.probe_problem([r for r in results if r.name != row], supported)
    assert missing.kind == "precondition"
    assert row in missing.cause


def test_the_write_row_is_judged_on_the_host(tmp_path):
    """`tmp_write` reads `writable` only when the host sees the file: a write
    into the sandbox's own overlay succeeds and reaches nothing."""
    with copilot_cli.probe_host(tmp_path) as host:
        assert host.sentinel.parent == tmp_path
        assert host.sentinel.is_file()
        assert host.marker.parent == tmp_path
        assert not host.marker.exists()
        assert copilot_cli._row_output("tmp_write", {"output": "0\n"}, host) == "denied"
        host.marker.write_text("", encoding="utf-8")
        assert copilot_cli._row_output("tmp_write", {"output": "1\n"}, host) == "writable"
        assert copilot_cli._row_output("host_tmp", {"output": "x\nreadable\n"}, host) == "readable"
    assert list(tmp_path.iterdir()) == []  # both removed
    with copilot_cli.probe_host(tmp_path / "missing") as host:
        assert (host.sentinel, host.marker) == (None, None)


GATED =("--sandbox/--no-sandbox requires the sandbox feature, available in experimental mode "
         "(run with --experimental or enable /experimental). Ignoring for this session.")


def _start(call: str, tool: str = "bash") -> dict:
    return {"type": "tool.execution_start", "data": {"toolCallId": call, "toolName": tool}}


def _complete(call: str, **data) -> dict:
    return {"type": "tool.execution_complete", "data": {"toolCallId": call, **data}}


@pytest.mark.parametrize(("events", "breach"), [
    ([_start("t1"), _complete("t1", sandboxed=True)], None),
    ([_start("t1", "view"), _complete("t1")], None),  # file tools are not watched
    ([_start("t1"), _complete("t1")], copilot_cli.UNCONFINED_CALL),
    ([_start("t1"), _complete("t1", sandboxed=False)], copilot_cli.UNCONFINED_CALL),
    ([_start("t1", "local_shell"), _complete("t1", sandboxed="true")],
     copilot_cli.UNCONFINED_CALL),
    ([{"type": "session.warning", "data": {"message": "Sandboxing is enabled but is not "
                                                      "supported on this host"}}],
     copilot_cli.SANDBOX_NOTICE),
    ([{"type": "session.warning", "data": {"message": GATED}}], None),
])
def test_the_live_watch_names_the_first_unconfined_shell_call(events, breach):
    """testing-harness spec: Unconfined shell call stops the run — pure over the
    stdout events: a shell completion not reported sandboxed, or a sandbox
    warning, is a breach; a sandboxed one, a file tool and the expected notice
    that the gated `--sandbox` flag was dropped are not."""
    watch = copilot_cli.ConfinementWatch()
    found = [watch.event_line(json.dumps(e)) for e in events]
    assert watch.breach == breach
    assert any(found) is (breach is not None)
    assert watch.event_line("not json\n") is False


def test_the_live_watch_reads_stderr_and_keeps_the_first_breach():
    watch = copilot_cli.ConfinementWatch()
    assert watch.stderr_line(GATED + "\n") is False
    assert watch.breach is None
    assert watch.stderr_line("Sandboxing is enabled but not supported on this platform: x\n")
    assert watch.breach == copilot_cli.SANDBOX_NOTICE
    watch.event_line(json.dumps(_start("t9")))
    assert watch.event_line(json.dumps(_complete("t9")))
    assert watch.breach == copilot_cli.SANDBOX_NOTICE  # the first one kept
    assert not copilot_cli.sandbox_warned(GATED)


def _file_start(call: str, tool: str, **arguments) -> dict:
    return {"type": "tool.execution_start",
            "data": {"toolCallId": call, "toolName": tool, "arguments": arguments}}


@POSIX
def test_the_live_watch_stops_a_file_tool_pointed_outside_the_workspace(tmp_path):
    """testing-harness spec: File tool outside the workspace stops the run. The
    client's file tools run in
    its own process, outside the sandbox, so a file tool whose path — links
    resolved on the harness's side — leaves the workspace is a breach; one
    inside it is not, and without a workspace the watch checks no path."""
    ws = tmp_path / "ws"
    (ws / "sub").mkdir(parents=True)
    secret = tmp_path / "secret"
    secret.write_text("synthetic", encoding="utf-8")
    (ws / "proposal-review.md").symlink_to(secret)
    patch = "*** Begin Patch\n*** Add File: notes.md\n*** Update File: /etc/hosts\n*** End Patch"
    cases = [
        (_file_start("f1", "view", path="sub"), None),
        (_file_start("f2", "view", path=str(ws / "sub")), None),
        (_file_start("f3", "glob", pattern="**/*.md"), None),  # no path: the workspace
        (_file_start("f4", "view", path=str(secret)), copilot_cli.OUTSIDE_FILE),
        (_file_start("f5", "view", path="proposal-review.md"), copilot_cli.OUTSIDE_FILE),
        (_file_start("f6", "grep", path="../"), copilot_cli.OUTSIDE_FILE),
        (_file_start("f7", "create", path="~/.bashrc"), copilot_cli.OUTSIDE_FILE),
        (_file_start("f8", "apply_patch", input=patch), copilot_cli.OUTSIDE_FILE),
        (_file_start("f9", "apply_patch", input=patch.replace("/etc/hosts", "a.md")), None),
    ]
    for event, breach in cases:
        assert copilot_cli.breach_of(event, set(), ws) == breach, event
        assert copilot_cli.breach_of(event, set()) is None  # no workspace, no path check
    mcp = _file_start("m1", "view", path=str(secret))
    mcp["data"]["mcpServerName"] = "github-mcp-server"
    assert copilot_cli.breach_of(mcp, set(), ws) is None
    watch = copilot_cli.ConfinementWatch(ws)
    assert watch.event_line(json.dumps(_file_start("f5", "view", path="proposal-review.md")))
    assert watch.breach == copilot_cli.OUTSIDE_FILE
    assert secret.read_text(encoding="utf-8") == "synthetic"


def test_a_run_the_watch_stopped_is_untested_for_isolation_and_stops():
    """testing-harness spec: Unconfined shell call stops the run — pure over the
    saved events: the harness record names the breach."""
    events = stream("success")
    harness = copilot_cli.harness_record(events)
    harness["confinement_breach"] = copilot_cli.UNCONFINED_CALL
    assessment = copilot_cli.assess(events)
    assert assessment.problem.untested
    assert assessment.problem.kind == "isolation"
    assert f"stopped at {copilot_cli.UNCONFINED_CALL}" in assessment.problem.message
    assert ("isolation", f"the run was stopped at {copilot_cli.UNCONFINED_CALL}") in (
        assessment.stops)


def test_the_probe_commands_print_one_word_and_name_no_output(tmp_path):
    account = tmp_path / "account"
    host = copilot_cli.ProbeHost("net:[4026531840]", tmp_path / "devrun-probe-tmp-x",
                                 tmp_path / "devrun-probe-write-x")
    commands = dict(copilot_cli.probe_commands(token_file=tmp_path / "copilot.token",
                                               server_pid=4242, harness_pid=4343,
                                               account=account, uid=1000,
                                               script=tmp_path / "check.py", host=host))
    assert set(commands) == {*copilot_cli.READ_TARGETS, *copilot_cli.AUTH_TARGETS, "python",
                             "skill_script", *copilot_cli.TMP_TARGETS,
                             *copilot_cli.MEASURED_TARGETS}
    for name in (*copilot_cli.READ_TARGETS, "host_tmp"):
        assert commands[name].endswith("&& echo readable || echo denied")
        assert ">/dev/null 2>&1" in commands[name]
    assert "/proc/4242/environ" in commands["client_environ"]
    assert "/proc/4343/environ" in commands["harness_environ"]
    assert "unix:path=/run/user/1000/bus" in commands["gh_token"]
    # git runs with the operator's own home, configuration, GitHub CLI directory
    # and session bus, so a configured credential helper is reached unless the
    # sandbox denies it; the child's scratch home holds none
    git = commands["git_credential"]
    for needle in (f"HOME={account}", f"XDG_CONFIG_HOME={account / '.config'}",
                   f"GH_CONFIG_DIR={account / '.config' / 'gh'}", "unix:path=/run/user/1000/bus",
                   "GIT_TERMINAL_PROMPT=0", "GIT_ASKPASS=/bin/false", "GCM_INTERACTIVE=never",
                   ">/dev/null 2>&1; echo $?"):
        assert needle in git, needle
    assert "'net:[4026531840]'" in commands["net_ns"]
    assert commands["net_ns"].count("echo ") == 3  # unknown, shared, private
    assert commands["tmp_write"] == f": > {host.marker} 2>/dev/null; echo $?"
    # without a host side, the host rows are left out (the /tmp ones then read
    # as no answer, test_the_host_tmp_rows_refuse_unless_denied)
    bare = dict(copilot_cli.probe_commands(token_file=tmp_path / "t", server_pid=1,
                                           harness_pid=2, account=account, uid=1000, script=None))
    assert not set(bare) & {*copilot_cli.MEASURED_TARGETS, *copilot_cli.TMP_TARGETS}


def test_no_scenario_prompt_names_a_skill_by_slash_command():
    """testing-harness spec: Scope — Copilot invokes a slash-named skill without a call."""
    for name, scenario in claude_runner.SCENARIOS.items():
        assert "/proposal-" not in str(scenario.get("request", "")), name


# ---------- 3.6: the readers ----------------------------------------------------------------


def test_copilot_tool_calls_map_every_row_of_decision_10():
    events = [
        *[{"type": "tool.execution_start", "data": {"toolCallId": f"c{i}", "toolName": name,
                                                    "arguments": args}}
          for i, (name, args) in enumerate([
              ("bash", {"command": "ls"}), ("write_bash", {}), ("edit", {"path": "a.md"}),
              ("create", {"path": "b.md"}), ("apply_patch", {}), ("view", {"path": "c.md"}),
              ("glob", {"pattern": "*.md"}), ("grep", {"pattern": "x"}),
              ("rg", {"pattern": "y"}), ("skill", {"skill": "plugin:proposal-check"}),
              ("task", {"prompt": "verify"}), ("web_fetch", {"url": "https://x"}),
              ("web_search", {"query": "q"}), ("report_intent", {}), ("update_todo", {}),
              ("local_shell", {"command": "pwd"})])],
        {"type": "tool.execution_start", "data": {"toolCallId": "m", "toolName": "docs-publish",
                                                  "mcpServerName": "docs",
                                                  "mcpToolName": "publish", "arguments": {}}},
    ]
    names = [name for name, _ in copilot_cli.copilot_tool_calls(events)]
    assert names == ["Bash", "Bash", "Edit", "Edit", "Edit", "Read", "Glob", "Grep", "Grep",
                     "Skill", "Agent", "WebFetch", "WebSearch", "Bash", "mcp__docs__publish"]
    calls_ = copilot_cli.copilot_tool_calls(events)
    assert calls_[9] == ("Skill", {"skill": "proposal-check"})
    assert calls_[10] == ("Agent", {"prompt": "verify"})


def test_a_failed_skill_call_is_an_attempt():
    """testing-harness spec: Failed skill call is an attempt."""
    names = [n for n, _ in copilot_cli.copilot_tool_calls(stream("skill-failed"))]
    assert "Skill" not in names
    assert "SkillAttempt" in names
    assert routing.route_from_events(stream("skill-failed")) is None


def test_a_skill_file_view_is_a_flagged_read_not_a_skill_call():
    """testing-harness spec: Skill file viewed on Copilot."""
    calls_ = copilot_cli.copilot_tool_calls(stream("skill-file-view"))
    assert ("Skill" not in [n for n, _ in calls_])
    read = next(payload for name, payload in calls_ if name == "Read")
    assert read["skill_file_read"] == "proposal-check"


def test_an_unknown_tool_is_untested():
    """testing-harness spec: Unknown Copilot tool."""
    assessment = copilot_cli.assess(stream("unknown-tool"))
    assert assessment.problem.kind == "precondition"
    assert "frobnicate" in (
        assessment.problem.message)
    assert ("copilot:frobnicate", {}) in copilot_cli.copilot_tool_calls(stream("unknown-tool"))


def test_routing_reads_the_copilot_shape():
    """testing-harness spec: Skill tool call read as Skill; Copilot subagent spawn;
    Copilot helper spawn counted."""
    assert routing.route_from_events(stream("success")) == "proposal-check"
    helper = stream("helper-spawn")
    calls_ = routing.tool_calls(helper)
    assert verdict_supervise_verifier(calls_)[0]
    single, why = verdict_single_context([n for n, _ in calls_], 0)
    assert not single
    assert "Agent" in why
    assert verdict_single_context([n for n, _ in calls_], 1)[0]


def test_copilot_read_reports_text_models_and_credits():
    """testing-harness spec: Copilot run reports credits, not cost."""
    events = stream("success")
    view = copilot_cli.copilot_read(events, Namespace(model="copilot-fixture-a", effort=None))
    assert view.final_text.startswith("The check of broken-format.md")
    assert (view.model, view.model_requested, view.cli_version) == (
        "copilot-fixture-a", "copilot-fixture-a", "1.0.91")
    t = view.telemetry
    assert t["cost_usd"] is None
    assert t["ai_credits"] == 12.0
    assert t["notional_usd"] == 0.12
    assert t["notional_basis"] == "copilot credits, not billed"
    assert (t["tokens_in"], t["tokens_out"], t["tokens_cache_read"], t["tokens_reasoning"]) == (
        21000, 1800, 15000, 400)
    assert (t["cap_credits"], t["overage_before"], t["overage_after"]) == (30, 0, 0)
    assert (t["remaining_before"], t["remaining_after"]) == (80.0, 79.2)
    assert copilot_cli.run_problem(events) is None


def test_creation_options_are_not_evidence():
    """testing-harness spec: Creation options are not evidence."""
    events = [e for e in stream("success") if e.get("type") not in (
        "assistant.message", "copilot.shutdown")]
    events.append({"type": "copilot.session_start", "copilotVersion": "1.0.91",
                   "selectedModel": "copilot-fixture-a", "reasoningEffort": "high"})
    view = copilot_cli.copilot_read(events, Namespace(model="copilot-fixture-a", effort="high"))
    assert view.model == "unreported"
    assert view.telemetry["effort_served"] == "requested, not verified"


def test_reduce_session_drops_system_text_and_extra_fields():
    raw = (STREAMS / "events-raw.jsonl").read_text(encoding="utf-8").splitlines()
    records = copilot_cli.reduce_session(raw)
    kinds = [r["type"] for r in records]
    assert kinds == ["copilot.session_start", "copilot.skill_invoked", "copilot.hook",
                     "copilot.model_change", "copilot.notice", "copilot.notice",
                     "copilot.shutdown"]
    text = json.dumps(records)
    for dropped in ("synthetic system prompt", "Please check my proposal", "SKILL.md body",
                    "selectedModel", "reasoningEffort", "systemTokens", "Synthetic answer"):
        assert dropped not in text
    assert records[1] == {"type": "copilot.skill_invoked", "name": "proposal-check",
                          "path": "__WS__/.agents/skills/proposal-check/SKILL.md",
                          "source": "project", "trigger": "agent-invoked"}
    assert set(records[-1]) == {"type", *copilot_cli.SHUTDOWN_KEYS}


@pytest.mark.parametrize(("name", "named"), [
    ("foreign-skill", "source inherited"),
    ("skills-unreported", "could not be confirmed"),
    ("mcp-call", "mcp__docs__publish"),
    ("mcp-connected", "MCP server docs connected"),
    ("hook-event", "hook event"),
])
def test_isolation_findings_after_the_run(name, named):
    """testing-harness spec: Foreign skill invoked on Copilot; Loaded skills
    unreported; MCP server on Copilot."""
    assessment = copilot_cli.assess(stream(name))
    assert assessment.problem.kind == "isolation"
    assert named in assessment.problem.message
    assert not assessment.stops


@pytest.mark.parametrize(("name", "named"), [
    ("model-differs", "copilot-fixture-b"),
    ("model-switch", "because of a rate limit"),
    ("effort-unapplied", "left unapplied"),
])
def test_model_and_effort_findings_are_untested_preconditions(name, named):
    """testing-harness spec: Served model differs on Copilot; Model switched by a
    rate limit."""
    problem = copilot_cli.run_problem(stream(name))
    assert problem.untested
    assert problem.kind == "precondition"
    assert named in problem.message


def test_a_helpers_second_model_does_not_make_the_run_untested():
    assert copilot_cli.run_problem(stream("helper-spawn")) is None


def test_each_task_call_is_cross_checked_with_its_subagent():
    """design Decision 10: a `task` call is read as `Agent`, cross-checked with
    `subagent.started` both ways, so the helper count the verdicts read holds."""
    events = stream("helper-spawn")
    unstarted = [e for e in events if e.get("type") != "subagent.started"]
    problem = copilot_cli.run_problem(unstarted)
    assert (problem.untested, problem.kind) == (True, "precondition")
    assert "t3" in problem.message
    stray = [*events, {"type": "subagent.started", "data": {"toolCallId": "t9",
                                                            "agentName": "extra"}}]
    problem = copilot_cli.run_problem(stray)
    assert (problem.untested, problem.kind) == (True, "precondition")
    assert "t9" in problem.message


def test_the_session_version_is_cross_checked_with_the_pinned_one():
    """design Decision 10: the CLI version the session file reports is the one
    the preflight checked."""
    events = stream("success")
    h(events)["cli_version"] = "1.0.91"
    assert copilot_cli.run_problem(events) is None
    next(e for e in events if e["type"] == "copilot.session_start")["copilotVersion"] = "1.0.92"
    problem = copilot_cli.run_problem(events)
    assert (problem.untested, problem.kind) == (True, "precondition")
    assert "1.0.92" in problem.message
    assert "1.0.91" in problem.message


@pytest.mark.parametrize(("name", "untested", "named"), [
    ("auth-error", True, "fine-grained token"),
    ("exit0-error", False, "model_call"),
    ("no-result", False, "no closing result line"),
])
def test_the_exit_mapping(name, untested, named):
    """testing-harness spec: Copilot token rejected during a run; Copilot exit code
    not trusted; No result line on Copilot."""
    problem = copilot_cli.run_problem(stream(name))
    assert problem.untested is untested
    assert named in problem.message
    if name == "auth-error":
        assert problem.message.endswith(f"{NOTE}.")
        assert "uv run poe host-login copilot --reset" in problem.message


def test_a_result_line_of_another_session_is_a_runner_failure():
    """design Decision 9: the result line's session is cross-checked."""
    events = stream("success")
    assert copilot_cli.session_problem(events) is None
    copilot_cli.harness_record(events)["session_id"] = "22222222-2222-4222-8222-222222222222"
    problem = copilot_cli.run_problem(events)
    assert not problem.untested
    assert "names the session 11111111" in problem.message


def test_a_runner_failure_explained_by_a_later_finding_becomes_untested():
    first = RunProblem("copilot failed: x", False)
    later = RunProblem("untested: y", True, "isolation")
    combined = copilot_cli.combine([first, None, later])
    assert combined.untested
    assert combined.kind == "isolation"
    assert "x" in combined.message
    final = RunProblem("no shutdown", False, final=True)
    assert not copilot_cli.combine([later, final]).untested
    assert copilot_cli.combine([]) is None


def test_a_timed_out_run_is_a_runner_failure_unless_its_events_say_more():
    failed = copilot_cli.CopilotRunFailed("copilot did not finish within 5s",
                                          stream("no-shutdown"))
    problem = copilot_cli.timeout_problem(failed)
    assert not problem.untested
    assert "did not finish" in problem.message
    over = copilot_cli.timeout_problem(copilot_cli.CopilotRunFailed("limit", stream("over-cap")))
    assert over.untested
    assert "more than twice" in over.message


# ---------- the run itself, against the fake client --------------------------------------------


def staged_ws(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    claude_runner.stage(claude_runner.SCENARIOS["check_report"], ws.mkdir() or ws,
                        skill_dir=(".agents", "skills"))
    return ws


def skip_scan(monkeypatch):
    """The real scan refuses a workspace under the repository or the account home;
    pytest's `tmp_path` is neither, but a parent may hold files on a developer machine."""
    monkeypatch.setattr(copilot_cli, "scan_problem", lambda _ws: None)


@POSIX
def test_a_run_holds_the_lock_reads_around_it_and_records_nothing_on_success(home, tmp_path,
                                                                           monkeypatch):
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch)
    ws = staged_ws(tmp_path)
    events = copilot_cli.run_copilot(ws, "Please check my proposal broken-format.md.",
                                     model="copilot-fixture-a", effort=None, cap=30, timeout=30,
                                     home=home, scenario=claude_runner.SCENARIOS["check_report"])
    kinds = [c["kind"] for c in calls(log)]
    assert kinds == ["headless", "skills", "mcp", "headless", "run", "headless"]
    assert all(c["token_names"] == [COPILOT.token_env] and c["token_ok"] for c in calls(log))
    assert all(c["copilot_home"] == str(home) for c in calls(log))
    assert all(c["home"] != os.environ.get("HOME") for c in calls(log))
    run = next(c for c in calls(log) if c["kind"] == "run")
    assert TOKEN not in json.dumps(run["argv"])
    assert copilot_cli.run_problem(events) is None
    assert copilot_cli.harness_record(events)["confinement_breach"] is None
    assert sessions(home) == []  # pruned
    assert copilot_cli.read_stop(home) is None
    # the probe's session left an empty `installed-plugins/` and an empty
    # session lock, as 1.0.91 does (K3); both hold nothing, so the home is clean
    assert (home / host_login.COPILOT_PLUGINS).is_dir()
    assert list((home / copilot_cli.SESSION_STATE / host_login.SESSION_LOCKS).iterdir())
    assert host_login.check_copilot_home(home) is None


@POSIX
def test_a_token_in_the_output_is_scrubbed_and_stops(home, tmp_path, monkeypatch):
    skip_scan(monkeypatch)
    ws = staged_ws(tmp_path)
    fake_copilot(tmp_path, monkeypatch, run="token-in-output", stderr=f"debug {TOKEN}\n",
                 write=[str(ws / "leak.md")])
    events = copilot_cli.run_copilot(ws, "check", model="copilot-fixture-a", effort=None,
                                     cap=30, timeout=30, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    assert TOKEN not in json.dumps(events)
    assert TOKEN not in (ws / "leak.md").read_text(encoding="utf-8")
    problem = copilot_cli.run_problem(events)
    assert problem.untested
    assert problem.kind == "isolation"
    assert TOKEN not in problem.message
    # the client's session store keeps the transcript unscrubbed: the remedy is
    # a new token and a reset, which deletes the store with the home
    assert "session store" in problem.message
    assert COPILOT.reset_command in problem.message
    assert copilot_cli.read_stop(home)["kind"] == "isolation"


@POSIX
def test_an_unavailable_read_after_the_run_records_a_billing_stop(home, tmp_path, monkeypatch):
    """testing-harness spec: Status read after the run unavailable — end to end:
    the fake server answers before the run and not after."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "STATUS_TIMEOUT_S", 1)
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 2)
    log = fake_copilot(tmp_path, monkeypatch, mode="once")
    monkeypatch.setattr(copilot_cli, "confinement_probe",
                        lambda _run: copilot_cli.Probe(True, None, tuple(probe("probe-ok")[1])))
    ws = staged_ws(tmp_path)
    events = copilot_cli.run_copilot(ws, "check", model="copilot-fixture-a", effort=None,
                                     cap=30, timeout=30, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    assert copilot_cli.harness_record(events)["after"] is None
    problem = copilot_cli.run_problem(events)
    assert problem.untested
    assert "cannot be ruled out" in problem.message
    assert copilot_cli.read_stop(home)["kind"] == "billing"
    assert [c["kind"] for c in calls(log)].count("headless") == 2


@POSIX
def test_a_read_after_the_run_that_raises_is_unavailable_and_stops(home, tmp_path, monkeypatch):
    """A broken pipe during the read after the run (the server's request answered
    into a closed stream) is an unavailable read: untested, with a billing stop."""
    skip_scan(monkeypatch)
    fake_copilot(tmp_path, monkeypatch)
    real, reads = copilot_cli.read_status, []

    def read_status(*args, **kwargs):
        reads.append(kwargs.get("models"))
        if len(reads) > 1:
            raise BrokenPipeError(32, "Broken pipe")
        return real(*args, **kwargs)

    monkeypatch.setattr(copilot_cli, "read_status", read_status)
    events = copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                     effort=None, cap=30, timeout=30, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    assert copilot_cli.harness_record(events)["after"] is None
    assert "cannot be ruled out" in copilot_cli.run_problem(events).message
    assert copilot_cli.read_stop(home)["kind"] == "billing"


@POSIX
def test_an_after_run_step_that_raises_still_scrubs_and_records_a_billing_stop(home, tmp_path,
                                                                              monkeypatch):
    """The after-run steps fail closed: whatever raises between the child's exit
    and the stops, the workspace is scrubbed and a billing stop is recorded."""
    skip_scan(monkeypatch)
    ws = staged_ws(tmp_path)
    fake_copilot(tmp_path, monkeypatch, write=[str(ws / "leak.md")])

    def broken(*_args, **_kwargs):
        raise RuntimeError("synthetic failure of an after-run step")

    monkeypatch.setattr(copilot_cli, "capture_session", broken)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        copilot_cli.run_copilot(ws, "check", model="copilot-fixture-a", effort=None, cap=30,
                                timeout=30, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    assert TOKEN not in (ws / "leak.md").read_text(encoding="utf-8")
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "billing"
    assert "did not complete" in stop["cause"]


def test_an_answer_into_a_closed_stream_does_not_raise():
    """`Rpc._route` answers a server's request; a server that already closed its
    input must not break the read."""
    closed = SimpleNamespace(stdin=SimpleNamespace(write=_broken_pipe, flush=_broken_pipe),
                             stdout=SimpleNamespace(readline=lambda: b"", read=lambda _n: b""))
    rpc = copilot_cli.Rpc(closed)  # type: ignore[arg-type]
    rpc._route({"id": 7, "method": "permission.request"})
    assert rpc.call("ping", {}, deadline=0) is None


def _broken_pipe(*_args):
    raise BrokenPipeError(32, "Broken pipe")


@POSIX
def test_a_timed_out_run_is_stopped_and_its_session_still_read(home, tmp_path, monkeypatch):
    skip_scan(monkeypatch)
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    fake_copilot(tmp_path, monkeypatch, run="no-shutdown", hang=True)
    ws = staged_ws(tmp_path)
    with pytest.raises(copilot_cli.CopilotRunFailed) as failed:
        copilot_cli.run_copilot(ws, "check", model="copilot-fixture-a", effort=None, cap=30,
                                timeout=1.5, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    assert "did not finish within 1.5s" in failed.value.message
    assert copilot_cli.harness_record(failed.value.events)["timed_out"] is True
    # its shell call was reported sandboxed, so the watch did not stop it
    assert copilot_cli.harness_record(failed.value.events)["confinement_breach"] is None
    assert copilot_cli.read_stop(home)["kind"] == "billing"
    assert sessions(home) == []


@POSIX
def test_the_watch_stops_a_run_at_its_first_unconfined_shell_call(home, tmp_path, monkeypatch):
    """testing-harness spec: Unconfined shell call stops the run — end to end:
    the child reports a shell completion without `sandboxed` and would then run
    on; the watch stops it there, long before the time limit, and the run is
    untested for isolation with an isolation stop recorded."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    fake_copilot(tmp_path, monkeypatch, run="sandbox-unreported", hang=True)
    begun = time.monotonic()
    events = copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                     effort=None, cap=30, timeout=60, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    assert time.monotonic() - begun < 30
    harness = copilot_cli.harness_record(events)
    assert harness["confinement_breach"] == copilot_cli.UNCONFINED_CALL
    assert harness["timed_out"] is False
    problem = copilot_cli.run_problem(events)
    assert problem.untested
    assert problem.kind == "isolation"
    assert "stopped at" in problem.message
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "isolation"
    assert "stopped at" in stop["cause"]


def _gone(pid: int, wait: float = 10.0) -> bool:
    """Whether a process has ended (gone, or a zombie its new parent has not
    reaped yet), polled for up to `wait` seconds."""
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        try:
            state = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
        except OSError:
            return True
        if state[0] in ("Z", "X"):
            return True
        time.sleep(0.1)
    return False


@POSIX
@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="reads /proc")
def test_a_process_the_run_left_in_its_group_is_killed(home, tmp_path, monkeypatch):
    """testing-harness spec: Process left behind by a Copilot run. Every
    Copilot child leads its own process
    group, and whatever ended the run, the group is killed — a process an
    unconfined shell command put in the background does not outlive it."""
    skip_scan(monkeypatch)
    pidfile = tmp_path / "background.pid"
    fake_copilot(tmp_path, monkeypatch, background=str(pidfile))
    copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                            effort=None, cap=30, timeout=30, home=home,
                            scenario=claude_runner.SCENARIOS["check_report"])
    pid = int(pidfile.read_text(encoding="utf-8"))
    try:
        assert _gone(pid)
    finally:
        with suppress(OSError):
            os.kill(pid, 9)


@POSIX
def test_a_stream_held_outside_the_group_does_not_stall_the_watch(tmp_path, monkeypatch):
    """A process that left the group (`setsid`) and holds the child's output
    pipe keeps its reader blocked: the stream is left to that reader rather
    than closed under it, so the watch returns after the grace period."""
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 1)
    pidfile = tmp_path / "holder.pid"
    script = ("import subprocess, sys, pathlib\n"
              "p = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], "
              "start_new_session=True)\n"
              f"pathlib.Path({str(pidfile)!r}).write_text(str(p.pid))\n"
              "print('{}', flush=True)\n")
    proc = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        begun = time.monotonic()
        out, _err, timed_out, breach = copilot_cli._watch_child(proc, timeout=20)
        assert time.monotonic() - begun < 10
        assert (out.strip(), timed_out, breach) == ("{}", False, None)
    finally:
        with suppress(OSError, ValueError):
            os.kill(int(pidfile.read_text(encoding="utf-8")), 9)
        for stream in (proc.stdout, proc.stderr):  # their readers end once the holder is gone
            stream.close()  # type: ignore[union-attr]


@POSIX
def test_a_planted_link_is_never_followed_and_the_run_is_untested(home, tmp_path, monkeypatch,
                                                                  capsys):
    """testing-harness spec: Workspace entry the runner must not follow (Decision
    13, the workspace after the run) — end to end through the
    runner: a run whose every shell call was sandboxed leaves the proposal as
    a link to a file outside and the event file as a link to another; the run
    is untested for isolation with an isolation stop, no verdict runs, the
    secret is in no output, summary or kept file, and the victim is
    unchanged."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    monkeypatch.setattr(copilot_cli, "managed_problem", lambda *_a, **_k: None)
    secret, victim = tmp_path / "secret", tmp_path / "victim"
    secret.write_text("SYNTHETIC-SECRET-CONTENT", encoding="utf-8")
    victim.write_text("SYNTHETIC-VICTIM-CONTENT", encoding="utf-8")
    fake_copilot(tmp_path, monkeypatch, links={
        "broken-format.md": str(secret), claude_runner.EVENTS_FILE: str(victim)})

    def no_verdict(*_args, **_kwargs):
        raise AssertionError("a verdict read the run's files")

    monkeypatch.setattr(claude_runner, "verdict", no_verdict)
    log = tmp_path / "run.jsonl"
    status = claude_runner.main(["check_report", "--host", "copilot", "--model",
                                 "copilot-fixture-a", "--max-ai-credits", "30", "--keep",
                                 "--summary-log", str(log)])
    out, err = capsys.readouterr()
    ws = Path(re.search(r"workspace kept: (\S+)", out)[1])  # type: ignore[index]
    try:
        assert status == claude_runner.EXIT_UNTESTED
        [line] = [json.loads(text) for text in log.read_text(encoding="utf-8").splitlines()]
        assert "must not follow" in line["why"]
        assert "broken-format.md (a link)" in line["why"]
        stop = copilot_cli.read_stop(home)
        assert stop["kind"] == "isolation"
        assert "must not follow" in stop["cause"]
        assert victim.read_text(encoding="utf-8") == "SYNTHETIC-VICTIM-CONTENT"
        assert secret.read_text(encoding="utf-8") == "SYNTHETIC-SECRET-CONTENT"
        assert "SYNTHETIC-SECRET-CONTENT" not in out + err + log.read_text(encoding="utf-8")
        assert not any(p.is_symlink() for p in ws.rglob("*"))
        events_file = ws / claude_runner.EVENTS_FILE
        assert not events_file.is_symlink()
        assert events_file.is_file()
        assert "SYNTHETIC-SECRET-CONTENT" not in events_file.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(ws, ignore_errors=True)


@POSIX
def test_the_probe_runs_through_the_headless_shell_and_deletes_its_session(home, tmp_path,
                                                                          monkeypatch):
    log = fake_copilot(tmp_path, monkeypatch)
    host_tmp = tmp_path / "host-tmp"
    host_tmp.mkdir()
    monkeypatch.setattr(copilot_cli, "PROBE_TMP", host_tmp)
    ws = staged_ws(tmp_path)
    run = copilot_cli.new_run(ws=ws, model="copilot-fixture-a")
    run.token, run.scratch = TOKEN, copilot_cli.make_scratch("devrun-test-")
    found = copilot_cli.confinement_probe(run)
    assert (found.supported, found.unapplied) == (True, None)
    assert {r.name for r in found.results} == {
        *copilot_cli.READ_TARGETS, *copilot_cli.AUTH_TARGETS, "python", "skill_script",
        *copilot_cli.TMP_TARGETS, *copilot_cli.MEASURED_TARGETS}
    assert all(r.sandboxed is True for r in found.results)
    assert copilot_cli.probe_problem(found.results, found.supported, found.unapplied) is None
    by = {r.name: r.output for r in found.results}
    assert by["tmp_write"] == "denied"  # judged on the host: the fake wrote nothing there
    assert list(host_tmp.iterdir()) == []  # the sentinel removed
    # the run's scratch home lies in the work directory, never in a temporary directory
    assert run.scratch.parent == copilot_cli.work_root()
    assert sessions(home) == []
    assert calls(log)[0]["cwd"] == str(ws)
    argv = calls(log)[0]["argv"]
    assert argv[argv.index("--log-dir") + 1] == str(run.scratch / "logs")
    assert not (home / "logs").exists()
    # testing-harness spec: Copilot children name the token variable
    assert "--no-auto-login" in argv
    assert _contains(argv, list(copilot_cli.TOKEN_FLAGS))
    assert TOKEN not in json.dumps(argv)
    assert "--sandbox" not in argv  # changes nothing on the server (K6 diagnosis)


@pytest.mark.usefixtures("home")
def test_a_write_that_reaches_the_host_tmp_refuses_the_probe(tmp_path, monkeypatch):
    """testing-harness spec: Host temporary directory denied to the sandboxed
    shell. The shell's write is judged on the host: one the host sees reads
    `writable` and refuses for isolation, whatever exit code the shell printed;
    the probe's files are removed either way."""
    fake_copilot(tmp_path, monkeypatch, tmp_reaches_host=True)
    host_tmp = tmp_path / "host-tmp"
    host_tmp.mkdir()
    monkeypatch.setattr(copilot_cli, "PROBE_TMP", host_tmp)
    ws = staged_ws(tmp_path)
    run = copilot_cli.new_run(ws=ws, model="copilot-fixture-a")
    run.token, run.scratch = TOKEN, copilot_cli.make_scratch("devrun-test-")
    found = copilot_cli.confinement_probe(run)
    by = {r.name: r.output for r in found.results}
    assert (by["host_tmp"], by["tmp_write"]) == ("denied", "writable")
    problem = copilot_cli.probe_problem(found.results, found.supported, found.unapplied)
    assert problem.kind == "isolation"
    assert "a write into the host's /tmp" in problem.cause
    assert list(host_tmp.iterdir()) == []


def probe_run(tmp_path: Path) -> copilot_cli.Run:
    run = copilot_cli.new_run(ws=staged_ws(tmp_path), model="copilot-fixture-a")
    run.token, run.scratch = TOKEN, copilot_cli.make_scratch("devrun-test-")
    return run


SHELL = "session.shell.executeUserRequested"


@POSIX
def test_the_probe_applies_the_pinned_sandbox_before_any_command(home, tmp_path, monkeypatch):
    """testing-harness spec: Confinement probe applies the pinned sandbox — the
    1.0.91 headless server never puts a session it creates in the sandbox (K6,
    2026-10-06), so the probe reads the block the client reads, refuses unless
    it is the pinned one, applies it with `session.options.update` as prompt
    mode does (origin `user_enabled`), and only then runs its commands."""
    log = fake_copilot(tmp_path, monkeypatch)
    found = copilot_cli.confinement_probe(probe_run(tmp_path))
    assert copilot_cli.probe_problem(found.results, found.supported, found.unapplied) is None
    methods = [c["method"] for c in rpc_calls(log)]
    commands = len(found.results)
    assert methods == ["connect", "sandbox.getHostSupport", "user.settings.get", "session.create",
                       "session.options.update", *[SHELL] * commands, "session.delete"]
    [update] = [c["params"] for c in rpc_calls(log) if c["method"] == "session.options.update"]
    pinned = host_login.pinned_settings(home, host_login.account_home())["sandbox"]
    assert update["sandboxConfig"] == pinned
    assert update["sandboxConfigSource"] == copilot_cli.SANDBOX_SOURCE == "user_enabled"
    created = next(c["params"] for c in rpc_calls(log) if c["method"] == "session.create")
    assert update["sessionId"] == created["sessionId"]


@POSIX
@pytest.mark.usefixtures("home")
def test_a_probe_session_without_the_sandbox_reproduces_k6_and_refuses(tmp_path, monkeypatch):
    """K6 (2026-10-06) on the fake server: a session the server created, with
    no options update, runs the probe's commands unconfined — every target
    readable, `gh` 0, nothing reported sandboxed — and the probe refuses for
    isolation, naming targets and never output."""
    fake_copilot(tmp_path, monkeypatch)
    monkeypatch.setattr(copilot_cli, "_apply_sandbox", lambda *_a: None)
    found = copilot_cli.confinement_probe(probe_run(tmp_path))
    by = {r.name: r for r in found.results}
    assert [by[n].output for n in copilot_cli.READ_TARGETS] == ["readable"] * 5
    assert by["gh_token"].output == "0"
    assert all(r.sandboxed is None for r in found.results)
    problem = copilot_cli.probe_problem(found.results, found.supported, found.unapplied)
    assert problem.kind == "isolation"
    assert "the token file" in problem.cause
    assert not re.search(r"\breadable\b", refusal(problem))


@POSIX
@pytest.mark.parametrize(("extra", "named", "created"), [
    ({"client_sandbox": {"enabled": False}}, "a sandbox block other than the pinned one", False),
    ({"client_sandbox": None}, "a sandbox block other than the pinned one", False),
    ({"options_update": "error"}, "session.options.update failed (JSON-RPC error -32000)", True),
    ({"options_update": "unsuccessful"}, "did not report success", True),
    ({"options_update": "no-result"}, "did not report success", True),
])
def test_a_sandbox_not_applied_refuses_for_isolation_and_runs_no_command(
        extra, named, created, home, tmp_path, monkeypatch):
    """testing-harness spec: Confinement probe applies the pinned sandbox — a
    block other than the pinned one refuses before any session exists; an
    options update that fails or reports no success refuses, runs no command
    and still deletes the session. The message never echoes the block."""
    log = fake_copilot(tmp_path, monkeypatch, **extra)
    found = copilot_cli.confinement_probe(probe_run(tmp_path))
    assert found.results == ()
    assert named in found.unapplied
    problem = copilot_cli.probe_problem(found.results, found.supported, found.unapplied)
    assert problem.kind == "isolation"
    assert "could not put its session in the pinned sandbox" in problem.cause
    assert "deniedPaths" not in refusal(problem)
    assert str(host_login.account_home()) not in refusal(problem)
    methods = [c["method"] for c in rpc_calls(log)]
    assert SHELL not in methods
    assert ("session.create" in methods) is created
    assert ("session.delete" in methods) is created
    assert sessions(home) == []


@POSIX
@pytest.mark.parametrize("token", [TOKEN, None])
def test_the_short_children_take_the_credential_flags_before_the_subcommand(token, home,
                                                                            tmp_path, monkeypatch):
    """testing-harness spec: Copilot children name the token variable — the
    version check and the two listings carry automatic login off, and the token
    variable named when they carry the token, before the subcommand: 1.0.91
    parses them as global options there and refuses them after `skill list` or
    `mcp list` (measured offline, 2026-10-06)."""
    log = fake_copilot(tmp_path, monkeypatch)
    ws = staged_ws(tmp_path)
    assert copilot_cli.installed_version(home, None, token) == (1, 0, 91)
    run = copilot_cli.new_run(ws=ws, token=token, scratch=copilot_cli.make_scratch("devrun-test-"))
    copilot_cli._roster_check(run)
    flags = ["--no-auto-login", *(copilot_cli.TOKEN_FLAGS if token else ())]
    by_kind = {c["kind"]: c for c in calls(log)}
    assert set(by_kind) == {"version", "skills", "mcp"}
    assert by_kind["version"]["argv"] == [*flags, "--version"]
    assert by_kind["skills"]["argv"] == [*flags, "skill", "list", "--json"]
    assert by_kind["mcp"]["argv"] == [*flags, "mcp", "list", "--json"]
    assert all(c["token_ok"] is bool(token) for c in by_kind.values())


@POSIX
def test_a_read_that_writes_into_the_home_refuses_its_own_run(home, tmp_path, monkeypatch):
    """testing-harness spec: Copilot read that writes into the home — the gate's
    last row checks the home as the reads left it, so the run stops before its
    prompt-mode child, not only the next run."""
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch, home_writes={"copilot-user-cache": "fixture"})
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                effort=None, cap=30, timeout=30, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    assert "is not clean: it holds copilot-user-cache" in refused.value.message
    assert "fixture" not in refused.value.message.replace("copilot-fixture-a", "")
    kinds = [c["kind"] for c in calls(log)]
    assert "headless" in kinds
    assert "run" not in kinds


@POSIX
@pytest.mark.usefixtures("home")
def test_preflight_only_prints_the_clean_row_after_the_reads(tmp_path, monkeypatch):
    """K3 reads it: the home as the status read, the listings and the probe
    left it, printed even when an earlier gate row ended the reads."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    fake_copilot(tmp_path, monkeypatch, probe="probe-gh-token",
                 home_writes={"exp-cache": "fixture"})
    checks, ready = copilot_cli.preflight_report(staged_ws(tmp_path),
                                                 claude_runner.SCENARIOS["check_report"],
                                                 model="copilot-fixture-a", effort=None)
    by = {c.name: c for c in checks}
    assert ready is False
    assert list(by)[-2:] == ["confinement_probe", "clean_after_reads"]
    assert by["confinement_probe"].problem is not None
    assert by["clean"].problem is None
    assert "it holds exp-cache" in by["clean_after_reads"].problem.cause


@POSIX
def test_the_preflight_order_spawns_nothing_before_location_marker_and_mode(tmp_path,
                                                                            monkeypatch):
    monkeypatch.setenv(host_login.STATE_VAR, str(tmp_path / "state"))
    spawned: list[str] = []
    monkeypatch.setattr(copilot_cli, "installed_version",
                        lambda *_a: spawned.append("version") or (1, 0, 91))
    run = copilot_cli.new_run()
    checks = list(copilot_cli.preflight_checks(run))
    assert [c.name for c in checks] == ["location", "home"]
    assert checks[-1].problem is not None
    assert spawned == []
    assert not (tmp_path / "state").exists()


@POSIX
def test_preflight_only_starts_no_prompt_child_and_reports_the_stop(home, tmp_path,
                                                                    monkeypatch):
    """testing-harness spec: Copilot preflight only."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    log = fake_copilot(tmp_path, monkeypatch)
    copilot_cli.record_stop(home, "approval", "first run not yet approved")
    ws = staged_ws(tmp_path)
    checks, ready = copilot_cli.preflight_report(ws, claude_runner.SCENARIOS["check_report"],
                                                 model="copilot-fixture-a", effort=None)
    names = [c.name for c in checks]
    assert names == ["location", "home", "clean", "token", "stop", "version", "managed_settings",
                     "sandbox_tools", "workspace", "status", "model", "rosters",
                     "confinement_probe", "clean_after_reads"]
    assert ready is True
    assert next(c for c in checks if c.name == "clean_after_reads").problem is None
    stop = next(c for c in checks if c.name == "stop")
    assert stop.problem is not None
    assert "approval" in stop.detail
    assert "run" not in [c["kind"] for c in calls(log)]
    assert sessions(home) == []
    roster = names.index("rosters")
    assert names.index("confinement_probe") > roster


@POSIX
@pytest.mark.usefixtures("home")
def test_preflight_only_goes_on_past_rows_that_leave_the_later_reads_safe(tmp_path, monkeypatch):
    """testing-harness spec: Copilot preflight only — every check before the run
    runs and is printed: a missing sandbox tool and a refused status row do not
    hold back the rosters and the confinement probe, which K6 reads."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "managed_problem", lambda *_a, **_k: None)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: LoginProblem(
        "the Copilot sandbox needs slirp4netns on PATH", "install slirp4netns", "copilot",
        "precondition"))
    log = fake_copilot(tmp_path, monkeypatch, status="status-no-entitlement-field")
    checks, ready = copilot_cli.preflight_report(staged_ws(tmp_path),
                                                 claude_runner.SCENARIOS["check_report"],
                                                 model="copilot-fixture-x", effort=None)
    by = {c.name: c for c in checks}
    assert ready is False
    assert list(by)[-5:] == ["status", "model", "rosters", "confinement_probe",
                             "clean_after_reads"]
    assert by["sandbox_tools"].problem is not None
    assert by["status"].problem is not None
    assert by["model"].problem is not None
    assert (by["rosters"].problem, by["confinement_probe"].problem) == (None, None)
    assert "run" not in [c["kind"] for c in calls(log)]


@POSIX
@pytest.mark.usefixtures("home")
def test_preflight_only_ends_at_a_row_that_makes_a_later_start_unsafe(tmp_path, monkeypatch):
    """A version other than the pinned one ends the report: the later reads
    speak the pinned version's server interface."""
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch, version="GitHub Copilot CLI 1.0.90.")
    checks, ready = copilot_cli.preflight_report(staged_ws(tmp_path),
                                                 claude_runner.SCENARIOS["check_report"],
                                                 model="copilot-fixture-a", effort=None)
    assert ready is False
    assert checks[-1].name == "version"
    assert [c["kind"] for c in calls(log)] == ["version"]


@POSIX
def test_the_rosters_and_the_probe_run_under_the_run_lock(home, tmp_path, monkeypatch):
    """Preflight order (design Decision 6): the rosters and the confinement probe
    run under the one hold of the run lock the status read takes."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    fake_copilot(tmp_path, monkeypatch)
    held: list[str] = []
    real_listing, real_probe = copilot_cli._listing, copilot_cli.confinement_probe

    def note(name: str) -> None:
        try:
            with host_login.run_lock(home, wait=0, record=COPILOT):
                held.append(f"{name}: free")
        except host_login.RunLockBusy:
            held.append(f"{name}: held")

    def listing(args, run):
        note(" ".join(args))
        return real_listing(args, run)

    def probe_(run):
        note("probe")
        return real_probe(run)

    monkeypatch.setattr(copilot_cli, "_listing", listing)
    monkeypatch.setattr(copilot_cli, "confinement_probe", probe_)
    _, ready = copilot_cli.preflight_report(staged_ws(tmp_path),
                                            claude_runner.SCENARIOS["check_report"],
                                            model="copilot-fixture-a", effort=None)
    assert ready is True
    assert held == ["skill list: held", "mcp list: held", "probe: held"]


def write_roster(ws_skill: str) -> list[dict]:
    """`skills-ok.json` with its staged skill renamed."""
    roster = load("skills-ok")
    roster[0] = {**roster[0], "name": ws_skill,  # type: ignore[index]
                 "path": f"__WS__/.agents/skills/{ws_skill}"}
    return roster  # type: ignore[return-value]


@POSIX
def test_a_leaked_token_reaches_no_summary_no_kept_file_and_no_judge(home, tmp_path,
                                                                      monkeypatch, capsys):
    """testing-harness spec: Token value scrubbed from a child's output — end to end
    through the runner: a child that prints the token on stdout and stderr and
    writes it into the draft leaves it in no summary line, no printed output, no
    file of the kept workspace and no judge input of a later re-grade; the run is
    untested for isolation and records an isolation stop."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    monkeypatch.setattr(copilot_cli, "managed_problem", lambda *_a, **_k: None)
    fake_copilot(tmp_path, monkeypatch, run="token-in-output",
                 skills=write_roster("proposal-write"),
                 stderr=f"debug {TOKEN}\n", write=["drift-detection-proposal.md"],
                 write_body=CLEAN_DRAFT + "\n")
    log = tmp_path / "run.jsonl"
    status = claude_runner.main(["write_from_seed", "--host", "copilot", "--model",
                                 "copilot-fixture-a", "--max-ai-credits", "30", "--keep",
                                 "--summary-log", str(log)])
    out, err = capsys.readouterr()
    ws = Path(re.search(r"workspace kept: (\S+)", out)[1])  # type: ignore[index]
    try:
        assert status == claude_runner.EXIT_UNTESTED
        assert TOKEN not in out + err
        assert TOKEN not in log.read_text(encoding="utf-8")
        [line] = [json.loads(text) for text in log.read_text(encoding="utf-8").splitlines()]
        assert "token's value appeared" in line["why"]
        assert copilot_cli.read_stop(home)["kind"] == "isolation"
        leaked = [p.name for p in ws.rglob("*") if p.is_file()
                  and TOKEN.encode() in p.read_bytes()]
        assert leaked == []
        draft = (ws / "drift-detection-proposal.md").read_text(encoding="utf-8")
        assert draft.endswith(copilot_cli.SCRUBBED)
        prompts: list[str] = []

        async def judge_all(criteria, *, model, effort, **_options):
            prompts.extend(c.prompt for c in criteria)
            call = JudgeCall("GRADE: C", model, "2.1.284", effort, 10, 0.01,
                             RateLimit("allowed", "five_hour", 0.1))
            return JudgeRun(tuple(Grade(c.name, True, "ok", call) for c in criteria), 0.02)

        monkeypatch.setattr(claude_cli, "judge_all", judge_all)
        isolated = tmp_path / "devjudge-config"
        isolated.mkdir()
        monkeypatch.setattr(claude_runner, "enter_isolation", lambda _stack, _prefix: isolated)
        assert claude_runner.main(["write_from_seed", "--host", "copilot", "--rejudge", str(ws),
                                   "--summary-log", str(tmp_path / "rejudge.jsonl")]) == 0
        assert prompts
        assert all(TOKEN not in prompt for prompt in prompts)
        assert any(copilot_cli.SCRUBBED in prompt for prompt in prompts)
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_check_is_a_frozen_dataclass():
    check = Check("x")
    with pytest.raises(AttributeError):
        check.name = "y"  # type: ignore[misc]


# ---------- run-env (K1) ----------------------------------------------------------------------


def test_run_env_refuses_without_a_home(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv(host_login.STATE_VAR, str(tmp_path / "state"))
    assert copilot_cli.main(["run-env", "--", "true"]) == host_login.EXIT_NOT_READY
    assert "uv run poe host-login copilot" in capsys.readouterr().err


@POSIX
def test_run_env_runs_a_command_without_the_token(home, monkeypatch):
    seen: list[dict] = []

    def run(cmd, *, env, cwd, check):
        seen.append({"cmd": cmd, "env": env, "cwd": cwd, "check": check})
        return subprocess.CompletedProcess(cmd, 7)

    monkeypatch.setattr(copilot_cli.subprocess, "run", run)
    assert copilot_cli.main(["run-env", "--", "sh", "-c", "exit 7"]) == 7
    [call] = seen
    assert call["cmd"] == ["sh", "-c", "exit 7"]
    assert COPILOT.token_env not in call["env"]
    assert call["env"]["DBUS_SESSION_BUS_ADDRESS"] == "disabled:"
    assert call["env"]["GH_CONFIG_DIR"] == str(home / "gh")
    assert call["env"]["HOME"] == str(call["cwd"])
    with pytest.raises(SystemExit):
        copilot_cli.main(["run-env"])
