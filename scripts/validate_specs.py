#!/usr/bin/env python3
"""The OpenSpec gate: the pinned CLI's strict validation, with a ratchet on long requirements.

testing-harness spec, "OpenSpec version kept current". `uv run poe specs` runs
this script, and CI runs that task. It runs the pinned CLI's
`validate --all --strict --json` and fails on every issue it reports except an
INFO, with one exception. A requirement longer than OpenSpec's limit (500
characters since 1.14.1) passes only while `openspec/long-requirements.json`
records it at no less than its current length. A long requirement the baseline
does not list fails, and so does one that grew. One that got shorter, moved from
a change into the specs, or went away is reported.

The report must cover the tree: every spec and open change on disk, an exit
status that agrees with its items. Anything less stops the gate (exit 2), so a
version that validates nothing can never pass it.

Lengths are OpenSpec's own. Each length warning is resolved through the pinned
CLI's `show --json` (by index for a spec, by name for an open change's ADDED
requirement), and the shown text is counted the way JavaScript counts it, in
UTF-16 code units. A warning that cannot be resolved fails the gate. MODIFIED
text draws no warning while its change is open, but an archive writes it into
the specs, so every open change with delta specs is shown and its MODIFIED
requirements over the limit are judged too: against their own entry, or else
the entry of the spec requirement they replace.

The pin below is the one place the OpenSpec CLI version is chosen. The weekly
workflow (`.github/workflows/openspec-currency.yml`, through
`scripts/openspec_currency.py --write`) proposes a bump as a pull request.

Standard library only: `scripts/openspec_currency.py` imports this module, and
the weekly workflow runs it with plain python3.

Usage:
    uv run poe specs                                   # the gate
    python3 scripts/validate_specs.py --update-baseline
        # record shorter, moved or removed long requirements; never adds an entry
        # or lengthens one, and refuses while another finding stands. With no
        # baseline file it records every long requirement (the bootstrap).

Exit status: 0 pass, 1 findings, 2 the gate could not run (no npx, CLI output
that is not the expected JSON or does not cover the tree, a refused `show`, a
missing or malformed baseline).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

OPENSPEC_VERSION = "1.14.1"
PACKAGE = "@fission-ai/openspec"
REPO = Path(__file__).resolve().parent.parent
BASELINE = Path("openspec") / "long-requirements.json"
# telemetry off and no update check: the gate neither phones home nor writes
# the user's global OpenSpec configuration (an anonymous id, a notice flag)
CLI_ENV = {"OPENSPEC_TELEMETRY": "0", "OPENSPEC_NO_UPDATE_CHECK": "1"}
SHOW_WORKERS = 6
VALIDATE = ["validate", "--all", "--strict", "--json", "--no-interactive"]
LENGTH_WARNING = "Requirement text is very long"
# OpenSpec's MAX_REQUIREMENT_TEXT_LENGTH, for MODIFIED text when the report
# carries no length warning that names the limit
LIMIT = 500
FAILING = frozenset({"issue", "unmatched", "new", "grew"})
STALE = frozenset({"shorter", "moved", "inherits", "gone"})
SHOW_NEEDS = ("the gate measures a change's ADDED and MODIFIED text through `openspec show`, "
              "which reads the change's proposal.md with its ## Why and ## What Changes "
              "sections (`openspec validate` does not)")
ABOUT = (
    "Requirements over OpenSpec's length limit, with their length as OpenSpec measures "
    "it (scripts/validate_specs.py). A listed requirement may get shorter, never longer; "
    "an unlisted one may not pass the limit. `python3 scripts/validate_specs.py "
    "--update-baseline` records shorter, moved and removed ones, and never adds or "
    "lengthens an entry: to accept one deliberately, edit this file, and the diff is "
    "the review."
)

_INDEX_RE = re.compile(r"^requirements\[(\d+)\]$")
_ADDED_RE = re.compile(r'^ADDED "(.+)": ' + re.escape(LENGTH_WARNING))
_LIMIT_RE = re.compile(r"\(>(\d+) characters\)")

Key = tuple[str, str, str]  # (change, capability, name); change "" for openspec/specs


class GateError(Exception):
    """The gate could not run or could not read what it was given (exit 2)."""


@dataclass(frozen=True, order=True)
class Requirement:
    """A requirement over the limit, measured by the pinned CLI."""

    change: str  # "" for openspec/specs
    capability: str
    name: str
    length: int

    @property
    def key(self) -> Key:
        return (self.change, self.capability, self.name)


@dataclass(frozen=True)
class LengthWarning:
    item: str
    kind: str  # spec | change
    path: str
    message: str
    limit: int

    @property
    def label(self) -> str:
        return f"{self.kind} {self.item} {self.path}"


@dataclass(frozen=True)
class Finding:
    """fail: issue | unmatched | new | grew; note: info | shorter | moved | inherits | gone"""

    kind: str
    subject: str
    detail: str

    @property
    def fails(self) -> bool:
        return self.kind in FAILING


def where(change: str) -> str:
    return f"changes/{change}" if change else "specs"


def describe(key: Key) -> str:
    change, capability, name = key
    return f'{where(change)} {capability}: "{name}"'


def utf16_len(text: str) -> int:
    """JavaScript's `String.length`, the count OpenSpec compares with its limit."""
    return len(text.encode("utf-16-le")) // 2


