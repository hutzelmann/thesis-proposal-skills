"""L0: documented script invocations use the host-neutral `<skill-dir>` placeholder.

The old workspace-root form (`.claude/skills/<skill>/scripts/…`) silently broke
on any non-standard install, and `${CLAUDE_SKILL_DIR}` resolved only on the one
host that substitutes it: every other host handed its shell an unset variable.
Hosts name the skill's directory when they load a skill, so each script-bearing
skill defines `<skill-dir>` once and the model fills it in like `<location>`
(skill-packaging spec: User-side script constraints; change
host-neutral-script-paths)."""

from __future__ import annotations

import re

import pytest
from helpers import REPO

SKILL_MDS = sorted(REPO.glob("skills/proposal-*/SKILL.md"))
SCRIPT_BEARING = sorted(
    md for md in SKILL_MDS if (md.parent / "scripts").is_dir()
)
PLACEHOLDER = "<skill-dir>/scripts/"
# the fixed opening of the one paragraph that defines the placeholder (design D2)
DEFINITION = "`<skill-dir>` stands for this skill's own folder"
# a host's substitution variable, `${NAME}` or a `$NAME/scripts/` prefix
HOST_VARIABLE = re.compile(r"\$\{[A-Za-z_]\w*\}|\$[A-Za-z_]\w*/scripts/")


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_no_workspace_root_path_to_any_skills_scripts(skill_md):
    """No skill addresses scripts by an install path. A script another skill
    owns ships as a synchronized copy and is run through `<skill-dir>` like any
    own script: `.claude/skills/<sibling>/…` broke under user-level and plugin
    installs, and `<skill-dir>/../<sibling>/scripts/` is the `../` cross-skill
    execution shape the audit invariants forbid
    (test_no_cross_skill_script_execution; change desktop-first-install)."""
    assert ".claude/skills/proposal-" not in skill_md.read_text(encoding="utf-8")


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_no_host_substitution_variable(skill_md):
    """No skill relies on one host's syntax. Claude Code substitutes
    `${CLAUDE_SKILL_DIR}` even inside prose that only names it, and no other
    host substitutes it at all."""
    found = HOST_VARIABLE.findall(skill_md.read_text(encoding="utf-8"))
    assert not found, f"host substitution variable in a shipped skill: {found}"


@pytest.mark.parametrize("skill_md", SCRIPT_BEARING, ids=lambda p: p.parent.name)
def test_script_invocations_use_the_placeholder(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    other = re.findall(r"python3 (?!<skill-dir>/scripts/)\S*scripts/\S+", text)
    assert not other, f"script invocation without {PLACEHOLDER}: {other}"
    assert PLACEHOLDER in text


@pytest.mark.parametrize("skill_md", SCRIPT_BEARING, ids=lambda p: p.parent.name)
def test_placeholder_defined_once(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    assert text.count(DEFINITION) == 1, "`<skill-dir>` definition missing or repeated"
    assert "holding this SKILL.md" in fallback_paragraph(skill_md), (
        "the definition does not say which folder `<skill-dir>` is")


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
    assert INTERPRETER_CLAUSE in fallback_paragraph(skill_md), (
        "the clause belongs in the paragraph that defines `<skill-dir>`")


# the six skills that ship the check (design D13 of adopt-proposal-folders)
CHECK_BEARING = sorted(
    md for md in SKILL_MDS if (md.parent / "scripts" / "check.py").is_file()
)
# the scripts whose argument is the proposal file
PROPOSAL_SCRIPTS = ("check", "validate_refs", "publish", "collect")
FOLDER_PATH = "<location>/<slug>/<slug>.md"


def test_six_skills_ship_the_check():
    assert [md.parent.name for md in CHECK_BEARING] == [
        "proposal-check", "proposal-import", "proposal-reverse", "proposal-supervise",
        "proposal-troubleshoot", "proposal-write"]


@pytest.mark.parametrize("skill_md", CHECK_BEARING, ids=lambda p: p.parent.name)
def test_the_fallback_names_the_workspace_root_stake(skill_md):
    """The check measures placement and orphan findings from the working
    directory, so a skill shipping it names that stake beside its fallback:
    the command runs from the workspace root (skill-packaging: User-side script
    constraints; design D13, D17 of adopt-proposal-folders)."""
    fallback = fallback_paragraph(skill_md)
    assert "workspace root" in fallback, "the fallback does not say where the command runs"
    assert "placement" in fallback, "the fallback does not say why the root matters"


def fallback_paragraph(skill_md) -> str:
    """The one paragraph that defines `<skill-dir>` and says where commands run."""
    text = skill_md.read_text(encoding="utf-8")
    paragraphs = [p for p in text.split("\n\n") if DEFINITION in p]
    assert len(paragraphs) == 1, "expected one paragraph defining `<skill-dir>`"
    return paragraphs[0]


def proposal_arguments(skill_md) -> list[str]:
    pattern = rf"scripts/(?:{'|'.join(PROPOSAL_SCRIPTS)})\.py (\S+)"
    return re.findall(pattern, skill_md.read_text(encoding="utf-8"))


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_proposal_arguments_name_the_folder(skill_md):
    """Every documented command that takes the proposal names it as it lies in
    its folder, as a path from the workspace root, and the fallback paragraph
    says what `<location>` stands for (design D13 of adopt-proposal-folders)."""
    arguments = proposal_arguments(skill_md)
    wrong = [arg for arg in arguments if arg != FOLDER_PATH]
    assert not wrong, f"proposal argument not {FOLDER_PATH}: {wrong}"
    if arguments:
        assert "`<location>`" in fallback_paragraph(skill_md), (
            "the fallback does not say what `<location>` stands for")


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
