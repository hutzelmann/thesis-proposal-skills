"""L0: source-client parsers against canned real API responses — no network.

Each sample under tests/unit/data/ was captured live; these tests pin the
parser contract so API drift surfaces as a deliberate live-test failure, not
a silent skill regression.
"""

import json
from pathlib import Path

import common
import pytest

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "tests" / "unit" / "data"


def patched(monkeypatch, payload):
    monkeypatch.setattr(common, "http_json", lambda *_a, **_k: payload)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def assert_entries(items, min_count=1, graph_minimal=False):
    assert len(items) >= min_count
    for item in items:
        assert item["_source"]
        if graph_minimal:
            assert item.get("DOI") or item.get("title")
        else:
            assert item["title"]
        if item.get("DOI"):
            assert "URL" not in item


def test_dblp_search(monkeypatch):
    import dblp
    patched(monkeypatch, load("dblp_search_sample.json"))
    items = dblp.search("code review", 3)
    assert_entries(items)
    assert any(i.get("author") for i in items)


def test_crossref_search(monkeypatch):
    import crossref
    patched(monkeypatch, load("crossref_search_sample.json"))
    items = crossref.search("code review", 3)
    assert_entries(items)
    assert any(i.get("issued", {}).get("year") for i in items)


def test_crossref_references(monkeypatch):
    import crossref
    patched(monkeypatch, load("crossref_refs_sample.json"))
    items = crossref.references("10.1145/3292500.3330919")
    assert len(items) >= 1
    assert all(i.get("DOI") or i.get("title") for i in items)


def test_arxiv_search(monkeypatch):
    import arxiv
    xml = (DATA / "arxiv_search_sample.xml").read_text(encoding="utf-8")
    monkeypatch.setattr(common, "http_text", lambda *_a, **_k: xml)
    items = arxiv.search("code review", 3)
    assert_entries(items)
    assert any(i.get("abstract") for i in items)


def test_opencitations_references(monkeypatch):
    import opencitations
    patched(monkeypatch, load("opencitations_refs_sample.json"))
    items = opencitations.references("10.1145/3292500.3330919", 3)
    assert_entries(items, graph_minimal=True)
    assert all(i["DOI"] for i in items)


def test_semantic_scholar_search(monkeypatch):
    import semantic_scholar
    patched(monkeypatch, load("semantic_scholar_search_sample.json"))
    items = semantic_scholar.search("code review", 3)
    assert_entries(items)


def test_openalex_search(monkeypatch):
    import openalex
    monkeypatch.setenv("OPENALEX_API_KEY", "test-key")
    patched(monkeypatch, load("openalex_search_sample.json"))
    items = openalex.search("code review", 3)
    assert_entries(items)
    assert any(i.get("abstract") for i in items), "inverted-index reconstruction failed"


def test_openalex_requires_key(monkeypatch):
    import openalex
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)
    with pytest.raises(common.SourceError, match="OPENALEX_API_KEY"):
        openalex.search("anything", 1)


def test_snowball_enrichment_uses_public_parser(monkeypatch):
    import crossref
    import snowball
    sample = load("crossref_search_sample.json")
    work = sample["message"]["items"][0]
    patched(monkeypatch, {"message": work})
    enriched = snowball.enrich_bare_dois([{"DOI": "10.1/x", "_source": "opencitations"}])
    assert enriched
    assert enriched[0]["title"]
    assert crossref.parse_work(work)["title"] == enriched[0]["title"]


def test_semantic_scholar_recommendations(monkeypatch):
    import semantic_scholar
    sample = load("semantic_scholar_search_sample.json")
    patched(monkeypatch, {"recommendedPapers": sample["data"]})
    items = semantic_scholar.recommendations("10.1/x", 3)
    assert items
    assert all(i["title"] for i in items)
