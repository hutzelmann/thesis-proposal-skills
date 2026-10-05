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
monkeypatch of `run_claude`, `isolated_config`, `follow_stream` and
`claude_cli.call`/`preflight` keeps working. This module holds only the
shapes; it imports nothing but `host_login`, so `codex_cli` may use it
without an import cycle.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path

from host_login import HostLogin


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
    """The CLI that grades dev runs (`host`), its call and login check, and
    the isolation it enters for a run whose own configuration it cannot reuse."""

    host: str
    call: Callable
    preflight: Callable
    isolation: Callable[[ExitStack], Path]


@dataclass(frozen=True)
class Host:
    """One host CLI behind the dev runner.

    `skill_dir` is where Codex or Claude Code discovers repository skills in
    the workspace; `run(ws, request, args, config)` returns the saved event
    list or raises the runner's failure; `isolation(stack, args)` prepares
    what the run executes in (None for an ambient Claude run); `label(config,
    isolated)` names the login a run used. `always_isolated` marks a host with
    no ambient mode."""

    name: str
    binary: str
    skill_dir: tuple[str, str]
    run: Callable[..., list[dict]]
    read: Callable[[list[dict], argparse.Namespace], RunView]
    isolation: Callable[[ExitStack, argparse.Namespace], Path | None]
    login: HostLogin
    label: Callable[[Path | None, bool], dict]
    always_isolated: bool = False

    @property
    def run_label(self) -> str:
        """The label every summary of this host carries."""
        return f"dev-runner ({self.name}), not comparable to matrix"