# ---------- the CLI -----------------------------------------------------------------


def run_cli(args: list[str], root: Path) -> subprocess.CompletedProcess:
    """Run the pinned OpenSpec CLI through npx from `root`."""
    npx = shutil.which("npx")
    if npx is None:
        raise GateError("npx not found: the gate runs the pinned OpenSpec CLI through npm's "
                        "npx; install Node.js (https://nodejs.org) and run again")
    return subprocess.run(
        [npx, "-y", f"{PACKAGE}@{OPENSPEC_VERSION}", *args],
        cwd=root, capture_output=True, text=True, encoding="utf-8", check=False,
        env={**os.environ, **CLI_ENV},
    )


def parsed(proc: subprocess.CompletedProcess, args: list[str]) -> dict:
    """The JSON object a CLI run printed; a status error is the CLI's refusal."""
    command = f"`openspec {' '.join(args)}`"
    try:
        data = json.loads(proc.stdout)
    except ValueError:
        tail = (proc.stderr or proc.stdout).strip()[-400:]
        raise GateError(f"{command} printed no JSON (exit {proc.returncode}): {tail}") from None
    if not isinstance(data, dict):
        raise GateError(f"{command} printed {type(data).__name__}, not an object")
    status = data.get("status")
    errors = [str(s.get("message", s)) for s in status if isinstance(s, dict)
              and s.get("severity") == "error"] if isinstance(status, list) else []
    if errors:
        raise GateError(f"{command} failed (exit {proc.returncode}): {'; '.join(errors)}")
    return data


def cli_json(args: list[str], root: Path) -> dict:
    return parsed(run_cli(args, root), args)


# ---------- the tree, as OpenSpec 1.14.1 discovers it ------------------------------------


def spec_ids(base: Path) -> set[str]:
    """Every `spec.md` below `base` in a capability folder, nested ones as
    `area/name`; dot entries skipped, symlinked folders not followed."""
    found = set()
    for folder, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        rel = Path(folder).relative_to(base)
        if rel.parts and "spec.md" in files and (Path(folder) / "spec.md").is_file():
            found.add("/".join(rel.parts))
    return found


def change_ids(root: Path) -> set[str]:
    """Every directory in `openspec/changes/` but `archive` and dot directories."""
    try:
        entries = list(os.scandir(root / "openspec" / "changes"))
    except FileNotFoundError:
        return set()
    return {e.name for e in entries if e.is_dir(follow_symlinks=False)
            and e.name != "archive" and not e.name.startswith(".")}


def tree_items(root: Path) -> set[tuple[str, str]]:
    specs = spec_ids(root / "openspec" / "specs")
    return {("spec", s) for s in specs} | {("change", c) for c in change_ids(root)}


def has_deltas(root: Path, change: str) -> bool:
    return bool(spec_ids(root / "openspec" / "changes" / change / "specs"))


# ---------- reading the validate report -----------------------------------------------


def _well_formed(item: object) -> bool:
    return (isinstance(item, dict) and isinstance(item.get("id"), str)
            and item.get("type") in ("spec", "change") and isinstance(item.get("valid"), bool)
            and isinstance(item.get("issues"), list)
            and all(isinstance(issue, dict) for issue in item["issues"]))


def _items(report: dict) -> list[dict]:
    items = report.get("items")
    if not isinstance(items, list) or not all(_well_formed(i) for i in items):
        raise GateError("the validate report carries no `items` list of specs and changes, "
                        "each with `id`, `type`, `valid` and a list of `issues`")
    return items


def _names(pairs: Iterable[tuple[str, str]]) -> str:
    return ", ".join(f"{kind} {item}" for kind, item in sorted(pairs))


