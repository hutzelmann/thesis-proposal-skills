"""L0: measured environments carry no eval definitions (testing-harness spec).

The skills ship `evals/evals.json` for the standard's sake; a runner that
installs it hands the model under test its own assertions. These tests call
the real staging functions and assert the projections stay behind."""

from __future__ import annotations

import claude_runner
import routing


def _no_evals_installed(root):
    homes = sorted(p for p in root.rglob("SKILL.md"))
    assert homes, "staging installed no skill at all"
    leaked = sorted(p for p in root.rglob("evals"))
    assert not leaked, f"eval definitions staged into a measured environment: {leaked}"


def test_dev_runner_stages_skills_without_eval_definitions(tmp_path):
    scenario = claude_runner.SCENARIOS["check_report"]
    claude_runner.stage(scenario, tmp_path)
    _no_evals_installed(tmp_path / ".claude" / "skills")
    installed = tmp_path / ".claude" / "skills" / scenario["skill"]
    assert (installed / "SKILL.md").is_file()
    assert (installed / "scripts").is_dir(), "scripts must still travel"


def test_routing_rig_installs_the_set_without_eval_definitions(tmp_path):
    routing.install_skills(tmp_path)
    _no_evals_installed(tmp_path)
    assert len(sorted(tmp_path.iterdir())) == len(routing.installed_skills())
