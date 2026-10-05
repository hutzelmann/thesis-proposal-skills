"""Dev runner: exercise a skill with the real Claude Code binary on the Max subscription.

Stages a fixture into a temp workspace, installs the skill under test into
`<ws>/.claude/skills/` (real skill discovery, closer to production than the
Inspect agent loop), runs headless `claude -p` with the user request, then
applies the same L1 verdicts as the authoritative evals (harness/l1_checks.py).

Dev loop only — not the source of record. `--judge` adds dev-runner L2: the
scenarios with a rubric twin are graded by the subscription judge
(`[roles].dev_judge` in harness/models.toml, at its pinned effort) against the
same rubric templates and criteria as the matrix (harness/l2_rubrics.py). Its
grades are labelled "dev-runner L2, not comparable to matrix", are never written
where the support report reads, and never stand in for a matrix cell.

Usage:
  uv run python harness/claude_runner.py check_report [--model haiku]
  uv run python harness/claude_runner.py review_fixture --model sonnet
  uv run python harness/claude_runner.py write_from_seed
  uv run python harness/claude_runner.py import_messy
  uv run python harness/claude_runner.py customize_override
  uv run python harness/claude_runner.py ideate_scoped --model sonnet
  uv run python harness/claude_runner.py ideate_scoped_adjacent --model sonnet
  uv run python harness/claude_runner.py write_offtopic_reference --model sonnet
  uv run python harness/claude_runner.py install_prompt --model sonnet
  uv run python harness/claude_runner.py install_prompt_answered --model sonnet
  uv run python harness/claude_runner.py review_fixture --isolated --max-budget-usd 2
  uv run python harness/claude_runner.py write_from_seed --isolated --judge --keep
  uv run python harness/claude_runner.py write_from_seed --rejudge /tmp/devrun-write_from_seed-x
  uv run python harness/claude_runner.py write_rich_seed --isolated --judge --max-notional 1
  uv run python harness/claude_runner.py --summarize logs/devrun/smoke.jsonl \
      --expect write_from_seed import_messy customize_override

Every run reads the host's stream-json events and prints, beside the L1
verdict, the run's cost, turns, duration, token counts, any helper-agent
tool calls (Agent/Task/Workflow) and an advisory single-context verdict —
the probe for the fan-out class of failure, which no other harness path can
see — plus the model the host served and its CLI version. `--isolated` runs
against a fresh host configuration (the routing rig's `isolated_config`, which
keeps the linked stored login current), so a run measures the default host
rather than the operator's session mode; the summary says which (`config`).

Billing stays on the subscription: every `ANTHROPIC_*` variable and every
`CLAUDE_CODE_USE_*` switch is stripped from the model run's environment, and a
run whose stream shows an API-key source, overage, a refused rate-limit status
or no rate-limit report at all is untested, never passed. `--rejudge` re-grades
kept workspaces without running the model again; `--max-notional` caps the
judge calls' cumulative notional cost (plan quota, not money).

Exit status: 0 every computed verdict passed, 1 a verdict failed (L1 or a
graded L2 criterion), 2 usage error, 3 untested (the subscription could not
serve the run or the judge), 4 other runner failure.

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
import traceback
import zipfile
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import anyio
import claude_cli
import support
from claude_cli import Criterion, Grade, JudgeRun, parse_events
from host_login import LOGIN_FAILURE, login_remedy
from l1_checks import (
    HELPER_TOOLS,
    NOTES_SUFFIX,
    feedback_body_words,
    load_closing_note,
    select_draft,
    verdict_check_report,
    verdict_cited_draft,
    verdict_customize_override,
    verdict_draft,
    verdict_hollow_review,
    verdict_ideate_scoped,
    verdict_import,
    verdict_install_prompt_asks_scope,
    verdict_install_prompt_installed,
    verdict_l2_grades,
    verdict_offtopic_reference,
    verdict_repaired_draft,
    verdict_review,
    verdict_scoping_containment,
    verdict_seed,
    verdict_single_context,
    verdict_supervise_feedback_contract,
    verdict_supervise_review_sections,
    verdict_supervise_scope_options,
    verdict_supervise_verification_declared,
    verdict_supervise_verifier,
)
from l2_rubrics import CRITERIA, DEV_RUBRICS, JUDGE_SYSTEM, judge_prompt, question_for
from routing import (
    OUTWARD_TOOLS,
    error_result_reason,
    isolated_config,
    result_event,
    tool_calls,
)
from sources import MESSY_REQUEST

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parent
SKILLS = REPO / "skills"
FIXTURES = REPO / "tests" / "fixtures"
CHECK = SKILLS / "proposal-check" / "scripts" / "check.py"
REGISTRY = HARNESS / "models.toml"

# exit statuses (design D7): only a failed verdict reads as a failure of the skill
EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_UNTESTED, EXIT_RUNNER = 0, 1, 2, 3, 4
OUTCOMES = {EXIT_PASS: "PASS", EXIT_FAIL: "FAIL", EXIT_UNTESTED: "UNTESTED",
            EXIT_RUNNER: "RUNNER FAILURE"}
JUDGE_LABEL = "dev-runner L2, not comparable to matrix"
DEFAULT_MAX_NOTIONAL = 5.00
# every model run drops these: they can route the host's billing away from the
# subscription login (API key, gateway base URL and token, cloud providers)
BILLING_PREFIXES = ("ANTHROPIC_", "CLAUDE_CODE_USE_")

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
    # the core set's third task: the Inspect request verbatim; the verdict reads
    # the untouched proposal and the guidelines.md the skill writes beside it
    "customize_override": {
        "fixture": "f00-clean-en",
        "skill": "proposal-customize",
        "proposal": "ml-code-review.md",
        "request": "My supervisor requires a detailed work plan with milestones in the "
                   "proposal, not just a one-line timeline, and at least 8 references. "
                   "Please adjust the rules for this workspace.",
    },
    # supervisor-side: raw email fixture (.txt) to paste-ready feedback; import
    # is installed as a sibling, matching a professor's whole-set install
    "supervise_feedback": {
        "fixture": "s01-raw-email",
        "skill": "proposal-supervise",
        "siblings": ("proposal-import",),
        "feedback": True,
        # the skill's one fresh verifier of the finished feedback; the probe
        # flags anything beyond it (skill-supervise spec: single-context execution)
        "helpers": 1,
        # the closing sentences pre-answer both interactive stops — the
        # borderline deferral and the lookup approval (claim checks and
        # literature alike): a headless single-turn run has no professor to
        # ask, so it exercises the needs-revision default and the offline
        # path instead of stalling
        "request": "A student emailed me this thesis idea — I saved it as "
                   "submission-email.txt. Prepare my feedback: the draft "
                   "I can send back. If the verdict turns out "
                   "borderline, do not ask me — take the needs-revision path. "
                   "Do not make any network lookups — no claim checks and no "
                   "literature — and I cannot answer any further question.",
    },
    # the network path of the same scenario: lit-search staged as a sibling and
    # the approval granted in the request, so the run asks nothing and — the
    # fixture's bibliography being two blog posts — has a finding to ground.
    # Live scholarly APIs: expect variance, read the woven papers by hand.
    "supervise_literature": {
        "fixture": "s01-raw-email",
        "skill": "proposal-supervise",
        "siblings": ("proposal-import", "proposal-lit-search"),
        "feedback": True,
        "helpers": 1,
        "request": "A student emailed me this thesis idea — I saved it as "
                   "submission-email.txt. Prepare my feedback: the draft "
                   "I can send back. If the verdict turns out "
                   "borderline, do not ask me — take the needs-revision path. "
                   "Yes, you may look up literature: read-only queries through "
                   "proposal-lit-search are fine, and I cannot answer any "
                   "further question.",
    },
    # the over-scoped export: chained packages, an uncounted catalogue, a phase
    # table and chapter outline as format bait, a wrong regulation claim and a
    # paper cited against its own abstract. The lookups are granted so the claim
    # checks can run; whether the planted claims were caught is read by hand.
    "supervise_scope": {
        "fixture": "s02-overscoped-export",
        "skill": "proposal-supervise",
        "siblings": ("proposal-import", "proposal-lit-search"),
        "feedback": True,
        "scope": True,
        "helpers": 1,
        "forbidden": ("Musterfrau", "00000000", "erika.musterfrau@example.org",
                      "Musterstraße", "Mustermann"),
        "request": "A student uploaded this revised exposé for a Bachelor's thesis — I "
                   "saved it as submission-export.txt. Prepare my feedback: the draft "
                   "I can send back. If the verdict turns out borderline, do not ask "
                   "me — take the needs-revision path. Yes, you may run read-only "
                   "lookups to check claims and find literature, and I cannot answer "
                   "any further question.",
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
    # the containment pair. `ideate_scoped` above shares its fixture but cannot
    # measure containment: its student idea restates the group's first research
    # area, so a profile term in the seed is indistinguishable from the student's
    # own words. These two put daylight between the idea and the profile — fully
    # in `_adjacent`, all but one area in `_partial` — so a term that arrived
    # through the lookup is attributable.
    "ideate_scoped_adjacent": {
        "skill": "proposal-ideate",
        "serve": "g01-research-group",
        "produces": True,
        "request": (
            "I want to develop a thesis idea. To answer your usual questions up "
            "front: I'm in the M.Sc. Embedded Systems Engineering program at "
            "Musterstadt University, it's a Master's thesis, the proposal should "
            "be in English, I have about five months (April 2027 to September "
            "2027), and yes, you may look things up online. The research group I "
            "hope will supervise me has its page at {url} — please take a look "
            "at what they do; a saved export of their recent publication list is "
            "at {dblp}. My rough idea: whether code review comments on embedded "
            "firmware predict where field defects later show up. This message is "
            "our whole session — I cannot reply again, so develop the idea as far "
            "as you can without asking me anything, then treat this as me saying "
            "'enough' and create the seed proposal file now. Don't keep any "
            "scoping notes for later sessions."
        ),
    },
    "ideate_scoped_partial": {
        "skill": "proposal-ideate",
        "serve": "g01-research-group",
        "produces": True,
        "request": (
            "I want to develop a thesis idea. To answer your usual questions up "
            "front: I'm in the M.Sc. Embedded Systems Engineering program at "
            "Musterstadt University, it's a Master's thesis, the proposal should "
            "be in English, I have about five months (April 2027 to September "
            "2027), and yes, you may look things up online. The research group I "
            "hope will supervise me has its page at {url} — please take a look "
            "at what they do; a saved export of their recent publication list is "
            "at {dblp}. My rough idea: how much an eBPF tracing probe changes the "
            "latency of the code it observes. This message is our whole session — "
            "I cannot reply again, so develop the idea as far as you can without "
            "asking me anything, then treat this as me saying 'enough' and create "
            "the seed proposal file now. Don't keep any scoping notes for later "
            "sessions."
        ),
    },
    # the fixture carries two uncited entries with opposite right answers, and
    # the request deliberately does not say which is which: the judgment is the
    # thing under test, and naming the off-topic entry would hand it over.
    "write_offtopic_reference": {
        "skill": "proposal-write",
        "fixture": "f26-offtopic-reference",
        "proposal": "onboarding-documentation-formats.md",
        "request": (
            "Please do a writing pass over onboarding-documentation-formats.md and "
            "resolve whatever the check reports. I cannot answer any questions — "
            "decide and tell me what you did."
        ),
    },
    # citation practice: neither request mentions citations. The rule has to
    # reach the draft through the skill's own guidance, which is what a student
    # asking for a draft or a polish gets.
    "write_rich_seed": {
        "skill": "proposal-write",
        "fixture": "w08-rich-seed",
        "proposal": "flaky-test-prediction.md",
        "citations": "draft",
        "request": (
            "Please turn my idea notes in flaky-test-prediction.md into a full proposal "
            "draft. Keep my idea, mark anything missing as TODO. I cannot answer any "
            "questions — decide and tell me what you did."
        ),
    },
    "write_repair_citations": {
        "skill": "proposal-write",
        "fixture": "f27-citation-runs",
        "proposal": "dependency-update-breakage.md",
        "citations": "repair",
        "request": (
            "Please do a writing pass over dependency-update-breakage.md so it is ready "
            "for my supervisor. I cannot answer any questions — decide and tell me what "
            "you did."
        ),
    },
    # the install prompt, unanswered and with the scope answer given up front
    # (run_install_probe; nothing is staged)
    "install_prompt": {"install": True},
    "install_prompt_answered": {"install": True, "answered": True},
}

# Scenarios whose verdict is scoping containment rather than the default.
CONTAINMENT_SCENARIOS = ("ideate_scoped_adjacent", "ideate_scoped_partial")
# Scenarios judged on the produced draft; `citations` adds the citation verdicts.
DRAFT_SCENARIOS = ("write_from_seed", "write_rich_seed", "write_repair_citations")
# Scenarios judged from `<slug>-review.md`: same inputs, different bar.
REVIEW_VERDICTS = {
    "review_fixture": verdict_review,
    "review_hollow": verdict_hollow_review,
}


# ---------- install prompt probe (installation spec) -------------------------
#
# Not a skill scenario: nothing is staged, and the agent installs the skills
# itself by carrying out the shared install prompt. The default branch is
# replaced by a local server holding install.py and a zip of the working tree,
# so the probe measures this tree and reaches no public service, and the run
# gets its own HOME so the installer can never touch the operator's skills.

INSTALL_PROMPT = REPO / "shared" / "blocks" / "install-prompt.md"
INSTALLER = REPO / "install.py"
RAW_INSTALLER_URL = (
    "https://raw.githubusercontent.com/hutzelmann/thesis-proposal-skills/main/install.py")
DEFAULT_ARCHIVE_URL = (
    "https://codeload.github.com/hutzelmann/thesis-proposal-skills/zip/refs/heads/main")
PROBE_REVISION = "0" * 39 + "1"  # stands in for the commit id a GitHub archive carries
INSTALL_TARGETS = (".agents/skills", ".claude/skills")
ANSWER = "(My answer to your question in step 2, in advance: install for all my projects.)"


def working_tree_skills() -> dict[str, dict[str, bytes]]:
    return {
        skill.name: {p.relative_to(skill).as_posix(): p.read_bytes()
                     for p in sorted(skill.rglob("*"))
                     if p.is_file() and "__pycache__" not in p.parts}
        for skill in sorted(SKILLS.iterdir())
        if skill.is_dir() and skill.name.startswith("proposal-")
    }


def stage_install_source(root: Path, base_url: str) -> None:
    """install.py, its default archive pointed at a zip of the working tree."""
    with zipfile.ZipFile(root / "main.zip", "w") as archive:
        for name, files in working_tree_skills().items():
            for rel, payload in files.items():
                archive.writestr(f"thesis-proposal-skills-main/skills/{name}/{rel}", payload)
        archive.comment = PROBE_REVISION.encode()
    text = INSTALLER.read_text(encoding="utf-8")
    if text.count(DEFAULT_ARCHIVE_URL) != 1:
        sys.exit("install.py no longer names the default archive the probe redirects")
    (root / "install.py").write_text(text.replace(DEFAULT_ARCHIVE_URL, f"{base_url}/main.zip"),
                                     encoding="utf-8")


def install_request(base_url: str, answered: bool) -> str:
    prompt = INSTALL_PROMPT.read_text(encoding="utf-8")
    if prompt.count(RAW_INSTALLER_URL) != 1:
        sys.exit("the install prompt no longer names the installer the probe redirects")
    request = prompt.replace(RAW_INSTALLER_URL, f"{base_url}/install.py")
    return f"{request.rstrip()}\n\n{ANSWER}" if answered else request


def skill_copies(*roots: Path) -> list[Path]:
    """Every `proposal-*` folder holding a SKILL.md under the given roots."""
    return sorted({p.parent for root in roots for p in root.rglob("SKILL.md")
                   if p.parent.name.startswith("proposal-")})


def install_probe_verdict(answered: bool, home: Path, ws: Path, chat: str) -> tuple[bool, str]:
    copies = skill_copies(home, ws)
    if not answered:
        return verdict_install_prompt_asks_scope(chat, [str(c) for c in copies])
    targets = {rel: home / rel for rel in INSTALL_TARGETS}
    found = {rel: {c.name: {p.relative_to(c).as_posix(): p.read_bytes()
                            for p in sorted(c.rglob("*")) if p.is_file()}
                   for c in copies if c.parent == root}
             for rel, root in targets.items()}
    records = {}
    for rel, root in targets.items():
        try:
            records[rel] = json.loads((root / ".thesis-proposal-install.json")
                                      .read_text(encoding="utf-8"))
        except (OSError, ValueError):
            records[rel] = None
    strays = [str(c) for c in copies if c.parent not in targets.values()]
    return verdict_install_prompt_installed(working_tree_skills(), found, records, strays)


def run_install_probe(args: argparse.Namespace, scenario: dict) -> int:
    """Two temp homes' worth of isolation, always: the host's config is the
    routing rig's isolated one (logged in without the real home, the stored
    login kept current), and HOME is empty, so whatever the installer writes
    lands where the verdict looks. Exit statuses as for a dev run."""
    base = Path(tempfile.mkdtemp(prefix=f"devrun-{args.scenario}-"))
    ws, home, served = base / "proposals", base / "home", base / "served"
    for d in (ws, home, served):
        d.mkdir()
    answered = scenario.get("answered", False)
    stack = ExitStack()
    config, chat = None, ""
    try:
        try:
            config = enter_isolation(stack, "devrun-config-")
            server = HTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(served)))
            threading.Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.shutdown)
            url = f"http://127.0.0.1:{server.server_port}"
            stage_install_source(served, url)
            events = run_claude(ws, install_request(url, answered), args.model, args.timeout,
                                budget=args.max_budget_usd, config=config, home=home)
            save_events(events, base)
            chat = final_text(events)
            passed, why = install_probe_verdict(answered, home, ws, chat)
            out = summary(args, passed, why, events, config)
            status = EXIT_PASS if passed else EXIT_FAIL
            out["outcome"], out["exit_status"] = OUTCOMES[status], status
        except RunnerFailure as failure:
            if failure.events:
                save_events(failure.events, base)
            out, status = failure_summary(args, failure, config), failure.status
            out["config"] = "isolated"  # the probe never runs ambient
        emit(out, args.summary_log)
        if chat:
            print("\n--- chat tail ---\n" + chat[-1200:])
        return status
    finally:
        stack.close()
        if args.keep:
            print(f"\nprobe directory kept: {base}")
        else:
            shutil.rmtree(base, ignore_errors=True)


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


def host_command(request: str, model: str, budget: float | None = None) -> list[str]:
    """The headless invocation: stream-json emits events only with --verbose,
    the outward-facing tools are denied because permission prompts are skipped,
    and the budget cap is added only when one was given."""
    command = [
        "claude", "-p", request, "--model", model, "--dangerously-skip-permissions",
        "--output-format", "stream-json", "--verbose",
        "--disallowed-tools", *OUTWARD_TOOLS,
    ]
    if budget is not None:
        command += ["--max-budget-usd", str(budget)]
    return command


def host_failure(events: list[dict], returncode: int, stderr: str) -> str | None:
    """Why the run is a runner failure, or None — with the re-login instruction
    when the reason is the stored login, which no rerun repairs."""
    message = host_failure_reason(events, returncode, stderr)
    return login_remedy(message) if message else None


def host_failure_reason(events: list[dict], returncode: int, stderr: str) -> str | None:
    """Checked in this order: an error result event (a budget overrun is one —
    it exits non-zero with nothing on stderr in stream mode, and carries the
    subtype, errors and cost so far), a non-zero exit without one (the stderr
    tail), and a zero exit with no result event at all, which the host allows
    and which would otherwise judge the L1 over partial narration with empty
    telemetry. The first is composed by `routing.error_result_reason`, which
    the routing rig reads the same way."""
    reason = error_result_reason(events)
    if reason:
        return reason
    if returncode != 0:
        return f"claude failed: {stderr.strip()[-800:] or 'no stderr'}"
    if not result_event(events):
        return "claude emitted no result event"
    return None


class RunnerFailure(Exception):
    """The run ended without a verdict. `untested` when the subscription could
    not serve it (exit status 3), else another runner failure (4); `events`
    is whatever stream the host produced, saved into a kept workspace."""

    def __init__(self, message: str, untested: bool = False,
                 events: list[dict] | None = None):
        super().__init__(message)
        self.message = message
        self.untested = untested
        self.events = events or []

    @property
    def status(self) -> int:
        return EXIT_UNTESTED if self.untested else EXIT_RUNNER


def model_env(environ: Mapping[str, str], config: Path | None) -> dict[str, str]:
    """The model-under-test child's environment: the inherited one minus every
    variable that can move its billing off the subscription login, in ambient
    and isolated mode alike. Effort and session settings stay — they are part
    of what a dev run measures. `environ` is not modified."""
    env = {name: value for name, value in environ.items()
           if not name.startswith(BILLING_PREFIXES)}
    if config is not None:
        env["CLAUDE_CONFIG_DIR"] = str(config)
    return env


def run_claude(ws: Path, request: str, model: str, timeout: int,
               budget: float | None = None, config: Path | None = None,
               home: Path | None = None) -> list[dict]:
    """Run the host headless and return its stream-json events.

    The stream, not the plain text, is what a run is judged on: the final
    `result` event carries the chat text plus cost, turns and token usage, and
    the assistant events carry every tool call — including a helper-agent
    spawn, which plain text output never shows. A run the host failed raises
    `RunnerFailure` — untested when the login was refused or the stream
    reports overage or a refused rate-limit status (a run stopped at the plan
    limit ends with an error result), else a runner failure; so does a
    finished run whose stream shows billing other than the subscription.
    """
    env = model_env(os.environ, config)
    if home is not None:
        # the install probe's scratch home, layered on top of the child's
        # environment so the installer can never touch the operator's skills
        env.update(HOME=str(home), USERPROFILE=str(home))
    try:
        result = subprocess.run(
            host_command(request, model, budget),
            # stdin must be closed: with an inherited non-tty stdin (backgrounded or
            # redirected runs) claude blocks waiting for piped input, warns, and can
            # exit non-zero — a runner failure that looks like a skill failure
            cwd=ws, env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RunnerFailure(f"claude did not finish within {timeout}s") from None
    events = parse_events(result.stdout)
    failure = host_failure(events, result.returncode, result.stderr)
    if failure:
        # only an explicit report counts here: a budget overrun with allowed
        # statuses stays a runner failure, and so does a stream with no report
        refusal = claude_cli.rate_refusal(events)
        message = f"{failure} (not a subscription result: {refusal})" if refusal else failure
        raise RunnerFailure(message, untested=bool(refusal or LOGIN_FAILURE.search(failure)),
                            events=events)
    billing = claude_cli.billing_problem(events)
    if billing:
        raise RunnerFailure(f"not a subscription result: {billing}", untested=True,
                            events=events)
    return events


# inside the workspace so a kept run carries its own transcript; the leading
# dot keeps it out of every `*.md` glob a verdict reads
EVENTS_FILE = ".devrun-events.jsonl"


def save_events(events: list[dict], ws: Path) -> Path:
    """Write the host's event stream into the workspace, one object per line —
    the only record of why a run did or skipped something."""
    path = ws / EVENTS_FILE
    path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events),
                    encoding="utf-8")
    return path


def final_text(events: list[dict]) -> str:
    """The chat the verdicts read: the result event's final text — what the
    plain output mode printed — and nothing else."""
    text = result_event(events).get("result")
    return text if isinstance(text, str) else ""


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


def served_model(events: list[dict]) -> tuple[str | None, str | None]:
    """The model the host served, by its full ID — from the `init` event,
    checked against the result's per-model usage — and a note when the two
    disagree. A full session may list an auxiliary model beside the main one,
    so only the init model's absence from the usage is a discrepancy."""
    reported = claude_cli.init_event(events).get("model")
    usage = claude_cli.model_usage(events)
    if reported and (not usage or reported in usage):
        return reported, None
    if reported:
        return reported, f"init reports {reported}, modelUsage lists {', '.join(sorted(usage))}"
    producing = sorted(usage, key=lambda m: -claude_cli.output_tokens(usage[m]))
    if producing:
        return producing[0], "no init event; taken from modelUsage"
    return None, None


