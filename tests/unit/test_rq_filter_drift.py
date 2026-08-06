"""L0: rq-filter.lua's heading matching must stay in sync with structure.json
(S3 design risk: the filter keys on heading text)."""

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LUA = (
    REPO / "skills" / "proposal-publish" / "templates" / "rq-filter.lua"
).read_text(encoding="utf-8")
STRUCTURE = json.loads((REPO / "shared" / "structure.json").read_text(encoding="utf-8"))


def test_lua_matches_canonical_rq_titles():
    titles = STRUCTURE["sections"]["titles"]["research_questions"]
    for lang in ("en", "de"):
        # the lua filter must recognize a distinctive part of each canonical title
        matched = any(
            fragment in titles[lang]
            for fragment in ("Research Questions", "Forschungsfragen")
            if fragment in LUA
        )
        assert matched, (
            f"rq-filter.lua matches no fragment of the canonical {lang} title "
            f"{titles[lang]!r} — filter and structure.json drifted"
        )
