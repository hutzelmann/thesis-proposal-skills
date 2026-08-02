#!/usr/bin/env python3
"""Pre-publish gate: run Snyk Agent Scan — the engine behind the skills.sh
Snyk audits — against this repository's skills, isolated from the developer's
real agent configuration.

Stages `skills/proposal-*` into a synthetic HOME as `.claude/skills/`,
overrides HOME and the XDG variables so discovery sees only the staged copies
(the scanner otherwise sweeps real agent configs, e.g. ~/.config/opencode, and
connecting to MCP servers can execute their commands), then runs
`uvx snyk-agent-scan@latest scan --skills --json` and gates on the findings.

Dev-side tooling: Linux/macOS, needs `uv` and a Snyk token (free account) in
`SNYK_TOKEN` or in the repo-root `.env` (template: `.env.example`).

Usage: uv run python scripts/audit_scan.py [--threshold 0.5] [--keep]
Exit codes: 0 = clean, 1 = findings at/above threshold, 2 = runtime failure.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Calibrated 2026-08-02: W011 findings at risk <= 0.3 exist on skills that
# skills.sh reports as "Snyk: No issues" (publish, write) — those are noise.
# Everything >= 0.5 corresponded to findings skills.sh surfaces as issues.
THRESHOLD = 0.5

SCAN_TIMEOUT = 900  # LLM-judge analysis of eight skills takes a few minutes


def snyk_token(env_file: Path = REPO / ".env") -> str | None:
    """SNYK_TOKEN from the environment first, then the repo-root .env
    (KEY=VALUE, `#` comments; template: .env.example) — value is never printed."""
    if token := os.environ.get("SNYK_TOKEN"):
        return token
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            if key.strip() == "SNYK_TOKEN" and value.strip():
                return value.strip().strip("'\"")
    except OSError:
        return None
    return None


def stage(workspace: Path) -> None:
    """Copy the repo's skills into <workspace>/.claude/skills, nothing else."""
    target = workspace / ".claude" / "skills"
    target.mkdir(parents=True)
    for skill_dir in sorted((REPO / "skills").glob("proposal-*")):
        if skill_dir.is_dir():
            shutil.copytree(
                skill_dir, target / skill_dir.name,
                ignore=shutil.ignore_patterns("__pycache__"),
            )


def extract_findings(scan: dict, staged_marker: str) -> list[dict]:
    """Findings for the staged entry only: {skill, code, risk, reason}.

    The scanner represents each skill as a server-like entry; an issue's
    `reference[0]` indexes into that entry's `servers` list.
    """
    findings: list[dict] = []
    for key, entry in scan.items():
        if staged_marker not in key:
            continue
        names = [s.get("name") or "?" for s in entry.get("servers") or []]
        for issue in entry.get("issues") or []:
            reference = issue.get("reference") or [None]
            index = reference[0] if isinstance(reference, list) else None
            extra = issue.get("extra_data") or {}
            findings.append({
                "skill": names[index] if isinstance(index, int) and index < len(names) else "?",
                "code": issue.get("code", "?"),
                "risk": float(extra.get("risk_score", 0.0)),
                "reason": (extra.get("reason") or issue.get("message") or "").strip(),
            })
    return sorted(findings, key=lambda f: -f["risk"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=float, default=THRESHOLD)
    parser.add_argument("--keep", action="store_true", help="keep the staging workspace")
    args = parser.parse_args()

    token = snyk_token()
    if not token:
        print("no Snyk token: set SNYK_TOKEN or fill it in .env "
              "(cp .env.example .env; free account: app.snyk.io)", file=sys.stderr)
        return 2

    workspace = Path(tempfile.mkdtemp(prefix="audit-scan-"))
    try:
        stage(workspace)
        env = {
            **os.environ,
            "SNYK_TOKEN": token,
            "HOME": str(workspace),
            "XDG_CONFIG_HOME": str(workspace / ".config"),
            "XDG_DATA_HOME": str(workspace / ".local" / "share"),
        }
        result = subprocess.run(
            ["uvx", "snyk-agent-scan@latest", "scan", "--skills", "--json"],
            cwd=workspace, env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=SCAN_TIMEOUT,
        )
        if result.returncode != 0:
            print(f"scanner failed (exit {result.returncode}):\n{result.stderr[-2000:]}",
                  file=sys.stderr)
            return 2
        try:
            scan = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            print(f"unparseable scanner output ({exc}):\n{result.stdout[:2000]}", file=sys.stderr)
            return 2

        findings = extract_findings(scan, staged_marker=str(workspace))
        blocking = [f for f in findings if f["risk"] >= args.threshold]
        for f in findings:
            marker = "BLOCK" if f["risk"] >= args.threshold else "info "
            print(f"{marker} {f['risk']:.2f} {f['code']} {f['skill']}: {f['reason'][:160]}")
        print(f"\n{len(findings)} finding(s), {len(blocking)} at/above threshold {args.threshold}")
        return 1 if blocking else 0
    finally:
        if args.keep:
            print(f"workspace kept: {workspace}", file=sys.stderr)
        else:
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