def identity(args: argparse.Namespace, events: list[dict]) -> dict:
    """What ran: the requested alias beside the served full ID and CLI version."""
    model, note = served_model(events)
    record = {"scenario": args.scenario, "model_requested": args.model, "model": model,
              "cli_version": claude_cli.init_event(events).get("claude_code_version")}
    if note:
        record["model_check"] = note
    return record


def summary(args: argparse.Namespace, passed: bool, why: str, events: list[dict],
            config: Path | None, allowed: int = 0, extra: dict | None = None) -> dict:
    """The run's L1 verdict plus the probe: telemetry and the advisory
    single-context verdict against the scenario's helper allowance, which never
    changes the exit status. `extra` carries scenario-specific information —
    a supervise run's feedback length — that is reported, never judged."""
    names = [name for name, _ in tool_calls(events)]
    single, single_why = verdict_single_context(names, allowed)
    return {
        **identity(args, events),
        "arm": "baseline" if args.no_skill else "with-skill",
        "l1": "PASS" if passed else "FAIL", "why": why,
        "config": "isolated" if config else "ambient",
        "config_dir": str(config) if config else None,
        **telemetry(events),
        "helper_calls": [name for name in names if name in HELPER_TOOLS],
        "single_context": f"{'PASS' if single else 'FAIL'}: {single_why}",
        **(extra or {}),
    }


