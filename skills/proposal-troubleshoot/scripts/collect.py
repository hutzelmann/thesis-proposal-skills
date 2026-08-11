#!/usr/bin/env python3
"""Assemble a bug-report bundle for the thesis-proposal skills.

Collects what a maintainer needs and nothing the user did not agree to: the
environment, which revision of the skills is installed, and as much or as
little of the proposal as the chosen disclosure level allows. Writes only
inside the bundle directory it creates.

Facts this script establishes are tagged `[measured]`. Fields only the agent
can supply — its model, its harness, its account of what happened — are left as
`[self-reported]` placeholders for the agent to fill in, so a maintainer can
tell evidence from testimony.

Usage:
    python3 collect.py [<proposal.md>] [--level minimal|structure|full]
                       [--dry-run] [--force] [--script-output FILE]...
                       [--out DIR]

Requires Python >= 3.11, standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import sys
from pathlib import Path

LEVELS = ("minimal", "structure", "full")
BUNDLE_DIR = "bug-report"
REDACTED = "<redacted>"
PROPOSAL_PLACEHOLDER = "<proposal>"
SKILL_PREFIX = "proposal-"
SKIP_DIR_NAMES = {"__pycache__", ".git"}
SKIP_SUFFIXES = (".pyc", ".pyo")

HERE = Path(__file__).resolve().parent
SKELETON = HERE.parent / "references" / "structure.json"
SUPPORT = HERE.parent / "references" / "model-support.json"

# personal data the full level must not carry out of the workspace; mirrors the
# categories the proposal rules already forbid inside a proposal
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
MATRICULATION_RE = re.compile(r"\b\d{6,10}\b")
AUTHOR_RE = re.compile(r"^\s*(?:author|family|given)\s*:\s*(.+)$", re.MULTILINE)
BACKTICK_RE = re.compile(r"`([^`]*)`")
TODO_RE = re.compile(r"\[TODO:[^\]]*\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:\w]+", re.IGNORECASE)

# workspace build definitions proposal-publish delegates to. Restated rather
# than imported: a skill never reaches into a sibling's scripts, and a user may
# have installed only one of the two. tests/unit/test_troubleshoot_collect.py
# pins these against publish.py's own constants so the two cannot drift.
BUILD_STEM = "proposal-build"
BUILD_RECIPE_NAMES = frozenset({"makefile", "gnumakefile", "justfile"})
BUILD_TARGET_RE = re.compile(rf"^{BUILD_STEM}\b[^\n]*:", re.MULTILINE)


# --------------------------------------------------------------------------
# hashing
# --------------------------------------------------------------------------

def _sha1(payload: bytes) -> str:
    try:
        return hashlib.sha1(payload, usedforsecurity=False).hexdigest()
    except TypeError:  # builds without the keyword
        return hashlib.sha1(payload).hexdigest()


def git_blob_hash(data: bytes) -> str:
    """Git's own object name for this content, so a maintainer can resolve it
    with `git log --all --find-object=<sha>` instead of walking history.
    """
    return _sha1(b"blob " + str(len(data)).encode() + b"\0" + data)


def file_hashes(path: Path) -> dict[str, str]:
    """Three hashes, because one is ambiguous. Git stores LF; a Windows checkout
    may hold CRLF, and then the raw blob hash matches nothing.
    """
    data = path.read_bytes()
    normalized = data.replace(b"\r\n", b"\n")
    out = {
        "git_blob": git_blob_hash(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": str(len(data)),
    }
    if normalized != data:
        out["git_blob_lf"] = git_blob_hash(normalized)
    return out


# --------------------------------------------------------------------------
# install identification
# --------------------------------------------------------------------------

def skill_roots(workspace: Path) -> list[Path]:
    """Directories that may hold installed `proposal-*` skills. The script's own
    grandparent is the reliable anchor; the rest cover project and global
    installs and the per-agent symlink trees the installer creates.
    """
    candidates = [
        HERE.parent.parent,
        workspace / ".agents" / "skills",
        workspace / ".claude" / "skills",
        Path.home() / ".agents" / "skills",
        Path.home() / ".claude" / "skills",
    ]
    roots: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_dir() and resolved not in seen:
            seen.add(resolved)
            roots.append(resolved)
    return roots


def installed_skills(workspace: Path) -> list[Path]:
    """Resolved skill directories, deduplicated: the per-agent trees are
    symlinks into one real directory, and hashing it twice says nothing twice.
    """
    found: list[Path] = []
    seen: set[Path] = set()
    for root in skill_roots(workspace):
        for entry in sorted(root.glob(SKILL_PREFIX + "*")):
            try:
                resolved = entry.resolve()
            except OSError:
                continue
            if resolved.is_dir() and resolved not in seen:
                seen.add(resolved)
                found.append(resolved)
    return found


def hash_lines(workspace: Path) -> tuple[list[str], int]:
    """One line per installed skill file: path, git blob, sha256, size. Paths are
    reported skill-relative, so no home directory or user name travels with them.
    """
    lines: list[str] = []
    count = 0
    for skill_dir in installed_skills(workspace):
        for path in sorted(skill_dir.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            if path.suffix in SKIP_SUFFIXES:
                continue
            h = file_hashes(path)
            rel = f"{skill_dir.name}/{path.relative_to(skill_dir).as_posix()}"
            fields = [rel, f"git_blob={h['git_blob']}"]
            if "git_blob_lf" in h:
                fields.append(f"git_blob_lf={h['git_blob_lf']}")
            fields.append(f"sha256={h['sha256']}")
            fields.append(f"bytes={h['bytes']}")
            lines.append(" ".join(fields))
            count += 1
    return lines, count


def find_lock(workspace: Path) -> Path | None:
    """The installer's lock record. It carries no commit SHA and covers only
    each skill's instruction file, so it corroborates source and install method
    rather than identifying a revision.
    """
    for candidate in (workspace / "skills-lock.json", Path.home() / "skills-lock.json"):
        if candidate.is_file():
            return candidate
    return None


# --------------------------------------------------------------------------
# redaction
# --------------------------------------------------------------------------

def canonical_titles() -> set[str]:
    """Section titles from the shipped skeleton, both languages, with the
    methodology template expanded. These are the only backticked spans that may
    survive redaction: they are fixed by the guidance, not written by the user.
    """
    if not SKELETON.is_file():
        return set()
    try:
        data = json.loads(SKELETON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    titles: set[str] = set()
    sections = data.get("sections", {}).get("titles", {})
    methodologies = data.get("methodologies", {})
    for key, per_lang in sections.items():
        for lang, title in per_lang.items():
            if key == "methodology" and "{methodology}" in title:
                for method in methodologies.values():
                    name = method.get("title", {}).get(lang)
                    if name:
                        titles.add(title.replace("{methodology}", name))
            else:
                titles.add(title)
    for method in methodologies.values():
        titles.update(method.get("title", {}).values())
        for sub in method.get("subsections", []):
            titles.update(sub.values())
    return titles


def redact_text(text: str, allowed: set[str], proposal_names: set[str]) -> str:
    """Strip user wording from text that was not written for disclosure. Every
    backticked span goes unless it is a canonical title, because backticks are
    how the shipped scripts quote content back. The proposal's own file name goes
    too: the slug is derived from the topic.
    """
    def replace_span(match: re.Match[str]) -> str:
        inner = match.group(1)
        return match.group(0) if inner in allowed else f"`{REDACTED}`"

    out = BACKTICK_RE.sub(replace_span, text)
    out = TODO_RE.sub("[TODO: " + REDACTED + "]", out)
    for name in sorted(proposal_names, key=len, reverse=True):
        if name:
            out = out.replace(name, PROPOSAL_PLACEHOLDER)
    return out


def strip_personal_data(text: str) -> str:
    """Apply the rules that already govern a proposal to text leaving the
    workspace: no address, no matriculation number, no author name. The author
    is taken from the metadata block and then removed everywhere, because a name
    that appears in the body is the same disclosure as one in the metadata.
    """
    out = EMAIL_RE.sub("<email removed>", text)
    out = MATRICULATION_RE.sub("<number removed>", out)
    for match in AUTHOR_RE.finditer(text):
        name = match.group(1).strip().strip("\"'")
        if len(name) < 3:
            continue
        out = out.replace(name, "<author removed>")
        for part in name.split():
            if len(part) > 2:
                out = re.sub(rf"\b{re.escape(part)}\b", "<name removed>", out)
    return out


# --------------------------------------------------------------------------
# proposal description per level
# --------------------------------------------------------------------------

def describe_proposal(path: Path, level: str) -> list[str]:
    """What the report says about the proposal, bounded by the level.

    minimal   — shape only: counts, hashes, whether each heading is canonical.
    structure — adds headings, TODO texts and DOIs verbatim; still no prose.
    full      — adds the text, with the personal-data rules applied.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    headings = [(m.group(1), m.group(2)) for m in (HEADING_RE.match(ln) for ln in lines) if m]
    todos = TODO_RE.findall(text)
    dois = sorted(set(DOI_RE.findall(text)))
    allowed = canonical_titles()
    h = file_hashes(path)

    out = [
        "[measured] proposal file recorded as " + PROPOSAL_PLACEHOLDER
        + f" ({h['bytes']} bytes, sha256:{h['sha256']})",
        f"[measured] {len(lines)} lines, {len(text.split())} words, "
        f"{len(headings)} headings, {len(todos)} open TODO marker(s), "
        f"{len(dois)} DOI(s) present",
    ]

    if level == "minimal":
        canonical = sum(1 for _, title in headings if title in allowed)
        out.append(
            f"[measured] {canonical} of {len(headings)} headings match a canonical "
            "title; heading text withheld at this level"
        )
        return out

    out.append("[measured] headings, in order:")
    for hashes, title in headings:
        mark = "canonical" if title in allowed else "custom"
        out.append(f"  {hashes} {title}   ({mark})")
    if todos:
        out.append("[measured] open TODO markers:")
        out.extend(f"  {t}" for t in todos)
    if dois:
        out.append("[measured] reference DOIs: " + ", ".join(dois))

    if level == "full":
        out.append("")
        out.append("[measured] full proposal text, personal data removed:")
        out.append("```markdown")
        out.append(strip_personal_data(text).rstrip())
        out.append("```")
    return out


