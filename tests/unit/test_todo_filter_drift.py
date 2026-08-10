"""L0: todo-filter.lua's marker scanner must stay in sync with structure.json.

Lua cannot read the canonical JSON without a dependency, so the filter
hardcodes the marker's opening token. Same risk and same guard as
test_rq_filter_drift.py, which keys rq-filter.lua on the canonical headings.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LUA = (
    REPO / "skills" / "proposal-publish" / "templates" / "todo-filter.lua"
).read_text(encoding="utf-8")
STRUCTURE = json.loads((REPO / "shared" / "structure.json").read_text(encoding="utf-8"))


def test_lua_scanner_matches_the_canonical_marker():
    marker = STRUCTURE["todo"]["marker"]
    # the canonical regex is "\[TODO:[^\]]*\]" — derive its literal opening
    # token rather than restating it, so a rename of the marker fails here
    opening = re.match(r"^\\\[([A-Za-z]+):", marker)
    assert opening, f"todo_marker {marker!r} no longer opens with a literal token"
    token = opening.group(1)

    assert f"^%[{token}:" in LUA, (
        f"todo-filter.lua does not scan for the canonical opening `[{token}:` "
        f"of todo_marker {marker!r} — filter and structure.json drifted"
    )


def test_lua_stops_at_the_first_closing_bracket():
    # todo_marker's [^\]]* means a marker ends at the FIRST "]"; the Lua
    # scanner must use the same non-greedy shape or hints would over-capture
    assert "^([^%]]*)%](.*)$" in LUA, (
        "todo-filter.lua no longer terminates a marker at the first `]`, "
        "diverging from todo_marker's [^\\]]* semantics"
    )
