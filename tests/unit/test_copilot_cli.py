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

import errno
import hashlib
import json
import os
import re
import shlex
import shutil
import stat
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
import workspace_guard
from claude_cli import Grade, JudgeCall, JudgeRun, RateLimit
from copilot_cli import CanaryReading, Check, ProbeResult, RunProblem
from helpers import CLEAN_DRAFT, COPILOT_STREAMS, PROC_FDS, REPO, copilot_stream, reusing_lstat
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
# a directory's mode keeps its owner out only when the owner is not root
ROOTLESS = pytest.mark.skipif(os.name != "posix" or host_login.fcntl is None
                              or os.geteuid() == 0, reason="POSIX modes, a non-root owner")
# the runner refuses `--host copilot` on Windows (test_windows_is_a_usage_error), so a
# Copilot session record only ever comes from a POSIX run: the saved streams join the
# workspace and a skill's SKILL.md with "/", and the check that a project skill ran from
# its own staged file compares that path with the platform's own spelling of it
POSIX_RECORDS = pytest.mark.skipif(os.name != "posix",
                                   reason="Copilot records come from POSIX runs only")
# taken at import, before the conftest replaces the seam (no test writes under /run/user)
REAL_RUNTIME_DIR = copilot_cli.runtime_dir
# the same for Yama's reader: tests hand it their own files, never the real sysctl
REAL_PTRACE_SCOPE = copilot_cli.ptrace_scope


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

def placed(text):
    # the workspace path put into JSON text: escaped, as helpers.json_path does
    return text.replace("__WS__", json.dumps(os.getcwd())[1:-1])

