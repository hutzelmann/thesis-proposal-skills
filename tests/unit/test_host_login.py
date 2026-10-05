"""L0: isolated configurations keep the stored host login current (testing-harness
spec: Isolated measurement environment).

Recorded 2026-10-04 (host 2.1.284): a refresh inside an isolated
CLAUDE_CONFIG_DIR replaces the credentials symlink with a file of its own by
atomic rename, rotating the refresh token. The temp directory took the only
valid refresh token with it, and every later run failed with "OAuth session
expired and could not be refreshed". These tests replay that replacement on
synthetic credentials — the values are placeholders, never a real login.
"""

from __future__ import annotations

import json
import os
import threading
import time
from contextlib import ExitStack
from pathlib import Path

import claude_runner
import host_login
import pytest
import routing
from account_surfaces import PINNED_SETTINGS, PROFILE_DIR, isolation_problem
from host_login import (
    CLAIM_NAME,
    CREDENTIALS,
    LONG_LIVED_TOKEN,
    acquire_claim,
    keep_login,
    release_claim,
    settle,
)

HOUR_MS = 3_600_000


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


# ---------- prepare_config and isolated_config -----------------------------


@pytest.fixture
def stored_dir(tmp_path, monkeypatch):
    stored = tmp_path / "home-claude"
    stored.mkdir()
    monkeypatch.setenv("CLAUDE_REAL_CONFIG_DIR", str(stored))
    monkeypatch.delenv("ROUTING_CONFIG_DIR", raising=False)
    monkeypatch.delenv(LONG_LIVED_TOKEN, raising=False)
    # the default Anthropic profile directory the run checks: never the operator's
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    return stored


def test_prepare_config_links_the_stored_login(stored_dir, tmp_path):
    source = store(stored_dir / CREDENTIALS, now_ms() + HOUR_MS)
    config = routing.prepare_config(tmp_path / "base")
    assert (config / CREDENTIALS).is_symlink()
    assert (config / CREDENTIALS).readlink() == source


def test_prepare_config_writes_exactly_the_pinned_opt_outs(stored_dir, tmp_path):
    """testing-harness spec: Account surfaces opted out — the settings hold the
    three opt-outs and nothing else, beside an empty profile directory."""
    store(stored_dir / CREDENTIALS, now_ms() + HOUR_MS)
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


@pytest.fixture
def prepared_override(stored_dir, tmp_path, monkeypatch):
    """A `ROUTING_CONFIG_DIR` an operator prepared the old way: `{}` settings,
    no profile directory."""
    override = tmp_path / "prepared"
    override.mkdir()
    (override / "settings.json").write_text("{}\n", encoding="utf-8")
    store(stored_dir / CREDENTIALS, now_ms() + HOUR_MS)
    monkeypatch.setenv("ROUTING_CONFIG_DIR", str(override))
    return override


@pytest.mark.usefixtures("prepared_override")
def test_an_override_without_the_opt_outs_is_refused():
    with pytest.raises(SystemExit) as refused, routing.isolated_config("test-config-"):
        pytest.fail("the run started on an unprepared configuration")
    message = str(refused.value.code)
    assert "settings.json" in message
    assert PROFILE_DIR in message


@pytest.mark.usefixtures("prepared_override")
def test_the_refused_override_is_untested_in_a_dev_run():
    with pytest.raises(claude_runner.RunnerFailure) as refused, ExitStack() as stack:
        claude_runner.enter_isolation(stack, "devrun-config-")
    assert refused.value.untested
    assert "settings.json" in refused.value.message


def test_an_override_with_the_opt_outs_is_used_as_it_is(prepared_override):
    (prepared_override / "settings.json").write_text(json.dumps(dict(PINNED_SETTINGS)),
                                                     encoding="utf-8")
    (prepared_override / PROFILE_DIR).mkdir()
    with routing.isolated_config("test-config-") as config:
        assert config == prepared_override
    assert prepared_override.is_dir(), "an operator's directory is never removed"


def test_a_profile_in_the_default_directory_refuses_the_run(stored_dir, tmp_path):
    """Fallback F8: whether the host ignores the default profile directory when
    ANTHROPIC_CONFIG_DIR names another is unverified (L8 inconclusive)."""
    store(stored_dir / CREDENTIALS, now_ms() + HOUR_MS)
    (tmp_path / "xdg" / "anthropic" / "work-profile-name").mkdir(parents=True)
    with pytest.raises(SystemExit) as refused, routing.isolated_config("test-config-"):
        pytest.fail("the run started beside a stored Anthropic profile")
    message = str(refused.value.code)
    assert str(tmp_path / "xdg" / "anthropic") in message
    assert "work-profile-name" not in message


@pytest.mark.usefixtures("stored_dir")
def test_long_lived_token_links_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv(LONG_LIVED_TOKEN, "placeholder-not-a-token")
    config = routing.prepare_config(tmp_path / "base")
    assert (config / "settings.json").is_file()
    assert not (config / CREDENTIALS).exists()
    assert not (config / CREDENTIALS).is_symlink()


@pytest.mark.usefixtures("stored_dir")
def test_missing_login_refusal_names_the_remedy(tmp_path):
    with pytest.raises(SystemExit) as refused:
        routing.prepare_config(tmp_path / "base")
    message = str(refused.value)
    assert "/login" in message
    assert LONG_LIVED_TOKEN in message


def test_isolated_config_writes_back_and_removes_itself(stored_dir, monkeypatch):
    monkeypatch.setattr(host_login, "POLL_S", 60)
    source = store(stored_dir / CREDENTIALS, now_ms() + HOUR_MS)
    with routing.isolated_config("test-config-") as config:
        link = config / CREDENTIALS
        assert link.is_symlink()
        host_refresh(link, now_ms() + 9 * HOUR_MS)
    assert refresh_token(source) == "refresh-1"
    assert not config.exists()
