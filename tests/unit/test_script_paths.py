"""L0: documented script invocations use the host's skill-directory variable.

The old workspace-root form (`.claude/skills/<skill>/scripts/…`) silently broke
on any non-standard install; `${CLAUDE_SKILL_DIR}` resolves everywhere the host
substitutes it, and every fallback paragraph rescues the hosts that don't
(skill-packaging spec: User-side script constraints)."""

from __future__ import annotations

import re

import pytest
from helpers import REPO

SKILL_MDS = sorted(REPO.glob("skills/proposal-*/SKILL.md"))
SCRIPT_BEARING = sorted(
    md for md in SKILL_MDS if (md.parent / "scripts").is_dir()
)


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_no_workspace_root_path_to_any_skills_scripts(skill_md):
    """No skill addresses scripts by an install path. A script another skill
    owns ships as a synchronized copy and is run through the variable like any
    own script: `.claude/skills/<sibling>/…` broke under user-level and plugin
    installs, and `${CLAUDE_SKILL_DIR}/../<sibling>/scripts/` is the `../`
    cross-skill execution shape the audit invariants forbid
    (test_no_cross_skill_script_execution; change desktop-first-install)."""
    assert ".claude/skills/proposal-" not in skill_md.read_text(encoding="utf-8")


@pytest.mark.parametrize("skill_md", SCRIPT_BEARING, ids=lambda p: p.parent.name)
def test_script_invocations_use_the_variable(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    bare = re.findall(r"python3 (?!\$\{CLAUDE_SKILL_DIR\})\S*scripts/\S+", text)
    assert not bare, f"script invocation without ${{CLAUDE_SKILL_DIR}}: {bare}"
    assert "${CLAUDE_SKILL_DIR}/scripts/" in text


@pytest.mark.parametrize("skill_md", SCRIPT_BEARING, ids=lambda p: p.parent.name)
def test_fallback_prose_names_the_unexpanded_case(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    assert "leaves it unexpanded" in text, "fallback for non-substituting hosts missing"
    assert "next to this SKILL.md" in text


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_fallback_prose_does_not_relocate_the_work(skill_md):
    """The fallback resolves a script path, never a place to work from:
    "so use that location" sent agents into the install directory, misplacing
    CWD-dependent output (skill-packaging spec: User-side script constraints,
    change 2026-08-31-fix-import-output-location)."""
    assert "so use that location" not in skill_md.read_text(encoding="utf-8")


# the one statement of what `python3` stands for (design D13 of
# desktop-first-install); its core is pinned here, not materialized, because the
# paragraph it joins is worded per skill
INTERPRETER_CLAUSE = (
    "`python3` stands for any Python 3.11 or newer that answers here (`python`, "
    "`py -3`, or a versioned name such as `python3.13`); keep the one that worked "
    "for the rest of the conversation."
)


@pytest.mark.parametrize("skill_md", SCRIPT_BEARING, ids=lambda p: p.parent.name)
def test_interpreter_clause_once_in_the_fallback_paragraph(skill_md):
    """Every script-bearing skill says once, where the agent reads how to run a
    script, what `python3` stands for (skill-packaging spec: User-side script
    constraints)."""
    text = skill_md.read_text(encoding="utf-8")
    assert text.count(INTERPRETER_CLAUSE) == 1, "interpreter clause missing or repeated"
    fallback = [p for p in text.split("\n\n") if "leaves it unexpanded" in p]
    assert len(fallback) == 1, "expected one unexpanded-variable fallback paragraph"
    assert INTERPRETER_CLAUSE in fallback[0], (
        "the clause belongs in the paragraph that holds the unexpanded-variable fallback")


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_no_scattered_interpreter_hints(skill_md):
    """Per-command Windows hints and a version-pinned Python install command gave
    way to the one clause and a link to the install guide."""
    text = skill_md.read_text(encoding="utf-8")
    assert not re.search(r"`py`\s+(?:instead of|if)\s+`python3`", text), "per-command py hint"
    assert not re.search(r"use `py` instead of `python3`", text), "per-command py hint"
    assert "winget install Python" not in text
    assert "brew install python" not in text


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_no_skill_names_a_host_instruction_file(skill_md):
    """No skill tells the agent to record the interpreter in a host's instruction
    file: that is persistent host configuration, and not portable."""
    text = skill_md.read_text(encoding="utf-8")
    assert "AGENTS.md" not in text
    assert "CLAUDE.md" not in text
