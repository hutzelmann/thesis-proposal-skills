"""L0 coverage for the cache reuse probe (harness/cache_probe.py) and its verdict.

No test here calls a metered model or opens a socket: the pass rule and the
worst-case estimate are pure functions, the gate is exercised with Inspect made
unimportable, and the one end-to-end run uses Inspect's offline `mockllm/model`.
"""

from __future__ import annotations

import gc
import re
import sys
from itertools import pairwise
from types import SimpleNamespace

import cache_probe as cp
import pytest
import support
from helpers import shipped_registry
from l1_checks import verdict_cache_reuse

# ---------- the pass rule (testing-harness spec: Cache reuse probe) ------------


def test_reuse_below_the_threshold_fails_naming_both_shares():
    # the first call writes; the two after it read 60 of every 100 prompt tokens
    passed, why = verdict_cache_reuse([(0, 1000, 0), (300, 100, 600), (200, 200, 600)])
    assert not passed
    assert "60.0%" in why
    assert "80%" in why


def test_no_cache_write_fails_saying_so():
    passed, why = verdict_cache_reuse([(2000, 0, 0), (3000, 0, 0)])
    assert not passed
    assert "no call wrote the cache" in why


def test_reuse_at_the_threshold_passes():
    passed, why = verdict_cache_reuse([(4000, 0, 0), (0, 4200, 0), (100, 100, 800),
                                       (0, 200, 800)])
    assert passed, why
    assert "80.0%" in why
    assert "call 2" in why, "the share counts only the calls after the first write"


def test_a_write_on_the_last_call_leaves_nothing_to_read():
    passed, why = verdict_cache_reuse([(2000, 0, 0), (0, 4100, 0)])
    assert not passed
    assert "call 2 of 2" in why


# ---------- the replay ----------------------------------------------------------


def test_the_replay_is_deterministic_and_sized_as_designed():
    replay = cp.build_replay()
    assert replay == cp.build_replay()
    sizes = cp.prompt_sizes(replay)
    assert len(sizes) == cp.TURNS == 10
    assert sizes[0] == pytest.approx(2200, abs=50)
    assert sizes[-1] == pytest.approx(11200, abs=50)
    assert sum(sizes) == pytest.approx(67000, abs=500)
    assert all(b - a == pytest.approx(1000, abs=10) for a, b in pairwise(sizes))


def test_every_second_assistant_turn_carries_no_text():
    replay = cp.build_replay()
    assert all(turn.text for turn in replay[::2])
    assert not any(turn.text for turn in replay[1::2])
    assert {turn.function for turn in replay} == {"bash", "text_editor"}


def test_the_estimator_overstates_english_text():
    """The worst case is a bound only while the estimate never undercounts. The
    floor counts every word, every punctuation mark and every newline as a token
    of its own, which no tokenizer beats on this text: it fails once
    CHARS_PER_TOKEN drifts to 5, where whitespace-split words alone still pass."""
    note = cp.build_replay()[0].result
    floor = len(re.findall(r"\w+|[^\w\s]|\n", note))
    assert cp.estimate_tokens(note) >= floor


# ---------- the worst-case estimate --------------------------------------------


@pytest.fixture
def default_models():
    registry = shipped_registry()
    return registry, cp.select_probe_models(registry, None)


def test_default_selection_is_the_cheap_and_mid_anthropic_rows(default_models):
    _, models = default_models
    assert sorted(m.tier for m in models) == ["cheap", "mid"]
    assert {m.family for m in models} == {support.PINNED_FAMILY}


def test_worst_case_estimate_at_registry_prices(default_models):
    registry, models = default_models
    sizes = cp.prompt_sizes(cp.build_replay())
    bound = {"cheap": 0.09, "mid": 0.17}  # design D1, per mechanism
    for m in models:
        usd = cp.worst_case_usd(sizes, support.model_price(registry, m.id))
        assert usd <= bound[m.tier], (m.id, usd)
    report = cp.worst_case_report(models, registry, sizes)
    assert report.total <= 0.26
    assert report.unknown_models == ()


