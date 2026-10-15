"""L0: the repository installer (installation spec).

Everything runs in-process against a temporary home and working directory, so
nothing here can touch the developer's own agent configuration. The default
source is the network; tests that exercise it replace `install.fetch`.
"""

from __future__ import annotations

import ast
import http.client
import io
import json
import ssl
import subprocess
import sys
import urllib.error
import zipfile
from pathlib import Path

import pytest
from helpers import REPO, fake_home, fixture_proposal

import install

SHA = "0123456789abcdef0123456789abcdef01234567"
NEWER = "fedcba9876543210fedcba9876543210fedcba98"
PREFIX = "thesis-proposal-skills-main/"


def skill_set(*names: str, extra: dict[str, bytes] | None = None) -> dict[str, dict[str, bytes]]:
    out = {n: {"SKILL.md": f"---\nname: {n}\n---\n".encode(), "scripts/run.py": b"x = 1\r\n"}
           for n in names}
    for path, payload in (extra or {}).items():
        name, inner = path.split("/", 1)
        out.setdefault(name, {})[inner] = payload
    return out


def make_zip(path: Path, skills: dict[str, dict[str, bytes]], comment: str | None = SHA) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(PREFIX + "README.md", "repo readme")
        for name, files in skills.items():
            for inner, payload in files.items():
                info = zipfile.ZipInfo(f"{PREFIX}skills/{name}/{inner}")
                info.external_attr = (0o755 if inner.endswith(".py") else 0o644) << 16
                archive.writestr(info, payload)
        if comment is not None:
            archive.comment = comment.encode()
    return path


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A fake home and a proposal folder inside it, the agent's working directory."""
    home = tmp_path / "home"
    cwd = home / "proposals"
    cwd.mkdir(parents=True)
    fake_home(monkeypatch, home)
    monkeypatch.chdir(cwd)
    return home, cwd


def run(*argv: str, capsys=None) -> tuple[int, str, str]:
    code = install.main(list(argv))
    out, err = capsys.readouterr() if capsys else ("", "")
    return code, out, err


def files_under(directory: Path) -> dict[str, bytes]:
    return {p.relative_to(directory).as_posix(): p.read_bytes()
            for p in sorted(directory.rglob("*")) if p.is_file()}


# ---------- usage and preconditions ------------------------------------------


def test_scope_is_required_and_both_choices_named(env, capsys):
    code, _out, err = run(capsys=capsys)
    assert code == install.EXIT_USAGE
    assert "--scope all" in err
    assert "--scope folder" in err
    assert not (env[0] / ".agents").exists()


@pytest.mark.usefixtures("env")
def test_unknown_option_is_a_usage_error(capsys):
    code, _, err = run("--scope", "everywhere", capsys=capsys)
    assert code == install.EXIT_USAGE
    assert "usage error" in err


@pytest.mark.usefixtures("env")
def test_old_interpreter_gets_a_sentence_not_a_traceback(capsys, monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 9, 6))
    code, _, err = run("--scope", "all", capsys=capsys)
    assert code == install.EXIT_ENV
    assert "Python 3.11 or newer" in err
    assert "3.9" in err


# ---------- fresh install, both scopes ------------------------------------------


def test_all_scope_fills_both_user_directories_byte_identically(env, tmp_path, capsys):
    home, _ = env
    skills = skill_set("proposal-check", "proposal-write")
    zip_path = make_zip(tmp_path / "src.zip", skills)
    code, out, _ = run("--scope", "all", "--source", str(zip_path), capsys=capsys)
    assert code == install.EXIT_OK
    for rel in (".agents/skills", ".claude/skills"):
        root = home / rel
        for name, files in skills.items():
            assert files_under(root / name) == files, f"{rel}/{name} differs"
        record = json.loads((root / install.RECORD_NAME).read_text(encoding="utf-8"))
        assert record["revision"] == SHA
        assert record["scope"] == "all"
        assert record["source"] == "zip"
        assert record["directories"] == ["~/.agents/skills", "~/.claude/skills"]
        assert record["skills"] == ["proposal-check", "proposal-write"]
    assert "revision 0123456 (before: not installed)" in out
    assert "new chat" in out
    assert str(home) not in out, "the user's home path must not be printed"


def test_folder_scope_installs_into_the_working_directory_only(env, tmp_path, capsys):
    home, cwd = env
    zip_path = make_zip(tmp_path / "src.zip", skill_set("proposal-check"))
    assert run("--scope", "folder", "--source", str(zip_path), capsys=capsys)[0] == 0
    assert (cwd / ".agents/skills/proposal-check/SKILL.md").is_file()
    assert (cwd / ".claude/skills/proposal-check/SKILL.md").is_file()
    assert not (home / ".agents").exists()
    record = install.read_record(cwd / ".claude/skills")
    assert record["directories"] == ["./.agents/skills", "./.claude/skills"]


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX mode bits")
def test_script_modes_travel(env, tmp_path, capsys):
    home, _ = env
    zip_path = make_zip(tmp_path / "src.zip", skill_set("proposal-check"))
    run("--scope", "all", "--source", str(zip_path), capsys=capsys)
    assert (home / ".claude/skills/proposal-check/scripts/run.py").stat().st_mode & 0o111


def test_app_specific_directory_only_when_the_app_is_present(env, tmp_path, capsys):
    home, cwd = env
    zip_path = make_zip(tmp_path / "src.zip", skill_set("proposal-check"))
    run("--scope", "all", "--source", str(zip_path), capsys=capsys)
    for host in install.HOST_DIRS:
        assert not (home / host.user_dir).exists(), f"{host.app} directory created without the app"
    for host in install.HOST_DIRS:
        (home / host.markers[0]).mkdir(parents=True, exist_ok=True)
    run("--scope", "all", "--source", str(zip_path), capsys=capsys)
    for host in install.HOST_DIRS:
        assert (home / host.user_dir / "proposal-check" / "SKILL.md").is_file(), host.app
    run("--scope", "folder", "--source", str(zip_path), capsys=capsys)
    for host in install.HOST_DIRS:
        if host.folder_dir:
            assert (cwd / host.folder_dir / "proposal-check" / "SKILL.md").is_file(), host.app


# ---------- updating ----------------------------------------------------------


