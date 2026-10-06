"""L0: the harness-owned login home, and isolated configurations that keep the
login they link current (testing-harness spec: Harness-owned host logins;
Isolated measurement environment).

Recorded 2026-10-04 (host 2.1.284): a refresh inside an isolated
CLAUDE_CONFIG_DIR replaces the credentials symlink with a file of its own by
atomic rename, rotating the refresh token. The temp directory took the only
valid refresh token with it, and every later run failed with "OAuth session
expired and could not be refreshed". These tests replay that replacement on
synthetic credentials — the values are placeholders, never a real login. The
harness home lives under a synthetic state root in `tmp_path`, and the host's
status is a monkeypatched `host_login.read_status`: no test starts a client.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from contextlib import ExitStack
from pathlib import Path

import claude_runner
import copilot_cli
import host_login
import pytest
import routing
from account_surfaces import PINNED_SETTINGS, PROFILE_DIR, isolation_problem
from helpers import COPILOT_STREAMS
from host_login import (
    CLAIM_NAME,
    CLAUDE,
    CREDENTIALS,
    L3_CAVEAT,
    LOGIN_COMMAND,
    LONG_LIVED_TOKEN,
    MARKER,
    NOT_AFFECTED,
    RESET_COMMAND,
    STATE_VAR,
    LoginProblem,
    LoginSource,
    acquire_claim,
    check_home,
    check_location,
    check_presence,
    check_status,
    keep_login,
    login_dir,
    login_note,
    login_remedy,
    login_source,
    refusal,
    release_claim,
    settle,
    state_root,
    wipe,
    writeback_target,
)

HOUR_MS = 3_600_000
PRIVATE = {"email": "erika.musterfrau@example.org", "orgName": "Example Org", "orgId": "org-0000"}


def _symlinks_available(tmp: Path) -> bool:
    try:
        (tmp / "probe-link").symlink_to(tmp)
    except OSError:  # Windows without the symlink privilege
        return False
    return True


@pytest.fixture(autouse=True)
def _symlinks(tmp_path):
    if not _symlinks_available(tmp_path):
        pytest.skip("symlinks cannot be created here")


def now_ms() -> int:
    return int(time.time() * 1000)


def store(path: Path, expires_at: int, refresh: str = "refresh-0") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"claudeAiOauth": {"accessToken": f"access-for-{refresh}",
                                 "refreshToken": refresh, "expiresAt": expires_at}}
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)
    return path


def refresh_token(path: Path) -> str:
    return json.loads(path.read_text(encoding="utf-8"))["claudeAiOauth"]["refreshToken"]


def host_refresh(link: Path, expires_at: int, refresh: str = "refresh-1") -> None:
    """What the host does on refresh: write beside the link, rename over it."""
    tmp = store(link.with_name(link.name + ".host-tmp"), expires_at, refresh)
    tmp.replace(link)


def wait_for(condition, timeout: float = 2.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.01)
    return condition()


@pytest.fixture
def linked(tmp_path):
    """A stored login valid for hours and a configuration linking to it."""
    source = store(tmp_path / "stored" / CREDENTIALS, now_ms() + 8 * HOUR_MS)
    link = tmp_path / "config" / CREDENTIALS
    link.parent.mkdir()
    link.symlink_to(source)
    return source, link


@pytest.fixture
def fast(monkeypatch):
    monkeypatch.setattr(host_login, "POLL_S", 0.02)
    monkeypatch.setattr(host_login, "CLAIM_POLL_S", 0.02)


# ---------- write-back -------------------------------------------------------


def test_newer_replacement_is_written_back_and_the_link_restored(linked):
    source, link = linked
    host_refresh(link, now_ms() + 9 * HOUR_MS)
    assert not link.is_symlink(), "the simulation must replace the link as the host does"

    assert settle(link, source) is True
    assert refresh_token(source) == "refresh-1"
    assert link.is_symlink()
    assert link.readlink() == source
    if os.name == "posix":
        assert source.stat().st_mode & 0o777 == 0o600


def test_older_replacement_is_never_written(linked):
    source, link = linked
    host_refresh(link, now_ms() + HOUR_MS, refresh="refresh-stale")
    assert settle(link, source) is False
    assert refresh_token(source) == "refresh-0"
    assert link.is_symlink()


def test_unreadable_replacement_is_left_for_the_next_look(linked):
    source, link = linked
    link.unlink()
    link.write_text("{not json", encoding="utf-8")
    assert settle(link, source) is False
    assert not link.is_symlink()
    assert refresh_token(source) == "refresh-0"


def test_an_intact_link_is_left_alone(linked):
    source, link = linked
    before = source.stat().st_mtime_ns
    assert settle(link, source) is False
    assert link.is_symlink()
    assert source.stat().st_mtime_ns == before


def test_write_back_lands_behind_a_symlinked_stored_login(tmp_path):
    """A dotfiles-style stored login is itself a link; replacing that link
    would repeat the bug one level up."""
    real = store(tmp_path / "dotfiles" / CREDENTIALS, now_ms() + HOUR_MS)
    source = tmp_path / "stored" / CREDENTIALS
    source.parent.mkdir()
    source.symlink_to(real)
    link = tmp_path / "config" / CREDENTIALS
    link.parent.mkdir()
    link.symlink_to(source)

    host_refresh(link, now_ms() + 9 * HOUR_MS)
    assert settle(link, source) is True
    assert source.is_symlink()
    assert refresh_token(real) == "refresh-1"


@pytest.mark.usefixtures("fast")
def test_keeper_writes_back_while_the_configuration_is_in_use(linked):
    source, link = linked
    with keep_login(link):
        host_refresh(link, now_ms() + 9 * HOUR_MS)
        assert wait_for(lambda: refresh_token(source) == "refresh-1")
        assert wait_for(link.is_symlink)


def test_exit_check_catches_a_replacement_the_poll_missed(linked, monkeypatch):
    source, link = linked
    monkeypatch.setattr(host_login, "POLL_S", 60)
    with keep_login(link):
        host_refresh(link, now_ms() + 9 * HOUR_MS)
    assert refresh_token(source) == "refresh-1"
    assert link.is_symlink()


def test_keeper_ignores_a_configuration_without_a_link(tmp_path):
    credentials = store(tmp_path / CREDENTIALS, now_ms() + HOUR_MS)
    with keep_login(credentials):
        pass
    with keep_login(tmp_path / "absent" / CREDENTIALS):
        pass
    assert refresh_token(credentials) == "refresh-0"


# ---------- the refresh claim -----------------------------------------------


def test_expired_login_takes_the_claim(linked):
    source, _ = linked
    store(source, now_ms() - 1000)
    claim = acquire_claim(source, "mark-a")
    assert claim == source.parent / CLAIM_NAME
    assert claim.read_text(encoding="utf-8") == "mark-a"


def test_fresh_login_takes_no_claim(linked):
    source, _ = linked
    assert acquire_claim(source, "mark-a") is None
    assert not (source.parent / CLAIM_NAME).exists()


@pytest.mark.usefixtures("fast")
def test_claim_is_released_once_the_refresh_is_written_back(linked):
    source, link = linked
    store(source, now_ms() - 1000)
    claim = source.parent / CLAIM_NAME
    with keep_login(link):
        assert claim.exists()
        host_refresh(link, now_ms() + 8 * HOUR_MS)
        assert wait_for(lambda: not claim.exists())
        assert refresh_token(source) == "refresh-1"


@pytest.mark.usefixtures("fast")
def test_waiter_proceeds_with_the_refreshed_login(linked, monkeypatch):
    source, _ = linked
    store(source, now_ms() - 1000)
    claim = source.parent / CLAIM_NAME
    claim.write_text("mark-holder", encoding="utf-8")
    monkeypatch.setattr(host_login, "CLAIM_WAIT_S", 5)

    def holder_writes_back():
        time.sleep(0.1)
        store(source, now_ms() + 8 * HOUR_MS, refresh="refresh-1")

    threading.Thread(target=holder_writes_back).start()
    assert acquire_claim(source, "mark-waiter") is None
    assert refresh_token(source) == "refresh-1"
    assert claim.read_text(encoding="utf-8") == "mark-holder"


@pytest.mark.usefixtures("fast")
def test_waiter_refuses_when_no_refresh_arrives(linked, monkeypatch):
    source, _ = linked
    store(source, now_ms() - 1000)
    (source.parent / CLAIM_NAME).write_text("mark-holder", encoding="utf-8")
    monkeypatch.setattr(host_login, "CLAIM_WAIT_S", 0.1)
    with pytest.raises(SystemExit, match=CLAIM_NAME) as refused:
        acquire_claim(source, "mark-waiter")
    assert "/login" in str(refused.value)


@pytest.mark.usefixtures("fast")
def test_abandoned_claim_is_taken_over(linked):
    source, _ = linked
    store(source, now_ms() - 1000)
    claim = source.parent / CLAIM_NAME
    claim.write_text("mark-dead", encoding="utf-8")
    old = time.time() - host_login.CLAIM_STALE_S - 10
    os.utime(claim, (old, old))
    assert acquire_claim(source, "mark-new") == claim
    assert claim.read_text(encoding="utf-8") == "mark-new"


def test_release_leaves_another_runs_claim(tmp_path):
    claim = tmp_path / CLAIM_NAME
    claim.write_text("mark-theirs", encoding="utf-8")
    release_claim(claim, "mark-mine")
    assert claim.exists()
    release_claim(claim, "mark-theirs")
    assert not claim.exists()


# ---------- stopping a host child -------------------------------------------------

TRAPS_SIGTERM = (
    "import pathlib, signal, sys, time\n"
    "def done(*_):\n"
    "    pathlib.Path(sys.argv[1]).write_text('terminated', encoding='utf-8')\n"
    "    sys.exit(0)\n"
    "signal.signal(signal.SIGTERM, done)\n"
    "pathlib.Path(sys.argv[2]).write_text('ready', encoding='utf-8')\n"
    "time.sleep(60)\n"
)
IGNORES_SIGTERM = (
    "import pathlib, signal, sys, time\n"
    "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
    "pathlib.Path(sys.argv[2]).write_text('ready', encoding='utf-8')\n"
    "time.sleep(60)\n"
)


def started_child(tmp_path: Path, script: str) -> tuple[subprocess.Popen, Path]:
    marker, ready = tmp_path / "terminated", tmp_path / "ready"
    proc = subprocess.Popen([sys.executable, "-c", script, str(marker), str(ready)])
    assert wait_for(ready.exists, timeout=10), "the child never installed its handler"
    return proc, marker


@pytest.mark.skipif(os.name != "posix", reason="SIGTERM handlers are POSIX")
def test_a_child_that_finishes_on_sigterm_is_never_killed(tmp_path, monkeypatch):
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    proc, marker = started_child(tmp_path, TRAPS_SIGTERM)
    assert host_login.stop_child(proc) == 0
    assert marker.read_text(encoding="utf-8") == "terminated"


@pytest.mark.skipif(os.name != "posix", reason="SIGTERM handlers are POSIX")
def test_a_child_that_ignores_sigterm_is_killed_after_the_grace(tmp_path, monkeypatch):
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 0.3)
    proc, marker = started_child(tmp_path, IGNORES_SIGTERM)
    started = time.monotonic()
    assert host_login.stop_child(proc) == -signal.SIGKILL
    assert time.monotonic() - started >= 0.3
    assert not marker.exists()


# ---------- the harness home: location ----------------------------------------


@pytest.fixture
def user_home(tmp_path):
    """A synthetic home directory with the operator's own client directories."""
    home = tmp_path / "user"
    (home / ".claude").mkdir(parents=True)
    (home / ".codex").mkdir()
    return home


