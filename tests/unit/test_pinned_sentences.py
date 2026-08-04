"""L0: load-bearing sentences stay verbatim in their skill prose (skill-packaging
spec: load-bearing sentences pinned offline).

Each file in `data/pinned_sentences/` is named `<skill>--<slug>.txt` and holds
one exact substring that must appear in `skills/<skill>/SKILL.md`. Rewording a
pinned sentence therefore requires editing its pinned copy in the same change,
so the reword shows up as a paired diff under review — the same contract the
mandate pins establish for the opening paragraphs.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PIN_DIR = Path(__file__).resolve().parent / "data" / "pinned_sentences"
PINS = sorted(PIN_DIR.glob("*.txt"))


def test_pin_corpus_is_nonempty_and_well_named():
    assert PINS, "no pinned sentences found"
    for pin in PINS:
        skill = pin.stem.split("--")[0]
        assert (REPO / "skills" / skill / "SKILL.md").exists(), (
            f"{pin.name}: no skill named {skill!r}"
        )


@pytest.mark.parametrize("pin", PINS, ids=lambda p: p.stem)
def test_pinned_sentence_present_verbatim(pin):
    skill = pin.stem.split("--")[0]
    sentence = pin.read_text(encoding="utf-8").strip()
    prose = (REPO / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    assert sentence in prose, (
        f"{skill}/SKILL.md no longer contains the pinned sentence from "
        f"{pin.name} — revise the pinned copy in the same change to reword it"
    )
