"""`.githooks/pre-commit`: a commit carries exactly what its author staged.

The hook checks the staged snapshot against the staged sources and refuses a
stale one; it never stages, writes or reverts anything (skill-packaging spec:
Commit-time drift check). Every case drives a real `git commit` in a scratch
repository holding a copy of everything the sync reads, so the tracked tree is
never committed to or synced.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from helpers import REPO, copy_sync_tree

HOOK = REPO / ".githooks" / "pre-commit"
SKILL = "skills/proposal-write/SKILL.md"
VOICE = "shared/blocks/voice.md"

pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="the hook runs python3 under sh; Windows may lack python3"
)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """Git with no configuration but the repository's own: the developer's
    signing, aliases or hooks path cannot reach the scratch repository, and a
    GIT_* variable inherited from an outer hook cannot redirect it."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env |= {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    identity = ["-c", "user.name=Erika Musterfrau", "-c", "user.email=erika@example.invalid"]
    return subprocess.run(["git", *identity, *args], cwd=repo, env=env, capture_output=True,
                          text=True, encoding="utf-8", check=check, timeout=60)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """An in-sync repository whose commits run the shipped hook."""
    copy_sync_tree(tmp_path)
    (tmp_path / ".githooks").mkdir()
    shutil.copy2(HOOK, tmp_path / ".githooks" / "pre-commit")
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "initial")
    git(tmp_path, "config", "core.hooksPath", ".githooks")
    return tmp_path


def commit(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return git(repo, "commit", "-q", "-m", "change", *args, check=False)


def staged(repo: Path) -> list[str]:
    return git(repo, "diff", "--cached", "--name-only").stdout.splitlines()


def committed(repo: Path) -> list[str]:
    return git(repo, "show", "--name-only", "--format=", "HEAD").stdout.split()


def status(repo: Path) -> list[str]:
    return git(repo, "status", "--porcelain").stdout.splitlines()


def head(repo: Path) -> str:
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def tree_bytes(repo: Path) -> dict[str, bytes]:
    """Every working-tree file outside .git, byte for byte."""
    return {
        p.relative_to(repo).as_posix(): p.read_bytes()
        for p in repo.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(repo).parts
    }


def hand_edit(repo: Path) -> None:
    """An author's own paragraph below the first heading: outside every
    materialized region, so no sync would ever touch it."""
    path = repo / SKILL
    text = path.read_text(encoding="utf-8")
    heading_end = text.index("\n", text.index("\n## ") + 1)
    path.write_text(text[:heading_end] + "\n\nAn unstaged paragraph of the author's own."
                    + text[heading_end:], encoding="utf-8")


def edit_voice(repo: Path) -> None:
    """A shared-source edit that every SKILL.md must follow."""
    path = repo / VOICE
    path.write_text(path.read_text(encoding="utf-8").rstrip("\n") + " Extra.\n", encoding="utf-8")


def stage_note(repo: Path) -> None:
    (repo / "notes.txt").write_text("an unrelated change\n", encoding="utf-8")
    git(repo, "add", "notes.txt")


def test_hook_is_executable():
    assert os.access(HOOK, os.X_OK)


def test_an_unstaged_hand_edit_is_never_swept_into_the_commit(repo):
    hand_edit(repo)
    stage_note(repo)
    before = tree_bytes(repo)
    run = commit(repo)
    assert run.returncode == 0, run.stderr
    assert committed(repo) == ["notes.txt"]
    assert status(repo) == [f" M {SKILL}"]
    assert tree_bytes(repo) == before


def test_staged_drift_is_refused_and_nothing_is_touched(repo):
    edit_voice(repo)
    git(repo, "add", VOICE)
    hand_edit(repo)
    head_before, before = head(repo), tree_bytes(repo)
    run = commit(repo)
    assert run.returncode != 0
    assert "python3 scripts/sync_shared.py" in run.stderr
    for skill_md in sorted((repo / "skills").glob("proposal-*/SKILL.md")):
        assert skill_md.relative_to(repo).as_posix() in run.stderr
    assert staged(repo) == [VOICE]
    assert head(repo) == head_before
    assert tree_bytes(repo) == before


def test_copies_synced_but_not_staged_are_still_refused(repo):
    edit_voice(repo)
    git(repo, "add", VOICE)
    subprocess.run([sys.executable, "scripts/sync_shared.py"], cwd=repo, check=True,
                   capture_output=True)
    head_before = head(repo)
    run = commit(repo)
    assert run.returncode != 0
    assert staged(repo) == [VOICE]
    assert head(repo) == head_before


def test_a_peers_unsynced_source_edit_does_not_block_an_unrelated_commit(repo):
    edit_voice(repo)
    stage_note(repo)
    before = (repo / VOICE).read_bytes()
    run = commit(repo)
    assert run.returncode == 0, run.stderr
    assert committed(repo) == ["notes.txt"]
    assert status(repo) == [f" M {VOICE}"]
    assert (repo / VOICE).read_bytes() == before


def test_commit_all_is_judged_by_what_it_would_commit(repo):
    edit_voice(repo)
    head_before = head(repo)
    run = commit(repo, "-a")
    assert run.returncode != 0
    assert head(repo) == head_before
    assert staged(repo) == []