def check_report(items: list[dict], returncode: int, root: Path) -> None:
    """The report covers the tree, and the exit status agrees with its items."""
    if not items:
        raise GateError(f"OpenSpec validated nothing under {root}: the report holds no item")
    reported = {(i["type"], i["id"]) for i in items}
    expected = tree_items(root)
    if reported != expected:
        problems = [f"missing {_names(expected - reported)}" if expected - reported else "",
                    f"not in the tree: {_names(reported - expected)}"
                    if reported - expected else ""]
        raise GateError("the validate report does not cover the tree under "
                        f"{root / 'openspec'}: {'; '.join(p for p in problems if p)}")
    invalid = sum(not i["valid"] for i in items)
    if returncode != (1 if invalid else 0):
        raise GateError(f"`openspec validate` exited {returncode}, but its report has "
                        f"{invalid} invalid item(s) of {len(items)}")


def validate(root: Path) -> list[dict]:
    proc = run_cli(VALIDATE, root)
    items = _items(parsed(proc, VALIDATE))
    check_report(items, proc.returncode, root)
    return items


def _length_warning(item: dict, issue: dict) -> LengthWarning | None:
    message = str(issue.get("message", ""))
    limit = _LIMIT_RE.search(message)
    if issue.get("level") != "WARNING" or LENGTH_WARNING not in message or not limit:
        return None
    return LengthWarning(item["id"], item["type"], str(issue.get("path", "")), message,
                         int(limit.group(1)))


def _classify_item(item: dict) -> tuple[list[Finding], list[LengthWarning]]:
    subject = f"{item['type']} {item['id']}"
    findings: list[Finding] = []
    warnings: list[LengthWarning] = []
    for issue in item["issues"]:
        length = _length_warning(item, issue)
        if length:
            warnings.append(length)
            continue
        level = issue.get("level")
        detail = f"{level} {issue.get('path', '')}: {issue.get('message', '')}"
        findings.append(Finding("info" if level == "INFO" else "issue", subject, detail))
    if not item["valid"] and not warnings and not any(f.fails for f in findings):
        findings.append(Finding("issue", subject,
                                "the CLI marked it invalid without naming an error or warning"))
    return findings, warnings


def classify(items: list[dict]) -> tuple[list[Finding], list[LengthWarning]]:
    """Every issue as a finding, except the length warnings, which the ratchet judges."""
    findings: list[Finding] = []
    warnings: list[LengthWarning] = []
    for item in items:
        more, long = _classify_item(item)
        findings += more
        warnings += long
    return findings, warnings


# ---------- resolving lengths through `show` ------------------------------------------------


def _show_args(kind: str, item: str) -> list[str]:
    if kind == "spec":
        return ["show", item, "--type", "spec", "--json"]
    return ["show", item, "--type", "change", "--json", "--deltas-only"]


def show(kind: str, item: str, root: Path) -> dict:
    try:
        return cli_json(_show_args(kind, item), root)
    except GateError as exc:
        if kind == "change":
            raise GateError(f"{exc}\n  {SHOW_NEEDS}") from None
        raise


def _shown_texts(kind: str, shown: dict) -> dict:
    """spec: index -> (name, text); change: (operation, capability, name) -> text,
    for its ADDED and MODIFIED deltas."""
    if kind == "spec":
        reqs = shown.get("requirements")
        if not isinstance(reqs, list):
            raise GateError("`openspec show --type spec` printed no `requirements` list")
        return {i: (r.get("name", ""), r.get("text", "")) for i, r in enumerate(reqs)}
    deltas = shown.get("deltas")
    if not isinstance(deltas, list):
        raise GateError("`openspec show --type change` printed no `deltas` list")
    return {(d.get("operation"), d.get("spec"), d["requirement"].get("name")):
            d["requirement"].get("text", "")
            for d in deltas
            if d.get("operation") in ("ADDED", "MODIFIED")
            and isinstance(d.get("requirement"), dict)}


def _locate(warning: LengthWarning, texts: dict) -> tuple[Key, str] | str:
    """The key and shown text a warning names, or why it names none."""
    if warning.kind == "spec":
        index = _INDEX_RE.match(warning.path)
        if not index:
            return "unrecognized path for a spec length warning"
        found = texts.get(int(index.group(1)))
        if found is None:
            return f"no requirement {index.group(1)} in `openspec show {warning.item}`"
        return ("", warning.item, found[0]), found[1]
    added = _ADDED_RE.match(warning.message)
    if warning.kind != "change" or not added or not warning.path.endswith("/spec.md"):
        return "unrecognized shape for a length warning"
    capability, name = warning.path.removesuffix("/spec.md"), added.group(1)
    text = texts.get(("ADDED", capability, name))
    if text is None:
        return f'no ADDED "{name}" in {capability} in `openspec show {warning.item}`'
    return (warning.item, capability, name), text


