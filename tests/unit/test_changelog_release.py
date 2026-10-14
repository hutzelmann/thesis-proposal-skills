"""L0: `poe release` (scripts/changelog.py release, add-release-command).

The pure steps are tested on text; one end-to-end run cuts a release in a
throwaway git repository and checks that it made exactly one commit and one
annotated tag, and left nothing else behind."""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

import changelog
import pytest
from helpers import CHANGELOG_SAMPLE, REPO, changelog_root


def unreleased(text: str = CHANGELOG_SAMPLE) -> changelog.Release:
    return changelog.parse(text).releases[0]


FIRST_ENTRY = "- Something new ([b-change](openspec/changes/archive/2026-10-15-b-change/))\n"


def with_entry(category: str, entry: str) -> str:
    """The sample with one more category after Added in [Unreleased]."""
    return CHANGELOG_SAMPLE.replace(FIRST_ENTRY, f"{FIRST_ENTRY}\n### {category}\n\n- {entry}\n", 1)


# ---------- the bump table --------------------------------------------------------


@pytest.mark.parametrize(("text", "current", "need"), [
    (CHANGELOG_SAMPLE, (0, 8, 0), "minor"),                       # an Added entry
    (with_entry("Fixed", "x"), (0, 8, 0), "minor"),               # Added still present
    (with_entry("Changed", "**Breaking:** x"), (0, 8, 0), "minor"),  # breaking below 1.0
    (with_entry("Changed", "**Breaking:** x"), (1, 2, 0), "major"),
])
def test_entries_set_the_minimum_bump(text, current, need):
    assert changelog.required_bump(unreleased(text), current) == need


def test_fixes_alone_need_a_patch():
    only_fixed = CHANGELOG_SAMPLE.replace("### Added\n\n- Something new", "### Fixed\n\n- A fix")
    assert changelog.required_bump(unreleased(only_fixed), (0, 8, 0)) == "patch"


def test_a_lower_bump_than_required_is_refused():
    with pytest.raises(changelog.ReleaseRefused, match="lower than the entries require"):
        changelog.choose_version(unreleased(), (0, 8, 0), "patch", None)
    with pytest.raises(changelog.ReleaseRefused, match=r"below 0\.9\.0"):
        changelog.choose_version(unreleased(), (0, 8, 0), None, "0.8.1")
    assert changelog.choose_version(unreleased(), (0, 8, 0), "major", None)[0] == (1, 0, 0)
    assert changelog.choose_version(unreleased(), (0, 8, 0), None, None)[0] == (0, 9, 0)


# ---------- the cut ------------------------------------------------------------------


def test_cut_moves_unreleased_under_the_new_version(tmp_path):
    text = changelog.cut(CHANGELOG_SAMPLE, "0.3.0", "2026-10-20", ["- Model support: x."])
    cl = changelog.parse(text)
    head, new = cl.releases[0], cl.releases[1]
    assert head.title == changelog.UNRELEASED
    assert head.entries == []
    assert head.body[1] == "_On `develop`, not yet released._"
    assert (new.title, new.date) == ("0.3.0", "2026-10-20")
    assert "A lead for the next release." in new.body
    assert new.by_category["Changed"] == ["- Model support: x."]
    assert new.entries[0].startswith("- Something new")
    root = changelog_root(tmp_path, text, stamp="0.3.0", project="0.3.0")
    assert changelog.check(root, lambda _t: None) == []


def test_cut_refuses_a_release_without_a_lead():
    no_lead = CHANGELOG_SAMPLE.replace("A lead for the next release.\n\n", "")
    with pytest.raises(changelog.ReleaseRefused, match="no lead"):
        changelog.cut(no_lead, "0.3.0", "2026-10-20", [])


