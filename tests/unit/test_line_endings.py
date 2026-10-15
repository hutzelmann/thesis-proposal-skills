"""L0: files a test compares byte for byte keep LF in every checkout.

git for Windows ships `core.autocrlf=true`, so a text file a test reads with
`read_bytes()` arrives there with CRLF, while the prompt it is compared with is
built through `read_text()`, which folds CRLF back to LF. The first Windows CI
run in six weeks (run 38385444225) failed all 16 golden-prompt tests that way.
The hand-written `eol=lf` lines in `.gitattributes` pin those files, and the
shell script a test runs under sh on that lane too; this test
replays a Windows checkout of them on any platform, with the repository's own
attributes, so a byte-compared file without that pin fails on Linux as well.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

# Every checked-out text file a test compares as bytes, with the test that does,
# and every shell script a test runs: a CRLF copy fails at `set -eu` already.
BYTE_COMPARED = {
    "tests/unit/data/l2_prompts/*.txt": "test_l2_rubrics.py, test_eval_wiring.py",
    "scripts/ci_typst_build.sh": "test_fixture_paths.py (runs it under sh)",
}
CONTROL = "control.txt"  # no attribute: proves the replay converts at all


def git(repo: Path, *args: str) -> None:
    """git in `repo`, blind to the host's own configuration (a global file that
    does not exist, no system file): the replay sets the one setting that
    matters, as git for Windows does."""
    env = {**os.environ, "GIT_CONFIG_GLOBAL": str(repo.parent / "no-global-gitconfig"),
           "GIT_CONFIG_NOSYSTEM": "1"}
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, env=env)


@pytest.fixture
def windows_checkout(tmp_path) -> Path:
    """The byte-compared files and a control file staged into a fresh repo with
    the repository's `.gitattributes`, then checked out again under
    `core.autocrlf=true`."""
    repo = tmp_path / "checkout"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "core.autocrlf", "true")
    shutil.copyfile(REPO / ".gitattributes", repo / ".gitattributes")
    (repo / CONTROL).write_bytes(b"one\ntwo\n")
    for pattern in BYTE_COMPARED:
        for source in REPO.glob(pattern):
            target = repo / source.relative_to(REPO)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    git(repo, "add", "-A")
    staged = [p for p in repo.rglob("*")
              if p.is_file() and ".git" not in p.parts and p.name != ".gitattributes"]
    for path in staged:
        path.unlink()
    git(repo, "checkout", "--", ".")
    return repo


@pytest.mark.parametrize("pattern", sorted(BYTE_COMPARED))
def test_byte_compared_files_keep_lf_in_a_windows_checkout(pattern, windows_checkout):
    sources = sorted(REPO.glob(pattern))
    assert sources, f"{pattern} matches nothing; update BYTE_COMPARED with its test"
    assert (windows_checkout / CONTROL).read_bytes() == b"one\r\ntwo\r\n", (
        "the replay converted nothing, so it proves nothing")
    for source in sources:
        checked_out = (windows_checkout / source.relative_to(REPO)).read_bytes()
        assert b"\r\n" not in checked_out, f"{source.name}: CRLF on Windows; pin it to eol=lf"
        assert checked_out == source.read_bytes().replace(b"\r\n", b"\n"), source.name