# --------------------------------------------------------------------------
# environment
# --------------------------------------------------------------------------

def tool_presence(name: str) -> str:
    """Presence only, never a version.

    Reading a version means executing the tool, and a shipped skill that spawns
    processes widens what the published-skill audit has to clear. Absence is the
    actionable fact anyway — a missing `typst` explains a failed build outright.
    Where a version genuinely matters, the skill asks the user to run the tool
    themselves and pass the output in as captured evidence.
    """
    return "present" if shutil.which(name) else "absent"


def environment_lines() -> list[str]:
    return [
        f"[measured] python {platform.python_version()}",
        f"[measured] platform {platform.system()} {platform.release()} ({platform.machine()})",
        f"[measured] pandoc: {tool_presence('pandoc')}",
        f"[measured] typst: {tool_presence('typst')}",
        f"[measured] git: {tool_presence('git')}",
        "[measured] tool versions not probed — this script runs no other program; paste "
        "`pandoc --version` or `typst --version` output if a version is in question",
    ]


# --------------------------------------------------------------------------
# artifacts
# --------------------------------------------------------------------------

def notes_log(proposal: Path | None) -> tuple[str, str] | None:
    """The companion notes file's Log section — the trace the skills already
    keep, which is why this script does not need to invent a new one.
    """
    if proposal is None:
        return None
    notes = proposal.with_name(proposal.stem + ".notes.md")
    if not notes.is_file():
        return None
    text = notes.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    headings = [(i, m) for i, m in enumerate(HEADING_RE.match(ln) for ln in lines) if m]
    start = next((i for i, m in headings if m.group(2).strip().lower() == "log"), None)
    if start is None:
        return ("notes-log.md", text)
    start_level = len(HEADING_RE.match(lines[start]).group(1))
    end = next(
        (i for i, m in headings if i > start and len(m.group(1)) <= start_level),
        len(lines),
    )
    return ("notes-log.md", "\n".join(lines[start:end]).rstrip() + "\n")