def resolve(warning: LengthWarning, texts: dict) -> Requirement | Finding:
    located = _locate(warning, texts)
    if isinstance(located, str):
        return Finding("unmatched", warning.label, located)
    key, text = located
    length = utf16_len(text)
    if length <= warning.limit:
        return Finding("unmatched", warning.label,
                       f'the shown text of "{key[2]}" is {length} characters, '
                       f"not over the limit of {warning.limit}")
    return Requirement(*key, length)


def modified(change: str, texts: dict, limit: int) -> list[Requirement]:
    """A change's MODIFIED requirements over the limit: OpenSpec warns about
    them only once an archive has written them into the specs."""
    return [Requirement(change, capability, name, utf16_len(text))
            for (operation, capability, name), text in texts.items()
            if operation == "MODIFIED" and utf16_len(text) > limit]


def measure(warnings: list[LengthWarning], changes: Iterable[str], root: Path
            ) -> tuple[list[Requirement], list[Finding]]:
    """One `show` per item with length warnings and per open change with delta
    specs, a few at a time."""
    items = sorted({(w.kind, w.item) for w in warnings} | {("change", c) for c in changes})
    with ThreadPoolExecutor(max_workers=SHOW_WORKERS) as pool:
        shown = list(pool.map(lambda ki: show(*ki, root), items))
    texts = {ki: _shown_texts(ki[0], data) for ki, data in zip(items, shown, strict=True)}
    measured: list[Requirement] = []
    unmatched: list[Finding] = []
    for warning in warnings:
        result = resolve(warning, texts[(warning.kind, warning.item)])
        (measured if isinstance(result, Requirement) else unmatched).append(result)
    limit = min((w.limit for w in warnings), default=LIMIT)
    for kind, item in items:
        if kind == "change":
            measured += modified(item, texts[(kind, item)], limit)
    return measured, unmatched


# ---------- the baseline --------------------------------------------------------------


def _lengths(node: object, what: str) -> dict[str, int]:
    if not isinstance(node, dict) or not all(
            isinstance(n, str) and type(v) is int for n, v in node.items()):
        raise GateError(f"malformed baseline at {what}: expected requirement names "
                        "mapped to integer lengths")
    return node


def _groups(node: object, what: str) -> dict:
    if not isinstance(node, dict):
        raise GateError(f"malformed baseline at {what}: expected an object")
    return node


