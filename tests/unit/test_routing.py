"""L0: the routing rig's verdict logic and dataset, without a model call.

The rig itself needs a host install and a subscription, so it never runs here.
What runs here is everything that decides what a run *means*: which skill an
event stream selected, how cases classify, whether a claude.ai account surface
voids a case or a sweep, and whether the dataset still covers every skill.
Stream fixtures live in `tests/unit/data/routing_streams/`. The stream reader
(`follow_stream`) is driven by stand-in hosts and by real `sys.executable`
children that write nothing, flood stderr, or leave a process holding their
stdout, so its deadline and its stderr file are tested without a host install.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import claude_runner
import pytest
import routing
from helpers import REPO
from routing import (
    DEFAULT_PROPOSAL,
    ISOLATION_CONDITIONS,
    KINDS,
    NO_ROUTE,
    Case,
    Result,
    case_result,
    classify,
    composition_problems,
    files_named,
    follow_stream,
    installed_skills,
    load_cases,
    misroutes,
    outcome_label,
    previous_isolation,
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


# ---------- claude.ai account surfaces (testing-harness spec: Isolated
# measurement environment) ----------------------------------------------------


def test_a_surface_outranks_a_recorded_route():
    """A route chosen with synced competitors on offer is not a measurement."""
    outcome = case_result(CHECK_CASE, events("claudeai-surfaces") + events("routed-check"), None)
    assert outcome.route is None
    assert "claude.ai Claude Docs" in outcome.error
    assert "opt-outs did not hold" in outcome.error
    assert classify([outcome]).totals == (0, 0)


def test_a_negative_case_does_not_pass_on_a_surface():
    outcome = case_result(NEGATIVE_CASE, events("claudeai-surfaces"), None)
    assert not outcome.passed
    assert classify([outcome]).totals == (0, 0)


class RecordingHost:
    """A stand-in host that logs what the reader does to it: how many lines
    were read, and the order of terminate, wait and kill. With `stubborn` it
    outlives the grace, so the kill path runs."""

    def __init__(self, lines: list[str], stubborn: bool = False):
        self.read, self.calls, self.stubborn = 0, [], stubborn
        self.stdout = self._lines(lines)

    def _lines(self, lines):
        for line in lines:
            self.read += 1
            yield line + "\n"

    def terminate(self) -> None:
        self.calls.append("terminate")

    def wait(self, timeout=None) -> int:
        self.calls.append("wait")
        if self.stubborn and timeout is not None:
            raise subprocess.TimeoutExpired("claude", timeout)
        return -15

    def kill(self) -> None:
        self.calls.append("kill")


def test_follow_stream_stops_at_the_first_accepted_event_and_reads_no_further(
        monkeypatch, tmp_path):
    lines = [json.dumps({"n": n}) for n in range(5)]
    host = RecordingHost(lines, stubborn=True)
    monkeypatch.setattr(routing.subprocess, "Popen", lambda *_a, **_k: host)
    seen = follow_stream(["claude"], cwd=tmp_path, env={}, timeout=60,
                         stop=lambda evs: evs[-1]["n"] == 2)
    assert seen.stopped
    assert not seen.timed_out
    assert seen.events == [{"n": 0}, {"n": 1}, {"n": 2}]
    assert host.read == 3
    assert host.calls == ["terminate", "wait", "kill", "wait"]


def test_follow_stream_skips_lines_that_are_not_json(monkeypatch, tmp_path):
    host = RecordingHost(["host warning: not json", json.dumps({"n": 0})])
    monkeypatch.setattr(routing.subprocess, "Popen", lambda *_a, **_k: host)
    seen = follow_stream(["claude"], cwd=tmp_path, env={}, timeout=60, stop=lambda _evs: False)
    assert seen.events == [{"n": 0}]


def test_follow_stream_stops_the_host_when_the_reader_fails(monkeypatch, tmp_path):
    """A malformed skill call raises out of the rig's stop condition; the host
    must not outlive the reader."""
    host = RecordingHost([json.dumps(e) for e in events("malformed-skill-call")])
    monkeypatch.setattr(routing.subprocess, "Popen", lambda *_a, **_k: host)
    with pytest.raises(ValueError, match="carries no skill name"):
        routing.stream_events(tmp_path, tmp_path, CHECK_CASE.utterance, "haiku", 90)
    assert host.calls[0] == "terminate"


def test_follow_stream_lets_a_finished_host_exit_on_its_own(monkeypatch, tmp_path):
    host = RecordingHost([json.dumps({"n": 0})])
    monkeypatch.setattr(routing.subprocess, "Popen", lambda *_a, **_k: host)
    seen = follow_stream(["claude"], cwd=tmp_path, env={}, timeout=60, stop=lambda _evs: False)
    assert (seen.stopped, seen.timed_out) == (False, False)
    assert "terminate" not in host.calls


def test_follow_stream_stops_a_silent_host_at_the_deadline(tmp_path):
    """The deadline holds even when the host writes nothing at all: the rig's
    old loop looked at the clock only when a line arrived."""
    silent = [sys.executable, "-c", "import time; time.sleep(60)"]
    started = time.monotonic()
    seen = follow_stream(silent, cwd=tmp_path, env=dict(os.environ), timeout=0.5,
                         stop=lambda _evs: False)
    assert seen.timed_out
    assert not seen.stopped
    assert seen.events == []
    assert time.monotonic() - started < 0.5 + routing.STOP_GRACE_S


@pytest.mark.skipif(os.name != "posix", reason="process groups are POSIX")
def test_follow_stream_deadline_holds_against_a_child_that_inherited_stdout(tmp_path):
    """A process the host started keeps the host's stdout open after the host
    is stopped. The deadline still ends the read: the host leads its own
    process group, and what is left of it is killed at the deadline."""
    host = [sys.executable, "-c",
            "import subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
            "time.sleep(60)"]
    started = time.monotonic()
    seen = follow_stream(host, cwd=tmp_path, env=dict(os.environ), timeout=1,
                         stop=lambda _evs: False)
    assert seen.timed_out
    assert time.monotonic() - started < 1 + routing.STOP_GRACE_S


def test_follow_stream_reads_past_a_flood_on_stderr(tmp_path):
    """stderr goes to a file, so a host that writes more than a pipe holds
    before its first event cannot block the reader."""
    noisy = [sys.executable, "-c",
             "import sys, time; sys.stderr.write('x' * 200_000); sys.stderr.flush(); "
             "print('{\"type\": \"system\", \"subtype\": \"init\"}', flush=True); time.sleep(60)"]
    seen = follow_stream(noisy, cwd=tmp_path, env=dict(os.environ), timeout=20,
                         stop=lambda evs: bool(evs))
    assert seen.events == [{"type": "system", "subtype": "init"}]
    assert seen.stopped
    assert not seen.timed_out
    assert len(seen.stderr) >= 200_000


def test_a_case_is_stopped_at_the_first_surface_before_any_skill_call(monkeypatch, tmp_path):
    """The tagged command-list change arrives before the model's turn: the case
    ends there, and the skill call after it is never read."""
    stream = [events("clean-init")[0], events("claudeai-surfaces")[1], *events("routed-check")]
    host = RecordingHost([json.dumps(e) for e in stream])
    monkeypatch.setattr(routing.subprocess, "Popen", lambda *_a, **_k: host)
    seen, error = routing.stream_events(tmp_path, tmp_path, CHECK_CASE.utterance, "haiku", 90)
    assert seen == stream[:2]
    assert host.read == 2
    assert "terminate" in host.calls
    assert "synced skill 'docs'" in error
    assert route_from_events(seen) is None
    assert case_result(CHECK_CASE, seen, error).error == error


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


def test_report_records_its_isolation_conditions(tmp_path):
    results = [result("a", "proposal-check", route="proposal-check")]
    text = render_report(results, classify(results), "sonnet")
    assert f"- isolation: {ISOLATION_CONDITIONS}\n" in text
    report = tmp_path / "skill-routing.md"
    report.write_text(text, encoding="utf-8")
    assert previous_isolation(report) == ISOLATION_CONDITIONS


def test_a_report_without_an_isolation_line_records_none(tmp_path):
    report = tmp_path / "skill-routing.md"
    report.write_text("measurements: 120 (119 correct), 3 epochs per case\n", encoding="utf-8")
    assert previous_isolation(report) is None
    assert previous_isolation(tmp_path / "absent.md") is None


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
    monkeypatch.setattr(routing, "REPO", tmp_path)  # the report path is printed relative to it
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


ROUTED = Result(case_id="", expected="", kind="", route="proposal-review")


def raw_payload(tmp_path: Path) -> dict:
    [log] = (tmp_path / "logs").glob("*.json")
    return json.loads(log.read_text(encoding="utf-8"))


def test_synced_content_after_the_sweep_voids_every_case(offline_rig, tmp_path):
    """testing-harness spec: Synced content found after a sweep — a case
    started after the content landed may have loaded it with no tag. The raw
    results keep what each case measured: its route, and its own error."""
    report = offline_rig(ROUTED, DEAD_LOGIN)
    (tmp_path / "plugins" / "synced" / "y").mkdir(parents=True)
    status = routing.main(["--case", "review-canonical", "--epochs", "2", "--jobs", "1"])
    assert status == 1
    assert report.read_text(encoding="utf-8") == EARLIER_REPORT
    results = raw_payload(tmp_path)["results"]
    assert [raw["route"] for raw in results] == ["proposal-review", None]
    for raw in results:
        assert raw["error"].startswith("synced content in the sweep's configuration")
        assert "plugins/synced/y" in raw["error"]
    assert results[1]["error"].endswith("The case's own error: claude failed: Not logged in")
    assert classify([Result(**raw) for raw in results]).totals == (0, 0)


def test_the_raw_results_record_the_isolation_conditions(offline_rig, tmp_path):
    offline_rig(ROUTED)
    routing.main(["--case", "review-canonical", "--epochs", "1", "--no-report"])
    assert raw_payload(tmp_path)["isolation"] == ISOLATION_CONDITIONS


@pytest.mark.parametrize("outgoing", [
    EARLIER_REPORT,
    EARLIER_REPORT + "- isolation: ambient claude.ai surfaces open\n",
], ids=["no-isolation-line", "other-isolation"])
def test_other_isolation_conditions_are_not_comparable_without_the_flag(
        offline_rig, outgoing):
    report = offline_rig(ROUTED)
    report.write_text(outgoing, encoding="utf-8")
    assert routing.main(["--case", "review-canonical", "--epochs", "1"]) == 0
    text = report.read_text(encoding="utf-8")
    assert "measured under different conditions, not comparable: 119/120" in text
    assert "supersedes" not in text


def test_the_same_isolation_conditions_supersede(offline_rig):
    report = offline_rig(ROUTED)
    report.write_text(f"{EARLIER_REPORT}- isolation: {ISOLATION_CONDITIONS}\n", encoding="utf-8")
    assert routing.main(["--case", "review-canonical", "--epochs", "1"]) == 0
    text = report.read_text(encoding="utf-8")
    assert "supersedes: 119/120" in text
    assert "not comparable" not in text


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


def test_polish_case_is_the_dev_scenarios_request():
    """The case exists to reproduce a dev-run routing miss in the cheaper rig;
    a reworded copy would measure a different sentence from the one that failed."""
    case = next(c for c in load_cases() if c.id == "write-polish-collision")
    assert case.utterance == claude_runner.SCENARIOS["write_repair_citations"]["request"]


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
