"""L0: the routing rig's verdict logic and dataset, without a model call.

The rig itself needs a host install and a subscription, so it never runs here.
What runs here is everything that decides what a run *means*: which skill an
event stream selected, how cases classify, and whether the dataset still covers
every skill. Stream fixtures live in `tests/unit/data/routing_streams/`.
"""

from __future__ import annotations

import io
import json
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest
import routing
from helpers import REPO
from routing import (
    DEFAULT_PROPOSAL,
    KINDS,
    NO_ROUTE,
    Case,
    Result,
    case_result,
    classify,
    composition_problems,
    files_named,
    installed_skills,
    load_cases,
    misroutes,
    outcome_label,
    previous_score,
    render_report,
    report_due,
    route_from_events,
    stage_workspace,
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


# ---------- host errors ------------------------------------------------------

CHECK_CASE = Case(id="c", utterance="Please check microservice-technical-debt.md.",
                  expected="proposal-check", kind="canonical", lang="en")
NEGATIVE_CASE = Case(id="n", utterance="Format my Python script.", expected=NO_ROUTE,
                     kind="negative", lang="en")
BUDGET_OVERRUN = {
    "type": "result", "subtype": "error_max_budget_usd", "is_error": True,
    "errors": ["Exceeded USD budget"], "total_cost_usd": 0.31, "num_turns": 4,
}


def test_dead_login_is_an_error_not_an_unrouted_case():
    """A sweep run on a dead login used to score every case as unrouted: the
    host's error result carries no skill call, and events had arrived."""
    outcome = case_result(CHECK_CASE, events("expired-login"), None)
    assert outcome.route is None
    assert "OAuth session expired and could not be refreshed" in outcome.error
    assert "`claude`" in outcome.error
    assert "`/login`" in outcome.error


def test_negative_case_does_not_pass_on_a_host_error():
    outcome = case_result(NEGATIVE_CASE, events("expired-login"), None)
    assert not outcome.passed
    assert classify([outcome]).totals == (0, 0)


def test_other_host_errors_name_the_host_reason_without_the_login_remedy():
    outcome = case_result(CHECK_CASE, [BUDGET_OVERRUN], None)
    assert outcome.error.startswith("claude failed: error_max_budget_usd: Exceeded USD budget")
    assert "/login" not in outcome.error


def test_an_answer_without_a_skill_call_stays_unrouted():
    outcome = case_result(NEGATIVE_CASE, events("unrouted-explore") + events("recorded-result"),
                          None)
    assert outcome.error is None
    assert outcome.passed


def test_a_route_outranks_every_error():
    stream = events("routed-check") + events("expired-login")
    outcome = case_result(CHECK_CASE, stream, "timed out after 90s")
    assert outcome.route == "proposal-check"
    assert outcome.error is None


def test_a_stream_error_stands_when_the_host_gave_no_reason():
    assert case_result(CHECK_CASE, [], "no events").error == "no events"
    timed_out = case_result(CHECK_CASE, events("unrouted-explore"), "timed out after 90s")
    assert timed_out.error == "timed out after 90s"


class StalledHost:
    """A `claude -p` stand-in that keeps writing events and never picks a skill."""

    def __init__(self, lines: list[str]):
        self.stdout = iter(lines)
        self.stderr = io.StringIO("")

    def terminate(self) -> None:
        pass

    def wait(self, **_kwargs) -> int:
        return 0

    def kill(self) -> None:
        pass


def read_until_the_limit(monkeypatch, tmp_path, stream: list[dict],
                         lines_in_time: int) -> tuple[list[dict], str | None]:
    """Drive the real reader over `stream` from a stand-in host, with a clock
    that passes the deadline on the line after the first `lines_in_time`."""
    lines = [json.dumps(e) for e in stream]
    monkeypatch.setattr(routing.subprocess, "Popen", lambda *_a, **_k: StalledHost(lines))
    ticks = iter([0.0] * (1 + lines_in_time))  # the deadline is set, then one reading per line
    monkeypatch.setattr(routing, "time", SimpleNamespace(monotonic=lambda: next(ticks, 1000.0)))
    return routing.stream_events(tmp_path, tmp_path, NEGATIVE_CASE.utterance, "haiku",
                                 timeout=90)


@pytest.mark.parametrize("lines_in_time", [0, 5], ids=["within-the-bound", "past-the-bound"])
def test_a_case_that_reaches_its_time_limit_is_an_error_not_unrouted(
        monkeypatch, tmp_path, lines_in_time):
    """The reader itself turns a passed deadline into an error. The tests above
    hand `case_result` that string ready-made, so they would stay green if the
    reader returned no error at the limit — and a negative case would then pass
    on a stalled host (testing-harness spec: Case reaches its time limit). The
    limit wins over the preparatory bound: five reads in time plus the one that
    finds the deadline passed is six non-skill calls, past the bound of three."""
    seen, error = read_until_the_limit(monkeypatch, tmp_path, events("unrouted-explore"),
                                       lines_in_time)

    assert error == "timed out after 90s"
    assert len(seen) == lines_in_time + 1
    outcome = case_result(NEGATIVE_CASE, seen, error)
    assert outcome.route is None
    assert outcome.error == "timed out after 90s"
    assert not outcome.passed
    assert classify([outcome]).totals == (0, 0)


def test_a_skill_invoked_past_the_bound_does_not_save_a_case_from_its_time_limit(
        monkeypatch, tmp_path):
    """What makes a case at its limit an error is that no route was recorded,
    not that no `proposal-*` skill was invoked: past the bound a skill call is
    no route, so the reader keeps reading and the limit still decides
    (testing-harness spec: Case reaches its time limit). Here `proposal-check`
    is the fifth call, past the bound of three, and the deadline passes on the
    line after it — so even the case that expected that skill does not pass."""
    peek = events("preparatory-then-route")[0]
    late_pick = [peek] * 4 + events("routed-check")

    seen, error = read_until_the_limit(monkeypatch, tmp_path, late_pick, lines_in_time=5)

    assert [p["skill"] for name, p in tool_calls(seen) if name == "Skill"] == ["proposal-check"]
    assert error == "timed out after 90s"
    for case in (CHECK_CASE, NEGATIVE_CASE):
        outcome = case_result(case, seen, error)
        assert outcome.route is None
        assert outcome.error == "timed out after 90s"
        assert not outcome.passed
        assert classify([outcome]).totals == (0, 0)


def test_a_malformed_skill_call_is_an_error():
    assert "carries no skill name" in case_result(
        CHECK_CASE, events("malformed-skill-call"), None).error


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


def test_report_is_due_only_once_a_measurement_completed():
    errored = result("e", "proposal-check", error="claude failed: no stderr")
    assert not report_due(classify([errored]))
    assert report_due(classify([errored, result("a", "proposal-check", route="proposal-check")]))


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


def test_report_states_the_epoch_count():
    results = [result("a", "proposal-check", route="proposal-check")]
    assert "3 epochs per case" in render_report(results, classify(results), "sonnet", epochs=3)


def test_a_conditions_change_is_not_a_comparison():
    results = [result("a", "proposal-check", route="proposal-check")]
    changed = render_report(results, classify(results), "sonnet", supersedes="55/60",
                            conditions_changed=True)
    assert "not comparable: 55/60" in changed
    assert "supersedes" not in changed


def test_partial_failure_renders_as_a_rate():
    results = [
        result("c", "proposal-ideate", route=None),
        result("c", "proposal-ideate", route="proposal-ideate"),
        result("c", "proposal-ideate", route="proposal-ideate"),
    ]
    assert "(1/3 epochs)" in render_report(results, classify(results), "sonnet")


# ---------- run outcome ------------------------------------------------------

EARLIER_REPORT = "measurements: 120 (119 correct), 3 epochs per case\n"


@pytest.fixture
def offline_rig(tmp_path, monkeypatch):
    """`routing.main` with the host taken out: each measurement returns the next
    of the given outcomes, relabelled for the case it stands in for, and the
    report and run log live in `tmp_path`."""
    report = tmp_path / "skill-routing.md"
    report.write_text(EARLIER_REPORT, encoding="utf-8")
    monkeypatch.setattr(routing, "REPORT_FILE", report)
    monkeypatch.setattr(routing, "LOG_DIR", tmp_path / "logs")
    monkeypatch.setattr(routing.shutil, "which", lambda _name: "claude")
    monkeypatch.setattr(routing, "isolated_config", lambda _prefix: nullcontext(tmp_path))

    def with_outcomes(*outcomes: Result) -> Path:
        queue = iter(outcomes)

        def measure(case: Case, *_args) -> Result:
            outcome = next(queue)
            return Result(case_id=case.id, expected=case.expected, kind=case.kind,
                          route=outcome.route, error=outcome.error)

        monkeypatch.setattr(routing, "measure", measure)
        return report

    return with_outcomes


DEAD_LOGIN = Result(case_id="", expected="", kind="", error="claude failed: Not logged in")


def test_a_run_with_nothing_measured_leaves_the_report_alone(offline_rig, tmp_path):
    report = offline_rig(DEAD_LOGIN, DEAD_LOGIN)
    status = routing.main(["--case", "review-canonical", "--epochs", "2", "--jobs", "1"])
    assert status == 1
    assert report.read_text(encoding="utf-8") == EARLIER_REPORT
    assert len(list((tmp_path / "logs").glob("*.json"))) == 1


def test_an_errored_measurement_fails_the_run(offline_rig):
    offline_rig(Result(case_id="", expected="", kind="", route="proposal-review"), DEAD_LOGIN)
    status = routing.main(["--case", "review-canonical", "--epochs", "2", "--jobs", "1",
                           "--no-report"])
    assert status == 1


def test_a_clean_run_succeeds(offline_rig):
    offline_rig(Result(case_id="", expected="", kind="", route="proposal-review"))
    status = routing.main(["--case", "review-canonical", "--epochs", "1", "--no-report"])
    assert status == 0


# ---------- staging ----------------------------------------------------------


def test_utterance_naming_one_file_stages_only_that_file():
    assert files_named("Please check microservice-technical-debt.md.") == [
        "microservice-technical-debt.md"
    ]


def test_utterance_naming_two_files_stages_both_in_order():
    named = files_named("Compare data-drift-detection.md with submission-email.txt please.")
    assert named == ["data-drift-detection.md", "submission-email.txt"]


def test_utterance_naming_nothing_stages_nothing_by_itself():
    assert files_named("I need something I can email tomorrow.") == []


def test_parenthesised_filename_is_still_named():
    assert files_named("Ein Student schickte das (submission-email.txt).") == [
        "submission-email.txt"
    ]


def test_unstageable_file_is_reported_not_silently_dropped():
    with pytest.raises(ValueError, match="cannot stage"):
        files_named("Please check my-own-thesis.md.")


def test_every_case_in_the_shipped_dataset_can_be_staged():
    for case in load_cases():
        files_named(case.utterance)


def test_staging_installs_every_skill_and_only_the_named_file(tmp_path):
    case = Case(id="x", utterance="Please check microservice-technical-debt.md.",
                expected="proposal-check", kind="canonical", lang="en")
    stage_workspace(tmp_path, case)
    assert sorted(p.name for p in tmp_path.glob("*.md")) == ["microservice-technical-debt.md"]
    installed = sorted(p.name for p in (tmp_path / ".claude" / "skills").iterdir())
    assert installed == installed_skills()


def test_staging_falls_back_to_one_proposal_when_nothing_is_named(tmp_path):
    case = Case(id="x", utterance="I need a PDF to email tomorrow.",
                expected="proposal-publish", kind="oblique", lang="en")
    stage_workspace(tmp_path, case)
    assert [p.name for p in tmp_path.glob("*.md")] == [DEFAULT_PROPOSAL]


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