def failure_summary(args: argparse.Namespace, failure: RunnerFailure,
                    config: Path | None) -> dict:
    """A run that ended without a verdict, in the same shape: no `l1` key, the
    outcome and the host's own message instead. The label follows the request:
    a run whose isolated config could not be prepared was still not ambient."""
    return {
        **identity(args, failure.events),
        "arm": "baseline" if args.no_skill else "with-skill",
        "outcome": OUTCOMES[failure.status], "exit_status": failure.status,
        "why": failure.message,
        "config": "isolated" if args.isolated else "ambient",
        "config_dir": str(config) if config else None,
        **telemetry(failure.events),
    }


def exit_status(*, runner_failure: bool, failed: bool, untested: bool) -> int:
    """Precedence: a runner failure, then a failed verdict — a real FAIL
    outranks an ungraded criterion — then untested, then pass."""
    if runner_failure:
        return EXIT_RUNNER
    if failed:
        return EXIT_FAIL
    if untested:
        return EXIT_UNTESTED
    return EXIT_PASS


def aggregate_status(statuses: list[int]) -> int:
    """Several outcomes as one exit status, by the same precedence; nothing
    recorded at all is a runner failure, never a pass, and so is any status
    that is not a verdict's (a usage error, or a value a log should not hold)."""
    if not statuses:
        return EXIT_RUNNER
    verdicts = (EXIT_PASS, EXIT_FAIL, EXIT_UNTESTED)
    return exit_status(runner_failure=any(s not in verdicts for s in statuses),
                       failed=EXIT_FAIL in statuses, untested=EXIT_UNTESTED in statuses)


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
    """The feedback draft(s) plus the notes file the literature verdict reads."""
    return {
        f.name: f.read_text(encoding="utf-8")
        for pattern in ("*-feedback.md", "*.notes.md")
        for f in sorted(ws.glob(pattern)) if f.is_file()
    }


