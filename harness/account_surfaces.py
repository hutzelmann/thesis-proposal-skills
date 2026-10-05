"""What counts as a claude.ai account surface, and how every host child closes them.

Account surfaces follow the login, not the configuration directory. Since host
2.1.273 every `/login` session downloads the account's synced skills and
plugins in the background and fetches its claude.ai MCP connectors, so an
isolated configuration that links the operator's login carries them too. A
routing case recorded on host 2.1.284 under the isolated configuration showed
all three: the Claude Docs connector in `system/init.mcp_servers`, and nine
skills tagged "(claude.ai sync)" with `anthropic-skills:*` aliases in two
`system/commands_changed` events before the first assistant turn
(`tests/unit/data/routing_streams/claudeai-surfaces.jsonl`). The synced skills
compete with the skills under test, and the connector publishes to the
operator's account from a run that skips permission prompts.

This module holds the rules once (testing-harness spec: Isolated measurement
environment; Isolated child environment): the settings an isolated
configuration must hold, the connector switch every host child gets, the
ambient environment, and the pure checks over a stream, a configuration
directory and the default Anthropic profile directory. The routing rig, the
dev runner, its judge and the audit pre-flight all import from here; none
re-spells a value. Standard library only.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from host_login import LONG_LIVED_TOKEN

# The connector switch, applied to every host child the harness starts.
CONNECTORS_OFF: Mapping[str, str] = MappingProxyType({"ENABLE_CLAUDEAI_MCP_SERVERS": "false"})

# Every model run drops these: they can route the host's billing away from the
# subscription login (API key, gateway base URL and token, cloud providers).
BILLING_PREFIXES = ("ANTHROPIC_", "CLAUDE_CODE_USE_")

# Exactly this object, and nothing else, is an isolated configuration's settings.
PINNED_SETTINGS: Mapping[str, bool] = MappingProxyType({
    "syncClaudeAiSkills": False,
    "syncClaudeAiPlugins": False,
    "disableClaudeAiConnectors": True,
})
SETTINGS_FILE = "settings.json"

# An empty directory inside the isolated configuration that the child's
# Anthropic profile variable names, meant to keep a profile stored outside the
# configuration from becoming its login. Whether the host honours the variable
# is unverified (L8 inconclusive on 2.1.284, 2026-10-05), so an isolated run is
# also refused while the default profile directory, `${XDG_CONFIG_HOME:-
# $HOME/.config}/anthropic`, holds any entry (fallback F8).
PROFILE_DIR = "anthropic-empty"
PROFILE_VARIABLE = "ANTHROPIC_CONFIG_DIR"
PROFILE_STORE = "anthropic"

# How the host marks what the account synced (recorded on 2.1.284).
SYNC_TAG = "(claude.ai sync)"
SYNCED_NAMESPACE = "anthropic-skills:"
CLAUDEAI_SOURCE = "claudeai"
BUILTIN_SUFFIX = "@builtin"
# Where the background sync writes inside a configuration directory.
SYNCED_DIRS = {"skills/synced": "synced skill", "plugins/synced": "synced plugin"}


@dataclass(frozen=True)
class SurfaceLeak:
    """One account surface: what kind it is and its name — never a value."""

    kind: str
    name: str


def ambient_env(environ: Mapping[str, str]) -> dict[str, str]:
    """The inherited environment less every billing variable, with the connector
    switch off. The ambient dev run and the audit pre-flight both start their
    child with it; `environ` is not modified."""
    env = {name: value for name, value in environ.items()
           if not name.startswith(BILLING_PREFIXES)}
    env.update(CONNECTORS_OFF)
    return env


def profile_dir(config: Path) -> Path:
    """The empty profile directory that belongs to an isolated configuration."""
    return config / PROFILE_DIR


# ---------- stream checks ------------------------------------------------------


def _system(event: Mapping, subtype: str) -> bool:
    return event.get("type") == "system" and event.get("subtype") == subtype


def _mcp_leaks(init: Mapping, isolated: bool) -> list[SurfaceLeak]:
    """Isolated runs configure no MCP server, so any one is foreign; an ambient
    run measures the operator's own servers and counts only claude.ai's."""
    leaks = []
    for server in init.get("mcp_servers") or []:
        entry = server if isinstance(server, Mapping) else {"name": str(server)}
        if isolated or entry.get("source") == CLAUDEAI_SOURCE:
            leaks.append(SurfaceLeak("MCP server", str(entry.get("name"))))
    return leaks


def _plugin_leaks(init: Mapping) -> list[SurfaceLeak]:
    leaks = []
    for plugin in init.get("plugins") or []:
        entry = plugin if isinstance(plugin, Mapping) else {"name": str(plugin)}
        source = str(entry.get("source") or entry.get("name"))
        if not source.endswith(BUILTIN_SUFFIX):
            leaks.append(SurfaceLeak("plugin", source))
    return leaks


def _namespaced(names: Iterable) -> list[SurfaceLeak]:
    return [SurfaceLeak("synced skill", name) for name in names
            if isinstance(name, str) and name.startswith(SYNCED_NAMESPACE)]


def _synced_command(command: Mapping) -> bool:
    names = [command.get("name"), *(command.get("aliases") or [])]
    return (SYNC_TAG in str(command.get("description") or "")
            or any(isinstance(n, str) and n.startswith(SYNCED_NAMESPACE) for n in names))


def _command_leaks(changed: Mapping) -> list[SurfaceLeak]:
    return [SurfaceLeak("synced skill", str(command.get("name")))
            for command in changed.get("commands") or []
            if isinstance(command, Mapping) and _synced_command(command)]


def _event_leaks(event: Mapping, isolated: bool) -> list[SurfaceLeak]:
    if _system(event, "init"):
        if not isolated:
            return _mcp_leaks(event, isolated=False)
        return [*_mcp_leaks(event, isolated=True), *_plugin_leaks(event),
                *_namespaced(event.get("skills") or []),
                *_namespaced(event.get("slash_commands") or [])]
    if isolated and _system(event, "commands_changed"):
        return _command_leaks(event)
    return []


def stream_surfaces(events: Iterable[Mapping], isolated: bool) -> list[SurfaceLeak]:
    """Every account surface a host stream shows, in order, each named once.

    Isolated: any MCP server, any plugin not built in, and any skill or
    command tagged as synced or named under the claude.ai skills namespace, in
    `init` or a later command-list change. Ambient: only a claude.ai-sourced
    MCP server — an ambient run measures the operator's configuration
    otherwise. Detection is by tag rather than against a list of the host's
    bundled skills, which changes on every host release."""
    leaks = [leak for event in events if isinstance(event, Mapping)
             for leak in _event_leaks(event, isolated)]
    return list(dict.fromkeys(leaks))


# ---------- configuration checks ------------------------------------------------


def config_surfaces(config: Path) -> list[SurfaceLeak]:
    """The synced skills and plugins a configuration directory holds, by their
    path inside it. A synced directory that exists but is empty is named too:
    with the opt-outs in force the sync never creates it."""
    leaks = []
    for rel, kind in SYNCED_DIRS.items():
        path = config / rel
        if not (path.exists() or path.is_symlink()):
            continue
        entries = sorted(p.name for p in path.iterdir()) if path.is_dir() else []
        leaks += [SurfaceLeak(kind, f"{rel}/{name}") for name in entries] or [
            SurfaceLeak(kind, rel)]
    return leaks


def _pinned_json() -> str:
    return json.dumps(dict(PINNED_SETTINGS), sort_keys=True)


def _settings_problem(config: Path) -> str | None:
    path = config / SETTINGS_FILE
    try:
        settings = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return f"{SETTINGS_FILE} is missing"
    except (OSError, ValueError):
        return f"{SETTINGS_FILE} is not readable JSON"
    # compared as JSON text, so `0` never passes for `false`
    if json.dumps(settings, sort_keys=True) != _pinned_json():
        return f"{SETTINGS_FILE} is not exactly {_pinned_json()}"
    return None


def _profile_problem(config: Path) -> str | None:
    path = profile_dir(config)
    if path.is_symlink() or not path.is_dir():
        return f"the empty profile directory {PROFILE_DIR}/ is missing"
    if any(path.iterdir()):
        return f"the profile directory {PROFILE_DIR}/ is not empty"
    return None


def isolation_problem(config: Path) -> str | None:
    """Why `config` may not host an isolated run, or None: settings that are
    not exactly the pinned opt-outs, a missing or non-empty profile directory,
    or synced content already present. Every problem is named at once; the
    profile directory's contents never are."""
    problems = [p for p in (_settings_problem(config), _profile_problem(config)) if p]
    leaks = config_surfaces(config)
    if leaks:
        problems.append("it already holds " + ", ".join(leak.name for leak in leaks))
    if not problems:
        return None
    return (f"the isolated configuration {config} is not closed to claude.ai account "
            f"surfaces: {'; '.join(problems)}. It must hold {SETTINGS_FILE} with exactly "
            f"{_pinned_json()}, an empty {PROFILE_DIR}/ directory and no synced skills or "
            "plugins; a directory passed through ROUTING_CONFIG_DIR is used as it is, so "
            "prepare it that way. The ambient configuration is never used instead.")