def test_state_root_on_linux(tmp_path):
    user = tmp_path / "home"
    default = user / ".local" / "state" / "thesis-proposal-dev"
    xdg = tmp_path / "xdg-state"
    assert state_root({"XDG_STATE_HOME": str(xdg)}, "linux", user) == xdg / "thesis-proposal-dev"
    assert state_root({"XDG_STATE_HOME": "relative/state"}, "linux", user) == default
    assert state_root({}, "linux", user) == default


def test_state_root_on_darwin_and_windows(tmp_path):
    user = tmp_path / "home"
    assert state_root({}, "darwin", user) == (
        user / "Library" / "Application Support" / "thesis-proposal-dev")
    local = tmp_path / "local"
    assert state_root({"LOCALAPPDATA": str(local)}, "win32", user) == (
        local / "thesis-proposal-dev")


def test_state_root_takes_the_override_first(tmp_path):
    environ = {STATE_VAR: str(tmp_path / "override"), "XDG_STATE_HOME": str(tmp_path / "xdg")}
    assert state_root(environ, "linux", tmp_path / "home") == tmp_path / "override"


def test_the_default_home_is_under_the_state_root_and_not_the_operators(tmp_path):
    """testing-harness spec: Default home location."""
    user = tmp_path / "home"
    root = state_root({}, "linux", user)
    home = host_login.home(CLAUDE, {STATE_VAR: str(root)})
    assert home == user / ".local" / "state" / "thesis-proposal-dev" / "hosts" / "claude"
    assert home != user / ".claude"


def overlapping_roots(user_home: Path, tmp_path: Path) -> dict[str, tuple[Path, dict, str]]:
    """Each refused root, its environment, and the overlap the cause names.
    No root but the two home cases contains the synthetic home, so each case
    reaches the branch it is about."""
    other = tmp_path / "other"
    codex = tmp_path / "codex-home"
    configuration = "client configuration directory"
    return {
        "equals-home": (user_home, {}, "home directory"),
        "contains-home": (user_home.parent, {}, "home directory"),
        "inside-dot-claude": (user_home / ".claude" / "state", {}, configuration),
        "contains-claude-config-dir": (other, {"CLAUDE_CONFIG_DIR": str(other / "cfg")},
                                       f"{configuration} {other / 'cfg'}"),
        "equals-dot-codex": (user_home / ".codex", {}, configuration),
        "inside-codex-home": (codex / "state", {"CODEX_HOME": str(codex)}, configuration),
        "inside-repository": (tmp_path / "repo" / "state", {}, "repository"),
    }


@pytest.mark.parametrize("case", [
    "equals-home", "contains-home", "inside-dot-claude", "contains-claude-config-dir",
    "equals-dot-codex", "inside-codex-home", "inside-repository"])
def test_the_location_guard_refuses_an_overlap(case, user_home, tmp_path):
    root, environ, overlap = overlapping_roots(user_home, tmp_path)[case]
    problem = check_location(root, {STATE_VAR: str(root), **environ}, tmp_path / "repo",
                             user_home=user_home)
    assert isinstance(problem, LoginProblem)
    assert str(root) in problem.cause
    assert overlap in problem.cause
    assert STATE_VAR in problem.remedy


def test_the_location_guard_refuses_a_relative_root(user_home, tmp_path, monkeypatch):
    """The spec makes the home's path absolute: a relative override would
    resolve against whichever directory a command runs in — the home itself,
    for a login — and an isolated configuration's link to it would dangle."""
    monkeypatch.chdir(tmp_path)
    problem = check_location(Path("state"), {STATE_VAR: "state"}, tmp_path / "repo",
                             user_home=user_home)
    assert isinstance(problem, LoginProblem)
    assert "not an absolute path" in problem.cause
    assert STATE_VAR in problem.remedy


def test_the_default_root_passes_the_guard(user_home, tmp_path):
    root = state_root({}, "linux", user_home)
    assert check_location(root, {}, tmp_path / "repo", user_home=user_home) is None


def test_a_symlink_into_the_operators_configuration_is_refused(user_home, tmp_path):
    link = tmp_path / "innocent-looking"
    link.symlink_to(user_home / ".claude")
    problem = check_location(link / "state", {STATE_VAR: str(link / "state")},
                             tmp_path / "repo", user_home=user_home)
    assert problem is not None
    assert ".claude" in problem.cause


# ---------- the harness home: marker, seed, wipe ---------------------------------


@pytest.fixture
def harness_home(tmp_path, monkeypatch):
    """A seeded harness home under a test state root; the operator's own
    environment cannot steer it."""
    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    for name in (LONG_LIVED_TOKEN, "CLAUDE_REAL_CONFIG_DIR", "ROUTING_CONFIG_DIR"):
        monkeypatch.delenv(name, raising=False)
    # the default Anthropic profile directory the run checks: never the operator's
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    home = host_login.home(CLAUDE)
    host_login.seed(CLAUDE, home)
    return home


def test_seeding_writes_the_marker_the_opt_outs_and_the_profile_directory(harness_home):
    assert (harness_home / MARKER).is_file()
    settings = json.loads((harness_home / "settings.json").read_text(encoding="utf-8"))
    assert settings == dict(PINNED_SETTINGS)
    assert (harness_home / PROFILE_DIR).is_dir()
    assert not list((harness_home / PROFILE_DIR).iterdir())
    if os.name == "posix":
        assert harness_home.stat().st_mode & 0o777 == 0o700
    assert check_presence(harness_home) is None
    assert check_home(CLAUDE, harness_home) is None


def test_wipe_deletes_a_marked_home(harness_home):
    (harness_home / "skills" / "synced").mkdir(parents=True)
    assert wipe(harness_home) is None
    assert not harness_home.exists()


def test_wipe_refuses_an_unmarked_home(harness_home):
    (harness_home / MARKER).unlink()
    problem = wipe(harness_home)
    assert problem is not None
    assert str(harness_home) in problem.cause
    assert harness_home.is_dir()


def test_wipe_refuses_a_symlinked_home(harness_home, tmp_path):
    link = tmp_path / "linked-home"
    link.symlink_to(harness_home)
    problem = wipe(link)
    assert problem is not None
    assert str(link) in problem.cause
    assert (harness_home / MARKER).is_file()


# ---------- the harness home: preflight checks -----------------------------------