# what a supervise run writes beside the normalized proposal
_SUPERVISE_SIDECARS = ("-feedback.md", "-review.md", NOTES_SUFFIX)


def normalized_proposal(ws: Path) -> str | None:
    """The normalized `<slug>.md` a supervise run wrote — the locator verdict
    compares the feedback's standards against it — or None."""
    found = [f for f in sorted(ws.glob("*.md"))
             if f.is_file() and not f.name.endswith(_SUPERVISE_SIDECARS)]
    return found[0].read_text(encoding="utf-8") if found else None


def first_text(ws: Path, pattern: str) -> str | None:
    found = sorted(f for f in ws.glob(pattern) if f.is_file())
    return found[0].read_text(encoding="utf-8") if found else None


def supervise_verdict(scenario: dict, ws: Path,
                      events: list[dict] | None = None) -> tuple[bool, str]:
    """The feedback contract over the scenario's fixture identity; the verifier
    — started with its brief, and declared in the review — wherever the
    scenario allows the helper; and, for the over-scoped fixture, the lettered
    cut options in the feedback and the workload and verification sections."""
    passed, why = verdict_supervise_feedback_contract(
        feedback_files(ws), scenario.get("forbidden", S01_FORBIDDEN), INSTALLED_SKILLS,
        load_closing_note(SKILLS), S01_LANGUAGE, proposal=normalized_proposal(ws))
    results = [(passed, why)]
    review = first_text(ws, "*-review.md")
    if scenario.get("helpers"):
        results += [verdict_supervise_verifier(tool_calls(events or [])),
                    verdict_supervise_verification_declared(review)]
    if scenario.get("scope"):
        results += [verdict_supervise_scope_options(first_text(ws, "*-feedback.md"),
                                                    load_closing_note(SKILLS)),
                    verdict_supervise_review_sections(review)]
    failed = [reason for ok, reason in results if not ok]
    if failed:
        return False, "; ".join(failed)
    return True, "; ".join(reason for _, reason in results)


