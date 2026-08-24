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
def test_no_workspace_root_path_to_a_skills_own_scripts(skill_md):
    """Own scripts go through the variable. A SIBLING's script keeps the
    workspace-root form on purpose: `${CLAUDE_SKILL_DIR}/../<sibling>/scripts/`
    is the `../` cross-skill execution shape ATH flagged and the audit
    invariants forbid (test_no_cross_skill_script_execution)."""
    own = f".claude/skills/{skill_md.parent.name}/"
    assert own not in skill_md.read_text(encoding="utf-8")


@pytest.mark.parametrize("skill_md", SCRIPT_BEARING, ids=lambda p: p.parent.name)
def test_script_invocations_use_the_variable(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    own = f".claude/skills/{skill_md.parent.name}/"
    bare = [
        hit for hit in re.findall(r"python3 (?!\$\{CLAUDE_SKILL_DIR\})\S*scripts/\S+", text)
        if own in hit or not hit.startswith("python3 .claude/skills/")
    ]
    assert not bare, f"own-script invocation without ${{CLAUDE_SKILL_DIR}}: {bare}"
    assert "${CLAUDE_SKILL_DIR}/scripts/" in text


@pytest.mark.parametrize("skill_md", SCRIPT_BEARING, ids=lambda p: p.parent.name)
def test_fallback_prose_names_the_unexpanded_case(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    assert "leaves it unexpanded" in text, "fallback for non-substituting hosts missing"
    assert "next to this SKILL.md" in text
