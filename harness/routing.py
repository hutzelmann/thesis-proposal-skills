#!/usr/bin/env python3
"""Routing rig: which skill does the real host selector invoke for an utterance?

Every other harness task hands the agent a skill body and measures what it does
with it. This one measures the step before that: the host reads only the eleven
frontmatter descriptions and picks one. The verdict is the first `proposal-*`
Skill invocation observed, after which the run is stopped as soon as the
routing turn's rate-limit report has been read (on 2.1.284 it follows the
`Skill` call's tool result and the skill's instructions), the run has ended,
or the next turn has begun — everything past the selection is paid noise.

The measurement runs against an isolated CLAUDE_CONFIG_DIR holding exactly the
skills under test, in the allowlisted environment `host_login.allowlisted_env`
builds for every isolated Claude child, so the number describes a student's
install rather than the developer's machine or session. `prepare_config` links
the harness's own login (`host_login`: its home, checked by a preflight that
fails closed), the directory `CLAUDE_REAL_CONFIG_DIR` names under the explicit
opt-in, or nothing when a long-lived token is exported; the removed
`ROUTING_CONFIG_DIR` override is refused. The operator's claude.ai account
would otherwise reach a run through the linked login: the configuration's
settings opt out of skill and plugin sync and connectors, every child gets the
connector switch off and an empty Anthropic profile directory (the run is
refused while the default one holds any entry), a case whose stream shows an
account surface is stopped there and recorded as an error, and synced content
found in the configuration after the sweep voids every case
(`account_surfaces`). Billing is held to the same checks as the dev runner's
(`billing_problem`, `billing_signals`, `case_billing`, which live here because
`claude_cli` imports this module): a case whose stream shows billing other
than the subscription voids the whole sweep, and no further case starts. The
report records the isolation conditions, so a report measured under others is
not compared as a predecessor; the raw run log also records the login the
sweep linked and its directory. The rig needs the `claude` binary and a
logged-in subscription, which is why it is an on-demand instrument and not
part of the L0 chain; the pure functions below and the dataset's integrity
are. `follow_stream`, the stream reader with its deadline and its stop at the
first decisive event (termination before kill, `host_login.stop_child`), is
shared with the dev runner.

Usage:
  uv run poe routing
  uv run python harness/routing.py --model haiku --kind collision
  uv run python harness/routing.py --case review-canonical --jobs 1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field, replace
from pathlib import Path

import codex_cli
import copilot_cli
import host_login
from account_surfaces import (
    PINNED_SETTINGS,
    SETTINGS_FILE,
    SurfaceLeak,
    config_surfaces,
    isolation_problem,
    profile_dir,
    profile_store_problem,
    stream_surfaces,
    surface_reason,
)
from host_login import (
    CREDENTIALS,
    LOGIN_COMMAND,
    LONG_LIVED_TOKEN,
    OPT_IN_VAR,
    RELOGIN,
    LoginProblem,
    LoginSource,
    keep_login,
    login_remedy,
    refusal,
)

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parent
SKILLS = REPO / "skills"
FIXTURES = REPO / "tests" / "fixtures"
CASES_FILE = HARNESS / "routing_cases.toml"
LOG_DIR = REPO / "logs" / "routing"
REPORT_FILE = REPO / "docs" / "skill-routing.md"

NO_ROUTE = "none"
SKILL_PREFIX = "proposal-"
KINDS = ("canonical", "oblique", "collision", "negative")

# Both bounds are judgment, not derivation. Three tolerates the agent glancing at
# a named file before choosing — observed in the 2026-08-10 probes — while still
# ending a run that has wandered off. Ninety seconds is roughly three times the
# slowest observed time-to-first-Skill; a case that exceeds it has not "not
# decided yet", it has failed to decide.
MAX_PREPARATORY_CALLS = 3
CASE_TIMEOUT_S = 90
# rate-limit statuses that mean a call stayed inside the plan: `allowed_warning`
# was recorded at 0.82 weekly utilization (2026-10-04) and is a legitimate state
ALLOWED_RATE_STATUS = ("allowed", "allowed_warning")
# The environment variable a removed override used to name; it is refused now.
ROUTING_OVERRIDE = "ROUTING_CONFIG_DIR"

# What the selector could see when a report was measured. Change it only when
# that changes; an outgoing report that records something else is then
# presented as measured under different conditions, automatically.
ISOLATION_CONDITIONS = ("claude.ai account surfaces closed "
                        "(skill and plugin sync off, connectors off)")

# Uniform, because the assumption behind measuring only the contested cases
# repeatedly did not survive contact: on 2026-08-10 `litsearch-oblique` — an
# ordinary case — failed in the sweep and passed on re-measurement the same
# evening. Any case can be flaky, and a single failure that cannot be told from a
# coin flip is worse than no measurement, because a description edit then gets
# credited with fixing it.
DEFAULT_EPOCHS = 3

# The agent must be able to pick a skill and glance at a file, and must not be
# able to start doing the work. Measured 2026-08-10: `--allowed-tools` alone does
# NOT restrict — a case run with `--allowed-tools Skill Read Glob` under the
# isolated config still executed Bash. The deny list is what actually holds, and
# the kill-on-route is what actually bounds the run; neither is decorative.
ALLOWED_TOOLS = ("Skill", "Read", "Glob")
# Host tools that reach outside the machine: publishing, messaging, scheduling.
# No measured run may use them, whatever the model decides — haiku published
# its own feedback as claude.ai artifacts in a 2026-10-03 dev run that skipped
# permission prompts. The dev runner denies the same list.
OUTWARD_TOOLS = (
    "Artifact", "ArtifactComments", "ArtifactData", "SendMessage", "ListAgents",
    "PushNotification", "RemoteTrigger", "CronCreate", "CronDelete", "ScheduleWakeup",
    "DesignSync",
)
DISALLOWED_TOOLS = ("Bash", "Write", "Edit", "NotebookEdit", "Task", "WebFetch", "WebSearch",
                    *OUTWARD_TOOLS)

# The files a case's utterance may name. Only the ones a given sentence actually
# names are staged for it: staging the union made "my idea" ambiguous in every
# workspace, and on 2026-08-10 the agent answered `litsearch-collision` by asking
# which of three drafts was meant — correct behaviour, scored as a routing
# failure.
WORKSPACE_FIXTURES = (
    ("f05-slr-interviews", "microservice-technical-debt.md"),
    ("f12-clean-de", "typsystem-einheitenfehler.md"),
    ("w01-ideate-seed", "data-drift-detection.md"),
    ("s01-raw-email", "submission-email.txt"),
    ("f27-citation-runs", "dependency-update-breakage.md"),
)

# What a case gets when its utterance names nothing. Not an empty directory: a
# student asking "how do I get this out of markdown" has a proposal, and an empty
# workspace would only trade one clarifying question for another.
DEFAULT_PROPOSAL = "microservice-technical-debt.md"


@dataclass(frozen=True)
class Case:
    id: str
    utterance: str
    expected: str
    kind: str
    lang: str


@dataclass
class Result:
    case_id: str
    expected: str
    kind: str
    route: str | None = None
    error: str | None = None

    @property
    def selected(self) -> str:
        return self.route or NO_ROUTE

    @property
    def passed(self) -> bool:
        return self.error is None and self.selected == self.expected


@dataclass(frozen=True)
class Followed:
    """What `follow_stream` read from one host process: its events, its exit
    status, its stderr, and whether the reader stopped it (`stopped`) or the
    deadline did (`timed_out`)."""

    events: list[dict]
    returncode: int
    stderr: str
    stopped: bool
    timed_out: bool


@dataclass
class Matrix:
    pairs: dict[tuple[str, str], int] = field(default_factory=dict)
    per_kind: dict[str, tuple[int, int]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def totals(self) -> tuple[int, int]:
        passed = sum(p for p, _ in self.per_kind.values())
        total = sum(t for _, t in self.per_kind.values())
        return passed, total


# ---------- dataset ----------------------------------------------------------


def load_cases(path: Path = CASES_FILE) -> list[Case]:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return [
        Case(
            id=c["id"],
            utterance=c["utterance"],
            expected=c["expected"],
            kind=c["kind"],
            lang=c.get("lang", "en"),
        )
        for c in raw["cases"]
    ]


def installed_skills() -> list[str]:
    return sorted(
        d.name for d in SKILLS.iterdir() if d.is_dir() and d.name.startswith(SKILL_PREFIX)
    )


def composition_problems(cases: list[Case], skills: list[str]) -> list[str]:
    """Every skill needs all three positive kinds; negatives and German cases
    must exist; ids unique; expected names a real skill."""
    problems = []
    ids = [c.id for c in cases]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    problems += [f"duplicate case id: {i}" for i in duplicates]

    for case in cases:
        if case.kind not in KINDS:
            problems.append(f"{case.id}: unknown kind {case.kind!r}")
        if case.expected != NO_ROUTE and case.expected not in skills:
            problems.append(f"{case.id}: expected {case.expected!r} is not an installed skill")
        if case.kind == "negative" and case.expected != NO_ROUTE:
            problems.append(f"{case.id}: negative case must expect {NO_ROUTE!r}")

    for skill in skills:
        for kind in ("canonical", "oblique", "collision"):
            if not any(c.expected == skill and c.kind == kind for c in cases):
                problems.append(f"{skill}: no {kind} case")

    if not any(c.kind == "negative" for c in cases):
        problems.append("dataset has no negative cases")
    if not any(c.lang == "de" for c in cases):
        problems.append("dataset has no German cases")
    return problems


# ---------- pure verdict logic ----------------------------------------------


def tool_calls(events: list[dict]) -> list[tuple[str, dict]]:
    """(tool name, input) in order, across assistant messages — then the
    completed items of a Codex stream and the tool events of a Copilot stream
    under the same canonical names (`codex_cli.codex_tool_calls`,
    `copilot_cli.copilot_tool_calls`; the three shapes never collide), so the
    verdicts and the route reader work on every dev-runner host."""
    calls = []
    for event in events:
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                calls.append((block.get("name", ""), block.get("input") or {}))
    return calls + codex_cli.codex_tool_calls(events) + copilot_cli.copilot_tool_calls(events)


def result_event(events: list[dict]) -> dict:
    """The host's closing `result` event, or {} when the run emitted none."""
    return next((e for e in reversed(events) if e.get("type") == "result"), {})


