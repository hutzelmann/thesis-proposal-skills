"""L0: the security-relevant properties of the weekly currency workflows.

Two workflows push a bump branch and open pull requests with the repository's
own token: `model-currency.yml` (the model roster in harness/models.toml) and
`openspec-currency.yml` (the OpenSpec pin in scripts/validate_specs.py). What
they may do is pinned here with one property list: exactly three write
permissions, no secret beyond that token, no model call, no baseline rewrite,
no merge, a fixed bump branch, the checker in write mode with a report check
that fails closed, the branch-handling guards, only the watched file staged,
and CI started on the bump branch: GitHub holds the pull_request runs of a pull
request github-actions[bot] opens or pushes to, so the workflow approves the held
runs of the commit it pushed and dispatches CI only as the fallback
(approve-bump-ci-runs). The check runs on `develop` and the pull
request targets it, since `main` only ever fast-forwards to a release; an update
moves an open pull request's base there too (finish-two-branch-flow). Narrow
text extraction only — no YAML parser (the
skills' scripts may not use one, and this test needs none).
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
# the integration branch: the check runs on it and the bump pull request targets it
BASE = "develop"
# the lines that keep a maintainer's commit on the bump branch from being
# overwritten (model-currency review follow-up 2026-10-05)
GUARDS = (
    # the lease is the commit that was inspected, not a later ls-remote read
    'expected=$(git rev-parse -q --verify "refs/remotes/origin/$BRANCH" || true)',
    # commits already on the base are nobody else's: the range starts there
    f'git log "origin/{BASE}..$expected"',
    '--force-with-lease="refs/heads/$BRANCH:$expected"',
    # the others-check runs whatever the PR state; only a merged tip is rebuilt
    "--state merged",
)
# the held CI runs the workflow approves: those of the commit it just pushed,
# nothing older and nothing it did not cause (approve-bump-ci-runs D2)
APPROVAL = (
    ("sha=$(git rev-parse HEAD)", "the pushed commit is not recorded"),
    ('--workflow ci.yml --event pull_request --commit "$sha"',
     "held runs are not looked up for the pushed commit"),
    ("""select(.conclusion == "action_required")""", "held runs are not selected"),
    ('"repos/$GITHUB_REPOSITORY/actions/runs/$id/approve"', "held CI runs are not approved"),
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
    problems += [problem for needle, problem in APPROVAL if needle not in text]
    if 'gh workflow run ci.yml --ref "$BRANCH"' not in text:
        problems.append("CI is not dispatched on the bump branch as the fallback")
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


def _base_problems(lines: list[str]) -> list[str]:
    problems = []
    if not any(line.strip() == f"ref: {BASE}" for line in lines):
        problems.append(f"the check does not run on {BASE}")
    joined = "\n".join(lines)
    bases = re.findall(r"gh pr create --base (\S+)", joined)
    if bases != [BASE]:
        problems.append(f"opens its pull request against {bases}, expected one against {BASE}")
    # an open bump pull request may predate the two-branch model and target main;
    # rebuilt from develop and left there, it would carry unreleased work to main
    retargets = [base or "(kept)"
                 for base in re.findall(r'gh pr edit "\$pr"(?: --base (\S+))?', joined)]
    if retargets != [BASE]:
        problems.append(f"updates its open pull request with base {retargets}, "
                        f"expected one update that moves it to {BASE}")
    return problems


def workflow_problems(weekly: Weekly, text: str) -> list[str]:
    lines = _uncommented(text)
    problems = _token_problems(text, lines) + _bump_problems(weekly, text, lines)
    problems += _base_problems(lines)
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


@weeklies
@pytest.mark.parametrize(("old", "new", "problem"), [
    # before the two-branch model: the check ran on main and the PR targeted it
    (f"gh pr create --base {BASE}", "gh pr create --base main", "pull request against"),
    (f"ref: {BASE}", "ref: main", f"does not run on {BASE}"),
    # with main as the range start, unreleased commits on develop count as others'
    (f'git log "origin/{BASE}..$expected"', 'git log "origin/main..$expected"', "guard missing"),
    # an update that keeps the base: a pull request the old workflow opened stays on main
    (f'gh pr edit "$pr" --base {BASE}', 'gh pr edit "$pr"', "open pull request with base"),
    (f'gh pr edit "$pr" --base {BASE}', 'gh pr edit "$pr" --base main',
     "open pull request with base"),
])
def test_the_pin_catches_a_bump_aimed_at_main(weekly, old, new, problem):
    text = weekly.text()
    assert text.count(old) == 1, f"workflow drifted: {old!r}"
    assert any(problem in p for p in workflow_problems(weekly, text.replace(old, new)))


@weeklies
@pytest.mark.parametrize(("old", "new", "problem"), [
    # the first version: CI dispatched only, so held runs stayed and no check reached the PR
    ('"repos/$GITHUB_REPOSITORY/actions/runs/$id/approve"', '"$id"', "not approved"),
    # every held run of the branch, older pushes included
    ('--event pull_request --commit "$sha"', "--event pull_request", "pushed commit"),
])
def test_the_pin_catches_a_weakened_approval(weekly, old, new, problem):
    text = weekly.text()
    assert text.count(old) == 1, f"workflow drifted: {old!r}"
    assert any(problem in p for p in workflow_problems(weekly, text.replace(old, new)))


@weeklies
def test_the_pin_catches_a_second_pull_request(weekly):
    text = weekly.text() + "      - run: gh pr create --base develop --head other\n"
    assert any("pull request against" in p for p in workflow_problems(weekly, text))


def test_ci_accepts_the_dispatch():
    """When no held run can be approved, the currency workflows fall back to
    dispatching CI, which works only because ci.yml declares workflow_dispatch."""
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