def supervise_extra(scenario: dict, ws: Path) -> dict:
    """What a supervise run reports beside its verdict without being judged on it."""
    if not scenario.get("feedback"):
        return {}
    feedback = first_text(ws, "*-feedback.md")
    return {"feedback_words": feedback_body_words(feedback, load_closing_note(SKILLS))
            if feedback else None}


def containment_inputs(request: str, chat: str,
                       events: list[dict]) -> tuple[str, str]:
    """A two-turn transcript and the run's issued queries.

    The dev runner's scenarios are one-shot, so the student's only turn is the
    request itself — which is the right attribution anyway: it is the whole of
    what the student said. Queries are read from the tool-call inputs, where a
    search term reaches whether the run used the shipped script, a fetch tool, or
    a shell command.
    """
    transcript = f"STUDENT: {request}\n\nASSISTANT: {chat}"
    queries = " ".join(json.dumps(inp, ensure_ascii=False) for _, inp in tool_calls(events))
    return transcript, queries


def containment_verdict(ws: Path, request: str, chat: str,
                        events: list[dict]) -> tuple[bool, str]:
    """Seed structurally complete, and no scoping vocabulary the student never
    voiced in the files or the queries."""
    files = workspace_markdown(ws)
    produced, where = select_draft(files)
    if not produced:
        return False, where
    seeded, why = verdict_seed(files.get(produced), produced)
    if not seeded:
        return False, why
    transcript, queries = containment_inputs(request, chat, events)
    contained, detail = verdict_scoping_containment(transcript, files, queries)
    return contained, f"{why}; {detail} ({where})"