def error_result_reason(events: list[dict]) -> str | None:
    """The host's own account of a run it ended with an error result, or None:
    the subtype, its errors, and the cost and turns so far. Shared by the dev
    runner and the routing rig, which both need the host's words for it."""
    result = result_event(events)
    if not result.get("is_error"):
        return None
    # an expired login arrives as subtype "success" with no `errors` and the
    # reason in `result` (recorded 2026-10-03); without the fallback the
    # message read "success: no detail"
    errors = "; ".join(str(e) for e in result.get("errors") or [])
    if not errors:
        reason = result.get("terminal_reason")
        text = result.get("result") if isinstance(result.get("result"), str) else ""
        errors = " — ".join(part for part in (reason, text) if part) or "no detail"
    return (f"claude failed: {result.get('subtype', 'error')}: {errors} "
            f"(cost so far {result.get('total_cost_usd')} USD, "
            f"{result.get('num_turns')} turns)")


# ---------- billing checks over a stream ------------------------------------------
# Pure, and shared: the dev runner, its judge (`claude_cli`, which imports them
# from here, since it imports this module) and the routing rig hold every
# Claude stream to the same billing checks.


def init_event(events: list[dict]) -> dict:
    """The host's `system/init` event, or {} when the stream carries none."""
    return next((e for e in events
                 if e.get("type") == "system" and e.get("subtype") == "init"), {})


