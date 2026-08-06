"""L0: SKILL.md prose describing the single-file format must state the full
canonical contract (proposal-file-format spec: skill prose must not drift).

Discovery rule: a SKILL.md naming two or more of the four canonical metadata
keys counts as describing the format; a single key in passing (lit-search's
`references:` block, check's "ending in a metadata block") stays exempt. A
discovered file must then name all four keys, the blank-line rule, and the
trailing position of the block.

`author` is deliberately absent: proposals are anonymous, so the writer's name
is not part of the contract (see the proposal-file-format spec).
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CANONICAL_KEYS = ("title", "subtitle", "lang", "references")
EXPECTED_DESCRIBERS = {"proposal-write", "proposal-import", "proposal-ideate"}


def named_keys(text: str) -> set[str]:
    return {k for k in CANONICAL_KEYS if re.search(rf"`{k}:?`", text)}


def format_describers():
    for skill_md in sorted((REPO / "skills").glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        keys = named_keys(text)
        if len(keys) >= 2:
            yield skill_md.parent.name, text, keys


def test_discovery_finds_known_describers():
    found = {name for name, _, _ in format_describers()}
    assert found >= EXPECTED_DESCRIBERS, (
        f"format-describing skills no longer discovered: {EXPECTED_DESCRIBERS - found}"
    )


def test_format_contract_complete():
    problems = []
    for name, text, keys in format_describers():
        missing = set(CANONICAL_KEYS) - keys
        if missing:
            problems.append(f"{name}: missing canonical keys {sorted(missing)}")
        if "blank line" not in text.lower():
            problems.append(f"{name}: blank-line rule not stated")
        if "trailing" not in text.lower():
            problems.append(f"{name}: trailing position of metadata block not stated")
    assert not problems, "format prose drift:\n" + "\n".join(problems)
