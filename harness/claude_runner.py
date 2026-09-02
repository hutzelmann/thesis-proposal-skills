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
  uv run python harness/claude_runner.py ideate_scoped --model sonnet
  uv run python harness/claude_runner.py review_fixture --isolated --max-budget-usd 2

Every run reads the host's stream-json events and prints, beside the L1
verdict, the run's cost, turns, duration, token counts, any helper-agent
tool calls (Agent/Task/Workflow) and an advisory single-context verdict —
the probe for the fan-out class of failure, which no other harness path can
see. `--isolated` runs against a fresh host configuration (the routing rig's
`prepare_config`), so a run measures the default host rather than the
operator's session mode; the summary says which (`config`).

Note: runs claude with --dangerously-skip-permissions inside the temp
workspace so file edits and script calls work headlessly.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from l1_checks import (
    HELPER_TOOLS,
    load_closing_note,
    select_draft,
    verdict_check_report,
    verdict_draft,
    verdict_hollow_review,
    verdict_ideate_scoped,
    verdict_import,
    verdict_review,
    verdict_single_context,
    verdict_supervise_feedback_contract,
)
from routing import prepare_config, tool_calls
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
        "request": "Please review my proposal microservice-technical-debt.md — "
                   "is it ready for my supervisor?",
    },
    # check-clean but hollow: the run passes only on the no-viable-core verdict,
    # judged by the pure L1 function alone — no model-graded scorer on this path
    "review_hollow": {
        "fixture": "f22-hollow-generic",
        "skill": "proposal-review",
        "proposal": "software-quality-ml.md",
        "request": "Please review my proposal software-quality-ml.md — "
                   "is it ready for my supervisor?",
    },
    "write_from_seed": {
        "fixture": "w01-ideate-seed",
        "skill": "proposal-write",
        "proposal": "data-drift-detection.md",
        "request": "Please turn my idea notes in data-drift-detection.md into a full "
                   "proposal draft. Keep my idea, mark anything missing as TODO.",
    },
    # no fixture: the source arrives pasted in the request and the skill
    # creates the proposal, choosing its own content-derived filename
    "import_messy": {
        "skill": "proposal-import",
        "request": MESSY_REQUEST,
        "produces": True,
    },
    # supervisor-side: raw email fixture (.txt) to paste-ready feedback; import
    # is installed as a sibling, matching a professor's whole-set install
    "supervise_feedback": {
        "fixture": "s01-raw-email",
        "skill": "proposal-supervise",
        "siblings": ("proposal-import",),
        "feedback": True,
        # the closing sentence pre-answers the borderline deferral: a headless
        # single-turn run has no professor to ask, so it exercises the
        # needs-revision default instead of stalling
        "request": "A student emailed me this thesis idea — I saved it as "
                   "submission-email.txt. Prepare my feedback: the draft "
                   "I can send back. If the verdict turns out "
                   "borderline, do not ask me — take the needs-revision path.",
    },
    # nothing staged: the group page and a canned DBLP-shaped publication list
    # are served over localhost ({url}/{dblp} filled at runtime) and the
    # single-turn request pre-answers the whole administrative preamble,
    # declining the guidelines.md note so the run needs no second turn
    "ideate_scoped": {
        "skill": "proposal-ideate",
        "serve": "g01-research-group",
        "produces": True,
        # the closing sentences are the session-termination cue: without them
        # the model ends turn one mid-Socratic-dialogue and never seeds (the
        # skill seeds at convergence or on "enough", and a one-shot run has no
        # second turn to converge in)
        "request": (
            "I want to develop a thesis idea. To answer your usual questions up "
            "front: I'm in the M.Sc. Embedded Systems Engineering program at "
            "Musterstadt University, it's a Master's thesis, the proposal should "
            "be in English, I have about five months (April 2027 to September "
            "2027), and yes, you may look things up online. The research group I "
            "hope will supervise me has its page at {url} — please take a look "
            "at what they do; a saved export of their recent publication list is "
            "at {dblp}. My rough idea: energy-efficient scheduling of "
            "containerized workloads on edge devices. This message is our whole "
            "session — I cannot reply again, so develop the idea as far as you "
            "can without asking me anything, then treat this as me saying "
            "'enough' and create the seed proposal file now. Don't keep any "
            "scoping notes for later sessions."
        ),
    },
}