def test_worst_case_charges_every_prompt_token_at_the_write_price():
    price = support.Price(input_price=1.0, output_price=5.0, cache_read_price=0.1,
                          cache_write_price=1.25)
    # 3000 prompt tokens written, 2 calls of 16 output tokens each
    assert cp.worst_case_usd([1000, 2000], price) == pytest.approx(
        (3000 * 1.25 + 32 * 5.0) / 1e6)


def test_a_non_anthropic_row_is_refused():
    registry = shipped_registry()
    other = next(m for m in registry.models if m.enabled and m.family != support.PINNED_FAMILY)
    with pytest.raises(ValueError, match="not an Anthropic row"):
        cp.select_probe_models(registry, [other.id])


def test_an_anthropic_row_is_selected_by_its_id_suffix():
    """`--models` takes suffixes as the matrix does, so a frontier row the
    default leaves out can be probed by name."""
    registry = shipped_registry()
    frontier = next(m for m in registry.models if m.enabled and m.tier == "frontier"
                    and m.family == support.PINNED_FAMILY)
    suffix = frontier.id.rsplit("/", 1)[-1]
    assert cp.select_probe_models(registry, [suffix]) == [frontier]


# ---------- the gate: no model call before approval ------------------------------


@pytest.fixture
def no_inspect(monkeypatch):
    """Any import of Inspect, or any run, fails the test."""
    monkeypatch.setitem(sys.modules, "inspect_ai", object())
    monkeypatch.setattr(cp, "run_probe", lambda *_args: pytest.fail("a probe run started"))


@pytest.mark.usefixtures("no_inspect")
def test_estimate_only_makes_no_model_call(capsys):
    assert cp.main(["--estimate-only"]) == 0
    out = capsys.readouterr().out
    assert "Worst-case cost" in out
    assert "TOTAL" in out
    assert "2,200 … 11,200" in out


@pytest.mark.usefixtures("no_inspect")
def test_a_declined_prompt_makes_no_model_call(monkeypatch, capsys):
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert cp.main([]) == 1
    assert "aborted before any metered call" in capsys.readouterr().out


@pytest.mark.usefixtures("no_inspect")
@pytest.mark.parametrize("argv", [[], ["--mechanism", "marker"]], ids=["default", "explicit"])
def test_marker_is_the_default_and_its_estimate_makes_no_model_call(capsys, argv):
    """The probe re-checks the matrix's mechanism, `marker` under the
    Bedrock/Vertex pin (adopted after probe 2)."""
    assert cp.DEFAULT_MECHANISM == support.CACHE_MECHANISM == "marker"
    assert cp.main([*argv, "--estimate-only"]) == 0
    out = capsys.readouterr().out
    assert "mechanism: marker" in out
    assert "providers: amazon-bedrock then google-vertex, no fallback beyond them" in out
    total = next(line for line in out.splitlines() if line.strip().startswith("TOTAL"))
    assert float(total.split("$")[1]) <= 0.26


@pytest.mark.usefixtures("routable_openrouter")
def test_a_marker_probe_builds_its_models_as_the_matrix_does(monkeypatch, tmp_path):
    """The probe hands Inspect the matrix's routed Model: the pin under the
    registry ID, with the breakpoint wrapper installed. The log's metadata names
    the mechanism, which the pin in model_args cannot show."""
    import inspect_ai
    import openrouter_cache

    sent = []
    monkeypatch.setattr(inspect_ai, "eval",
                        lambda _task, model, **kw: sent.append((model, kw["metadata"])) or [])
    registry = shipped_registry()
    models = cp.select_probe_models(registry, None)
    args = SimpleNamespace(mechanism="marker", log_dir=str(tmp_path))
    assert cp.run_probe(models, cp.build_replay(), args) == []
    [(built, metadata)] = sent
    assert [str(m) for m in built] == [m.id for m in models]
    assert all(m.model_args == {"provider": support.provider_pin()} for m in built)
    assert openrouter_cache.installed()
    assert metadata == {"cache_mechanism": "marker"}


