"""L0: source-client parsers against canned real API responses — no network.

Each sample under tests/unit/data/ was captured live; these tests pin the
parser contract so API drift surfaces as a deliberate live-test failure, not
a silent skill regression.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "proposal-lit-search" / "scripts"
DATA = REPO / "tests" / "unit" / "data"
sys.path.insert(0, str(SCRIPTS))

import common  # noqa: E402


def patched(monkeypatch, payload):
    monkeypatch.setattr(common, "http_json", lambda *a, **k: payload)


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
    monkeypatch.setattr(common, "http_text", lambda *a, **k: xml)
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