def test_rerun_replaces_removes_upstream_deletions_and_names_both_revisions(
        env, tmp_path, capsys):
    home, _ = env
    old = skill_set("proposal-check", "proposal-retired",
                    extra={"proposal-check/references/gone.md": b"old"})
    run("--scope", "all", "--source", str(make_zip(tmp_path / "a.zip", old)), capsys=capsys)
    new = skill_set("proposal-check")
    new["proposal-check"]["SKILL.md"] = b"---\nname: proposal-check\n---\nnew\n"
    code, out, _ = run("--scope", "all", "--source",
                       str(make_zip(tmp_path / "b.zip", new, NEWER)), capsys=capsys)
    assert code == 0
    root = home / ".claude/skills"
    assert files_under(root / "proposal-check") == new["proposal-check"]
    assert not (root / "proposal-retired").exists(), "a skill retired upstream stayed behind"
    assert "revision fedcba9 (before: 0123456)" in out
    assert not [p for p in root.iterdir() if p.name.startswith(".proposal-")], "staging left"


def test_unrelated_skills_are_left_alone(env, tmp_path, capsys):
    home, _ = env
    mine = home / ".claude/skills/my-own-skill"
    mine.mkdir(parents=True)
    (mine / "SKILL.md").write_text("mine", encoding="utf-8")
    run("--scope", "all", "--source",
        str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))), capsys=capsys)
    assert (mine / "SKILL.md").read_text(encoding="utf-8") == "mine"


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation needs privileges")
def test_symlinked_copies_from_the_terminal_installer_are_replaced(env, tmp_path, capsys):
    """The skills CLI links `.claude/skills/<name>` into `.agents/skills`."""
    _home, cwd = env
    real = cwd / ".agents/skills/proposal-check"
    real.mkdir(parents=True)
    (real / "SKILL.md").write_text("stale", encoding="utf-8")
    (cwd / ".claude/skills").mkdir(parents=True)
    (cwd / ".claude/skills/proposal-check").symlink_to(real, target_is_directory=True)
    zip_path = make_zip(tmp_path / "src.zip", skill_set("proposal-check"))
    assert run("--scope", "folder", "--source", str(zip_path), capsys=capsys)[0] == 0
    link = cwd / ".claude/skills/proposal-check"
    assert not link.is_symlink()
    assert (link / "SKILL.md").read_bytes().startswith(b"---")


# ---------- conflicting installs -------------------------------------------------


def claude_registry(home: Path) -> None:
    path = home / ".claude/plugins/installed_plugins.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"version": 2, "plugins": {install.PLUGIN_ID: [{"scope": "user"}]}}),
                    encoding="utf-8")


def codex_config(home: Path) -> None:
    path = home / ".codex/config.toml"
    path.parent.mkdir(parents=True)
    path.write_text(f'[plugins."{install.PLUGIN_ID}"]\nenabled = true\n', encoding="utf-8")


def copilot_folder(home: Path) -> None:
    (home / install.PLUGIN_FOLDERS[0][1]).mkdir(parents=True)


def vscode_folder(home: Path) -> None:
    (home / ".config/Code" / install.VSCODE_PLUGIN).mkdir(parents=True)


@pytest.mark.parametrize("plant", [claude_registry, codex_config, copilot_folder, vscode_folder],
                         ids=lambda f: f.__name__)
def test_plugin_install_refuses_and_writes_nothing(env, tmp_path, capsys, plant):
    home, _ = env
    plant(home)
    code, out, _ = run("--scope", "all", "--source",
                       str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))),
                       capsys=capsys)
    assert code == install.EXIT_CONFLICT
    assert "plugin" in out
    assert "Check for updates" in out
    assert not (home / ".agents").exists()


def test_a_lingering_plugin_cache_is_not_an_install(env, tmp_path, capsys):
    """Claude keeps an uninstalled plugin's cache for two weeks."""
    home, _ = env
    (home / ".claude/plugins/cache/thesis-proposal/thesis-proposal/abc123").mkdir(parents=True)
    (home / ".claude/plugins").joinpath("installed_plugins.json").write_text(
        '{"version": 2, "plugins": {}}', encoding="utf-8")
    code, _, _ = run("--scope", "all", "--source",
                     str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))),
                     capsys=capsys)
    assert code == install.EXIT_OK


def test_other_scope_copies_listed_and_kept_then_removed_on_request(env, tmp_path, capsys):
    home, cwd = env
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    run("--scope", "folder", "--source", zip_path, capsys=capsys)
    code, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert code == 0
    assert "./.claude/skills/proposal-check" in out
    assert "--remove-other" in out
    assert (cwd / ".claude/skills/proposal-check").is_dir(), "kept without the option"
    code, out, _ = run("--scope", "all", "--remove-other", "--source", zip_path, capsys=capsys)
    assert code == 0
    assert "Removed" in out
    assert not (cwd / ".claude/skills/proposal-check").exists()
    assert not (cwd / ".claude/skills" / install.RECORD_NAME).exists()
    assert (home / ".claude/skills/proposal-check").is_dir()


