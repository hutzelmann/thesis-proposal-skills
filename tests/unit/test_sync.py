"""L0: shared/ copies must be in sync (skill-packaging spec: sync verification).

The tampering cases run in-process so the drift logic is measurable; one case
keeps the subprocess call, because a broken shebang or a missing
`sys.exit(main())` is invisible to an in-process test and `poe test` invokes
this script from the command line.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import sync_shared

REPO = Path(__file__).resolve().parents[2]
SYNC = REPO / "scripts" / "sync_shared.py"


# These tests share mutable state that is not `tmp_path`: the tampering cases
# edit tracked files in place and restore them, and the in-sync cases read those
# same files. Under `-n auto` they would otherwise land on different workers and
# race, so the group keeps them on one worker in declaration order.
pytestmark = pytest.mark.xdist_group("sync_shared_tree")


def test_copies_in_sync(capsys):
    assert sync_shared.main(["--check"]) == 0, capsys.readouterr().out


def test_cli_entry_point_runs():
    """The interpreter boundary: shebang, imports, and `sys.exit(main())`."""
    result = subprocess.run(
        [sys.executable, str(SYNC), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("victim_rel", [
    "skills/proposal-write/references/guidelines.md",
    "skills/proposal-write/scripts/check.py",
])
def test_check_detects_tampering(victim_rel, capsys):
    victim = REPO / victim_rel
    original = victim.read_text(encoding="utf-8")
    try:
        victim.write_text(original + "\ntampered\n", encoding="utf-8")
        assert sync_shared.main(["--check"]) == 1
        assert "OUT OF SYNC" in capsys.readouterr().out
    finally:
        victim.write_text(original, encoding="utf-8")
