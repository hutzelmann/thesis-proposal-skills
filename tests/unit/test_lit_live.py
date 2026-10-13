"""L0: `poe lit-live` (`harness/lit_live.py`) — the live check's verdicts, exit
codes, key gate and privacy. Every source is stubbed in-process; no socket is
opened. The real requests happen only when a developer runs the task by hand
(widen-lit-live design D6).
"""

from __future__ import annotations

import dataclasses
import tomllib
from pathlib import Path

import common
import lit_live
import pytest
import search
import snowball

REPO = Path(__file__).resolve().parents[2]
ORDER = ["dblp", "crossref", "arxiv", "semantic_scholar", "opencitations", "openalex"]
KEY = "oa-key-7f3a-NEVER-PRINTED"
# what a raised error's own text may carry: server text, an address, a contact,
# a URL, and a line break that would forge a line of its own
LEAKY = ("HTTP/1.1 <html>verify 192.0.2.7 erika.musterfrau@example.org "
         "https://dblp.org/search?q=x\r\ndblp ok (3)")
LEAKED = ("<html>", "verify", "192.0.2.7", "erika.musterfrau", "https://", "q=x")
HITS = [{"title": "Agents for Penetration Testing", "_source": "stub"}] * 3


def error(kind: str | None, status: int | None = None) -> common.SourceError:
    return common.SourceError(f"source: {LEAKY}", kind=kind, status=status)


class Stub:
    """A source module that answers both probe requests with one fixed result."""

    def __init__(self, result) -> None:
        self.result = result
        self.calls: list[tuple] = []

    def _answer(self, *args) -> list:
        self.calls.append(args)
        if isinstance(self.result, BaseException):
            raise self.result
        return list(self.result)

    def search(self, query, limit):
        return self._answer(query, limit)

    def references(self, doi, limit):
        return self._answer(doi, limit)


@pytest.fixture
def run(monkeypatch, capsys):
    """Run `main` with each named source answering through a stub, every other
    source answering `HITS`. Returns (exit code, stdout, stderr, stubs)."""
    def go(*argv: str, **answers):
        stubs = {name: Stub(answers.get(name, HITS)) for name in lit_live.PROBES}
        monkeypatch.setattr(lit_live, "PROBES", {
            name: dataclasses.replace(probe, module=stubs[name])
            for name, probe in lit_live.PROBES.items()
        })
        code = lit_live.main(list(argv))
        out, err = capsys.readouterr()
        return code, out, err, stubs
    return go


# ---------- the verdict table (design D4) -----------------------------------


@pytest.mark.parametrize(("raised", "label", "needs_change"), [
    (error("network"), "busy (network)", False),
    (error("http", 429), "busy (HTTP 429)", False),
    (error("http", 500), "busy (HTTP 500)", False),
    (error("http", 502), "busy (HTTP 502)", False),
    (error("http", 503), "busy (HTTP 503)", False),
    (error("http", 504), "busy (HTTP 504)", False),  # a gateway timeout, not an API change
    (error("http", 599), "busy (HTTP 599)", False),
    (error("http", 400), "http (HTTP 400)", True),
    (error("http", 404), "http (HTTP 404)", True),
    (error("http", 410), "http (HTTP 410)", True),
    (error("http", 499), "http (HTTP 499)", True),
    (error("challenge", 200), "challenge (HTTP 200)", True),
    (error("unexpected", 200), "unexpected (HTTP 200)", True),
    (error("unexpected"), "unexpected", True),  # an answer no parser anticipated
    (error("malformed", 200), "malformed (HTTP 200)", True),
    (error(None), "unclassified", True),  # a module's own raise, e.g. a missing key
    (error("a-kind-from-the-future", 200), "unclassified", True),
    (KeyError(LEAKY), "crashed (KeyError)", True),
    (AttributeError(LEAKY), "crashed (AttributeError)", True),
])
def test_an_error_maps_to_its_verdict(raised, label, needs_change):
    assert lit_live.classify_error(raised) == lit_live.Verdict(label, needs_change)


def test_busy_covers_everything_the_client_retries():
    """What the shipped client retries is transient here too; busy is wider
    (429 and every 5xx), since a server fault never means the API changed."""
    for code in common.RETRY_CODES:
        assert not lit_live.classify_error(error("http", code)).needs_change


@pytest.mark.parametrize(("results", "label", "needs_change"), [
    (HITS, "ok (3)", False),
    (HITS[:1], "ok (1)", False),
    ([], "empty (0)", True),  # parser or query drift, never a pass
])
def test_results_map_to_their_verdict(results, label, needs_change):
    assert lit_live.classify_results(results) == lit_live.Verdict(label, needs_change)


# ---------- output and exit code (D5) ---------------------------------------


