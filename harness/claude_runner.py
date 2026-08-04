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
  uv run python harness/claude_runner.py import_messy
  uv run python harness/claude_runner.py ideate_scoped

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
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from l1_checks import (
    select_draft,
    verdict_check_report,
    verdict_draft,
    verdict_ideate_scoped,
    verdict_import,
    verdict_review,
)
from sources import MESSY_REQUEST

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
    # no fixture: the source arrives pasted in the request and the skill
    # creates the proposal, choosing its own content-derived filename
    "import_messy": {
        "skill": "proposal-import",
        "request": MESSY_REQUEST,
        "produces": True,
    },
    # nothing staged: the group page is served over localhost ({url} filled at
    # runtime) and the single-turn request pre-answers the scoping preamble,
    # declining the guidelines.md note so the run needs no second turn
    "ideate_scoped": {
        "skill": "proposal-ideate",
        "serve": "g01-research-group",
        "produces": True,
        # the closing sentences are the session-termination cue: without them
        # the model ends turn one mid-Socratic-dialogue and never seeds (the
        # skill seeds "before the session ends", and a one-shot run has no
        # second turn to end on)
        "request": (
            "I want to develop a thesis idea. I'm in the M.Sc. Embedded Systems "
            "Engineering program at Musterstadt University. The research group I "
            "hope will supervise me has its page at {url} — please take a look at "
            "what they do. My rough idea: energy-efficient scheduling of "
            "containerized workloads on edge devices. This message is our whole "
            "session — I cannot reply again, so develop the idea as far as you "
            "can without asking me anything, then treat this as me saying "
            "'enough' and create the seed proposal file now. My thesis starts in "
            "April 2027 and is due in September 2027. Don't keep any scoping "
            "notes for later sessions."
        ),
    },
}


class QuietHandler(SimpleHTTPRequestHandler):
    """Serve the fixture page without request logging on stderr."""

    def log_message(self, *_args) -> None:
        pass


def stage(scenario: dict, ws: Path) -> None:
    if scenario.get("fixture"):
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
        # stdin must be closed: with an inherited non-tty stdin (backgrounded or
        # redirected runs) claude blocks waiting for piped input, warns, and can
        # exit non-zero — a runner failure that looks like a skill failure
        cwd=ws, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=timeout,
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


def workspace_markdown(ws: Path) -> dict[str, str]:
    return {f.name: f.read_text(encoding="utf-8") for f in sorted(ws.glob("*.md"))}


def verdict(name: str, scenario: dict, ws: Path, chat: str) -> tuple[bool, str]:
    if name == "ideate_scoped":
        files = workspace_markdown(ws)
        produced, where = select_draft(files)
        if not produced:
            return False, where
        passed, why = verdict_ideate_scoped(files, produced, chat)
        return passed, f"{why} ({where})"
    if scenario.get("produces"):
        produced, _ = select_draft(workspace_markdown(ws))
        if not produced:
            return verdict_import(None)
        return verdict_import(read(ws / produced), run_check(ws, produced), produced)
    fixture = FIXTURES / scenario["fixture"]
    original = (fixture / scenario["proposal"]).read_text(encoding="utf-8")
    current = read(ws / scenario["proposal"])
    if name == "check_report":
        return verdict_check_report(fixture / "expected.json", original, current, chat)
    if name == "review_fixture":
        review_name = scenario["proposal"].replace(".md", "-review.md")
        return verdict_review(original, current, read(ws / review_name), review_name)
    if name == "write_from_seed":
        # the skill may draft into a fresh <slug>.md instead of the seed
        chosen, where = select_draft(workspace_markdown(ws), scenario["proposal"], original)
        if not chosen:
            return False, where
        passed, why = verdict_draft(read(ws / chosen), run_check(ws, chosen))
        return passed, f"{why} ({where})"
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
    server = None
    try:
        stage(scenario, ws)
        request = scenario["request"]
        if scenario.get("serve"):
            handler = partial(QuietHandler, directory=str(FIXTURES / scenario["serve"]))
            server = HTTPServer(("127.0.0.1", 0), handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            request = request.format(url=f"http://127.0.0.1:{server.server_port}/group.html")
        chat = run_claude(ws, request, args.model, args.timeout)
        passed, why = verdict(args.scenario, scenario, ws, chat)
        print(json.dumps({
            "scenario": args.scenario, "model": args.model,
            "l1": "PASS" if passed else "FAIL", "why": why,
        }, indent=2))
        print("\n--- chat tail ---\n" + chat[-1200:])
        return 0 if passed else 1
    finally:
        if server:
            server.shutdown()
        if args.keep:
            print(f"\nworkspace kept: {ws}")
        else:
            shutil.rmtree(ws, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
