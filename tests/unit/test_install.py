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
from helpers import FIXTURES, REPO

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


def isolate(monkeypatch, home: Path) -> None:
    """Every place the installer looks for the user's apps, inside `home`."""
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("APPDATA", str(home / "AppData" / "Roaming"))


@pytest.fixture
def env(tmp_path, monkeypatch):
    """A fake home and a proposal folder inside it, the agent's working directory."""
    home = tmp_path / "home"
    cwd = home / "proposals"
    cwd.mkdir(parents=True)
    isolate(monkeypatch, home)
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
    isolate(monkeypatch, home)
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
    isolate(monkeypatch, home)
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
         str(FIXTURES / "f15-format-broken" / "broken-format.md")],
        capture_output=True, text=True, check=False,
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