def model_usage(events: list[dict]) -> dict[str, dict]:
    """The result event's per-model usage, keyed by served model ID."""
    usage = result_event(events).get("modelUsage")
    return usage if isinstance(usage, dict) else {}


def version_label(events: list[dict]) -> str:
    """The CLI version for a fail-closed reason: a host change is the usual cause."""
    return init_event(events).get("claude_code_version") or "unknown"


def rate_limit_infos(events: list[dict]) -> list[dict]:
    return [e.get("rate_limit_info") or {} for e in events if e.get("type") == "rate_limit_event"]


def _source_problem(events: list[dict]) -> str | None:
    """The session billed the subscription login through Anthropic's own API.
    The checks are source-free, so the reason names both remedies: an exported
    key or helper, or a login that is not the subscription's."""
    source = init_event(events).get("apiKeySource")
    if source != "none":
        return (f"the session used API-key source {source!r}, not the subscription login "
                "(unset the key or key helper that supplied it, or log in again with the "
                "subscription login — the remedy is never an API key)")
    for model_id, usage in model_usage(events).items():
        provider = (usage or {}).get("provider")
        if provider != "firstParty":
            return (f"{model_id} was served through provider {provider!r}, not Anthropic's "
                    "own API (firstParty)")
    return None


def rate_refusal(events: list[dict]) -> str | None:
    """A rate-limit report that rules the subscription out: overage in use, or
    a status the plan does not allow. Reads only the reports present, so it
    also classifies a run the host ended with an error — a run refused at the
    limit ends that way and is untested, not a runner failure."""
    for info in rate_limit_infos(events):
        if info.get("isUsingOverage"):
            return f"overage in use (rate limit {info.get('rateLimitType')})"
        status = info.get("status")
        if status not in ALLOWED_RATE_STATUS:
            return (f"rate-limit status {status!r} is not one of "
                    f"{', '.join(ALLOWED_RATE_STATUS)}")
    return None


def _unreported(events: list[dict]) -> str:
    return (f"rate limit not reported, overage cannot be ruled out "
            f"(Claude Code {version_label(events)})")


def _flag_problem(events: list[dict]) -> str | None:
    """Every rate-limit report carries its overage flag — a renamed field must
    not read as "no overage"."""
    if any(not isinstance(info.get("isUsingOverage"), bool) for info in rate_limit_infos(events)):
        return (f"rate limit reported without an overage flag, overage cannot be ruled out "
                f"(Claude Code {version_label(events)})")
    return None


def _rate_problem(events: list[dict]) -> str | None:
    """A rate-limit report exists, none shows overage, every one carries its
    overage flag, and every status is one the plan allows. Without a report or
    a flag, "$0" would rest on the account setting alone, so their absence
    fails closed too."""
    if not rate_limit_infos(events):
        return _unreported(events)
    return rate_refusal(events) or _flag_problem(events)


def billing_problem(events: list[dict]) -> str | None:
    """Why a finished stream may not count as a subscription result — the
    source and rate-limit checks the judge and the dev runner's model run share."""
    return _source_problem(events) or _rate_problem(events)


def billing_signals(events: list[dict]) -> list[str]:
    """The explicit billing reasons a stream carries, complete or not: an
    API-key source or a non-first-party provider, and overage in use or a
    refused rate-limit status. Unlike `billing_problem`, an absent report is
    no signal — a run stopped at `init` has none yet — so these can be named
    beside an account surface without inventing a billing problem. The source
    check needs the `init` event and reads nothing without one."""
    source = _source_problem(events) if init_event(events) else None
    return [reason for reason in (source, rate_refusal(events)) if reason]


# The model name the host gives an assistant event it writes itself for a
# failed API call — a dead login among them — with `isApiErrorMessage` set
# (recorded in 2.1.258 session transcripts, 2026-10-03). No model served it.
API_ERROR_MODEL = "<synthetic>"


def model_turns(events: list[dict]) -> list[dict]:
    """The assistant events a model produced: every one but the host's own
    API-error message, which no model served and which carries no rate-limit
    report — a dead login must keep its login remedy, not read as billing."""
    return [e for e in events if e.get("type") == "assistant"
            and not e.get("isApiErrorMessage")
            and (e.get("message") or {}).get("model") != API_ERROR_MODEL]