def test_working_directory_equal_to_home_is_not_its_own_other_scope(
        tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"
    home.mkdir()
    fake_home(monkeypatch, home)
    monkeypatch.chdir(home)
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    run("--scope", "all", "--source", zip_path, capsys=capsys)
    _, out, _ = run("--scope", "all", "--remove-other", "--source", zip_path, capsys=capsys)
    assert "other scope" not in out
    assert "~/.claude/skills" in out, "an all-projects install is shown home-relative"
    assert (home / ".claude/skills/proposal-check").is_dir()


def test_folder_scope_in_the_home_folder_is_an_all_projects_install(
        tmp_path, monkeypatch, capsys):
    home = tmp_path / "home"
    home.mkdir()
    fake_home(monkeypatch, home)
    monkeypatch.chdir(home)
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", "folder", "--source", zip_path, capsys=capsys)
    assert code == 0
    assert "for all your projects" in out
    assert "your home folder" in out
    assert install.read_record(home / ".claude/skills")["scope"] == "all"


def test_paths_above_the_home_folder_never_show_a_user_name(tmp_path):
    home = tmp_path / "users" / "erika"
    assert install.display(home / ".agents/skills", home, tmp_path / "users") == "~/.agents/skills"
    assert install.display(home / ".agents/skills", home, home) == "~/.agents/skills"
    assert install.display(home / "p" / ".claude/skills", home, home / "p") == "./.claude/skills"


# ---------- sources ---------------------------------------------------------------


def test_directory_source_records_an_unknown_revision(env, tmp_path, capsys):
    home, _ = env
    src = tmp_path / "repo" / "skills" / "proposal-check"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text("---\nname: proposal-check\n---\n", encoding="utf-8")
    assert run("--scope", "all", "--source", str(tmp_path / "repo"), capsys=capsys)[0] == 0
    assert install.read_record(home / ".claude/skills")["revision"] == "unknown"


def test_zip_without_a_commit_comment_records_unknown(env, tmp_path, capsys):
    home, _ = env
    zip_path = make_zip(tmp_path / "src.zip", skill_set("proposal-check"), comment=None)
    run("--scope", "all", "--source", str(zip_path), capsys=capsys)
    assert install.read_record(home / ".agents/skills")["revision"] == "unknown"


def test_unsafe_member_paths_are_ignored(env, tmp_path, capsys):
    home, _ = env
    zip_path = make_zip(tmp_path / "src.zip", skill_set(
        "proposal-check", extra={"proposal-check/../../escaped.txt": b"no",
                                 "proposal-check/sub\\..\\x.txt": b"no"}))
    assert run("--scope", "all", "--source", str(zip_path), capsys=capsys)[0] == 0
    assert not list(home.rglob("escaped.txt"))
    assert not list(home.rglob("*x.txt"))


def test_source_without_skills_changes_nothing(env, tmp_path, capsys):
    home, _ = env
    zip_path = make_zip(tmp_path / "src.zip", {"proposal-check": {"README.md": b"no skill"}})
    code, _, err = run("--scope", "all", "--source", str(zip_path), capsys=capsys)
    assert code == install.EXIT_ENV
    assert "no complete skills" in err
    assert not (home / ".agents").exists()


@pytest.mark.usefixtures("env")
def test_missing_source_is_an_environment_error(tmp_path, capsys):
    code, _, err = run("--scope", "all", "--source", str(tmp_path / "nope.zip"), capsys=capsys)
    assert code == install.EXIT_ENV
    assert "source not found" in err


def test_default_source_is_the_default_branch_archive(env, tmp_path, capsys, monkeypatch):
    home, _ = env
    payload = make_zip(tmp_path / "src.zip", skill_set("proposal-check")).read_bytes()
    seen = []
    monkeypatch.setattr(install, "fetch", lambda url: seen.append(url) or payload)
    assert run("--scope", "all", capsys=capsys)[0] == 0
    assert seen == [install.DEFAULT_SOURCE]
    assert install.read_record(home / ".claude/skills")["source"] == "default-branch"


def test_network_failure_leaves_the_existing_install_unchanged(env, tmp_path, capsys,
                                                               monkeypatch):
    home, _ = env
    run("--scope", "all", "--source",
        str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))), capsys=capsys)
    before = files_under(home / ".claude/skills")

    def offline(*_args, **_kwargs):
        raise urllib.error.URLError("Name or service not known")

    monkeypatch.setattr(install.urllib.request, "urlopen", offline)
    code, _, err = run("--scope", "all", capsys=capsys)
    assert code == install.EXIT_ENV
    assert "internet connection" in err
    assert files_under(home / ".claude/skills") == before


def no_certs(*_args, **_kwargs):
    raise urllib.error.URLError(ssl.SSLCertVerificationError("unable to get local issuer"))


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def test_certificate_failure_retries_with_the_system_bundle(monkeypatch, tmp_path):
    bundle = tmp_path / "cert.pem"
    bundle.write_text("certs", encoding="utf-8")
    contexts = []

    def picky(request, timeout, context=None):
        contexts.append(context)
        if context is None:
            return no_certs(request, timeout)
        return FakeResponse(b"zipbytes")

    monkeypatch.setattr(install, "SYSTEM_CA_FILE", bundle)
    monkeypatch.setattr(install.ssl, "create_default_context", lambda cafile: f"ctx:{cafile}")
    monkeypatch.setattr(install.urllib.request, "urlopen", picky)
    assert install.fetch("https://example.org/x.zip") == b"zipbytes"
    assert contexts == [None, f"ctx:{bundle}"]


def test_certificate_failure_retries_through_curl(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, **_kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"zipbytes", stderr=b"")

    monkeypatch.setattr(install, "SYSTEM_CA_FILE", tmp_path / "absent.pem")
    monkeypatch.setattr(install.urllib.request, "urlopen", no_certs)
    monkeypatch.setattr(install, "system_curl", lambda: "/usr/bin/curl")
    monkeypatch.setattr(install.subprocess, "run", fake_run)
    install.NOTICES.clear()
    assert install.fetch("https://example.org/x.zip") == b"zipbytes"
    assert calls[0][0] == "/usr/bin/curl"
    assert calls[0][-1] == "https://example.org/x.zip"
    assert "=https" in calls[0], "a redirect must not downgrade to http"
    assert install.NOTICES == [install.CERT_NOTICE], "the student learns the skills need it too"


def test_certificate_failure_without_curl_names_the_macos_fix(monkeypatch, tmp_path):
    monkeypatch.setattr(install, "SYSTEM_CA_FILE", tmp_path / "absent.pem")
    monkeypatch.setattr(install.urllib.request, "urlopen", no_certs)
    monkeypatch.setattr(install, "system_curl", lambda: None)
    with pytest.raises(install.EnvironmentProblem, match="Install Certificates"):
        install.fetch("https://example.org/x.zip")


def test_curl_failure_is_reported(monkeypatch):
    monkeypatch.setattr(install, "system_curl", lambda: "/usr/bin/curl")
    monkeypatch.setattr(install.subprocess, "run", lambda cmd, **_kw: subprocess.CompletedProcess(
        cmd, 22, stdout=b"", stderr=b"curl: (22) 404"))
    with pytest.raises(install.EnvironmentProblem, match="404"):
        install.fetch_with_curl("https://example.org/x.zip")


def test_curl_timeout_is_an_environment_problem(monkeypatch):
    def slow(cmd, **_kw):
        raise subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(install, "system_curl", lambda: "/usr/bin/curl")
    monkeypatch.setattr(install.subprocess, "run", slow)
    with pytest.raises(install.EnvironmentProblem, match="timed out"):
        install.fetch_with_curl("https://example.org/x.zip")