def default_profile_store(environ: Mapping[str, str]) -> Path:
    """The default Anthropic profile directory, as a host child started from
    `environ` would resolve it: `${XDG_CONFIG_HOME:-$HOME/.config}/anthropic`."""
    base = environ.get("XDG_CONFIG_HOME")
    if base:
        return Path(base) / PROFILE_STORE
    home = environ.get("HOME") or environ.get("USERPROFILE") or str(Path.home())
    return Path(home) / ".config" / PROFILE_STORE


def profile_store_problem(environ: Mapping[str, str]) -> str | None:
    """Why the default Anthropic profile directory bars an isolated run, or
    None (fallback F8). Whether the host reads its profiles from
    `ANTHROPIC_CONFIG_DIR` instead is unverified, so a profile there could
    become an isolated child's login: refuse while the directory holds any
    entry, or cannot be listed. Token mode (a long-lived token in `environ`)
    lifts the refusal, being the fallback's other remedy (close-claudeai-
    surfaces design Decision 7). The directory is named, never its contents."""
    if environ.get(LONG_LIVED_TOKEN):
        return None
    store = default_profile_store(environ)
    try:
        if not any(store.iterdir()):
            return None
    except (FileNotFoundError, NotADirectoryError):
        return None
    except OSError:
        pass  # not listable, so not known to be empty
    return (f"the default Anthropic profile directory {store} is not empty, and whether the "
            f"host ignores it when {PROFILE_VARIABLE} names the isolated configuration's "
            "empty one is unverified, so a profile there could become an isolated run's "
            "login. Move the profiles aside, or use token mode: run `claude setup-token` and "
            f"export {LONG_LIVED_TOKEN} in the shell that starts the harness, then rerun.")


def surface_reason(leaks: Iterable[SurfaceLeak], *, isolated: bool) -> str:
    """The one message for a run an account surface reached: each surface by
    kind and name, which opt-out did not hold, and the token-mode fallback.
    An isolated run had the pinned settings and the connector switch; an
    ambient run keeps the operator's own settings, so only the switch was its
    opt-out."""
    named = ", ".join(f"{leak.kind} {leak.name!r}" for leak in leaks)
    switch = ", ".join(f"{name}={value}" for name, value in CONNECTORS_OFF.items())
    failed = (f"The opt-outs did not hold (settings {_pinned_json()}, {switch})" if isolated
              else f"The connector switch did not hold ({switch})")
    return (f"claude.ai account surfaces reached the run: {named}. {failed}, so the run "
            f"measures nothing. Fallback: token mode — run `claude setup-token` and export "
            f"{LONG_LIVED_TOKEN} in the shell that starts the harness, then rerun.")
