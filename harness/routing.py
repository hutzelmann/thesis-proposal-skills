#!/usr/bin/env python3
"""Routing rig: which skill does the real host selector invoke for an utterance?

Every other harness task hands the agent a skill body and measures what it does
with it. This one measures the step before that: the host reads only the ten
frontmatter descriptions and picks one. The verdict is the first `proposal-*`
Skill invocation observed, after which the run is killed — everything past the
selection is paid noise.

The measurement runs against an isolated CLAUDE_CONFIG_DIR holding exactly the
skills under test, so the number describes a student's install rather than the
developer's machine. It needs the `claude` binary and a logged-in subscription,
which is why it is an on-demand instrument and not part of the L0 chain; the
pure functions below and the dataset's integrity are.

Usage:
  uv run poe routing
  uv run python harness/routing.py --model haiku --kind collision
  uv run python harness/routing.py --case review-canonical --jobs 1
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

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

# The contested cases are the ones whose outcome is genuinely in doubt, so they
# are the only ones worth repeating. Spending epochs uniformly buys repetition of
# cases that were never close.
COLLISION_EPOCHS = 3

# The agent must be able to pick a skill and glance at a file, and must not be
# able to start doing the work. Measured 2026-08-10: `--allowed-tools` alone does
# NOT restrict — a case run with `--allowed-tools Skill Read Glob` under the
# isolated config still executed Bash. The deny list is what actually holds, and
# the kill-on-route is what actually bounds the run; neither is decorative.
ALLOWED_TOOLS = ("Skill", "Read", "Glob")
DISALLOWED_TOOLS = ("Bash", "Write", "Edit", "NotebookEdit", "Task", "WebFetch", "WebSearch")

# Staged into every measurement workspace so utterances can name a real file the
# way a user's would.
WORKSPACE_FIXTURES = (
    ("f05-slr-interviews", "microservice-technical-debt.md"),
    ("f12-clean-de", "typsystem-einheitenfehler.md"),
    ("w01-ideate-seed", "data-drift-detection.md"),
    ("s01-raw-email", "submission-email.txt"),
)


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
    """(tool name, input) in order, across assistant messages."""
    calls = []
    for event in events:
        if event.get("type") != "assistant":
            continue
        for block in event.get("message", {}).get("content", []) or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                calls.append((block.get("name", ""), block.get("input") or {}))
    return calls


def route_from_events(events: list[dict]) -> str | None:
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
        if seen > MAX_PREPARATORY_CALLS:
            return None
    return None


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


def render_report(results: list[Result], matrix: Matrix, model: str,
                  revision: str | None = None) -> str:
    passed, total = matrix.totals
    lines = [
        "# Skill routing",
        "",
        "Which skill the host selector invokes for a user utterance, decided by the "
        "frontmatter descriptions alone. Generated by `uv run poe routing` — see "
        "`harness/README.md`.",
        "",
        f"- model: `{model}`",
        f"- skills revision: `{revision or skills_revision()}`",
        f"- measurements: {total} ({passed} correct)",
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
    seen: dict[tuple[str, str, str], int] = {}
    for result in wrong:
        key = (result.case_id, result.expected, result.selected)
        seen[key] = seen.get(key, 0) + 1
    for (case_id, expected, selected), count in seen.items():
        times = f" ({count}/{COLLISION_EPOCHS} epochs)" if count > 1 else ""
        lines.append(f"- `{case_id}` expected `{expected}`, selected "
                     f"`{selected}`{times}")

    if matrix.errors:
        lines += ["", "## Errors", ""] + [f"- {e}" for e in matrix.errors]
    return "\n".join(lines) + "\n"


# ---------- isolated environment --------------------------------------------


def prepare_config(base: Path) -> Path:
    """A config directory holding only what the measurement needs.

    A fresh CLAUDE_CONFIG_DIR reports `Not logged in`, because subscription
    credentials live in the config directory. Rather than copy the secret, the
    rig links it — and refuses to run without it, since falling back to the
    ambient configuration would silently measure the operator's own skills,
    hooks and plugins instead of a user's install.
    """
    override = os.environ.get("ROUTING_CONFIG_DIR")
    if override:
        return Path(override)

    source = Path(os.environ.get("CLAUDE_REAL_CONFIG_DIR", Path.home() / ".claude"))
    credentials = source / ".credentials.json"
    config = base / "config"
    config.mkdir(parents=True, exist_ok=True)
    (config / "settings.json").write_text("{}\n", encoding="utf-8")

    if not credentials.exists():
        sys.exit(
            f"no credentials at {credentials}. Log in with `claude` first, or point "
            f"ROUTING_CONFIG_DIR at a prepared config directory."
        )
    link = config / ".credentials.json"
    if not link.exists():
        link.symlink_to(credentials)
    return config


def stage_workspace(ws: Path) -> None:
    skill_home = ws / ".claude" / "skills"
    skill_home.mkdir(parents=True, exist_ok=True)
    for name in installed_skills():
        shutil.copytree(SKILLS / name, skill_home / name)
    for fixture, filename in WORKSPACE_FIXTURES:
        source = FIXTURES / fixture / filename
        if source.exists():
            shutil.copy2(source, ws / filename)


def stream_events(ws: Path, config: Path, utterance: str, model: str,
                  timeout: int) -> tuple[list[dict], str | None]:
    """Run one utterance, reading events until a route is decided, then kill."""
    env = dict(os.environ, CLAUDE_CONFIG_DIR=str(config))
    command = [
        "claude", "-p", utterance, "--model", model,
        "--output-format", "stream-json", "--verbose",
        "--allowed-tools", *ALLOWED_TOOLS,
        "--disallowed-tools", *DISALLOWED_TOOLS,
    ]
    proc = subprocess.Popen(
        command, cwd=ws, env=env, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    events: list[dict] = []
    deadline = time.monotonic() + timeout
    error = None
    try:
        for line in proc.stdout:  # type: ignore[union-attr]
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            if route_from_events(events) is not None:
                break
            if time.monotonic() > deadline:
                error = f"timed out after {timeout}s"
                break
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    if not events and error is None:
        error = (proc.stderr.read() or "").strip()[-300:] or "no events"
    return events, error


def measure(case: Case, config: Path, model: str, timeout: int,
            keep_events: bool = False) -> Result:
    result = Result(case_id=case.id, expected=case.expected, kind=case.kind)
    with tempfile.TemporaryDirectory(prefix="routing-") as tmp:
        ws = Path(tmp)
        stage_workspace(ws)
        events, error = stream_events(ws, config, case.utterance, model, timeout)
    if keep_events:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        (LOG_DIR / f"events-{case.id}.jsonl").write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    try:
        result.route = route_from_events(events)
    except ValueError as exc:
        result.error = str(exc)
        return result
    if result.route is None and error:
        result.error = error
    return result


# ---------- entry point ------------------------------------------------------


def select_cases(cases: list[Case], args: argparse.Namespace) -> list[Case]:
    if args.case:
        return [c for c in cases if c.id in args.case]
    if args.kind:
        return [c for c in cases if c.kind in args.kind]
    return cases


def epochs_for(case: Case, override: int | None) -> int:
    if override is not None:
        return override
    return COLLISION_EPOCHS if case.kind == "collision" else 1


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
    args = parser.parse_args(argv)

    if args.render:
        payload = json.loads(args.render.read_text(encoding="utf-8"))
        results = [Result(**r) for r in payload["results"]]
        REPORT_FILE.write_text(
            render_report(results, classify(results), payload["model"],
                          payload.get("skills_revision")), encoding="utf-8")
        print(f"routing: report rebuilt from {args.render} into {REPORT_FILE.relative_to(REPO)}")
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

    with tempfile.TemporaryDirectory(prefix="routing-config-") as tmp:
        config = prepare_config(Path(tmp))
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            results = list(pool.map(
                lambda c: measure(c, config, args.model, args.timeout, args.keep_events), work))

    matrix = classify(results)
    passed, total = matrix.totals
    for result in misroutes(results):
        print(f"  MIS-ROUTE {result.case_id}: expected {result.expected}, got {result.selected}")
    for error in matrix.errors:
        print(f"  ERROR {error}")
    print(f"routing: {passed}/{total} correct")

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    payload = {
        "model": args.model,
        "skills_revision": skills_revision(),
        "results": [vars(r) for r in results],
    }
    (LOG_DIR / f"{stamp}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if not args.no_report:
        REPORT_FILE.write_text(render_report(results, matrix, args.model), encoding="utf-8")
        print(f"routing: report written to {REPORT_FILE.relative_to(REPO)}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