def test_presence_names_the_login_command(harness_home, tmp_path):
    missing = check_presence(tmp_path / "nowhere")
    assert missing is not None
    assert LOGIN_COMMAND in missing.remedy
    (harness_home / MARKER).unlink()
    unmarked = check_presence(harness_home)
    assert unmarked is not None
    assert MARKER in unmarked.cause
    # a directory without the marker is never adopted: the same remedy as a wipe's
    assert unmarked.remedy == f"move it aside, then run `{LOGIN_COMMAND}`"


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission bits")
def test_presence_refuses_a_home_wider_than_owner_only(harness_home):
    harness_home.chmod(0o750)
    problem = check_presence(harness_home)
    assert problem is not None
    assert "0700" in problem.cause
    assert LOGIN_COMMAND in problem.remedy


@pytest.mark.parametrize("entry", [
    "skills/synced/x", "skills/mine", "agents/helper.md", "commands/go.md",
    "output-styles/terse.md", "CLAUDE.md", "plugins/synced/y"])
def test_check_home_names_each_forbidden_entry(entry, harness_home):
    path = harness_home / entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("synthetic\n", encoding="utf-8")
    problem = check_home(CLAUDE, harness_home)
    assert problem is not None
    named = "/".join(entry.split("/")[:2])
    assert named in problem.cause
    assert RESET_COMMAND in problem.remedy


def test_check_home_names_an_installed_plugin(harness_home):
    record = harness_home / "plugins" / "installed_plugins.json"
    record.parent.mkdir()
    record.write_text(json.dumps({"version": 2, "plugins": {}}), encoding="utf-8")
    assert check_home(CLAUDE, harness_home) is None
    record.write_text(json.dumps({"version": 2, "plugins": {"x@market": [{}]}}),
                      encoding="utf-8")
    problem = check_home(CLAUDE, harness_home)
    assert problem is not None
    assert "plugins/installed_plugins.json" in problem.cause


def test_check_home_names_settings_with_an_extra_key(harness_home):
    (harness_home / "settings.json").write_text(
        json.dumps({**PINNED_SETTINGS, "model": "opus"}), encoding="utf-8")
    problem = check_home(CLAUDE, harness_home)
    assert problem is not None
    assert "settings.json" in problem.cause


def test_check_home_allows_host_state_and_marketplace_caches(harness_home):
    for entry in ("plugins/marketplaces/m/x.json", "plugins/cache/c", "projects/p/s.jsonl"):
        path = harness_home / entry
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    (harness_home / ".claude.json").write_text("{}", encoding="utf-8")
    assert check_home(CLAUDE, harness_home) is None


def ready(home: Path, **fields) -> dict:
    return {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty",
            "configDirectory": str(home), **PRIVATE, **fields}


def test_check_status_passes_the_subscription_login(harness_home):
    assert check_status(ready(harness_home), harness_home) is None


@pytest.mark.parametrize(("fields", "fragment", "remedy"), [
    ({"loggedIn": False}, "no login", LOGIN_COMMAND),
    ({"authMethod": "api_key"}, "'api_key'", RESET_COMMAND),
    ({"authMethod": "api_key_helper"}, "'api_key_helper'", RESET_COMMAND),
    ({"authMethod": "third_party"}, "'third_party'", RESET_COMMAND),
    ({"apiProvider": "bedrock"}, "'bedrock'", RESET_COMMAND),
    ({"configDirectory": "/fake/elsewhere"}, "/fake/elsewhere", "redirect"),
    ({"configDirectory": None}, "no configuration directory", "update Claude Code"),
])
def test_check_status_refuses_each_unusable_login(fields, fragment, remedy, harness_home):
    status = ready(harness_home, **fields)
    if fields.get("configDirectory", "") is None:
        del status["configDirectory"]
    problem = check_status(status, harness_home)
    assert problem is not None
    assert fragment in problem.cause
    assert remedy in problem.remedy
    for value in PRIVATE.values():
        assert value not in refusal(problem)


def test_an_empty_status_is_no_login(harness_home):
    problem = check_status({}, harness_home)
    assert problem is not None
    assert LOGIN_COMMAND in problem.remedy


# ---------- the refusal template and the login note ---------------------------


@pytest.mark.parametrize("passed", [False, True], ids=["L3-open", "L3-passed"])
@pytest.mark.parametrize("remedy", [
    f"run `{LOGIN_COMMAND}`", f"remove skills/synced, or run `{RESET_COMMAND}`",
    "remove the wrapper or managed setting that redirects the configuration directory",
    "update Claude Code to a version that reports `configDirectory`"])
def test_refusal_follows_one_template(remedy, passed, monkeypatch):
    monkeypatch.setattr(host_login, "L3_PASSED", passed)
    message = refusal(LoginProblem("the harness login home /fake/home holds no login", remedy))
    assert message.startswith("untested: the harness login home /fake/home holds no login. ")
    assert message.count(remedy[1:]) == 1
    if "host-login" in remedy and not passed:
        assert message.endswith(f"{L3_CAVEAT}.")
        assert "not affected" not in message
    else:
        assert message.endswith(f"{NOT_AFFECTED}.")


@pytest.mark.parametrize("passed", [False, True])
def test_login_note_tracks_l3(passed, monkeypatch):
    monkeypatch.setattr(host_login, "L3_PASSED", passed)
    assert login_note("redirect") == NOT_AFFECTED
    assert login_note(RESET_COMMAND) == (NOT_AFFECTED if passed else L3_CAVEAT)


def test_preflight_runs_its_checks_in_order(harness_home, monkeypatch):
    monkeypatch.setattr(host_login, "read_status", lambda _record, home: ready(home))
    assert host_login.preflight(CLAUDE) is None
    (harness_home / "CLAUDE.md").write_text("synthetic\n", encoding="utf-8")
    monkeypatch.setattr(host_login, "read_status", lambda *_a: {})
    problem = host_login.preflight(CLAUDE)
    assert problem is not None
    assert "CLAUDE.md" in problem.cause  # cleanliness is checked before the login


def test_preflight_on_a_missing_home_starts_no_client(tmp_path, monkeypatch):
    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    monkeypatch.setattr(host_login, "read_status",
                        lambda *_a: pytest.fail("a client was started for a missing home"))
    problem = host_login.preflight(CLAUDE)
    assert problem is not None
    assert LOGIN_COMMAND in problem.remedy
    assert not (tmp_path / "state").exists()


def test_read_status_keeps_only_the_four_fields(harness_home, monkeypatch):
    seen = {}

    def client(argv, env, *, interactive, cwd, stop_signal):
        seen.update(argv=argv, env=env, interactive=interactive, cwd=cwd, stop=stop_signal)
        return 0, json.dumps(ready(harness_home))

    monkeypatch.setenv(LONG_LIVED_TOKEN, "placeholder-not-a-token")
    monkeypatch.setattr(host_login, "run_client", client)
    status = host_login.read_status(CLAUDE, harness_home)
    assert status == {"loggedIn": True, "authMethod": "claude.ai",
                      "apiProvider": "firstParty", "configDirectory": str(harness_home)}
    assert seen["argv"] == ["claude", "auth", "status", "--json"]
    assert not seen["interactive"]
    assert seen["stop"] == CLAUDE.stop_signal  # a termination request at the limit
    assert seen["env"]["CLAUDE_CONFIG_DIR"] == str(harness_home)
    assert seen["env"]["ANTHROPIC_CONFIG_DIR"] == str(harness_home / PROFILE_DIR)
    assert LONG_LIVED_TOKEN not in seen["env"]  # the home's own login, not the token


def test_read_status_without_json_is_no_login_state(harness_home, monkeypatch):
    monkeypatch.setattr(host_login, "run_client", lambda *_a, **_k: (1, "Not logged in"))
    assert host_login.read_status(CLAUDE, harness_home) == {}


# ---------- prepare_config and isolated_config -----------------------------


@pytest.fixture
def linked_home(harness_home, monkeypatch):
    """The harness home logged in, with its preflight stubbed to pass."""
    store(harness_home / CREDENTIALS, now_ms() + HOUR_MS)
    monkeypatch.setattr(host_login, "preflight", lambda *_a, **_k: None)
    return harness_home


@pytest.fixture
def opted_in(request, tmp_path, monkeypatch):
    """The explicit opt-in: CLAUDE_REAL_CONFIG_DIR names the operator's login,
    beside a harness home it must leave alone."""
    request.getfixturevalue("harness_home")
    stored = tmp_path / "home-claude"
    stored.mkdir()
    monkeypatch.setenv("CLAUDE_REAL_CONFIG_DIR", str(stored))
    monkeypatch.setattr(host_login, "preflight",
                        lambda *_a, **_k: pytest.fail("the opt-in ran the preflight"))
    return stored


def test_prepare_config_links_the_harness_login_by_default(linked_home, tmp_path):
    config = routing.prepare_config(tmp_path / "base")
    assert (config / CREDENTIALS).is_symlink()
    assert (config / CREDENTIALS).readlink() == linked_home / CREDENTIALS