def case_billing(events: list[dict]) -> str | None:
    """Why a routing case's stream rules the subscription out, or None: an
    explicit billing signal, a rate-limit report without its overage flag, or
    a model turn with no rate-limit report at all, so overage cannot be ruled
    out — the dev runner's checks over the part of the stream the case read.
    A case stopped before any model turn is not held to the report, and
    neither is a case stopped for an account surface: the surface cut its
    read short and errors that case alone (`case_result`), so only a billing
    reason the stream itself shows voids the sweep. A routed case is read on
    for the report (`_case_decided`): 2.1.284 writes one report per run,
    after the routing turn's assistant events, and after a `Skill` call's
    tool result and the skill's instructions (recorded 2026-10-05,
    `route-before-report.jsonl`), so the rig reads past the route to the
    report, the run's result or the next turn's first assistant event;
    stopped at either of the last two, or at the deadline, without one, the
    case is unreported."""
    signals = billing_signals(events)
    if signals:
        return signals[0]
    if rate_limit_infos(events):
        return _flag_problem(events)
    if not model_turns(events) or stream_surfaces(events, isolated=True):
        return None
    return _unreported(events)


def route_from_events(events: list[dict], bound: int = MAX_PREPARATORY_CALLS) -> str | None:
    """First `proposal-*` skill invoked, or None when the case went unrouted.

    Non-skill calls are tolerated up to MAX_PREPARATORY_CALLS, as is an
    invocation of somebody else's skill — neither is our route. A Skill call
    that carries no skill name means the host's output shape changed, which is
    raised rather than silently counted as unrouted.
    """
    for seen, (name, payload) in enumerate(tool_calls(events), start=1):
        if name == "Skill":
            skill = payload.get("skill")
            if not isinstance(skill, str) or not skill:
                raise ValueError(f"Skill tool_use carries no skill name: {payload!r}")
            if skill.startswith(SKILL_PREFIX):
                return skill
        if seen > bound:
            return None
    return None


def case_result(case: Case, events: list[dict], stream_error: str | None,
                source: LoginSource) -> Result:
    """What one measurement means.

    A claude.ai account surface outranks everything, a route included: a
    selection made with the account's synced skills competing is not a
    measurement of the skills under test. Billing other than the subscription
    comes next: a routed case that billed per token is no measurement either,
    and it voids the sweep (`main`). Then a route outranks every error: a host
    that fails after selecting has still selected. Without one, the host's
    error result outranks the stream's error, so a dead login is reported in
    the host's words, with the remedy for the login the sweep used (`source`),
    rather than as "no events" — and never as unrouted, which a negative case
    would count as correct: a sweep run while logged out would otherwise pass
    every negative case and report every other case as not selected.
    """
    result = Result(case_id=case.id, expected=case.expected, kind=case.kind)
    leaks = stream_surfaces(events, isolated=True)
    if leaks:
        result.error = surface_reason(leaks, isolated=True)
        return result
    billing = case_billing(events)
    if billing:
        result.error = f"not a subscription result: {billing}"
        return result
    try:
        result.route = route_from_events(events)
    except ValueError as exc:
        result.error = str(exc)
        return result
    if result.route is None:
        failure = error_result_reason(events)
        result.error = login_remedy(failure, source) if failure else stream_error
    return result


def classify(results: list[Result]) -> Matrix:
    matrix = Matrix()
    for result in results:
        if result.error is not None:
            matrix.errors.append(f"{result.case_id}: {result.error}")
            continue
        key = (result.expected, result.selected)
        matrix.pairs[key] = matrix.pairs.get(key, 0) + 1
        passed, total = matrix.per_kind.get(result.kind, (0, 0))
        matrix.per_kind[result.kind] = (passed + int(result.passed), total + 1)
    return matrix


def misroutes(results: list[Result]) -> list[Result]:
    return [r for r in results if r.error is None and not r.passed]


def void(results: list[Result], reason: str) -> list[Result]:
    """Every result of a sweep turned into an error naming `reason`. What each
    case measured stays in the record — its route, and its own error after the
    voiding reason — so the persisted run log still shows it; an errored
    result counts toward no total (`classify`)."""
    return [replace(r, error=reason if r.error is None else f"{reason} The case's own error: "
                    f"{r.error}") for r in results]


def voided(results: list[Result], leaks: list[SurfaceLeak]) -> list[Result]:
    """Every result of a sweep whose shared configuration holds synced content
    afterwards, voided. The whole sweep, not only the cases after the content
    landed: a case started after it may have loaded it with no tag in its
    stream."""
    return void(results, "synced content in the sweep's configuration voids every case: "
                f"{surface_reason(leaks, isolated=True)}")


