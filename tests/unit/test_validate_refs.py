"""L0: import reference validation (skill-import spec scenarios), offline."""

import common
import validate_refs

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


def test_extract_references():
    refs = validate_refs.extract_references(PROPOSAL)
    assert [r["id"] for r in refs] == ["Good25Paper", "NoDoi24Entry", "Broken23Doi"]
    assert refs[0]["DOI"] == "10.1/good"
    assert refs[1].get("DOI") is None


def run_main(tmp_path, monkeypatch, capsys, http_json, search):
    monkeypatch.setattr(common, "http_json", http_json)
    monkeypatch.setattr(validate_refs.crossref, "search", search)
    p = tmp_path / "x.md"
    p.write_text(PROPOSAL)
    assert validate_refs.main([str(p)]) == 0
    return capsys.readouterr().out


def test_scenarios(tmp_path, monkeypatch, capsys):
    # the stubs stand in for network calls, so they take the real signatures and
    # ignore the arguments they do not need
    def http_json(url, **_kw):
        if "10.1/good" in url:
            return {"message": {"DOI": "10.1/good", "title": ["A Fine Paper on Testing"],
                                "issued": {"date-parts": [[2025]]}, "type": "journal-article",
                                "author": [{"family": "Doe", "given": "J."}]}}
        raise common.SourceError("crossref: HTTP 404")

    def search(_query, _limit):
        return [{"id": "x", "title": "Identifiable Work Without Identifier",
                 "DOI": "10.9/found", "_source": "crossref"}]

    out = run_main(tmp_path, monkeypatch, capsys, http_json, search)
    assert "VERIFIED Good25Paper" in out
    assert "ENRICHED NoDoi24Entry" in out
    assert "10.9/found" in out
    assert "UNVERIFIABLE Broken23Doi" in out
    assert "[TODO: verify reference Broken23Doi]" in out
    assert "completed CSL-YAML" in out


def test_offline_path(tmp_path, monkeypatch, capsys):
    def http_json(_url, **_kw):
        raise common.SourceError("crossref: network unreachable")

    def search(_query, _limit):
        raise common.SourceError("crossref: network unreachable")

    out = run_main(tmp_path, monkeypatch, capsys, http_json, search)
    assert out.count("OFFLINE") >= 1
    assert "UNVERIFIABLE" not in out.split("OFFLINE")[0]  # offline is not misreported


def test_no_references_block(tmp_path):
    p = tmp_path / "y.md"
    p.write_text("Just text, no metadata.\n")
    assert validate_refs.main([str(p)]) == 2