@pytest.mark.usefixtures("linked_home")
def test_prepare_config_writes_exactly_the_pinned_opt_outs(tmp_path):
    """testing-harness spec: Account surfaces opted out — the settings hold the
    three opt-outs and nothing else, beside an empty profile directory."""
    config = routing.prepare_config(tmp_path / "base")
    settings = json.loads((config / "settings.json").read_text(encoding="utf-8"))
    assert settings == dict(PINNED_SETTINGS)
    assert all(isinstance(value, bool) for value in settings.values())
    profile = config / PROFILE_DIR
    assert profile.is_dir()
    assert not list(profile.iterdir())
    if os.name == "posix":
        assert profile.stat().st_mode & 0o777 == 0o700
    assert isolation_problem(config) is None


def test_a_preflight_problem_refuses_and_links_nothing(harness_home, tmp_path, monkeypatch):
    problem = LoginProblem(f"the harness login home {harness_home} holds no login",
                           f"run `{LOGIN_COMMAND}`")
    monkeypatch.setattr(host_login, "preflight", lambda *_a, **_k: problem)
    with pytest.raises(SystemExit) as refused:
        routing.prepare_config(tmp_path / "base")
    assert refused.value.code == refusal(problem)
    assert not (tmp_path / "base" / "config" / CREDENTIALS).is_symlink()


@pytest.mark.usefixtures("harness_home")
def test_a_login_that_is_no_file_refuses_with_token_mode(tmp_path, monkeypatch):
    """A clean, logged-in home without a `.credentials.json` — the macOS
    Keychain keeps the login — has nothing to link: refused with token mode,
    never a dangling link."""
    monkeypatch.setattr(host_login, "read_status", lambda _record, home: ready(home))
    assert host_login.preflight(CLAUDE) is None
    with pytest.raises(SystemExit) as refused:
        routing.prepare_config(tmp_path / "base")
    message = str(refused.value.code)
    assert message.startswith("untested: ")
    assert "Keychain" in message
    assert "claude setup-token" in message
    link = tmp_path / "base" / "config" / CREDENTIALS
    assert not link.exists()
    assert not link.is_symlink()


@pytest.mark.usefixtures("harness_home")
def test_the_preflight_checks_the_default_profile_directory_first(tmp_path, monkeypatch):
    """Fallback F8 before the status check starts a client: the harness
    login's own host processes are held to it too, token or not."""
    monkeypatch.setattr(host_login, "read_status",
                        lambda *_a: pytest.fail("a client was started beside a profile"))
    monkeypatch.setenv(LONG_LIVED_TOKEN, "placeholder-not-a-token")
    (tmp_path / "xdg" / "anthropic" / "work-profile-name").mkdir(parents=True)
    problem = host_login.preflight(CLAUDE)
    assert problem is not None
    assert str(tmp_path / "xdg" / "anthropic") in problem.cause
    assert "work-profile-name" not in refusal(problem)
    assert problem.remedy == "move the profiles aside"


def test_the_routing_config_override_is_refused(linked_home, tmp_path, monkeypatch):
    """testing-harness spec: Prepared configuration without the opt-outs — the
    override is no longer read, prepared or not."""
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    (prepared / "settings.json").write_text(json.dumps(dict(PINNED_SETTINGS)), encoding="utf-8")
    monkeypatch.setenv("ROUTING_CONFIG_DIR", str(prepared))
    with pytest.raises(SystemExit) as refused, routing.isolated_config("test-config-"):
        pytest.fail("the run started on an operator-prepared configuration")
    message = str(refused.value.code)
    assert "ROUTING_CONFIG_DIR" in message
    assert "no longer read" in message
    assert LOGIN_COMMAND in message
    assert linked_home.is_dir()


@pytest.mark.usefixtures("linked_home")
def test_the_refused_override_is_untested_in_a_dev_run(tmp_path, monkeypatch):
    monkeypatch.setenv("ROUTING_CONFIG_DIR", str(tmp_path / "prepared"))
    with pytest.raises(claude_runner.RunnerFailure) as refused, ExitStack() as stack:
        claude_runner.enter_isolation(stack, "devrun-config-")
    assert refused.value.untested
    assert "ROUTING_CONFIG_DIR" in refused.value.message


def test_a_preflight_refusal_is_untested_in_a_dev_run(harness_home):
    """The home is seeded but holds no login: the real preflight refuses before
    any status check could find one (testing-harness spec: No harness login)."""
    (harness_home / MARKER).unlink()
    with pytest.raises(claude_runner.RunnerFailure) as refused, ExitStack() as stack:
        claude_runner.enter_isolation(stack, "devrun-config-")
    assert refused.value.untested
    assert refused.value.message.startswith("untested: ")
    assert LOGIN_COMMAND in refused.value.message


def test_the_opt_in_links_the_named_login_without_a_preflight(opted_in, tmp_path):
    source = store(opted_in / CREDENTIALS, now_ms() + HOUR_MS)
    config = routing.prepare_config(tmp_path / "base")
    assert (config / CREDENTIALS).readlink() == source


@pytest.mark.usefixtures("opted_in")
def test_a_missing_opted_in_login_names_its_remedy(tmp_path):
    with pytest.raises(SystemExit) as refused:
        routing.prepare_config(tmp_path / "base")
    message = str(refused.value)
    assert "/login" in message
    assert "CLAUDE_REAL_CONFIG_DIR" in message


@pytest.mark.usefixtures("linked_home")
def test_a_profile_in_the_default_directory_refuses_the_run(tmp_path):
    """Fallback F8: whether the host ignores the default profile directory when
    ANTHROPIC_CONFIG_DIR names another is unverified (L8 inconclusive)."""
    (tmp_path / "xdg" / "anthropic" / "work-profile-name").mkdir(parents=True)
    with pytest.raises(SystemExit) as refused, routing.isolated_config("test-config-"):
        pytest.fail("the run started beside a stored Anthropic profile")
    message = str(refused.value.code)
    assert str(tmp_path / "xdg" / "anthropic") in message
    assert "work-profile-name" not in message


def test_long_lived_token_links_nothing_and_never_reads_the_home(tmp_path, monkeypatch):
    """testing-harness spec: Token bypasses the harness login."""
    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    monkeypatch.setenv(LONG_LIVED_TOKEN, "placeholder-not-a-token")
    monkeypatch.setattr(host_login, "read_status",
                        lambda *_a: pytest.fail("the token run checked the harness login"))
    config = routing.prepare_config(tmp_path / "base")
    assert (config / "settings.json").is_file()
    assert not (config / CREDENTIALS).exists()
    assert not (config / CREDENTIALS).is_symlink()
    assert not (tmp_path / "state").exists()


def test_isolated_config_writes_back_to_the_harness_home(linked_home, tmp_path, monkeypatch):
    """testing-harness spec: Refresh inside an isolated run reaches the stored
    login — the harness login, never the operator's. HOME points at the
    stand-in, so `~/.claude` is the stand-in operator login: a regression that
    linked `~/.claude` again would write there and fail, never reach the
    developer's own login."""
    monkeypatch.setattr(host_login, "POLL_S", 60)
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(tmp_path / "user"))
    assert Path.home() == tmp_path / "user"
    operator = store(tmp_path / "user" / ".claude" / CREDENTIALS, now_ms() + HOUR_MS,
                     refresh="refresh-operator")
    before = (operator.read_bytes(), operator.stat().st_mtime_ns)
    with routing.isolated_config("test-config-") as config:
        link = config / CREDENTIALS
        assert link.is_symlink()
        host_refresh(link, now_ms() + 9 * HOUR_MS)
    assert refresh_token(linked_home / CREDENTIALS) == "refresh-1"
    assert (operator.read_bytes(), operator.stat().st_mtime_ns) == before
    assert not config.exists()


# ---------- which login a run used, and its remedy ---------------------------------


def test_login_source_names_each_login(linked_home, opted_in, tmp_path, monkeypatch):
    assert login_source(None, os.environ) is LoginSource.AMBIENT
    operator = tmp_path / "operator-config"
    operator.mkdir()
    (operator / CREDENTIALS).symlink_to(store(opted_in / CREDENTIALS, now_ms() + HOUR_MS))
    assert login_source(operator, os.environ) is LoginSource.OPERATOR
    monkeypatch.delenv("CLAUDE_REAL_CONFIG_DIR")
    harness = tmp_path / "harness-config"
    harness.mkdir()
    (harness / CREDENTIALS).symlink_to(linked_home / CREDENTIALS)
    assert login_source(harness, os.environ) is LoginSource.HARNESS
    monkeypatch.setenv(LONG_LIVED_TOKEN, "placeholder-not-a-token")
    assert login_source(harness, os.environ) is LoginSource.TOKEN