@pytest.mark.usefixtures("no_inspect")
def test_a_non_anthropic_selection_exits_2(capsys):
    other = next(m for m in shipped_registry().models
                 if m.enabled and m.family != support.PINNED_FAMILY)
    assert cp.main(["--models", other.id, "--estimate-only"]) == 2
    assert "not an Anthropic row" in capsys.readouterr().err


# ---------- reading a probe log ----------------------------------------------------


def _usage(tin, cwrite, cread):
    return SimpleNamespace(input_tokens=tin, output_tokens=16,
                           input_tokens_cache_write=cwrite, input_tokens_cache_read=cread)


def test_call_usage_counts_only_the_calls_that_returned_usage():
    """A call that raised leaves a model event without usage (probe 1's 404):
    it is no call made, so it neither counts nor scores."""
    events = [
        SimpleNamespace(event="model", output=SimpleNamespace(usage=_usage(2200, 0, 0))),
        SimpleNamespace(event="model", output=SimpleNamespace(usage=_usage(0, 4200, 0))),
        SimpleNamespace(event="model", output=SimpleNamespace(usage=None)),
    ]
    assert cp.call_usage(events) == [(2200, 0, 0), (0, 4200, 0)]


PROBED = "openrouter/lab/probed-1"


def _call(tin, cwrite, cread):
    return SimpleNamespace(event="model", model=PROBED, call=None,
                           output=SimpleNamespace(usage=_usage(tin, cwrite, cread)))


def _probe_log(calls, error=None, status="success"):
    """A stand-in probe log: one sample whose model events carry `calls`. With
    an `error`, the call that raised it leaves one more model event, without
    usage, as in the real probe-1 logs."""
    tool = SimpleNamespace(event="tool", model=None)
    events = [e for c in calls for e in (_call(*c), tool)]
    if error is not None:
        events.append(SimpleNamespace(event="model", model=PROBED, call=None,
                                      output=SimpleNamespace(usage=None)))
    sample = SimpleNamespace(events=events, error=error, model_usage={})
    return SimpleNamespace(eval=SimpleNamespace(model=PROBED, task="cache_probe"),
                           stats=SimpleNamespace(model_usage={}), samples=[sample],
                           status=status, error=None, location="")


def _api_error(code: int, text: str) -> SimpleNamespace:
    """A sample error as Inspect records it: the OpenAI SDK's message."""
    return SimpleNamespace(message=f"Error code: {code} - {{'error': {{'message': '{text}'}}}}")


# a write on call 1, then reads covering 85% of each later prompt
CACHED = [(1500, 2200, 0)] + [(150, 0, 850)] * (cp.TURNS - 1)


def test_a_full_cached_replay_passes():
    result = cp.summarize(_probe_log(CACHED), shipped_registry())
    assert result.status == cp.PASS, result.explanation
    assert result.passed
    assert result.providers == {support.UNRECORDED: cp.TURNS}


def test_a_400_rejecting_the_request_is_a_scored_failure():
    """With fail_on_error=False Inspect marks the log 'success' even when the
    sample raised: the probe must not score the calls made before the error. A
    400 rejects the request the mechanism shaped, so it fails the mechanism."""
    error = _api_error(400, "cache_control not allowed here")
    result = cp.summarize(_probe_log(CACHED[:7], error=error), shipped_registry())
    assert result.status == cp.FAIL
    assert result.explanation == (
        f"the replay errored after 7 of {cp.TURNS} answered call(s): {error.message}")