def test_version_is_set_in_pyproject_and_the_lock():
    pyproject = '[project]\nname = "x"\nversion = "0.1.0"\n\n[tool.x]\nversion = "9"\n'
    out = changelog.set_project_version(pyproject, "0.9.0")
    assert tomllib.loads(out)["project"]["version"] == "0.9.0"
    assert 'version = "9"' in out
    lock = '[[package]]\nname = "thesis-proposal-skills"\nversion = "0.1.0"\nsource = {}\n'
    assert 'version = "0.9.0"' in changelog.set_lock_version(lock, "0.9.0")
    assert (REPO / "uv.lock").read_text(encoding="utf-8").count(
        'name = "thesis-proposal-skills"\nversion = ') == 1


# ---------- the 1.0.0 readiness gate ---------------------------------------------------


README = """# x
<!-- model-support:start -->
| Model (pinned version) | Verdict | Notes |
|---|---|---|
| `anthropic/claude-sonnet-5.5` | ✅ solid |  |
| `moonshotai/kimi-k3` | ❔ untested |  |
<!-- model-support:end -->
"""


def test_readiness_names_the_open_change_and_each_untested_row(tmp_path):
    (tmp_path / "README.md").write_text(README, encoding="utf-8")
    (tmp_path / "openspec" / "changes" / "desktop-first-install").mkdir(parents=True)
    assert changelog.readiness_problems(tmp_path) == [
        "OpenSpec change desktop-first-install is still open",
        "model-support summary reads untested for moonshotai/kimi-k3"]
    (tmp_path / "README.md").write_text(README.replace("❔ untested", "✅ solid"),
                                        encoding="utf-8")
    (tmp_path / "openspec" / "changes" / "desktop-first-install").rmdir()
    assert changelog.readiness_problems(tmp_path) == []


def test_the_live_readme_summary_parses():
    rows = changelog.summary_rows((REPO / "README.md").read_text(encoding="utf-8"))
    assert rows, "the README model-support table changed shape; update summary_rows"


# ---------- model support ------------------------------------------------------------


def test_model_support_line_names_added_retired_and_rejudged():
    line = changelog.model_support_line(
        ["openrouter/anthropic/claude-haiku-4.5", "openrouter/moonshotai/kimi-k3"],
        ["openrouter/anthropic/claude-haiku-5.5", "openrouter/moonshotai/kimi-k3"],
        {"moonshotai/kimi-k3": "❔ untested"}, {"moonshotai/kimi-k3": "🟡 partial"})
    assert line == ("- Model support: joins the roster: Claude Haiku 5.5; leaves the roster: "
                    "Claude Haiku 4.5; re-judged: Kimi K3 (untested → partial) "
                    "(see the README's Model support table).")
    assert changelog.model_support_line(["a/b-c"], ["a/b-c"], {}, {}) is None


def test_prose_names_of_the_roster_are_never_model_ids():
    # tests/unit/test_model_ids.py matches lowercase, hyphenated identifier heads
    models = changelog.roster((REPO / "harness" / "models.toml").read_text(encoding="utf-8"))
    for model_id in models:
        name = changelog.prose_name(model_id)
        assert "-" not in name
        assert "/" not in name
        assert all(not word[0].islower() for word in name.split()), name


# ---------- end to end ----------------------------------------------------------------


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=True).stdout


@pytest.fixture
def repo(tmp_path):
    root = changelog_root(tmp_path / "repo")
    git(root, "init", "-q", "-b", "main")
    for key, value in (("user.name", "Erika Musterfrau"), ("user.email", "erika@example.org"),
                       ("commit.gpgsign", "false"), ("tag.gpgSign", "false"),
                       ("core.hooksPath", "/dev/null")):
        git(root, "config", key, value)
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "seed")
    return root


def release(root: Path, *args: str) -> int:
    return changelog.main(["--root", str(root), "release", "--date", "2026-10-20", *args])


def test_dry_run_changes_nothing(repo, capsys):
    assert release(repo, "--dry-run") == 0
    out = capsys.readouterr().out
    assert out.startswith("release 0.3.0: minor bump over 0.2.0")
    assert "A lead for the next release." in out
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "tag") == ""


