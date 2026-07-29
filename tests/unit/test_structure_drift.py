"""L0: every canonical title in structure.json appears verbatim in the prose
guidelines (guidance-model spec: structured data and prose must not drift)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STRUCTURE = json.loads((REPO / "shared" / "structure.json").read_text(encoding="utf-8"))
PROSE = (REPO / "shared" / "guidelines" / "guidelines.md").read_text(encoding="utf-8")


def all_titles():
    for key, langs in STRUCTURE["sections"]["titles"].items():
        for lang in ("en", "de"):
            yield f"section {key} ({lang})", langs[lang]
    for key, meth in STRUCTURE["methodologies"].items():
        for lang in ("en", "de"):
            yield f"methodology {key} ({lang})", meth["title"][lang]
        for sub in meth["subsections"]:
            for lang in ("en", "de"):
                yield f"subsection of {key} ({lang})", sub[lang]


def test_titles_present_in_prose():
    missing = [
        f"{label}: {title!r}"
        for label, title in all_titles()
        if title not in PROSE
    ]
    assert not missing, "titles in structure.json missing from guidelines.md:\n" + "\n".join(missing)