def test_curl_comes_from_its_fixed_system_location(monkeypatch, tmp_path):
    """Never a PATH search: on Windows that looks in the student's folder first."""
    monkeypatch.setenv("SYSTEMROOT", "C:\\Windows\\")
    assert install.curl_candidates(windows=True) == [r"C:\Windows\System32\curl.exe"]
    assert install.curl_candidates(windows=False) == ["/usr/bin/curl", "/bin/curl"]
    planted = tmp_path / "curl"
    planted.write_bytes(b"")
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert install.system_curl() != str(planted)


@pytest.mark.usefixtures("env")
def test_a_broken_off_download_is_an_environment_problem(capsys, monkeypatch):
    def cut(*_args, **_kwargs):
        raise http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(install.urllib.request, "urlopen", cut)
    code, _, err = run("--scope", "all", capsys=capsys)
    assert code == install.EXIT_ENV
    assert "broke off" in err


def test_a_damaged_archive_member_is_an_environment_problem(env, tmp_path, capsys):
    home, _ = env
    good = make_zip(tmp_path / "good.zip", skill_set("proposal-check")).read_bytes()
    marker = b"---\nname: proposal-check"
    damaged = tmp_path / "damaged.zip"
    damaged.write_bytes(good.replace(marker, b"X" * len(marker), 1))
    code, _, err = run("--scope", "all", "--source", str(damaged), capsys=capsys)
    assert code == install.EXIT_ENV
    assert "damaged" in err
    assert not (home / ".agents").exists()


def test_dry_run_writes_nothing(env, tmp_path, capsys):
    home, _ = env
    code, out, _ = run("--scope", "all", "--dry-run", "--source",
                       str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))),
                       capsys=capsys)
    assert code == 0
    assert "Would install 1 skills" in out
    assert "~/.claude/skills" in out
    assert not (home / ".claude").exists()


@pytest.mark.usefixtures("env")
def test_unwritable_target_is_an_environment_error(tmp_path, capsys, monkeypatch):
    def denied(*_args, **_kwargs):
        raise PermissionError(13, "Permission denied", "/somewhere")

    monkeypatch.setattr(install, "install_into", denied)
    code, _, err = run("--scope", "all", "--source",
                       str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))),
                       capsys=capsys)
    assert code == install.EXIT_ENV
    assert "writable" in err


# ---------- the real tree -------------------------------------------------------------


def working_tree_zip(path: Path) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for file in sorted((REPO / "skills").rglob("*")):
            if file.is_file() and "__pycache__" not in file.parts:
                archive.write(file, PREFIX + file.relative_to(REPO).as_posix())
        archive.comment = SHA.encode()
    return path


# reads skills/ twice, and test_sync.py's tamper cases rewrite files there in place
@pytest.mark.xdist_group("sync_shared_tree")
def test_the_shipped_skills_install_and_run_from_their_installed_location(
        env, tmp_path, capsys):
    home, _ = env
    assert run("--scope", "all", "--source", str(working_tree_zip(tmp_path / "tree.zip")),
               capsys=capsys)[0] == 0
    shipped = sorted(d.name for d in (REPO / "skills").iterdir()
                     if d.is_dir() and d.name.startswith("proposal-"))
    root = home / ".claude/skills"
    assert sorted(p.name for p in root.iterdir() if p.is_dir()) == shipped
    for name in shipped:
        want = {k: v for k, v in files_under(REPO / "skills" / name).items()
                if "__pycache__" not in k}
        assert files_under(root / name) == want, name
    done = subprocess.run(
        [sys.executable, str(root / "proposal-check/scripts/check.py"),
         str(fixture_proposal("f15-format-broken"))],
        capture_output=True, encoding="utf-8", check=False,
    )
    assert done.returncode != 0
    assert "ERROR" in done.stdout


def test_record_is_valid_json_with_the_documented_keys(env, tmp_path, capsys):
    home, _ = env
    run("--scope", "all", "--source",
        str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))), capsys=capsys)
    record = json.loads((home / ".agents/skills" / install.RECORD_NAME).read_text(encoding="utf-8"))
    assert set(record) == {"package", "installer", "revision", "installed_at", "scope",
                           "source", "directories", "skills"}
    assert record["package"] == "thesis-proposal"


# ---------- names from records and archives never leave their folder --------


TRAVERSAL = ["proposal-check/../../..", "proposal-check/../../victim", "proposal-x\\..\\..",
             "../proposal-check", "proposal-check/scripts", None, 7, {"a": 1}]


def plant_record(directory: Path, skills: object) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / install.RECORD_NAME).write_text(
        json.dumps({"skills": skills, "revision": ["not", "a", "sha"]}), encoding="utf-8")


def test_a_planted_record_cannot_delete_outside_the_skill_folders(env, tmp_path, capsys):
    home, cwd = env
    victim = cwd.parent / "victim"
    victim.mkdir()
    (victim / "thesis.md").write_text("mine", encoding="utf-8")
    (cwd / "proposal.md").write_text("mine", encoding="utf-8")
    for rel in install.SHARED_DIRS:
        (cwd / rel / "proposal-check").mkdir(parents=True)
        plant_record(cwd / rel, TRAVERSAL)
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    assert run("--scope", "folder", "--source", zip_path, capsys=capsys)[0] == 0
    assert (cwd / "proposal.md").read_text(encoding="utf-8") == "mine"
    assert (victim / "thesis.md").is_file()
    assert (cwd / ".agents/skills/proposal-check/scripts/run.py").is_file()
    plant_record(cwd / ".claude/skills", TRAVERSAL)
    assert run("--scope", "all", "--remove-other", "--source", zip_path, capsys=capsys)[0] == 0
    assert (cwd / "proposal.md").is_file()
    assert (victim / "thesis.md").is_file()
    assert (home / ".claude/skills/proposal-check/SKILL.md").is_file()


def test_a_record_with_a_non_list_skills_entry_does_not_crash(env, tmp_path, capsys):
    home, _ = env
    plant_record(home / ".claude/skills", None)
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert code == 0
    assert "(before: unknown)" in out


def test_archive_folder_names_outside_the_pattern_are_ignored(env, tmp_path, capsys):
    home, _ = env
    zip_path = make_zip(tmp_path / "src.zip", {
        **skill_set("proposal-check"),
        "proposal-x\\..\\..": {"SKILL.md": b"no"},
        "Proposal-Upper": {"SKILL.md": b"no"},
    })
    assert run("--scope", "all", "--source", str(zip_path), capsys=capsys)[0] == 0
    installed = sorted(p.name for p in (home / ".claude/skills").iterdir() if p.is_dir())
    assert installed == ["proposal-check"]


