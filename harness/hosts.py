"""The dev runner's host seam: one runner, one adapter per host CLI.

The dev runner (`claude_runner.py`) shares one core across its hosts — the
scenario set and the workspace staging, the L1 verdicts, the summary and its
exit statuses, the saved event stream, the re-grading of kept workspaces and
the judge machinery. Five parts differ per host, and each sits behind a field
of `Host`: its command and run (`run`), its stream readers (`read`, which
returns a `RunView`), its isolation (`isolation`) and its login (`login`)
(testing-harness spec: Dev-runner host adapters). The judge has an isolation
of its own (`JudgeBackend`): the Claude dev judge grades every host's runs in
a fresh isolated Claude configuration, never in another host's login home.

The `Host` objects are built in `claude_runner.HOSTS`, where the Claude
callables live, as lambdas over the module attributes, so that every existing
monkeypatch of `run_claude`, `isolated_config` and `follow_stream` keeps
working; a host's binary is its login record's (`login.binary`). Three hosts
sit behind the seam: Claude Code (the default), Codex (`codex_cli`) and the
GitHub Copilot CLI (`copilot_cli`). Codex and Copilot stage skills under
`<ws>/.agents/skills`, run only in their harness homes (`always_isolated`), and
share one notion of a scenario that needs the network (`needs_network`), so
both hosts grant it to the same scenarios. This module holds only the shapes
and that predicate; it imports nothing but `host_login`, so `codex_cli` and
`copilot_cli` may use it without an import cycle.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path

from host_login import HostLogin

# The skills whose scripts contact the network (add-codex-dev-runner D4(a)):
# a scenario that stages one of them, or serves a fixture over localhost,
# needs the network on every host that can withhold it.
NETWORK_SKILLS = frozenset({"proposal-import", "proposal-lit-search", "proposal-reverse"})


def needs_network(scenario: Mapping) -> bool:
    """A scenario that serves a fixture over localhost, or whose skill or
    siblings include import, literature search or reverse."""
    skills = {scenario.get("skill"), *scenario.get("siblings", ())}
    return bool(scenario.get("serve")) or bool(skills & NETWORK_SKILLS)


@dataclass(frozen=True)
class RunView:
    """What the shared core reads from a host's saved event list: the chat the
    verdicts read, the requested and the served model, the host CLI version
    and the telemetry the summary prints. `model_check` notes a discrepancy
    the reader found in the served model."""

    final_text: str
    model_requested: str | None
    model: str | None
    cli_version: str | None
    telemetry: dict = field(default_factory=dict)
    model_check: str | None = None


@dataclass(frozen=True)
class JudgeBackend:
    """The CLI that grades dev runs (`host`) and the isolation it enters for a
    run whose own configuration it cannot reuse. Its calls and its login check
    are `claude_cli.judge_all`'s, reached through `claude_runner.run_judge`."""

    host: str
    isolation: Callable[[ExitStack], Path]


@dataclass(frozen=True)
class Host:
    """One host CLI behind the dev runner.

    `skill_dir` is where Codex or Claude Code discovers repository skills in
    the workspace; `run(ws, request, args, config)` returns the saved event
    list or raises the runner's failure; `isolation(stack, args)` prepares
    what the run executes in (None for an ambient Claude run); `label(config,
    isolated)` names the login a run used. `always_isolated` marks a host with
    no ambient mode. `workspace_root()` names the directory the run's
    temporary workspace is made in, where the host needs one of its own
    (Copilot: its work directory, never the system temporary directory, which
    its sandbox denies); None makes it in the system temporary directory."""

    name: str
    skill_dir: tuple[str, str]
    run: Callable[..., list[dict]]
    read: Callable[[list[dict], argparse.Namespace], RunView]
    isolation: Callable[[ExitStack, argparse.Namespace], Path | None]
    login: HostLogin
    label: Callable[[Path | None, bool], dict]
    always_isolated: bool = False
    workspace_root: Callable[[], Path] | None = None

    @property
    def run_label(self) -> str:
        """The label every summary of this host carries."""
        return f"dev-runner ({self.name}), not comparable to matrix"