def test_the_label_survives_the_hosts_refresh_window(linked_home, opted_in, tmp_path,
                                                     monkeypatch):
    """While the host's refreshed file stands where the link was, before the
    keeper restores the link, the run is still labelled with the login it
    linked, and with that login's directory — never as the operator's opt-in."""
    config = tmp_path / "config"
    config.mkdir()
    (config / CREDENTIALS).write_text("{}", encoding="utf-8")  # the host's own file
    monkeypatch.delenv("CLAUDE_REAL_CONFIG_DIR")
    assert login_source(config, os.environ) is LoginSource.HARNESS
    assert login_dir(config, os.environ) == linked_home.resolve()
    monkeypatch.setenv("CLAUDE_REAL_CONFIG_DIR", str(opted_in))
    assert login_source(config, os.environ) is LoginSource.OPERATOR
    assert login_dir(config, os.environ) == opted_in.resolve()


EXPIRED_REASON = ("claude failed: success: api_error — Failed to authenticate: OAuth session "
                  "expired and could not be refreshed")


@pytest.mark.parametrize("passed", [False, True])
@pytest.mark.parametrize(("source", "remedy"), [
    (LoginSource.HARNESS, LOGIN_COMMAND),
    (LoginSource.AMBIENT, "`/login`"),
    (LoginSource.OPERATOR, "`/login`"),
    (LoginSource.TOKEN, "claude setup-token"),
])
def test_login_remedy_appends_exactly_that_logins_remedy(source, remedy, passed, monkeypatch):
    monkeypatch.setattr(host_login, "L3_PASSED", passed)
    message = login_remedy(EXPIRED_REASON, source)
    assert message.startswith(EXPIRED_REASON)
    assert remedy in message
    others = {LOGIN_COMMAND, "`/login`", "claude setup-token"} - {remedy}
    assert not [other for other in others if other in message]
    if source is LoginSource.HARNESS:
        assert message.endswith(f"{NOT_AFFECTED if passed else L3_CAVEAT}.")
    assert login_remedy("claude failed: error_max_budget_usd", source) == (
        "claude failed: error_max_budget_usd")


def test_the_write_back_target_is_the_labelled_login_directory(linked_home, opted_in, tmp_path,
                                                                monkeypatch):
    """testing-harness spec: Write-back target labelled — under the default,
    the only place a refresh is written is inside the harness home."""
    monkeypatch.delenv("CLAUDE_REAL_CONFIG_DIR")
    monkeypatch.setattr(host_login, "preflight", lambda *_a, **_k: None)
    config = routing.prepare_config(tmp_path / "default")
    assert login_dir(config, os.environ) == linked_home
    assert writeback_target(config / CREDENTIALS) == login_dir(config, os.environ) / CREDENTIALS

    monkeypatch.setenv("CLAUDE_REAL_CONFIG_DIR", str(opted_in))
    store(opted_in / CREDENTIALS, now_ms() + HOUR_MS)
    config = routing.prepare_config(tmp_path / "opt-in")
    assert login_dir(config, os.environ) == opted_in
    assert writeback_target(config / CREDENTIALS) == opted_in / CREDENTIALS

    monkeypatch.setenv(LONG_LIVED_TOKEN, "placeholder-not-a-token")
    config = routing.prepare_config(tmp_path / "token")
    assert login_dir(config, os.environ) is None
    assert writeback_target(config / CREDENTIALS) is None


# ---------- the Codex record and home (add-codex-dev-runner) -----------------------
#
# The Codex home must lie outside the system temporary directory, and `tmp_path`
# lies inside it, so these tests hand `check_location` a temporary directory of
# their own (`tempdir=`) that does not contain `tmp_path`.

CODEX_NOTE = "Your own Codex login is not affected"
X8_NOTE = "Whether this logs out your other ChatGPT sessions is unverified (X8)"


def test_the_default_codex_home_is_under_the_state_root_and_not_the_operators(tmp_path):
    """testing-harness spec: Default home location."""
    user = tmp_path / "home"
    root = state_root({}, "linux", user)
    home = host_login.home(host_login.CODEX, {STATE_VAR: str(root)})
    assert home == user / ".local" / "state" / "thesis-proposal-dev" / "hosts" / "codex"
    assert home != user / ".codex"


def test_a_root_in_the_temporary_directory_is_refused_for_codex_only(user_home, tmp_path):
    """testing-harness spec: Codex home in the temporary directory."""
    fake_tmp = tmp_path / "system-tmp"
    root = fake_tmp / "state"
    environ = {STATE_VAR: str(root)}
    problem = check_location(root, environ, tmp_path / "repo", user_home=user_home,
                             record=host_login.CODEX, tempdir=fake_tmp)
    assert isinstance(problem, LoginProblem)
    assert str(root) in problem.cause
    assert "temporary directory" in problem.cause
    assert problem.client == "codex"
    assert check_location(root, environ, tmp_path / "repo", user_home=user_home,
                          record=CLAUDE, tempdir=fake_tmp) is None
    elsewhere = tmp_path / "state"
    assert check_location(elsewhere, {STATE_VAR: str(elsewhere)}, tmp_path / "repo",
                          user_home=user_home, record=host_login.CODEX,
                          tempdir=fake_tmp) is None


@pytest.mark.parametrize("case", ["equals-dot-codex", "inside-dot-codex", "contains-codex-home"])
def test_the_codex_location_guard_refuses_an_overlap(case, user_home, tmp_path):
    """testing-harness spec: Override overlapping the operator's configuration."""
    codex_home = tmp_path / "elsewhere" / "codex-home"
    root, environ = {
        "equals-dot-codex": (user_home / ".codex", {}),
        "inside-dot-codex": (user_home / ".codex" / "state", {}),
        "contains-codex-home": (tmp_path / "elsewhere", {"CODEX_HOME": str(codex_home)}),
    }[case]
    problem = check_location(root, {STATE_VAR: str(root), **environ}, tmp_path / "repo",
                             user_home=user_home, record=host_login.CODEX,
                             tempdir=tmp_path / "system-tmp")
    assert isinstance(problem, LoginProblem)
    assert str(root) in problem.cause
    assert "client configuration directory" in problem.cause


def test_the_pinned_codex_configuration_is_one_text_and_one_parse():
    import tomllib

    assert tomllib.loads(host_login.PINNED_CONFIG_TOML) == host_login.PINNED_CONFIG
    assert host_login.PINNED_CONFIG["model_provider"] == "openai"
    assert host_login.PINNED_CONFIG["forced_login_method"] == "chatgpt"
    assert host_login.PINNED_CONFIG["cli_auth_credentials_store"] == "file"
    assert host_login.CODEX.seed == {"config.toml": host_login.PINNED_CONFIG_TOML}


@pytest.fixture
def codex_home(tmp_path):
    home = tmp_path / "codex-home"
    host_login.seed(host_login.CODEX, home)
    return home


def test_a_seeded_codex_home_is_clean(codex_home):
    assert (codex_home / MARKER).is_file()
    assert host_login.check_codex_home(codex_home) is None
    assert check_presence(codex_home, host_login.CODEX) is None


@pytest.mark.parametrize(("old", "new", "named"), [
    ('model_provider = "openai"', 'model_provider = "openrouter"', "model_provider"),
    ("[analytics]\nenabled = false", "[analytics]\nenabled = true", "analytics.enabled"),
    ("[analytics]\nenabled = false", "[analytics]\nenabled = 0", "analytics.enabled"),
    ("[history]\npersistence = \"none\"", "[history]\npersistence = \"save-all\"",
     "history.persistence"),
    ("check_for_update_on_startup = false\n", "", "check_for_update_on_startup"),
    ("[skills.bundled]\nenabled = false", "[skills.bundled]\nenabled = false\nextra = 1",
     "skills.bundled.extra"),
    ("[feedback]", "[mcp_servers.docs]\ncommand = \"docs\"\n\n[feedback]", "mcp_servers"),
])
def test_check_codex_home_names_the_differing_key_path(old, new, named, codex_home):
    """testing-harness spec: Codex home not clean — a changed, missing or extra key,
    compared as parsed values, so `0` never passes for `false`."""
    text = host_login.PINNED_CONFIG_TOML
    assert old in text
    (codex_home / "config.toml").write_text(text.replace(old, new), encoding="utf-8")
    problem = host_login.check_codex_home(codex_home)
    assert problem is not None
    assert named in problem.cause
    assert "uv run poe host-login codex --reset" in problem.remedy
    assert problem.client == "codex"


def test_check_codex_home_names_a_missing_configuration(codex_home):
    (codex_home / "config.toml").unlink()
    problem = host_login.check_codex_home(codex_home)
    assert problem is not None
    assert "config.toml" in problem.cause


@pytest.mark.parametrize("entry", [
    "AGENTS.md", "AGENTS.override.md", ".env", "hooks.json", "skills/x/SKILL.md",
    "memories/note.md"])
def test_check_codex_home_names_each_forbidden_entry(entry, codex_home):
    path = codex_home / entry
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("synthetic\n", encoding="utf-8")
    problem = host_login.check_codex_home(codex_home)
    assert problem is not None
    assert "/".join(entry.split("/")[:2]) in problem.cause


def test_check_codex_home_allows_the_host_state(codex_home):
    for entry in ("skills/.system/x/SKILL.md", "log/codex-tui.log", "quota.json",
                  ".harness-run.lock", "installation_id", "state.sqlite",
                  "shell_snapshots/s.sh", "plugins/cache/c", "models_cache.json"):
        path = codex_home / entry
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
    assert host_login.check_codex_home(codex_home) is None