# ---------- the swap: rollback, best-effort cleanup, leftover sweep ---------


def test_a_failed_swap_restores_the_previous_copy(env, tmp_path, capsys, monkeypatch):
    home, _ = env
    old = skill_set("proposal-check")
    run("--scope", "all", "--source", str(make_zip(tmp_path / "a.zip", old)), capsys=capsys)
    real_rename = Path.rename

    def locked(self, target):
        if ".new-" in self.name:
            raise PermissionError(13, "in use", str(self))
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", locked)
    new = skill_set("proposal-check", extra={"proposal-check/added.md": b"new"})
    code, _, err = run("--scope", "all", "--source", str(make_zip(tmp_path / "b.zip", new)),
                       capsys=capsys)
    assert code == install.EXIT_ENV
    assert "~/" in err, "the failing path is shown home-relative"
    root = home / ".agents/skills"
    assert files_under(root / "proposal-check") == old["proposal-check"]
    assert sorted(p.name for p in root.iterdir()) == [install.RECORD_NAME, "proposal-check"]


def test_a_locked_old_copy_does_not_fail_a_finished_install(env, tmp_path, capsys, monkeypatch):
    home, _ = env
    zip_path = str(make_zip(tmp_path / "a.zip", skill_set("proposal-check")))
    run("--scope", "all", "--source", zip_path, capsys=capsys)
    real_remove = install.remove_entry

    def locked(path):
        if ".old-" in path.name and path.exists():
            raise PermissionError(13, "in use", str(path))
        return real_remove(path)

    monkeypatch.setattr(install, "remove_entry", locked)
    assert run("--scope", "all", "--source", zip_path, capsys=capsys)[0] == 0
    monkeypatch.setattr(install, "remove_entry", real_remove)
    root = home / ".claude/skills"
    assert [p for p in root.iterdir() if p.name.startswith(".proposal")], "a locked copy stays"
    assert run("--scope", "all", "--source", zip_path, capsys=capsys)[0] == 0
    assert not [p for p in root.iterdir() if p.name.startswith(".proposal")], "and is swept"


def test_leftovers_of_an_interrupted_run_are_swept(env, tmp_path, capsys):
    home, _ = env
    root = home / ".claude/skills"
    for name in (".proposal-check.new-123", ".proposal-check.old-456"):
        (root / name).mkdir(parents=True)
        (root / name / "SKILL.md").write_text("half", encoding="utf-8")
    (root / ".unrelated-dotfolder").mkdir()
    run("--scope", "all", "--source",
        str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))), capsys=capsys)
    assert sorted(p.name for p in root.iterdir()) == [
        install.RECORD_NAME, ".unrelated-dotfolder", "proposal-check"]


@pytest.mark.skipif(sys.platform != "win32", reason="directory junctions are a Windows feature")
def test_windows_junctions_from_the_terminal_installer_are_replaced(env, tmp_path, capsys):
    import _winapi

    home, _ = env
    real = home / ".agents/skills/proposal-check"
    real.mkdir(parents=True)
    (real / "SKILL.md").write_text("stale", encoding="utf-8")
    (home / ".claude/skills").mkdir(parents=True)
    _winapi.CreateJunction(str(real), str(home / ".claude/skills/proposal-check"))
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    assert run("--scope", "all", "--source", zip_path, capsys=capsys)[0] == 0
    link = home / ".claude/skills/proposal-check"
    assert not install.is_link(link)
    assert (link / "SKILL.md").read_bytes().startswith(b"---")


# ---------- more conflict evidence ------------------------------------------


def test_claude_plugin_button_install_refuses(env, tmp_path, capsys):
    """A plugin added with Claude's button syncs into Code sessions without an
    entry in installed_plugins.json."""
    home, _ = env
    (home / install.CLAUDE_SYNCED / "acct_org" / "marketplaces" / install.PACKAGE).mkdir(
        parents=True)
    code, out, _ = run("--scope", "all", "--source",
                       str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))),
                       capsys=capsys)
    assert code == install.EXIT_CONFLICT
    assert "Claude" in out


def test_claude_settings_naming_the_plugin_refuses(env, tmp_path, capsys):
    home, _ = env
    settings = home / ".claude/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"enabledPlugins": {"thesis-proposal@synced": True}}),
                        encoding="utf-8")
    code, _, _ = run("--scope", "all", "--source",
                     str(make_zip(tmp_path / "src.zip", skill_set("proposal-check"))),
                     capsys=capsys)
    assert code == install.EXIT_CONFLICT


def test_an_earlier_terminal_install_is_named(env, tmp_path, capsys):
    _, cwd = env
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    run("--scope", "folder", "--source", zip_path, capsys=capsys)
    (cwd / "skills-lock.json").write_text("{}", encoding="utf-8")
    _, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert "npx skills" in out
    assert (cwd / "skills-lock.json").read_text(encoding="utf-8") == "{}"


# ---------- pinned facts --------------------------------------------------------


def test_the_directory_table_is_the_documented_one():
    """Design D3, from the apps' own documentation (2026-10-03). A change here is
    a change to where students' skills land, so it must be deliberate."""
    assert install.SHARED_DIRS == (".agents/skills", ".claude/skills")
    assert [(h.app, h.markers, h.user_dir, h.folder_dir) for h in install.HOST_DIRS] == [
        ("Antigravity", (".gemini/antigravity", ".antigravity"), ".gemini/config/skills", None),
        ("Antigravity CLI", (".gemini/antigravity-cli",), ".gemini/antigravity-cli/skills",
         None),
        ("Kiro", (".kiro",), ".kiro/skills", ".kiro/skills"),
    ]


def test_an_exported_archive_names_its_commit(tmp_path):
    """The installer reads the revision from the zip comment, as GitHub writes it;
    the repository's own archive export writes it the same way, which is what
    install-check relies on."""
    head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--verify", "HEAD"],
                          capture_output=True, text=True, check=False)
    if head.returncode != 0:
        pytest.skip("not a git checkout")
    archive = tmp_path / "head.zip"
    subprocess.run(["git", "-C", str(REPO), "archive", "--format=zip", "--prefix=x/",
                    "-o", str(archive), "HEAD"], check=True)
    assert install.read_zip(archive.read_bytes(), "zip").revision == head.stdout.strip()


