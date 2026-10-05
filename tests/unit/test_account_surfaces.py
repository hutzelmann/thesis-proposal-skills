"""L0: the claude.ai account-surface rules (testing-harness spec: Isolated
measurement environment; Isolated child environment).

Account surfaces follow the login, not the configuration directory: on host
2.1.284 an isolated routing case was offered the account's synced skills and its
Claude Docs connector. The streams come from `data/routing_streams/`: the reduced
recording `claudeai-surfaces.jsonl` and the synthetic `clean-init.jsonl` and
`ambient-user-mcp.jsonl`. Every environment value below is a placeholder.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from account_surfaces import (
    BILLING_PREFIXES,
    CONNECTORS_OFF,
    PINNED_SETTINGS,
    PROFILE_DIR,
    SurfaceLeak,
    ambient_env,
    config_surfaces,
    default_profile_store,
    isolation_problem,
    profile_store_problem,
    stream_surfaces,
    surface_reason,
)

STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"
TAGGED = ("docs", "google-workspace", "import-memory")


def events(name: str) -> list[dict]:
    lines = (STREAMS / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def init_with(**fields) -> list[dict]:
    """The clean init with some fields replaced."""
    clean = events("clean-init")
    return [{**clean[0], **fields}, *clean[1:]]


# ---------- stream_surfaces, isolated ---------------------------------------


def test_the_recorded_leak_yields_the_connector_and_every_tagged_skill():
    leaks = stream_surfaces(events("claudeai-surfaces"), isolated=True)
    assert SurfaceLeak("MCP server", "claude.ai Claude Docs") in leaks
    for name in TAGGED:
        assert SurfaceLeak("synced skill", name) in leaks
    assert len(leaks) == len(set(leaks)), "a skill synced twice is named once"
    assert not [leak for leak in leaks if leak.name.startswith("proposal-")]


def test_a_clean_init_yields_nothing():
    assert stream_surfaces(events("clean-init"), isolated=True) == []


def test_a_plugin_that_is_not_built_in_is_a_surface():
    plugins = [*events("clean-init")[0]["plugins"],
               {"name": "notes", "path": "/x", "source": "notes@claude.ai"}]
    assert stream_surfaces(init_with(plugins=plugins), isolated=True) == [
        SurfaceLeak("plugin", "notes@claude.ai")]


def test_a_namespaced_name_in_the_init_skills_is_a_surface():
    leaks = stream_surfaces(init_with(skills=["proposal-check", "anthropic-skills:pdf"]),
                            isolated=True)
    assert leaks == [SurfaceLeak("synced skill", "anthropic-skills:pdf")]


def test_any_mcp_server_is_a_surface_in_an_isolated_run():
    leaks = stream_surfaces(events("ambient-user-mcp"), isolated=True)
    assert [leak.name for leak in leaks] == ["local-notes", "claude.ai Claude Docs"]


def test_a_command_with_only_the_namespace_alias_is_a_surface():
    changed = {"type": "system", "subtype": "commands_changed", "commands": [
        {"name": "pdf", "description": "no tag here", "aliases": ["anthropic-skills:pdf"]}]}
    assert stream_surfaces([changed], isolated=True) == [SurfaceLeak("synced skill", "pdf")]


def test_other_events_are_not_read():
    assert stream_surfaces([{"type": "assistant", "message": {"content": []}},
                            {"type": "result", "result": "anthropic-skills:docs"}],
                           isolated=True) == []


# ---------- stream_surfaces, ambient ------------------------------------------


def test_ambient_runs_count_only_the_claudeai_server():
    assert stream_surfaces(events("ambient-user-mcp"), isolated=False) == [
        SurfaceLeak("MCP server", "claude.ai Claude Docs")]


def test_ambient_runs_ignore_the_operators_own_server_and_synced_skills():
    user_only = init_with(mcp_servers=[{"name": "local-notes", "source": "user"}])
    assert stream_surfaces(user_only, isolated=False) == []
    recorded = events("claudeai-surfaces")
    assert stream_surfaces(recorded, isolated=False) == [
        SurfaceLeak("MCP server", "claude.ai Claude Docs")]


# ---------- config_surfaces ---------------------------------------------------


@pytest.mark.parametrize(("path", "kind"), [
    ("skills/synced/x", "synced skill"), ("plugins/synced/y", "synced plugin")])
def test_synced_content_in_the_configuration_is_a_leak(tmp_path, path, kind):
    (tmp_path / path).mkdir(parents=True)
    assert config_surfaces(tmp_path) == [SurfaceLeak(kind, path)]


def test_an_empty_synced_directory_is_still_named(tmp_path):
    (tmp_path / "skills" / "synced").mkdir(parents=True)
    assert config_surfaces(tmp_path) == [SurfaceLeak("synced skill", "skills/synced")]


def test_a_clean_configuration_holds_no_synced_content(tmp_path):
    (tmp_path / "skills" / "proposal-check").mkdir(parents=True)
    assert config_surfaces(tmp_path) == []


# ---------- isolation_problem -------------------------------------------------


def closed(config: Path, settings: object = None) -> Path:
    """A configuration holding the pinned settings (or `settings`) and an
    empty profile directory."""
    config.mkdir(parents=True, exist_ok=True)
    payload = dict(PINNED_SETTINGS) if settings is None else settings
    (config / "settings.json").write_text(json.dumps(payload), encoding="utf-8")
    (config / PROFILE_DIR).mkdir(exist_ok=True)
    return config


def test_the_pinned_settings_and_an_empty_profile_directory_pass(tmp_path):
    assert isolation_problem(closed(tmp_path)) is None


@pytest.mark.parametrize("settings", [
    {},
    {**PINNED_SETTINGS, "model": "haiku"},
    {**PINNED_SETTINGS, "syncClaudeAiSkills": 0},
    {"syncClaudeAiSkills": False, "syncClaudeAiPlugins": False},
], ids=["empty", "extra-key", "number-for-bool", "missing-key"])
def test_settings_that_are_not_exactly_the_pinned_object_are_named(tmp_path, settings):
    problem = isolation_problem(closed(tmp_path, settings))
    assert "settings.json" in problem
    assert "disableClaudeAiConnectors" in problem


def test_missing_settings_are_named(tmp_path):
    (closed(tmp_path) / "settings.json").unlink()
    assert "settings.json" in isolation_problem(tmp_path)


def test_a_missing_profile_directory_is_named(tmp_path):
    (closed(tmp_path) / PROFILE_DIR).rmdir()
    assert PROFILE_DIR in isolation_problem(tmp_path)


def test_a_non_empty_profile_directory_is_named_without_its_contents(tmp_path):
    (closed(tmp_path) / PROFILE_DIR / "profile-secret-name").mkdir()
    problem = isolation_problem(tmp_path)
    assert PROFILE_DIR in problem
    assert "not empty" in problem
    assert "profile-secret-name" not in problem


def test_synced_content_is_a_preparation_problem(tmp_path):
    (closed(tmp_path) / "plugins" / "synced" / "y").mkdir(parents=True)
    assert "plugins/synced/y" in isolation_problem(tmp_path)


def test_every_problem_is_named_at_once(tmp_path):
    tmp_path.joinpath("settings.json").write_text("{}\n", encoding="utf-8")
    problem = isolation_problem(tmp_path)
    assert "settings.json" in problem
    assert PROFILE_DIR in problem


# ---------- surface_reason ----------------------------------------------------


def test_the_reason_names_each_surface_the_failed_opt_outs_and_token_mode(capsys):
    leaks = [SurfaceLeak("MCP server", "claude.ai Claude Docs"),
             SurfaceLeak("synced skill", "docs"),
             SurfaceLeak("synced plugin", "plugins/synced/y")]
    reason = surface_reason(leaks, isolated=True)
    for leak in leaks:
        assert f"{leak.kind} '{leak.name}'" in reason
    assert "opt-outs did not hold" in reason
    assert "disableClaudeAiConnectors" in reason
    assert "claude setup-token" in reason
    assert "CLAUDE_CODE_OAUTH_TOKEN" in reason
    assert capsys.readouterr() == ("", "")


def test_an_ambient_reason_blames_only_the_connector_switch():
    """An ambient run keeps the operator's own settings, so the pinned
    settings were never its opt-out: only the switch was."""
    reason = surface_reason([SurfaceLeak("MCP server", "claude.ai Claude Docs")],
                            isolated=False)
    assert "MCP server 'claude.ai Claude Docs'" in reason
    assert "connector switch did not hold (ENABLE_CLAUDEAI_MCP_SERVERS=false)" in reason
    assert "settings" not in reason
    assert "disableClaudeAiConnectors" not in reason
    assert "claude setup-token" in reason


# ---------- default profile directory (fallback F8) ---------------------------


def test_the_default_profile_directory_follows_xdg_then_home(tmp_path):
    assert default_profile_store({"XDG_CONFIG_HOME": str(tmp_path / "xdg"),
                                  "HOME": str(tmp_path / "home")}) == tmp_path / "xdg" / "anthropic"
    for xdg in ({}, {"XDG_CONFIG_HOME": ""}):
        assert default_profile_store({**xdg, "HOME": str(tmp_path / "home")}) == (
            tmp_path / "home" / ".config" / "anthropic")


@pytest.mark.parametrize("state", ["absent", "empty", "a-file"])
def test_an_absent_or_empty_profile_directory_bars_nothing(tmp_path, state):
    store = tmp_path / "anthropic"
    if state == "empty":
        store.mkdir()
    elif state == "a-file":
        store.write_text("", encoding="utf-8")
    assert profile_store_problem({"XDG_CONFIG_HOME": str(tmp_path)}) is None


def test_a_profile_in_the_default_directory_bars_an_isolated_run(tmp_path, capsys):
    (tmp_path / "anthropic" / "work-profile-name").mkdir(parents=True)
    problem = profile_store_problem({"XDG_CONFIG_HOME": str(tmp_path)})
    assert str(tmp_path / "anthropic") in problem
    assert "work-profile-name" not in problem
    assert "ANTHROPIC_CONFIG_DIR" in problem
    assert "claude setup-token" in problem
    assert capsys.readouterr() == ("", "")


@pytest.mark.skipif(os.name != "posix" or os.geteuid() == 0,
                    reason="needs POSIX permissions that bind the caller")
def test_a_profile_directory_that_cannot_be_listed_bars_the_run(tmp_path):
    store = tmp_path / "anthropic"
    store.mkdir(mode=0o000)
    try:
        assert profile_store_problem({"XDG_CONFIG_HOME": str(tmp_path)}) is not None
    finally:
        store.chmod(0o700)


def test_token_mode_lifts_the_profile_refusal(tmp_path):
    (tmp_path / "anthropic" / "profile").mkdir(parents=True)
    assert profile_store_problem({"XDG_CONFIG_HOME": str(tmp_path),
                                  "CLAUDE_CODE_OAUTH_TOKEN": "placeholder"}) is None


# ---------- ambient_env -------------------------------------------------------

LAUNCH = {
    "ANTHROPIC_API_KEY": "placeholder-not-a-key",
    "ANTHROPIC_BASE_URL": "https://gateway.invalid",
    "ANTHROPIC_AUTH_TOKEN": "placeholder",
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "ENABLE_CLAUDEAI_MCP_SERVERS": "true",
    "CLAUDE_EFFORT": "xhigh",
    "PATH": "/fake/bin",
}


def test_ambient_env_drops_billing_and_switches_connectors_off():
    before = dict(LAUNCH)
    env = ambient_env(LAUNCH)
    assert not [name for name in env if name.startswith(BILLING_PREFIXES)]
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert (env["CLAUDE_EFFORT"], env["PATH"]) == ("xhigh", "/fake/bin")
    assert set(env) == {"CLAUDE_EFFORT", "PATH", *CONNECTORS_OFF}
    assert before == LAUNCH


def test_the_switch_is_defined_once_and_reads_off():
    assert dict(CONNECTORS_OFF) == {"ENABLE_CLAUDEAI_MCP_SERVERS": "false"}
    assert dict(PINNED_SETTINGS) == {"syncClaudeAiSkills": False, "syncClaudeAiPlugins": False,
                                     "disableClaudeAiConnectors": True}