class BillingStop:
    """The first billing reason a sweep's cases reported, shared across the
    pool: once set, a case not yet started starts no host. Detection after a
    case is the rig's only billing check, so it stops the rest of the sweep."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reason: str | None = None

    def trip(self, case_id: str, reason: str) -> None:
        with self._lock:
            if self.reason is None:
                self.reason = f"case {case_id} was not a subscription result: {reason}"

    def voiding(self) -> str:
        return (f"a billing signal voids every case of the sweep ({self.reason}); no further "
                "case was started.")


def report_due(matrix: Matrix) -> bool:
    """Whether a run measured anything to report. A run in which every case
    errored would replace the report with 0/0, and the next run would be
    compared against that instead of the last real score."""
    return matrix.totals[1] > 0


def outcome_label(expected: str, selected: str) -> str:
    """A skill that never fired and a skill that stole the utterance are
    different findings, and the fix for each is different: one description is
    too narrow, the other reaches too far."""
    if expected == selected:
        return ""
    return " ← not selected" if selected == NO_ROUTE else " ← mis-routed"


# ---------- report -----------------------------------------------------------


def skills_revision() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD:skills"],
            cwd=REPO, capture_output=True, text=True, timeout=10,
        )
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


SCORE_LINE = re.compile(r"measurements: (\d+) \((\d+) correct\)")
ISOLATION_LINE = re.compile(r"^- isolation: (.+)$", re.MULTILINE)


def previous_score(path: Path = REPORT_FILE) -> str | None:
    """The score the report about to be overwritten was carrying.

    A routing number in isolation says little — the question is always whether a
    description edit moved it. Reading the outgoing report is enough to keep that
    comparison in the artifact instead of in someone's memory.
    """
    if not path.exists():
        return None
    match = SCORE_LINE.search(path.read_text(encoding="utf-8"))
    return f"{match.group(2)}/{match.group(1)}" if match else None


def previous_isolation(path: Path = REPORT_FILE) -> str | None:
    """The isolation conditions the outgoing report records; None when it
    records none, as every report measured before they were recorded."""
    if not path.exists():
        return None
    match = ISOLATION_LINE.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else None


def render_report(results: list[Result], matrix: Matrix, model: str,
                  revision: str | None = None, supersedes: str | None = None,
                  epochs: int = DEFAULT_EPOCHS, conditions_changed: bool = False,
                  isolation: str | None = ISOLATION_CONDITIONS) -> str:
    passed, total = matrix.totals
    earlier = (
        f"- measured under different conditions, not comparable: {supersedes}"
        if conditions_changed else f"- supersedes: {supersedes}"
    ) if supersedes else None
    lines = [
        "# Skill routing",
        "",
        "Which skill the host selector invokes for a user utterance, decided by the "
        "frontmatter descriptions alone. Generated by `uv run poe routing` — see "
        "`harness/README.md`.",
        "",
        f"- model: `{model}`",
        f"- skills revision: `{revision or skills_revision()}`",
        *([f"- isolation: {isolation}"] if isolation else []),
        f"- measurements: {total} ({passed} correct), {epochs} epochs per case",
        *([earlier] if earlier else []),
        "",
        "## Per kind",
        "",
        "| kind | correct | measured |",
        "| --- | --- | --- |",
    ]
    for kind in KINDS:
        if kind in matrix.per_kind:
            kind_passed, kind_total = matrix.per_kind[kind]
            lines.append(f"| {kind} | {kind_passed} | {kind_total} |")

    lines += ["", "## Expected against selected", "",
              "| expected | selected | n |", "| --- | --- | --- |"]
    for (expected, selected), count in sorted(matrix.pairs.items()):
        lines.append(f"| {expected} | {selected}{outcome_label(expected, selected)} | {count} |")

    wrong = misroutes(results)
    lines += ["", "## Wrong outcomes", ""]
    if not wrong:
        lines.append("None.")
    attempts: dict[str, int] = {}
    for result in results:
        if result.error is None:
            attempts[result.case_id] = attempts.get(result.case_id, 0) + 1
    seen: dict[tuple[str, str, str], int] = {}
    for result in wrong:
        key = (result.case_id, result.expected, result.selected)
        seen[key] = seen.get(key, 0) + 1
    for (case_id, expected, selected), count in seen.items():
        lines.append(f"- `{case_id}` expected `{expected}`, selected "
                     f"`{selected}` ({count}/{attempts[case_id]} epochs)")

    if matrix.errors:
        lines += ["", "## Errors", ""] + [f"- {e}" for e in matrix.errors]
    return "\n".join(lines) + "\n"


# ---------- isolated environment --------------------------------------------


def _login_to_link() -> Path:
    """The `.credentials.json` an isolated configuration links: the directory
    `CLAUDE_REAL_CONFIG_DIR` names under the explicit opt-in (labelled, never a
    fallback), else the harness login after its preflight. Never the
    operator's own login because the harness login is missing or refused."""
    opted = os.environ.get(OPT_IN_VAR)
    if opted:
        credentials = Path(opted) / CREDENTIALS
        if not credentials.exists():
            sys.exit(f"no stored login at {credentials}, which {OPT_IN_VAR} names as an "
                     f"explicit opt-in: {RELOGIN} with CLAUDE_CONFIG_DIR={opted}, or unset "
                     f"{OPT_IN_VAR} to use the harness login.")
        return credentials
    problem = host_login.preflight(host_login.CLAUDE)
    if problem:
        sys.exit(refusal(problem))
    credentials = host_login.home(host_login.CLAUDE) / CREDENTIALS
    if not credentials.exists():  # macOS keeps the login in the Keychain
        sys.exit(refusal(LoginProblem(
            f"the harness login home holds no {CREDENTIALS} to link (on macOS the login is a "
            "Keychain entry, not a file)",
            f"use token mode: run `claude setup-token` and export {LONG_LIVED_TOKEN}")))
    return credentials


