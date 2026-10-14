"""L0: the two-branch model in the repository's automation and contributor docs.

`main` holds releases and is what every installer fetches; completed work lands
on `develop` (skill-packaging spec: Rolling release policy). CI and the install
check therefore run on pushes to both branches, so work on `develop` is tested
before a release moves `main`. Narrow text extraction only, no YAML parser.
"""

from __future__ import annotations

import re

import pytest
from helpers import REPO

WORKFLOWS = REPO / ".github" / "workflows"
# the inline form every workflow here uses: `on:` / `  push:` / `    branches: [...]`
PUSH_BRANCHES_RE = re.compile(r"^  push:\n    branches: \[([^\]\n]*)\]$", re.MULTILINE)


def push_branches(text: str) -> list[str]:
    """A workflow's `on.push.branches`, or [] when it has no such inline list."""
    match = PUSH_BRANCHES_RE.search(text)
    return [] if match is None else [b.strip() for b in match.group(1).split(",")]


@pytest.mark.parametrize("workflow", ["ci.yml", "install.yml"])
def test_the_workflow_runs_on_pushes_to_both_branches(workflow):
    text = (WORKFLOWS / workflow).read_text(encoding="utf-8")
    assert sorted(push_branches(text)) == ["develop", "main"]


def test_the_extraction_sees_a_main_only_trigger():
    assert push_branches("on:\n  push:\n    branches: [main]\n  schedule:\n") == ["main"]


def readme_contributors() -> str:
    text = (REPO / "README.md").read_text(encoding="utf-8")
    start = text.index("\n## For contributors")
    end = text.find("\n## ", start + 1)
    return text[start:] if end == -1 else text[start:end]


# GitHub proposes the default branch, main, as a pull request's base; the docs
# a contributor reads say to target develop instead
CONTRIBUTOR_DOCS = {
    "README For contributors": readme_contributors,
    "CONTRIBUTING.md": lambda: (REPO / "CONTRIBUTING.md").read_text(encoding="utf-8"),
    "PR template": lambda: (REPO / ".github" / "PULL_REQUEST_TEMPLATE.md").read_text(
        encoding="utf-8"),
}
TARGETS_DEVELOP_RE = re.compile(r"\btargets? `develop`")


@pytest.mark.parametrize("doc", CONTRIBUTOR_DOCS)
def test_contributor_docs_name_develop_as_the_target(doc):
    assert TARGETS_DEVELOP_RE.search(CONTRIBUTOR_DOCS[doc]()), doc


@pytest.mark.parametrize("doc", ["README For contributors", "CONTRIBUTING.md"])
def test_contributor_docs_say_main_stays_the_default_branch(doc):
    text = CONTRIBUTOR_DOCS[doc]()
    assert "default branch" in text, doc
    assert "`main`" in text, doc
