"""L0: shared/ copies must be in sync (skill-packaging spec: sync verification)."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SYNC = REPO / "scripts" / "sync_shared.py"


def run_check() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--check"], capture_output=True, text=True
    )


def test_copies_in_sync():
    result = run_check()
    assert result.returncode == 0, result.stdout + result.stderr


def test_check_detects_tampering(tmp_path):
    victim = REPO / "skills" / "proposal-write" / "references" / "guidelines.md"
    original = victim.read_text(encoding="utf-8")
    try:
        victim.write_text(original + "\ntampered\n", encoding="utf-8")
        result = run_check()
        assert result.returncode == 1
        assert "OUT OF SYNC" in result.stdout
    finally:
        victim.write_text(original, encoding="utf-8")
