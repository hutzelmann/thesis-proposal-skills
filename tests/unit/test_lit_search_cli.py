"""L0: the orchestrators' degradation contract — `search.py` and `snowball.py`.
Candidates alone on stdout, notes on stderr, a blocked source named with its
cause and never counted as a zero-hit contributor, an unanticipated failure
named by its type only, each snowball note once per run, exit codes unchanged.
Sources are stubbed in-process; no network.
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path

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
                                "sources: crossref(1)", count_line(1, out)]


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
    assert "candidates:" not in err


# ---------- output sized for what a host shows -------------------------------------
#
# skill-lit-search: Search output sized for what a host shows. Both scripts say,
# before their output, how many candidates they emitted and how large stdout is,
# so an agent can tell when a host showed it less than that; the snowball
# default keeps one seed's output under the threshold (measurement.md, task 1.1).

REPO = Path(__file__).resolve().parents[2]
COUNT_RE = re.compile(r"^candidates: (\d+) \((\d+) lines, (\d+) characters on stdout\)(.*)$")
TOO_LARGE = " — more than some hosts show from one command; run narrower"


def count_line(n: int, out: str, flagged: bool = False) -> str:
    line = f"candidates: {n} ({len(out.splitlines())} lines, {len(out)} characters on stdout)"
    return line + (TOO_LARGE if flagged else "")


def lit_search_requirement() -> str:
    """The requirement's text, from the main spec once archived and from the
    active change until then — never from the archive."""
    specs = [REPO / "openspec" / "specs" / "skill-lit-search" / "spec.md",
             *sorted((REPO / "openspec" / "changes").glob("*/specs/skill-lit-search/spec.md"))]
    texts = [p.read_text(encoding="utf-8") for p in specs if p.is_file()]
    found = [t for t in texts if "Search output sized for what a host shows" in t]
    assert found, "no spec states 'Search output sized for what a host shows'"
    return found[0]


def spec_number(pattern: str) -> int:
    match = re.search(pattern, lit_search_requirement())
    assert match, pattern
    return int(match.group(1).replace(",", ""))


@pytest.mark.parametrize("script", [search, snowball], ids=["search", "snowball"])
def test_the_threshold_is_the_specified_one(script):
    chars, lines = (spec_number(r"threshold of ([\d,]+) characters"),
                    spec_number(r"characters or ([\d,]+) lines"))
    assert (chars, lines) == (script.MAX_SHOWN_CHARS, script.MAX_SHOWN_LINES)


def test_count_line_follows_the_unchanged_sources_line(run):
    code, out, err = run(dblp=[], crossref=[paper("A", "crossref"), paper("B", "crossref")],
                         arxiv=[paper("C", "arxiv")])
    assert code == 0
    lines = err.splitlines()
    assert lines[-2] == "sources: dblp(0), crossref(2), arxiv(1)"
    assert lines[-1] == count_line(3, out)


def test_count_line_counts_what_was_printed(run):
    _, out, err = run(crossref=[paper(f"Paper {i}", "crossref") for i in range(4)])
    n, lines, chars, rest = COUNT_RE.match(err.splitlines()[-1]).groups()
    assert int(n) == out.count("- id: ") == 4
    assert (int(lines), int(chars)) == (len(out.splitlines()), len(out))
    assert rest == ""


def test_count_line_is_printed_before_the_candidates(monkeypatch):
    """One stream for both, as a terminal shows them: the line comes first."""
    both = io.StringIO()
    monkeypatch.setattr(sys, "stdout", both)
    monkeypatch.setattr(sys, "stderr", both)
    monkeypatch.setattr(search, "SEARCH_SOURCES", {"crossref": Stub([paper("A", "crossref")])})
    assert search.main([QUERY, "--sources", "crossref"]) == 0
    text = both.getvalue()
    assert text.index("sources: crossref(1)") < text.index("candidates: 1 (") < text.index("- id:")


@pytest.mark.parametrize("bound", ["MAX_SHOWN_CHARS", "MAX_SHOWN_LINES"])
def test_output_over_the_threshold_is_flagged(run, monkeypatch, bound):
    _, out, err = run(crossref=[paper("A", "crossref")])
    assert err.splitlines()[-1] == count_line(1, out)
    at = len(out) if bound == "MAX_SHOWN_CHARS" else len(out.splitlines())
    monkeypatch.setattr(search, bound, at)  # exactly at the bound: not more than it
    _, out, err = run(crossref=[paper("A", "crossref")])
    assert err.splitlines()[-1] == count_line(1, out)
    monkeypatch.setattr(search, bound, at - 1)
    _, out, err = run(crossref=[paper("A", "crossref")])
    assert err.splitlines()[-1] == count_line(1, out, flagged=True)


def test_snowball_prints_the_same_count_line(expand, monkeypatch):
    code, out, err = expand(["10.1/a"], crossref=Graph([paper("One", "crossref"),
                                                       paper("Two", "crossref")]))
    assert code == 0
    assert err.splitlines()[-1] == count_line(2, out)
    monkeypatch.setattr(snowball, "MAX_SHOWN_CHARS", len(out) - 1)
    _, out, err = expand(["10.1/a"], crossref=Graph([paper("One", "crossref"),
                                                    paper("Two", "crossref")]))
    assert err.splitlines()[-1] == count_line(2, out, flagged=True)


def test_snowball_default_per_seed_limit_is_the_specified_one(monkeypatch, capsys):
    seen = []

    def expand(_seeds, limit, _direction):
        seen.append(limit)
        return []

    monkeypatch.setattr(snowball, "expand", expand)
    assert snowball.main(["10.1/a"]) == 1
    capsys.readouterr()
    assert seen == [spec_number(r"default per-seed limit SHALL be (\d+)")]


# The recorded two-seed run at N=5 (measurement.md): per seed, Crossref and
# OpenCitations answered 5 references each with one in common, Semantic Scholar
# 5 citations and 5 recommendations, OpenCitations 5 citations — 9 backward and
# 15 forward after deduplication, the larger of the two seeds; on average 963
# characters and 17.9 lines per candidate.
AVERAGE_CHARS = 963
AUTHORS = [{"family": f"Musterfrau{i}", "given": "Erika"} for i in range(5)]  # 19 lines each


def sized(tag: str, i: int) -> dict:
    item = common.entry(title=f"Synthetic {tag} candidate {i}", source="replay",
                        doi=f"10.1/{tag}-{i}", authors=AUTHORS, year=2024,
                        venue="Proceedings of a Synthetic Venue")
    pad = AVERAGE_CHARS - len(common.to_csl_yaml([item])) - len("  abstract: \n")
    item["abstract"] = ("lorem ipsum " * 100)[:pad].strip().ljust(pad, "x")
    return item


class Replay:
    """One graph source of the recorded run, answering from fixed pools and
    capped at the limit it is called with."""

    def __init__(self, **edges):
        self.edges = edges

    def __getattr__(self, edge):
        if edge not in self.edges:
            raise AttributeError(edge)
        pool, offset = self.edges[edge]
        return lambda _doi, limit: [sized(pool, i) for i in range(offset, offset + limit)]


REPLAY = {
    "semantic_scholar": Replay(citations=("forward", 0), recommendations=("forward", 20)),
    "crossref": Replay(references=("backward", 0)),
    "opencitations": Replay(references=("backward", 4), citations=("forward", 40)),
}


def test_a_default_run_with_the_examples_seed_count_stays_under_the_threshold(expand):
    """The skill's example snowballs one seed per call."""
    assert len(sized("x", 0)["abstract"]) > 0
    assert len(common.to_csl_yaml([sized("x", 0)])) == AVERAGE_CHARS
    code, _, err = expand(["10.1/seed"], **REPLAY)
    assert code == 0
    n, lines, chars, rest = COUNT_RE.match(err.splitlines()[-1]).groups()
    assert int(n) == 9 + 15
    assert int(chars) < snowball.MAX_SHOWN_CHARS
    assert int(lines) < snowball.MAX_SHOWN_LINES
    assert rest == ""


def test_the_replay_overflows_the_threshold_at_the_old_default(expand):
    """The replay is sensitive to the limit: at the former default of 20 the
    same seed is flagged."""
    code, _, err = expand(["10.1/seed", "--limit-per-seed", "20"], **REPLAY)
    assert code == 0
    assert err.splitlines()[-1].endswith(TOO_LARGE)
