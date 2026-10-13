"""L0: the install guide keeps the promises the onboarding spec makes about it.

The install prompt itself is drift-gated by `scripts/sync_shared.py`; these
tests cover what the sync cannot see — that every recipe says when it was last
carried out, and that the network advice names the services the literature
search really contacts.
"""

from __future__ import annotations

import re
from types import SimpleNamespace

import publish
import pytest
import search
import sync_shared
from helpers import REPO, winget_problems

import install

GUIDE = REPO / "docs" / "install.md"
VERIFIED_RE = re.compile(r"^\*Verified \d{4}-\d{2}-\d{2} with \S.* \S+\*$")
UNVERIFIED = "*unverified*"
# the open change that introduces the recipes; once it is archived, an
# unverified recipe can no longer pass (user-onboarding spec: Concrete agent
# walkthroughs — a recipe nobody has carried out is not published)
INTRODUCING_CHANGE = REPO / "openspec" / "changes" / "desktop-first-install"
API_HOST_RE = re.compile(r"https?://((?:api|export)\.[a-z0-9.-]+|dblp\.org)")
OFFLINE_SECTION = "Literature search cannot reach its sources"
TIERS_SECTION = "What you need"
CHECKLIST_SECTION = "Is everything working?"
PDF_SECTION = "PDF export"
# what the checklist quotes from the installer and the search (onboarding spec:
# Setup tiers and readiness checks — the quoted output must match the scripts)
PRESENCE_HEADING = "On this computer:"
SOURCES_PREFIX = "sources: "
VERSION_RE = re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b")
LATEST_RELEASES = ("https://github.com/typst/typst/releases/latest",
                   "https://github.com/jgm/pandoc/releases/latest")
HASH_COMMANDS = ("certutil -hashfile", "shasum -a 256", "sha256sum")


def section(text: str, heading: str) -> str:
    start = text.index(f"\n## {heading}\n")
    end = text.find("\n## ", start + 1)
    return text[start:end if end != -1 else len(text)]


def guide_section(heading: str) -> str:
    return section(GUIDE.read_text(encoding="utf-8"), heading)


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


def test_the_prompt_looks_further_before_it_reports_no_python():
    """A uv-only or Anaconda-only machine answers to none of the three usual
    names; the prompt has the agent look (never download) before it sends the
    student to install a Python they already have (installation spec, design D12)."""
    prompt = sync_shared.PROMPT_SOURCE.read_text(encoding="utf-8")
    assert 'uv python find ">=3.11"' in prompt
    assert "uv python install" not in prompt
    assert "versioned names" in prompt
    assert "python3.13" in prompt
    assert "py -0p" in prompt
    usual = prompt.index("py -3 --version")
    guidance = prompt.index("stop and tell me how to install it")
    for further in ('uv python find ">=3.11"', "versioned names", "py -0p"):
        assert usual < prompt.index(further) < guidance, f"{further} is out of order"
    assert "without downloading or installing anything" in prompt[usual:guidance]


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
               "prompt": sync_shared.PROMPT_SOURCE.read_text(encoding="utf-8"),
               # a script message is read where no repository exists either
               "publish.py": publish.INSTALL_HINT}
    # an installed skill has no repository beside it, so it links the guide by URL
    sources |= {md.parent.name: md.read_text(encoding="utf-8")
                for md in sorted(REPO.glob("skills/proposal-*/SKILL.md"))}
    linked = [name for name, text in sources.items()
              if name.startswith("proposal-") and "install.md#" in text]
    assert "proposal-check" in linked, "proposal-check no longer links the guide's Python section"
    assert "proposal-publish" in linked, "proposal-publish no longer links the guide's PDF section"
    assert "install.md#pdf-export" in sources["publish.py"]
    assert "docs/install.md#is-everything-working" in sources["README.md"]
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


# -- setup tiers, readiness checks, PDF tools (onboarding spec) --------------

def checklist_items() -> list[str]:
    return re.split(r"^\d\. ", guide_section(CHECKLIST_SECTION), flags=re.MULTILINE)[1:]


def test_the_guide_says_what_each_kind_of_work_needs():
    rows = [line for line in guide_section(TIERS_SECTION).splitlines()
            if line.startswith("| ")][1:]  # the first is the header
    assert len(rows) == 4, rows
    writing, scripts, pdf, keys = rows
    assert "agent app" in writing
    assert "Python 3.11" in scripts
    assert all(word in pdf for word in ("`pandoc`", "`typst`", "LaTeX", "optional"))
    assert "API key" in keys
    assert "optional" in keys


def test_the_proposals_folder_is_never_a_clone_of_this_repository():
    tiers = guide_section(TIERS_SECTION)
    assert "clone" in tiers
    assert "`AGENTS.md`" in tiers


def test_the_checklist_has_four_checks_that_each_state_their_limits():
    items = checklist_items()
    assert len(items) == 4, f"expected four checks, found {len(items)}"
    for number, item in enumerate(items, 1):
        for label in ("**Shows:**", "**Does not show:**", "**If not"):
            assert label in item, f"check {number} lacks {label}"
    discovery, interpreter, network, pdf = items
    assert "eleven" in discovery
    assert "--help" in interpreter
    assert "`sources:" in network
    assert "Build a PDF" in pdf
    assert PRESENCE_HEADING in guide_section(CHECKLIST_SECTION)


def test_the_checklist_quotes_what_the_installer_and_the_search_print(tmp_path, capsys,
                                                                      monkeypatch):
    checklist = guide_section(CHECKLIST_SECTION)
    install.report_readiness(tmp_path / "home", tmp_path)
    assert PRESENCE_HEADING in capsys.readouterr().out
    assert PRESENCE_HEADING in checklist
    monkeypatch.setitem(search.SEARCH_SOURCES, "stub",
                        SimpleNamespace(search=lambda _query, **_limit: []))
    search.federate("readiness", 1, ["stub"])
    err = capsys.readouterr().err.splitlines()
    assert any(line.startswith(SOURCES_PREFIX) for line in err), err
    assert f"`{SOURCES_PREFIX.strip()}" in checklist


def test_the_pdf_fallback_is_version_free_and_digest_checked():
    pdf = guide_section(PDF_SECTION)
    assert not VERSION_RE.search(pdf), f"pinned version: {VERSION_RE.search(pdf).group(0)}"
    for url in LATEST_RELEASES:
        assert url in pdf
    assert set(re.findall(r"https://github\.com/[^)\s]+/releases/[^)\s]*", pdf)) == set(
        LATEST_RELEASES)
    assert "SHA-256" in pdf
    for command in HASH_COMMANDS:
        assert command in pdf
    assert "delete the file" in pdf
    assert "do not repair or reset" in pdf
    assert "sudo" not in pdf
    assert "winget install" in pdf
    assert winget_problems(pdf) == []


@pytest.mark.parametrize("doc", ["docs/install.md", "README.md"])
def test_the_workspace_root_is_called_the_proposals_folder(doc):
    text = (REPO / doc).read_text(encoding="utf-8")
    found = re.findall(r"\bproposal folders?\b", text, flags=re.IGNORECASE)
    assert not found, f"{doc}: say 'proposals folder' for the workspace root: {found}"
