"""L0: the security-relevant properties of the weekly currency workflows.

Two workflows push a bump branch and open pull requests with the repository's
own token: `model-currency.yml` (the model roster in harness/models.toml) and
`openspec-currency.yml` (the OpenSpec pin in scripts/validate_specs.py). What
they may do is pinned here with one property list: exactly three write
permissions, no secret beyond that token, no model call, no baseline rewrite,
no merge, a fixed bump branch, the checker in write mode with a report check
that fails closed, the branch-handling guards, only the watched file staged,
and CI dispatched on the bump branch. Narrow text extraction only — no YAML
parser (the skills' scripts may not use one, and this test needs none).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pytest
from helpers import REPO

WORKFLOWS = REPO / ".github" / "workflows"
PERMISSIONS = {"contents": "write", "pull-requests": "write", "actions": "write"}
FORBIDDEN = ("--yes", "poe matrix", "inspect eval", "poe smoke", "OPENROUTER",
             "--update-baseline", "gh pr merge")
# the lines that keep a maintainer's commit on the bump branch from being
# overwritten (model-currency review follow-up 2026-10-05)
GUARDS = (
    # the lease is the commit that was inspected, not a later ls-remote read
    'expected=$(git rev-parse -q --verify "refs/remotes/origin/$BRANCH" || true)',
    'git log "origin/main..$expected"',
    '--force-with-lease="refs/heads/$BRANCH:$expected"',
    # the others-check runs whatever the PR state; only a merged tip is rebuilt
    "--state merged",
)


@dataclass(frozen=True)
class Weekly:
    file: str
    branch: str
    checker: str  # the write-mode run, with plain python3
    report_guard: str  # a crash exits like a finding: only a parsed report is a verdict
    watched: str  # the one file a bump changes

    def text(self) -> str:
        return (WORKFLOWS / self.file).read_text(encoding="utf-8")


WEEKLIES = (
    Weekly("model-currency.yml", "model-currency/bump",
           "python3 harness/model_currency.py --write --json",
           """jq -e '(.findings | type == "array") and (.alerts | type == "array")'""",
           "harness/models.toml"),
    Weekly("openspec-currency.yml", "openspec-currency/bump",
           "python3 scripts/openspec_currency.py --write --json",
           """jq -e '(.status | type == "string") and (.warnings | type == "array")'""",
           "scripts/validate_specs.py"),
)
weeklies = pytest.mark.parametrize("weekly", WEEKLIES, ids=lambda w: w.file)


def _uncommented(text: str) -> list[str]:
    return [line.split(" #", 1)[0].rstrip() for line in text.splitlines()
            if not line.lstrip().startswith("#")]


def top_level_block(text: str, key: str) -> list[str]:
    """The indented lines under a top-level `key:` (comments dropped)."""
    lines = _uncommented(text)
    try:
        start = lines.index(f"{key}:")
    except ValueError:
        return []
    block = []
    for line in lines[start + 1:]:
        if line and not line.startswith(" "):
            break
        if line.strip():
            block.append(line)
    return block


def _token_problems(text: str, lines: list[str]) -> list[str]:
    problems = []
    permissions = dict(
        line.strip().split(": ", 1) for line in top_level_block(text, "permissions")
    )
    if permissions != PERMISSIONS:
        problems.append(f"permissions are {permissions}, expected exactly {PERMISSIONS}")
    if sum(line.strip() == "permissions:" for line in lines) != 1:
        problems.append("a second permissions block widens or narrows a job")
    secrets = set(re.findall(r"secrets\.(\w+)", text))
    if secrets - {"GITHUB_TOKEN"}:
        problems.append(f"reads secrets beyond the built-in token: {sorted(secrets)}")
    triggers = {line.strip().rstrip(":") for line in top_level_block(text, "on")
                if line.startswith("  ") and not line.startswith("    ")}
    if triggers != {"schedule", "workflow_dispatch"}:
        problems.append(f"triggers are {sorted(triggers)}, expected schedule + workflow_dispatch")
    return problems


def _bump_problems(weekly: Weekly, text: str, lines: list[str]) -> list[str]:
    problems = []
    if f"BRANCH: {weekly.branch}" not in text:
        problems.append(f"the bump branch is not the fixed {weekly.branch}")
    if 'gh workflow run ci.yml --ref "$BRANCH"' not in text:
        problems.append("CI is not dispatched on the bump branch")
    if weekly.checker not in text:
        problems.append("the checker does not run in write mode with plain python3")
    if weekly.report_guard not in text:
        problems.append(f"guard missing: {weekly.report_guard!r}")
    staged = [line.strip() for line in lines if line.strip().startswith("git add")]
    if staged != [f"git add {weekly.watched}"]:
        problems.append(f"stages {staged}, expected only {weekly.watched}")
    if f"git diff --quiet -- {weekly.watched}" not in text:
        problems.append(f"the change is not decided by {weekly.watched}")
    return problems


def workflow_problems(weekly: Weekly, text: str) -> list[str]:
    lines = _uncommented(text)
    problems = _token_problems(text, lines) + _bump_problems(weekly, text, lines)
    problems += [f"forbidden: {word!r}" for word in FORBIDDEN if word in "\n".join(lines)]
    problems += [f"guard missing: {guard!r}" for guard in GUARDS if guard not in text]
    if '[ -n "$pr" ] && [ -n "$expected" ]' in text:
        problems.append("the others-check is gated on an open pull request")
    return problems


@weeklies
def test_the_workflow_keeps_its_security_properties(weekly):
    assert workflow_problems(weekly, weekly.text()) == []


@weeklies
@pytest.mark.parametrize(("addition", "problem"), [
    ("      - run: echo ${{ secrets.OPENROUTER_API_KEY }}\n", "secrets beyond"),
    ("      - run: uv run poe matrix --yes\n", "forbidden"),
    ("      - run: python3 scripts/validate_specs.py --update-baseline\n", "forbidden"),
    ('      - run: gh pr merge "$pr" --squash\n', "forbidden"),
])
def test_the_pin_catches_a_widened_workflow(weekly, addition, problem):
    widened = weekly.text() + addition
    assert any(problem in p for p in workflow_problems(weekly, widened))


@weeklies
def test_the_pin_catches_an_extra_permission(weekly):
    text = weekly.text().replace("permissions:\n", "permissions:\n  id-token: write\n", 1)
    assert any("permissions are" in p for p in workflow_problems(weekly, text))


@weeklies
@pytest.mark.parametrize("staging", ["git add -A", "git add .", "git add openspec/"])
def test_the_pin_catches_staging_more_than_the_watched_file(weekly, staging):
    text = weekly.text().replace(f"git add {weekly.watched}", staging)
    assert any("stages" in p for p in workflow_problems(weekly, text))


@weeklies
@pytest.mark.parametrize(("old", "new", "problem"), [
    # the first version: no report check, so a crash closed the PR as "current"
    ("report_guard", "false", "guard missing"),
    # the first version: the lease read after the inspection, so a push in between was lost
    ('expected=$(git rev-parse -q --verify "refs/remotes/origin/$BRANCH" || true)',
     'expected=$(git ls-remote --heads origin "$BRANCH" | cut -f1)', "guard missing"),
    # the first version: maintainer commits were protected only while a PR was open
    ('if [ -n "$expected" ]; then', 'if [ -n "$pr" ] && [ -n "$expected" ]; then',
     "gated on an open pull request"),
])
def test_the_pin_catches_the_first_versions_branch_handling(weekly, old, new, problem):
    old = f"! {weekly.report_guard}" if old == "report_guard" else old
    text = weekly.text()
    assert text.count(old) == 1, f"workflow drifted: {old!r}"
    assert any(problem in p for p in workflow_problems(weekly, text.replace(old, new)))


def test_ci_accepts_the_dispatch():
    """GITHUB_TOKEN pull requests trigger no pull_request run; the currency
    workflows can start CI only because ci.yml declares workflow_dispatch."""
    triggers = top_level_block((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"), "on")
    assert "  workflow_dispatch:" in triggers


def test_ci_runs_the_spec_gate_through_its_task():
    """The bump pull request's CI run is what shows a new version's findings."""
    lines = _uncommented((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
    assert any(line.strip() == "run: uv run poe specs" for line in lines)


def rewrites_baseline(text: str) -> bool:
    return "--update-baseline" in "\n".join(_uncommented(text))


def test_no_workflow_rewrites_the_baseline():
    """CI SHALL NOT rewrite the long-requirement baseline: not the weekly bump,
    and not ci.yml, the workflow that runs the gate."""
    workflows = sorted(WORKFLOWS.glob("*.yml"))
    assert "ci.yml" in [w.name for w in workflows]
    assert [w.name for w in workflows if rewrites_baseline(w.read_text(encoding="utf-8"))] == []


def test_the_baseline_check_catches_a_ci_step():
    text = (WORKFLOWS / "ci.yml").read_text(encoding="utf-8")
    assert rewrites_baseline(text + "      - run: python3 scripts/validate_specs.py "
                                    "--update-baseline\n")