MASKED = "sk-proj-***SYNTH"


@pytest.mark.parametrize(("stderr", "method"), [
    ("Logged in using ChatGPT\n", "chatgpt"),
    (f"Logged in using an API key - {MASKED}\n", "api-key"),
    ("Logged in using an access token\n", "access-token"),
    ("Logged in using a method from the future\n", "other"),
    ("Not logged in\n", "none"),
    ("", "none"),
])
def test_codex_status_maps_the_login_line_and_drops_the_key(stderr, method):
    """testing-harness spec: Codex status reveals no key."""
    parsed = host_login.codex_status(stderr)
    assert parsed == method
    assert MASKED not in repr(parsed)


def test_codex_version_parses_and_refuses_an_old_cli():
    """testing-harness spec: Codex CLI too old."""
    assert host_login.codex_version("codex-cli 0.160.0\n") == (0, 160, 0)
    assert host_login.codex_version("codex-cli 1.2.3-alpha.4") == (1, 2, 3)
    assert host_login.codex_version("not a version") is None
    assert host_login.CODEX_MIN_VERSION == (0, 160, 0)
    assert host_login.check_codex_version((0, 160, 0)) is None
    problem = host_login.check_codex_version((0, 159, 9))
    assert problem is not None
    assert "0.159.9" in problem.cause
    assert "0.160.0" in problem.cause
    assert "update the Codex CLI" in problem.remedy
    assert problem.client == "codex"
    installed = host_login.check_codex_version((0, 133, 0))  # the CLI installed on 2026-10-06
    assert installed is not None
    assert "0.133.0" in installed.cause
    unknown = host_login.check_codex_version(None)
    assert unknown is not None
    assert "update the Codex CLI" not in unknown.cause


@pytest.mark.parametrize("passed", [False, True], ids=["X8-open", "X8-passed"])
@pytest.mark.parametrize("remedy", [
    "run `uv run poe host-login codex`",
    "remove AGENTS.md, or run `uv run poe host-login codex --reset`",
    "update the Codex CLI through your package manager to 0.160.0 or later",
    "report it: the pinned feature list does not match this CLI"])
def test_a_codex_refusal_closes_with_the_codex_login_note(remedy, passed, monkeypatch):
    """testing-harness spec: Codex login note until X8."""
    monkeypatch.setattr(host_login, "X8_PASSED", passed)
    message = refusal(LoginProblem("the harness login home /fake/codex holds no login", remedy,
                                   "codex"))
    assert message.startswith("untested: the harness login home /fake/codex holds no login. ")
    if "host-login codex" in remedy and not passed:
        assert message.endswith(f"{X8_NOTE}.")
        assert "not affected" not in message
    else:
        assert message.endswith(f"{CODEX_NOTE}.")
    assert "Claude" not in message


@pytest.mark.parametrize("passed", [False, True])
def test_the_claude_note_ignores_x8_and_codex_ignores_l3(passed, monkeypatch):
    monkeypatch.setattr(host_login, "X8_PASSED", passed)
    monkeypatch.setattr(host_login, "L3_PASSED", True)
    assert login_note(f"run `{LOGIN_COMMAND}`") == NOT_AFFECTED
    assert refusal(LoginProblem("cause", f"run `{LOGIN_COMMAND}`")).endswith(f"{NOT_AFFECTED}.")
    monkeypatch.setattr(host_login, "L3_PASSED", False)
    assert login_note("run `uv run poe host-login codex`", "codex") == (
        CODEX_NOTE if passed else X8_NOTE)
    assert login_note(f"run `{LOGIN_COMMAND}`", "codex") == CODEX_NOTE


@pytest.mark.parametrize("passed", [False, True], ids=["X8-open", "X8-passed"])
def test_a_codex_login_failure_names_the_codex_remedy(passed, monkeypatch):
    """testing-harness spec: Codex login failure names the Codex remedy."""
    monkeypatch.setattr(host_login, "X8_PASSED", passed)
    reason = ("codex failed: Your access token could not be refreshed because your refresh "
              "token was already used. Please log out and sign in again.")
    message = login_remedy(reason, LoginSource.HARNESS, host_login.CODEX)
    assert message.startswith(reason)
    assert "uv run poe host-login codex" in message
    assert message.rstrip(".").endswith(CODEX_NOTE if passed else X8_NOTE)
    assert login_remedy("codex failed: something else", LoginSource.HARNESS,
                        host_login.CODEX) == "codex failed: something else"
    assert login_remedy(reason, LoginSource.HARNESS) == reason  # Claude's wording differs


# ---------- the Copilot record and home (add-copilot-dev-runner) -----------------------

COPILOT = host_login.COPILOT
COPILOT_NOTE = "Your own Copilot login is not affected"


def test_the_default_copilot_home_and_token_file_lie_under_the_state_root(tmp_path):
    """testing-harness spec: Default home location — the token file beside the home."""
    user = tmp_path / "home"
    root = state_root({}, "linux", user)
    home = host_login.home(COPILOT, {STATE_VAR: str(root)})
    assert home == user / ".local" / "state" / "thesis-proposal-dev" / "hosts" / "copilot"
    assert host_login.token_path(home) == home.parent / "copilot.token"
    assert home not in host_login.token_path(home).parents
    assert home != user / ".copilot"


@pytest.mark.parametrize("case", ["dot-copilot", "github-copilot", "copilot-home"])
@pytest.mark.parametrize("record", ["claude", "codex", "copilot"])
def test_the_location_guard_refuses_the_copilot_directories_for_every_record(
        case, record, user_home, tmp_path):
    """testing-harness spec: Override overlapping the operator's configuration."""
    inherited = tmp_path / "inherited-copilot"
    roots = {"dot-copilot": (user_home / ".copilot" / "state", {}),
             "github-copilot": (user_home / ".config" / "github-copilot" / "state", {}),
             "copilot-home": (inherited / "state", {"COPILOT_HOME": str(inherited)})}
    root, environ = roots[case]
    problem = check_location(root, {STATE_VAR: str(root), **environ}, tmp_path / "repo",
                             user_home=user_home, record=host_login.RECORDS[record])
    assert problem is not None
    assert "client configuration directory" in problem.cause
    assert problem.client == record


def test_a_refused_override_starts_no_copilot_child_and_creates_nothing(tmp_path, monkeypatch):
    """The location check runs before `copilot --version`, which would unpack the
    package under the state root."""
    root = tmp_path / "user"
    (root / ".copilot").mkdir(parents=True)
    monkeypatch.setattr(host_login.Path, "home", classmethod(lambda _cls: root))
    override = root / ".copilot" / "state"
    monkeypatch.setenv(STATE_VAR, str(override))
    popen: list = []
    monkeypatch.setattr(copilot_cli.subprocess, "Popen",
                        lambda *a, **_k: popen.append(a) or pytest.fail("Popen reached"))
    checks = list(copilot_cli.preflight_checks(copilot_cli.new_run()))
    assert [c.name for c in checks] == ["location"]
    assert checks[0].problem is not None
    assert popen == []
    assert not override.exists()


@pytest.fixture
def copilot_home(tmp_path, monkeypatch):
    """A seeded Copilot home; the account home comes from a patched password entry."""
    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    account = tmp_path / "account"
    account.mkdir()

    class Entry:
        pw_dir = str(account)

    monkeypatch.setattr(host_login, "pwd", type("Pwd", (), {
        "getpwuid": staticmethod(lambda _uid: Entry())}))
    monkeypatch.setattr(host_login.os, "getuid", lambda: 4242, raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "scratch-home"))  # never the deny list's source
    home = host_login.home(COPILOT)
    host_login.seed(COPILOT, home)
    return home


@pytest.mark.skipif(host_login.pwd is None, reason="the password database is POSIX")
def test_the_deny_list_is_built_by_construction_from_the_password_entry(copilot_home, tmp_path):
    """testing-harness spec: Copilot settings seeded before the token is read."""
    settings = json.loads((copilot_home / "settings.json").read_text(encoding="utf-8"))
    sandbox = settings["sandbox"]
    assert (sandbox["enabled"], sandbox["allowBypass"], sandbox["allowDevToolAccess"]) == (
        True, False, False)
    assert sandbox["auth"] == {"git": False, "gh": False}
    deny = sandbox["userPolicy"]["filesystem"]["deniedPaths"]
    state = copilot_home.parent.parent
    assert deny == [str(tmp_path / "account"), "/run/user/4242", str(state),
                    str(host_login.token_path(copilot_home))]
    assert all(str(tmp_path / "scratch-home") not in path for path in deny)
    assert "deniedPaths" not in sandbox["userPolicy"]  # the package's path, not the docs'
    assert (settings["autoUpdate"], settings["memory"], settings["disableAllHooks"],
            settings["storeTokenPlaintext"]) == (False, False, True, True)
    assert (copilot_home / "gh").is_dir()
    assert not any((copilot_home / "gh").iterdir())
    assert host_login.check_copilot_home(copilot_home) is None


