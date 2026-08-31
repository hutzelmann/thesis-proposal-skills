"""L0: SKILL.md prose describing the single-file format must state the full
canonical contract (proposal-file-format spec: skill prose must not drift).

Discovery rule: a SKILL.md that names the `references` metadata key AND says
"metadata block" counts as describing the format; a single passing mention
(lit-search's `references:` block without the block's position, check's
"ending in a metadata block" without the key) stays exempt. A discovered file
must then state every element of the contract: the leading `# ` title line,
the emphasized subtitle paragraph, the closing references heading, the
`references` key, the blank-line rule, and the trailing position of the block.

`author`, `title`, `subtitle`, and `lang` are deliberately not required keys:
proposals are anonymous, and title/subtitle/lang moved into the body or are
inferred (see the proposal-file-format spec). A describer that reintroduces
one of them as a metadata key fails.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# `author` is not scanned for: every describer names it precisely to forbid it
RETIRED_KEYS = ("title", "subtitle", "lang")
EXPECTED_DESCRIBERS = {
    "proposal-write", "proposal-import", "proposal-ideate", "proposal-reverse",
}

CONTRACT = {
    "leading `# ` title line": r"leading `# ",
    "emphasized subtitle paragraph": r"emphasized",
    "closing references heading": r"references heading",
    "`references` key": r"`references:?`",
    "blank-line rule": r"blank line",
    "trailing position": r"trailing",
}


def format_describers():
    for skill_md in sorted((REPO / "skills").glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        if re.search(r"`references:?`", text) and "metadata block" in text.lower():
            yield skill_md.parent.name, text


def test_discovery_finds_known_describers():
    found = {name for name, _ in format_describers()}
    assert found >= EXPECTED_DESCRIBERS, (
        f"format-describing skills no longer discovered: {EXPECTED_DESCRIBERS - found}"
    )


def test_format_contract_complete():
    problems = []
    for name, text in format_describers():
        low = text.lower()
        for label, pattern in CONTRACT.items():
            if not re.search(pattern, low):
                problems.append(f"{name}: {label} not stated")
    assert not problems, "format prose drift:\n" + "\n".join(problems)


def test_no_describer_reintroduces_a_retired_metadata_key():
    problems = []
    for name, text in format_describers():
        for key in RETIRED_KEYS:
            # a retired key described as part of the metadata block, e.g.
            # "metadata block (`title`, ..." — matched narrowly: the backticked
            # key directly after the word "block" or in a key list with
            # `references`
            if re.search(rf"metadata block[^.]*`{key}:?`", text):
                problems.append(f"{name}: names retired metadata key `{key}`")
    assert not problems, "format prose drift:\n" + "\n".join(problems)
