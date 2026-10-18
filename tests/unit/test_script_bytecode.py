"""L0: a shipped script writes no bytecode cache into its skill's install directory
(skill-packaging spec, "Scripts write nothing into the install directory";
change scripts-write-no-bytecode).

Python caches the bytecode of every module it imports beside the module's file,
so a script that imports a sibling left `scripts/__pycache__/` in the installed
skill. Whether a cache is written is decided by a fresh interpreter importing a
module it has not imported yet, so each case runs a real child against a copy of
the skill's folder: the measurement is the property itself, however a script
achieves it. `--help` exits after the module-level imports and before any file
or network access, and every entry script parses its arguments with argparse.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from helpers import REPO

SKILLS = REPO / "skills"
MAIN_GUARD = 'if __name__ == "__main__":'
# an ambient setting that suppresses or relocates caches would let a script
# without the switch pass; the child runs without either
CACHE_SETTINGS = ("PYTHONDONTWRITEBYTECODE", "PYTHONPYCACHEPREFIX")

ENTRY_SCRIPTS = sorted(path for path in SKILLS.glob("*/scripts/*.py")
                       if MAIN_GUARD in path.read_text(encoding="utf-8"))


def label(path: Path) -> str:
    return path.relative_to(SKILLS).as_posix()


def child_env(**extra: str) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in CACHE_SETTINGS}
    return {**env, **extra}


def installed_copy(skill: str, dest: Path) -> Path:
    """The skill's folder as an install holds it: no cache from the test suite's
    own imports of the working tree."""
    return Path(shutil.copytree(SKILLS / skill, dest / skill,
                                ignore=shutil.ignore_patterns("__pycache__")))


def caches(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                  if "__pycache__" in p.parts)


def test_every_script_with_sibling_imports_is_an_entry_script_here():
    """The discovery must reach the scripts that import siblings; were it to miss
    them, the guard below would pass on nothing."""
    names = {label(path) for path in ENTRY_SCRIPTS}
    assert {"proposal-lit-search/scripts/search.py",
            "proposal-lit-search/scripts/snowball.py",
            "proposal-import/scripts/validate_refs.py",
            "proposal-reverse/scripts/validate_refs.py"} <= names


# copies skills/, and test_sync.py's tamper cases rewrite files there
@pytest.mark.xdist_group("sync_shared_tree")
@pytest.mark.parametrize("script", ENTRY_SCRIPTS, ids=label)
def test_documented_run_leaves_no_bytecode_in_the_install_directory(script, tmp_path):
    skill = script.parent.parent.name
    installed = installed_copy(skill, tmp_path / "skills")
    work = tmp_path / "work"
    work.mkdir()
    done = subprocess.run([sys.executable, str(installed / "scripts" / script.name), "--help"],
                          cwd=work, env=child_env(), capture_output=True, encoding="utf-8",
                          errors="replace", check=False)
    assert done.returncode == 0, done.stderr
    left = caches(installed)
    assert not left, f"{label(script)} left bytecode in its install directory: {left}"


# copies skills/, and test_sync.py's tamper cases rewrite files there
@pytest.mark.xdist_group("sync_shared_tree")
def test_importing_a_shipped_module_leaves_the_importers_setting_alone(tmp_path):
    """The switch fires only when the script is the program: the test suite and
    the harness import these modules, and the flag belongs to the whole
    interpreter. The cache this import writes is also the negative control —
    without it, an environment that never writes caches would pass the guard."""
    scripts = installed_copy("proposal-lit-search", tmp_path / "skills") / "scripts"
    work = tmp_path / "work"
    work.mkdir()
    done = subprocess.run(
        [sys.executable, "-c", "import sys; import search; print(sys.dont_write_bytecode)"],
        cwd=work, env=child_env(PYTHONPATH=str(scripts)), capture_output=True,
        encoding="utf-8", errors="replace", check=False)
    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == "False"
    assert any(name.startswith("__pycache__/common.") for name in caches(scripts))
