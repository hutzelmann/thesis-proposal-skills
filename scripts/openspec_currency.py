#!/usr/bin/env python3
"""OpenSpec currency: the spec gate's pin against npm's latest release.

testing-harness spec, "OpenSpec version kept current". Compares the pin in
`scripts/validate_specs.py` with the `latest` version npm publishes for the
OpenSpec package, the URL OpenSpec's own update check reads. It also reads the
local `openspec --version` and the `generatedBy` stamp of the agent skills
OpenSpec generated under `.claude/skills/`. Either one differing from the pin
prints a warning naming the action that brings it in line, and neither changes
the exit status. An absent CLI or absent skills, as on a CI runner, are noted.

Standard library only, so CI runs it with plain `python3`; no key, no credential.

Usage:
    uv run poe openspec-currency                      # human-readable report
    python3 scripts/openspec_currency.py --json
    python3 scripts/openspec_currency.py --write --json --pr-body body.md   # the weekly bump

Exit status: 0 the pin is current (or ahead of npm, with a warning), 1 the pin
is behind (the write mode then rewrites the pin line and nothing else),
2 currency unknown (the registry could not be read or gave no usable version;
nothing written), 3 the pin line could not be read or written (nothing written).
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import validate_specs

REPO = validate_specs.REPO
PIN_FILE = Path("scripts") / "validate_specs.py"
SKILLS_GLOB = ".claude/skills/openspec-*/SKILL.md"
REGISTRY_URL = f"https://registry.npmjs.org/{validate_specs.PACKAGE}/latest"
RELEASES_URL = "https://github.com/Fission-AI/OpenSpec/releases"
TIMEOUT = 30.0

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
# the line is read and written byte for byte: a Windows checkout keeps its CRLF
_PIN_RE = re.compile(r'^OPENSPEC_VERSION = "([^"\r\n]*)"(?=\r?$)', re.MULTILINE)
_PIN_ASSIGN_RE = re.compile(r"^OPENSPEC_VERSION = ", re.MULTILINE)
# the line OpenSpec writes into a generated skill's frontmatter (`generatedBy:
# "X.Y.Z"` under `metadata:`), read narrowly: AGENTS.md admits no general YAML parsing
_STAMP_RE = re.compile(r"""^[ \t]*generatedBy:[ \t]*["']?([^"'\n]+?)["']?[ \t]*$""", re.MULTILINE)

Fetch = Callable[[str, float], object]


class CurrencyUnknown(Exception):
    """The registry could not be read, or its answer carries no usable version."""


@dataclass(frozen=True)
class Report:
    pin: str
    latest: str
    status: str  # current | behind | ahead
    local_cli: str | None
    skills_stamps: dict[str, str | None]
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.status == "behind" else 0


# ---------- sources ---------------------------------------------------------------------


def fetch_json(url: str, timeout: float) -> object:
    """The one network call: an unauthenticated GET of the public registry."""
    request = urllib.request.Request(url, headers={"User-Agent": "thesis-proposal-skills"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def version_tuple(version: str) -> tuple[int, int, int] | None:
    match = _VERSION_RE.match(version)
    return tuple(int(n) for n in match.groups()) if match else None


def latest_version() -> str:
    try:
        answer = fetch_json(REGISTRY_URL, TIMEOUT)
    # URLError and JSONDecodeError included; a truncated body (IncompleteRead)
    # is an HTTPException, which is neither
    except (OSError, ValueError, http.client.HTTPException) as exc:
        raise CurrencyUnknown(f"{REGISTRY_URL}: {exc}") from exc
    if not isinstance(answer, dict) or answer.get("name") != validate_specs.PACKAGE:
        raise CurrencyUnknown(f"{REGISTRY_URL} did not answer for {validate_specs.PACKAGE}")
    version = answer.get("version")
    if not isinstance(version, str) or version_tuple(version) is None:
        raise CurrencyUnknown(f"{REGISTRY_URL} gave no plain X.Y.Z version: {version!r}")
    return version


def local_cli_version() -> str | None:
    """`openspec --version` of the CLI on PATH, or None when there is none to ask."""
    binary = shutil.which("openspec")
    if binary is None:
        return None
    try:
        proc = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, encoding="utf-8",
            check=False, timeout=TIMEOUT, env={**os.environ, **validate_specs.CLI_ENV},
        )
    except (OSError, subprocess.SubprocessError):
        return None
    version = proc.stdout.strip()
    return version if proc.returncode == 0 and version_tuple(version) else None


def skills_stamps(root: Path) -> dict[str, str | None]:
    """Each generated OpenSpec skill's `generatedBy` stamp, None where it has none."""
    stamps: dict[str, str | None] = {}
    for skill_md in sorted(root.glob(SKILLS_GLOB)):
        match = _STAMP_RE.search(skill_md.read_text(encoding="utf-8"))
        stamps[skill_md.parent.name] = match.group(1).strip() if match else None
    return stamps


