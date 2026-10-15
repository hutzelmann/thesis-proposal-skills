"""L0: every runner checks a staged workspace from its root (testing-harness:
Check run from the staged workspace's root).

A user's agent runs the check from the workspace root, with the proposal's path
relative to it; the workspace's `guidelines.md` is found from there, and in the
folder layout the placement and orphan findings are measured from there too
(adopt-proposal-folders, design D17). A runner that starts the check anywhere
else grades a report the user never sees.
"""

from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace

import claude_runner
import pytest
import skill_evals
from fixture_paths import fixture_dir, fixture_proposal
from helpers import CLEAN_DRAFT, write_proposal

GUIDELINES = "```toml\n[references]\nmin_count = 99\n```\n"


def folder_workspace(ws) -> str:
    """A proposal in its folder and the workspace's guidelines.md at the root;
    the proposal's path relative to the root."""
    proposal = write_proposal(ws, "ml-code-review", CLEAN_DRAFT)
    (ws / "guidelines.md").write_text(GUIDELINES, encoding="utf-8")
    return proposal.relative_to(ws).as_posix()


def test_the_dev_runners_check_reads_the_workspace_guidelines(tmp_path):
    assert "at least 99 required" in claude_runner.run_check(tmp_path, folder_workspace(tmp_path))


def test_the_dev_runners_structured_check_reads_the_workspace_guidelines(tmp_path):
    findings = claude_runner.run_check_json(tmp_path, folder_workspace(tmp_path))
    assert any("at least 99 required" in f["message"] for f in findings), findings


def test_the_dev_runner_starts_the_check_in_the_workspace(tmp_path, monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs.get("cwd")))
        return SimpleNamespace(stdout='{"findings": []}', stderr="", returncode=0)

    monkeypatch.setattr(claude_runner.subprocess, "run", fake_run)
    claude_runner.run_check(tmp_path, "a/a.md")
    claude_runner.run_check_json(tmp_path, "a/a.md")
    check = [sys.executable, str(claude_runner.CHECK), "a/a.md"]
    assert calls == [(check, tmp_path), ([*check, "--json"], tmp_path)]


def test_the_sandbox_check_runs_in_the_workspace(monkeypatch):
    """The sandbox's root is the workspace root and the agent's working
    directory, so the scorer's check runs there as the agent's own does, with
    no working directory of its own, through the task skill's installed copy."""
    calls = []

    class Sandbox:
        async def exec(self, cmd, timeout=None, cwd=None):
            calls.append((cmd, cwd, timeout))
            return SimpleNamespace(stdout="report", stderr="", returncode=0, success=True)

    monkeypatch.setattr(skill_evals, "sandbox", lambda *_args, **_kwargs: Sandbox())
    assert asyncio.run(skill_evals.run_check("a/a.md", "proposal-write")) == "report"
    script = f"{skill_evals.SKILL_HOME}/proposal-write/scripts/check.py"
    assert calls == [(["python3", script, "a/a.md"], None, 60)]


@pytest.mark.parametrize("name", [name for name, scenario in claude_runner.SCENARIOS.items()
                                  if scenario.get("fixture") and scenario.get("proposal")])
def test_a_scenarios_proposal_is_its_fixtures_proposal(name):
    """The verdicts read the fixture's original through the fixture-path
    helper and the run's result at the scenario's `proposal`; both name the
    same file, at the same place relative to the workspace root."""
    scenario = claude_runner.SCENARIOS[name]
    proposal = fixture_proposal(scenario["fixture"])
    assert proposal.relative_to(fixture_dir(scenario["fixture"])).as_posix() == scenario["proposal"]
