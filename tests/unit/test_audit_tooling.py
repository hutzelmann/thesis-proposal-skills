"""L0: pure logic of the audit gate tooling — no network, no scanner runs."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "harness"))

import audit_llm_preflight  # noqa: E402
import audit_scan  # noqa: E402
import audit_status  # noqa: E402

SAMPLE = json.loads((Path(__file__).parent / "data" / "agent_scan_sample.json").read_text())


# ---------- audit_scan -------------------------------------------------------

def test_extract_findings_maps_reference_to_skill_and_sorts_by_risk():
    findings = audit_scan.extract_findings(SAMPLE, staged_marker="/tmp/audit-scan-sample123")
    assert [f["skill"] for f in findings] == ["proposal-lit-search", "proposal-ideate"]
    assert findings[0]["code"] == "W007" and findings[0]["risk"] == 1.0
    assert findings[0]["reason"] == "agent writes the secret value"


def test_extract_findings_ignores_foreign_entries():
    findings = audit_scan.extract_findings(SAMPLE, staged_marker="/tmp/audit-scan-sample123")
    assert all(f["code"] != "W001" for f in findings)


def test_threshold_separates_noise_from_blockers():
    findings = audit_scan.extract_findings(SAMPLE, staged_marker="/tmp/audit-scan-sample123")
    blocking = [f for f in findings if f["risk"] >= audit_scan.THRESHOLD]
    assert [f["code"] for f in blocking] == ["W007"]


def test_snyk_token_env_wins_then_file(tmp_path, monkeypatch):
    credentials = tmp_path / "credentials.txt"
    credentials.write_text("Email: x@y.z\nSnyk API Key: from-file\n")
    monkeypatch.setenv("SNYK_TOKEN", "from-env")
    assert audit_scan.snyk_token(credentials) == "from-env"
    monkeypatch.delenv("SNYK_TOKEN")
    assert audit_scan.snyk_token(credentials) == "from-file"
    assert audit_scan.snyk_token(tmp_path / "missing.txt") is None


# ---------- audit_status -----------------------------------------------------

PAYLOAD = {
    "audits": [
        {"provider": "Snyk", "status": "fail", "riskLevel": "HIGH",
         "summary": "Risk: HIGH · 2 issues", "auditedAt": "2026-07-30T08:17:22Z"},
        {"provider": "Socket", "status": "pass", "summary": "No alerts"},
    ]
}


def test_normalize_keeps_verdict_drops_churn():
    normalized = audit_status.normalize(PAYLOAD)
    assert normalized == {
        "Snyk": {"status": "fail", "riskLevel": "HIGH"},
        "Socket": {"status": "pass", "riskLevel": None},
    }


def test_diff_names_skill_provider_and_both_verdicts():
    baseline = {"proposal-lit-search": {"Snyk": {"status": "fail", "riskLevel": "HIGH"}}}
    current = {"proposal-lit-search": {"Snyk": {"status": "pass", "riskLevel": "LOW"}}}
    lines = audit_status.diff(baseline, current)
    assert len(lines) == 1
    assert "proposal-lit-search / Snyk" in lines[0]
    assert "fail" in lines[0] and "pass" in lines[0]


def test_diff_empty_on_match():
    state = {"proposal-check": {"Snyk": {"status": "pass", "riskLevel": "LOW"}}}
    assert audit_status.diff(state, state) == []


# ---------- audit_llm_preflight ----------------------------------------------

def test_parse_verdict_extracts_json_from_prose():
    output = 'Here you go:\n{"categories": {"PROMPT_INJECTION": {"flagged": true, "reason": "x"}}}'
    verdicts = audit_llm_preflight.parse_verdict(output)
    assert verdicts["PROMPT_INJECTION"]["flagged"] is True


def test_parse_verdict_none_on_garbage():
    assert audit_llm_preflight.parse_verdict("no json here") is None
