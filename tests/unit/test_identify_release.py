"""L0: resolving a submitted report's hashes to the revision that produced it.

Each case is built as a real two-commit history rather than mocked, because the
thing under test is agreement with git's own object naming — a mock would assert
that the code matches itself.

The distinction that matters operationally: a clean install of an older revision
is a report to reproduce against that revision, while a file matching no revision
is an install someone edited, and the two must never read alike.
"""

import subprocess
from pathlib import Path

import identify_release
import pytest

REPO = Path(__file__).resolve().parents[2]

SKILL_FILE = "skills/proposal-check/SKILL.md"
OTHER_FILE = "skills/proposal-check/scripts/check.py"
V1 = "# Check\n\nfirst published wording\n"
V2 = "# Check\n\nsecond published wording\n"
SCRIPT = "print('check')\n"


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


def blob(repo: Path, text: str) -> str:
    """The blob name git would give these exact bytes.

    The pipe is binary on purpose: `text=True` wraps stdin in a `TextIOWrapper`
    whose default newline setting translates every `\\n` to `os.linesep`, so on
    Windows this hashed CRLF content and matched no committed blob at all.
    """
    proc = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "--stdin"],
        input=text.encode("utf-8"), capture_output=True, check=True,
    )
    return proc.stdout.decode("utf-8").strip()


@pytest.fixture
def history(tmp_path):
    """A repo where SKILL.md was published as V1, then changed to V2."""
    repo = tmp_path / "repo"
    (repo / "skills" / "proposal-check" / "scripts").mkdir(parents=True)
    run_git_init = ["git", "-C", str(repo), "init", "-q", "-b", "main"]
    subprocess.run(run_git_init, check=True)
    run_git(repo, "config", "user.email", "dev@example.org")
    run_git(repo, "config", "user.name", "Dev")
    # git for Windows ships core.autocrlf=true, which would store these files
    # LF-normalized while the test hashes what it wrote: pin it, and write bytes,
    # so the fixture's stored bytes do not depend on the host's git config
    run_git(repo, "config", "core.autocrlf", "false")

    (repo / SKILL_FILE).write_bytes(V1.encode("utf-8"))
    (repo / OTHER_FILE).write_bytes(SCRIPT.encode("utf-8"))
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "first release")
    first = run_git(repo, "rev-parse", "--short", "HEAD").strip()

    (repo / SKILL_FILE).write_bytes(V2.encode("utf-8"))
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-q", "-m", "reword the check skill")
    second = run_git(repo, "rev-parse", "--short", "HEAD").strip()
    return repo, first, second


def write_hashes(tmp_path, repo, entries):
    """entries: (installed-relative path, content) -> a hashes.txt as shipped."""
    lines = [
        f"{path} git_blob={blob(repo, text)} sha256=unused bytes={len(text.encode())}"
        for path, text in entries
    ]
    target = tmp_path / "hashes.txt"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def resolve(tmp_path, repo, entries, capsys):
    path = write_hashes(tmp_path, repo, entries)
    code = identify_release.main([str(path), "--repo", str(repo)])
    return code, capsys.readouterr().out


def test_install_matching_head_is_reported_as_current(history, tmp_path, capsys):
    repo, _, second = history
    code, out = resolve(
        tmp_path, repo,
        [("proposal-check/SKILL.md", V2), ("proposal-check/scripts/check.py", SCRIPT)],
        capsys,
    )
    assert code == 0
    assert "matches HEAD" in out
    assert second in out


def test_clean_install_of_an_older_revision_names_that_revision(history, tmp_path, capsys):
    repo, first, _ = history
    code, out = resolve(
        tmp_path, repo,
        [("proposal-check/SKILL.md", V1), ("proposal-check/scripts/check.py", SCRIPT)],
        capsys,
    )
    assert code == 0
    assert f"Clean install of {first}" in out
    assert "1 commit(s) behind" in out
    assert "Reproduce against that revision" in out