@pytest.mark.skipif(host_login.pwd is None, reason="the password database is POSIX")
def test_a_state_root_inside_the_account_home_is_covered_by_the_home(tmp_path):
    account = tmp_path / "account"
    home = account / ".local" / "state" / "thesis-proposal-dev" / "hosts" / "copilot"
    deny = host_login.deny_list(home, account, uid=1000)
    assert deny == [str(account), "/run/user/1000", str(home.parent / "copilot.token")]


@pytest.mark.parametrize(("change", "named"), [
    (lambda s: s["sandbox"].update(allowBypass=True), "sandbox.allowBypass"),
    (lambda s: s.update(memory=True), "memory"),
    (lambda s: s.update(extra=1), "extra key extra"),
])
def test_check_copilot_home_names_a_differing_settings_key(change, named, copilot_home):
    path = copilot_home / "settings.json"
    settings = json.loads(path.read_text(encoding="utf-8"))
    change(settings)
    path.write_text(json.dumps(settings), encoding="utf-8")
    problem = host_login.check_copilot_home(copilot_home)
    assert problem is not None
    assert named in problem.cause
    assert "uv run poe host-login copilot --reset" in problem.remedy


LAUNCHED = "2026-01-01T00:00:00.000Z"  # the shape of the client's `firstLaunchAt`


def test_check_copilot_home_names_a_state_key_outside_the_managed_set(copilot_home):
    (copilot_home / "config.json").write_text(json.dumps(
        {"firstLaunchAt": LAUNCHED, "loggedInUsers": [], "model": "copilot-fixture-a"}),
        encoding="utf-8")
    problem = host_login.check_copilot_home(copilot_home)
    assert "key model outside the managed-state set" in problem.cause
    assert "firstLaunchAt" not in problem.cause


@pytest.mark.parametrize("entry", ["copilot-instructions.md", "skills/", "mcp-config.json",
                                   "pkg/", "copilot.token", "session-state/x", "gh/hosts.yml"])
def test_check_copilot_home_names_each_entry_outside_the_allow_list(entry, copilot_home):
    """testing-harness spec: Copilot home not clean."""
    path = copilot_home / entry.rstrip("/")
    if entry.endswith("/"):
        path.mkdir()
    else:
        path.parent.mkdir(exist_ok=True)
        path.write_text("synthetic", encoding="utf-8")
    problem = host_login.check_copilot_home(copilot_home)
    assert problem is not None
    assert entry.split("/")[0].rstrip("/") in problem.cause


def _make(path: Path, shape: str) -> None:
    if shape == "dir":
        path.mkdir()
    elif shape == "link":
        target = path.parent.parent / f"elsewhere-{path.name}"
        target.write_text("", encoding="utf-8")
        path.symlink_to(target)
    else:
        path.write_text(shape, encoding="utf-8")


@pytest.mark.parametrize(("name", "shape", "named"), [
    ("session-store.db-journal", "", "session-store.db-journal"),  # not one of the three
    ("session-store.db.bak", "x", "session-store.db.bak"),
    ("session-store.db", "link", "session-store.db (not a regular file)"),
    ("session-store.db-wal", "dir", "session-store.db-wal (not a regular file)"),
    (host_login.LOCK_NAME, "written through an inherited descriptor",
     f"{host_login.LOCK_NAME} (not an empty regular file)"),
    (host_login.LOCK_NAME, "link", f"{host_login.LOCK_NAME} (not an empty regular file)"),
    (host_login.LOCK_NAME, "dir", f"{host_login.LOCK_NAME} (not an empty regular file)"),
])
def test_check_copilot_home_holds_the_store_and_the_lock_to_their_shape(name, shape, named,
                                                                       copilot_home):
    """Decision 6: the session store is exactly its three regular files, and the
    run lock an empty regular file; anything else under those names refuses,
    named, never read."""
    _make(copilot_home / name, shape)
    problem = host_login.check_copilot_home(copilot_home)
    assert problem is not None
    assert named in problem.cause


def test_check_copilot_home_allows_every_allow_listed_entry(copilot_home):
    (copilot_home / "config.json").write_text(json.dumps(
        dict.fromkeys(host_login.MANAGED_STATE_KEYS, LAUNCHED)), encoding="utf-8")
    for name in (*host_login.COPILOT_STORE, "quota.json", host_login.LOCK_NAME):
        (copilot_home / name).write_text("", encoding="utf-8")
    (copilot_home / "session-store.db").write_text("SQLite format 3", encoding="utf-8")
    (copilot_home / "session-state").mkdir()
    assert host_login.check_copilot_home(copilot_home) is None


CLIENT_CONFIG = (COPILOT_STREAMS / "client-config.jsonc").read_text(encoding="utf-8")
SYNTHETIC_PAT = "github_pat_SYNTHETIC_STATE_VALUE"


HEADER, _, CLIENT_BODY = CLIENT_CONFIG.partition("{")
CLIENT_BODY = "{" + CLIENT_BODY


@pytest.mark.parametrize("text", [CLIENT_CONFIG, CLIENT_BODY])
def test_the_state_file_the_client_writes_is_clean(text, copilot_home):
    """testing-harness spec: Copilot state file written by the client — the
    two-line comment header and `firstLaunchAt` (1.0.91, task 7.4a); the same
    object without the header too."""
    assert HEADER.splitlines() == list(host_login.COPILOT_CONFIG_HEADER)
    (copilot_home / "config.json").write_text(text, encoding="utf-8")
    assert host_login.copilot_offenders(copilot_home) == []
    assert {"firstLaunchAt"} == host_login.MANAGED_STATE_KEYS


def _client_config(**extra: object) -> str:
    return HEADER + json.dumps({**json.loads(CLIENT_BODY), **extra}, indent=2)


TOKEN_STRING = "config.json (a token-shaped string)"
UNEXPECTED_COMMENT = "config.json (unexpected comment)"
NOT_A_TIMESTAMP = "key firstLaunchAt is not a timestamp string"
NESTED = 200_000  # deeper than the parser's recursion limit


@pytest.mark.parametrize(("text", "named"), [
    (_client_config(loggedInUsers=[]), "key loggedInUsers outside the managed-state set"),
    (_client_config(lastLoggedInUser="fixture-login-octocat"),
     "key lastLoggedInUser outside the managed-state set"),
    # a token prefix anywhere in the raw text, comments included (review follow-up)
    (_client_config(firstLaunchAt=SYNTHETIC_PAT), TOKEN_STRING),
    (_client_config(firstLaunchAt={"nested": [f"Bearer {SYNTHETIC_PAT}"]}), TOKEN_STRING),
    (_client_config(**{SYNTHETIC_PAT: 1}), TOKEN_STRING),
    (HEADER + f"// {SYNTHETIC_PAT}\n" + CLIENT_BODY, TOKEN_STRING),
    (CLIENT_CONFIG + "\n// gho_SYNTHETIC_TRAILING\n", TOKEN_STRING),
    # a prefix written with JSON escapes, found after the parse
    (HEADER + '{"firstLaunchAt": "\\u0067ithub_pat_SYNTHETIC"}', NOT_A_TIMESTAMP),
    (HEADER + f'{{"\\u0067ithub_pat_SYNTHETIC": 1, "firstLaunchAt": "{LAUNCHED}"}}',
     "a token-shaped key outside the managed-state set"),
    # the managed key holds a timestamp string, nothing else
    (_client_config(firstLaunchAt={"mcpServers": {"fixture": {}}}), NOT_A_TIMESTAMP),
    (_client_config(firstLaunchAt="Bearer fixture"), NOT_A_TIMESTAMP),
    (_client_config(firstLaunchAt=None), NOT_A_TIMESTAMP),
    pytest.param(HEADER + '{"firstLaunchAt": ' + "[" * NESTED + "]" * NESTED + "}",
                 "config.json (unreadable)", id="nested-too-deep"),
    # only the client's own header, exactly, at the top
    (CLIENT_CONFIG.replace("// This", "/* This") + "*/", UNEXPECTED_COMMENT),
    (HEADER + f'{{\n// fixture-comment-a\n"firstLaunchAt": "{LAUNCHED}"\n// fixture-comment-b\n}}',
     UNEXPECTED_COMMENT),
    ("\n".join(reversed(HEADER.splitlines())) + "\n" + CLIENT_BODY, UNEXPECTED_COMMENT),
    (HEADER.splitlines()[0] + "\n" + CLIENT_BODY, UNEXPECTED_COMMENT),
    (CLIENT_CONFIG.replace('Z"', 'Z" // an inline comment'), "config.json (unreadable)"),
    (HEADER + "[]\n", "config.json (not an object)"),
])
def test_a_client_state_file_with_more_than_the_header_and_the_key_is_refused(
        text, named, copilot_home):
    """testing-harness spec: Copilot home not clean — an extra key, another
    comment, a token prefix anywhere or a managed key that is no timestamp is
    named by its key or the file's state, never echoed."""
    (copilot_home / "config.json").write_text(text, encoding="utf-8")
    problem = host_login.check_copilot_home(copilot_home)
    assert problem is not None
    assert named in problem.cause
    for value in (SYNTHETIC_PAT, "SYNTHETIC", "fixture-login-octocat", "Bearer", "mcpServers",
                  "github_pat_", "gho_", "fixture-comment"):
        assert value not in problem.cause
    assert "uv run poe host-login copilot --reset" in problem.remedy