class QuietHandler(SimpleHTTPRequestHandler):
    """Serve the fixture page without request logging on stderr."""

    def log_message(self, *_args) -> None:
        pass


def stage(scenario: dict, ws: Path, install_skill: bool = True) -> None:
    if scenario.get("fixture"):
        fixture = FIXTURES / scenario["fixture"]
        for f in fixture.iterdir():
            # .txt: raw-submission fixtures (s prefix) ship the source as text
            if f.is_file() and f.suffix in (".md", ".txt"):
                shutil.copy(f, ws / f.name)
            if f.is_dir() and f.name == "img":
                shutil.copytree(f, ws / "img")
    if not install_skill:  # baseline arm: same workspace, no skill discovered
        return
    # evals/ stays out: a model that can read its own eval assertions is not
    # being measured (testing-harness spec: Measured environments carry no
    # eval definitions). User installs legitimately carry it; measured ones not.
    no_evals = shutil.ignore_patterns("evals")
    skill_home = ws / ".claude" / "skills" / scenario["skill"]
    shutil.copytree(SKILLS / scenario["skill"], skill_home, ignore=no_evals)
    # Sibling skills the scenario relies on (e.g. ideate's lit-search fallback).
    for sibling in scenario.get("siblings", ()):
        shutil.copytree(SKILLS / sibling, ws / ".claude" / "skills" / sibling,
                        ignore=no_evals)


