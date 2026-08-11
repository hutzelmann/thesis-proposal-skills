"""L0: audit-invariant tests (skill-packaging spec) — risk patterns remediated in
past security audits stay out of shipped skill content.

Each test names the pattern and the audit that motivated it; see
openspec/changes/archive/2026-08-02-harden-audit-flagged-skills/ and the W007
finding fixed in local-audit-gates.
"""

import re
from pathlib import Path

import publish
import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL_DIRS = sorted(
    d for d in (REPO / "skills").iterdir() if d.is_dir() and d.name.startswith("proposal-")
)
SKILL_MDS = [d / "SKILL.md" for d in SKILL_DIRS]
USER_SCRIPTS = sorted((REPO / "skills").glob("proposal-*/scripts/*.py"))

ids = lambda paths: [p.relative_to(REPO).as_posix() for p in paths]  # noqa: E731


# publish.py invokes fixed document tools (pandoc/typst) by constant name — the
# one accepted subprocess use; Snyk rates the published skill LOW with it.
SUBPROCESS_ALLOWED = {"proposal-publish/scripts/publish.py"}


@pytest.mark.parametrize("script", USER_SCRIPTS, ids=ids(USER_SCRIPTS))
def test_no_dynamic_code_loading(script):
    """Snyk flagged importlib-from-argv as code injection (lit-search HIGH)."""
    text = script.read_text(encoding="utf-8")
    patterns = ["importlib", "__import__", "exec(", "eval(", "os.system"]
    # .as_posix(): SUBPROCESS_ALLOWED holds POSIX keys, so a Windows separator
    # here would silently un-allow publish.py and fail the run.
    if script.relative_to(REPO / "skills").as_posix() not in SUBPROCESS_ALLOWED:
        patterns.append("subprocess")
    for pattern in patterns:
        assert pattern not in text, (
            f"{script.name}: forbidden dynamic-execution pattern `{pattern}`"
        )


@pytest.mark.parametrize("script", USER_SCRIPTS, ids=ids(USER_SCRIPTS))
def test_no_ancestor_directory_traversal(script):
    """Snyk flagged the api-keys.env ancestor walk as insecure credential discovery."""
    text = script.read_text(encoding="utf-8")
    assert ".parents" not in text, (
        f"{script.name}: `.parents` traversal — credential/key lookup must stay in the "
        "documented locations (env, $THESIS_PROPOSAL_KEYS, cwd, global config)"
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=ids(SKILL_MDS))
def test_no_permission_mutation_instructions(skill_md):
    """ATH flagged the chmod/attrib read-only guard as command injection (check)."""
    text = skill_md.read_text(encoding="utf-8")
    assert not re.search(r"\b(chmod|attrib|icacls)\b", text), (
        f"{skill_md.parent.name}: instruction to mutate file permissions"
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=ids(SKILL_MDS))
def test_no_cross_skill_script_execution(skill_md):
    """ATH flagged ideate's `python3 ../proposal-lit-search/scripts/...` line;
    referencing a sibling's SKILL.md or references/ stays allowed."""
    text = skill_md.read_text(encoding="utf-8")
    assert not re.search(r"\.\./proposal-[a-z-]+/scripts/", text), (
        f"{skill_md.parent.name}: executes/addresses another skill's scripts directly"
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=ids(SKILL_MDS))
def test_no_secret_value_through_agent(skill_md):
    """Agent Scan W007: instructing the agent to write a key value verbatim.
    A key name followed by `=` and any value character is the forbidden shape;
    the empty placeholder `KEY=` (user pastes the value) is the allowed one."""
    text = skill_md.read_text(encoding="utf-8")
    assert not re.search(r"[A-Z][A-Z0-9_]*_(KEY|TOKEN|SECRET)=[^`\s]", text), (
        f"{skill_md.parent.name}: shows the agent writing a secret value after `=`"
    )


def test_lit_search_keeps_no_hand_through_rule():
    """Drift guard: the W007 fix's core sentence must survive rewordings."""
    text = (REPO / "skills" / "proposal-lit-search" / "SKILL.md").read_text(encoding="utf-8")
    assert "never read, echo, log, or write the key value" in text
    assert "OPENALEX_API_KEY=` (no value" in text  # placeholder, not a value, is documented


# -- workspace-supplied build (skill-packaging: "Audit-pattern regressions
# caught by tests"). publish.py may start the fixed document tools by constant
# name; it may not start a file it discovered in the user's workspace. A build
# definition is user-authored code, and running it belongs to the agent the
# user already directs, not to a shipped script. Discovery reports, the agent
# executes -- the split is what keeps SUBPROCESS_ALLOWED meaning what it meant
# when Snyk rated the published skill LOW.


@pytest.mark.parametrize("script", USER_SCRIPTS, ids=ids(USER_SCRIPTS))
def test_no_shell_invocation(script):
    text = script.read_text(encoding="utf-8")
    assert "shell=True" not in text, (
        f"{script.name}: subprocess through a shell — arguments must stay a list"
    )


def test_publish_never_executes_a_discovered_build_definition(tmp_path, monkeypatch):
    """Handover must reach no subprocess at all: not the discovered definition,
    and not the built-in pipeline it replaces."""
    proposal = tmp_path / "topic.md"
    proposal.write_text("Body.\n", encoding="utf-8")
    (tmp_path / "proposal-build.py").write_text("raise SystemExit('ran')\n", encoding="utf-8")

    def refuse(*args, **_kwargs):
        raise AssertionError(
            f"publish.py started a subprocess while handing over: {args!r} — a shipped "
            "script must not execute a path it found in the workspace"
        )

    monkeypatch.setattr(publish.subprocess, "run", refuse)
    assert publish.main([str(proposal)]) == publish.HANDOVER_EXIT