def start_writes(kind):
    # what the 1.0.91 client writes when it starts (task 7.4a, measured): its
    # state file with the comment header and `firstLaunchAt`, and an empty
    # process log under `--log-dir`, or under `<COPILOT_HOME>/logs` without it;
    # CONFIG["log_text"][kind] is what a test makes that log carry
    home = pathlib.Path(os.environ["COPILOT_HOME"])
    if not (home / "config.json").exists():
        (home / "config.json").write_text(
            HEADER + json.dumps({"firstLaunchAt": "2026-01-01T00:00:00.000Z"}), encoding="utf-8")
    logs = pathlib.Path(ARGS[ARGS.index("--log-dir") + 1]) if "--log-dir" in ARGS else home / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with open(CONFIG["log"] + ".logdirs", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": kind, "log_dir": str(logs)}) + "\n")
    (logs / f"process-{int(time.time() * 1000)}-{os.getpid()}.log").write_text(
        CONFIG.get("log_text", {}).get(kind, ""), encoding="utf-8")
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

PROBES = (("/.agents-probe", "staged_ro"),  # its paths name the workspace, so it comes first
          ("/cmdline", "client_environ"),  # the content scan over every environ and cmdline
          ("GITHUB_TOKEN+x", "token_env"), ("devrun-probe-var-", "var_tmp"),
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
              "net_ns": "shared", "tmp_write": "0", "staged_ro": "writable"}

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

def trial(params, calls):
    # the canary's script run once in the probe's session (the trial): each of
    # its rows answered from the probe fixture as a tagged line, then the
    # closing line unless CONFIG["trial"] says otherwise
    ident = f"probe-{len(calls)}"
    calls.append("trial")
    script = pathlib.Path(".devrun-canary.sh")
    with open(CONFIG["log"] + ".trial", "a", encoding="utf-8") as fh:  # its mode, as run
        fh.write(oct(script.stat().st_mode & 0o777) + "\n")
    lines = []
    for row in script.read_text(encoding="utf-8").splitlines():
        if not row.startswith("w=$("):
            continue
        name = row.rsplit(" ", 2)[-2]
        found = next(r for r in CONFIG["probe"]["results"] if r["name"] == name)
        lines.append(f"canary {name} {'0' if name == 'tmp_write' else found['output']}")
    if CONFIG.get("trial") != "unclosed":
        lines.append("canary end")
    send({"jsonrpc": "2.0", "method": "session.event", "params": {
        "sessionId": params["sessionId"], "event": {"type": "tool.execution_complete", "data": {
            "toolCallId": ident, "success": True,
            "sandboxed": params["sessionId"] in SANDBOXED}}}})
    return {"result": {"toolCallId": ident, "success": True, "output": "\n".join(lines) + "\n",
                       "exitCode": 0}}

def shell(params, calls):
    # 1.0.91 (K6, 2026-10-06): a session the server created runs its shell
    # unconfined and reports no `sandboxed`, until `session.options.update`
    # gives it the home's sandbox block
    if params["command"] == "sh .devrun-canary.sh":
        return trial(params, calls)
    name = probe_name(params["command"])
    ident = f"probe-{len(calls)}"
    calls.append(name)
    if name == "tmp_write" and CONFIG.get("tmp_reaches_host"):  # a host /tmp left writable
        target = params["command"].split(": > ", 1)[1].split(" 2>", 1)[0].strip("'")
        pathlib.Path(target).write_text("", encoding="utf-8")
    if params["sessionId"] in SANDBOXED:
        found = next(r for r in CONFIG["probe"]["results"] if r["name"] == name)
        data = {"toolCallId": ident, "success": True, "sandboxed": found["sandboxed"]}
        # `tmp_write` prints its exit code, and the harness judges the row on the host
        output = "0" if name == "tmp_write" else found["output"]
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

def canary_completion(output, sandboxed):
    # 1.0.91's two shapes of a shell completion (the first canary, 2026-10-07):
    # one that ran, and the client's own permission refusal before any shell
    if CONFIG.get("canary_refused"):
        return {"toolCallId": "c0", "success": False, "sandboxed": True,
                "error": {"code": "denied", "message": "Permission denied (synthetic)"},
                "toolTelemetry": {"properties": {"shell_error_category": "permission_denied"}}}
    text = output + "<shellId: 1 completed with exit code 0>"
    return {"toolCallId": "c0", "success": True, "sandboxed": sandboxed,
            "result": {"content": text, "detailedContent": text},
            "shellExecution": {"exitCode": 0},
            "toolTelemetry": {"properties": {"sandboxApplied": "true"}}}

def canary_stream(prompt):
    # the canary (D-c): one bash call of the prompt's fixed command, which runs
    # the script the harness wrote into the workspace; each of its rows is
    # answered from CONFIG["canary"] (name -> [word, sandboxed]) as a tagged line
    command = prompt.split("```sh\n", 1)[1].split("\n```", 1)[0]
    script = pathlib.Path(command.split()[-1]).read_text(encoding="utf-8")
    output, sandboxed = "", True
    for row in script.splitlines():
        if not row.startswith("w=$("):
            continue
        name = row.rsplit(" ", 2)[-2]
        if name in CONFIG.get("canary_skip", []):
            continue
        if name == "tmp_write" and CONFIG.get("tmp_reaches_host"):
            target = row.split(": > ", 1)[1].split(" 2>", 1)[0].strip("'")
            pathlib.Path(target).write_text("", encoding="utf-8")
        word, confined = CONFIG["canary"][name]
        output += f"canary {name} {word}\n"
        sandboxed = sandboxed and confined
    output += "canary end\n"
    ran = CONFIG.get("canary_command", command)
    lines = [{"type": "tool.execution_start", "data": {
                 "toolCallId": "c0", "toolName": "bash", "arguments": {"command": ran}}},
             {"type": "tool.execution_complete", "data": canary_completion(output, sandboxed)}]
    lines.append({"type": "assistant.message", "data": {"messageId": "m1", "content": "done",
                                                        "model": CONFIG["canary_model"]}})
    lines.append({"type": "result", "sessionId": "11111111-1111-4111-8111-111111111111",
                  "exitCode": 0})
    return "".join(json.dumps(line) + "\n" for line in lines)

def run():
    session = next(a.split("=", 1)[1] for a in ARGS if a.startswith("--session-id="))
    if "canary" in CONFIG:
        CONFIG["stream"] = canary_stream(ARGS[ARGS.index("-p") + 1])
    folder = pathlib.Path(os.environ["COPILOT_HOME"], "session-state", session)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "events.jsonl").write_text(placed(CONFIG["session"]), encoding="utf-8")
    for name in CONFIG.get("write", []):  # a relative name lands in the workspace
        pathlib.Path(name).write_text(CONFIG.get("write_body", "") + CONFIG["token"],
                                      encoding="utf-8")
    for name in CONFIG.get("mkdirs", []):  # a file at the name is replaced by the directory
        if pathlib.Path(name).is_file():
            pathlib.Path(name).unlink()
        pathlib.Path(name).mkdir(exist_ok=True)
    for name, target in CONFIG.get("links", {}).items():  # what a sandboxed shell may plant
        pathlib.Path(name).unlink(missing_ok=True)
        pathlib.Path(name).symlink_to(target)
    for name in CONFIG.get("close", []):  # a directory the shell left write-and-search only
        os.chmod(name, 0o300)
    if CONFIG.get("background"):  # a process the run leaves behind in its group
        import subprocess
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pathlib.Path(CONFIG["background"]).write_text(str(child.pid), encoding="utf-8")
    sys.stdout.write(placed(CONFIG["stream"])
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
    print(placed(json.dumps(CONFIG["skills"])))
elif CMD[:2] == ["mcp", "list"]:
    record("mcp")
    print(json.dumps(CONFIG["mcp"]))
elif "--headless" in ARGS:
    record("headless")
    start_writes("headless")
    serve()
elif "-p" in ARGS:
    record("run")
    start_writes("run")
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
        elif kind == "copilot.skill_context":
            lines.append({"type": data["event"], "data": {"source": data["source"],
                                                          "contentId": "sha256:0"}})
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


@POSIX
def test_scrub_tree_counts_a_read_only_file_and_a_failed_rewrite(tmp_path, monkeypatch):
    """Decision 4, scrubbing (revised 2026-10-07, review of task 8.0a): a
    file closed to writing (0400, as the canary's script is) is rewritten
    through its owner and given its mode back, and a file that held the
    value counts as a hit even when its rewrite fails, so the scrub's
    isolation stop follows instead of a silent miss."""
    locked = tmp_path / "locked.md"
    locked.write_text(f"token {TOKEN}", encoding="utf-8")
    locked.chmod(0o400)
    assert copilot_cli.scrub_tree(tmp_path, TOKEN) == ["locked.md"]
    assert TOKEN not in locked.read_text(encoding="utf-8")
    assert stat.S_IMODE(locked.stat().st_mode) == 0o400
    locked.chmod(0o600)
    locked.write_text(f"again {TOKEN}", encoding="utf-8")

    def refuse(*_a, **_k):
        raise PermissionError(13, "synthetic")

    monkeypatch.setattr(copilot_cli, "_rewrite", refuse)
    assert copilot_cli.scrub_tree(tmp_path, TOKEN) == ["locked.md"]  # the hit, not the rewrite


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
    identity = workspace_guard.workspace_identity(ws)
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
    for index in range(workspace_guard.SHOWN_ENTRIES + 2):
        (ws / f"{TOKEN}-{index}").symlink_to(tmp_path)
    found = copilot_cli.workspace_breach(ws, workspace_guard.workspace_identity(ws), TOKEN)
    assert found.endswith(" and 2 more")
    assert TOKEN not in found
    assert copilot_cli.SCRUBBED in found
    assert list(ws.iterdir()) == []


@POSIX
def test_a_replaced_workspace_is_read_by_nothing(tmp_path):
    """A workspace swapped for a link (or for another directory) is not the one
    the run started in: the link is removed, never followed, and nothing in
    its target is walked or scrubbed. The identity is held as both runners
    hold it (`workspace_guard.pinned`)."""
    ws, outside = tmp_path / "ws", tmp_path / "outside"
    ws.mkdir()
    outside.mkdir()
    (outside / "keep.md").write_text(f"keep {TOKEN}", encoding="utf-8")
    with workspace_guard.pinned(ws) as identity:
        ws.rmdir()
        ws.symlink_to(outside)
        assert (copilot_cli.workspace_breach(ws, identity, TOKEN)
                == workspace_guard.WORKSPACE_REPLACED)
        assert not ws.is_symlink()
        assert not ws.exists()
        assert (outside / "keep.md").read_text(encoding="utf-8") == f"keep {TOKEN}"
        ws.mkdir()  # another directory under the same name
        assert (copilot_cli.workspace_breach(ws, identity, TOKEN)
                == workspace_guard.WORKSPACE_REPLACED)
        assert ws.is_dir()
        ws.rmdir()
        assert (copilot_cli.workspace_breach(ws, identity, TOKEN)
                == workspace_guard.WORKSPACE_REPLACED)


@pytest.mark.skipif(not PROC_FDS, reason="reads this process's descriptors (/proc/self/fd)")
def test_a_workspace_made_again_is_replaced_where_inode_numbers_are_reused(tmp_path,
                                                                           monkeypatch):
    """CI, 2026-10-13: on the runner's ext4 /tmp the directory made under the
    workspace's name got the removed workspace's inode number, so the check
    read it as the directory the run started in; tmpfs and btrfs never hand a
    number on. Simulated here on any filesystem (`reusing_lstat`): an
    identity merely read is fooled, one held as the runners hold it
    (`workspace_guard.pinned`) keeps the start's inode alive, so its number
    is never handed on."""
    ws = tmp_path / "ws"
    ws.mkdir()
    start = workspace_guard.workspace_identity(ws)
    monkeypatch.setattr(os, "lstat", reusing_lstat(ws, start))
    ws.rmdir()
    ws.mkdir()
    assert workspace_guard.breach(ws, start) is None  # the simulation bites: read, not held
    ws.rmdir()
    ws.mkdir()
    with workspace_guard.pinned(ws) as held:
        monkeypatch.setattr(os, "lstat", reusing_lstat(ws, held))
        ws.rmdir()
        ws.mkdir()
        assert copilot_cli.workspace_breach(ws, held, TOKEN) == workspace_guard.WORKSPACE_REPLACED


@POSIX
def test_a_link_in_the_workspace_place_is_never_pinned(tmp_path):
    ws, outside = tmp_path / "ws", tmp_path / "outside"
    outside.mkdir()
    ws.symlink_to(outside)
    # Linux reports ENOTDIR (a link is no directory), macOS ELOOP (O_NOFOLLOW)
    refusals = rf"\[Errno ({errno.ENOTDIR}|{errno.ELOOP})\]"
    with pytest.raises(OSError, match=refusals), workspace_guard.pinned(ws):
        pytest.fail("a link was opened as the workspace")


def test_without_directory_descriptors_the_identity_is_read_alone(tmp_path, monkeypatch):
    """Where a directory cannot be opened (no `O_DIRECTORY`: Windows),
    `pinned` yields the identity `workspace_identity` reads and opens
    nothing."""
    ws = tmp_path / "ws"
    ws.mkdir()
    monkeypatch.delattr(workspace_guard.os, "O_DIRECTORY", raising=False)
    monkeypatch.setattr(workspace_guard.os, "open", lambda *_a, **_k: pytest.fail("opened"))
    with workspace_guard.pinned(ws) as identity:
        assert identity == workspace_guard.workspace_identity(ws)


@contextmanager
def reopened(*paths: Path):
    """Give a test's closed directories back to their owner afterwards, so
    `tmp_path` can be cleaned; the check under test never does this."""
    try:
        yield
    finally:
        for path in paths:
            with suppress(OSError):
                path.chmod(0o700)


@ROOTLESS
@pytest.mark.parametrize(("where", "mode", "named"), [
    (".", 0o300, "the workspace itself is a directory closed to its owner (mode 0300)"),
    ("sub", 0o300, "sub (a directory closed to its owner (mode 0300))"),
    ("sub", 0o600, "sub/proposal.md (an entry the harness could not examine)"),
], ids=["root-0300", "sub-0300", "sub-0600"])
def test_a_directory_closed_to_its_owner_is_a_breach_and_is_never_reopened(where, mode, named,
                                                                           tmp_path):
    """Decision 13, revised 2026-10-07 (review of task 8.0): `os.walk` passes
    over a directory it cannot list, so a shell that left the workspace, or a
    directory in it, write-and-search only would hide a link the harness could
    still open by name. The check fails closed: such a directory, or an entry
    it cannot examine, is a breach, named, never chmodded or reopened, and the
    link behind it is neither followed nor read."""
    ws, secret = tmp_path / "ws", tmp_path / "secret"
    (ws / "sub").mkdir(parents=True)
    secret.write_text("SYNTHETIC-SECRET-CONTENT", encoding="utf-8")
    closed = ws if where == "." else ws / where
    (closed / "proposal.md").symlink_to(secret)
    identity = workspace_guard.workspace_identity(ws)
    closed.chmod(mode)
    with reopened(closed):
        found = workspace_guard.breach(ws, identity)
        assert found is not None
        assert named in found
        assert stat.S_IMODE(closed.stat().st_mode) == mode  # never chmodded
        assert copilot_cli.workspace_breach(ws, identity, TOKEN) is not None  # still a breach
    assert (closed / "proposal.md").is_symlink()  # behind a closed directory: left, unread
    assert secret.read_text(encoding="utf-8") == "SYNTHETIC-SECRET-CONTENT"


def test_closed_dir_reads_the_owner_bits_only():
    assert workspace_guard.closed_dir(stat.S_IFDIR | 0o700) is None
    assert workspace_guard.closed_dir(stat.S_IFDIR | 0o755) is None
    for mode in (0o300, 0o500, 0o600, 0o000, 0o077):
        assert workspace_guard.closed_dir(stat.S_IFDIR | mode) == (
            f"{workspace_guard.CLOSED} (mode {mode:04o})")
    assert workspace_guard.unsafe_entry(stat.S_IFDIR | 0o300, 2).startswith(
        workspace_guard.CLOSED)


@ROOTLESS
@pytest.mark.parametrize("where", [".", "sub"], ids=["root", "sub"])
def test_a_run_that_closes_a_workspace_directory_is_untested_and_reads_nothing(
        where, home, tmp_path, monkeypatch, capsys):
    """testing-harness spec: Copilot workspace directory the runner cannot
    list — end to end through the runner: the fake shell plants the proposal
    as a link (at the top, or in a directory it then closes) and leaves that
    directory write-and-search only; the run is untested for isolation with
    an isolation stop, no verdict opens a fixed name, and the secret is in no
    output or summary."""
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    monkeypatch.setattr(copilot_cli, "managed_problem", lambda *_a, **_k: None)
    secret = tmp_path / "secret"
    secret.write_text("SYNTHETIC-SECRET-CONTENT", encoding="utf-8")
    name = "broken-format.md" if where == "." else "sub/broken-format.md"
    fake_copilot(tmp_path, monkeypatch, mkdirs=["sub"], links={name: str(secret)},
                 close=[where])

    def no_verdict(*_args, **_kwargs):
        raise AssertionError("a verdict read the run's files")

    monkeypatch.setattr(claude_runner, "verdict", no_verdict)
    log = tmp_path / "run.jsonl"
    status = claude_runner.main(["check_report", "--host", "copilot", "--model",
                                 "copilot-fixture-a", "--max-ai-credits", "30", "--keep",
                                 "--summary-log", str(log)])
    out, err = capsys.readouterr()
    ws = Path(re.search(r"workspace kept: (\S+)", out)[1])  # type: ignore[index]
    with reopened(ws, ws / "sub"):
        assert status == claude_runner.EXIT_UNTESTED
        [line] = [json.loads(text) for text in log.read_text(encoding="utf-8").splitlines()]
        assert "closed to its owner" in line["why"]
        stop = copilot_cli.read_stop(home)
        assert (stop["kind"], "closed to its owner" in stop["cause"]) == ("isolation", True)
        assert "SYNTHETIC-SECRET-CONTENT" not in out + err + log.read_text(encoding="utf-8")
        assert secret.read_text(encoding="utf-8") == "SYNTHETIC-SECRET-CONTENT"
    shutil.rmtree(ws, ignore_errors=True)


def test_a_workspace_breach_is_untested_for_isolation_and_stops():
    events = stream("success")
    copilot_cli.harness_record(events)["workspace_breach"] = workspace_guard.WORKSPACE_REPLACED
    assessment = copilot_cli.assess(events)
    assert assessment.problem.untested
    assert assessment.problem.kind == "isolation"
    assert workspace_guard.WORKSPACE_REPLACED in assessment.problem.message
    assert ("isolation", workspace_guard.WORKSPACE_REPLACED) in assessment.stops


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
    ("approval", "precondition", "that is the go, which covers one canary"),
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
    (home / copilot_cli.QUOTA_FILE).unlink()  # the fixture's go
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
    assert copilot_cli.clear_stop(home) is None  # no stop: the clear records the go alone
    assert copilot_cli.read_go(home)["canary"] is None


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
    # task 8.1a: the client's file and search tools refuse the workspace under
    # its denied ancestor, so no scenario offers one
    assert not set(offered) & copilot_cli.FILE_TOOLS
    assert {"bash", "skill"} <= set(offered)
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
    for offered in tools.values():  # none offers the client's own file or search tools
        assert not {"view", "create", "edit", "apply_patch", "glob", "grep", "rg"} & set(offered)


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


@ROOTLESS
def test_work_root_repairs_an_owned_level_left_group_readable(tmp_path, monkeypatch):
    """testing-harness spec: Copilot work directory owner-only. A level the
    harness owns that another process created group- or world-readable (a
    scratch rig's `mkdir(parents=True)` leaves intermediates 0755) is repaired
    to 0700 even though it already exists; the per-user runtime directory, which
    the harness does not own, is never chmodded."""
    runtime = tmp_path / "run-user-1000"
    runtime.mkdir(mode=0o755)  # systemd-logind's; the harness must not touch it
    (runtime / "thesis-proposal-dev").mkdir(mode=0o755)  # owned, left lax by a rig
    (runtime / "thesis-proposal-dev" / "work").mkdir(mode=0o755)  # owned, left lax
    account = tmp_path / "account"
    state = account / ".local" / "state" / "thesis-proposal-dev"
    monkeypatch.setenv(host_login.STATE_VAR, str(state))
    monkeypatch.setattr(host_login, "account_home", lambda _uid=None: account)
    monkeypatch.setattr(copilot_cli, "runtime_dir", lambda _uid=None: runtime)
    root = copilot_cli.work_root()
    assert root == runtime / "thesis-proposal-dev" / "work" / "copilot"
    assert _mode(runtime / "thesis-proposal-dev") == 0o700  # repaired
    assert _mode(runtime / "thesis-proposal-dev" / "work") == 0o700  # repaired
    assert _mode(root) == 0o700  # created owner-only
    assert _mode(runtime) == 0o755  # the boundary the harness does not own is untouched


def test_owned_base_is_the_ancestor_the_harness_does_not_own():
    runtime = PurePosixPath("/run/user/1000")
    runtime_root = runtime / "thesis-proposal-dev" / "work" / "copilot"
    assert copilot_cli.owned_base(STATE_P, runtime, runtime_root) == runtime
    state_root = STATE_P / "work" / "copilot"
    assert copilot_cli.owned_base(STATE_P, runtime, state_root) == STATE_P.parent
    assert copilot_cli.owned_base(STATE_P, None, state_root) == STATE_P.parent


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


@pytest.mark.skipif(not hasattr(os, "getuid"),
                    reason="the per-user runtime directory /run/user/<uid> is POSIX")
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


def test_runtime_dir_is_none_without_posix_users(monkeypatch):
    """Without POSIX user ids (Windows) there is no per-user runtime
    directory, and nothing is read."""
    monkeypatch.delattr(copilot_cli.os, "getuid", raising=False)
    monkeypatch.setattr(copilot_cli.os, "lstat", lambda _path: pytest.fail("read"))
    assert REAL_RUNTIME_DIR() is None
    assert REAL_RUNTIME_DIR(4242) is None


@POSIX
@pytest.mark.usefixtures("copilot_account")
def test_the_copilot_workspace_is_made_in_the_work_directory(tmp_path, monkeypatch):
    """testing-harness spec: Copilot workspace outside the system temporary
    directory — a run's (and `--preflight-only`'s) workspace comes from the
    host's work directory; Claude's and Codex's stay where they were. The
    account home is the test's own, so the state root in `tmp_path` lies
    outside it wherever the system keeps its temporary directory (inside the
    user's profile on Windows, or under a TMPDIR in the home)."""
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


@pytest.mark.skipif(sys.platform == "win32" or host_login.fcntl is None,
                    reason="the runner refuses --host copilot here as a usage error "
                           "(test_windows_is_a_usage_error)")
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


def shell_done(output: str = "0\n", *, sandboxed: bool = True, code: int | None = 0,
               applied: bool = True, refused: bool = False) -> dict:
    """A 1.0.91 shell completion's `data`, reduced from the first canary's
    recorded shapes (2026-10-07; field paths, words and exit codes only):
    one that ran (`result.content` and `detailedContent`, `shellExecution`,
    `toolTelemetry.properties.sandboxApplied`), or the client's own
    permission refusal before any shell ran (`error.code` `denied`, the
    `permission_denied` category, no `result`, `sandboxed` true all the same)."""
    if refused:
        return {"success": False, "sandboxed": True,
                "error": {"code": "denied", "message": "Permission denied (synthetic)"},
                "toolTelemetry": {"properties": {"shell_error_category": "permission_denied"}}}
    shown = f"{output}<shellId: 3 completed with exit code {code}>"
    data: dict = {"success": True, "sandboxed": sandboxed,
                  "result": {"content": shown, "detailedContent": shown},
                  "toolTelemetry": {"properties": {"sandboxApplied": "true"} if applied else {}}}
    if code is not None:
        data["shellExecution"] = {"exitCode": code}
    return data


def shell_calls(*completions: dict | None) -> list[dict]:
    """Bash starts with the given completions (None: no completion)."""
    events: list[dict] = []
    for i, done in enumerate(completions):
        events.append({"type": "tool.execution_start", "data": {
            "toolCallId": f"s{i}", "toolName": "bash", "arguments": {"command": "true"}}})
        if done is not None:
            events.append({"type": "tool.execution_complete",
                           "data": {"toolCallId": f"s{i}", **done}})
    return events


@pytest.mark.parametrize(("completions", "named"), [
    ((shell_done(refused=True),) * 2, "permission check refused every shell call"),
    ((shell_done(code=None),), "no shell call ran"),
    ((shell_done(refused=True), {**shell_done(refused=True), "sandboxed": False}),
     "not reported as sandboxed"),
    ((shell_done(), None), "not reported as sandboxed"),
    ((shell_done(applied=False),), "not reported as sandboxed"),
    ((), "(no shell call)"),
], ids=["all-refused", "no-exit-code", "refused-unsandboxed", "no-completion",
        "ran-unapplied", "none"])
def test_only_a_shell_call_that_ran_reports_the_sandbox_active(completions, named):
    """testing-harness spec: Shell calls refused by the client confirm
    nothing — the client's permission refusal reports `sandboxed: true` but
    ran nothing (the first canary, 2026-10-07), so only a completion with a
    result and an exit code confirms the sandbox, while every completion
    must still read sandboxed; one that ran must report the sandbox applied
    too (review of task 8.0a), and a run whose every call was refused points
    to the kept permission records."""
    problem = copilot_cli.sandbox_after(shell_calls(*completions))
    assert (problem.untested, problem.kind) == (True, "isolation")
    assert named in problem.message
    refused_only = bool(completions) and all(c and c.get("error") for c in completions)
    assert ("copilot.permission" in problem.message) is refused_only
    assert copilot_cli.sandbox_after(shell_calls(shell_done(refused=True), shell_done())) is None
    assert copilot_cli.shell_refused(shell_done(refused=True))
    assert not copilot_cli.shell_refused(shell_done())
    assert not copilot_cli.shell_ran({**shell_done(), "shellExecution": {"exitCode": True}})


def probe(name: str) -> tuple[object, list[ProbeResult]]:
    data = load(name)
    return data["host_support"]["supported"], [ProbeResult(**r) for r in data["results"]]


@pytest.mark.parametrize(("name", "target", "kind"), [
    ("probe-token-readable", "the token file", "isolation"),
    ("probe-environ-readable", "a token in a process environment or command line", "isolation"),
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
        # a command that printed no exit code never ran: unanswered, not judged
        assert copilot_cli._row_output("tmp_write", {}, host) is None
        assert copilot_cli._row_output("tmp_write", {"output": "denied\n"}, host) is None
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
    # a call that ran must report the sandbox applied too (review of task 8.0a)
    ([_start("t1"), _complete("t1", **shell_done())], None),
    ([_start("t1"), _complete("t1", **shell_done(applied=False))], copilot_cli.UNCONFINED_CALL),
    ([_start("t1"), _complete("t1", **shell_done(refused=True))], None),
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
    (ws / "outside-link.md").symlink_to(secret)
    patch = "*** Begin Patch\n*** Add File: notes.md\n*** Update File: /etc/hosts\n*** End Patch"
    cases = [
        (_file_start("f1", "view", path="sub"), None),
        (_file_start("f2", "view", path=str(ws / "sub")), None),
        (_file_start("f3", "glob", pattern="**/*.md"), None),  # no path: the workspace
        (_file_start("f4", "view", path=str(secret)), copilot_cli.OUTSIDE_FILE),
        (_file_start("f5", "view", path="outside-link.md"), copilot_cli.OUTSIDE_FILE),
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
    assert watch.event_line(json.dumps(_file_start("f5", "view", path="outside-link.md")))
    assert watch.breach == copilot_cli.OUTSIDE_FILE
    assert secret.read_text(encoding="utf-8") == "synthetic"


def _staged_tree(ws: Path) -> Path:
    """A staged skill tree with one skill and one regular file; returns its root."""
    skill = ws / ".agents" / "skills" / "proposal-check"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: proposal-check\n---\nbody\n", encoding="utf-8")
    (skill / "scripts").mkdir()
    (skill / "scripts" / "check.py").write_text("print(1)\n", encoding="utf-8")
    return ws / ".agents" / "skills"


@POSIX
def test_staged_digest_fingerprints_files_dirs_and_unsafe_entries(tmp_path):
    """The before/after fingerprint of the staged skill tree: a regular file by
    its sha256, a directory as `dir`, and a link, FIFO or hard link as `UNSAFE`;
    an absent or link-replaced tree is empty."""
    ws = tmp_path / "ws"
    _staged_tree(ws)
    digest = copilot_cli.staged_digest(ws)
    assert digest["proposal-check/SKILL.md"] == hashlib.sha256(
        b"---\nname: proposal-check\n---\nbody\n").hexdigest()
    assert digest["proposal-check"] == "dir"
    assert digest["proposal-check/scripts"] == "dir"
    secret = tmp_path / "secret"
    secret.write_text("synthetic", encoding="utf-8")
    (ws / ".agents" / "skills" / "proposal-check" / "SKILL.md").unlink()
    (ws / ".agents" / "skills" / "proposal-check" / "SKILL.md").symlink_to(secret)
    os.mkfifo(ws / ".agents" / "skills" / "proposal-check" / "pipe")
    after = copilot_cli.staged_digest(ws)
    assert after["proposal-check/SKILL.md"].startswith("UNSAFE:")
    assert after["proposal-check/pipe"].startswith("UNSAFE:")
    assert secret.read_text(encoding="utf-8") == "synthetic"  # the link was never followed
    assert copilot_cli.staged_digest(tmp_path / "none") == {}  # absent tree
    (tmp_path / "link-ws" / ".agents" / "skills").parent.mkdir(parents=True)
    (tmp_path / "link-ws" / ".agents" / "skills").symlink_to(tmp_path)
    assert copilot_cli.staged_digest(tmp_path / "link-ws") == {}  # tree replaced by a link


def test_staged_changes_names_what_the_sandboxed_shell_changed():
    before = {"a/SKILL.md": "sha1", "a": "dir", "b/SKILL.md": "sha2", "c/SKILL.md": "sha3"}
    after = {"a/SKILL.md": "UNSAFE:a link", "a": "dir", "b/SKILL.md": "sha2changed",
             "d/SKILL.md": "sha4", "e/SKILL.md": "UNSAFE:a link"}
    found = copilot_cli.staged_changes(before, after)
    assert "a/SKILL.md became a link" in found
    assert "b/SKILL.md changed" in found
    assert "c/SKILL.md removed" in found
    assert "d/SKILL.md added" in found
    assert "e/SKILL.md added (a link)" in found
    assert copilot_cli.staged_changes(before, before) == []  # no change, no finding
    big = {str(i): "x" for i in range(copilot_cli.SHOWN_SKILL_CHANGES + 5)}
    assert len(copilot_cli.staged_changes({}, big)) == copilot_cli.SHOWN_SKILL_CHANGES


@POSIX
def test_a_skill_tool_call_stops_the_run_when_the_staged_tree_holds_a_link(tmp_path):
    """testing-harness spec: Skill read outside the staged tree stops the run.
    The client's `skill` tool reads its SKILL.md in the client's own process,
    outside the sandbox, and follows a link; its start names the skill, not a
    path, so on a `skill` start the watch checks the staged tree for a planted
    link rather than a path (`skill.invoked`, with the path, never reaches
    stdout)."""
    ws = tmp_path / "ws"
    _staged_tree(ws)
    start = _file_start("s1", "skill", skill="proposal-check")
    assert copilot_cli.breach_of(start, set(), ws) is None  # clean tree, no breach
    assert copilot_cli.breach_of(start, set()) is None  # no workspace, no check
    secret = tmp_path / "secret"
    secret.write_text("synthetic", encoding="utf-8")
    skillmd = ws / ".agents" / "skills" / "proposal-check" / "SKILL.md"
    skillmd.unlink()
    skillmd.symlink_to(secret)
    assert copilot_cli.breach_of(start, set(), ws) == copilot_cli.SKILL_LINK
    mcp = _file_start("s2", "skill", skill="proposal-check")
    mcp["data"]["mcpServerName"] = "github-mcp-server"
    assert copilot_cli.breach_of(mcp, set(), ws) is None  # an MCP tool, not the client's skill
    watch = copilot_cli.ConfinementWatch(ws)
    assert watch.event_line(json.dumps(start))
    assert watch.breach == copilot_cli.SKILL_LINK
    assert secret.read_text(encoding="utf-8") == "synthetic"  # the watch followed no link


def test_a_changed_staged_skill_is_untested_for_isolation_and_stops():
    """testing-harness spec: Staged skill changed during the run — pure over the
    saved events: the harness record names what changed."""
    events = stream("success")
    harness = copilot_cli.harness_record(events)
    harness["skill_findings"] = ["proposal-check/SKILL.md became a link"]
    assessment = copilot_cli.assess(events)
    assert assessment.problem.untested
    assert assessment.problem.kind == "isolation"
    assert copilot_cli.SKILL_TAMPER in assessment.problem.message
    assert "became a link" in assessment.problem.message  # the entry named
    assert ("isolation", f"{copilot_cli.SKILL_TAMPER}: proposal-check/SKILL.md became a link") in (
        assessment.stops)


@POSIX
def test_a_link_planted_over_a_staged_skill_stops_the_run(home, tmp_path, monkeypatch):
    """End to end: a sandboxed shell that replaced a staged SKILL.md with a link
    to a file under a denied path (the client's `skill` tool would follow it) is
    caught after the run by the staged-tree comparison — untested for isolation,
    the link unlinked unread, its target untouched, with the tamper stop."""
    skip_scan(monkeypatch)
    ws = staged_ws(tmp_path)
    secret = tmp_path / "secret"
    secret.write_text("SYNTHETIC-SKILL-SECRET", encoding="utf-8")
    link = ws / ".agents" / "skills" / "proposal-check" / "SKILL.md"
    fake_copilot(tmp_path, monkeypatch, links={str(link): str(secret)})
    events = copilot_cli.run_copilot(ws, "check", model="copilot-fixture-a", effort=None,
                                     cap=30, timeout=30, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    problem = copilot_cli.run_problem(events)
    assert problem.untested
    assert problem.kind == "isolation"
    assert copilot_cli.SKILL_TAMPER in problem.message
    assert "proposal-check/SKILL.md" in problem.message
    assert "SYNTHETIC-SKILL-SECRET" not in json.dumps(events)
    assert secret.read_text(encoding="utf-8") == "SYNTHETIC-SKILL-SECRET"  # never followed
    assert not link.is_symlink()  # the workspace check unlinked it unread
    assert copilot_cli.read_stop(home)["kind"] == "isolation"
    assert copilot_cli.SKILL_TAMPER in copilot_cli.read_stop(home)["cause"]


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
                                 tmp_path / "devrun-probe-write-x",
                                 tmp_path / "devrun-probe-var-x")
    commands = dict(copilot_cli.probe_commands(token_file=tmp_path / "copilot.token",
                                               harness_pid=4343,
                                               account=account, uid=1000,
                                               script=tmp_path / "check.py", host=host))
    assert set(commands) == {*copilot_cli.READ_TARGETS, *copilot_cli.AUTH_TARGETS, "python",
                             "skill_script", *copilot_cli.TMP_TARGETS,
                             *copilot_cli.MEASURED_TARGETS}
    for name in (*copilot_cli.READ_TARGETS, "host_tmp", "var_tmp"):
        if name == "client_environ":  # the content scan (test_the_content_scan_*)
            continue
        assert commands[name].endswith("&& echo readable || echo denied")
        assert ">/dev/null 2>&1" in commands[name] or name == "token_env"
    assert str(host.var_sentinel) in commands["var_tmp"]
    # the shell's own environment: set (even empty) reads `readable`; no value
    # is ever expanded, only whether each name is set
    assert commands["token_env"] == (
        '[ -n "${COPILOT_GITHUB_TOKEN+x}${GH_TOKEN+x}${GITHUB_TOKEN+x}" ] && echo readable '
        "|| echo denied")
    for value, word in (({}, "denied"), ({"GH_TOKEN": ""}, "readable"),
                        ({"COPILOT_GITHUB_TOKEN": "x"}, "readable")):
        shell = subprocess.run(["sh", "-c", commands["token_env"]], capture_output=True,
                               text=True, env={"PATH": os.environ.get("PATH", ""), **value},
                               check=False)
        assert shell.stdout.strip() == word, value
    # the client's environment is searched by content, never by a host pid,
    # which does not exist in the sandbox's own pid namespace (the second canary)
    assert commands["client_environ"] == copilot_cli.token_scan()
    assert not re.search(r"/proc/\d", commands["client_environ"])
    assert "/proc/4343/environ" in commands["harness_environ"]
    assert "unix:path=/run/user/1000/bus" in commands["gh_token"]
    # git runs with the operator's own home, configuration, GitHub CLI directory
    # and session bus, so a configured credential helper is reached unless the
    # sandbox denies it; the child's scratch home holds none
    git = commands["git_credential"]

    def quoted(path: Path) -> str:  # a path as the shell command spells it
        return shlex.quote(str(path))

    for needle in (f"HOME={quoted(account)}", f"XDG_CONFIG_HOME={quoted(account / '.config')}",
                   f"GH_CONFIG_DIR={quoted(account / '.config' / 'gh')}",
                   "unix:path=/run/user/1000/bus",
                   "GIT_TERMINAL_PROMPT=0", "GIT_ASKPASS=/bin/false", "GCM_INTERACTIVE=never",
                   ">/dev/null 2>&1; echo $?"):
        assert needle in git, needle
    assert "'net:[4026531840]'" in commands["net_ns"]
    assert commands["net_ns"].count("echo ") == 3  # unknown, shared, private
    assert commands["tmp_write"] == f": > {quoted(host.marker)} 2>/dev/null; echo $?"
    # without a host side, the host rows are left out (the /tmp ones then read
    # as no answer, test_the_host_tmp_rows_refuse_unless_denied)
    bare = dict(copilot_cli.probe_commands(token_file=tmp_path / "t",
                                           harness_pid=2, account=account, uid=1000, script=None))
    assert not set(bare) & {*copilot_cli.MEASURED_TARGETS, *copilot_cli.TMP_TARGETS,
                            *copilot_cli.STAGED_TARGETS}
    # `staged_ro` is asked over a staged SKILL.md only (`staged_target`)
    staged = tmp_path / "ws" / ".agents" / "skills" / "proposal-check" / "SKILL.md"
    with_tree = dict(copilot_cli.probe_commands(token_file=tmp_path / "t", harness_pid=2,
                                                account=account, uid=1000, script=None,
                                                staged=staged))
    assert set(with_tree) - set(bare) == set(copilot_cli.STAGED_TARGETS)
    assert with_tree["staged_ro"] == copilot_cli.staged_command(staged)


def staged_tree(tmp_path: Path, name: str = "proposal-check") -> tuple[Path, Path]:
    """A workspace with one staged skill; its `SKILL.md`."""
    ws = tmp_path / "ws"
    skill = ws / ".agents" / "skills" / name / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: x\n---\n", encoding="utf-8")
    return ws, skill


def test_the_staged_command_is_one_line_naming_the_tree_and_no_output(tmp_path):
    """testing-harness spec: Staged tree rename refused — `staged_ro` tries
    the rename of `.agents` aside, a new file in it and a link over the
    staged `SKILL.md`, each with its errors discarded, and prints one word."""
    ws, skill = staged_tree(tmp_path)
    command = copilot_cli.staged_command(skill)
    assert "\n" not in command
    quoted = {name: shlex.quote(str(path)) for name, path in (
        ("f", skill), ("a", ws / ".agents"), ("b", ws / copilot_cli.STAGED_ASIDE),
        ("n", ws / ".agents" / copilot_cli.STAGED_PROBE_FILE))}
    for name, value in quoted.items():
        assert f"{name}={value};" in command
    for attempt in ('mv "$a" "$b" 2>/dev/null', 'touch "$n" 2>/dev/null',
                    'ln -sf /dev/null "$f" 2>/dev/null'):
        assert attempt in command
    assert set(re.findall(r"echo (\w+)", command)) == {"unknown", "denied", "writable"}
    assert all(copilot_cli.PROBE_WORD.match(w) for w in ("unknown", "denied", "writable"))


@POSIX
def test_the_staged_command_reads_writable_on_a_writable_tree_and_undoes_what_it_can(tmp_path):
    """Run by `sh` over a synthetic tree only: on a writable tree the rename
    and the new file succeed and are undone at once, the link stays (the
    run is refused before its child); a tree the shell cannot see reads
    `unknown`."""
    ws, skill = staged_tree(tmp_path)

    def word() -> str:
        return subprocess.run(["sh", "-c", copilot_cli.staged_command(skill)], capture_output=True,
                              text=True, check=True).stdout.strip()

    assert word() == "writable"
    assert (ws / ".agents").is_dir()  # the rename undone
    assert not (ws / copilot_cli.STAGED_ASIDE).exists()
    assert not (ws / ".agents" / copilot_cli.STAGED_PROBE_FILE).exists()  # the file removed
    assert skill.is_symlink()  # the link stays, for the checks that follow
    skill.unlink()
    assert word() == "unknown"


@ROOTLESS
def test_the_staged_command_reads_denied_when_every_attempt_fails(tmp_path):
    """The bind's effect, approximated on the host by modes (the sandbox's own
    reading is the probe's and the canary's): no rename of `.agents`, no file
    in it, no link over the `SKILL.md` — `denied`, and the tree unchanged."""
    ws, skill = staged_tree(tmp_path)
    closed = (skill.parent, ws / ".agents", ws)
    for folder in closed:
        folder.chmod(0o500)
    try:
        out = subprocess.run(["sh", "-c", copilot_cli.staged_command(skill)],
                             capture_output=True, text=True, check=True)
    finally:
        for folder in reversed(closed):
            folder.chmod(0o700)
    assert (out.stdout.strip(), out.stderr) == ("denied", "")
    assert not skill.is_symlink()
    assert sorted(p.name for p in ws.iterdir()) == [".agents"]


@pytest.mark.parametrize(("platform", "guarded"), [
    ("linux", True), ("darwin", False), ("win32", False)])
def test_the_staged_row_follows_the_pinned_read_only_entry(platform, guarded, tmp_path):
    """`staged_ro` is asked where the pinned settings carry the read-only
    entry (`host_login.readonly_paths`: Linux), over the first regular staged
    `SKILL.md`; never over a link, and not without a staged tree."""
    assert copilot_cli.guards_staged(platform) is guarded
    assert copilot_cli.staged_target(tmp_path / "empty", platform) is None
    ws, skill = staged_tree(tmp_path, "proposal-b")
    first = ws / ".agents" / "skills" / "proposal-a" / "SKILL.md"
    first.parent.mkdir()
    if os.name == "posix":
        first.symlink_to(skill)  # a link is never the row's target
    assert copilot_cli.staged_target(ws, platform) == (skill if guarded else None)


@pytest.mark.parametrize(("rows", "staged", "kind", "named"), [
    ({"staged_ro": "writable"}, True, "isolation", "the staged skill tree"),
    ({"staged_ro": "writable"}, False, "isolation", "the staged skill tree"),  # asked: judged
    ({"staged_ro": "unknown"}, True, "isolation", "the staged skill tree"),
    ({"staged_ro": None}, True, "precondition", "gave no answer for staged_ro"),
    ({}, True, "precondition", "gave no answer for staged_ro"),
    ({}, False, None, None),  # a baseline run: no staged tree, no row
    ({"staged_ro": "denied"}, True, None, None),
])
def test_the_staged_row_refuses_unless_denied_and_is_required_where_staged(rows, staged, kind,
                                                                           named):
    """testing-harness spec: Staged skill tree read-only in the sandbox; Staged
    tree rename refused — the row reads `denied` or refuses for isolation,
    naming the tree and never the word; where the tree is guarded and a
    skill is staged, a missing answer refuses as a precondition."""
    supported, results = probe("probe-ok")
    results = [r for r in results if r.name != "staged_ro"]
    results += [ProbeResult(name, word, True) for name, word in rows.items()]
    problem = copilot_cli.probe_problem(results, supported, staged=staged)
    if kind is None:
        assert problem is None
        return
    assert (problem.kind, named in problem.cause) == (kind, True)
    assert not re.search(r"\b(?:writable|unknown|denied)\b", refusal(problem))


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


@POSIX_RECORDS
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


@POSIX_RECORDS
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


def test_every_skill_record_is_kept_by_name_and_source_only():
    """design Decision 9 (added 2026-10-13, task 8.1a): `skill.invoked_ref` is
    read as `skill.invoked`; `skill.context_delivered` and its receipt keep
    their event and source, never the delivered wrapper or its id (1.0.91
    `session-events.schema.json`, the shapes the first skill run recorded)."""
    lines = [json.dumps(line) for line in (
        {"type": "skill.invoked_ref", "data": {
            "name": "proposal-check", "path": "/ws/.agents/skills/proposal-check/SKILL.md",
            "source": "project", "trigger": "agent-invoked", "contentId": "sha256:ab",
            "contentLength": 9}},
        {"type": "skill.context_delivered", "data": {
            "content": "SKILL WRAPPER TEXT", "source": "skill-proposal-check",
            "interactionId": "i1"}},
        {"type": "skill.context_delivered_ref", "data": {
            "contentId": "sha256:cd", "prefix": "PREFIX TEXT", "suffix": "SUFFIX TEXT",
            "source": "skill-proposal-check"}},
        {"type": "skill.context_delivered_ref", "data": {"contentId": "sha256:ef"}})]
    records = copilot_cli.reduce_session(lines)
    assert records == [
        {"type": "copilot.skill_invoked", "name": "proposal-check",
         "path": "/ws/.agents/skills/proposal-check/SKILL.md", "source": "project",
         "trigger": "agent-invoked"},
        {"type": "copilot.skill_context", "event": "skill.context_delivered",
         "source": "skill-proposal-check"},
        {"type": "copilot.skill_context", "event": "skill.context_delivered_ref",
         "source": "skill-proposal-check"},
        {"type": "copilot.skill_context", "event": "skill.context_delivered_ref", "source": None}]
    text = json.dumps(records)
    for dropped in ("SKILL WRAPPER TEXT", "PREFIX TEXT", "SUFFIX TEXT", "sha256:", "i1"):
        assert dropped not in text
    assert set(copilot_cli.SKILL_RECORDS) <= set(copilot_cli.SESSION_REDUCERS)


def test_the_permission_records_are_kept_without_the_command_and_scrubbed(tmp_path):
    """testing-harness spec: Invocation on Copilot — the session file's
    `permission.requested` and `permission.completed` (1.0.91 schema:
    `permissionRequest` kind `shell`, `promptRequest` kind `path` with
    `accessKind` and `paths`, `result.kind`) are kept as `copilot.permission`
    records, never with the command text, and scrubbed of the token."""
    secret = f"/x/{TOKEN}/y"
    requested = {"type": "permission.requested", "data": {
        "requestId": "r1", "permissionRequest": {
            "kind": "shell", "toolCallId": "c0", "fullCommandText": "cat /home/x/secret-command",
            "intention": "read it", "possiblePaths": ["/home/x/secret-command"]},
        "promptRequest": {"kind": "path", "toolCallId": "c0", "accessKind": "shell",
                          "paths": [*[f"/p/{i}" for i in range(12)], secret]}}}
    completed = {"type": "permission.completed", "data": {
        "requestId": "r1", "toolCallId": "c0", "decisionSource": "unattended_fallback",
        "result": {"kind": "denied-no-approval-rule-and-could-not-request-from-user"}}}
    folder = tmp_path / copilot_cli.SESSION_STATE / SID
    folder.mkdir(parents=True)
    (folder / "events.jsonl").write_text(
        "".join(json.dumps(e) + "\n" for e in (requested, completed)), encoding="utf-8")
    records, hit = copilot_cli.capture_session(tmp_path, SID, TOKEN)
    asked, answered = [r for r in records if r["type"] == "copilot.permission"]
    assert asked == {"type": "copilot.permission", "event": "permission.requested",
                     "requestId": "r1", "toolCallId": "c0", "kind": "shell", "prompt": "path",
                     "accessKind": "shell", "result": None, "decisionSource": None,
                     "paths": [f"/p/{i}" for i in range(copilot_cli.SHOWN_PERMISSION_PATHS)]}
    assert answered["result"] == "denied-no-approval-rule-and-could-not-request-from-user"
    assert (answered["toolCallId"], answered["decisionSource"]) == ("c0", "unattended_fallback")
    assert "secret-command" not in json.dumps(records)
    assert not folder.exists()
    folder.mkdir(parents=True)  # a token in a kept path is scrubbed before the reduction
    (folder / "events.jsonl").write_text(json.dumps({**requested, "data": {
        **requested["data"], "promptRequest": {"kind": "path", "paths": [secret]}}}) + "\n",
        encoding="utf-8")
    records, hit = copilot_cli.capture_session(tmp_path, SID, TOKEN)
    assert hit
    assert TOKEN not in json.dumps(records)


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


# ---------- 8.1a: the loaded skills without the report (the first skill run, 2026-10-13) ----


@POSIX_RECORDS
def test_a_run_without_the_report_is_confirmed_by_its_roster_and_records():
    """testing-harness spec: Loaded skills confirmed without the report — the
    shape the first skill run recorded: no `session.skills_loaded` anywhere,
    the roster and the staged names in the runner's record, the session file
    read, an invocation and a context receipt naming the staged skill."""
    events = stream("skills-by-roster")
    assert not [e for e in events if e.get("type") == "session.skills_loaded"]
    assert copilot_cli.isolation_findings(events, copilot_cli.harness_record(events)) == []
    assert copilot_cli.run_problem(events) is None


def _harness_with(events: list[dict], **fields) -> list[dict]:
    """The stream with its runner's record changed (a key set to None is dropped)."""
    harness = {**copilot_cli.harness_record(events), **fields}
    harness = {key: value for key, value in harness.items() if value is not None}
    return [*(e for e in events if e.get("type") != "copilot.harness"), harness]


def _without(events: list[dict], kind: str) -> list[dict]:
    return [e for e in events if e.get("type") != kind]


def _types(events: list[dict], *extra: str) -> list[dict]:
    record = copilot_cli._last(events, "copilot.session_types")
    return [*_without(events, "copilot.session_types"),
            {**record, "types": [*record["types"], *extra]}]


def _skill_record(events: list[dict], **record) -> list[dict]:
    at = next(i for i, e in enumerate(events) if e.get("type") == "copilot.shutdown")
    return [*events[:at], record, *events[at:]]


BUNDLED = list(copilot_cli.BUILTIN_SKILLS)


@pytest.mark.parametrize(("change", "named"), [
    (lambda e: _harness_with(e, roster=None), "no skill listing recorded before the child"),
    (lambda e: _harness_with(e, roster=[]), "no skill listing recorded before the child"),
    (lambda e: _harness_with(e, staged=None), "no skill listing recorded before the child"),
    (lambda e: _harness_with(e, roster=[*BUNDLED, "proposal-check", "proposal-review"]),
     "is not the staged skills (proposal-check)"),
    (lambda e: _harness_with(e, roster=BUNDLED), "is not the staged skills"),
    (lambda e: _harness_with(e, roster=["personal-skill", "proposal-check"]),
     "is not the staged skills"),
    (lambda e: _without(e, "copilot.session_start"), "the session file was not read"),
    (lambda e: _without(e, "copilot.session_types"), "the session file was not read"),
    (lambda e: _types(e, "skill.preloaded"), "skill records the runner cannot check "
                                             "(skill.preloaded)"),
    (lambda e: _skill_record(e, type="copilot.skill_context",
                             event="skill.context_delivered_ref", source="skill-foreign"),
     "skill context delivered from skill-foreign"),
    (lambda e: _skill_record(e, type="copilot.skill_context",
                             event="skill.context_delivered_ref", source=None),
     "skill context delivered from an unnamed source"),
    (lambda e: _skill_record(e, type="copilot.skill_invoked", name="proposal-check",
                             path="/elsewhere/proposal-check/SKILL.md", source="project",
                             trigger="agent-invoked"),
     "invoked from source project (/elsewhere/proposal-check/SKILL.md)"),
    (lambda e: _skill_record(e, type="copilot.skill_invoked", name="proposal-review",
                             path=str(WS / ".agents/skills/proposal-review/SKILL.md"),
                             source="project", trigger="agent-invoked"),
     "skill proposal-review invoked from source project"),
    (lambda e: _skill_record(e, type="copilot.skill_invoked", name="discover-resources",
                             path="/pkg/builtin-skills/discover-resources/SKILL.md",
                             source="builtin", trigger="agent-invoked"),
     "skill discover-resources invoked from source builtin"),
    (lambda e: _skill_record(e, type="copilot.skill_invoked", name="helper",
                             path="/home/x/.agents/skills/helper/SKILL.md",
                             source="personal-agents", trigger="agent-invoked"),
     "invoked from source personal-agents"),
], ids=["no-roster", "empty-roster", "no-staged", "roster-beyond", "roster-short",
        "roster-foreign", "no-session-start", "no-session-types", "unread-type",
        "foreign-context", "unnamed-context", "project-elsewhere", "project-unstaged",
        "builtin-unlisted", "personal"])
def test_the_loaded_skills_stay_unconfirmed_without_positive_evidence(change, named):
    """testing-harness spec: Loaded skills unreported; Loaded skills not
    confirmed by the record — every part of the evidence must be there and
    match; an absence never passes."""
    events = change(stream("skills-by-roster"))
    problem = copilot_cli.assess(events).problem
    assert (problem.untested, problem.kind) == (True, "isolation")
    assert named in problem.message


@POSIX_RECORDS
def test_a_bundled_skill_the_roster_listed_may_be_invoked():
    events = _skill_record(stream("skills-by-roster"), type="copilot.skill_invoked",
                           name="github-pr-media", path="/pkg/builtin/github-pr-media/SKILL.md",
                           source="builtin", trigger="agent-invoked")
    events = _skill_record(events, type="copilot.skill_context",
                           event="skill.context_delivered_ref", source="skill-github-pr-media")
    assert copilot_cli.run_problem(events) is None
    # a roster without it: listed bundled names only
    events = _harness_with(events, roster=["customize-cloud-agent", "proposal-check"])
    assert "github-pr-media invoked from source builtin" in copilot_cli.run_problem(
        events).message


@POSIX_RECORDS
def test_a_report_that_arrives_is_still_compared_with_the_roster():
    """The report, when present, is positive evidence of its own and must name
    the roster; the skill records are checked either way."""
    events = stream("success")
    assert copilot_cli.run_problem(events) is None
    loaded = copilot_cli._last(events, "session.skills_loaded")
    loaded["data"]["skills"] = loaded["data"]["skills"][:1]
    assert "differ from the listing" in copilot_cli.run_problem(events).message
    events = _skill_record(stream("success"), type="copilot.skill_context",
                           event="skill.context_delivered", source="skill-foreign")
    assert "skill context delivered from skill-foreign" in copilot_cli.run_problem(
        events).message


def test_a_canary_records_the_confirmation_rather_than_requiring_it(tmp_path):
    """The canary stages only its placeholder skill (since 2026-10-13): its
    roster is the bundled names and the placeholder, and its own record turns
    the requirement off (Decision 13, passing)."""
    events = canary_events(tmp_path)
    assert copilot_cli.isolation_findings(events, copilot_cli.harness_record(events),
                                          loaded=False) == []
    assert copilot_cli.assess(events).problem is None


@POSIX
def test_a_skill_run_without_the_report_passes_end_to_end(home, tmp_path, monkeypatch):
    """task 8.1a, end to end through the fake client: the runner records the
    staged names beside the roster, reduces the context receipt from the
    session file, and confirms the loaded skills without the report."""
    skip_scan(monkeypatch)
    fake_copilot(tmp_path, monkeypatch, run="skills-by-roster")
    ws = staged_ws(tmp_path)
    events = copilot_cli.run_copilot(ws, "Please check my proposal broken-format.md.",
                                     model="copilot-fixture-a", effort=None, cap=30,
                                     timeout=30, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    harness = copilot_cli.harness_record(events)
    assert harness["staged"] == ["proposal-check"]
    assert set(harness["roster"]) == {*BUNDLED, "proposal-check"}
    assert {"type": "copilot.skill_context", "event": "skill.context_delivered_ref",
            "source": "skill-proposal-check"} in events
    assert "skill.context_delivered_ref" in copilot_cli._last(
        events, "copilot.session_types")["types"]
    assert copilot_cli.isolation_findings(events, harness) == []


@POSIX_RECORDS
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


@POSIX_RECORDS
def test_a_helpers_second_model_does_not_make_the_run_untested():
    assert copilot_cli.run_problem(stream("helper-spawn")) is None


@POSIX_RECORDS
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


@POSIX_RECORDS
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


@POSIX_RECORDS
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


@POSIX_RECORDS
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
    """A clean skill run records no finding; the one stop after it is the
    approval stop its start recorded, which ended its go (Decision 9)."""
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
    # the probe's and the run's process logs were scanned, found clean and deleted
    assert copilot_cli.harness_record(events)["log_findings"] == 0
    assert list(host_login.log_dir(home).iterdir()) == []
    assert sessions(home) == []  # pruned
    assert copilot_cli.read_stop(home) == {"kind": "approval", "cause": copilot_cli.GO_USED,
                                           "at": copilot_cli.read_stop(home)["at"]}
    assert copilot_cli.read_go(home) is None
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
    # `staged_ro` where the pinned settings guard the staged tree (Linux)
    staged = copilot_cli.guards_staged()
    assert {r.name for r in found.results} == {
        *copilot_cli.READ_TARGETS, *copilot_cli.AUTH_TARGETS, "python", "skill_script",
        *copilot_cli.TMP_TARGETS, *copilot_cli.MEASURED_TARGETS,
        *(copilot_cli.STAGED_TARGETS if staged else ())}
    assert all(r.sandboxed is True for r in found.results)
    assert copilot_cli.probe_problem(found.results, found.supported, found.unapplied,
                                     staged=staged) is None
    by = {r.name: r.output for r in found.results}
    assert by["tmp_write"] == "denied"  # judged on the host: the fake wrote nothing there
    assert list(host_tmp.iterdir()) == []  # the sentinel removed
    # the run's scratch home lies in the work directory, never in a temporary directory
    assert run.scratch.parent == copilot_cli.work_root()
    assert sessions(home) == []
    assert calls(log)[0]["cwd"] == str(ws)
    argv = calls(log)[0]["argv"]
    # the probe's server logs where the deny list names the directory, never
    # under scratch, which the client would bind into the sandbox (2026-10-13)
    assert argv[argv.index("--log-dir") + 1] == str(host_login.log_dir(home))
    assert str(host_login.log_dir(home)) in host_login.deny_list(home, host_login.account_home())
    assert not (home / "logs").exists()
    # testing-harness spec: Copilot children name the token variable
    assert "--no-auto-login" in argv
    assert _contains(argv, list(copilot_cli.TOKEN_FLAGS))
    assert TOKEN not in json.dumps(argv)
    assert "--sandbox" not in argv  # changes nothing on the server (K6 diagnosis)


@POSIX
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
    assert found.trial is None  # a skill run's probe runs no canary script
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
    assert [by[n].output for n in copilot_cli.READ_TARGETS] == (
        ["readable"] * len(copilot_cli.READ_TARGETS))
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


GUARDED = pytest.mark.skipif(not copilot_cli.guards_staged(),
                             reason="the pinned settings guard the staged tree on Linux")


@POSIX
@GUARDED
def test_a_writable_staged_tree_refuses_the_skill_run_before_its_child(home, tmp_path,
                                                                      monkeypatch):
    """testing-harness spec: Staged tree rename refused — end to end through
    the fake client: the probe asks `staged_ro` over the staged
    `proposal-check`, reads `writable`, and the run is refused for isolation
    before any prompt-mode child, naming the staged tree, never the word."""
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch, probe="probe-staged-writable")
    ws = staged_ws(tmp_path)
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.run_copilot(ws, "check", model="copilot-fixture-a", effort=None, cap=30,
                                timeout=30, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    assert refused.value.kind == "isolation"
    assert "the staged skill tree" in refused.value.message
    assert "writable" not in refused.value.message
    assert "run" not in [c["kind"] for c in calls(log)]
    skill = ws / ".agents" / "skills" / "proposal-check" / "SKILL.md"
    asked = [c["params"]["command"] for c in rpc_calls(log)
             if c["method"] == SHELL and copilot_cli.STAGED_ASIDE in c["params"]["command"]]
    assert asked == [copilot_cli.staged_command(skill)]


@POSIX
@GUARDED
def test_a_staged_skill_without_its_row_refuses_the_probe(home, tmp_path, monkeypatch):
    """Where the tree is guarded and the roster recorded a staged skill, a
    probe that did not ask `staged_ro` measured nothing: refused as a
    precondition, before any prompt-mode child."""
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch)
    monkeypatch.setattr(copilot_cli, "staged_target", lambda *_a, **_k: None)
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                effort=None, cap=30, timeout=30, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    assert refused.value.kind == "precondition"
    assert "gave no answer for staged_ro" in refused.value.message
    assert "run" not in [c["kind"] for c in calls(log)]


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
    assert list(by)[-3:] == ["confinement_probe", "process_logs", "clean_after_reads"]
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
    assert names == ["location", "home", "clean", "token", "stop", "go", "version",
                     "managed_settings", "sandbox_tools", "ptrace_scope", "workspace", "status",
                     "model", "rosters", "confinement_probe", "process_logs", "clean_after_reads"]
    assert ready is True  # neither the stop nor the go decides the outcome
    assert next(c for c in checks if c.name == "clean_after_reads").problem is None
    stop = next(c for c in checks if c.name == "stop")
    assert stop.problem is not None
    assert "approval" in stop.detail
    go = next(c for c in checks if c.name == "go")  # the stop ended the fixture's go
    assert (go.detail, "no go is recorded" in go.problem.cause) == ("none", True)
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
    assert list(by)[-6:] == ["status", "model", "rosters", "confinement_probe",
                             "process_logs", "clean_after_reads"]
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


# ---------- 8.0: the canary (the user's decision D-c) ------------------------------------------

SID = "22222222-2222-4222-8222-222222222222"
PROBE_OK_WORDS = {r["name"]: r["output"] for r in load("probe-ok")["results"]}  # type: ignore[index]


def placeholder(tmp_path: Path) -> Path:
    """The canary's placeholder `SKILL.md` in `<tmp_path>/ws`, never created."""
    return tmp_path / "ws" / ".agents" / "skills" / copilot_cli.CANARY_SKILL / "SKILL.md"


def canary_cmds(tmp_path: Path, net_ns: str | None = "net:[4026531840]") -> list[tuple[str, str]]:
    """The canary's commands as Linux builds them: `staged_ro` over the
    placeholder skill among them."""
    host = copilot_cli.ProbeHost(net_ns, tmp_path / "devrun-probe-tmp-x",
                                 tmp_path / "devrun-probe-write-x",
                                 tmp_path / "devrun-probe-var-x")
    return copilot_cli.canary_commands(token_file=tmp_path / "copilot.token",
                                       harness_pid=4343, account=tmp_path / "account", uid=1000,
                                       host=host, staged=placeholder(tmp_path))


SCRIPT_SHA = "a" * 64  # the canary script's digest as the runner records it


def script_output(words: dict, names: list[str], *, skip: tuple = (), repeat: tuple = (),
                  closed: bool = True) -> str:
    """What the canary's script prints: one tagged line per row, then its
    closing line."""
    lines = [f"canary {n} {words[n]}" for n in names if n not in skip]
    lines += [f"canary {n} {words[n]}" for n in repeat]
    return "\n".join([*lines, *([copilot_cli.CANARY_END] if closed else [])]) + "\n"


def canary_events(tmp_path: Path, *, words: dict | None = None, skip: tuple = (),
                  repeat: tuple = (), closed: bool = True, done: dict | None = None,
                  command: str = copilot_cli.CANARY_RUN, rerun: bool = False, extra: int = 0,
                  script_after: str | None = SCRIPT_SHA, tmp_seen: bool = False,
                  guard: str | None = None, loaded: bool = False,
                  net_ns: str | None = "net:[4026531840]", **shape) -> list[dict]:
    """A synthetic canary run, as the runner saves it: the client's one bash
    call of the fixed command and its completion (`shell_done`, its output
    the script's tagged lines), any further shell calls, the closing result
    line, the reduced session records and the runner's own records.
    `net_ns=None` is a host that could not read its own namespace, so no
    `net_ns` row is asked."""
    words = {**PROBE_OK_WORDS, "tmp_write": "0", **(words or {})}
    events: list[dict] = []
    commands = canary_cmds(tmp_path, net_ns)
    output = script_output(words, [n for n, _ in commands], skip=skip, repeat=repeat,
                           closed=closed)
    call = done if done is not None else shell_done(output, **shape)
    calls = [(command, call), *([(command, call)] if rerun else []),
             *[(f"echo extra {i}", shell_done()) for i in range(extra)]]
    for i, (ran, data) in enumerate(calls):
        events.append({"type": "tool.execution_start", "data": {
            "toolCallId": f"c{i}", "toolName": "bash", "arguments": {"command": ran}}})
        events.append({"type": "tool.execution_complete",
                       "data": {"toolCallId": f"c{i}", **data}})
    if loaded:
        events.insert(0, {"type": "session.skills_loaded", "data": {"skills": []}})
    snapshot = {"overage_count": 0, "remaining_pct": 99.7}
    events += [
        {"type": "assistant.message", "data": {"content": "done", "model": "copilot-fixture-a"}},
        {"type": "result", "sessionId": SID, "exitCode": 0},
        {"type": "copilot.session_start", "copilotVersion": "1.0.91"},
        {"type": "copilot.shutdown", "shutdownType": "routine", "totalPremiumRequests": 0,
         "totalNanoAiu": 1_500_000_000, "modelMetrics": {"copilot-fixture-a": {
             "usage": {"inputTokens": 900, "outputTokens": 90}, "totalNanoAiu": 1_500_000_000}}},
        {"type": "copilot.session_types", "types": ["session.shutdown", "session.start",
                                                    "tool.execution_complete"]},
        {"type": "copilot.canary", "commands": [list(pair) for pair in commands],
         "tmp_seen": tmp_seen, "script_sha256": SCRIPT_SHA, "script_after": script_after},
        {"type": "copilot.harness", "duration_ms": 5000, "exit_code": 0, "stderr_tail": "",
         "timed_out": False, "session_id": SID, "cap": 30, "model": "copilot-fixture-a",
         "effort": None, "helpers": 0, "network": False, "tools": ["bash"],
         "roster": ["customize-cloud-agent", copilot_cli.CANARY_SKILL, "github-pr-media"],
         "staged": [copilot_cli.CANARY_SKILL],
         "skill_root": str(tmp_path / "ws" / ".agents" / "skills"), "scrub_hit": False,
         "before": snapshot, "after": snapshot, "after_guard": guard, "first_event_ms": 400,
         "sandbox_flag_notice": True, "cli_version": "1.0.91"}]
    return events


def test_the_canary_command_offers_the_shell_alone_and_keeps_the_other_denials():
    """testing-harness spec: Canary takes the minimum cap and the shell alone."""
    network = claude_runner.SCENARIOS["import_messy"]  # a skill run would approve its URLs
    assert copilot_cli.url_hosts(network)
    argv = copilot_cli.command(network, "p", model="m", effort=None, session_id="s",
                               log_dir=PurePosixPath("/x/logs"), cap=30, canary=True)
    assert "--available-tools=bash" in argv
    assert "--deny-tool=shell(gh:*)" not in argv
    for tool in copilot_cli.CANARY_DENIED:
        assert f"--deny-tool={tool}" in argv
    assert not any(a.startswith("--allow-url") for a in argv)
    assert _contains(argv, ["--max-ai-credits", "30"])
    for switch in copilot_cli.SWITCHES:
        assert switch in argv
    # a skill run keeps every denial and its own tools
    plain = copilot_cli.command({"skill": "proposal-check"}, "p", model="m", effort=None,
                                session_id="s", log_dir=PurePosixPath("/x/logs"), cap=30)
    assert "--deny-tool=shell(gh:*)" in plain
    assert "--available-tools=bash" not in plain


def test_the_canary_commands_are_the_probe_commands_without_the_skill_script(tmp_path):
    commands = dict(canary_cmds(tmp_path))
    assert set(commands) == {*copilot_cli.READ_TARGETS, *copilot_cli.AUTH_TARGETS, "python",
                             *copilot_cli.TMP_TARGETS, *copilot_cli.MEASURED_TARGETS,
                             *copilot_cli.STAGED_TARGETS}
    # since 2026-10-13 the canary's `client_environ` is the probe's own content
    # scan: the session-id row matched the sandbox's init, and the trial, which
    # runs before any process carries the id, read it `denied` trivially; and
    # `staged_ro` works on the placeholder skill the harness staged
    assert commands == dict(copilot_cli.probe_commands(
        token_file=tmp_path / "copilot.token", harness_pid=4343, account=tmp_path / "account",
        uid=1000, script=None, host=copilot_cli.ProbeHost(
            "net:[4026531840]", tmp_path / "devrun-probe-tmp-x", tmp_path / "devrun-probe-write-x",
            tmp_path / "devrun-probe-var-x"), staged=placeholder(tmp_path)))
    assert commands["staged_ro"] == copilot_cli.staged_command(placeholder(tmp_path))
    assert commands["client_environ"] == copilot_cli.token_scan()
    assert SID not in "".join(commands.values())
    assert "/proc/4343/environ" in commands["harness_environ"]


def test_the_canary_prompt_is_one_fixed_command_with_nothing_to_re_escape(tmp_path):
    """testing-harness spec: Canary on Copilot — the prompt carries only the
    one fixed command, which names the script relatively and holds no
    absolute path, quote, backslash, `$` or line break (the first canary's
    path check and re-escaping, 2026-10-07); the script holds every command."""
    prompt = copilot_cli.canary_prompt()
    assert prompt == f"{copilot_cli.CANARY_PROMPT}\n\n```sh\n{copilot_cli.CANARY_RUN}\n```"
    assert re.fullmatch(r"sh [.\w-]+", copilot_cli.CANARY_RUN)
    assert not any(ch in copilot_cli.CANARY_RUN for ch in "/\\'\"$\n")
    assert "/proposal-" not in prompt
    script = copilot_cli.canary_script(canary_cmds(tmp_path))
    for name, command in canary_cmds(tmp_path):
        assert f"w=$( {{ {command} ; }} 2>/dev/null | tail -n 1 ); " \
               f"printf 'canary %s %s\\n' {name} \"$w\"" in script
        assert command not in prompt
    assert script.endswith(f"echo {copilot_cli.CANARY_END}\n")
    assert TOKEN not in script


@POSIX
def test_the_canary_script_prints_one_tagged_line_per_row(tmp_path):
    """The script's shape, run by `sh` over synthetic commands only (never
    the real targets): each row's last output line, errors discarded, as
    `canary <name> <word>`, an empty word dropping its row, and the closing
    line; `script_words` reads the rows back."""
    commands = [("one", "echo noise; echo denied"), ("two", "echo oops >&2; false; echo $?"),
                ("three", "printf 'a\\nb\\n'; echo readable"), ("four", "true")]
    script = tmp_path / "s.sh"
    script.write_text(copilot_cli.canary_script(commands), encoding="utf-8")
    out = subprocess.run(["sh", str(script)], capture_output=True, text=True, check=True)
    assert out.stderr == ""
    assert copilot_cli.script_words(out.stdout) == (
        {"one": "denied", "two": "1", "three": "readable"}, True)


def test_script_words_counts_a_row_only_once_and_only_a_probe_word():
    words = copilot_cli.script_words
    end = copilot_cli.CANARY_END
    assert words(f"canary a denied\ncanary b 128\n{end}\n<shellId: 3 completed>") == (
        {"a": "denied", "b": "128"}, True)
    assert words("canary a denied\n") == ({"a": "denied"}, False)  # no closing line
    assert words(f"canary a denied\ncanary a readable\n{end}") == ({}, True)  # repeated
    assert words(f"canary a /home/x/.ssh/id_ed25519\n{end}") == ({}, True)  # no probe word
    assert words(f"canary a\ncanary end extra\n {end} \n") == ({}, True)


def trial_of(tmp_path: Path, *, words: dict | None = None, skip: tuple = (),
             closed: bool = True, **fields) -> copilot_cli.Trial:
    """The canary script's trial in the probe's session, as `script_trial`
    returns it: the canary's rows, the script's output, the call's report."""
    names = tuple(name for name, _ in canary_cmds(tmp_path))
    output = script_output({**PROBE_OK_WORDS, "tmp_write": "0", **(words or {})}, list(names),
                           skip=skip, closed=closed)
    return copilot_cli.Trial(**{"names": names, "output": output, "sandboxed": True,
                                "seconds": 2.0, **fields})


@pytest.mark.parametrize(("change", "kind", "named"), [
    ({"closed": False}, "precondition", "did not reach its closing line"),
    ({"skip": ("net_ns",)}, "precondition", "no tagged line with a probe word for net_ns"),
    ({"seconds": 25.0}, "precondition", "took 25s"),
    ({"failed": "its script could not be written (FileExistsError)"}, "precondition",
     "FileExistsError"),
    ({"sandboxed": None}, "isolation", "as sandboxed"),
    ({"words": {"token_file": "readable"}}, "isolation", "the token file"),
    ({"tmp_seen": True}, "isolation", "a write into the host's /tmp"),
    ({"words": {"staged_ro": "writable"}}, "isolation", "the staged skill tree"),
    ({"words": {"staged_ro": "unknown"}}, "isolation", "the staged skill tree"),
    ({"skip": ("staged_ro",)}, "precondition", "no tagged line with a probe word for staged_ro"),
], ids=["unclosed", "row-missing", "too-slow", "not-written", "not-sandboxed", "reached",
        "tmp-reached", "staged-writable", "staged-unseen", "staged-missing"])
def test_the_canary_script_trial_refuses_before_any_model_call(change, kind, named, tmp_path):
    """testing-harness spec: Canary script fails in the probe's session —
    the script run once in the probe's sandboxed session (review of task
    8.0a) refuses a script that would leave the canary's rows unanswered
    as a precondition, and rows that do not read as the probe requires for
    isolation; the message names what failed, never any output."""
    assert copilot_cli.trial_problem(trial_of(tmp_path)) is None
    problem = copilot_cli.trial_problem(trial_of(tmp_path, **change))
    assert problem.kind == kind
    assert named in problem.cause
    assert not re.search(r"\b(?:readable|writable)\b", refusal(problem))


def test_a_trial_without_the_staged_row_refuses_where_the_tree_is_guarded(tmp_path):
    """testing-harness spec: Staged skill tree read-only in the sandbox — the
    canary always stages its placeholder, so where the pinned settings guard
    the staged tree a script without `staged_ro` measured nothing and refuses
    as a precondition; elsewhere the row is not asked."""
    names = tuple(n for n, _ in canary_cmds(tmp_path) if n != "staged_ro")
    trial = trial_of(tmp_path, names=names)
    problem = copilot_cli.trial_problem(trial, staged=True)
    assert (problem.kind, "gave no answer for staged_ro" in problem.cause) == (
        "precondition", True)
    assert copilot_cli.trial_problem(trial, staged=False) is None


def test_the_trial_detail_counts_rows_and_never_prints_one(tmp_path):
    names = len(canary_cmds(tmp_path))
    assert copilot_cli.trial_detail(trial_of(tmp_path)) == (
        f"canary script: {names} of {names} rows answered, closing line, 2.0s")
    assert copilot_cli.trial_detail(trial_of(tmp_path, closed=False, sandboxed=False)) == (
        f"canary script: {names} of {names} rows answered, no closing line, 2.0s, "
        "not sandboxed")
    assert copilot_cli.trial_detail(trial_of(tmp_path, failed="x")) == "canary script: x"


@POSIX
def test_the_canary_script_is_written_once_owner_read_only_and_never_through_a_link(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    digest = copilot_cli.write_canary_script(ws, canary_cmds(tmp_path))
    path = ws / copilot_cli.CANARY_SCRIPT
    assert stat.S_IMODE(path.stat().st_mode) == 0o400
    assert copilot_cli.script_digest(ws) == digest
    with pytest.raises(FileExistsError):
        copilot_cli.write_canary_script(ws, canary_cmds(tmp_path))
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / copilot_cli.CANARY_SCRIPT).symlink_to(tmp_path / "elsewhere")
    with pytest.raises(FileExistsError):  # O_EXCL never follows the link
        copilot_cli.write_canary_script(linked, [])
    assert not (tmp_path / "elsewhere").exists()
    assert copilot_cli.script_digest(linked) is None  # a link is never read through
    assert copilot_cli.script_digest(tmp_path) is None  # no script


@POSIX
def test_a_directory_at_the_script_name_reads_as_unreadable_and_closes_its_descriptor(
        tmp_path, monkeypatch):
    """Review of task 8.0a: a directory at the script's name (which the
    workspace check does not flag) used to raise inside `_settle`; it now
    reads as unreadable, and the descriptor is closed on that path."""
    (tmp_path / copilot_cli.CANARY_SCRIPT).mkdir()
    opened: list[int] = []
    closed: list[int] = []
    real_open, real_close = os.open, os.close

    def spy_open(path, flags, *rest):
        opened.append(real_open(path, flags, *rest))
        return opened[-1]

    def spy_close(fd):
        closed.append(fd)
        real_close(fd)

    with monkeypatch.context() as patched:
        patched.setattr(copilot_cli.os, "open", spy_open)
        patched.setattr(copilot_cli.os, "close", spy_close)
        assert copilot_cli.script_digest(tmp_path) is None
    assert opened
    assert opened == closed


def test_a_canary_with_every_row_confirmed_passes_and_records_no_stop(tmp_path):
    """testing-harness spec: Canary passes on confirmed confinement — the
    loaded-skills report is recorded, not required."""
    events = canary_events(tmp_path)
    assessment = copilot_cli.assess(events)
    assert assessment.problem is None
    assert assessment.stops == ()
    report = copilot_cli.canary_report(events)
    assert report["canary_unanswered"] == []
    assert report["canary_call"] == copilot_cli.CALL_RAN
    assert (report["canary_extra_shell_calls"], report["canary_unmatched"]) == (0, [])
    assert report["canary_rows"]["token_file"] == {"output": "denied", "sandboxed": True}
    assert report["canary_rows"]["token_env"]["output"] == "denied"
    assert report["canary_rows"]["var_tmp"]["output"] == "denied"
    assert report["canary_rows"]["net_ns"]["output"] == "private"
    assert report["canary_rows"]["tmp_write"]["output"] == "denied"  # judged on the host
    assert report["canary_rows"]["gh_token"]["output"] == "1"
    assert report["canary_rows"]["staged_ro"]["output"] == "denied"
    # a skill run without the loaded-skills report, and without the staged
    # names to confirm it from the roster, stays untested
    skill_run = [e for e in events if e["type"] != "copilot.canary"]
    copilot_cli.harness_record(skill_run).pop("staged")
    assert "loaded skills could not be confirmed" in copilot_cli.assess(skill_run).problem.message


@pytest.mark.parametrize(("change", "kind", "named"), [
    ({"words": {"token_file": "readable"}}, "isolation", "the token file"),
    ({"words": {"harness_environ": "readable"}}, "isolation", "the harness process's environment"),
    ({"words": {"gh_token": "0"}}, "isolation", "the GitHub CLI's token"),
    ({"words": {"host_tmp": "readable"}}, "isolation", "a file in the host's /tmp"),
    ({"tmp_seen": True}, "isolation", "a write into the host's /tmp"),
    ({"words": {"var_tmp": "readable"}}, "isolation", "a file in the host's /var/tmp"),
    ({"words": {"token_env": "readable"}}, "isolation",
     "the token variables in the shell's own environment"),
    # the first literal reading of the staged tree's read-only bind in prompt
    # mode (2026-10-13): a rename, a file or a link that succeeded
    ({"words": {"staged_ro": "writable"}}, "isolation", "the staged skill tree"),
    ({"skip": ("staged_ro",)}, "precondition", "staged_ro"),
    ({"words": {"python": "127"}}, "precondition", "the skills' interpreter"),
    ({"skip": ("ssh_dir",)}, "precondition", "ssh_dir"),
    ({"repeat": ("ssh_dir",)}, "precondition", "ssh_dir"),
    ({"words": {"gh_config": "/home/x/.config/gh/hosts.yml"}}, "precondition", "gh_config"),
    # ran without `sandboxApplied`: since the review of task 8.0a every run's
    # check (`reported_sandboxed`) names it first, the canary's rows after it
    ({"applied": False}, "isolation", "a shell call was not reported as sandboxed"),
])
def test_a_canary_that_does_not_confirm_the_sandbox_records_a_stop(change, kind, named,
                                                                   tmp_path):
    """testing-harness spec: Canary reaches a target; Canary command not run
    verbatim (a row's line missing, repeated or without a probe word). Every
    outcome but a pass records an isolation stop."""
    assessment = copilot_cli.assess(canary_events(tmp_path, **change))
    problem = assessment.problem
    assert problem.untested
    assert problem.kind == kind
    assert named in problem.message
    assert any(kind == "isolation" and cause.startswith(copilot_cli.NOT_CONFIRMED)
               for kind, cause in assessment.stops)


def test_an_unsandboxed_canary_completion_is_untested_for_isolation(tmp_path):
    assessment = copilot_cli.assess(canary_events(tmp_path, sandboxed=False))
    assert assessment.problem.kind == "isolation"
    assert "not reported as sandboxed" in assessment.problem.message
    kinds = {kind for kind, _cause in assessment.stops}
    assert kinds == {"isolation"}
    # an answered row's sandbox report needs the sandbox applied too (spec: Canary on Copilot)
    rows = copilot_cli._rows_problem(canary_events(tmp_path, applied=False))
    assert (rows.kind, "the canary's commands as sandboxed" in rows.message) == ("isolation", True)


ALL_ROWS = {*copilot_cli.READ_TARGETS, *copilot_cli.AUTH_TARGETS, "python",
            *copilot_cli.TMP_TARGETS, *copilot_cli.MEASURED_TARGETS, *copilot_cli.STAGED_TARGETS}
# the rows an end-to-end canary asks on this platform: `staged_ro` only where
# the pinned settings guard the staged tree (Linux)
HOST_ROWS = ALL_ROWS - (set() if copilot_cli.guards_staged() else set(copilot_cli.STAGED_TARGETS))


def test_a_canary_command_the_client_refused_answers_no_row(tmp_path):
    """testing-harness spec: Canary command refused by the client — the
    first canary's shape (2026-10-07): `sandboxed` true, the `denied` error,
    no result. No row is answered (`tmp_write` included: its command never
    ran), the message names the client's refusal, and the stop names the
    namespace as unanswered for that reason, not as `unknown`."""
    events = canary_events(tmp_path, done=shell_done(refused=True))
    assessment = copilot_cli.assess(events)
    assert (assessment.problem.untested, assessment.problem.kind) == (True, "isolation")
    assert "permission check refused every shell call" in assessment.problem.message
    # the finding that leads points to the kept permission records (review of task 8.0a)
    assert "copilot.permission" in assessment.problem.message
    cause = f"{copilot_cli.NOT_CONFIRMED} (net_ns unanswered: {copilot_cli.CALL_REFUSED})"
    assert ("isolation", cause) in assessment.stops
    report = copilot_cli.canary_report(events)
    assert report["canary_call"] == copilot_cli.CALL_REFUSED
    assert set(report["canary_unanswered"]) == ALL_ROWS
    assert report["canary_rows"]["tmp_write"]["output"] is None
    rows = copilot_cli._rows_problem(events)
    assert copilot_cli.CALL_REFUSED in rows.message
    assert "copilot.permission" in rows.message  # REFUSED_REMEDY


@pytest.mark.parametrize("change", [
    {"done": shell_done(code=None)},  # a result but no exit code
    {"done": shell_done(code=1)},
    {"done": {**shell_done(), "success": False}},
    {"done": {**shell_done(), "error": {"code": "failed", "message": "synthetic"}}},
    {"closed": False},
    {"script_after": "b" * 64},  # the script changed during the run
    {"script_after": None},  # or could not be read after it
], ids=["no-exit-code", "exit-code-1", "not-successful", "an-error", "no-closing-line",
        "script-changed", "script-unread"])
def test_a_canary_call_that_did_not_run_to_its_end_answers_no_row(change, tmp_path):
    """testing-harness spec: Canary command not run verbatim; Canary script
    changed during the run — the rows count only from a completion that
    ran to its end, its closing line present, its script unchanged: every
    row unanswered, `tmp_write` never `denied` without its line."""
    events = canary_events(tmp_path, **change)
    assessment = copilot_cli.assess(events)
    assert assessment.problem.untested
    report = copilot_cli.canary_report(events)
    assert set(report["canary_unanswered"]) == ALL_ROWS
    assert report["canary_call"] != copilot_cli.CALL_RAN
    assert report["canary_rows"]["tmp_write"]["output"] is None
    assert report["canary_call"] in copilot_cli._rows_problem(events).message
    assert any(cause.startswith(f"{copilot_cli.NOT_CONFIRMED} (net_ns unanswered: ")
               for _kind, cause in assessment.stops)


def test_tmp_write_is_judged_on_the_host_only_once_answered(tmp_path):
    """The host judges `tmp_write` only once its line shows its command ran,
    in the canary and in the probe (the first canary's unmeasured pass)."""
    report = copilot_cli.canary_report(canary_events(tmp_path, skip=("tmp_write",)))
    assert report["canary_unanswered"] == ["tmp_write"]
    seen = copilot_cli.canary_report(canary_events(tmp_path, tmp_seen=True))
    assert seen["canary_rows"]["tmp_write"]["output"] == "writable"
    assert copilot_cli.host_write(None, False) is None
    assert copilot_cli.host_write("denied", False) is None  # no exit code
    assert copilot_cli.host_write("0", False) == "denied"
    assert copilot_cli.host_write("1", True) == "writable"


@pytest.mark.parametrize(("change", "unmatched"), [
    ({"extra": 2}, ["echo extra 0", "echo extra 1"]),
    ({"rerun": True}, [copilot_cli.CANARY_RUN]),
    ({"command": "sh ./.devrun-canary.sh"}, ["sh ./.devrun-canary.sh"]),
], ids=["another-command", "the-command-twice", "the-command-altered"])
def test_a_shell_call_beyond_the_fixed_command_fails_the_canary_and_is_named(change, unmatched,
                                                                             tmp_path):
    """testing-harness spec: Canary runs another shell command; Canary
    command not run verbatim — a call beyond the one fixed command (or that
    command twice, which could undo the marker the host judges) is untested
    with the stop, and the summary names each call, cut short; an altered
    command answers no row."""
    events = canary_events(tmp_path, **change)
    assessment = copilot_cli.assess(events)
    assert assessment.problem.untested
    assert any(cause.startswith(copilot_cli.NOT_CONFIRMED) for _k, cause in assessment.stops)
    report = copilot_cli.canary_report(events)
    assert (report["canary_extra_shell_calls"], report["canary_unmatched"]) == (
        len(unmatched), unmatched)
    if "command" in change:
        assert report["canary_call"] == copilot_cli.CALL_MISSING
        assert set(report["canary_unanswered"]) == ALL_ROWS
        assert copilot_cli.CALL_MISSING in assessment.problem.message
    else:
        assert "beyond the canary's fixed command" in assessment.problem.message


def test_an_unmatched_shell_call_is_cut_short_in_the_summary(tmp_path):
    events = canary_events(tmp_path)
    long = "x" * (copilot_cli.UNMATCHED_CHARS + 50)
    events.insert(0, {"type": "tool.execution_start", "data": {
        "toolCallId": "z", "toolName": "bash", "arguments": {"command": long}}})
    events.insert(1, {"type": "tool.execution_complete", "data": {
        "toolCallId": "z", "success": True, "sandboxed": True, "result": {"content": "0"}}})
    for i in range(copilot_cli.SHOWN_UNMATCHED + 2):
        events.insert(0, {"type": "tool.execution_start", "data": {
            "toolCallId": f"y{i}", "toolName": "bash", "arguments": {"command": f"echo {i}"}}})
    report = copilot_cli.canary_report(events)
    assert report["canary_extra_shell_calls"] == copilot_cli.SHOWN_UNMATCHED + 3
    assert len(report["canary_unmatched"]) == copilot_cli.SHOWN_UNMATCHED
    assert all(len(call) <= copilot_cli.UNMATCHED_CHARS for call in report["canary_unmatched"])


@pytest.mark.parametrize(("net_ns", "word", "reading"), [
    ("net:[4026531840]", "shared", "shared"),
    ("net:[4026531840]", "unknown", "unknown"),  # the shell's own readlink failed
    (None, None, "unmeasured"),  # the host could not read its own namespace: no row asked
], ids=["shared", "unknown", "no-row"])
def test_a_canary_without_its_own_network_namespace_fails_with_a_stop_naming_it(
        net_ns, word, reading, tmp_path):
    """testing-harness spec: Canary shares the network namespace."""
    events = canary_events(tmp_path, net_ns=net_ns, words={"net_ns": word} if word else None)
    assessment = copilot_cli.assess(events)
    assert (assessment.problem.untested, assessment.problem.kind) == (True, "isolation")
    assert f"net_ns {reading}" in assessment.problem.message
    assert "sandbox.userPolicy.network" in assessment.problem.message
    assert ("isolation", f"{copilot_cli.NOT_CONFIRMED} (net_ns {reading})") in assessment.stops


def test_an_unanswered_network_namespace_is_never_read_as_unknown(tmp_path):
    """testing-harness spec: Canary shares the network namespace — a row
    without its line reads `unanswered`, with why, in the stop."""
    assessment = copilot_cli.assess(canary_events(tmp_path, skip=("net_ns",)))
    assert "net_ns" in assessment.problem.message
    assert copilot_cli.NO_LINE in assessment.problem.message
    cause = f"{copilot_cli.NOT_CONFIRMED} (net_ns unanswered: {copilot_cli.NO_LINE})"
    assert ("isolation", cause) in assessment.stops
    rows = (ProbeResult("net_ns", None, True),)
    assert copilot_cli.net_reading(rows) == copilot_cli.NET_UNANSWERED
    assert copilot_cli.net_reading(()) == copilot_cli.NET_UNMEASURED
    assert copilot_cli.net_reading((ProbeResult("net_ns", "unknown", True),)) == "unknown"


def test_the_billing_guard_after_the_canary_records_a_billing_stop(tmp_path):
    """testing-harness spec: Canary billing guard after the run."""
    guard = "a Copilot budget is possible: overage is permitted"
    assessment = copilot_cli.assess(canary_events(tmp_path, guard=guard))
    assert assessment.problem.kind == "subscription"
    assert guard in assessment.problem.message
    assert ("billing", f"the billing guard after the canary: {guard}") in assessment.stops
    assert ("isolation", copilot_cli.NOT_CONFIRMED) in assessment.stops


def test_the_canary_rows_come_from_detailed_content_first():
    """The rows are read from `result.detailedContent`, falling back to
    `content`, as 1.0.91 carries both (the first canary)."""
    end = copilot_cli.CANARY_END
    record = {"type": "copilot.canary", "commands": [["a", "x"]], "tmp_seen": False,
              "script_sha256": SCRIPT_SHA, "script_after": SCRIPT_SHA}

    def reading(result: dict) -> CanaryReading:
        start = {"toolCallId": "c0", "toolName": "bash",
                 "arguments": {"command": f" {copilot_cli.CANARY_RUN}\n"}}  # stripped
        done = {"toolCallId": "c0", **shell_done(), "result": result}
        return copilot_cli.canary_rows([{"type": "tool.execution_start", "data": start},
                                        {"type": "tool.execution_complete", "data": done},
                                        record])

    both = reading({"content": "truncated", "detailedContent": f"canary a denied\n{end}"})
    assert (both.rows[0].output, both.call) == ("denied", copilot_cli.CALL_RAN)
    assert reading({"content": f"canary a 1\n{end}", "detailedContent": ""}).rows[0].output == "1"
    assert reading({"content": "", "detailedContent": ""}).call == copilot_cli.CALL_UNCLOSED
    assert copilot_cli.canary_rows([record]).call == copilot_cli.CALL_MISSING


def test_events_seen_tells_stdout_from_the_session_file(tmp_path):
    """K5's parts in every Copilot run's telemetry: where each listed event
    type arrived, the first stdout event against the run's duration, and the
    ignored-flag notice."""
    seen = copilot_cli.events_seen(canary_events(tmp_path, loaded=True))
    assert seen["where"]["tool.execution_complete"] == "both"
    assert seen["where"]["result"] == "stdout"
    assert seen["where"]["session.skills_loaded"] == "stdout"
    assert seen["where"]["session.shutdown"] == "session file"
    assert seen["where"]["session.mcp_servers_loaded"] == "neither"
    assert "session.start" in seen["session_file_only"]
    assert (seen["first_event_ms"], seen["duration_ms"]) == (400, 5000)
    assert seen["sandbox_flag_notice"] is True
    view = copilot_cli.copilot_read(canary_events(tmp_path), Namespace(model="copilot-fixture-a",
                                                                       effort=None))
    assert view.telemetry["events_seen"]["where"]["result"] == "stdout"


def test_the_session_types_are_recorded_by_type_alone():
    lines = ['{"type":"session.start","data":{"prompt":"secret text"}}', "torn",
             '{"type":"skill.invoked","data":{"content":"SKILL"}}', '[1]']
    record = copilot_cli.session_types(lines)
    assert record == {"type": "copilot.session_types", "types": ["session.start", "skill.invoked"]}


@pytest.mark.parametrize("extra", [
    ["--host", "claude"], ["--host", "codex", "--model", "gpt-fixture-a"],
    ["--max-ai-credits", "31"], ["--max-ai-credits", "40"], ["--judge"], ["--no-skill"],
])
def test_canary_usage_errors_make_nothing(extra, monkeypatch, capsys):
    """testing-harness spec: Canary takes the minimum cap and the shell alone."""
    monkeypatch.setattr(claude_runner.tempfile, "mkdtemp",
                        lambda *_a, **_k: pytest.fail("staged before the usage error"))
    argv = ["canary", "--host", "copilot", "--model", "copilot-fixture-a", "--max-ai-credits",
            "30"]
    with pytest.raises(SystemExit) as usage:
        claude_runner.main([*argv, *extra])
    assert usage.value.code == claude_runner.EXIT_USAGE
    assert "canary" in capsys.readouterr().err


def _canary_setup(home: Path, tmp_path: Path, monkeypatch, **extra) -> Path:
    """The fake client for a canary, and the operator's go with its canary
    not yet passed (the `home` fixture's go has passed one)."""
    copilot_cli.clear_stop(home)
    skip_scan(monkeypatch)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    monkeypatch.setattr(copilot_cli, "managed_problem", lambda *_a, **_k: None)
    host_tmp, host_var_tmp = tmp_path / "host-tmp", tmp_path / "host-var-tmp"
    host_tmp.mkdir()
    host_var_tmp.mkdir()
    monkeypatch.setattr(copilot_cli, "PROBE_TMP", host_tmp)
    monkeypatch.setattr(copilot_cli, "PROBE_VAR_TMP", host_var_tmp)
    session = "".join(json.dumps(line) + "\n" for line in [
        {"type": "session.start", "data": {"copilotVersion": "1.0.91", "sessionId": "x"}},
        {"type": "session.shutdown", "data": {
            "shutdownType": "routine", "totalPremiumRequests": 0, "totalNanoAiu": 1_500_000_000,
            "modelMetrics": {"copilot-fixture-a": {"usage": {"inputTokens": 900,
                                                             "outputTokens": 90}}}}}])
    words = {name: [word, True] for name, word in PROBE_OK_WORDS.items()}
    words["tmp_write"] = ["0", True]
    words.update(extra.pop("words", {}))
    # a workspace holding the placeholder skill alone (since 2026-10-13): the
    # client lists it as the one project skill beside its bundled ones
    roster = [*({"name": name, "source": "builtin"} for name in copilot_cli.BUILTIN_SKILLS),
              {"name": copilot_cli.CANARY_SKILL, "source": "project"}]
    return fake_copilot(tmp_path, monkeypatch, skills=roster, session=session, canary=words,
                        canary_model="copilot-fixture-a", **extra)


CANARY_RUN = ["canary", "--host", "copilot", "--model", "copilot-fixture-a",
              "--max-ai-credits", "30"]


@POSIX
def test_a_canary_end_to_end_passes_and_records_every_row(home, tmp_path, monkeypatch, capsys):
    """testing-harness spec: Canary passes on confirmed confinement — end to
    end through the runner and the fake client: an empty workspace in the
    work directory, the script's trial in the probe's session first, the
    shell alone, the one fixed command that runs the script as the prompt,
    the rows from the client's completion of it, no stop."""
    log = _canary_setup(home, tmp_path, monkeypatch)
    summary = tmp_path / "canary.jsonl"
    status = claude_runner.main([*CANARY_RUN, "--summary-log", str(summary)])
    capsys.readouterr()
    [line] = [json.loads(text) for text in summary.read_text(encoding="utf-8").splitlines()]
    assert status == claude_runner.EXIT_PASS, line["why"]
    assert (line["scenario"], line["label"]) == ("canary", claude_runner.CANARY_LABEL)
    assert set(line["canary_rows"]) == HOST_ROWS
    assert all(row["sandboxed"] is True for row in line["canary_rows"].values())
    assert line["canary_rows"]["tmp_write"]["output"] == "denied"
    assert line["canary_call"] == copilot_cli.CALL_RAN  # the fake read the script it ran
    assert line["events_seen"]["sandbox_flag_notice"] is False  # the fake prints no notice
    assert copilot_cli.read_stop(home) is None
    # the go records the passed canary, under the run's own session id
    [run] = [c for c in calls(log) if c["kind"] == "run"]
    session = next(a.split("=", 1)[1] for a in run["argv"] if a.startswith("--session-id="))
    assert copilot_cli.read_go(home)["canary"]["session_id"] == session
    # a second canary under the same go is refused before any Copilot process
    before = len(calls(log))
    assert claude_runner.main(CANARY_RUN) == claude_runner.EXIT_UNTESTED
    assert "the canary already passed" in capsys.readouterr().out
    assert len(calls(log)) == before
    assert "--available-tools=bash" in run["argv"]
    assert "--deny-tool=shell(gh:*)" not in run["argv"]
    assert Path(run["cwd"]).parent == copilot_cli.work_root()
    prompt = run["argv"][run["argv"].index("-p") + 1]
    assert prompt == copilot_cli.canary_prompt()
    assert TOKEN not in prompt


@POSIX
def test_a_canary_end_to_end_that_reaches_a_target_records_a_stop(home, tmp_path, monkeypatch,
                                                                  capsys):
    """testing-harness spec: Canary reaches a target — the stop ends the go,
    so the skill run stays refused."""
    _canary_setup(home, tmp_path, monkeypatch, words={"token_file": ["readable", True]})
    status = claude_runner.main(CANARY_RUN)
    capsys.readouterr()
    assert status == claude_runner.EXIT_UNTESTED
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "isolation"
    assert copilot_cli.NOT_CONFIRMED in stop["cause"]
    assert copilot_cli.read_go(home) is None


@POSIX
def test_a_canary_end_to_end_refused_by_the_client_keeps_the_script_and_names_the_refusal(
        home, tmp_path, monkeypatch, capsys):
    """testing-harness spec: Canary command refused by the client — end to
    end: the kept workspace holds the script, owner read-only, with the
    digest the record names; no row is answered and the stop names why."""
    _canary_setup(home, tmp_path, monkeypatch, canary_refused=True)
    summary = tmp_path / "canary.jsonl"
    status = claude_runner.main([*CANARY_RUN, "--keep", "--summary-log", str(summary)])
    capsys.readouterr()
    assert status == claude_runner.EXIT_UNTESTED
    [line] = [json.loads(text) for text in summary.read_text(encoding="utf-8").splitlines()]
    assert line["canary_call"] == copilot_cli.CALL_REFUSED
    assert set(line["canary_unanswered"]) == HOST_ROWS
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "isolation"
    ws = Path(line["workspace"])
    try:
        script = ws / copilot_cli.CANARY_SCRIPT
        assert stat.S_IMODE(script.stat().st_mode) == 0o400
        events = claude_runner.load_events(ws)
        [record] = [e for e in events if e["type"] == "copilot.canary"]
        assert record["script_sha256"] == record["script_after"] == copilot_cli.script_digest(ws)
    finally:
        shutil.rmtree(ws, ignore_errors=True)


@POSIX
def test_a_canary_whose_script_became_a_directory_reads_as_changed_not_a_crash(
        home, tmp_path, monkeypatch, capsys):
    """testing-harness spec: Canary script changed during the run — the
    shell leaves a directory at the script's name, which the workspace check
    does not flag (review of task 8.0a): the run ends on the script-changed
    verdict with the isolation stop, not through the exception path's
    billing stop."""
    _canary_setup(home, tmp_path, monkeypatch, mkdirs=[copilot_cli.CANARY_SCRIPT])
    summary = tmp_path / "canary.jsonl"
    status = claude_runner.main([*CANARY_RUN, "--summary-log", str(summary)])
    capsys.readouterr()
    assert status == claude_runner.EXIT_UNTESTED
    [line] = [json.loads(text) for text in summary.read_text(encoding="utf-8").splitlines()]
    assert line["canary_call"] == copilot_cli.CALL_CHANGED
    assert set(line["canary_unanswered"]) == HOST_ROWS
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "isolation"
    assert copilot_cli.NOT_CONFIRMED in stop["cause"]
    assert copilot_cli.AFTER_INCOMPLETE not in stop["cause"]


@POSIX
def test_the_canary_stages_its_placeholder_skill_before_anything_reads_the_workspace(
        home, tmp_path, monkeypatch, capsys):
    """testing-harness spec: Canary stages a placeholder skill (2026-10-13) —
    the kept workspace holds the placeholder alone, unchanged; the client's
    listing ran in it and named it, the runner recorded it as staged, and,
    where the pinned settings guard the staged tree, the canary's script
    tried `staged_ro` on its `SKILL.md`."""
    log = _canary_setup(home, tmp_path, monkeypatch)
    summary = tmp_path / "canary.jsonl"
    status = claude_runner.main([*CANARY_RUN, "--keep", "--summary-log", str(summary)])
    capsys.readouterr()
    [line] = [json.loads(text) for text in summary.read_text(encoding="utf-8").splitlines()]
    assert status == claude_runner.EXIT_PASS, line["why"]
    ws = Path(line["workspace"])
    try:
        skill = ws / ".agents" / "skills" / copilot_cli.CANARY_SKILL / "SKILL.md"
        assert skill.read_text(encoding="utf-8") == copilot_cli.CANARY_SKILL_TEXT
        assert [p.name for p in (ws / ".agents" / "skills").iterdir()] == [
            copilot_cli.CANARY_SKILL]
        assert stat.S_IMODE(skill.parent.stat().st_mode) == 0o700
        [listing] = [c for c in calls(log) if c["kind"] == "skills"]
        assert listing["cwd"] == str(ws)
        events = claude_runner.load_events(ws)
        harness = copilot_cli.harness_record(events)
        assert harness["staged"] == [copilot_cli.CANARY_SKILL]
        assert copilot_cli.CANARY_SKILL in harness["roster"]
        assert harness["skill_findings"] == []  # the staged tree as staged
        [record] = [e for e in events if e["type"] == "copilot.canary"]
        commands = dict(record["commands"])
        if copilot_cli.guards_staged():
            assert commands["staged_ro"] == copilot_cli.staged_command(skill)
        else:
            assert "staged_ro" not in commands
    finally:
        shutil.rmtree(ws, ignore_errors=True)


def test_a_workspace_that_refuses_the_placeholder_refuses_the_canary(tmp_path):
    """The placeholder is created exclusively: a workspace that already holds
    one, or cannot take it, refuses the canary as a precondition."""
    ws = tmp_path / "ws"
    ws.mkdir()
    staged = copilot_cli.stage_canary_skill(ws)
    assert staged == ws / ".agents" / "skills" / copilot_cli.CANARY_SKILL / "SKILL.md"
    assert copilot_cli.staged_names(ws) == [copilot_cli.CANARY_SKILL]
    with pytest.raises(copilot_cli.CopilotRefused) as again:
        copilot_cli.stage_canary_skill(ws)
    assert again.value.kind == "precondition"
    assert "placeholder skill" in again.value.message


@POSIX
def test_the_canary_preflight_stages_only_its_placeholder(home, tmp_path, monkeypatch, capsys):
    """testing-harness spec: Copilot preflight only; Canary script fails in
    the probe's session — the canary's `--preflight-only` runs its script
    once in the probe's sandboxed session (review of task 8.0a), owner
    read-only as the canary writes it, and removes it again; its workspace
    holds the placeholder skill, as its run's does (2026-10-13)."""
    log = _canary_setup(home, tmp_path, monkeypatch)
    status = claude_runner.main([*CANARY_RUN, "--preflight-only"])
    out = capsys.readouterr().out
    assert status == claude_runner.EXIT_PASS, out
    assert (f"rosters: ok — customize-cloud-agent, {copilot_cli.CANARY_SKILL}, "
            "github-pr-media") in out
    assert "go: ok — canary (go given" in out
    assert "var_tmp denied" in out
    assert "token_env denied" in out
    assert "skill_script" not in out
    assert ("staged_ro denied" in out) is copilot_cli.guards_staged()
    rows = len(HOST_ROWS)
    assert f"canary script: {rows} of {rows} rows answered, closing line" in out
    assert Path(f"{log}.trial").read_text(encoding="utf-8").split() == ["0o400"]
    trial = [c["params"] for c in rpc_calls(log)
             if c["method"] == SHELL and c["params"]["command"] == copilot_cli.CANARY_RUN]
    assert len(trial) == 1
    assert not any(c["kind"] == "run" for c in calls(log))
    assert sessions(home) == []


@POSIX
def test_a_canary_whose_script_fails_its_trial_is_refused_before_its_child(
        home, tmp_path, monkeypatch, capsys):
    """testing-harness spec: Canary script fails in the probe's session — no
    prompt-mode child, no stop, the go's canary still unpassed."""
    log = _canary_setup(home, tmp_path, monkeypatch, trial="unclosed")
    status = claude_runner.main(CANARY_RUN)
    out = capsys.readouterr().out
    assert status == claude_runner.EXIT_UNTESTED
    assert "did not reach its closing line" in out
    assert not any(c["kind"] == "run" for c in calls(log))
    assert copilot_cli.read_stop(home) is None
    assert copilot_cli.read_go(home)["canary"] is None


# ---------- the operator's go (Decision 9, the go; task 7.16) -----------------------------------


def test_go_problem_covers_one_canary_then_one_skill_run():
    """testing-harness spec: Skill run before a passed canary; One go covers
    one canary and one skill run — pure."""
    pending = {"at": "2026-10-07T00:00:00Z", "canary": None}
    passed = {**pending, "canary": {"passed_at": "2026-10-07T00:05:00Z", "session_id": SID}}
    assert copilot_cli.go_problem(pending, canary=True) is None
    assert copilot_cli.go_problem(passed, canary=False) is None
    for go, canary, named in ((None, True, "no go is recorded"), (None, False, "no go is recorded"),
                              (pending, False, "no canary has passed"),
                              (passed, True, "the canary already passed")):
        problem = copilot_cli.go_problem(go, canary)
        assert problem.kind == "precondition"
        assert named in problem.cause
    assert copilot_cli.CANARY_COMMAND in copilot_cli.go_problem(pending, False).remedy
    assert host_login.CLEAR_STOP_COMMAND in copilot_cli.go_problem(None, False).remedy
    assert copilot_cli.go_text(None) == "none"
    assert copilot_cli.go_text(pending).startswith("canary")
    assert copilot_cli.go_text(passed).startswith("skill run")


def test_the_go_is_recorded_by_a_clear_and_ended_by_any_stop(copilot_home):
    """The clear records the go, with no stop recorded too; a canary's pass
    is recorded in it; every stop ends it; a damaged go reads as none; a new
    status snapshot keeps it."""
    home = copilot_home
    copilot_cli.record_stop(home, "approval", host_login.APPROVAL_CAUSE)
    assert copilot_cli.read_go(home) is None
    assert copilot_cli.clear_stop(home)["kind"] == "approval"
    assert copilot_cli.read_go(home)["canary"] is None
    copilot_cli.record_canary_pass(home, SID)
    assert copilot_cli.read_go(home)["canary"]["session_id"] == SID
    copilot_cli.write_snapshot(home, status_of("status-ok"))
    assert copilot_cli.read_go(home)["canary"]["session_id"] == SID
    for kind in ("billing", "isolation", "approval"):
        copilot_cli.clear_stop(home)
        assert copilot_cli.read_stop(home) is None
        assert copilot_cli.read_go(home) is not None
        copilot_cli.record_stop(home, kind, f"synthetic {kind}")
        assert copilot_cli.read_go(home) is None
    copilot_cli.clear_stop(home)
    copilot_cli.record_canary_pass(home, SID)
    data = json.loads((home / copilot_cli.QUOTA_FILE).read_text(encoding="utf-8"))
    for damaged in ("yes", {"canary": None}, {"at": "", "canary": None}):
        (home / copilot_cli.QUOTA_FILE).write_text(json.dumps({**data, "go": damaged}),
                                                   encoding="utf-8")
        assert copilot_cli.read_go(home) is None
    (home / copilot_cli.QUOTA_FILE).write_text(json.dumps(
        {**data, "go": {"at": "t", "canary": "passed"}}), encoding="utf-8")
    assert copilot_cli.read_go(home) == {"at": "t", "canary": None}  # a bad pass is no pass
    copilot_cli.record_stop(home, "isolation", "x")
    copilot_cli.record_canary_pass(home, SID)  # no go: nothing recorded
    assert copilot_cli.read_go(home) is None


@POSIX
@pytest.mark.parametrize(("go", "named"), [
    ("none", "no go is recorded"), ("pending", "no canary has passed"),
])
def test_a_skill_run_no_go_covers_is_refused_before_any_child(go, named, home, tmp_path,
                                                              monkeypatch):
    """testing-harness spec: Skill run before a passed canary — before the
    first child (the preflight) and again under the lock, nothing recorded."""
    data = json.loads((home / copilot_cli.QUOTA_FILE).read_text(encoding="utf-8"))
    data.pop("go")
    if go == "pending":
        data["go"] = {"at": "2026-10-07T00:00:00Z", "canary": None}
    (home / copilot_cli.QUOTA_FILE).write_text(json.dumps(data), encoding="utf-8")
    spy = Spy()
    monkeypatch.setattr(copilot_cli.subprocess, "Popen", spy)
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.isolated_home(None, Namespace(scenario="check_report"))
    assert (refused.value.kind, named in refused.value.message) == ("precondition", True)
    skip_scan(monkeypatch)
    with pytest.raises(copilot_cli.CopilotRefused) as locked:
        copilot_cli.run_copilot(staged_ws(tmp_path), "request", model="copilot-fixture-a",
                                effort=None, cap=30, timeout=30, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    assert named in locked.value.message
    assert spy.calls == []
    assert copilot_cli.read_stop(home) is None
    assert json.loads((home / copilot_cli.QUOTA_FILE).read_text(encoding="utf-8")) == data


@POSIX
def test_a_canary_refused_before_its_child_leaves_the_skill_run_refused(home, tmp_path,
                                                                       monkeypatch, capsys):
    """testing-harness spec: Canary refused before its child — a gate row
    (here the billing guard) refuses it with no stop, the go's canary stays
    unpassed, and the skill run asked next is refused too."""
    log = _canary_setup(home, tmp_path, monkeypatch, status="status-budget")
    assert claude_runner.main(CANARY_RUN) == claude_runner.EXIT_UNTESTED
    assert "overage is permitted" in capsys.readouterr().out
    assert not [c for c in calls(log) if c["kind"] == "run"]
    assert copilot_cli.read_stop(home) is None
    assert copilot_cli.read_go(home)["canary"] is None
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.isolated_home(None, Namespace(scenario="check_report"))
    assert "no canary has passed" in refused.value.message


@POSIX
def test_one_go_covers_one_skill_run_whose_start_records_the_approval_stop(home, tmp_path,
                                                                           monkeypatch):
    """testing-harness spec: One go covers one canary and one skill run — the
    approval stop returns as the skill run's child starts, whatever the run's
    outcome, and holds every later model call back."""
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch, run="no-shutdown")  # a runner failure
    ws = staged_ws(tmp_path)
    request = "Please check my proposal broken-format.md."
    events = copilot_cli.run_copilot(ws, request, model="copilot-fixture-a", effort=None, cap=30,
                                     timeout=30, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    assert copilot_cli.run_problem(events) is not None
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "billing"  # the missing shutdown's stop outranks the approval stop
    assert copilot_cli.GO_USED in stop["cause"]
    assert copilot_cli.read_go(home) is None
    before = len(calls(log))
    for scenario in ("check_report", "canary"):
        with pytest.raises(copilot_cli.CopilotRefused):
            copilot_cli.isolated_home(None, Namespace(scenario=scenario))
    assert len(calls(log)) == before


# ---------- 8.0c: the pid-1 and log-directory routes (the second canary, 2026-10-13) --------

LONG_TAIL = "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"  # 36 synthetic token characters


def nul(*entries: str) -> str:
    """Entries as /proc writes an environment or a command line."""
    return "".join(f"{entry}\0" for entry in entries)


def proc_tree(root: Path, processes: dict[int, dict[str, str]]) -> Path:
    """A synthetic /proc: per pid, files by their path under `/proc/<pid>/`."""
    for pid, files in processes.items():
        for name, text in files.items():
            path = root / str(pid) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
    return root


def scan(proc: Path, path: str | None = None) -> str:
    """The content scan run by the host's `sh` over a synthetic tree only."""
    return subprocess.run(["sh", "-c", copilot_cli.token_scan(str(proc))], capture_output=True,
                          text=True, env={"PATH": path or os.environ.get("PATH", "")},
                          check=False).stdout.strip()


def test_the_content_scan_splits_every_literal_so_it_never_counts_itself():
    """Verifier finding 2 (2026-10-13): the scan's pattern lies in its own
    command line, the shell's and grep's, which the scan reads as well; each
    literal is split by a bracket expression, so the text never matches the
    pattern, while the pattern matches each token variable and each GitHub
    token prefix followed by a token's tail."""
    pattern, row = copilot_cli.token_pattern(), copilot_cli.token_scan()
    literals = (*copilot_cli.TOKEN_ENV_VARS, *copilot_cli.GITHUB_TOKEN_PREFIXES)
    assert {"COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"} <= set(literals)
    assert {"github_pat_", "ghp_", "gho_", "ghu_"} <= set(literals)
    for literal in literals:
        assert literal not in pattern, literal
        assert literal not in row, literal
    assert not re.search(pattern, pattern)
    assert not re.search(pattern, row)
    for name in copilot_cli.TOKEN_ENV_VARS:
        assert re.search(pattern, f"{name}=x")
        assert re.search(pattern, f"{name}=")  # set, even empty
    for prefix in copilot_cli.GITHUB_TOKEN_PREFIXES:
        assert re.search(pattern, f"value {prefix}{LONG_TAIL}")
        assert not re.search(pattern, f"value {prefix}short")  # a directory name, not a token
    assert copilot_cli.unmatchable("GH_TOKEN") == "GH_TOKE[N]"
    with pytest.raises(ValueError, match="not a word"):
        copilot_cli.unmatchable("a-b")
    # one word, never a match: no output of a scanned file reaches the result
    assert row.endswith('echo denied; elif [ -n "$c" ]; then echo readable; '
                        "else echo unknown; fi")


@POSIX
@pytest.mark.parametrize(("files", "word"), [
    ({}, "denied"),
    ({"environ": nul("GH_TOKEN=x")}, "readable"),
    ({"task/7/environ": nul("COPILOT_GITHUB_TOKEN=x")}, "readable"),
    ({"cmdline": nul("env", "GITHUB_TOKEN=", "sh")}, "readable"),
    ({"cmdline": nul("sh", "-c", f"echo github_pat_{LONG_TAIL}")}, "readable"),
    ({"environ": nul(f"X=ghp_{LONG_TAIL}")}, "readable"),
    ({"environ": nul(f"X=gho_{LONG_TAIL}")}, "readable"),
    ({"environ": nul(f"X=ghu_{LONG_TAIL}")}, "readable"),
    ({"environ": nul("X=ghp_short", "MY_GH_TOKEN=x", "PATH=/usr/bin")}, "denied"),
], ids=["none", "environ", "thread", "cmdline-name", "pat", "ghp", "gho", "ghu", "near-misses"])
def test_the_content_scan_finds_a_token_in_any_environment_or_command_line(files, word,
                                                                          tmp_path):
    """Verifier finding 2: every environment, every thread's and every command
    line of every process the shell can see, by content rather than by pid,
    since the sandbox has a pid namespace of its own (the second canary read
    the client's environment through the sandbox's init, pid 1). Run by `sh`
    over a synthetic tree only, never the host's /proc."""
    proc = proc_tree(tmp_path / "proc", {1: {"environ": nul("PATH=/usr/bin")},
                                         7: {"cmdline": nul("sleep", "1"), **files}})
    assert scan(proc) == word


@POSIX
def test_the_content_scan_never_counts_its_own_command_line(tmp_path):
    """Verifier finding 2: the processes that run the scan carry its text — the
    tool's `bash -c`, the canary script's `sh`, and grep with the pattern as
    its argument — and the scan reads their command lines too."""
    row = copilot_cli.token_scan(str(tmp_path / "proc"))
    proc = proc_tree(tmp_path / "proc", {
        2: {"cmdline": nul("/bin/bash", "--norc", "--noprofile", "-c", row)},
        3: {"cmdline": nul("sh", "-c", row), "environ": nul("PATH=/usr/bin")},
        4: {"cmdline": nul("grep", "-cE", "--", copilot_cli.token_pattern())},
        5: {"cmdline": nul("sh", "-c", copilot_cli.canary_script([("client_environ", row)]))}})
    assert scan(proc) == "denied"


@ROOTLESS
def test_the_content_scan_passes_over_what_the_shell_cannot_read(tmp_path):
    """Another user's process, or a non-dumpable one, is unreadable to the
    shell, as on the host's /proc: passed over, not a failure of the scan."""
    proc = proc_tree(tmp_path / "proc", {9: {"environ": nul("GH_TOKEN=x")}})
    (proc / "9" / "environ").chmod(0)
    try:
        assert scan(proc) == "denied"
    finally:
        (proc / "9" / "environ").chmod(0o600)


@POSIX
def test_a_content_scan_that_cannot_search_reads_unknown_and_refuses(tmp_path):
    """A scan whose search fails prints `unknown`, never `denied`, and the
    probe refuses it like a reached target: fail closed."""
    proc = proc_tree(tmp_path / "proc", {1: {"environ": nul("A=1")}})
    tools = tmp_path / "bin"
    tools.mkdir()
    (tools / "grep").write_text("#!/bin/sh\nexit 2\n", encoding="utf-8")
    (tools / "grep").chmod(0o755)
    assert scan(proc, f"{tools}:{os.environ.get('PATH', '')}") == "unknown"
    supported, results = probe("probe-ok")
    rows = [ProbeResult(r.name, "unknown" if r.name == "client_environ" else r.output,
                        r.sandboxed) for r in results]
    problem = copilot_cli.probe_problem(rows, supported)
    assert problem.kind == "isolation"
    assert copilot_cli.READ_TARGETS["client_environ"] in problem.cause


@POSIX
@pytest.mark.usefixtures("home")
def test_every_runs_probe_and_the_canarys_script_carry_the_content_scan(tmp_path, monkeypatch):
    """Verifier finding 4: the hardened row runs in every Copilot run's probe,
    a skill run's included, and in the canary's script and so its trial; no
    row reads a host pid of the client."""
    log = fake_copilot(tmp_path, monkeypatch)
    copilot_cli.confinement_probe(probe_run(tmp_path))
    sent = [c["params"]["command"] for c in rpc_calls(log) if c["method"] == SHELL]
    assert copilot_cli.token_scan() in sent
    assert copilot_cli.token_scan() in copilot_cli.canary_script(canary_cmds(tmp_path))
    assert not hasattr(copilot_cli, "_client_row")


@pytest.mark.parametrize(("scope", "platform", "refused"), [
    (None, "linux", "is not available (no Yama)"), (0, "linux", "is 0"), (-1, "linux", "is -1"),
    (1, "linux", None), (2, "linux", None), (3, "linux", None),
    (None, "darwin", None), (0, "darwin", None), (None, "win32", None)])
def test_the_ptrace_scope_is_mandatory_on_linux_only(scope, platform, refused):
    """Verifier finding 1 (2026-10-13): with Yama missing or its scope below 1,
    a same-user shell in the sandbox could attach to the sandbox's init and
    read the client's environment from its memory, past the /proc mask. Other
    platforms keep their behaviour. The remedy changes nothing on the host."""
    problem = copilot_cli.ptrace_problem(scope, platform)
    if refused is None:
        assert problem is None
        return
    assert problem.kind == "precondition"
    assert refused in problem.cause
    assert copilot_cli.YAMA_PTRACE in problem.cause
    assert "never changes it" in problem.remedy


@pytest.mark.parametrize(("text", "scope"), [
    ("0\n", 0), ("1\n", 1), ("2", 2), ("3\n", 3), ("", None), ("one\n", None), (None, None)])
def test_the_ptrace_scope_is_read_from_the_file_it_is_given(text, scope, tmp_path):
    """The reader is read-only and takes its path from the caller; L0 hands it
    files of its own, never the kernel's (the conftest replaces the seam)."""
    path = tmp_path / "ptrace_scope"
    if text is not None:
        path.write_text(text, encoding="ascii")
    assert REAL_PTRACE_SCOPE(path) == scope
    assert REAL_PTRACE_SCOPE(tmp_path) is None  # a directory
    assert copilot_cli.YAMA_PTRACE == "/proc/sys/kernel/yama/ptrace_scope"
    assert copilot_cli.ptrace_scope() == copilot_cli.MIN_PTRACE_SCOPE  # the conftest's stand-in


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="the ptrace scope is Linux's")
@pytest.mark.parametrize("scope", [None, 0])
@pytest.mark.usefixtures("home")
def test_a_low_ptrace_scope_refuses_a_run_before_its_reads(scope, tmp_path, monkeypatch):
    """Verifier finding 1: a preflight row before the status read, the probe
    and any prompt-mode child; `--preflight-only` prints it and goes on, and
    the status command (and so the login) reports the host not ready."""
    log = fake_copilot(tmp_path, monkeypatch)
    monkeypatch.setattr(copilot_cli, "ptrace_scope", lambda _path=None: scope)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    monkeypatch.setattr(copilot_cli, "managed_problem", lambda *_a, **_k: None)
    run = copilot_cli.new_run(ws=staged_ws(tmp_path), model="copilot-fixture-a")
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli._require(copilot_cli.preflight_checks(run))
    assert "Yama ptrace scope" in refused.value.message
    assert refused.value.kind == "precondition"
    assert [c["kind"] for c in calls(log)] == ["version"]
    row = next(c for c in copilot_cli.preflight_checks(copilot_cli.new_run())
               if c.name == "ptrace_scope")
    assert row.detail == ("missing" if scope is None else "0")
    assert "ptrace_scope" in copilot_cli.REPORTED
    assert "Yama" in copilot_cli.machine_problem(os.environ).cause
    assert copilot_cli._ptrace_line() == ("missing" if scope is None else "0")
    assert copilot_cli._ptrace_line("darwin") == "not applicable"


def test_a_process_log_with_the_token_or_a_github_token_is_a_finding():
    """Verifier finding 3: the logs are searched for the token's value and for
    any GitHub token, a prefix with a token's tail. Pure."""
    assert copilot_cli.logged(f"auth {TOKEN} ok".encode(), TOKEN)
    for prefix in copilot_cli.GITHUB_TOKEN_PREFIXES:
        assert copilot_cli.logged(f"x {prefix}{LONG_TAIL} y".encode(), None)
        assert not copilot_cli.logged(f"x {prefix}short y".encode(), None)
    assert not copilot_cli.logged(b"", TOKEN)
    assert not copilot_cli.logged(b"2026-10-13 warning: nothing to see", None)


@POSIX
def test_drain_logs_names_each_finding_and_empties_the_directory(home, tmp_path):
    """Verifier finding 3: after the probe and after the run every entry is
    scanned, a link, a FIFO or a directory counted as a finding unread, and
    the directory emptied without following anything; it stays, owner-only."""
    assert copilot_cli.log_dir_problem(home) is None
    folder = host_login.log_dir(home)
    assert stat.S_IMODE(folder.stat().st_mode) == 0o700
    (folder / "process-1-1.log").write_text("warning: fine\n", encoding="utf-8")
    (folder / "process-2-2.log").write_text(f"oops {TOKEN}\n", encoding="utf-8")
    (folder / "process-3-3.log").write_text(f"x ghu_{LONG_TAIL}\n", encoding="utf-8")
    victim = tmp_path / "victim.txt"
    victim.write_text("keep", encoding="utf-8")
    (folder / "link.log").symlink_to(victim)
    (folder / "sub").mkdir()
    (folder / "sub" / "x.log").write_text("x", encoding="utf-8")
    os.mkfifo(folder / "fifo")
    found = copilot_cli.drain_logs(home, TOKEN)
    assert found == ["fifo", "link.log", "process-2-2.log", "process-3-3.log", "sub"]
    assert list(folder.iterdir()) == []
    assert victim.read_text(encoding="utf-8") == "keep"
    assert copilot_cli.drain_logs(home, TOKEN) == []


@POSIX
def test_a_log_directory_that_is_no_directory_of_its_own_is_never_entered(home, tmp_path):
    """A link at the log directory's name is refused before any child and
    never entered by the scan, so nothing it leads to is read or deleted; so
    is a file there, or a directory open to others."""
    folder = host_login.log_dir(home)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "keep.log").write_text("keep", encoding="utf-8")
    folder.symlink_to(elsewhere)
    assert copilot_cli.log_dir_problem(home).kind == "precondition"
    assert copilot_cli.drain_logs(home, TOKEN) == [host_login.LOG_DIR]
    assert (elsewhere / "keep.log").read_text(encoding="utf-8") == "keep"
    folder.unlink()
    folder.write_text("x", encoding="utf-8")
    assert copilot_cli.log_dir_problem(home) is not None
    folder.unlink()
    folder.mkdir()
    folder.chmod(0o750)
    assert copilot_cli.log_dir_problem(home) is not None
    folder.rmdir()
    assert copilot_cli.drain_logs(home, TOKEN) == []  # none yet: nothing to scan
    assert copilot_cli.log_dir_problem(home) is None
    assert folder.is_dir()


@POSIX
def test_the_run_logs_where_the_deny_list_masks_and_a_token_there_stops_it(home, tmp_path,
                                                                           monkeypatch):
    """Verifier finding 3: the 1.0.91 client binds its log directory into the
    sandbox after the deny list's masks, so the run logs into the directory
    the deny list names exactly (measured: masked), never under scratch; the
    log is scanned after the run beside the workspace scrub, and a GitHub
    token there makes the run untested for isolation with an isolation stop,
    the log deleted and no part of it saved."""
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch, log_text={"run": f"debug ghp_{LONG_TAIL}\n"})
    events = copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                     effort=None, cap=30, timeout=30, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"])
    argv = next(c["argv"] for c in calls(log) if c["kind"] == "run")
    folder = host_login.log_dir(home)
    assert argv[argv.index("--log-dir") + 1] == str(folder)
    pinned = host_login.pinned_settings(home, host_login.account_home())
    assert str(folder) in pinned["sandbox"]["userPolicy"]["filesystem"]["deniedPaths"]
    assert copilot_cli.harness_record(events)["log_findings"] == 1
    problem = copilot_cli.run_problem(events)
    assert (problem.untested, problem.kind) == (True, "isolation")
    assert copilot_cli.LOGGED_CAUSE in problem.message
    assert LONG_TAIL not in json.dumps(events)
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "isolation"
    assert copilot_cli.LOGGED_CAUSE in stop["cause"]
    assert list(folder.iterdir()) == []


@POSIX
def test_a_token_in_the_probes_process_log_refuses_the_run_before_its_child(home, tmp_path,
                                                                           monkeypatch):
    """The probe's server, whose session the client sandboxes, logs into the
    same directory; a finding there refuses the run for isolation before its
    prompt-mode child. The status reads, which sandbox no session, log under
    their own scratch, deleted with the call."""
    skip_scan(monkeypatch)
    log = fake_copilot(tmp_path, monkeypatch, log_text={"headless": f"x {TOKEN}\n"})
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                effort=None, cap=30, timeout=30, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    assert refused.value.kind == "isolation"
    assert f"{copilot_cli.LOGGED_CAUSE} after the confinement probe" in refused.value.message
    assert TOKEN not in refused.value.message
    assert "run" not in [c["kind"] for c in calls(log)]
    folder = host_login.log_dir(home)
    assert list(folder.iterdir()) == []
    dirs = [json.loads(line)["log_dir"] for line in
            Path(f"{log}.logdirs").read_text(encoding="utf-8").splitlines()]
    assert dirs.count(str(folder)) == 1  # the probe's; the status read's lay under scratch
    assert all(not Path(d).exists() for d in dirs if d != str(folder))
    assert copilot_cli.read_stop(home) is None  # refused before any model call: no stop


@POSIX
def test_an_after_run_step_that_raises_still_drains_the_logs_and_stops(home, tmp_path,
                                                                       monkeypatch):
    """The exception path fails closed for the logs too: scanned, emptied, and
    a finding recorded as an isolation stop beside the billing stop."""
    skip_scan(monkeypatch)
    fake_copilot(tmp_path, monkeypatch, log_text={"run": f"x {TOKEN}\n"})

    def broken(*_args, **_kwargs):
        raise RuntimeError("synthetic failure of an after-run step")

    monkeypatch.setattr(copilot_cli, "capture_session", broken)
    with pytest.raises(RuntimeError, match="synthetic failure"):
        copilot_cli.run_copilot(staged_ws(tmp_path), "check", model="copilot-fixture-a",
                                effort=None, cap=30, timeout=30, home=home,
                                scenario=claude_runner.SCENARIOS["check_report"])
    stop = copilot_cli.read_stop(home)
    assert stop["kind"] == "billing"
    assert copilot_cli.LOGGED_CAUSE in stop["cause"]
    assert list(host_login.log_dir(home).iterdir()) == []