def draft_verdict(scenario: dict, ws: Path, original: str) -> tuple[bool, str]:
    """The draft is mechanically sound. The citation scenarios add that no
    source is cited on consecutive sentences — and, over the over-citing
    fixture, that no source was dropped to get there."""
    # the skill may draft into a fresh <slug>.md instead of the seed
    chosen, where = select_draft(workspace_markdown(ws), scenario["proposal"], original)
    if not chosen:
        return False, where
    text = read(ws / chosen)
    check = run_check(ws, chosen)
    citations = scenario.get("citations")
    if citations == "repair":
        passed, why = verdict_repaired_draft(original, text, check)
    elif citations == "draft":
        passed, why = verdict_cited_draft(text, check)
    else:
        passed, why = verdict_draft(text, check)
    return passed, f"{why} ({where})"


def ideate_verdict(ws: Path, chat: str) -> tuple[bool, str]:
    files = workspace_markdown(ws)
    produced, where = select_draft(files)
    if not produced:
        return False, where
    # the request explicitly declines the scoping note, so a guidelines.md
    # existing at all fails the run
    passed, why = verdict_ideate_scoped(files, produced, chat, note_declined=True)
    return passed, f"{why} ({where})"


def import_verdict(ws: Path) -> tuple[bool, str]:
    produced, _ = select_draft(workspace_markdown(ws))
    if not produced:
        return verdict_import(None)
    return verdict_import(read(ws / produced), run_check(ws, produced), produced)


def verdict(name: str, scenario: dict, ws: Path, chat: str,
            request: str = "", events: list[dict] | None = None) -> tuple[bool, str]:
    if name in CONTAINMENT_SCENARIOS:
        return containment_verdict(ws, request, chat, events or [])
    if scenario.get("feedback"):
        return supervise_verdict(scenario, ws, events)
    if name == "ideate_scoped":
        return ideate_verdict(ws, chat)
    if scenario.get("produces"):
        return import_verdict(ws)
    fixture = FIXTURES / scenario["fixture"]
    original = (fixture / scenario["proposal"]).read_text(encoding="utf-8")
    current = read(ws / scenario["proposal"])
    if name == "check_report":
        return verdict_check_report(fixture / "expected.json", original, current, chat)
    if name == "customize_override":
        return verdict_customize_override(original, current, read(ws / "guidelines.md"))
    if name == "write_offtopic_reference":
        # the reason may land in the notes file or in chat; the verdict accepts
        # either, so both are handed over as one blob
        notes = "".join(text for fname, text in workspace_markdown(ws).items()
                        if fname.endswith(NOTES_SUFFIX))
        return verdict_offtopic_reference(current, notes + chat)
    if name in REVIEW_VERDICTS:
        review_name = scenario["proposal"].replace(".md", "-review.md")
        return REVIEW_VERDICTS[name](original, current, read(ws / review_name), review_name)
    if name in DRAFT_SCENARIOS:
        return draft_verdict(scenario, ws, original)
    raise ValueError(name)


# ---------- dev-runner L2: the subscription judge -------------------------------


@dataclass(frozen=True)
class Judge:
    """The dev judge of one invocation, validated before anything is staged."""

    model: str
    effort: str
    cap: float


def resolve_judge(args: argparse.Namespace, parser: argparse.ArgumentParser) -> Judge | None:
    """None without judging. Otherwise the registry's dev-judge role at its
    pinned effort — refused with a usage error, before any staging or call,
    when it could not judge: no isolation, no rubric twin, or an ID the
    subscription does not serve (an alias, or a metered provider's ID)."""
    if not (args.judge or args.rejudge):
        return None
    if args.judge and args.rejudge:
        parser.error("--judge grades a fresh run and --rejudge kept workspaces: pass one")
    if args.judge and not args.isolated:
        parser.error("--judge requires --isolated: the judge reuses the run's isolated "
                     "configuration and never reads the ambient one")
    if args.scenario not in DEV_RUBRICS:
        parser.error(f"{args.scenario} has no rubric twin; dev-runner L2 grades only "
                     f"{', '.join(DEV_RUBRICS)}")
    roles = support.parse_registry(REGISTRY.read_text(encoding="utf-8")).roles
    model = support.role_model(roles, "dev_judge", os.environ)
    if not support.is_subscription_model(model):
        source = " (set by DEV_JUDGE_MODEL)" if os.environ.get("DEV_JUDGE_MODEL") else ""
        parser.error(f"[roles].dev_judge resolves to {model!r}{source}, which is not a full "
                     "model ID the subscription serves (claude-…, no provider prefix, not an "
                     "alias); a metered ID never grades dev runs")
    return Judge(model, roles.dev_judge_effort, args.max_notional)


def l2_artifact(name: str, scenario: dict, ws: Path) -> str | None:
    """What the judge grades, selected as the scenario's L1 verdict selects it:
    the review file, or the produced draft (which may be a fresh `<slug>.md`)."""
    if name in REVIEW_VERDICTS:
        return read(ws / scenario["proposal"].replace(".md", "-review.md")) or None
    original = (FIXTURES / scenario["fixture"] / scenario["proposal"]).read_text(encoding="utf-8")
    chosen, _ = select_draft(workspace_markdown(ws), scenario["proposal"], original)
    return (read(ws / chosen) or None) if chosen else None


def fixture_oracle(scenario: dict) -> dict:
    path = FIXTURES / scenario["fixture"] / "expected.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def judge_criteria(name: str, scenario: dict, ws: Path,
                   request: str) -> tuple[list[Criterion], dict[str, str]]:
    """One prompt per rubric criterion of the scenario, from the same templates
    and criteria the matrix judge reads; the question is the visible request
    (the oracle list for the review scenarios). Nothing to grade costs no call:
    those criteria are reported "not judged"."""
    artifact = l2_artifact(name, scenario, ws)
    if artifact is None:
        return [], {entry.name: "not judged: no artifact" for entry in DEV_RUBRICS[name]}
    facts = fixture_oracle(scenario)
    return [
        Criterion(entry.name, judge_prompt(entry.rubric, question_for(entry, request, facts),
                                           artifact, CRITERIA[entry.key]))
        for entry in DEV_RUBRICS[name]
    ], {}