def test_a_release_makes_one_commit_and_one_annotated_tag(repo, capsys):
    before = git(repo, "rev-parse", "HEAD").strip()
    assert release(repo) == 0
    out = capsys.readouterr().out
    assert "Nothing was pushed" in out
    assert "git push origin main v0.3.0" in out
    assert git(repo, "status", "--porcelain") == ""
    assert git(repo, "rev-parse", "HEAD~1").strip() == before
    assert git(repo, "log", "-1", "--format=%s").strip() == "chore(publish): stamp 0.3.0"
    assert git(repo, "cat-file", "-t", "v0.3.0").strip() == "tag"
    assert git(repo, "rev-parse", "v0.3.0^{commit}") == git(repo, "rev-parse", "HEAD")
    changed = set(git(repo, "diff", "--name-only", "HEAD~1", "HEAD").split())
    assert changed == {"CHANGELOG.md", "pyproject.toml", "skills/proposal-one/SKILL.md",
                       "skills/proposal-two/SKILL.md"}
    assert "metadata:\n  version: 0.3.0" in (repo / "skills/proposal-one/SKILL.md").read_text(
        encoding="utf-8")


def test_a_release_refuses_edited_files_and_an_existing_tag(repo, capsys):
    (repo / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n# edit\n',
                                         encoding="utf-8")
    assert release(repo) == 1
    assert "uncommitted edits" in capsys.readouterr().err
    git(repo, "checkout", "--", "pyproject.toml")
    git(repo, "tag", "-a", "v0.3.0", "-m", "x")
    assert release(repo) == 1
    assert "tag v0.3.0 already exists" in capsys.readouterr().err
    assert git(repo, "status", "--porcelain") == ""


def on_develop(repo: Path) -> Path:
    git(repo, "checkout", "-q", "-b", "develop")
    return repo


def test_a_release_on_develop_fast_forwards_main(repo, capsys):
    on_develop(repo)
    assert release(repo) == 0
    assert git(repo, "rev-parse", "main") == git(repo, "rev-parse", "HEAD")
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip() == "develop"
    out = capsys.readouterr().out
    assert "`main` fast-forwarded and tagged v0.3.0" in out
    assert "git push origin develop main v0.3.0" in out


def test_main_checked_out_elsewhere_is_left_for_the_maintainer(repo, tmp_path, capsys):
    on_develop(repo)
    other = tmp_path / "main-checkout"
    git(repo, "worktree", "add", "-q", str(other), "main")
    before = git(repo, "rev-parse", "main")
    assert release(repo) == 0
    assert git(repo, "rev-parse", "main") == before
    assert f"git -C {other} merge --ff-only develop" in capsys.readouterr().out


@pytest.mark.parametrize("setup", ["feature", "main-with-develop", "main-diverged"])
def test_releases_are_cut_on_develop_only(repo, capsys, setup):
    if setup == "feature":
        git(repo, "checkout", "-q", "-b", "feature")
        expected = "releases are cut on `develop` (current branch: feature)"
    elif setup == "main-with-develop":
        git(repo, "branch", "develop")
        expected = "releases are cut on `develop` (current branch: main)"
    else:
        git(repo, "branch", "develop")
        git(repo, "commit", "-q", "--allow-empty", "-m", "straight onto main")
        git(repo, "checkout", "-q", "develop")
        expected = "`main` has commits `develop` lacks"
    assert release(repo) == 1
    assert expected in capsys.readouterr().err
    assert git(repo, "status", "--porcelain") == ""


def test_one_zero_is_refused_while_the_gate_is_open(repo, capsys):
    (repo / "README.md").write_text(README, encoding="utf-8")
    assert release(repo, "--version", "1.0.0", "--dry-run") == 1
    assert "readiness gate: model-support summary reads untested for moonshotai/kimi-k3" in (
        capsys.readouterr().err)
