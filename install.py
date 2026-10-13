#!/usr/bin/env python3
"""Install or update the thesis-proposal skills.

Normally run by an AI agent carrying out the install prompt (README, or
docs/install.md), but it works the same by hand:

    python3 install.py --scope all       # for all your projects (recommended)
    python3 install.py --scope folder    # only for the current folder

It fetches the default branch of github.com/hutzelmann/thesis-proposal-skills,
copies every `skills/proposal-*` folder byte-for-byte into the agent skill
directories of the chosen scope, and writes an install record beside them.
Running it again is the update. It runs no skill script and touches nothing
but `proposal-*` folders, its own staging folders, and its own record. Copies
of the skills in the other scope, or in apps' own skill folders it never fills,
are listed, and removed only with --remove-other. The output ends with what the
computer has ready (Python, PDF tools, an API-key file), by presence only.

Exit codes: 0 installed, 1 usage, 2 environment (Python, network, files),
3 refused because another install of the same skills would conflict.

Requires Python >= 3.11, standard library only. It still parses on Python 3.7
and later, so an older interpreter gets a sentence instead of a traceback.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import http.client
import io
import json
import os
import re
import shutil
import ssl
import stat
import subprocess
import sys
import urllib.error
import urllib.request
import zipfile
import zlib
from pathlib import Path, PurePosixPath

MIN_PYTHON = (3, 11)
PACKAGE = "thesis-proposal"
REPO_URL = "https://github.com/hutzelmann/thesis-proposal-skills"
DEFAULT_SOURCE = (
    "https://codeload.github.com/hutzelmann/thesis-proposal-skills/zip/refs/heads/main"
)
RECORD_NAME = ".thesis-proposal-install.json"
RECORD_FORMAT = 1
SKILL_FILE = "SKILL.md"
TIMEOUT = 60
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
# The only names the installer ever creates, replaces or removes. A name read
# from an archive or from an existing record is used as a path only when it
# matches: a record lies in the folder the student opened, which may have come
# from anywhere, and "proposal-x/../.." must never reach shutil.rmtree.
SKILL_NAME_RE = re.compile(r"proposal-[a-z0-9][a-z0-9-]*")
LEFTOVER_RE = re.compile(r"\.(proposal-[a-z0-9][a-z0-9-]*)\.(?:new|old)-\d+")

EXIT_OK, EXIT_USAGE, EXIT_ENV, EXIT_CONFLICT = 0, 1, 2, 3

# Where agents look for skills. Two shared directories cover most agents: the
# cross-agent `.agents/skills` (ChatGPT/Codex, VS Code and the Copilot app,
# Cursor, Gemini CLI, OpenCode, Cline, Zed and others) and Claude's own
# `.claude/skills`, which Claude reads instead of the cross-agent one.
SHARED_DIRS = (".agents/skills", ".claude/skills")


class HostDir:
    """An app that reads neither shared directory. Its directory is written only
    when the app is present (one of its own directories exists), so nobody's
    home gains folders for apps they never installed. `folder_dir` is None when
    the app reads the shared `.agents/skills` inside a project."""

    def __init__(self, app: str, markers: tuple[str, ...], user_dir: str,
                 folder_dir: str | None) -> None:
        self.app = app
        self.markers = markers
        self.user_dir = user_dir
        self.folder_dir = folder_dir

    def present(self, home: Path) -> bool:
        return any((home / marker).is_dir() for marker in self.markers)


# Pinned 2026-10-03 from the apps' own documentation (antigravity.google/docs/skills,
# kiro.dev/docs/skills). Antigravity ignores ~/.agents/skills at user level.
HOST_DIRS = (
    HostDir("Antigravity", (".gemini/antigravity", ".antigravity"),
            ".gemini/config/skills", None),
    HostDir("Antigravity CLI", (".gemini/antigravity-cli",),
            ".gemini/antigravity-cli/skills", None),
    HostDir("Kiro", (".kiro",), ".kiro/skills", ".kiro/skills"),
)

# Skill folders that apps read but this installer never fills (design D3 and
# D14): a copy of a shipped skill there, made by hand or by an older tool, can be
# loaded instead of the installed one, or beside it. Listed on every run, removed
# only with --remove-other. (app, base, folder): base is "home" or "folder", the
# working folder. Checked 2026-10-13:
# - OpenCode: anomalyco/opencode dev c1615b1db9c2e7a955f2be1024e84bb74c90cc6b.
#   packages/core/src/config/plugin/skill.ts loads skill/ and skills/ under
#   .opencode and ~/.config/opencode, after the .claude and .agents folders
#   (plugin/internal.ts:265-266), and the last copy of a name wins
#   (skill.ts:100-101). OpenCode also reads .opencode in parent folders up to the
#   git root; only the working folder is checked here.
# - Codex: openai/codex 90f00bd, codex-rs/ext/skills/src/host_roots.rs:96, the
#   deprecated $CODEX_HOME/skills, still read.
# - Cursor: cursor.com/docs/context/skills, ~/.cursor/skills.
# - GitHub Copilot: docs.github.com, "About agent skills", ~/.copilot/skills.
# The troubleshooting collector restates this table; an offline test keeps the
# two equal.
NATIVE_DIRS = (
    ("OpenCode", "folder", ".opencode/skill"),
    ("OpenCode", "folder", ".opencode/skills"),
    ("OpenCode", "home", ".config/opencode/skill"),
    ("OpenCode", "home", ".config/opencode/skills"),
    ("Codex", "home", ".codex/skills"),
    ("Cursor", "home", ".cursor/skills"),
    ("GitHub Copilot", "home", ".copilot/skills"),
)

# A plugin install of the same skills next to copied ones loads every skill
# twice, so the installer refuses when it sees one. Each app records its plugin
# installs differently; cache folders alone are no evidence (Claude keeps an
# uninstalled plugin's cache for two weeks). Paths are home-relative.
PLUGIN_ID = f"{PACKAGE}@{PACKAGE}"
PLUGIN_MARK = f'"{PACKAGE}@'  # an installed plugin id, from any marketplace
PLUGIN_RECORDS = (  # (app, file that names installed or enabled plugins)
    ("Claude", ".claude/plugins/installed_plugins.json"),
    ("Claude", ".claude/settings.json"),
    ("ChatGPT/Codex", ".codex/config.toml"),
)
PLUGIN_FOLDERS = (  # (app, folder that exists only while the plugin is installed)
    ("GitHub Copilot", f".copilot/installed-plugins/{PACKAGE}/{PACKAGE}"),
)
# plugins added with Claude's plugin button arrive in Claude Code sessions here,
# with no entry in installed_plugins.json
CLAUDE_SYNCED = ".claude/plugins/synced"
VSCODE_PLUGIN = "agentPlugins/github.com/hutzelmann/thesis-proposal-skills"

# The base system's certificate bundle on macOS, which python.org's builds do not
# use until "Install Certificates.command" has run. Absent elsewhere, harmlessly.
SYSTEM_CA_FILE = "/etc/ssl/cert.pem"
CERT_NOTICE = (
    "Note: this Python could not check the website's certificate by itself, so the "
    "skills' literature search will run into the same problem. On macOS, open "
    "Applications > Python 3.x and double-click Install Certificates.command once."
)
# messages for the end of the report, collected while running
NOTICES: list[str] = []

# Readiness lines (design D15): presence only. Nothing named here is run or
# opened, and none of it enters the install record.
PDF_TOOLS = ("pandoc", "typst")
KEY_FILE = "api-keys.env"
USER_KEY_DIR = ".config/thesis-proposal"  # the user-level key location the skills consult
# On Windows, the App Installer package owns the python/python3 App Execution
# Aliases that only open the Microsoft Store; the Python install manager's own
# aliases sit in a PythonSoftwareFoundation.* package folder beside it (pinned
# 2026-10-13, task 9.1 of desktop-first-install; confirmed live by task 8.7).
STORE_ALIAS_PACKAGE = "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe"
PYTHON_ALIAS_PACKAGES = "PythonSoftwareFoundation.*"


class UsageError(Exception):
    pass


class EnvironmentProblem(Exception):
    pass


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # exit code 1, not argparse's 2
        raise UsageError(message)


def valid_name(name: object) -> bool:
    return isinstance(name, str) and SKILL_NAME_RE.fullmatch(name) is not None


# --------------------------------------------------------------------------
# the source: a revision archive or a local copy of the repository
# --------------------------------------------------------------------------

class Source:
    """Every shipped skill's files as bytes, plus where they came from."""

    def __init__(self, kind: str, revision: str, skills: dict[str, dict[str, tuple[bytes, int]]]):
        self.kind = kind
        self.revision = revision
        self.skills = skills

    @property
    def names(self) -> list[str]:
        return sorted(self.skills)


