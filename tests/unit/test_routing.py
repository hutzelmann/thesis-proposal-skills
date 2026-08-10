"""L0: the routing rig's verdict logic and dataset, without a model call.

The rig itself needs a host install and a subscription, so it never runs here.
What runs here is everything that decides what a run *means*: which skill an
event stream selected, how cases classify, and whether the dataset still covers
every skill. Stream fixtures live in `tests/unit/data/routing_streams/`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from helpers import REPO
from routing import (
    KINDS,
    NO_ROUTE,
    WORKSPACE_FIXTURES,
    Case,
    Result,
    classify,
    composition_problems,
    installed_skills,
    load_cases,
    misroutes,
    outcome_label,
    previous_score,
    render_report,
    route_from_events,
    tool_calls,
)

STREAMS = Path(__file__).parent / "data" / "routing_streams"


def events(name: str) -> list[dict]:
    path = STREAMS / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


# ---------- route extraction -------------------------------------------------


def test_recorded_selection_is_the_route():
    assert route_from_events(events("routed-check")) == "proposal-check"


def test_exploration_without_a_skill_is_unrouted():
    assert route_from_events(events("unrouted-explore")) is None


def test_preparatory_calls_are_tolerated():
    assert route_from_events(events("preparatory-then-route")) == "proposal-review"


def test_first_pick_owns_the_route_when_a_sibling_is_chained():
    assert route_from_events(events("chained-sibling")) == "proposal-ideate"


def test_foreign_skill_is_not_our_route():
    assert route_from_events(events("foreign-skill-first")) == "proposal-ideate"


def test_skill_call_without_a_skill_name_raises_with_the_input():
    with pytest.raises(ValueError, match="carries no skill name"):
        route_from_events(events("malformed-skill-call"))


def test_route_ignores_non_assistant_events():
    stream = [{"type": "system", "subtype": "hook_started"}, *events("routed-check")]
    assert route_from_events(stream) == "proposal-check"


def test_wandering_past_the_bound_is_unrouted():
    peek = events("preparatory-then-route")[0]
    assert route_from_events([peek] * 4 + events("routed-check")) is None


def test_the_preparatory_bound_is_a_parameter_not_a_law():
    """Raising it must be able to change a verdict, or the constant could never
    be questioned against a recorded run."""
    peek = events("preparatory-then-route")[0]
    wandering = [peek] * 4 + events("routed-check")
    assert route_from_events(wandering) is None
    assert route_from_events(wandering, bound=10) == "proposal-check"


def test_tool_calls_preserve_order():
    names = [name for name, _ in tool_calls(events("preparatory-then-route"))]
    assert names == ["Glob", "Read", "Skill"]


# ---------- classification ---------------------------------------------------


def result(case_id: str, expected: str, kind: str = "canonical", route: str | None = None,
           error: str | None = None) -> Result:
    return Result(case_id=case_id, expected=expected, kind=kind, route=route, error=error)


def test_correct_route_passes():
    assert result("a", "proposal-check", route="proposal-check").passed


def test_negative_case_passes_when_nothing_is_selected():
    assert result("n", NO_ROUTE, kind="negative", route=None).passed


def test_negative_case_fails_when_a_skill_claims_it():
    assert not result("n", NO_ROUTE, kind="negative", route="proposal-write").passed


def test_errors_are_a_category_of_their_own_not_a_route():
    matrix = classify([result("e", "proposal-check", error="timed out after 90s")])
    assert matrix.errors == ["e: timed out after 90s"]
    assert matrix.pairs == {}
    assert matrix.totals == (0, 0)


def test_matrix_counts_expected_against_selected():
    matrix = classify([
        result("a", "proposal-review", route="proposal-check"),
        result("b", "proposal-review", route="proposal-check"),
        result("c", "proposal-review", route="proposal-review"),
    ])
    assert matrix.pairs[("proposal-review", "proposal-check")] == 2
    assert matrix.totals == (1, 3)


def test_per_kind_totals_are_kept_apart():
    matrix = classify([
        result("a", "proposal-check", kind="canonical", route="proposal-check"),
        result("b", "proposal-check", kind="collision", route="proposal-review"),
    ])
    assert matrix.per_kind == {"canonical": (1, 1), "collision": (0, 1)}


def test_misroutes_lists_only_wrong_completed_measurements():
    results = [
        result("a", "proposal-check", route="proposal-check"),
        result("b", "proposal-review", route="proposal-check"),
        result("c", "proposal-write", error="no events"),
    ]
    assert [r.case_id for r in misroutes(results)] == ["b"]


# ---------- report -----------------------------------------------------------


def test_report_names_the_stealing_skill_and_the_utterance():
    results = [result("review-canonical", "proposal-review", route="proposal-check")]
    text = render_report(results, classify(results), "sonnet")
    assert "review-canonical" in text
    assert "mis-routed" in text
    assert "sonnet" in text


def test_report_separates_never_selected_from_stolen():
    assert outcome_label("proposal-ideate", NO_ROUTE) == " ← not selected"
    assert outcome_label("proposal-review", "proposal-check") == " ← mis-routed"
    assert outcome_label("proposal-check", "proposal-check") == ""


def test_report_states_the_score_it_supersedes(tmp_path):
    earlier = tmp_path / "skill-routing.md"
    results = [result("a", "proposal-check", route="proposal-check")]
    earlier.write_text(render_report(results, classify(results), "sonnet"), encoding="utf-8")
    assert previous_score(earlier) == "1/1"
    assert "supersedes: 1/1" in render_report(
        results, classify(results), "sonnet", supersedes=previous_score(earlier))


def test_first_report_has_nothing_to_supersede(tmp_path):
    assert previous_score(tmp_path / "absent.md") is None


def test_report_records_the_revision_it_was_rendered_for():
    results = [result("a", "proposal-check", route="proposal-check")]
    assert "deadbee" in render_report(results, classify(results), "sonnet", "deadbee")


def test_repeated_epochs_of_one_case_collapse_to_one_line():
    results = [result("c", "proposal-ideate", kind="collision", route=None)] * 3
    text = render_report(results, classify(results), "sonnet")
    assert text.count("- `c` expected") == 1
    assert "3/3 epochs" in text


def test_report_states_when_nothing_mis_routed():
    results = [result("a", "proposal-check", route="proposal-check")]
    assert "None." in render_report(results, classify(results), "sonnet")


# ---------- dataset ----------------------------------------------------------


def test_shipped_dataset_is_well_formed():
    assert composition_problems(load_cases(), installed_skills()) == []


def test_every_installed_skill_is_covered_by_the_dataset():
    covered = {c.expected for c in load_cases()}
    assert set(installed_skills()) <= covered


def test_dataset_carries_negatives_and_german_cases():
    cases = load_cases()
    assert sum(c.kind == "negative" for c in cases) >= 4
    assert sum(c.lang == "de" for c in cases) >= 6


def test_dataset_kinds_are_known():
    assert {c.kind for c in load_cases()} <= set(KINDS)


def test_utterances_naming_a_file_name_one_that_is_staged():
    staged = {name for _, name in WORKSPACE_FIXTURES}
    for case in load_cases():
        for word in case.utterance.replace("(", " ").replace(")", " ").split():
            token = word.strip(".,;:!?")
            if token.endswith((".md", ".txt")):
                assert token in staged, f"{case.id} names unstaged file {token}"


def test_missing_case_kind_is_reported():
    cases = [c for c in load_cases()
             if not (c.expected == "proposal-check" and c.kind == "oblique")]
    problems = composition_problems(cases, installed_skills())
    assert any("proposal-check: no oblique case" in p for p in problems)


def test_negative_case_expecting_a_skill_is_reported():
    broken = [c for c in load_cases() if c.kind != "negative"]
    broken.append(Case(id="bad", utterance="x", expected="proposal-write",
                       kind="negative", lang="en"))
    assert any("must expect" in p for p in composition_problems(broken, installed_skills()))


def test_repo_ships_the_stream_fixture_readme():
    assert (STREAMS / "README.md").is_file()
    assert REPO.joinpath("harness", "routing_cases.toml").is_file()