def test_the_installer_still_parses_on_an_old_interpreter():
    """The version gate only helps if Python 3.7 to 3.10 can reach it: no newer
    syntax anywhere, and nothing newer than 3.7's standard library at module
    level (a 3.11 name such as datetime.UTC belongs inside a function)."""
    source = Path(install.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source, feature_version=(3, 7))
    modules = {alias.name.split(".")[0] for node in tree.body if isinstance(node, ast.Import)
               for alias in node.names}
    modules |= {node.module.split(".")[0] for node in tree.body
                if isinstance(node, ast.ImportFrom) and node.module}
    assert not modules & {"tomllib", "zoneinfo", "graphlib"}, "a module newer than 3.7"
    module_level = [node for node in tree.body
                    if not isinstance(node, (ast.FunctionDef, ast.ClassDef))]
    defaults = [d for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                for d in node.args.defaults]
    for node in [*module_level, *defaults]:
        names = {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}
        assert "UTC" not in names, "datetime.UTC is 3.11+; use it inside a function"


# ---------- copies in apps' own skill folders (design D14) ------------------


def plant_skill(folder: Path, name: str = "proposal-check", body: str = "hand copy") -> Path:
    (folder / name).mkdir(parents=True, exist_ok=True)
    (folder / name / "SKILL.md").write_text(body, encoding="utf-8")
    return folder / name


def native_folder(home: Path, cwd: Path, app_dir: str) -> Path:
    base = next(base for _app, base, rel in install.NATIVE_DIRS if rel == app_dir)
    return (home if base == "home" else cwd) / app_dir


HAND_COPIES = [".opencode/skills", ".config/opencode/skill", ".codex/skills", ".cursor/skills",
               ".copilot/skills"]


@pytest.mark.parametrize("scope", ["all", "folder"])
def test_hand_copies_in_apps_own_folders_are_listed_and_kept(env, tmp_path, capsys, scope):
    home, cwd = env
    planted = [plant_skill(native_folder(home, cwd, rel)) for rel in HAND_COPIES]
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", scope, "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    for copy in planted:
        assert install.display(copy, home, cwd) in out, f"{copy} not listed"
        assert (copy / "SKILL.md").read_text(encoding="utf-8") == "hand copy", "kept"
    for app in ("OpenCode", "Codex", "Cursor", "GitHub Copilot"):
        assert f"({app})" in out
    assert "./.opencode/skills/proposal-check (OpenCode)" in out
    assert "~/.config/opencode/skill/proposal-check (OpenCode)" in out
    assert "--remove-other" in out


@pytest.mark.parametrize("scope", ["all", "folder"])
def test_remove_other_removes_exactly_the_listed_copies(env, tmp_path, capsys, scope):
    home, cwd = env
    folder = native_folder(home, cwd, ".opencode/skills")
    listed = plant_skill(folder)
    mine = plant_skill(folder, "my-own-skill", "mine")
    unshipped = plant_skill(folder, "proposal-mine", "mine")
    (folder / "notes.txt").write_text("mine", encoding="utf-8")
    codex = plant_skill(home / ".codex/skills")
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", scope, "--remove-other", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert "Removed the copies in other apps' own skill folders" in out
    assert not listed.exists()
    assert not codex.exists()
    assert (mine / "SKILL.md").read_text(encoding="utf-8") == "mine"
    assert (unshipped / "SKILL.md").read_text(encoding="utf-8") == "mine", \
        "a proposal-* folder that is not a shipped skill is not the installer's to judge"
    assert (folder / "notes.txt").is_file()
    assert (home / ".codex/skills").is_dir(), "the folder itself stays"


