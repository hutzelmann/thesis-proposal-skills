"""Dev runner: exercise a skill with the real Claude Code binary on the Max subscription.

Stages a fixture into a temp workspace, installs the skill under test into
`<ws>/.claude/skills/` (real skill discovery, closer to production than the
Inspect agent loop), runs headless `claude -p` with the user request, then
applies the same L1 verdicts as the authoritative evals (harness/l1_checks.py).

Dev loop only — not the source of record. No judge/L2 (use Inspect for that).

Usage:
  uv run python harness/claude_runner.py check_report [--model haiku]
  uv run python harness/claude_runner.py review_fixture --model sonnet
  uv run python harness/claude_runner.py write_from_seed

Note: runs claude with --dangerously-skip-permissions inside the temp
workspace so file edits and script calls work headlessly.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from l1_checks import verdict_check_report, verdict_draft, verdict_review

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parent
SKILLS = REPO / "skills"
FIXTURES = REPO / "tests" / "fixtures"
CHECK = SKILLS / "proposal-check" / "scripts" / "check.py"

SCENARIOS = {
    "check_report": {
        "fixture": "f15-format-broken",
        "skill": "proposal-check",
        "proposal": "broken-format.md",
        "request": "Please check my proposal broken-format.md.",
    },
    "review_fixture": {
        "fixture": "f05-slr-interviews",
        "skill": "proposal-review",
        "proposal": "microservice-technical-debt.md",
        "request": "Please review my proposal microservice-technical-debt.md — is it ready for my supervisor?",
    },
    "write_from_seed": {
        "fixture": "w01-ideate-seed",
        "skill": "proposal-write",
        "proposal": "data-drift-detection.md",
        "request": "Please turn my idea notes in data-drift-detection.md into a full proposal draft. Keep my idea, mark anything missing as TODO.",
    },
}


def stage(scenario: dict, ws: Path) -> None:
    fixture = FIXTURES / scenario["fixture"]
    for f in fixture.iterdir():
        if f.is_file() and f.suffix == ".md":
            shutil.copy(f, ws / f.name)
        if f.is_dir() and f.name == "img":
            shutil.copytree(f, ws / "img")
    skill_home = ws / ".claude" / "skills" / scenario["skill"]
    shutil.copytree(SKILLS / scenario["skill"], skill_home)
    # Sibling skills the scenario relies on (e.g. ideate's lit-search fallback).
    for sibling in scenario.get("siblings", ()):
        shutil.copytree(SKILLS / sibling, ws / ".claude" / "skills" / sibling)


def run_claude(ws: Path, request: str, model: str, timeout: int) -> str:
    result = subprocess.run(
        ["claude", "-p", request, "--model", model, "--dangerously-skip-permissions"],
        cwd=ws, capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        sys.exit(f"claude failed: {result.stderr.strip()[-800:]}")
    return result.stdout


def run_check(ws: Path, proposal: str) -> str:
    result = subprocess.run(
        [sys.executable, str(CHECK), str(ws / proposal)], capture_output=True, text=True
    )
    return result.stdout


def read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def verdict(name: str, scenario: dict, ws: Path, chat: str) -> tuple[bool, str]:
    fixture = FIXTURES / scenario["fixture"]
    original = (fixture / scenario["proposal"]).read_text(encoding="utf-8")
    current = read(ws / scenario["proposal"])
    if name == "check_report":
        return verdict_check_report(fixture / "expected.json", original, current, chat)
    if name == "review_fixture":
        review_name = scenario["proposal"].replace(".md", "-review.md")
        return verdict_review(original, current, read(ws / review_name), review_name)
    if name == "write_from_seed":
        return verdict_draft(current, run_check(ws, scenario["proposal"]) if current else "")
    raise ValueError(name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=sorted(SCENARIOS))
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--keep", action="store_true", help="keep the temp workspace")
    args = parser.parse_args()
    scenario = SCENARIOS[args.scenario]

    ws = Path(tempfile.mkdtemp(prefix=f"devrun-{args.scenario}-"))
    try:
        stage(scenario, ws)
        chat = run_claude(ws, scenario["request"], args.model, args.timeout)
        passed, why = verdict(args.scenario, scenario, ws, chat)
        print(json.dumps({
            "scenario": args.scenario, "model": args.model,
            "l1": "PASS" if passed else "FAIL", "why": why,
        }, indent=2))
        print("\n--- chat tail ---\n" + chat[-1200:])
        return 0 if passed else 1
    finally:
        if args.keep:
            print(f"\nworkspace kept: {ws}")
        else:
            shutil.rmtree(ws, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