def prepare_config(base: Path) -> Path:
    """A config directory holding only what the measurement needs.

    A fresh CLAUDE_CONFIG_DIR reports `Not logged in`, because subscription
    credentials live in the config directory. Rather than copy the secret, the
    rig links it — the harness's own login (`host_login`) by default, after its
    preflight — and refuses to run without it, since falling back to the
    ambient configuration would silently measure the operator's own skills,
    hooks and plugins instead of a user's install. A long-lived token from
    `claude setup-token` in the environment needs no link: the child inherits
    it, nothing in the directory can be refreshed or stranded, and the harness
    login is neither checked nor read.

    Account surfaces follow the login, not the directory, so the settings hold
    the claude.ai opt-outs (`account_surfaces.PINNED_SETTINGS`) and the
    directory holds the empty profile directory the child's
    `ANTHROPIC_CONFIG_DIR` names. The removed `ROUTING_CONFIG_DIR` override is
    refused rather than ignored, so nobody believes a prepared directory was
    measured.
    """
    if os.environ.get(ROUTING_OVERRIDE):
        sys.exit(refusal(LoginProblem(
            f"{ROUTING_OVERRIDE} is no longer read: isolated runs prepare their own "
            "configuration and link the harness login",
            f"unset {ROUTING_OVERRIDE}; set the harness login up once with `{LOGIN_COMMAND}`")))
    config = base / "config"
    config.mkdir(parents=True, exist_ok=True)
    (config / SETTINGS_FILE).write_text(json.dumps(dict(PINNED_SETTINGS), indent=2) + "\n",
                                        encoding="utf-8")
    profile_dir(config).mkdir(mode=0o700, exist_ok=True)
    if os.environ.get(LONG_LIVED_TOKEN):
        return config
    credentials = _login_to_link()
    link = config / CREDENTIALS
    if not link.exists():
        link.symlink_to(credentials)
    return config


@contextmanager
def isolated_config(prefix: str) -> Iterator[Path]:
    """A prepared config directory for the duration of a run: the login it
    links is kept current (`host_login.keep_login`, which writes a refresh only
    to the link's target), and the directory is removed afterwards. Every
    configuration is checked before the run: one not closed to the claude.ai
    account surfaces exits with a message naming what is wrong, and the ambient
    configuration is never used instead. So does a run whose children would
    find an Anthropic profile in the default profile directory
    (`account_surfaces.profile_store_problem`); they resolve it from this
    process's environment, as the check does. That check comes first, before
    `prepare_config` starts the harness login's status check."""
    problem = profile_store_problem(os.environ)
    if problem:
        sys.exit(problem)
    with tempfile.TemporaryDirectory(prefix=prefix, ignore_cleanup_errors=True) as tmp:
        config = prepare_config(Path(tmp))
        problem = isolation_problem(config)
        if problem:
            sys.exit(problem)
        with keep_login(config / CREDENTIALS):
            yield config


def files_named(utterance: str) -> list[str]:
    """Fixture filenames the sentence itself names, in order of appearance.

    Derived from the utterance rather than declared per case: a `files` key would
    say the same thing twice and the two would drift, with the drift invisible
    until a case quietly stopped routing.
    """
    stageable = {name for _, name in WORKSPACE_FIXTURES}
    named = []
    for word in utterance.replace("(", " ").replace(")", " ").split():
        token = word.strip(".,;:!?\"'")
        if token.endswith((".md", ".txt")) and token not in named:
            named.append(token)
    unknown = [n for n in named if n not in stageable]
    if unknown:
        raise ValueError(f"utterance names files the suite cannot stage: {unknown}")
    return named


def install_skills(skill_home: Path) -> None:
    """Install the whole set for measurement — without `evals/`: a selector
    that can read assertion text is not choosing from the metadata alone
    (testing-harness spec: Measured environments carry no eval definitions)."""
    skill_home.mkdir(parents=True, exist_ok=True)
    for name in installed_skills():
        shutil.copytree(SKILLS / name, skill_home / name,
                        ignore=shutil.ignore_patterns("evals"))


def stage_workspace(ws: Path, case: Case | None = None) -> None:
    install_skills(ws / ".claude" / "skills")
    wanted = files_named(case.utterance) if case else []
    for filename in wanted or [DEFAULT_PROPOSAL]:
        fixture = next(f for f, name in WORKSPACE_FIXTURES if name == filename)
        shutil.copy2(FIXTURES / fixture / filename, ws / filename)


def _read_events(lines: Iterable[str], events: list[dict],
                 stop: Callable[[list[dict]], bool], timeout: float) -> tuple[bool, bool]:
    """Append each JSON line to `events` until `stop` accepts them or the
    deadline has passed; (stopped, late). A line that is not JSON is skipped
    without a look at either."""
    deadline = time.monotonic() + timeout
    for raw in lines:
        line = raw.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if stop(events):
            return True, False
        if time.monotonic() > deadline:
            return False, True
    return False, False


def _own_group(proc: subprocess.Popen) -> int | None:
    """The process group a followed host leads: on POSIX `follow_stream`
    starts it in one of its own. None elsewhere, and for a stand-in host."""
    pid = getattr(proc, "pid", None)
    if os.name != "posix" or not isinstance(pid, int):
        return None
    try:
        return pid if os.getpgid(pid) == pid else None
    except OSError:
        return None


def _end_group(group: int | None) -> None:
    """Kill what is left of a host's process group once the host is stopped.
    A process the host started that inherited its stdout would otherwise hold
    the read open past the deadline, for as long as that process lives."""
    if group is not None:
        with suppress(ProcessLookupError, PermissionError):
            os.killpg(group, signal.SIGKILL)