def test_a_locally_edited_file_matches_no_revision(history, tmp_path, capsys):
    repo, _, _ = history
    code, out = resolve(
        tmp_path, repo,
        [
            ("proposal-check/SKILL.md", V2 + "\n<!-- student tweaked this -->\n"),
            ("proposal-check/scripts/check.py", SCRIPT),
        ],
        capsys,
    )
    assert code == 1
    assert "edited locally" in out
    assert SKILL_FILE in out


def test_a_mixed_install_does_not_read_as_clean(history, tmp_path, capsys):
    """V1 of the instructions beside an edited script: no single revision holds
    both, so the verdict must not name one as a clean match."""
    repo, _, _ = history
    code, out = resolve(
        tmp_path, repo,
        [
            ("proposal-check/SKILL.md", V1),
            ("proposal-check/scripts/check.py", SCRIPT + "print('patched')\n"),
        ],
        capsys,
    )
    assert code == 1
    assert "Clean install" not in out
    assert OTHER_FILE in out


def test_a_file_absent_from_history_is_distinguished_from_an_edit(history, tmp_path, capsys):
    """A skill from a newer release, or another package, is not a local edit."""
    repo, _, _ = history
    code, out = resolve(
        tmp_path, repo,
        [
            ("proposal-check/SKILL.md", V2),
            ("proposal-check/scripts/check.py", SCRIPT),
            ("proposal-newthing/SKILL.md", "# Something we never shipped\n"),
        ],
        capsys,
    )
    assert code == 1
    assert "Not in this repository's history" in out
    assert "proposal-newthing/SKILL.md" in out
    assert "edited locally" not in out


def test_crlf_install_matches_via_the_normalized_hash(history, tmp_path, capsys):
    """A Windows checkout of an unmodified file must not read as modified."""
    repo, _, second = history
    crlf = V2.replace("\n", "\r\n")
    line = (
        f"proposal-check/SKILL.md git_blob={blob(repo, crlf)} "
        f"git_blob_lf={blob(repo, V2)} sha256=unused bytes={len(crlf.encode())}"
    )
    target = tmp_path / "hashes.txt"
    target.write_text(line + "\n", encoding="utf-8")
    code = identify_release.main([str(target), "--repo", str(repo)])
    out = capsys.readouterr().out
    assert code == 0
    assert second in out
    assert "edited locally" not in out


def test_accepts_a_bundle_directory(history, tmp_path, capsys):
    repo, _, _ = history
    bundle = tmp_path / "bug-report"
    bundle.mkdir()
    entries = [("proposal-check/SKILL.md", V2), ("proposal-check/scripts/check.py", SCRIPT)]
    written = write_hashes(tmp_path, repo, entries)
    (bundle / "hashes.txt").write_text(written.read_text(encoding="utf-8"), encoding="utf-8")
    assert identify_release.main([str(bundle), "--repo", str(repo)]) == 0
    assert "matches HEAD" in capsys.readouterr().out


def test_missing_hashes_file_is_an_error_not_a_verdict(tmp_path, capsys):
    assert identify_release.main([str(tmp_path / "nope.txt")]) == 2
    assert "no hashes.txt" in capsys.readouterr().err


def test_an_unparseable_hashes_file_is_an_error(history, tmp_path, capsys):
    repo, _, _ = history
    target = tmp_path / "hashes.txt"
    target.write_text("this is not a hash line\n", encoding="utf-8")
    assert identify_release.main([str(target), "--repo", str(repo)]) == 2
    assert "no hash entries parsed" in capsys.readouterr().err


def test_parse_hashes_prefixes_paths_into_the_repository_layout():
    entries = identify_release.parse_hashes(
        "proposal-check/SKILL.md git_blob=abc123 sha256=def bytes=10\n"
    )
    assert entries[0]["path"] == "skills/proposal-check/SKILL.md"
    assert entries[0]["git_blob"] == "abc123"


def test_parse_hashes_skips_comments_and_blank_lines():
    assert identify_release.parse_hashes("# a comment\n\n") == []
