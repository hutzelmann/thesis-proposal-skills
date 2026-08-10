"""L0: audit_status roster + fetch semantics — the post-publish gate must watch
every shipped skill, including ones skills.sh does not know yet (the listed
roster silently omitted proposal-troubleshoot for four days)."""

import urllib.error
from pathlib import Path

import audit_status
import pytest

REPO = Path(__file__).resolve().parents[2]


def _http_error(request, code, msg):
    return urllib.error.HTTPError(request.full_url, code, msg, None, None)


def test_roster_derived_from_shipped_skills():
    shipped = sorted(
        d.name
        for d in (REPO / "skills").iterdir()
        if d.is_dir() and d.name.startswith("proposal-")
    )
    assert shipped == audit_status.SKILLS
    assert "proposal-troubleshoot" in audit_status.SKILLS


def test_fetch_records_unpublished_skill_as_null(monkeypatch):
    def fake_urlopen(request, **_kwargs):
        raise _http_error(request, 404, "Not Found")

    monkeypatch.setattr(audit_status.urllib.request, "urlopen", fake_urlopen)
    verdicts = audit_status.fetch_all()
    assert set(verdicts) == set(audit_status.SKILLS)
    assert all(v is None for v in verdicts.values())


def test_fetch_still_raises_on_other_http_errors(monkeypatch):
    def fake_urlopen(request, **_kwargs):
        raise _http_error(request, 500, "Server Error")

    monkeypatch.setattr(audit_status.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(urllib.error.HTTPError):
        audit_status.fetch_all()


def test_main_exits_2_when_fetch_fails(monkeypatch):
    def broken_fetch():
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(audit_status, "fetch_all", broken_fetch)
    assert audit_status.main([]) == 2


def test_diff_treats_null_as_unpublished():
    published = {"Snyk": {"status": "pass", "riskLevel": "LOW"}}
    assert audit_status.diff({"s": None}, {"s": None}) == []
    lines = audit_status.diff({"s": None}, {"s": published})
    assert len(lines) == 1
    assert lines[0].startswith("s / Snyk: None -> ")
