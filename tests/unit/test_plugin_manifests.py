"""L0: the plugin definition delivers exactly the shipped skills (installation
spec: Plugin definition for apps with a plugin button).

A listed path that does not exist passes `claude plugin validate --strict`, yet
the whole plugin then fails to load with "Path not found" — so the list is
checked here against the directories, not left to the host's validator.
"""

from __future__ import annotations

import json

from helpers import REPO

MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"


def manifest() -> dict:
    return json.loads(MARKETPLACE.read_text(encoding="utf-8"))


def shipped() -> list[str]:
    return sorted(d.name for d in (REPO / "skills").iterdir()
                  if d.is_dir() and d.name.startswith("proposal-") and (d / "SKILL.md").is_file())


def keys_anywhere(node: object) -> set[str]:
    if isinstance(node, dict):
        return set(node) | {k for v in node.values() for k in keys_anywhere(v)}
    if isinstance(node, list):
        return {k for v in node for k in keys_anywhere(v)}
    return set()


def test_marketplace_and_plugin_are_both_named_thesis_proposal():
    data = manifest()
    assert data["name"] == "thesis-proposal"
    assert [p["name"] for p in data["plugins"]] == ["thesis-proposal"]


def test_plugin_lists_exactly_the_shipped_skills():
    plugin = manifest()["plugins"][0]
    root = REPO / plugin["source"]
    listed = [path.removeprefix("./") for path in plugin["skills"]]
    assert sorted(listed) == shipped(), "plugin skill list differs from skills/proposal-*"
    missing = [p for p in listed if not (root / p / "SKILL.md").is_file()]
    assert not missing, f"listed skill paths without a SKILL.md: {missing}"


def test_plugin_ships_only_the_skills_folder():
    """A root source would copy tests, harness and specs into every user's cache."""
    assert manifest()["plugins"][0]["source"] == "./skills"


def test_no_version_is_pinned():
    """Without a version, a plugin install follows the default branch's commits."""
    assert "version" not in keys_anywhere(manifest())


def test_no_second_manifest_would_conflict():
    """`strict: false` turns a later plugin.json into a loud "conflicting
    manifests" error rather than a silent merge; keep the entry the only one."""
    assert manifest()["plugins"][0]["strict"] is False
    assert not (REPO / "skills" / ".claude-plugin").exists()