def test_a_routing_404_on_the_first_call_is_untested_not_a_caching_failure():
    """Probe 1's shape: one model event without usage and a 404 from routing."""
    error = _api_error(404, "No endpoints found for anthropic/claude-haiku-4.5")
    result = cp.summarize(_probe_log([], error=error), shipped_registry())
    assert result.status == cp.UNTESTED
    assert not result.passed
    assert f"after 0 of {cp.TURNS} answered call(s)" in result.explanation
    assert "No endpoints found" in result.explanation
    assert "no call wrote the cache" not in result.explanation


@pytest.mark.parametrize("code", [401, 402, 404, 429, 503])
def test_account_and_api_errors_leave_the_mechanism_untested(code):
    result = cp.summarize(_probe_log(CACHED[:3], error=_api_error(code, "x")),
                          shipped_registry())
    assert result.status == cp.UNTESTED


def test_an_error_without_an_http_status_is_untested():
    error = SimpleNamespace(message="RuntimeError: sandbox went away")
    result = cp.summarize(_probe_log(CACHED[:2], error=error), shipped_registry())
    assert result.status == cp.UNTESTED
    assert cp.http_status(error.message) is None


def test_a_partial_replay_is_never_scored():
    result = cp.summarize(_probe_log(CACHED[:5]), shipped_registry())
    assert result.status == cp.UNTESTED
    assert result.explanation == f"the replay recorded 5 of {cp.TURNS} calls"


def test_an_unfinished_run_is_untested_naming_its_status():
    result = cp.summarize(_probe_log(CACHED, status="cancelled"), shipped_registry())
    assert result.status == cp.UNTESTED
    assert result.explanation == "the probe run did not finish: cancelled"


def _result(status):
    return cp.ProbeResult("m", status, "why", {}, None, "")


@pytest.mark.parametrize(("statuses", "code"), [
    ([cp.PASS, cp.PASS], 0),
    ([cp.PASS, cp.UNTESTED], cp.EXIT_UNTESTED),
    ([cp.FAIL, cp.UNTESTED], 1),  # a scored failure outranks an untested model
    ([cp.PASS, cp.FAIL], 1),
    ([], cp.EXIT_UNTESTED),  # no result is no verdict
])
def test_exit_status_tells_a_scored_failure_from_an_untested_model(statuses, code):
    assert cp.exit_status([_result(s) for s in statuses]) == code
    assert cp.EXIT_UNTESTED not in (0, 1, 2), "distinct from pass, fail and usage error"


def test_an_untested_model_prints_as_untested(capsys):
    cp.print_results([_result(cp.UNTESTED)], "marker")
    out = capsys.readouterr().out
    assert "UNTESTED  m" in out
    assert "no caching verdict" in out
    assert "FAIL" not in out


# Inspect 0.3.250's in-process eval leaves its log reader and an anyio stream for
# the garbage collector, which reports them as unraisable ResourceWarnings. The
# leak is the dependency's, so the ignore is scoped to the one test that runs an
# eval, and the test collects the garbage itself so nothing reaches a later test.
@pytest.mark.filterwarnings("ignore::ResourceWarning")
@pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
def test_the_main_path_runs_offline_and_reports_no_cache_write(tmp_path, monkeypatch, capsys):
    """End to end against Inspect's mock model: it records no cache usage, so the
    probe must fail with the spec's 'no call wrote the cache'."""
    monkeypatch.chdir(tmp_path)  # Inspect loads the nearest .env; there is none here
    monkeypatch.setenv("INSPECT_DISPLAY", "none")
    monkeypatch.setattr(cp, "MODEL_OVERRIDE", "mockllm/model")
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    log_dir = tmp_path / "logs"
    code = cp.main(["--log-dir", str(log_dir)])
    gc.collect()
    assert code == 1
    out = capsys.readouterr().out
    assert "FAIL  mockllm/model" in out
    assert "no call wrote the cache (10 call(s) made)" in out
    assert "unpriced" in out, "the mock is in no registry"
    assert list(log_dir.glob("*.eval")), "the probe log lands in its own directory"