PROCESS_LOG = "process-1791308979893-4242.log"  # the client's naming, `process-<ms>-<pid>.log`


@pytest.mark.parametrize("names", [[], [PROCESS_LOG],
                                   [PROCESS_LOG, "process-1791308980001-4243.log"]])
def test_empty_process_logs_in_the_home_are_clean(names, copilot_home):
    """testing-harness spec: Copilot state file written by the client — the first
    login's headless read left one empty process log in `<home>/logs` before
    `--log-dir` (2026-10-06); an empty log holds nothing, so no reset is needed."""
    logs = copilot_home / "logs"
    logs.mkdir(mode=0o700)
    for name in names:
        (logs / name).write_text("", encoding="utf-8")
    assert host_login.copilot_offenders(copilot_home) == []


def _log_with_content(logs: Path) -> None:
    (logs / PROCESS_LOG).write_text("fixture-log-line\n", encoding="utf-8")


def _other_name(logs: Path) -> None:
    (logs / "fixture-notes.txt").write_text("", encoding="utf-8")


def _subdirectory(logs: Path) -> None:
    (logs / "process-1-2.log").mkdir()


def _linked_log(logs: Path) -> None:
    (logs / PROCESS_LOG).symlink_to(logs.parent / "settings.json")


def _linked_directory(logs: Path) -> None:
    logs.rmdir()
    elsewhere = logs.parent.parent / "fixture-elsewhere-logs"
    elsewhere.mkdir()
    logs.symlink_to(elsewhere, target_is_directory=True)


SYMLINKS = pytest.mark.skipif(os.name != "posix", reason="symlinks need privileges on Windows")


@pytest.mark.parametrize("fill", [_log_with_content, _other_name, _subdirectory,
                                  pytest.param(_linked_log, marks=SYMLINKS),
                                  pytest.param(_linked_directory, marks=SYMLINKS)])
def test_a_process_log_directory_with_more_than_empty_logs_is_refused(fill, copilot_home):
    """testing-harness spec: Copilot home not clean — every child logs to scratch,
    so a log with content, another entry, a subdirectory or a link in or as
    `<home>/logs` is refused; never read, only named."""
    logs = copilot_home / "logs"
    logs.mkdir(mode=0o700)
    fill(logs)
    problem = host_login.check_copilot_home(copilot_home)
    assert problem is not None
    assert "logs/ (client process logs with content or other entries" in problem.cause
    for value in ("process-", "fixture-log-line", "fixture-notes", "fixture-elsewhere"):
        assert value not in problem.cause


SESSION_ID = "0f1e2d3c-4b5a-4968-8776-655443322110"  # a uuid4, as the probe names its session


def _session_locks(home: Path) -> Path:
    locks = home / host_login.SESSION_STATE / host_login.SESSION_LOCKS
    locks.mkdir(parents=True, exist_ok=True)
    return locks


def _probe_leftovers(home: Path) -> None:
    """What K3 found after the probe's `session.create` and `session.delete`
    (2026-10-06): an empty `installed-plugins/` and one empty session lock."""
    (home / host_login.COPILOT_PLUGINS).mkdir()
    (_session_locks(home) / f"{SESSION_ID}.lock").write_text("", encoding="utf-8")


@pytest.mark.parametrize("fill", [
    _probe_leftovers,
    lambda home: (home / host_login.COPILOT_PLUGINS).mkdir(),
    lambda home: _session_locks(home),
    lambda home: [(_session_locks(home) / f"{SESSION_ID[:-1]}{n}.lock").write_text(
        "", encoding="utf-8") for n in range(3)],
])
def test_the_empty_entries_a_session_leaves_are_clean(fill, copilot_home):
    """testing-harness spec: Copilot session leftovers that hold nothing — the
    entries a model-free session's creation and deletion leave at 1.0.91 (K3)
    are accepted while they hold nothing, so the probe's reads leave the home
    clean without a reset."""
    fill(copilot_home)
    assert host_login.copilot_offenders(copilot_home) == []


def _plugin_entry(home: Path) -> None:
    (home / host_login.COPILOT_PLUGINS / "fixture-plugin").mkdir(parents=True)


def _lock_with_content(home: Path) -> None:
    (_session_locks(home) / f"{SESSION_ID}.lock").write_text("fixture-lock-body", encoding="utf-8")


def _lock_other_name(home: Path) -> None:
    (_session_locks(home) / "fixture-notes.lock").write_text("", encoding="utf-8")


def _lock_subdirectory(home: Path) -> None:
    (_session_locks(home) / f"{SESSION_ID}.lock").mkdir()


def _session_folder(home: Path) -> None:
    _probe_leftovers(home)
    (home / host_login.SESSION_STATE / SESSION_ID).mkdir()


def _locks_as_a_file(home: Path) -> None:
    (home / host_login.SESSION_STATE).mkdir(exist_ok=True)
    (home / host_login.SESSION_STATE / host_login.SESSION_LOCKS).write_text("", encoding="utf-8")


def _plugins_as_a_file(home: Path) -> None:
    (home / host_login.COPILOT_PLUGINS).write_text("", encoding="utf-8")


def _linked_lock(home: Path) -> None:
    (_session_locks(home) / f"{SESSION_ID}.lock").symlink_to(home / "settings.json")


def _linked_plugins(home: Path) -> None:
    elsewhere = home.parent / "fixture-elsewhere-plugins"
    elsewhere.mkdir()
    (home / host_login.COPILOT_PLUGINS).symlink_to(elsewhere, target_is_directory=True)


@pytest.mark.parametrize(("fill", "named"), [
    (_plugin_entry, "installed-plugins/ (not an empty directory)"),
    (_plugins_as_a_file, "installed-plugins/ (not an empty directory)"),
    pytest.param(_linked_plugins, "installed-plugins/ (not an empty directory)", marks=SYMLINKS),
    (_lock_with_content, "session-state/ (a session, or more than empty session locks)"),
    (_lock_other_name, "session-state/ (a session, or more than empty session locks)"),
    (_lock_subdirectory, "session-state/ (a session, or more than empty session locks)"),
    (_session_folder, "session-state/ (a session, or more than empty session locks)"),
    (_locks_as_a_file, "session-state/ (a session, or more than empty session locks)"),
    pytest.param(_linked_lock, "session-state/ (a session, or more than empty session locks)",
                 marks=SYMLINKS),
])
def test_session_leftovers_that_hold_anything_are_refused(fill, named, copilot_home):
    """testing-harness spec: Copilot session leftovers that hold nothing — a
    plugin directory with an entry, a lock with content, another name or a
    link, or a session folder refuses the home; named, never read."""
    fill(copilot_home)
    problem = host_login.check_copilot_home(copilot_home)
    assert problem is not None
    assert named in problem.cause
    for value in ("fixture-", SESSION_ID):
        assert value not in problem.cause


@pytest.mark.parametrize("remedy", ["run `uv run poe host-login copilot`",
                                    "run `uv run poe host-login copilot --reset`",
                                    "check the billing page"])
def test_the_copilot_note_is_always_the_not_affected_sentence(remedy):
    assert login_note(remedy, "copilot") == COPILOT_NOTE
    assert refusal(LoginProblem("cause", remedy, "copilot")).endswith(f"{COPILOT_NOTE}.")


@pytest.mark.parametrize(("value", "kind"), [
    ("ghp_CLASSIC_PLACEHOLDER", "a classic personal access token"),
    ("gho_OAUTH_PLACEHOLDER", "not a fine-grained personal access token"),
    ("github_patX_PLACEHOLDER", "not a fine-grained personal access token"),
])
def test_token_problem_refuses_by_prefix_without_echoing(value, kind):
    problem = host_login.token_problem(value)
    assert kind in problem.cause
    assert value not in refusal(problem)
    assert value[:6] not in problem.cause.replace(
        "github_pat_", "")
    assert host_login.token_problem("github_pat_SYNTHETIC_TEST_ONLY") is None


def test_the_copilot_record_keeps_claude_and_codex_unchanged():
    assert (CLAUDE.credential, CLAUDE.token_env) == ("client-login", None)
    assert (host_login.CODEX.credential, host_login.CODEX.token_env) == ("client-login", None)
    assert (COPILOT.credential, COPILOT.token_env) == ("token-file", "COPILOT_GITHUB_TOKEN")
    assert set(host_login.RECORDS) == {"claude", "codex", "copilot"}
    assert COPILOT.stripped("BASH_ENV")
    assert COPILOT.stripped("SSH_AUTH_SOCK")
    assert not COPILOT.stripped("BASH_ENVX")
    assert not host_login.CODEX.stripped("BASH_ENV")