def test_a_folder_without_a_skill_file_is_not_a_copy(env, tmp_path, capsys):
    home, _ = env
    stray = home / ".cursor/skills/proposal-check"
    stray.mkdir(parents=True)
    (stray / "README.md").write_text("not a skill", encoding="utf-8")
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", "all", "--remove-other", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert ".cursor" not in out
    assert (stray / "README.md").is_file()


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation needs privileges")
@pytest.mark.parametrize("scope", ["all", "folder"])
def test_a_link_into_the_installed_copy_is_neither_listed_nor_removed(
        env, tmp_path, capsys, scope):
    """The skills CLI links agent folders into the shared copy; that is not a second copy."""
    home, cwd = env
    base = home if scope == "all" else cwd
    installed = base / ".agents/skills/proposal-check"
    link = home / ".codex/skills/proposal-check"
    link.parent.mkdir(parents=True)
    link.symlink_to(installed, target_is_directory=True)
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", scope, "--remove-other", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert ".codex" not in out
    assert link.is_symlink()
    assert (link / "SKILL.md").read_bytes().startswith(b"---")


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation needs privileges")
def test_a_whole_folder_linked_to_a_target_is_not_a_copy(env, tmp_path, capsys):
    home, _ = env
    (home / ".agents/skills").mkdir(parents=True)
    (home / ".cursor").mkdir()
    (home / ".cursor/skills").symlink_to(home / ".agents/skills", target_is_directory=True)
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", "all", "--remove-other", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert ".cursor" not in out
    assert (home / ".agents/skills/proposal-check/SKILL.md").is_file()


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation needs privileges")
def test_a_copy_in_a_folder_linked_elsewhere_is_listed_but_never_removed(
        env, tmp_path, capsys):
    """~/.codex/skills linked to a dotfiles folder (or a clone's skills/): the copy
    is not a link itself, so removing it would delete the tree at the link's target."""
    home, _ = env
    dotfiles = tmp_path / "dotfiles" / "skills"
    elsewhere = plant_skill(dotfiles, body="my own work")
    (home / ".codex").mkdir()
    (home / ".codex/skills").symlink_to(dotfiles, target_is_directory=True)
    direct = plant_skill(home / ".cursor/skills")
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    _, out, _ = run("--scope", "all", "--dry-run", "--remove-other", "--source", zip_path,
                    capsys=capsys)
    assert "Would remove copies in other apps' own skill folders: " \
           "~/.cursor/skills/proposal-check (Cursor)" in out
    assert "reached through a linked folder: ~/.codex/skills/proposal-check (Codex)" in out
    code, out, _ = run("--scope", "all", "--remove-other", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert "Removed the copies in other apps' own skill folders:\n" \
           "  ~/.cursor/skills/proposal-check (Cursor)\n" in out
    assert "reached through a link" in out
    assert "  ~/.codex/skills/proposal-check (Codex)" in out
    assert not direct.exists()
    assert (elsewhere / "SKILL.md").read_text(encoding="utf-8") == "my own work", \
        "nothing is deleted through a linked folder"
    assert (home / ".codex/skills").is_symlink()


@pytest.mark.skipif(sys.platform != "win32", reason="directory junctions are a Windows feature")
def test_a_junction_into_the_installed_copy_is_neither_listed_nor_removed(env, tmp_path, capsys):
    import _winapi

    home, _ = env
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    assert run("--scope", "all", "--source", zip_path, capsys=capsys)[0] == 0
    link = home / ".codex/skills/proposal-check"
    link.parent.mkdir(parents=True)
    _winapi.CreateJunction(str(home / ".agents/skills/proposal-check"), str(link))
    code, out, _ = run("--scope", "all", "--remove-other", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert ".codex" not in out
    assert install.is_link(link)
    assert (link / "SKILL.md").is_file()


@pytest.mark.skipif(sys.platform == "win32", reason="symlink creation needs privileges")
def test_a_link_to_a_copy_elsewhere_is_listed_and_removed_as_a_link(env, tmp_path, capsys):
    home, _ = env
    elsewhere = plant_skill(tmp_path / "elsewhere", body="my own work")
    link = home / ".config/opencode/skills/proposal-check"
    link.parent.mkdir(parents=True)
    link.symlink_to(elsewhere, target_is_directory=True)
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    _, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert "~/.config/opencode/skills/proposal-check (OpenCode)" in out
    assert link.is_symlink()
    run("--scope", "all", "--remove-other", "--source", zip_path, capsys=capsys)
    assert not link.is_symlink()
    assert not link.exists()
    assert (elsewhere / "SKILL.md").read_text(encoding="utf-8") == "my own work", \
        "the link's target is never touched"


def test_dry_run_names_copies_in_apps_folders_and_removes_nothing(env, tmp_path, capsys):
    home, cwd = env
    copy = plant_skill(cwd / ".opencode/skill")
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    _, out, _ = run("--scope", "all", "--dry-run", "--source", zip_path, capsys=capsys)
    assert "Would keep copies in other apps' own skill folders: " \
           "./.opencode/skill/proposal-check (OpenCode)" in out
    _, out, _ = run("--scope", "all", "--dry-run", "--remove-other", "--source", zip_path,
                    capsys=capsys)
    assert "Would remove copies in other apps' own skill folders" in out
    assert (copy / "SKILL.md").is_file()
    assert not (home / ".claude").exists()


@pytest.mark.parametrize("scope", ["all", "folder"])
def test_no_app_folder_is_ever_created(env, tmp_path, capsys, scope):
    home, cwd = env
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    run("--scope", scope, "--remove-other", "--source", zip_path, capsys=capsys)
    for _app, base, rel in install.NATIVE_DIRS:
        assert not ((home if base == "home" else cwd) / rel).exists(), rel
    assert not (home / ".codex").exists()
    assert not (cwd / ".opencode").exists()


def test_the_apps_own_folders_table_is_the_documented_one():
    """Design D14, checked 2026-10-13 (sources in the table's comment). The
    installer never writes these, so none may coincide with a target."""
    assert install.NATIVE_DIRS == (
        ("OpenCode", "folder", ".opencode/skill"),
        ("OpenCode", "folder", ".opencode/skills"),
        ("OpenCode", "home", ".config/opencode/skill"),
        ("OpenCode", "home", ".config/opencode/skills"),
        ("Codex", "home", ".codex/skills"),
        ("Cursor", "home", ".cursor/skills"),
        ("GitHub Copilot", "home", ".copilot/skills"),
    )
    written = set(install.SHARED_DIRS) | {h.user_dir for h in install.HOST_DIRS} \
        | {h.folder_dir for h in install.HOST_DIRS if h.folder_dir}
    assert not written & {rel for _app, _base, rel in install.NATIVE_DIRS}


# ---------- readiness lines (design D15) ----------------------------------------


def tool_path(monkeypatch, tmp_path: Path, *tools: str) -> None:
    """A PATH holding only stub executables for `tools`."""
    folder = tmp_path / "bin"
    folder.mkdir(exist_ok=True)
    for tool in tools:
        stub = folder / (tool + (".exe" if sys.platform == "win32" else ""))
        stub.write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(folder))


@pytest.mark.usefixtures("env")
def test_missing_pdf_tools_are_optional_and_do_not_fail_the_install(tmp_path, capsys,
                                                                   monkeypatch):
    tool_path(monkeypatch, tmp_path)
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert "On this computer:" in out
    assert "PDF export (optional): pandoc missing, typst missing." in out
    assert "Only PDF export needs them" in out
    assert out.rstrip().splitlines()[-1].startswith("  API keys (optional)"), \
        "the readiness lines end the output"


@pytest.mark.usefixtures("env")
def test_found_pdf_tools_are_reported_without_running_them(tmp_path, capsys, monkeypatch):
    tool_path(monkeypatch, tmp_path, "pandoc", "typst")
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))

    def forbidden(*_args, **_kwargs):
        raise AssertionError("the installer ran a program to produce a readiness line")

    monkeypatch.setattr(install.subprocess, "run", forbidden)
    monkeypatch.setattr(install.subprocess, "Popen", forbidden)
    code, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert "PDF export (optional): pandoc found, typst found." in out


def test_the_python_line_names_the_version_and_file_name_only(env, tmp_path, capsys,
                                                             monkeypatch):
    home, _ = env
    monkeypatch.setattr(sys, "executable", str(home / "tools" / "python3.13"))
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    _, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    version = ".".join(str(p) for p in sys.version_info[:3])
    assert f"Python {version} ran the installer (python3.13)." in out
    assert "tools" not in out


def windows_aliases(local: Path, *packages: str) -> Path:
    """An App Execution Alias layout: top-level aliases plus per-package folders."""
    aliases = local / "Microsoft" / "WindowsApps"
    aliases.mkdir(parents=True)
    (aliases / "python3.exe").write_bytes(b"")
    for package in packages:
        (aliases / package).mkdir()
        (aliases / package / "python3.exe").write_bytes(b"")
    return aliases


