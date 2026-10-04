"""L0: the install guide keeps the promises the onboarding spec makes about it.

The install prompt itself is drift-gated by `scripts/sync_shared.py`; these
tests cover what the sync cannot see — that every recipe says when it was last
carried out, and that the network advice names the services the literature
search really contacts.
"""

from __future__ import annotations

import re

import pytest
import sync_shared
from helpers import REPO

GUIDE = REPO / "docs" / "install.md"
VERIFIED_RE = re.compile(r"^\*Verified \d{4}-\d{2}-\d{2} with \S.* \S+\*$")
UNVERIFIED = "*unverified*"
# the open change that introduces the recipes; once it is archived, an
# unverified recipe can no longer pass (user-onboarding spec: Concrete agent
# walkthroughs — a recipe nobody has carried out is not published)
INTRODUCING_CHANGE = REPO / "openspec" / "changes" / "desktop-first-install"
API_HOST_RE = re.compile(r"https?://((?:api|export)\.[a-z0-9.-]+|dblp\.org)")
OFFLINE_SECTION = "Literature search cannot reach its sources"


def section(text: str, heading: str) -> str:
    start = text.index(f"\n## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else len(text)]


def recipes() -> list[tuple[str, str]]:
    """(heading, first non-empty line after it) for every recipe."""
    body = section(GUIDE.read_text(encoding="utf-8"), "Recipes")
    found = []
    for match in re.finditer(r"^### (.+)$", body, re.MULTILINE):
        rest = body[match.end():].lstrip("\n")
        found.append((match.group(1), rest.splitlines()[0] if rest else ""))
    return found


def test_the_featured_apps_have_recipes():
    names = [name for name, _ in recipes()]
    for app in ("ChatGPT desktop app", "Claude desktop app", "VS Code with GitHub Copilot",
                "Antigravity", "Cursor", "Any other agent"):
        assert app in names, f"no recipe for {app}"


@pytest.mark.parametrize(("name", "stamp"), [r for r in recipes() if r[0] != "Any other agent"],
                         ids=lambda v: v if isinstance(v, str) and not v.startswith("*") else "")
def test_every_recipe_says_when_it_was_last_carried_out(name, stamp):
    """`unverified` is allowed only while the change that adds a recipe is open;
    a maintainer replaces it after running the recipe (onboarding spec)."""
    if stamp == UNVERIFIED:
        assert INTRODUCING_CHANGE.is_dir(), (
            f"{name}: still unverified, but the change that introduced it is archived — "
            "run the recipe and stamp it, or remove it")
        return
    assert VERIFIED_RE.match(stamp), f"{name}: stamp line missing or malformed: {stamp!r}"


@pytest.mark.parametrize("doc", sync_shared.PROMPT_DOCS)
def test_each_document_presents_the_prompt_once(doc):
    text = (REPO / doc).read_text(encoding="utf-8")
    assert text.count(sync_shared.PROMPT_MARKER) == 1
    assert sync_shared.PROMPT_SOURCE.read_text(encoding="utf-8").strip() in text


def test_offline_advice_names_every_service_the_search_contacts():
    scripts = "\n".join(p.read_text(encoding="utf-8") for p in
                        sorted((REPO / "skills/proposal-lit-search/scripts").glob("*.py")))
    contacted = set(API_HOST_RE.findall(scripts))
    advice = section(GUIDE.read_text(encoding="utf-8"), OFFLINE_SECTION)
    named = set(re.findall(r"`([a-z0-9.-]+\.[a-z]+)`", advice))
    assert contacted, "found no service hosts in the literature-search scripts"
    assert contacted == named, f"scripts contact {sorted(contacted)}, guide names {sorted(named)}"


def test_the_prompt_downloads_the_installer_from_the_default_branch():
    prompt = sync_shared.PROMPT_SOURCE.read_text(encoding="utf-8")
    assert "raw.githubusercontent.com/hutzelmann/thesis-proposal-skills/main/install.py" in prompt
    assert (REPO / "install.py").is_file()
    for choice in ("--scope all", "--scope folder"):
        assert choice in prompt


def test_the_prompt_keeps_the_agent_away_from_skill_files_and_system_software():
    prompt = sync_shared.PROMPT_SOURCE.read_text(encoding="utf-8")
    assert "Do not install any software yourself" in prompt
    assert "do not copy, edit or run any skill files" in prompt
    assert "tell me instead of doing it" in prompt
    assert "(recommended)" in prompt


def test_the_prompt_stops_where_it_cannot_install():
    """Pasted into a cloud sandbox, the installer would succeed in a container that
    is gone in the next chat; the prompt makes the agent stop and say so."""
    prompt = sync_shared.PROMPT_SOURCE.read_text(encoding="utf-8")
    assert "cloud sandbox" in prompt
    assert "docs/install.md#chat-only-apps" in prompt
    assert "\n## Chat-only apps\n" in GUIDE.read_text(encoding="utf-8")


def test_every_link_into_the_guide_names_an_existing_section():
    """GitHub's slugs: lowercase, spaces to hyphens, punctuation dropped."""
    guide = GUIDE.read_text(encoding="utf-8")
    slugs = {re.sub(r"[^a-z0-9 -]", "", h.lower()).replace(" ", "-")
             for h in re.findall(r"^#{2,3} (.+)$", guide, re.MULTILINE)}
    sources = {"docs/install.md": guide,
               "README.md": (REPO / "README.md").read_text(encoding="utf-8"),
               "prompt": sync_shared.PROMPT_SOURCE.read_text(encoding="utf-8")}
    for where, text in sources.items():
        anchors = re.findall(r"\]\(#([a-z0-9-]+)\)", text) if where == "docs/install.md" else []
        anchors += re.findall(r"install\.md#([a-z0-9-]+)", text)
        missing = sorted(set(anchors) - slugs)
        assert not missing, f"{where} links to sections the guide does not have: {missing}"


def test_the_issue_routes_the_troubleshoot_skill_names_exist_in_the_template():
    skill = (REPO / "skills/proposal-troubleshoot/SKILL.md").read_text(encoding="utf-8")
    template = (REPO / ".github/ISSUE_TEMPLATE/skill-defect.yml").read_text(encoding="utf-8")
    mapped = re.findall(r"→ `([^`]+)`", skill)
    assert len(mapped) == 5
    for option in mapped:
        assert f"- {option}\n" in template, f"route option {option!r} is not in the template"