def follow_stream(command: Sequence[str], *, cwd: Path, env: Mapping[str, str],
                  timeout: float, stop: Callable[[list[dict]], bool]) -> Followed:
    """Run a host and read its stream-json events as they arrive.

    The host is stopped (`host_login.stop_child`: a termination request, a
    grace, then a kill) at the first event `stop` accepts, so what it
    announced there — a route, or a claude.ai account surface — is not left
    running for the turns after it. A timer stops it at the deadline even when
    it writes nothing; a line that arrives after the deadline stops it too. On
    POSIX the host leads its own process group, and the timer kills what is
    left of the group after the host, so a child holding the host's stdout
    cannot keep the read open past the deadline. stderr goes to a temporary
    file rather than a pipe, so a host that writes a lot there cannot block
    while stdout is read. stdin is closed: with an inherited non-tty stdin the
    host waits for piped input. Shared by the routing rig and the dev runner.
    """
    with tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(
            list(command), cwd=cwd, env=dict(env), stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=err, text=True, encoding="utf-8", errors="replace",
            process_group=0 if os.name == "posix" else None,
        )
        group = _own_group(proc)
        expired = threading.Event()

        def at_deadline() -> None:
            expired.set()
            host_login.stop_child(proc)
            _end_group(group)

        timer = threading.Timer(timeout, at_deadline)
        timer.daemon = True
        timer.start()
        events: list[dict] = []
        stopped = late = False
        try:
            stopped, late = _read_events(proc.stdout or (), events, stop, timeout)
        except BaseException:
            stopped = True  # whatever went wrong, the host does not outlive the reader
            raise
        finally:
            returncode = _settle(proc, timer, stop_host=stopped or late)
        err.seek(0)
        stderr = err.read().decode("utf-8", "replace")
    return Followed(events, returncode, stderr, stopped=stopped,
                    timed_out=late or expired.is_set())


def _settle(proc: subprocess.Popen, timer: threading.Timer, stop_host: bool) -> int:
    """End one followed host: stopped by the harness, or waited for — a host
    that closed its stream exits on its own, and the deadline timer still
    bounds one that does not. Then the timer is retired and stdout closed."""
    if stop_host:
        timer.cancel()
        returncode = host_login.stop_child(proc)
    else:
        returncode = proc.wait()
    timer.cancel()
    timer.join()
    close = getattr(proc.stdout, "close", None)
    if close is not None:  # a stand-in host's stdout may be a plain iterator
        close()
    return returncode


def _message_id(event: dict) -> str | None:
    return (event.get("message") or {}).get("id")


def _routing_event(events: list[dict]) -> dict:
    """The assistant event that carried the route: the first one with which
    the events up to it hold a route."""
    return next((event for at, event in enumerate(events)
                 if event.get("type") == "assistant"
                 and route_from_events(events[:at + 1]) is not None), {})


def _later_turn(events: list[dict]) -> bool:
    """Whether the newest event is an assistant event of a turn after the
    routing one: a message id other than the routing event's. The host starts
    that turn only once the routing turn's response, and its report, ended."""
    newest = events[-1]
    return (newest.get("type") == "assistant"
            and _message_id(newest) != _message_id(_routing_event(events)))


def _case_decided(events: list[dict]) -> bool:
    """The rig's stop condition: a surface in the newest event, or a route
    followed by the first of its rate-limit report, the run's `result`, or the
    next turn's first assistant event. 2.1.284 writes the report once, after
    the routing turn's assistant events; recorded, it came before a `Glob`
    call's result (2026-10-05) and after a `Read` call's (2026-10-04) and the
    routing `Skill` call's (2026-10-05, `route-before-report.jsonl`: its tool
    result, the skill's instructions as a second `user` event, then the
    report, then the next turn); why is inferred (`add-harness-claude-login`
    design, Context). So a routed case reads past the routing turn's `user`
    events and its own later blocks, never past the next turn's first output;
    stopping at the first `user` event voided every `Skill` route
    (`skill-result-unreported.jsonl`). `case_billing` then judges what it read."""
    if stream_surfaces(events[-1:], isolated=True):
        return True
    if route_from_events(events) is None:
        return False
    return (bool(rate_limit_infos(events)) or events[-1].get("type") == "result"
            or _later_turn(events))


def stream_events(ws: Path, config: Path, utterance: str, model: str,
                  timeout: int) -> tuple[list[dict], str | None]:
    """Run one utterance, reading events until a route is decided and its
    rate-limit report read, the run ended or the next turn begun
    (`_case_decided`), or a claude.ai account surface appears, then stop the
    host; the deadline (`timeout`, `CASE_TIMEOUT_S` by default) bounds the
    read either way. On 2.1.284 a `Skill` route's report arrived right after
    the call's tool result and the skill's instructions, 2.2 s into the run,
    and the run's `result` 30 s later, after seven turns in all (recorded
    2026-10-05), so the stop saves the skill run. A surface is the case's
    error (testing-harness spec: Isolated measurement environment). On
    2.1.284 `init` and the command-list changes precede every assistant
    event, so a polluted case costs one process start and no turns."""
    command = [
        "claude", "-p", utterance, "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--allowed-tools", *ALLOWED_TOOLS,
        "--disallowed-tools", *DISALLOWED_TOOLS,
    ]
    env = host_login.allowlisted_env(host_login.CLAUDE, config)
    seen = follow_stream(command, cwd=ws, env=env, timeout=timeout, stop=_case_decided)
    leaks = stream_surfaces(seen.events, isolated=True)
    if leaks:
        return seen.events, surface_reason(leaks, isolated=True)
    if seen.timed_out:
        return seen.events, f"timed out after {timeout}s"
    if not seen.events:
        return seen.events, seen.stderr.strip()[-300:] or "no events"
    return seen.events, None


