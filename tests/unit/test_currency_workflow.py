"""L0: the security-relevant properties of the weekly model-currency workflow.

The workflow pushes a branch and opens pull requests with the repository's own
token, so what it may do is pinned here: exactly three write permissions, no
secret beyond that token, no model call, and CI dispatched on the bump branch.
Narrow text extraction only — no YAML parser (the skills' scripts may not use
one, and this test needs none).
"""

from __future__ import annotations

import re

import pytest
from helpers import REPO

WORKFLOWS = REPO / ".github" / "workflows"
CURRENCY = WORKFLOWS / "model-currency.yml"
PERMISSIONS = {"contents": "write", "pull-requests": "write", "actions": "write"}
FORBIDDEN = ("--yes", "poe matrix", "inspect eval", "poe smoke", "OPENROUTER")
# the lines that keep a crash from passing as "current" and a maintainer's
# commit on the bump branch from being overwritten (review follow-up 2026-10-05)
GUARDS = (
    # a crash exits 1 like a run with findings: only a parsed report is a verdict
    """jq -e '(.findings | type == "array") and (.alerts | type == "array")'""",
    # the lease is the commit that was inspected, not a later ls-remote read
    'expected=$(git rev-parse -q --verify "refs/remotes/origin/$BRANCH" || true)',
    'git log "origin/main..$expected"',
    '--force-with-lease="refs/heads/$BRANCH:$expected"',
    # the others-check runs whatever the PR state; only a merged tip is rebuilt
    "--state merged",
)


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


def workflow_problems(text: str) -> list[str]:
    problems = []
    lines = _uncommented(text)
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
    if "BRANCH: model-currency/bump" not in text:
        problems.append("the bump branch is not the fixed model-currency/bump")
    if 'gh workflow run ci.yml --ref "$BRANCH"' not in text:
        problems.append("CI is not dispatched on the bump branch")
    if "python3 harness/model_currency.py --write --json" not in text:
        problems.append("the checker does not run in write mode with plain python3")
    problems += [f"forbidden: {word!r}" for word in FORBIDDEN if word in "\n".join(lines)]
    problems += [f"guard missing: {guard!r}" for guard in GUARDS if guard not in text]
    if '[ -n "$pr" ] && [ -n "$expected" ]' in text:
        problems.append("the others-check is gated on an open pull request")
    return problems


def test_currency_workflow_keeps_its_security_properties():
    assert workflow_problems(CURRENCY.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(("addition", "problem"), [
    ("      - run: echo ${{ secrets.OPENROUTER_API_KEY }}\n", "secrets beyond"),
    ("      - run: uv run poe matrix --yes\n", "forbidden"),
])
def test_the_pin_catches_a_widened_workflow(addition, problem):
    widened = CURRENCY.read_text(encoding="utf-8") + addition
    assert any(problem in p for p in workflow_problems(widened))


def test_the_pin_catches_an_extra_permission():
    text = CURRENCY.read_text(encoding="utf-8").replace(
        "permissions:\n", "permissions:\n  id-token: write\n", 1)
    assert any("permissions are" in p for p in workflow_problems(text))


@pytest.mark.parametrize(("old", "new", "problem"), [
    # the first version: no report check, so a crash closed the PR as "current"
    ("""! jq -e '(.findings | type == "array") and (.alerts | type == "array")'""",
     "false", "guard missing"),
    # the first version: the lease read after the inspection, so a push in between was lost
    ('expected=$(git rev-parse -q --verify "refs/remotes/origin/$BRANCH" || true)',
     'expected=$(git ls-remote --heads origin "$BRANCH" | cut -f1)', "guard missing"),
    # the first version: maintainer commits were protected only while a PR was open
    ('if [ -n "$expected" ]; then', 'if [ -n "$pr" ] && [ -n "$expected" ]; then',
     "gated on an open pull request"),
])
def test_the_pin_catches_the_first_versions_branch_handling(old, new, problem):
    text = CURRENCY.read_text(encoding="utf-8")
    assert text.count(old) == 1, f"workflow drifted: {old!r}"
    assert any(problem in p for p in workflow_problems(text.replace(old, new)))


def test_ci_accepts_the_dispatch():
    """GITHUB_TOKEN pull requests trigger no pull_request run; the currency
    workflow can start CI only because ci.yml declares workflow_dispatch."""
    triggers = top_level_block((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"), "on")
    assert "  workflow_dispatch:" in triggers
