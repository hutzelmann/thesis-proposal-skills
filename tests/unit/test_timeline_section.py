"""L0: the timeline section — presence, size guard, canonical order.

Covers the guidance-model "Coarse timeline section" requirement and the
skill-check order/size rules. The size guard is what replaced the deleted
`timeline`/`zeitplan` forbidden-heading patterns, so its coverage is the
barrier against Gantt charts.
"""

import json
from pathlib import Path

import pytest
from helpers import FIXTURES, REPO, run_check

STRUCTURE = REPO / "shared" / "structure.json"
CLEAN = FIXTURES / "f00-clean-en" / "ml-code-review.md"
CLEAN_DE = FIXTURES / "f12-clean-de" / "typsystem-einheitenfehler.md"


def with_timeline(tmp_path: Path, body: str, source: Path = CLEAN,
                  heading: str = "Timeline") -> str:
    """Replace the clean fixture's timeline body with `body`."""
    text = source.read_text(encoding="utf-8")
    head, _, tail = text.partition(f"# {heading}\n")
    _, sep, rest = tail.partition("\n---\n")
    assert sep, "fixture layout changed: timeline is no longer the last section"
    victim = tmp_path / source.name
    victim.write_text(f"{head}# {heading}\n\n{body}\n\n---\n{rest}", encoding="utf-8")
    return run_check(victim).stdout


# ---------- presence ---------------------------------------------------------

def test_missing_timeline_is_an_error(tmp_path):
    text = CLEAN.read_text(encoding="utf-8")
    head, sep, tail = text.partition("# Timeline\n")
    assert sep
    victim = tmp_path / "no-timeline.md"
    victim.write_text(head + tail.partition("\n---\n")[2].join(["---\n", ""]), encoding="utf-8")
    result = run_check(victim)
    assert "required section missing: `Timeline`" in result.stdout
    assert result.returncode == 1


def test_german_proposal_requires_zeitplan(tmp_path):
    text = CLEAN_DE.read_text(encoding="utf-8")
    head, sep, tail = text.partition("# Zeitplan\n")
    assert sep
    victim = tmp_path / "kein-zeitplan.md"
    victim.write_text(head + "---\n" + tail.partition("\n---\n")[2], encoding="utf-8")
    result = run_check(victim)
    assert "required section missing: `Zeitplan`" in result.stdout


# ---------- size guard -------------------------------------------------------

def test_coarse_sentence_passes(tmp_path):
    out = with_timeline(
        tmp_path, "The thesis starts in October 2026 and is submitted in March 2027."
    )
    assert "ERROR" not in out


def test_as_soon_as_possible_passes(tmp_path):
    assert "ERROR" not in with_timeline(tmp_path, "The thesis starts as soon as possible.")


def test_todo_marker_passes_the_size_guard(tmp_path):
    """An unknown timeframe is a TODO, not an invented statement — the script
    warns about the marker but the guard itself must stay silent."""
    out = with_timeline(
        tmp_path, '[TODO: state start month and submission month, or "as soon as possible"]'
    )
    assert "ERROR" not in out
    assert "WARNING" in out


def test_three_lines_pass(tmp_path):
    body = ("The thesis starts in October 2026.\nIt is submitted in March 2027.\n"
            "Registration is pending.")
    assert "ERROR" not in with_timeline(tmp_path, body)


def test_four_lines_fail(tmp_path):
    body = (
        "The thesis starts in October 2026.\nIt is submitted in March 2027.\n"
        "Registration is pending.\nThe supervisor has agreed to the window."
    )
    out = with_timeline(tmp_path, body)
    assert "runs 4 lines — at most 3 allowed" in out


def test_blank_lines_do_not_count(tmp_path):
    body = "The thesis starts in October 2026.\n\n\nIt is submitted in March 2027."
    assert "ERROR" not in with_timeline(tmp_path, body)


@pytest.mark.parametrize(
    ("body", "needle"),
    [
        ("| Phase | Month |\n|---|---|\n| Setup | 1 |", "table in `Timeline`"),
        ("- Phase 1: literature review\n- Phase 2: implementation", "list in `Timeline`"),
        ("1. Literature review\n2. Implementation", "list in `Timeline`"),
        ("## Work Packages\n\nWP1 runs first.", "subsection in `Timeline`"),
    ],
    ids=["table", "bullet-list", "ordered-list", "subsection"],
)
def test_structural_violations_are_errors(tmp_path, body, needle):
    assert needle in with_timeline(tmp_path, body)


