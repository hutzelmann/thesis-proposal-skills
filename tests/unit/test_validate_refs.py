"""L0: import reference validation (skill-import spec scenarios), offline."""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "proposal-import" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import common  # noqa: E402
import validate_refs  # noqa: E402

PROPOSAL = """Body text [@Good25Paper] and [@NoDoi24Entry] and [@Broken23Doi].

---
title: T
references:
- id: Good25Paper
  type: article-journal
  title: A Fine Paper on Testing
  DOI: 10.1/good
- id: NoDoi24Entry
  type: article-journal
  title: Identifiable Work Without Identifier
- id: Broken23Doi
  type: article-journal
  title: Vanished Work
  DOI: 10.1/dead
---
"""


def test_extract_references(tmp_path):
    refs = validate_refs.extract_references(PROPOSAL)
    assert [r["id"] for r in refs] == ["Good25Paper", "NoDoi24Entry", "Broken23Doi"]
    assert refs[0]["DOI"] == "10.1/good"
    assert refs[1].get("DOI") is None


def run_main(tmp_path, monkeypatch, capsys, http_json, search):
    monkeypatch.setattr(common, "http_json", http_json)
    monkeypatch.setattr(validate_refs.crossref, "search", search)
    p = tmp_path / "x.md"
    p.write_text(PROPOSAL)
    monkeypatch.setattr(sys, "argv", ["validate_refs.py", str(p)])
    assert validate_refs.main() == 0
    return capsys.readouterr().out


def test_scenarios(tmp_path, monkeypatch, capsys):
    def http_json(url, **kw):
        if "10.1/good" in url:
            return {"message": {"DOI": "10.1/good", "title": ["A Fine Paper on Testing"],
                                "issued": {"date-parts": [[2025]]}, "type": "journal-article",
                                "author": [{"family": "Doe", "given": "J."}]}}
        raise common.SourceError("crossref: HTTP 404")

    def search(query, limit):
        return [{"id": "x", "title": "Identifiable Work Without Identifier",
                 "DOI": "10.9/found", "_source": "crossref"}]

    out = run_main(tmp_path, monkeypatch, capsys, http_json, search)
    assert "VERIFIED Good25Paper" in out
    assert "ENRICHED NoDoi24Entry" in out and "10.9/found" in out
    assert "UNVERIFIABLE Broken23Doi" in out and "[TODO: verify reference Broken23Doi]" in out
    assert "completed CSL-YAML" in out


def test_offline_path(tmp_path, monkeypatch, capsys):
    def http_json(url, **kw):
        raise common.SourceError("crossref: network unreachable")

    def search(query, limit):
        raise common.SourceError("crossref: network unreachable")

    out = run_main(tmp_path, monkeypatch, capsys, http_json,
                   lambda q, l: (_ for _ in ()).throw(common.SourceError("offline")))
    assert out.count("OFFLINE") >= 1
    assert "UNVERIFIABLE" not in out.split("OFFLINE")[0]  # offline is not misreported


def test_no_references_block(tmp_path, monkeypatch, capsys):
    p = tmp_path / "y.md"
    p.write_text("Just text, no metadata.\n")
    monkeypatch.setattr(sys, "argv", ["validate_refs.py", str(p)])
    assert validate_refs.main() == 2