def run_claude(ws: Path, request: str, model: str, timeout: int,
               budget: float | None = None, config: Path | None = None) -> list[dict]:
    """Run the host headless and return its stream-json events.

    The stream, not the plain text, is what a run is judged on: the final
    `result` event carries the chat text plus cost, turns and token usage, and
    the assistant events carry every tool call — including a helper-agent
    spawn, which plain text output never shows.
    """
    command = [
        "claude", "-p", request, "--model", model, "--dangerously-skip-permissions",
        "--output-format", "stream-json", "--verbose",
    ]
    if budget is not None:
        command += ["--max-budget-usd", str(budget)]
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config)) if config else None
    result = subprocess.run(
        command,
        # stdin must be closed: with an inherited non-tty stdin (backgrounded or
        # redirected runs) claude blocks waiting for piped input, warns, and can
        # exit non-zero — a runner failure that looks like a skill failure
        cwd=ws, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        sys.exit(f"claude failed: {result.stderr.strip()[-800:]}")
    return parse_events(result.stdout)


def parse_events(stdout: str) -> list[dict]:
    """One JSON object per non-empty line; lines that are not JSON are skipped."""
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def result_event(events: list[dict]) -> dict:
    return next((e for e in reversed(events) if e.get("type") == "result"), {})


def final_text(events: list[dict]) -> str:
    """The chat the verdicts read: the result event's text, else the assistant turns joined."""
    text = result_event(events).get("result")
    if isinstance(text, str) and text:
        return text
    parts = []
    for event in events:
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
    return "\n".join(parts)


def telemetry(events: list[dict]) -> dict:
    """Cost, turns, duration and tokens from the result event; None where absent.

    `tokens_in` is the uncached input only; the bulk of a run's input is the
    cache pair, and the 2026-09-02 fan-out was a cache-write story (~45K per
    helper), so both cache counts travel too.
    """
    result = result_event(events)
    usage = result.get("usage") or {}
    return {
        "cost_usd": result.get("total_cost_usd"),
        "num_turns": result.get("num_turns"),
        "duration_ms": result.get("duration_ms"),
        "tokens_in": usage.get("input_tokens"),
        "tokens_out": usage.get("output_tokens"),
        "tokens_cache_read": usage.get("cache_read_input_tokens"),
        "tokens_cache_write": usage.get("cache_creation_input_tokens"),
    }


def summary(args: argparse.Namespace, passed: bool, why: str, events: list[dict],
            config: Path | None) -> dict:
    """The run's L1 verdict plus the probe: telemetry and the advisory
    single-context verdict, which never changes the exit status."""
    names = [name for name, _ in tool_calls(events)]
    single, single_why = verdict_single_context(names)
    return {
        "scenario": args.scenario, "model": args.model,
        "arm": "baseline" if args.no_skill else "with-skill",
        "l1": "PASS" if passed else "FAIL", "why": why,
        "config": "isolated" if config else "ambient",
        **telemetry(events),
        "helper_calls": [name for name in names if name in HELPER_TOOLS],
        "single_context": f"{'PASS' if single else 'FAIL'}: {single_why}",
    }


def run_check(ws: Path, proposal: str) -> str:
    result = subprocess.run(
        [sys.executable, str(CHECK), str(ws / proposal)], capture_output=True, text=True
    )
    return result.stdout


def read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def workspace_markdown(ws: Path) -> dict[str, str]:
    return {f.name: f.read_text(encoding="utf-8") for f in sorted(ws.glob("*.md"))}


S01_FORBIDDEN = ("Musterfrau", "00000000", "erika.musterfrau@example.org", "Musterstraße")
# the fixture email is written in English, so the feedback — and its closing
# note — must be too
S01_LANGUAGE = "English"
INSTALLED_SKILLS = tuple(sorted(
    d.name for d in SKILLS.iterdir() if d.is_dir() and d.name.startswith("proposal-")
))


def feedback_files(ws: Path) -> dict[str, str]:
    return {
        f.name: f.read_text(encoding="utf-8")
        for f in sorted(ws.glob("*-feedback.md")) if f.is_file()
    }


def verdict(name: str, scenario: dict, ws: Path, chat: str) -> tuple[bool, str]:
    if scenario.get("feedback"):
        return verdict_supervise_feedback_contract(
            feedback_files(ws), S01_FORBIDDEN, INSTALLED_SKILLS,
            load_closing_note(SKILLS), S01_LANGUAGE)
    if name == "ideate_scoped":
        files = workspace_markdown(ws)
        produced, where = select_draft(files)
        if not produced:
            return False, where
        # the request explicitly declines the scoping note, so a guidelines.md
        # existing at all fails the run
        passed, why = verdict_ideate_scoped(files, produced, chat, note_declined=True)
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
    if name == "review_hollow":
        review_name = scenario["proposal"].replace(".md", "-review.md")
        return verdict_hollow_review(original, current, read(ws / review_name), review_name)
    if name == "write_from_seed":
        # the skill may draft into a fresh <slug>.md instead of the seed
        chosen, where = select_draft(workspace_markdown(ws), scenario["proposal"], original)
        if not chosen:
            return False, where
        passed, why = verdict_draft(read(ws / chosen), run_check(ws, chosen))
        return passed, f"{why} ({where})"
    raise ValueError(name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=sorted(SCENARIOS))
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--keep", action="store_true", help="keep the temp workspace")
    parser.add_argument("--no-skill", action="store_true",
                        help="baseline arm: same staging and request, skill not installed")
    parser.add_argument("--max-budget-usd", type=float, default=None,
                        help="hard cost cap passed through to the host")
    parser.add_argument("--isolated", action="store_true",
                        help="run against a fresh host configuration (settings emptied, "
                             "credentials linked) instead of the operator's ambient one")
    args = parser.parse_args(argv)
    scenario = SCENARIOS[args.scenario]

    ws = Path(tempfile.mkdtemp(prefix=f"devrun-{args.scenario}-"))
    # the isolated config lives outside the workspace: it links the credentials
    # file, and the agent under test must never be able to read that
    config_base = Path(tempfile.mkdtemp(prefix="devrun-config-")) if args.isolated else None
    config = prepare_config(config_base) if config_base else None
    server = None
    try:
        stage(scenario, ws, install_skill=not args.no_skill)
        request = scenario["request"]
        if scenario.get("serve"):
            handler = partial(QuietHandler, directory=str(FIXTURES / scenario["serve"]))
            server = HTTPServer(("127.0.0.1", 0), handler)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            base = f"http://127.0.0.1:{server.server_port}"
            request = request.format(url=f"{base}/group.html", dblp=f"{base}/dblp.json")
        events = run_claude(ws, request, args.model, args.timeout,
                            budget=args.max_budget_usd, config=config)
        chat = final_text(events)
        passed, why = verdict(args.scenario, scenario, ws, chat)
        print(json.dumps(summary(args, passed, why, events, config), indent=2))
        print("\n--- chat tail ---\n" + chat[-1200:])
        return 0 if passed else 1
    finally:
        if server:
            server.shutdown()
        if config_base:
            shutil.rmtree(config_base, ignore_errors=True)
        if args.keep:
            print(f"\nworkspace kept: {ws}")
        else:
            shutil.rmtree(ws, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