def workspace_build_lines(proposal: Path) -> list[str]:
    """The workspace build definition, if publish would delegate to one.

    Without this line a report from a workspace-built document is
    indistinguishable from one about the shipped pipeline, and every such
    report reads as "works for me". The names come from the fixed set publish
    recognizes, so they carry nothing about the user and are recorded verbatim;
    the file's content is the user's own code and never enters the report.
    """
    out: list[str] = []
    for entry in sorted(proposal.parent.iterdir(), key=lambda p: p.name):
        if not entry.is_file():
            continue
        recipe = entry.name.lower().lstrip(".") in BUILD_RECIPE_NAMES
        if recipe and not BUILD_TARGET_RE.search(
            entry.read_text(encoding="utf-8", errors="replace")
        ):
            continue
        if not recipe and not (
            entry.name == BUILD_STEM or entry.name.startswith(BUILD_STEM + ".")
        ):
            continue
        h = file_hashes(entry)
        target = f" (target `{BUILD_STEM}`)" if recipe else ""
        out.append(
            f"[measured] workspace build definition present as {entry.name}{target} "
            f"({h['bytes']} bytes, sha256:{h['sha256']}); content withheld at every "
            "level — this document was not built by the shipped pipeline"
        )
    return out


def sibling_artifacts(proposal: Path | None) -> list[str]:
    """Hash-level inventory of the companion artifacts beside the proposal —
    the review file, the supervise send-package, and any workspace build
    definition. Slug-bearing names are recorded under the placeholder; content
    never enters the report at any level, because the letter derives from a
    student's unpublished submission, the build definition is the user's own
    code, and the graded levels govern the proposal only.
    """
    if proposal is None:
        return []
    out: list[str] = list(workspace_build_lines(proposal))
    review = proposal.with_name(proposal.stem + "-review.md")
    if review.is_file():
        h = file_hashes(review)
        out.append(
            f"[measured] review file present as {PROPOSAL_PLACEHOLDER}-review.md "
            f"({h['bytes']} bytes, sha256:{h['sha256']}); content withheld at every level"
        )
    package = proposal.with_name(proposal.stem + "-package")
    if package.is_dir():
        files = sorted(f for f in package.iterdir() if f.is_file())
        out.append(
            f"[measured] send-package present as {PROPOSAL_PLACEHOLDER}-package/ "
            f"({len(files)} file(s)); content withheld at every level:"
        )
        for f in files:
            shown = f.name if f.name == "letter.md" else PROPOSAL_PLACEHOLDER + f.suffix
            h = file_hashes(f)
            out.append(f"  {shown} — {h['bytes']} bytes, sha256:{h['sha256']}")
    return out


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def build_report(level: str, proposal: Path | None,
                 script_outputs: list[tuple[str, str]], hash_count: int,
                 lock: Path | None) -> str:
    allowed = canonical_titles()
    names = set()
    if proposal is not None:
        names = {proposal.name, proposal.stem}

    sections: list[str] = [
        "# Bug report — thesis-proposal skills",
        "",
        f"Disclosure level: **{level}**. Facts marked `[measured]` were established by "
        "this script. Facts marked `[self-reported]` come from the agent, which is also "
        "the subject of this report — weigh them accordingly.",
        "",
        "## Triage",
        "",
        "[self-reported] rung reached: <stale-install | model | guidelines | script | "
        "mandate | dissatisfaction | unidentified>",
        "[self-reported] verdict: <defect | not a defect>",
        "[self-reported] installed skills were updated before reporting: <yes | no>",
        "",
        "## What happened",
        "",
        "[self-reported] what the user asked for:",
        "[self-reported] what the skill did:",
        "[self-reported] what was expected instead:",
        "[self-reported] which skill and which of its steps:",
        "",
        "## Agent and harness",
        "",
        "[self-reported] model:",
        "[self-reported] harness:",
        "",
        "## Environment",
        "",
    ]
    sections.extend(environment_lines())
    sections += ["", "## Installed skills", ""]
    if lock is not None:
        sections.append(
            "[measured] installer lock record copied to `skills-lock.json` "
            "(source and install method; carries no commit identifier)"
        )
    else:
        sections.append(
            "[measured] no installer lock record found — install method unknown "
            "(hand-copied or installed by other means)"
        )
    sections.append(
        f"[measured] {hash_count} installed skill file(s) hashed in `hashes.txt`; "
        "resolve them with scripts/identify_release.py in the development repository"
    )
    sections.append(
        "[measured] support verdicts consulted from the skill's shipped "
        f"`references/model-support.json` ({'present' if SUPPORT.is_file() else 'MISSING'})"
    )

    sections += ["", "## Proposal", ""]
    if proposal is None:
        sections.append("[measured] no proposal file was named; the problem is not tied to one")
    else:
        sections.extend(describe_proposal(proposal, level))
        sections.extend(sibling_artifacts(proposal))

    sections += ["", "## Captured script output", ""]
    if not script_outputs:
        sections.append("[measured] none supplied")
    for name, body in script_outputs:
        shown = body if level == "full" else redact_text(body, allowed, names)
        note = "" if level == "full" else " (backticked spans redacted unless canonical)"
        sections += [f"### {name}{note}", "", "```", shown.rstrip(), "```", ""]

    sections += [
        "",
        "## Reproduction",
        "",
        "[self-reported] reproducible from a file and a command: <yes | no | reduction failed>",
        "[self-reported] if yes, see `repro/input.md` and `repro/command.txt`",
        "",
        "---",
        "",
        "Delivery is yours: this bundle was written locally and nothing was sent. "
        "Paste it into a GitHub issue, email it, or hand it to your supervisor. "
        "The directory can be deleted once you have sent it.",
        "",
    ]
    return "\n".join(sections)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def resolve_model(reported: str, support_path: Path = SUPPORT) -> tuple[str | None, dict]:
    """Match an agent's self-reported model name against the shipped verdicts.
    Matching is by suffix on a path boundary, because an agent reports
    `claude-opus-5` while the roster keys it as `anthropic/claude-opus-5`.
    Returns (matched key or None, that model's record).
    """
    if not support_path.is_file():
        return None, {}
    try:
        data = json.loads(support_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, {}
    models = data.get("models", {})
    wanted = reported.strip().removeprefix("openrouter/")
    if wanted in models:
        return wanted, models[wanted]
    hits = [key for key in sorted(models) if key.endswith("/" + wanted)]
    if len(hits) == 1:
        return hits[0], models[hits[0]]
    return None, {}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("proposal", nargs="?", type=Path,
                        help="the proposal the problem concerns, if it concerns one")
    parser.add_argument("--level", choices=LEVELS, default="minimal",
                        help="how much of the proposal the report carries (default: minimal)")
    parser.add_argument("--dry-run", action="store_true",
                        help="print what would be written and write nothing")
    parser.add_argument("--force", action="store_true",
                        help="overwrite an existing bundle directory")
    parser.add_argument("--script-output", action="append", type=Path, default=[],
                        metavar="FILE", help="captured stdout/stderr of a shipped script")
    parser.add_argument("--out", type=Path, default=None,
                        help=f"bundle directory (default: ./{BUNDLE_DIR})")
    return parser.parse_args(argv)


class Plan:
    """Everything the bundle will contain, computed before anything is written.

    Splitting the plan from the write is what makes `--dry-run` honest: it
    prints this object, and the write step consumes the same one.
    """

    def __init__(self, level: str, report: str, hash_lines_: list[str], hash_count: int,
                 lock: Path | None, notes: tuple[str, str] | None, guidelines: Path | None,
                 stored_outputs: list[tuple[str, str]]) -> None:
        self.level = level
        self.report = report
        self.hash_lines = hash_lines_
        self.hash_count = hash_count
        self.lock = lock
        self.notes = notes
        self.guidelines = guidelines
        self.stored_outputs = stored_outputs

    @property
    def paths(self) -> list[str]:
        out = [f"{BUNDLE_DIR}/report.md", f"{BUNDLE_DIR}/hashes.txt"]
        if self.lock is not None:
            out.append(f"{BUNDLE_DIR}/skills-lock.json")
        if self.notes is not None:
            out.append(f"{BUNDLE_DIR}/artifacts/{self.notes[0]}")
        if self.guidelines is not None:
            out.append(f"{BUNDLE_DIR}/artifacts/guidelines.md")
        out += [f"{BUNDLE_DIR}/artifacts/{name}" for name, _ in self.stored_outputs]
        return out


def read_script_outputs(paths: list[Path]) -> list[tuple[str, str]]:
    """Raises FileNotFoundError naming the first missing capture."""
    outputs = []
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(str(path))
        outputs.append((path.name, path.read_text(encoding="utf-8", errors="replace")))
    return outputs


def plan_bundle(level: str, proposal: Path | None, script_outputs: list[tuple[str, str]],
                workspace: Path) -> Plan:
    lock = find_lock(workspace)
    lines, hash_count = hash_lines(workspace)
    report = build_report(level, proposal, script_outputs, hash_count, lock)
    # the copies in artifacts/ must obey the level exactly as the report does;
    # writing them verbatim would hand out at minimal what minimal withholds
    allowed = canonical_titles()
    proposal_names = {proposal.name, proposal.stem} if proposal else set()
    stored_outputs = [
        (name, body if level == "full" else redact_text(body, allowed, proposal_names))
        for name, body in script_outputs
    ]
    guidelines = workspace / "guidelines.md"
    return Plan(
        level=level, report=report, hash_lines_=lines, hash_count=hash_count, lock=lock,
        notes=notes_log(proposal), guidelines=guidelines if guidelines.is_file() else None,
        stored_outputs=stored_outputs,
    )


def write_bundle(bundle: Path, plan: Plan) -> None:
    (bundle / "artifacts").mkdir(parents=True, exist_ok=True)
    (bundle / "report.md").write_text(plan.report, encoding="utf-8")
    (bundle / "hashes.txt").write_text("\n".join(plan.hash_lines) + "\n", encoding="utf-8")
    if plan.lock is not None:
        (bundle / "skills-lock.json").write_text(
            plan.lock.read_text(encoding="utf-8"), encoding="utf-8"
        )
    if plan.notes is not None:
        (bundle / "artifacts" / plan.notes[0]).write_text(plan.notes[1], encoding="utf-8")
    if plan.guidelines is not None:
        (bundle / "artifacts" / "guidelines.md").write_text(
            plan.guidelines.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
        )
    for name, body in plan.stored_outputs:
        (bundle / "artifacts" / name).write_text(body, encoding="utf-8")


def clear_existing(bundle: Path, force: bool) -> int:
    """0 to proceed, 3 to abort. A half-stale bundle reads as a whole one, so an
    accepted overwrite replaces rather than merges."""
    if not bundle.exists():
        return 0
    if not force:
        print(f"error: {bundle} already exists — inspect or move it, or pass --force",
              file=sys.stderr)
        return 3
    if not (bundle / "report.md").is_file():
        print(f"error: {bundle} exists but is not a bug-report bundle — refusing to "
              "overwrite it", file=sys.stderr)
        return 3
    shutil.rmtree(bundle)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    workspace = Path.cwd()
    bundle = (args.out or workspace / BUNDLE_DIR).resolve()

    if args.proposal is not None and not args.proposal.is_file():
        print(f"error: proposal file not found: {args.proposal}", file=sys.stderr)
        return 2
    try:
        script_outputs = read_script_outputs(args.script_output)
    except FileNotFoundError as exc:
        print(f"error: captured output not found: {exc}", file=sys.stderr)
        return 2

    plan = plan_bundle(args.level, args.proposal, script_outputs, workspace)

    if args.dry_run:
        print(f"level: {args.level} (of {', '.join(LEVELS)})")
        print(f"would write into {bundle}:")
        for item in plan.paths:
            print(f"  {item}")
        print(f"\n{plan.hash_count} installed skill file(s) would be hashed")
        print("\n--- report.md as it would be written ---")
        print(plan.report)
        return 0

    if (code := clear_existing(bundle, args.force)) != 0:
        return code
    write_bundle(bundle, plan)

    print(f"bundle written to {bundle} at level {args.level}")
    print("nothing was sent — review it, then deliver it yourself")
    for item in plan.paths:
        print(f"  {item}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