def load_baseline(path: Path) -> dict[Key, int] | None:
    """The baseline's entries, or None when the file does not exist."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise GateError(f"malformed baseline {path}: {exc}") from None
    data = _groups(data, "the top level")
    entries: dict[Key, int] = {}
    for capability, names in _groups(data.get("specs", {}), "specs").items():
        for name, length in _lengths(names, f"specs.{capability}").items():
            entries[("", capability, name)] = length
    for change, capabilities in _groups(data.get("changes", {}), "changes").items():
        for capability, names in _groups(capabilities, f"changes.{change}").items():
            for name, length in _lengths(names, f"changes.{change}.{capability}").items():
                entries[(change, capability, name)] = length
    return entries


def render_baseline(entries: dict[Key, int]) -> str:
    specs: dict = {}
    changes: dict = {}
    for (change, capability, name), length in entries.items():
        home = changes.setdefault(change, {}) if change else specs
        home.setdefault(capability, {})[name] = length
    document = {"about": ABOUT, "changes": changes, "specs": specs}
    return json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# ---------- the ratchet ------------------------------------------------------------------


def candidates(key: Key, baseline: dict[Key, int], open_changes: set[str]) -> list[Key]:
    """The entries a requirement answers to. An open change's requirement with
    an entry of its own answers to that entry alone. Otherwise its own entry,
    if any, and every entry with its capability and name in the specs or under
    a change that is no longer open: an archive moves an ADDED or MODIFIED
    requirement from its change into the specs, and a MODIFIED delta without
    an entry answers to the spec requirement it replaces. An open change's
    entry never loosens the spec it modifies."""
    if key[0] and key in baseline:
        return [key]
    return [other for other in baseline if other[1:] == key[1:]
            and (other == key or not other[0] or other[0] not in open_changes)]


def _verdicts(req: Requirement, entry: Key, allowed: int) -> list[Finding]:
    subject = describe(req.key)
    verdicts = []
    if entry != req.key and req.change and not entry[0]:
        verdicts.append(Finding("inherits", subject,
                                "has no entry of its own and answers to the entry in specs "
                                "for the requirement it replaces"))
    elif entry != req.key:
        verdicts.append(Finding("moved", subject, f"matched the entry in {where(entry[0])}"))
    if req.length > allowed:
        verdicts.append(Finding(
            "grew", subject,
            f"is {req.length} characters, recorded {allowed}: shorten it to at most "
            f"{allowed} (move detail into scenarios), or, to accept it deliberately, "
            f"record {req.length} for it in {BASELINE.as_posix()} by hand"))
    elif req.length < allowed:
        verdicts.append(Finding("shorter", subject,
                                f"is {req.length} characters, recorded {allowed}"))
    return verdicts


def judge(measured: Iterable[Requirement], baseline: dict[Key, int], open_changes: set[str]
          ) -> tuple[list[Finding], dict[Key, int]]:
    """The ratchet's findings, and the baseline tightened to what was measured:
    a passing requirement is recorded at its own location and length, a grown
    one leaves the entry it answers to as it was."""
    findings: list[Finding] = []
    tightened: dict[Key, int] = {}
    used: set[Key] = set()
    for req in sorted(measured):
        found = candidates(req.key, baseline, open_changes)
        used.update(found)
        if not found:
            findings.append(Finding(
                "new", describe(req.key), f"is {req.length} characters and has no baseline "
                "entry: move detail into scenarios, or, if it was renamed, rename its entry"))
            continue
        # the largest; on a tie its own entry, so a tie reports no move
        entry = max(found, key=lambda k, own=req.key: (baseline[k], k == own, k))
        allowed = baseline[entry]
        findings += _verdicts(req, entry, allowed)
        keep, length = (entry, allowed) if req.length > allowed else (req.key, req.length)
        tightened[keep] = min(length, tightened.get(keep, length))
    findings += [Finding("gone", describe(key), "is no longer over the limit or no longer exists")
                 for key in sorted(set(baseline) - used)]
    return findings, tightened


# ---------- entry point ---------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--update-baseline", action="store_true",
                        help="record shorter, moved or removed long requirements")
    parser.add_argument("--root", type=Path, default=REPO,
                        help="the directory holding openspec/ (default: this repository)")
    parser.add_argument("--baseline", type=Path,
                        help=f"the baseline file (default: <root>/{BASELINE.as_posix()})")
    return parser


def report(findings: list[Finding]) -> None:
    for finding in sorted(findings, key=lambda f: (not f.fails, f.kind, f.subject)):
        print(f"{'FAIL' if finding.fails else 'note'}  {finding.kind:<9} "
              f"{finding.subject} {finding.detail}")


def update(path: Path, findings: list[Finding], measured: list[Requirement],
           baseline: dict[Key, int] | None, open_changes: set[str]) -> int:
    if any(f.kind in ("issue", "unmatched") for f in findings):
        print(f"{path}: nothing written while the findings above stand (fix them first)")
        return 1
    if baseline is None:
        entries = {req.key: req.length for req in measured}
        verdicts: list[Finding] = []
    else:
        verdicts, entries = judge(measured, baseline, open_changes)
    report(verdicts)
    path.write_text(render_baseline(dict(sorted(entries.items()))), encoding="utf-8",
                    newline="\n")
    print(f"{path}: {len(entries)} long requirements recorded")
    return 1 if any(f.fails for f in verdicts) else 0


def run(root: Path) -> tuple[list[dict], list[Finding], list[Requirement]]:
    """Validate, classify and measure: the report's items, its findings, and
    the long requirements."""
    items = validate(root)
    findings, warnings = classify(items)
    changes = [i["id"] for i in items if i["type"] == "change" and has_deltas(root, i["id"])]
    measured, unmatched = measure(warnings, changes, root)
    return items, findings + unmatched, measured


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    path = args.baseline or root / BASELINE
    try:
        baseline = load_baseline(path)
        if baseline is None and not args.update_baseline:
            raise GateError(f"no baseline at {path}: record one with "
                            "`python3 scripts/validate_specs.py --update-baseline`")
        items, findings, measured = run(root)
    except GateError as exc:
        print(f"spec gate could not run: {exc}", file=sys.stderr)
        return 2
    open_changes = {i["id"] for i in items if i["type"] == "change"}
    print(f"OpenSpec {OPENSPEC_VERSION}: {len(items)} items validated, "
          f"{len(measured)} long requirements")
    report(findings)
    if args.update_baseline:
        return update(path, findings, measured, baseline, open_changes)
    verdicts, _ = judge(measured, baseline, open_changes)
    report(verdicts)
    failed = [f for f in findings + verdicts if f.fails]
    if failed:
        print(f"spec gate failed: {len(failed)} finding(s)")
        return 1
    if any(f.kind in STALE for f in verdicts):
        print("the baseline is stale: `python3 scripts/validate_specs.py --update-baseline` "
              "records it")
    print("spec gate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