def _download(url: str, context: ssl.SSLContext | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": f"{PACKAGE}-installer"})
    with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as response:
        return response.read()


def _certificate_problem(exc: BaseException) -> bool:
    return isinstance(getattr(exc, "reason", None), ssl.SSLCertVerificationError)


def fetch(url: str) -> bytes:
    """Download with Python's own certificates; on a certificate failure, retry
    with the system bundle, then with the system curl, before giving up."""
    try:
        return _download(url)
    except urllib.error.URLError as exc:
        if not _certificate_problem(exc):
            raise EnvironmentProblem(
                f"could not download the skills from {url}: {exc.reason}. Check the internet "
                "connection, or whether the agent needs permission to access the network."
            ) from exc
    except (OSError, http.client.HTTPException) as exc:
        raise EnvironmentProblem(
            f"the download from {url} broke off ({exc.__class__.__name__}); run the "
            "installer again"
        ) from exc
    NOTICES.append(CERT_NOTICE)
    if Path(SYSTEM_CA_FILE).is_file():
        try:
            return _download(url, ssl.create_default_context(cafile=SYSTEM_CA_FILE))
        except (OSError, http.client.HTTPException):
            pass
    return fetch_with_curl(url)


def curl_candidates(windows: bool) -> list[str]:
    """curl's fixed system locations. Never a PATH search: on Windows that looks
    in the current folder first, and the installer runs in the student's folder."""
    if windows:
        root = os.environ.get("SYSTEMROOT", r"C:\Windows").rstrip("\\/")
        return [root + r"\System32\curl.exe"]
    return ["/usr/bin/curl", "/bin/curl"]


def system_curl() -> str | None:
    return next((c for c in curl_candidates(os.name == "nt") if Path(c).is_file()), None)


def fetch_with_curl(url: str) -> bytes:
    curl = system_curl()
    if curl is None:
        raise EnvironmentProblem(
            "this Python cannot verify https certificates and no curl was found. "
            "On macOS, run 'Install Certificates.command' in your Python folder "
            "(Applications > Python 3.x), then try again."
        )
    try:
        done = subprocess.run(
            [curl, "--fail", "--silent", "--show-error", "--location", "--proto", "=https", url],
            capture_output=True, check=False, timeout=TIMEOUT * 2,
        )
    except subprocess.TimeoutExpired as exc:
        raise EnvironmentProblem(f"the download from {url} timed out; run the installer "
                                 "again") from exc
    if done.returncode != 0:
        raise EnvironmentProblem(
            f"could not download the skills from {url}: "
            f"{done.stderr.decode(errors='replace').strip()}"
        )
    return done.stdout


def _skill_member(parts: tuple[str, ...]) -> tuple[str, str] | None:
    """(skill name, path inside the skill) for an archive member under a
    `skills/proposal-*/` folder at the archive root or one level below it.
    Neither part may leave its folder: no traversal, separators or drives."""
    for depth in (0, 1):
        if len(parts) > depth + 2 and parts[depth] == "skills" \
                and valid_name(parts[depth + 1]):
            inner = parts[depth + 2:]
            if any(part in ("", ".", "..") or "\\" in part or ":" in part for part in inner):
                return None
            return parts[depth + 1], "/".join(inner)
    return None


def read_zip(payload: bytes, kind: str) -> Source:
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
        comment = archive.comment.decode("ascii", errors="replace").strip()
        skills: dict[str, dict[str, tuple[bytes, int]]] = {}
        for info in archive.infolist():
            found = None if info.is_dir() else _skill_member(PurePosixPath(info.filename).parts)
            if found is None:
                continue
            name, inner = found
            mode = (info.external_attr >> 16) & 0o777
            skills.setdefault(name, {})[inner] = (archive.read(info), mode)
    except (zipfile.BadZipFile, zlib.error, EOFError) as exc:
        raise EnvironmentProblem("the download is damaged; run the installer again") from exc
    return Source(kind, comment if SHA_RE.match(comment) else "unknown", skills)


def read_directory(root: Path) -> Source:
    base = root / "skills" if (root / "skills").is_dir() else root
    skills: dict[str, dict[str, tuple[bytes, int]]] = {}
    for skill_dir in sorted(base.iterdir()):
        if not (skill_dir.is_dir() and valid_name(skill_dir.name)):
            continue
        files: dict[str, tuple[bytes, int]] = {}
        for path in sorted(skill_dir.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                inner = path.relative_to(skill_dir).as_posix()
                files[inner] = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        skills[skill_dir.name] = files
    return Source("directory", "unknown", skills)


def load_source(spec: str | None) -> Source:
    if spec is None:
        source = read_zip(fetch(DEFAULT_SOURCE), "default-branch")
    elif spec.startswith(("https://", "http://")):
        source = read_zip(fetch(spec), "url")
    else:
        path = Path(spec).expanduser()
        if path.is_dir():
            source = read_directory(path)
        elif path.is_file():
            source = read_zip(path.read_bytes(), "zip")
        else:
            raise EnvironmentProblem(f"source not found: {spec}")
    incomplete = [name for name, files in source.skills.items() if SKILL_FILE not in files]
    if not source.skills or incomplete:
        raise EnvironmentProblem(
            "the source holds no complete skills"
            + (f" (missing {SKILL_FILE}: {', '.join(sorted(incomplete))})" if incomplete else "")
        )
    return source


# --------------------------------------------------------------------------
# where the skills go
# --------------------------------------------------------------------------

def same_place(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return a == b


def effective_scope(scope: str, home: Path, cwd: Path) -> str:
    """A folder install in the home folder is an install for all projects."""
    if scope == "folder" and same_place(cwd, home):
        NOTICES.append("The folder that is open is your home folder, so the skills were "
                       "installed for all your projects.")
        return "all"
    return scope


def target_dirs(scope: str, home: Path, cwd: Path) -> list[Path]:
    base = home if scope == "all" else cwd
    dirs = [base / rel for rel in SHARED_DIRS]
    for host in HOST_DIRS:
        rel = host.user_dir if scope == "all" else host.folder_dir
        if rel is not None and host.present(home) and base / rel not in dirs:
            dirs.append(base / rel)
    return dirs


def display(path: Path, home: Path, cwd: Path) -> str:
    """Home- or folder-relative, so no user name ends up in the output or the
    record. The more specific base wins, and the home on a tie, so a working
    folder that is the home folder, or lies above it, never shows a user name."""
    candidates = []
    for base, label in ((home, "~"), (cwd, ".")):
        try:
            rel = path.relative_to(base)
        except ValueError:
            continue
        candidates.append((len(base.parts), label == "~", label, rel))
    if not candidates:
        return path.as_posix()
    _, _, label, rel = max(candidates)
    return f"{label}/{rel.as_posix()}" if rel.parts else label


def vscode_dirs(home: Path) -> list[Path]:
    """VS Code's user-data folder on each platform."""
    dirs = [home / "Library" / "Application Support" / "Code", home / ".config" / "Code"]
    if os.environ.get("APPDATA"):
        dirs.append(Path(os.environ["APPDATA"]) / "Code")
    return dirs


def plugin_install(home: Path) -> str | None:
    """The app that has this package installed as a plugin, if any."""
    for app, rel in PLUGIN_RECORDS:
        try:
            if PLUGIN_MARK in (home / rel).read_text(encoding="utf-8", errors="replace"):
                return app
        except OSError:
            continue
    for app, rel in PLUGIN_FOLDERS:
        if (home / rel).is_dir():
            return app
    synced = home / CLAUDE_SYNCED
    if synced.is_dir() and any(p.is_dir() for p in synced.glob(f"**/{PACKAGE}")):
        return "Claude"
    if any((base / VSCODE_PLUGIN).is_dir() for base in vscode_dirs(home)):
        return "VS Code"
    return None


def read_record(directory: Path) -> dict | None:
    record = directory / RECORD_NAME
    if not record.is_file():
        return None
    try:
        data = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def recorded_skills(record: dict | None) -> list[str]:
    """The skill names a record lists, keeping only names the installer could
    have written itself."""
    names = (record or {}).get("skills")
    return [n for n in names if valid_name(n)] if isinstance(names, list) else []


def recorded_revision(record: dict | None) -> str:
    revision = (record or {}).get("revision")
    return revision if isinstance(revision, str) and (
        SHA_RE.match(revision) or revision == "unknown") else "unknown"


def is_link(path: Path) -> bool:
    """A symlink, or a Windows directory junction: the skills CLI links agent
    folders with junctions there, and is_symlink() misses them before 3.12."""
    if path.is_symlink():
        return True
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction is not None and isjunction(path):
        return True
    if os.name == "nt":
        try:
            attributes = os.lstat(path).st_file_attributes
        except (OSError, AttributeError):
            return False
        return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return False


def present(path: Path) -> bool:
    return path.exists() or is_link(path)


def copies_in(directory: Path, names: list[str]) -> list[Path]:
    """Installed copies of this package in a directory: shipped names, and
    anything an earlier record says was installed there."""
    known = set(names) | set(recorded_skills(read_record(directory)))
    return [directory / n for n in sorted(known) if present(directory / n)]


def other_copies(scope: str, home: Path, cwd: Path, targets: list[Path],
                 names: list[str]) -> list[Path]:
    other = "folder" if scope == "all" else "all"
    return [copy for d in target_dirs(other, home, cwd)
            if not any(same_place(d, t) for t in targets)
            for copy in copies_in(d, names)]


def terminal_lock(home: Path, cwd: Path) -> bool:
    """Whether the skills CLI (npx skills) recorded an earlier install."""
    return any(p.is_file() for p in (cwd / "skills-lock.json", home / ".agents/.skill-lock.json"))


def inside(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory.resolve())
    except (ValueError, OSError):
        return False
    return True


def native_copy(entry: Path, targets: list[Path]) -> bool:
    """Whether an entry in an app's own skill folder is a copy of a skill: a real
    folder holding its SKILL.md, or a link to one elsewhere. A link (or a linked
    parent folder) that resolves into a directory this run fills is the installed
    copy itself, not a second one."""
    if not present(entry):
        return False
    try:
        resolved = entry.resolve()
    except (OSError, RuntimeError):
        return False
    if any(inside(resolved, t) for t in targets):
        return False
    return (resolved / SKILL_FILE).is_file()


def through_linked_folder(entry: Path, base: Path) -> bool:
    """Whether a folder between the base and the entry is a link or junction, as
    when ~/.codex/skills links to a dotfiles folder: removing the entry would then
    delete files at the link's target, outside the listed folder."""
    folder = entry.parent
    while folder != base and folder != folder.parent:
        if is_link(folder):
            return True
        folder = folder.parent
    return False


def native_copies(home: Path, cwd: Path, targets: list[Path],
                  names: list[str]) -> list[tuple[str, Path, bool]]:
    """(app, entry, linked) for each shipped skill found in an app's own skill
    folder; linked is True when the folder is reached through a link, and such a
    copy is listed but never removed."""
    found: list[tuple[str, Path, bool]] = []
    for app, base, rel in NATIVE_DIRS:
        root = home if base == "home" else cwd
        for name in names:
            entry = root / rel / name
            if entry not in [p for _, p, _ in found] and native_copy(entry, targets):
                found.append((app, entry, through_linked_folder(entry, root)))
    return found


# --------------------------------------------------------------------------
# writing
# --------------------------------------------------------------------------

def remove_entry(path: Path) -> None:
    """Remove a file, a folder, or a link, never following a link into its target."""
    if is_link(path):
        if os.name == "nt" and (path.is_dir() or not path.exists()):
            path.rmdir()  # a junction or directory symlink, dangling or not
        else:
            path.unlink()
    elif path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def remove_quietly(path: Path) -> None:
    # a locked leftover is swept by the next run
    with contextlib.suppress(OSError):
        remove_entry(path)


def sweep_leftovers(directory: Path) -> None:
    """Staging and set-aside copies an interrupted earlier run left behind."""
    for entry in directory.iterdir():
        if LEFTOVER_RE.fullmatch(entry.name):
            remove_quietly(entry)


def write_skill(directory: Path, name: str, files: dict[str, tuple[bytes, int]]) -> None:
    """Stage the new copy beside the old one, then swap, so an interrupted run
    leaves either the previous copy or the new one, never half of each."""
    staging = directory / f".{name}.new-{os.getpid()}"
    aside = directory / f".{name}.old-{os.getpid()}"
    remove_entry(staging)
    remove_entry(aside)
    for inner, (payload, mode) in files.items():
        target = staging.joinpath(*inner.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        if mode and os.name != "nt":
            target.chmod(mode | stat.S_IRUSR | stat.S_IWUSR)
    live = directory / name
    had_live = present(live)
    if had_live:
        live.rename(aside)
    try:
        staging.rename(live)
    except OSError:
        if had_live and not present(live):
            aside.rename(live)
        remove_quietly(staging)
        raise
    remove_quietly(aside)


def install_into(directory: Path, source: Source, previous: dict | None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    sweep_leftovers(directory)
    for name in source.names:
        write_skill(directory, name, source.skills[name])
    # skills an earlier run installed here that upstream has since retired
    for old in recorded_skills(previous):
        if old not in source.skills:
            remove_entry(directory / old)


def write_record(directory: Path, record: dict) -> None:
    (directory / RECORD_NAME).write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def remove_copies(directory: Path, names: list[str]) -> None:
    for path in copies_in(directory, names):
        remove_entry(path)
    (directory / RECORD_NAME).unlink(missing_ok=True)


# --------------------------------------------------------------------------
# what the computer has ready: presence only, nothing is run or opened
# --------------------------------------------------------------------------

def store_python3_only(local_app_data: str | None, search_path: str | None) -> bool:
    """Whether `python3` on this Windows PATH is only the App Installer's alias
    that opens the Microsoft Store. Read from the alias folders without running
    anything; callable on any system, so the offline tests can plant a layout."""
    if not local_app_data:
        return False
    aliases = Path(local_app_data) / "Microsoft" / "WindowsApps"
    if not os.path.lexists(aliases / STORE_ALIAS_PACKAGE / "python3.exe"):
        return False
    if any(os.path.lexists(p / "python3.exe") for p in aliases.glob(PYTHON_ALIAS_PACKAGES)):
        return False  # the Python install manager (or a Store Python) answers instead
    for folder in (search_path or "").split(os.pathsep):
        folder = folder.strip().strip('"')
        if folder and os.path.lexists(Path(folder) / "python3.exe"):
            return same_place(Path(folder), aliases)
    return False


def readiness_lines(home: Path, cwd: Path, windows: bool) -> list[str]:
    version = ".".join(str(part) for part in sys.version_info[:3])
    executable = Path(sys.executable).name or "python"  # never the full path
    lines = [f"Python {version} ran the installer ({executable})."]
    if windows and store_python3_only(os.environ.get("LOCALAPPDATA"), os.environ.get("PATH")):
        lines.append("python3 opens only the Microsoft Store; the skills use the Python above.")
    found_tools = [tool for tool in PDF_TOOLS if shutil.which(tool)]
    tools = ", ".join(tool + (" found" if tool in found_tools else " missing")
                      for tool in PDF_TOOLS)
    missing = "" if len(found_tools) == len(PDF_TOOLS) else (
        " Only PDF export needs them; the publish skill says what to install when you first "
        "ask for a PDF.")
    lines.append(f"PDF export (optional): {tools}.{missing}")
    key_places = [("this folder", cwd / KEY_FILE),
                  (display(home / USER_KEY_DIR, home, cwd), home / USER_KEY_DIR / KEY_FILE)]
    found = [label for label, path in key_places if path.is_file()]
    if found:
        lines.append(f"API keys (optional): an {KEY_FILE} file is in " + " and in ".join(found)
                     + ".")
    else:
        lines.append(f"API keys (optional): no {KEY_FILE} file in "
                     + " or in ".join(label for label, _ in key_places) + ".")
    return lines


def report_readiness(home: Path, cwd: Path) -> None:
    lines = readiness_lines(home, cwd, os.name == "nt")
    print("On this computer:\n" + "\n".join(f"  {line}" for line in lines))


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = _Parser(description="Install or update the thesis-proposal skills.")
    parser.add_argument("--scope", choices=("all", "folder"),
                        help="all = for all your projects; folder = only the current folder")
    parser.add_argument("--remove-other", action="store_true",
                        help="also remove copies installed earlier in the other scope, "
                        "and copies of these skills in other apps' own skill folders")
    parser.add_argument("--source", help="install from this URL, zip file or directory "
                        "instead of the default branch (for testing)")
    parser.add_argument("--dry-run", action="store_true",
                        help="show what would happen and write nothing")
    args = parser.parse_args(argv)
    if args.scope is None:
        raise UsageError(
            "choose where to install: --scope all (for all your projects, recommended) "
            "or --scope folder (only the current folder)"
        )
    return args


def short(revision: str) -> str:
    return revision[:7] if SHA_RE.match(revision) else revision


class Plan:
    """What one run installs, and the copies it found elsewhere."""

    def __init__(self, args: argparse.Namespace, home: Path, cwd: Path) -> None:
        self.home, self.cwd = home, cwd
        self.remove_other = args.remove_other
        self.scope = effective_scope(args.scope, home, cwd)
        self.targets = target_dirs(self.scope, home, cwd)
        self.source = load_source(args.source)
        names = self.source.names
        self.others = other_copies(self.scope, home, cwd, self.targets, names)
        self.native = native_copies(home, cwd, self.targets, names)

    def show(self, path: Path) -> str:
        return display(path, self.home, self.cwd)

    @property
    def shown(self) -> list[str]:
        return [self.show(d) for d in self.targets]

    def native_listing(self, separator: str, linked: bool | None = None) -> str:
        """The copies in apps' own folders; only those reached through a linked
        folder (True), only the others (False), or all of them (None)."""
        return separator.join(f"{self.show(p)} ({app})" for app, p, through in self.native
                              if linked is None or through == linked)

    @property
    def native_removable(self) -> list[Path]:
        return [p for _, p, through in self.native if not through]

    @property
    def native_linked(self) -> bool:
        return any(through for _, _, through in self.native)


def report_copies(plan: Plan) -> None:
    """Copies the run did not install: in the other scope's directories, and in
    apps' own skill folders. Kept, unless --remove-other was given."""
    removed = plan.remove_other
    if plan.others:
        listed = "\n".join(f"  {plan.show(p)}" for p in plan.others)
        print(("Removed the earlier copies in the other scope:\n" if removed else
               "Earlier copies in the other scope are still there, so your agent may see two "
               "versions:\n") + listed)
    if plan.native and not removed:
        print("Copies in other apps' own skill folders are still there, and those apps may "
              "load them instead of the installed skills:\n  " + plan.native_listing("\n  "))
    if removed and plan.native_removable:
        print("Removed the copies in other apps' own skill folders:\n  "
              + plan.native_listing("\n  ", linked=False))
    if removed and plan.native_linked:
        print("Kept these copies in other apps' own skill folders, because the folder is "
              "reached through a link and removing them would delete files where the link "
              "points. Those apps may load them instead of the installed skills; remove "
              "them by hand if they are copies:\n  "
              + plan.native_listing("\n  ", linked=True))
    if removed:
        return
    print("To remove them, run this installer again with --remove-other added.")
    if plan.others and terminal_lock(plan.home, plan.cwd):
        print("They were installed earlier from a terminal (npx skills); its lock file is "
              "left as it is, and `npx skills remove` tidies it up.")


def report_dry_run(plan: Plan) -> None:
    action = "remove" if plan.remove_other else "keep"
    print(f"Would install {len(plan.source.names)} skills (revision "
          f"{short(plan.source.revision)}) into:")
    print("\n".join(f"  {s}" for s in plan.shown))
    if plan.others:
        print(f"Would {action} copies in the other scope: "
              + ", ".join(plan.show(p) for p in plan.others))
    if plan.native and not plan.remove_other:
        print("Would keep copies in other apps' own skill folders: "
              + plan.native_listing(", "))
    if plan.remove_other and plan.native_removable:
        print("Would remove copies in other apps' own skill folders: "
              + plan.native_listing(", ", linked=False))
    if plan.remove_other and plan.native_linked:
        print("Would keep copies in other apps' own skill folders that are reached through "
              "a linked folder: " + plan.native_listing(", ", linked=True))


def run(args: argparse.Namespace, home: Path, cwd: Path) -> int:
    NOTICES.clear()
    app = plugin_install(home)
    if app is not None:
        print(f"Not installed: the skills are already installed as the {PACKAGE} plugin "
              f"in {app}. Update them from the app's plugin page (Check for updates), or "
              "remove the plugin first if you want this installer to manage them instead. "
              "Having both loads every skill twice.")
        return EXIT_CONFLICT
    plan = Plan(args, home, cwd)
    if args.dry_run:
        report_dry_run(plan)
    else:
        install(plan)
    report_readiness(home, cwd)
    return EXIT_OK


def install(plan: Plan) -> None:
    scope, targets, source, shown = plan.scope, plan.targets, plan.source, plan.shown
    previous = next((r for r in map(read_record, targets) if r), None)
    record = {
        "package": PACKAGE,
        "installer": RECORD_FORMAT,
        "revision": source.revision,
        "installed_at": datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat(),
        "scope": scope,
        "source": source.kind,
        "directories": shown,
        "skills": source.names,
    }
    for directory in targets:
        install_into(directory, source, read_record(directory))
        write_record(directory, record)
    if plan.remove_other:
        for directory in {p.parent for p in plan.others}:
            remove_copies(directory, source.names)
        for entry in plan.native_removable:
            remove_entry(entry)  # a link goes as a link; its target stays

    was = short(recorded_revision(previous)) if previous else "not installed"
    print(f"Installed {len(source.names)} thesis-proposal skills, revision "
          f"{short(source.revision)} (before: {was}), for "
          + ("all your projects" if scope == "all" else "this folder only") + ":")
    print("\n".join(f"  {s}" for s in shown))
    if plan.others or plan.native:
        report_copies(plan)
    for notice in NOTICES:
        print(notice)
    print("Next: start a new chat (or reload skills, if your app has that) so your agent "
          "picks up the skills.")


def main(argv: list[str] | None = None) -> int:
    if sys.version_info < MIN_PYTHON:
        print(f"This installer needs Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer; this is "
              f"{sys.version_info[0]}.{sys.version_info[1]}. Install a current Python from "
              "https://www.python.org/downloads/ and run it again.", file=sys.stderr)
        return EXIT_ENV
    try:
        args = parse_args(argv)
    except UsageError as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    home, cwd = Path.home(), Path.cwd()
    try:
        return run(args, home, cwd)
    except EnvironmentProblem as exc:
        print(f"Not installed: {exc}", file=sys.stderr)
        return EXIT_ENV
    except OSError as exc:
        where = display(Path(exc.filename), home, cwd) if exc.filename else "a file"
        print(f"Not installed: could not write {where}: {exc.strerror or exc}. Check that "
              "the folder is writable, or that the agent may write there.", file=sys.stderr)
        return EXIT_ENV


if __name__ == "__main__":
    sys.exit(main())