def test_every_source_ok_prints_one_line_each_in_order_and_exits_zero(run, monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", KEY)
    code, out, err, _ = run()
    assert code == 0
    assert out.splitlines() == [f"{name} ok (3)" for name in ORDER]
    assert err == ""


def test_transient_failures_and_a_missing_key_exit_zero(run):
    code, out, _, _ = run(semantic_scholar=error("http", 429), crossref=error("network"))
    assert code == 0
    assert out.splitlines() == [
        "dblp ok (3)",
        "crossref busy (network)",
        "arxiv ok (3)",
        "semantic_scholar busy (HTTP 429)",
        "opencitations ok (3)",
        "openalex skipped (no key)",
    ]


@pytest.mark.parametrize("answer", [
    error("challenge", 200), error("unexpected", 200), error("malformed", 200),
    error("http", 404), error(None), [], KeyError("x"),
])
def test_any_change_signal_exits_one(run, answer):
    code, _, _, _ = run(arxiv=answer)
    assert code == 1


def test_unpassed_dblp_verification_still_exits_one(run):
    """Today's meaning of the task's exit 1 survives the widening."""
    code, out, _, _ = run("--sources", "dblp", dblp=error("challenge", 200))
    assert (code, out) == (1, "dblp challenge (HTTP 200)\n")


def test_sources_selects_a_subset_and_asks_no_one_else(run):
    code, out, _, stubs = run("--sources", "opencitations, arxiv")
    assert code == 0
    assert out.splitlines() == ["arxiv ok (3)", "opencitations ok (3)"]
    assert [name for name, stub in stubs.items() if stub.calls] == ["arxiv", "opencitations"]


def test_an_unknown_source_is_a_usage_error(run, capsys):
    with pytest.raises(SystemExit) as exit_info:
        run("--sources", "dblp,scholar")
    assert exit_info.value.code == 2
    err = capsys.readouterr().err
    assert "scholar" in err
    assert all(name in err for name in ORDER)


def test_an_empty_selection_is_a_usage_error_not_a_pass(run):
    """A check that asked no source must not report success."""
    with pytest.raises(SystemExit) as exit_info:
        run("--sources", " , ")
    assert exit_info.value.code == 2


def test_no_server_text_reaches_the_output(run, monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", KEY)
    _, out, err, _ = run(dblp=error("challenge", 200), crossref=error("http", 503),
                         arxiv=error("unexpected", 200), semantic_scholar=error(None),
                         opencitations=ValueError(LEAKY), openalex=error("malformed", 200))
    assert len(out.splitlines()) == len(ORDER)
    for fragment in LEAKED:
        assert fragment not in out + err


# ---------- the probes (D2) and the key gate (D3) ---------------------------


def test_each_probe_sends_its_one_fixed_request(run, monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", KEY)
    _, _, _, stubs = run()
    seed = (lit_live.SEED_DOI, lit_live.LIMIT)
    query = (lit_live.QUERY, lit_live.LIMIT)
    assert {name: stub.calls for name, stub in stubs.items()} == {
        name: [seed if name == "opencitations" else query] for name in ORDER
    }


def test_every_lit_search_source_module_has_a_probe():
    """A source added to the skill without a live probe would leave the live
    check silently narrower than the skill."""
    shipped = {**search.SEARCH_SOURCES, **snowball.GRAPH_SOURCES}
    assert list(lit_live.PROBES) == ORDER
    assert {name: probe.module for name, probe in lit_live.PROBES.items()} == shipped


def test_only_openalex_is_key_gated():
    assert {name: probe.key for name, probe in lit_live.PROBES.items() if probe.key} == {
        "openalex": "OPENALEX_API_KEY"}


def test_openalex_without_a_key_is_skipped_and_never_asked(run):
    code, out, _, stubs = run("--sources", "openalex")
    assert (code, out) == (0, "openalex skipped (no key)\n")
    assert stubs["openalex"].calls == []


def test_openalex_key_resolves_like_the_shipped_scripts(run, monkeypatch, tmp_path):
    """The key file that `$THESIS_PROPOSAL_KEYS` names is found through
    `common.get_key`, and its value never reaches the output."""
    keys = tmp_path / "api-keys.env"
    keys.write_text(f"OPENALEX_API_KEY={KEY}\n", encoding="utf-8")
    monkeypatch.setenv(common.KEY_FILE_ENV, str(keys))
    code, out, err, stubs = run("--sources", "openalex")
    assert (code, out) == (0, "openalex ok (3)\n")
    assert stubs["openalex"].calls == [(lit_live.QUERY, lit_live.LIMIT)]
    assert KEY not in out + err


# ---------- the poe task ----------------------------------------------------


def test_poe_task_runs_the_live_check_without_the_dev_env():
    """A plain command string with no task-level `envfile`, and no global one,
    so the repository's dev `.env` (and any key in it) never reaches the check."""
    poe = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["poe"]
    assert poe["tasks"]["lit-live"] == "python3 harness/lit_live.py"
    assert "envfile" not in poe