def measure(case: Case, config: Path, model: str, timeout: int, keep_events: bool,
            stop: BillingStop, source: LoginSource) -> Result:
    """One case: no host is started once an earlier case reported billing."""
    if stop.reason:
        return Result(case_id=case.id, expected=case.expected, kind=case.kind,
                      error=f"not started: {stop.reason}")
    with tempfile.TemporaryDirectory(prefix="routing-") as tmp:
        ws = Path(tmp)
        stage_workspace(ws, case)
        events, error = stream_events(ws, config, case.utterance, model, timeout)
    if keep_events:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        (LOG_DIR / f"events-{case.id}.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    billing = case_billing(events)
    if billing:
        stop.trip(case.id, billing)
    return case_result(case, events, error, source)


# ---------- entry point ------------------------------------------------------


def select_cases(cases: list[Case], args: argparse.Namespace) -> list[Case]:
    if args.case:
        return [c for c in cases if c.id in args.case]
    if args.kind:
        return [c for c in cases if c.kind in args.kind]
    return cases


def epochs_for(_case: Case, override: int | None) -> int:
    return override if override is not None else DEFAULT_EPOCHS


def sweep(work: list[Case], args: argparse.Namespace) -> tuple[list[Result], dict]:
    """Measure every case in one shared isolated configuration, and record the
    login it linked: its kind and its directory, the one place a refresh is
    written back. A billing signal in any case voids the whole sweep, as
    synced content left in the configuration does (testing-harness spec:
    Billing signal in a routing case; Synced content found after a sweep)."""
    stop = BillingStop()
    with (isolated_config("routing-config-") as config,
          ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool):
        source = host_login.login_source(config, os.environ)
        directory = host_login.login_dir(config, os.environ)
        results = list(pool.map(
            lambda c: measure(c, config, args.model, args.timeout, args.keep_events, stop,
                              source), work))
        # before the directory goes: content the background sync wrote
        synced = config_surfaces(config)
    if synced:
        results = voided(results, synced)
    if stop.reason:
        results = void(results, stop.voiding())
    return results, {"login": source.value, "login_dir": str(directory) if directory else None}


def write_report(results: list[Result], matrix: Matrix, args: argparse.Namespace) -> None:
    """Replace the tracked report — unless the run measured nothing, which
    leaves the earlier report and its score standing."""
    if not report_due(matrix):
        print(f"routing: no measurement completed; {REPORT_FILE.name} left unchanged")
        return
    supersedes = previous_score(REPORT_FILE)
    # isolation is a measurement condition recorded in the report itself, so
    # its change needs no one to remember --conditions-changed
    isolation_changed = (supersedes is not None
                         and previous_isolation(REPORT_FILE) != ISOLATION_CONDITIONS)
    REPORT_FILE.write_text(
        render_report(results, matrix, args.model, supersedes=supersedes,
                      epochs=args.epochs or DEFAULT_EPOCHS,
                      conditions_changed=args.conditions_changed or isolation_changed),
        encoding="utf-8")
    print(f"routing: report written to {REPORT_FILE.relative_to(REPO).as_posix()}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="sonnet")
    parser.add_argument("--kind", nargs="+", choices=KINDS)
    parser.add_argument("--case", nargs="+", help="measure only these case ids")
    parser.add_argument("--epochs", type=int, help="override the per-kind epoch count")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=CASE_TIMEOUT_S)
    parser.add_argument("--no-report", action="store_true",
                        help="skip writing docs/skill-routing.md")
    parser.add_argument("--keep-events", action="store_true",
                        help="write each case's raw event stream to logs/routing/ for diagnosis")
    parser.add_argument("--render", type=Path,
                        help="regenerate the report from a saved run log, measuring nothing")
    parser.add_argument("--conditions-changed", action="store_true",
                        help="the rig, not the skills, changed since the last report — "
                             "record the earlier score as not comparable")
    args = parser.parse_args(argv)

    if args.render:
        payload = json.loads(args.render.read_text(encoding="utf-8"))
        results = [Result(**r) for r in payload["results"]]
        REPORT_FILE.write_text(
            render_report(results, classify(results), payload["model"],
                          payload.get("skills_revision"), isolation=payload.get("isolation")),
            encoding="utf-8")
        print("routing: report rebuilt from "
              f"{args.render} into {REPORT_FILE.relative_to(REPO).as_posix()}")
        return 0

    cases = load_cases()
    problems = composition_problems(cases, installed_skills())
    if problems:
        for problem in problems:
            print(f"dataset: {problem}", file=sys.stderr)
        return 2

    selected = select_cases(cases, args)
    if not selected:
        print("no cases selected", file=sys.stderr)
        return 2
    if shutil.which("claude") is None:
        sys.exit("the `claude` binary is not on PATH; the routing rig needs a host install")

    work = [c for c in selected for _ in range(epochs_for(c, args.epochs))]
    print(f"routing: {len(work)} measurements over {len(selected)} cases, model {args.model}")
    results, login = sweep(work, args)

    matrix = classify(results)
    passed, total = matrix.totals
    for result in misroutes(results):
        print(f"  MIS-ROUTE {result.case_id}: expected {result.expected}, got {result.selected}")
    for error in matrix.errors:
        print(f"  ERROR {error}")
    errored = f", {len(matrix.errors)} errored" if matrix.errors else ""
    print(f"routing: {passed}/{total} correct{errored}")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    payload = {
        "model": args.model,
        "skills_revision": skills_revision(),
        "isolation": ISOLATION_CONDITIONS,
        **login,
        "results": [vars(r) for r in results],
    }
    (LOG_DIR / f"{stamp}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if not args.no_report:
        write_report(results, matrix, args)
    # an errored case is no verdict, so it cannot count as a pass either: a
    # sweep in which every case errored totals 0/0
    return 0 if passed == total and not matrix.errors else 1


if __name__ == "__main__":
    sys.exit(main())
