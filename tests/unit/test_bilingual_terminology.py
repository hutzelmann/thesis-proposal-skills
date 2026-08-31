"""L0: the shipped bilingual surfaces use one document term per language —
"proposal" in English, "Exposé" in German, never crossed (guidance-model spec:
per-language document terminology; testing-harness spec: bilingual terminology
guard).

URLs, backtick spans, and the identifiers `thesis-proposal-skills` /
`proposal-*` are exempt: they are names, not prose.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BLURB = REPO / "skills" / "proposal-supervise" / "references" / "getting-started.md"
SUPERVISE_SKILL = REPO / "skills" / "proposal-supervise" / "SKILL.md"
IDEATE_SKILL = REPO / "skills" / "proposal-ideate" / "SKILL.md"

IDENTIFIER = re.compile(r"https?://\S+|`[^`]*`|thesis-proposal-skills|proposal-[a-z-]+")


def blurb_sections() -> dict[str, str]:
    text = BLURB.read_text(encoding="utf-8")
    sections = {}
    for heading in ("English", "Deutsch"):
        match = re.search(rf"^## {heading}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
        assert match, f"{BLURB.name}: section '## {heading}' not found"
        body = match.group(1).strip()
        assert body, f"{BLURB.name}: section '## {heading}' is empty"
        sections[heading] = body
    return sections


def test_english_blurb_says_proposal_never_expose():
    english = blurb_sections()["English"]
    prose = IDENTIFIER.sub(" ", english)
    assert re.search(r"\bproposals?\b", prose, re.IGNORECASE), (
        f"{BLURB.name}: English section never names the document a proposal"
    )
    assert "exposé" not in english.lower(), (
        f"{BLURB.name}: English section must not use the term 'Exposé'"
    )


def test_german_blurb_says_expose_never_proposal():
    german = blurb_sections()["Deutsch"]
    assert "Exposé" in german, (
        f"{BLURB.name}: German section must name the document an Exposé (accented)"
    )
    prose = IDENTIFIER.sub(" ", german)
    assert not re.search(r"\bproposals?\b", prose, re.IGNORECASE), (
        f"{BLURB.name}: German section uses the term 'proposal' outside an identifier"
    )


def test_german_tier_phrases_use_expose():
    text = SUPERVISE_SKILL.read_text(encoding="utf-8")
    assert "noch kein Exposé" in text, (
        f"{SUPERVISE_SKILL.name}: German idea-stage tier must render as 'noch kein Exposé'"
    )


def test_german_subtitles_use_expose():
    text = IDEATE_SKILL.read_text(encoding="utf-8")
    for subtitle in ("Exposé zur Bachelorarbeit", "Exposé zur Masterarbeit"):
        assert subtitle in text, (
            f"{IDEATE_SKILL.name}: German subtitle {subtitle!r} missing or reworded"
        )