def run_judge(judge: Judge, criteria: list[Criterion], config: Path | None,
              projection: bool = False) -> JudgeRun:
    """Every judge call of the invocation under one event loop: the login
    preflight, the warm-up alone, then the bounded fan-out."""
    if not criteria:
        return JudgeRun((), 0.0)
    return anyio.run(partial(
        claude_cli.judge_all, criteria, model=judge.model, effort=judge.effort,
        system_prompt=JUDGE_SYSTEM, config=config, cap=judge.cap, projection=projection))


GRADE_NAMES = {True: "PASS", False: "FAIL", None: "UNTESTED"}


def l2_report(judge: Judge, grades: tuple[Grade, ...] | list[Grade],
              not_judged: dict[str, str], served: str | None) -> tuple[dict, int]:
    """The summary's L2 part under its label, and the L2 status: a graded
    failure fails, an ungraded criterion is untested, never a failing grade."""
    calls = [g.call for g in grades if g.call is not None]
    criteria = {name: {"grade": "UNTESTED", "why": why} for name, why in not_judged.items()}
    criteria.update({g.name: {"grade": GRADE_NAMES[g.passed], "why": g.reason} for g in grades})
    graded = {g.name: bool(g.passed) for g in grades if g.passed is not None}
    passed, why = verdict_l2_grades(graded) if graded else (True, "nothing graded")
    untested = bool(not_judged) or len(graded) < len(grades)
    status = exit_status(runner_failure=False, failed=not passed, untested=untested)
    block = {
        "criteria": criteria,
        "judge_model": judge.model,
        "judge_served": calls[0].model if calls else None,
        "effort": judge.effort,
        "cli_version": calls[0].cli_version if calls else None,
        "thinking_tokens": sum(c.thinking_tokens for c in calls),
        "notional_usd": round(sum(c.notional_usd for c in calls), 6),
        "rate_limit": asdict(calls[-1].rate_limit) if calls else None,
    }
    return {"l2": block, "l2_label": JUDGE_LABEL, "l2_verdict": why,
            "self_graded": served is not None and served == judge.model}, status


# ---------- one dev run ---------------------------------------------------------


def enter_isolation(stack: ExitStack, prefix: str) -> Path:
    """The isolated configuration, a sibling temp directory outside the
    workspace (staging and the verdicts' `*.md` glob never see it). Preparing
    it exits with a message when no stored login exists or another run's
    refresh never arrives: the subscription cannot serve the run — untested."""
    try:
        return stack.enter_context(isolated_config(prefix))
    except SystemExit as exc:
        if isinstance(exc.code, str):
            raise RunnerFailure(exc.code, untested=True) from None
        raise


def served_request(scenario: dict, stack: ExitStack) -> str:
    """The scenario's request; a `serve` scenario's fixture is served over
    localhost for the run's duration and its URLs are filled in."""
    request = scenario["request"]
    if not scenario.get("serve"):
        return request
    handler = partial(QuietHandler, directory=str(FIXTURES / scenario["serve"]))
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    stack.callback(server.shutdown)
    base = f"http://127.0.0.1:{server.server_port}"
    return request.format(url=f"{base}/group.html", dblp=f"{base}/dblp.json")


def completed_run(args: argparse.Namespace, judge: Judge | None, scenario: dict, ws: Path,
                  request: str, events: list[dict], config: Path | None) -> tuple[dict, int]:
    """The verdicts of a run the host finished: L1, then — inside the same
    isolation — the judge, with the precedence of `exit_status`."""
    passed, why = verdict(args.scenario, scenario, ws, final_text(events), request, events)
    out = summary(args, passed, why, events, config, allowed=scenario.get("helpers", 0),
                  extra=supervise_extra(scenario, ws))
    status = EXIT_PASS if passed else EXIT_FAIL
    if judge:
        criteria, not_judged = judge_criteria(args.scenario, scenario, ws, request)
        l2, l2_status = l2_report(judge, run_judge(judge, criteria, config).grades,
                                  not_judged, out["model"])
        out.update(l2)
        status = aggregate_status([status, l2_status])
    out["outcome"], out["exit_status"] = OUTCOMES[status], status
    return out, status


def emit(out: dict, log: Path | None) -> None:
    """Print the summary; with a summary log, also append it as one JSON line."""
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(out, ensure_ascii=False) + "\n")


def dev_run(args: argparse.Namespace, judge: Judge | None) -> int:
    scenario = SCENARIOS[args.scenario]
    ws = Path(tempfile.mkdtemp(prefix=f"devrun-{args.scenario}-"))
    # the isolated config's linked credentials are as reachable for the child as
    # ~/.claude is in ambient mode, and a refresh the child performs is written
    # back to them; the judge reuses the same config, after L1
    stack = ExitStack()
    config, chat = None, ""
    try:
        try:
            config = enter_isolation(stack, "devrun-config-") if args.isolated else None
            stage(scenario, ws, install_skill=not args.no_skill)
            request = served_request(scenario, stack)
            events = run_claude(ws, request, args.model, args.timeout,
                                budget=args.max_budget_usd, config=config)
            save_events(events, ws)
            chat = final_text(events)
            out, status = completed_run(args, judge, scenario, ws, request, events, config)
        except RunnerFailure as failure:
            if failure.events:
                save_events(failure.events, ws)
            out, status = failure_summary(args, failure, config), failure.status
        except Exception as exc:  # a crash still leaves its line in the summary log
            traceback.print_exc()
            failure = RunnerFailure(f"runner crashed: {exc!r}")
            out, status = failure_summary(args, failure, config), failure.status
        emit(out, args.summary_log)
        if chat:
            print("\n--- chat tail ---\n" + chat[-1200:])
        return status
    finally:
        stack.close()
        if args.keep:
            print(f"\nworkspace kept: {ws}")
        else:
            shutil.rmtree(ws, ignore_errors=True)


# ---------- re-grade kept workspaces ----------------------------------------------


def load_events(ws: Path) -> list[dict]:
    path = ws / EVENTS_FILE
    return parse_events(path.read_text(encoding="utf-8")) if path.exists() else []


