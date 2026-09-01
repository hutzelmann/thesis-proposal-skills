"""L0: the shipped supervise closing note stays a markup-free single paragraph
per language (testing-harness spec: closing-note shape guard).

The note's whole purpose is to survive a channel that renders no markup — the
professor pastes the feedback as text into an email reply or a learning
platform's feedback field, where a blockquote marker reaches the student as the
literal character. That is the regression this file exists to stop, and nothing
else in the suite looks at it.

The single-paragraph rule is not tidiness: the note carries a run-in label
("Note:" / "Hinweis:") instead of a heading, and a run-in label reaches only the
paragraph it opens. A split leaves the second half unlabelled.
"""

import re
from pathlib import Path

from l1_checks import CLOSING_NOTE_LANGUAGES, closing_note_sections

REPO = Path(__file__).resolve().parents[2]
NOTE = REPO / "skills" / "proposal-supervise" / "references" / "closing-note.md"

# markdown that changes meaning when it is not rendered
BLOCK_MARKER = re.compile(r"^\s*(>|#{1,6}\s|[-*+]\s|\d+[.)]\s)")
EMPHASIS = re.compile(r"[*_]")
URL = re.compile(r"https?://\S+")

RUN_IN = {"English": "Note:", "Deutsch": "Hinweis:"}


def sections() -> dict[str, str]:
    parsed = closing_note_sections(NOTE.read_text(encoding="utf-8"))
    missing = [name for name in CLOSING_NOTE_LANGUAGES if name not in parsed]
    assert not missing, f"{NOTE.name}: section(s) missing or empty: {', '.join(missing)}"
    return parsed


def test_each_section_is_one_paragraph():
    for name, body in sections().items():
        blocks = [b for b in re.split(r"\n\s*\n", body) if b.strip()]
        assert len(blocks) == 1, (
            f"{NOTE.name}: '{name}' section is {len(blocks)} paragraphs — the run-in "
            f"label reaches only the paragraph it opens"
        )


def test_no_block_markup_survives_into_a_plain_text_channel():
    for name, body in sections().items():
        for line in body.splitlines():
            marker = BLOCK_MARKER.match(line)
            assert not marker, (
                f"{NOTE.name}: '{name}' section has a line starting with "
                f"{marker.group(1).strip()!r} — it reaches the student literally"
            )


def test_no_emphasis_markers():
    for name, body in sections().items():
        # URLs are addresses, not prose, and may carry any character
        prose = URL.sub(" ", body)
        found = EMPHASIS.findall(prose)
        assert not found, (
            f"{NOTE.name}: '{name}' section carries emphasis marker(s) "
            f"{''.join(sorted(set(found)))!r} — they reach the student literally"
        )


def test_each_section_opens_with_its_run_in_label():
    for name, body in sections().items():
        assert body.startswith(RUN_IN[name]), (
            f"{NOTE.name}: '{name}' section must open with {RUN_IN[name]!r}"
        )


def test_german_section_names_the_artifact():
    german = sections()["Deutsch"]
    assert "Rückmeldung" in german, (
        f"{NOTE.name}: German section must name the artifact 'Rückmeldung' — the "
        f"disclosure exists to make unambiguous what was AI-prepared"
    )