def test_the_store_shortcut_is_told_apart_from_the_install_manager(tmp_path):
    store = windows_aliases(tmp_path / "store", install.STORE_ALIAS_PACKAGE)
    assert install.store_python3_only(str(tmp_path / "store"), str(store))
    manager = windows_aliases(tmp_path / "manager", install.STORE_ALIAS_PACKAGE,
                              "PythonSoftwareFoundation.PythonManager_qbz5n2kfra8p0")
    assert not install.store_python3_only(str(tmp_path / "manager"), str(manager))
    uv_bin = tmp_path / "uv-bin"
    uv_bin.mkdir()
    (uv_bin / "python3.exe").write_bytes(b"")
    first = f"{uv_bin}{install.os.pathsep}{store}"
    assert not install.store_python3_only(str(tmp_path / "store"), first), \
        "a real python3 earlier on the PATH answers instead"
    assert not install.store_python3_only(None, str(store))
    assert not install.store_python3_only(str(tmp_path / "nothing"), str(store))


def test_the_store_shortcut_line_appears_only_on_windows(env, tmp_path, monkeypatch):
    home, cwd = env
    aliases = windows_aliases(tmp_path / "local", install.STORE_ALIAS_PACKAGE)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setenv("PATH", str(aliases))
    store_line = "python3 opens only the Microsoft Store; the skills use the Python above."
    assert store_line in install.readiness_lines(home, cwd, windows=True)
    assert store_line not in install.readiness_lines(home, cwd, windows=False)


SENTINEL = "sk-SENTINEL-0000-do-not-print"


def guard_key_files(monkeypatch) -> None:
    """Fail the test if anything opens a key file."""
    real_open = open

    def watched_open(file, *args, **kwargs):
        if str(file).endswith(install.KEY_FILE):
            raise AssertionError("a key file was opened")
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr("builtins.open", watched_open)
    monkeypatch.setattr(install.io, "open", watched_open)
    for name in ("read_text", "read_bytes", "open"):
        real = getattr(Path, name)

        def watched(self, *args, _real=real, **kwargs):
            if self.name == install.KEY_FILE:
                raise AssertionError("a key file was opened")
            return _real(self, *args, **kwargs)

        monkeypatch.setattr(Path, name, watched)


def all_records(*roots: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8") for root in roots
                     for p in root.rglob(install.RECORD_NAME))


def test_key_files_are_reported_present_and_never_read(env, tmp_path, capsys, monkeypatch):
    home, cwd = env
    (cwd / install.KEY_FILE).write_text(f"S2_API_KEY={SENTINEL}\n", encoding="utf-8")
    user_keys = home / install.USER_KEY_DIR / install.KEY_FILE
    user_keys.parent.mkdir(parents=True)
    user_keys.write_text(f"OPENALEX_API_KEY={SENTINEL}\n", encoding="utf-8")
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    guard_key_files(monkeypatch)
    code, out, err = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert ("API keys (optional): an api-keys.env file is in this folder and in "
            "~/.config/thesis-proposal.") in out
    monkeypatch.undo()
    records = all_records(home)
    assert SENTINEL not in out + err + records
    for fact in ("pandoc", "typst", "api-keys", "Microsoft Store", "ran the installer"):
        assert fact not in records, f"readiness fact {fact!r} entered the record"


@pytest.mark.usefixtures("env")
def test_no_key_file_names_both_places(tmp_path, capsys):
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    _, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert ("API keys (optional): no api-keys.env file in this folder or in "
            "~/.config/thesis-proposal.") in out


def test_a_dry_run_ends_with_the_readiness_lines(env, tmp_path, capsys, monkeypatch):
    tool_path(monkeypatch, tmp_path, "pandoc")
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", "all", "--dry-run", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    assert "On this computer:" in out
    assert "pandoc found, typst missing" in out
    assert not (env[0] / ".claude").exists()


def test_a_refused_install_prints_no_readiness_lines(env, tmp_path, capsys):
    copilot_folder(env[0])
    zip_path = str(make_zip(tmp_path / "src.zip", skill_set("proposal-check")))
    code, out, _ = run("--scope", "all", "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_CONFLICT
    assert "On this computer:" not in out


# ---------- a user name and spaces in every path (task 9.6) -------------------


@pytest.mark.parametrize("scope", ["all", "folder"])
def test_a_home_with_a_user_name_and_spaces_never_shows_the_name(tmp_path, monkeypatch, capsys,
                                                                 scope):
    home = tmp_path / "Erika Musterfrau"
    cwd = home / "My Proposals"
    cwd.mkdir(parents=True)
    fake_home(monkeypatch, home)
    monkeypatch.chdir(cwd)
    tool_path(monkeypatch, tmp_path)
    opencode_folder = plant_skill(cwd / ".opencode/skills")
    opencode_user = plant_skill(home / ".config/opencode/skills")
    (cwd / install.KEY_FILE).write_text(f"S2_API_KEY={SENTINEL}\n", encoding="utf-8")
    (home / install.USER_KEY_DIR).mkdir(parents=True)
    (home / install.USER_KEY_DIR / install.KEY_FILE).write_text(SENTINEL, encoding="utf-8")
    skills = skill_set("proposal-check", "proposal-write")
    zip_path = str(make_zip(tmp_path / "src.zip", skills))
    other = "folder" if scope == "all" else "all"
    assert run("--scope", other, "--source", zip_path, capsys=capsys)[0] == 0
    code, out, err = run("--scope", scope, "--source", zip_path, capsys=capsys)
    assert code == install.EXIT_OK
    base = home if scope == "all" else cwd
    for rel in install.SHARED_DIRS:
        for name, files in skills.items():
            assert files_under(base / rel / name) == files
    records = all_records(home)
    prefix = "~/" if scope == "all" else "./"
    assert f'"{prefix}.agents/skills"' in records
    other_prefix = "./" if scope == "all" else "~/"
    assert f"  {other_prefix}.claude/skills/proposal-check" in out, "other-scope listing"
    assert "./.opencode/skills/proposal-check (OpenCode)" in out
    assert "~/.config/opencode/skills/proposal-check (OpenCode)" in out
    assert ("an api-keys.env file is in this folder and in ~/.config/thesis-proposal."
            in out)
    for text in (out, err, records):
        assert "Erika Musterfrau" not in text
        assert "Erika" not in text
        assert SENTINEL not in text
    assert opencode_folder.is_dir()
    assert opencode_user.is_dir()
