"""L0: the orchestrators' degradation contract — `search.py` and `snowball.py`.
Candidates alone on stdout, notes on stderr, a blocked source named with its
cause and never counted as a zero-hit contributor, an unanticipated failure
named by its type only, each snowball note once per run, exit codes unchanged.
Sources are stubbed in-process; no network.
"""

from __future__ import annotations

import common
import openalex
import pytest
import search
import snowball

QUERY = "SECRET-QUERY-7f3a"
# what an unanticipated error's text may carry: server text, an address, a
# contact, and a line break that would forge a note of its own
LEAKY = f"HTTP/1.1 {QUERY} 192.0.2.7 erika.musterfrau@example.org\r\nnote: X-Injected"
LEAKED = (QUERY, "192.0.2.7", "erika.musterfrau", "X-Injected")
CHALLENGE = common.SourceError(
    "dblp: API returned an Anubis browser-verification page (HTTP 200, text/html), "
    "not JSON, and automatic verification did not pass",
    kind="challenge", status=200, media_type="text/html")


class Stub:
    def __init__(self, result):
        self.result = result

    def search(self, _query, limit):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result[:limit]


def paper(title: str, source: str) -> dict:
    doi = "10.1/" + common.normalize_title(title).replace(" ", "-")
    return common.entry(title=title, source=source, doi=doi,
                        authors=[{"family": "Musterfrau", "given": "Erika"}], year=2025)


@pytest.fixture
def run(monkeypatch, capsys):
    def go(**sources):
        monkeypatch.setattr(search, "SEARCH_SOURCES", {n: Stub(r) for n, r in sources.items()})
        code = search.main([QUERY, "--sources", ",".join(sources)])
        out, err = capsys.readouterr()
        return code, out, err
    return go


def test_blocked_dblp_degrades_with_the_browser_hint(run):
    code, out, err = run(dblp=CHALLENGE,
                         crossref=[paper("Agents for Penetration Testing", "crossref")])
    assert code == 0
    assert out.startswith("- id: ")
    assert "note" not in out
    assert "dblp" not in out
    note = next(line for line in err.splitlines() if line.startswith("note:"))
    assert note == (
        "note: source degraded — dblp: API returned an Anubis browser-verification page "
        "(HTTP 200, text/html), not JSON, and automatic verification did not pass. "
        'A normal browser may still pass it (see "If a source asks for browser verification" '
        "in the skill); this script stays blocked either way. "
        "This run continues without dblp results.")
    assert "sources: crossref(1)" in err
    assert "dblp(" not in err


@pytest.mark.parametrize("kind", ["unexpected", "malformed", "http", "network", None])
def test_other_failures_carry_no_browser_hint(run, kind):
    failure = common.SourceError("dblp: something else", kind=kind)
    _, _, err = run(dblp=failure, crossref=[paper("A", "crossref")])
    assert "note: source degraded — dblp: something else\n" in err
    assert "browser" not in err


def test_every_source_degraded_exits_one_with_empty_stdout(run):
    code, out, err = run(dblp=CHALLENGE, crossref=common.SourceError("crossref: HTTP 503"))
    assert code == 1
    assert out == ""
    assert "sources: none" in err
    assert "no results from any source" in err


def test_valid_empty_answer_is_a_zero_hit_source_not_a_degradation(run):
    code, _, err = run(dblp=[], crossref=[paper("A", "crossref")])
    assert code == 0
    assert "sources: dblp(0), crossref(1)" in err
    assert "note:" not in err


def test_stderr_never_echoes_the_query(run):
    _, _, err = run(dblp=CHALLENGE, crossref=[paper("A", "crossref")])
    assert QUERY not in err


def test_an_unanticipated_failure_is_named_by_its_type_only(run):
    code, out, err = run(arxiv=RuntimeError(LEAKY), crossref=[paper("A", "crossref")])
    assert code == 0
    assert out.startswith("- id: ")
    assert err.splitlines() == ["note: source failed unexpectedly — arxiv: RuntimeError",
                                "sources: crossref(1)"]


# ---------- snowball.py ----------------------------------------------------------

class Graph:
    """A graph source answering both directions alike."""

    def __init__(self, result):
        self.result = result

    def _answer(self, _doi, limit):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result[:limit]

    references = citations = _answer


@pytest.fixture
def expand(monkeypatch, capsys):
    def go(seeds, **sources):
        monkeypatch.setattr(snowball, "GRAPH_SOURCES", sources)
        code = snowball.main(seeds)
        out, err = capsys.readouterr()
        return code, out, err
    return go


def test_snowball_prints_each_note_once_per_run(expand):
    """Two seeds, both directions: OpenAlex without a key used to print the
    same note four times (keyless through conftest's `_lit_keys_offline`)."""
    code, out, err = expand(["10.1/a", "10.1/b"], openalex=openalex,
                            broken=Graph(RuntimeError(LEAKY)),
                            crossref=Graph([paper("Seed neighbour", "crossref")]))
    assert code == 0
    assert out.startswith("- id: ")
    lines = err.splitlines()
    assert sum("openalex: no OPENALEX_API_KEY" in line for line in lines) == 1
    assert lines.count("note: broken.references failed — RuntimeError") == 1
    assert lines.count("note: broken.citations failed — RuntimeError") == 1
    assert len(lines) == len(set(lines))
    assert not [value for value in LEAKED if value in err]


def test_snowball_with_every_source_failing_exits_one(expand):
    code, out, err = expand(["10.1/a"], openalex=openalex)
    assert (code, out) == (1, "")
    assert "no expansion results" in err