def test_german_guard_names_the_german_title(tmp_path):
    out = with_timeline(
        tmp_path, "| Phase | Monat |\n|---|---|\n| Aufbau | 1 |",
        source=CLEAN_DE, heading="Zeitplan",
    )
    assert "table in `Zeitplan`" in out


# ---------- order ------------------------------------------------------------

def test_canonical_order_passes():
    assert "out of order" not in run_check(CLEAN).stdout


def test_timeline_before_methodology_is_an_error(tmp_path):
    text = CLEAN.read_text(encoding="utf-8")
    head, sep, tail = text.partition("# Timeline\n")
    assert sep
    timeline_body, _, meta = tail.partition("\n---\n")
    moved = f"# Timeline\n{timeline_body}\n\n{head}\n---\n{meta}"
    victim = tmp_path / "reordered.md"
    victim.write_text(moved, encoding="utf-8")
    result = run_check(victim)
    assert "section out of order: `Timeline` before" in result.stdout
    assert result.returncode == 1


def test_order_error_names_the_methodology_as_written(tmp_path):
    """Not the `{methodology}` template — the heading the author actually wrote."""
    text = CLEAN.read_text(encoding="utf-8")
    head, _, tail = text.partition("# Timeline\n")
    timeline_body, _, meta = tail.partition("\n---\n")
    victim = tmp_path / "reordered.md"
    victim.write_text(f"# Timeline\n{timeline_body}\n\n{head}\n---\n{meta}", encoding="utf-8")
    out = run_check(victim).stdout
    assert "{methodology}" not in out.split("section out of order")[1].split("\n")[0]
    assert "Prototype Implementation" in out


def test_non_canonical_headings_do_not_affect_order(tmp_path):
    text = CLEAN.read_text(encoding="utf-8")
    victim = tmp_path / "extra-heading.md"
    victim.write_text(text.replace("# Timeline\n", "# Acknowledgements\n\nThanks.\n\n# Timeline\n"))
    assert "out of order" not in run_check(victim).stdout


def test_override_list_supplies_its_own_order(tmp_path):
    """An overridden [sections] required list is ordered; that order is enforced,
    and the canonical default no longer applies."""
    victim = tmp_path / "custom.md"
    victim.write_text(
        "# Beta\n\nSecond by default, first here.\n\n# Alpha\n\nText.\n\n"
        "---\ntitle: t\nlang: en\nreferences: []\n---\n"
    )
    (tmp_path / "guidelines.md").write_text(
        '```toml\n[sections]\nrequired = ["Beta", "Alpha"]\n```\n'
    )
    assert "out of order" not in run_check(victim).stdout

    (tmp_path / "guidelines.md").write_text(
        '```toml\n[sections]\nrequired = ["Alpha", "Beta"]\n```\n'
    )
    assert "section out of order: `Beta` before `Alpha`" in run_check(victim).stdout


# ---------- substring-collision regression ----------------------------------

def test_no_forbidden_pattern_collides_with_a_canonical_title():
    """Forbidden headings match by substring, so a canonical title that contains
    a forbidden pattern would be permanently unusable. Deleting `timeline` and
    `zeitplan` from the list was what made those two titles possible; this pins
    that no future pattern quietly takes them back."""
    structure = json.loads(STRUCTURE.read_text(encoding="utf-8"))
    titles = structure["sections"]["titles"]
    patterns = [p.lower() for p in structure["forbidden"]["heading_patterns"]]
    for key, per_lang in titles.items():
        for lang, title in per_lang.items():
            stem = title.split("{")[0].strip().lower()
            hits = [p for p in patterns if p in stem]
            assert not hits, f"canonical title `{title}` ({key}/{lang}) matches forbidden {hits}"


def test_work_plan_patterns_are_a_subset_of_forbidden():
    structure = json.loads(STRUCTURE.read_text(encoding="utf-8"))
    forbidden = {p.lower() for p in structure["forbidden"]["heading_patterns"]}
    work_plan = {p.lower() for p in structure["forbidden"]["work_plan_patterns"]}
    assert work_plan <= forbidden, work_plan - forbidden


def test_rival_timeline_names_stay_forbidden_even_when_detailed():
    """`schedule` and `time plan` are rival names for the canonical section, not
    work-plan markers — the detailed mode must not un-forbid them."""
    structure = json.loads(STRUCTURE.read_text(encoding="utf-8"))
    work_plan = {p.lower() for p in structure["forbidden"]["work_plan_patterns"]}
    assert "schedule" not in work_plan
    assert "time plan" not in work_plan