def rejudge_lines(args: argparse.Namespace, judge: Judge,
                  workspaces: list[Path]) -> list[dict]:
    """One summary per kept workspace. One invocation: one isolated config,
    one warm-up, and the batch projection before the fan-out; a config that
    cannot be prepared leaves every criterion untested."""
    scenario = SCENARIOS[args.scenario]
    plans = [(ws, *judge_criteria(args.scenario, scenario, ws, scenario["request"]))
             for ws in workspaces]
    flat = [c for _, criteria, _ in plans for c in criteria]
    with ExitStack() as stack:
        try:
            run = run_judge(judge, flat, enter_isolation(stack, "devjudge-config-"),
                            projection=True)
        except RunnerFailure as failure:
            run = JudgeRun(tuple(Grade(c.name, None, failure.message) for c in flat), 0.0)
    grades = iter(run.grades)
    lines = []
    for ws, criteria, not_judged in plans:
        served, _ = served_model(load_events(ws))
        l2, status = l2_report(judge, [next(grades) for _ in criteria], not_judged, served)
        lines.append({"scenario": args.scenario, "mode": "rejudge", "workspace": str(ws),
                      "model": served, **l2, "outcome": OUTCOMES[status],
                      "exit_status": status})
    return lines


def rejudge(args: argparse.Namespace, judge: Judge) -> int:
    """Re-grade kept workspaces of the scenario with the current rubric and
    request text, never running the model under test. A crash is a runner
    failure with one summary line per workspace, as a dev run's is."""
    workspaces = list(args.rejudge)
    missing = [str(ws) for ws in workspaces if not ws.is_dir()]
    if missing:
        print(f"--rejudge: not a kept workspace: {', '.join(missing)}", file=sys.stderr)
        return EXIT_USAGE
    try:
        lines = rejudge_lines(args, judge, workspaces)
    except Exception as exc:  # a crash still leaves its lines in the summary log
        traceback.print_exc()
        failure = RunnerFailure(f"runner crashed: {exc!r}")
        lines = [{"scenario": args.scenario, "mode": "rejudge", "workspace": str(ws),
                  "outcome": OUTCOMES[failure.status], "exit_status": failure.status,
                  "why": failure.message} for ws in workspaces]
    for line in lines:
        emit(line, args.summary_log)
    return aggregate_status([line["exit_status"] for line in lines])


# ---------- the closing summary of a sequence of runs -------------------------------


NO_LINE = ("no summary line: the step ended before recording one (a usage error, a "
           "crash outside the run, or a kill)")


def summary_rows(lines: list[dict], expected: tuple[str, ...] | list[str] = ()) -> list[dict]:
    """One row per scenario — per workspace for a re-grade — from its latest
    line, in the order the scenarios first appeared; then a runner-failure row
    for each expected scenario that recorded no line at all."""
    latest: dict[tuple, dict] = {}
    for line in lines:
        why = "; ".join(part for part in (line.get("why"), line.get("l2_verdict")) if part)
        latest[(line.get("scenario"), line.get("workspace"))] = {
            "scenario": line.get("scenario"), "workspace": line.get("workspace"),
            "outcome": line.get("outcome", OUTCOMES[EXIT_RUNNER]),
            "exit_status": int(line.get("exit_status", EXIT_RUNNER)), "why": why,
        }
    rows = list(latest.values())
    seen = {row["scenario"] for row in rows}
    rows += [{"scenario": name, "workspace": None, "outcome": OUTCOMES[EXIT_RUNNER],
              "exit_status": EXIT_RUNNER, "why": NO_LINE}
             for name in dict.fromkeys(expected) if name not in seen]
    return rows


def summarize(path: Path, expected: tuple[str, ...] | list[str] = ()) -> int:
    """Print the rows of a summary log, remove it, and exit with the combined
    status: zero only when every row passed. With `expected`, a scenario that
    left no line is a runner failure — a step can exit before it records one —
    and an absent log with nothing expected means nothing ran."""
    lines = parse_events(path.read_text(encoding="utf-8")) if path.exists() else []
    rows = summary_rows(lines, expected)
    if not rows:
        print(f"no runs recorded in {path}: nothing ran")
        return EXIT_RUNNER
    print(f"\n=== {len(rows)} run(s) ===")
    for row in rows:
        where = f" [{row['workspace']}]" if row["workspace"] else ""
        print(f"  {row['outcome']:<15} {row['scenario']}{where}: {row['why'][:160]}")
    path.unlink(missing_ok=True)
    status = aggregate_status([row["exit_status"] for row in rows])
    print(f"=== {OUTCOMES[status]} ===")
    return status


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scenario", nargs="?", choices=sorted(SCENARIOS))
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
    parser.add_argument("--judge", action="store_true",
                        help="grade the scenario's rubric criteria with the subscription dev "
                             "judge ([roles].dev_judge); needs --isolated. Dev-runner L2, not "
                             "comparable to matrix")
    parser.add_argument("--rejudge", nargs="+", type=Path, metavar="DIR",
                        help="re-grade kept workspaces of the scenario with the dev judge, "
                             "without running the model under test")
    parser.add_argument("--max-notional", type=float, default=DEFAULT_MAX_NOTIONAL,
                        metavar="USD",
                        help="cap on the judge calls' cumulative notional cost — plan quota, "
                             "not money (default %(default).2f)")
    parser.add_argument("--summary-log", type=Path, metavar="PATH",
                        help="append the run's summary to PATH as one JSON line, failures "
                             "included (a usage error records none)")
    parser.add_argument("--summarize", type=Path, metavar="PATH",
                        help="print one row per scenario from a summary log, exit non-zero "
                             "unless every row passed, and remove the log")
    parser.add_argument("--expect", nargs="+", choices=sorted(SCENARIOS), metavar="SCENARIO",
                        help="with --summarize: the scenarios the sequence ran; one that left "
                             "no line in the log is a runner failure")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.expect and not args.summarize:
        parser.error("--expect lists the scenarios a --summarize PATH should hold")
    if not (args.summarize or args.scenario):
        parser.error("a scenario is required (or --summarize PATH)")
    try:
        if args.summarize:
            return summarize(args.summarize, args.expect or ())
        judge = resolve_judge(args, parser)
        if args.rejudge:
            return rejudge(args, judge)
        scenario = SCENARIOS[args.scenario]
        if scenario.get("install"):  # no rubric twin, so no judge reaches here
            return run_install_probe(args, scenario)
        return dev_run(args, judge)
    except Exception:  # whatever escaped the run's own handling never reads as FAIL (1)
        traceback.print_exc()
        return EXIT_RUNNER


if __name__ == "__main__":
    sys.exit(main())