def read_pin(text: str) -> str:
    """The pinned version in the gate's source; ValueError unless exactly one
    plain `OPENSPEC_VERSION = "X.Y.Z"` line exists."""
    pins = _PIN_RE.findall(text)
    if len(_PIN_ASSIGN_RE.findall(text)) != 1 or len(pins) != 1 or not version_tuple(pins[0]):
        raise ValueError(f'expected exactly one line `OPENSPEC_VERSION = "X.Y.Z"` in {PIN_FILE}')
    return pins[0]


def set_pin(text: str, version: str) -> str:
    read_pin(text)
    return _PIN_RE.sub(f'OPENSPEC_VERSION = "{version}"', text, count=1)


# ---------- the assessment ------------------------------------------------------------------


def _status(pin: str, latest: str) -> str:
    ours, theirs = version_tuple(pin), version_tuple(latest)
    if ours == theirs:
        return "current"
    return "behind" if ours < theirs else "ahead"


def _stamp_warnings(pin: str, stamps: dict[str, str | None]) -> list[str]:
    off: dict[str | None, list[str]] = {}
    for skill, stamp in stamps.items():
        if stamp != pin:
            off.setdefault(stamp, []).append(skill)
    found = []
    for stamp, skills in sorted(off.items(), key=lambda kv: str(kv[0])):
        what = f"were generated by {stamp}" if stamp else "carry no generatedBy stamp"
        found.append(f"{len(skills)} OpenSpec skill(s) in .claude/skills {what} "
                     f"({', '.join(skills)}), the pin is {pin}: regenerate them with "
                     f"`openspec update` once the local CLI is at {pin}")
    return found


def assess(pin: str, latest: str, local_cli: str | None,
           stamps: dict[str, str | None]) -> Report:
    status = _status(pin, latest)
    warnings: list[str] = []
    notes: list[str] = []
    if status == "ahead":
        warnings.append(f"the pin {pin} is newer than npm's latest {latest}: check whether "
                        f"{pin} was withdrawn ({RELEASES_URL})")
    if local_cli is None:
        notes.append("no local openspec CLI reported a version")
    elif local_cli != pin:
        warnings.append(f"the local openspec CLI is {local_cli}, the pin is {pin}: update the "
                        f"openspec package to {pin}")
    if stamps:
        warnings += _stamp_warnings(pin, stamps)
    else:
        notes.append(f"no generated OpenSpec skills ({SKILLS_GLOB})")
    return Report(pin, latest, status, local_cli, stamps, warnings, notes)


# ---------- output ----------------------------------------------------------------------------


def render_text(report: Report) -> str:
    lines = [f"OpenSpec pin {report.pin}, npm latest {report.latest}: {report.status}"]
    lines += [f"warning: {w}" for w in report.warnings]
    lines += [f"note: {n}" for n in report.notes]
    return "\n".join(lines)


def render_json(report: Report, written: bool) -> dict:
    return {**asdict(report), "package": validate_specs.PACKAGE, "written": written,
            "source": REGISTRY_URL,
            "fetched_at": datetime.now(UTC).isoformat(timespec="seconds")}


def render_pr_body(report: Report) -> str:
    return "\n".join([
        "## OpenSpec currency",
        "",
        f"npm's latest OpenSpec is `{report.latest}`; the spec gate pins `{report.pin}`. "
        f"This pull request moves the pin in `{PIN_FILE.as_posix()}` and changes nothing "
        f"else. Release notes: {RELEASES_URL}",
        "",
        f"- CI on this branch runs `uv run poe specs` with `{report.latest}`. If it fails, the "
        "new version reports something the pinned one did not: fix the specs, or, for a "
        "requirement over the length limit, shorten it or edit "
        "`openspec/long-requirements.json` deliberately, and push to this branch. The weekly "
        "run then leaves the branch alone.",
        f"- After merging, update the local `openspec` package to `{report.latest}` and "
        "regenerate the agent skills with `openspec update`; `uv run poe openspec-currency` "
        "warns until both match the pin.",
        "",
        "If CI's checks do not appear on this pull request, close and reopen it.",
    ]) + "\n"


# ---------- entry point -----------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    parser.add_argument("--write", action="store_true",
                        help="move a pin that is behind to npm's latest version")
    parser.add_argument("--pr-body", type=Path, help="write the bump-PR description here")
    parser.add_argument("--root", type=Path, default=REPO,
                        help="the repository to read (default: this one)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pin_file = args.root / PIN_FILE
    try:
        text = pin_file.read_bytes().decode("utf-8")
        pin = read_pin(text)
    except (OSError, ValueError) as exc:  # UnicodeDecodeError is a ValueError
        print(f"openspec currency: {exc}; nothing written", file=sys.stderr)
        return 3
    try:
        latest = latest_version()
    except CurrencyUnknown as exc:
        print(f"openspec currency unknown: {exc}", file=sys.stderr)
        return 2
    report = assess(pin, latest, local_cli_version(), skills_stamps(args.root))
    written = args.write and report.status == "behind"
    if written:
        pin_file.write_bytes(set_pin(text, latest).encode("utf-8"))
    if args.pr_body:
        args.pr_body.write_text(render_pr_body(report), encoding="utf-8")
    if args.json:
        print(json.dumps(render_json(report, written), indent=2))
    else:
        print(render_text(report))
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
