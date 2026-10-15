#!/usr/bin/env python3
# GENERATED from skills/proposal-check/scripts/check.py
# Edit there, then run scripts/sync_shared.py
"""Deterministic low-level checks for a thesis proposal file.

Stdlib-only (Python >= 3.11). Reads the proposal's markdown — leading `# ` title
line, emphasized subtitle paragraph, sections, and the trailing references
metadata block (narrow extraction — no general YAML parsing) — plus the
canonical skeleton from references/structure.json and an optional workspace
guidelines.md TOML override block. Where the proposal's review file exists, it
is read for the record of the research questions it judged, never written. The
proposal's language is inferred from the
subtitle wording, falling back to a majority of canonical section titles.

Output: two-bucket report (mechanical errors / mechanical warnings) plus a
fixed note on what is deferred to the agent pass. Exit 1 only on mechanical
errors — the check is advisory, warnings never fail the run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import tomllib
import unicodedata
from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

BOOLEAN_LITERALS = {"y", "n", "yes", "no", "on", "off", "true", "false"}
KEY_MAX_LEN = 20  # guidance: reference keys stay shorter than 20 characters


# ---------- findings ---------------------------------------------------------
#
# A finding is a value, not a sentence. `rule` is the contract a consumer keys
# on and stays stable when `message` is reworded; `message` is what a student
# reads and is free to change. The closed set below is the whole vocabulary.

@dataclass(frozen=True)
class Finding:
    level: str  # "error" | "warning"
    rule: str
    message: str


def error(rule: str, message: str) -> Finding:
    return Finding("error", rule, message)


def warn(rule: str, message: str) -> Finding:
    return Finding("warning", rule, message)


RULE_IDS = (
    # metadata block and reference syntax
    "guidelines-toml-parse",
    "metadata-block-missing",
    "metadata-block-blank-line",
    "metadata-block-multiple",
    "reference-id-boolean-literal",
    "duplicate-reference-id",
    "retired-metadata-key",
    "legacy-format",
    # document frame
    "title-line-missing",
    "title-not-first",
    "multiple-h1",
    "subtitle-missing",
    "subtitle-not-emphasized",
    "references-section-missing",
    "references-section-not-last",
    "references-section-not-empty",
    "language-undeterminable",
    # title
    "title-implementation-opener",
    "title-buzzword",
    "title-question-form",
    "title-too-short",
    "title-too-long",
    # workspace override file
    "override-key-retired",
    "override-key-unknown",
    "methodology-branch-invalid",
    "paths-proposals-invalid",
    "proposal-misplaced",
    "proposal-folder-mismatch",
    # workspace family
    "companion-orphaned",
    "build-definition-unused",
    # structure
    "heading-style-setext",
    "timeline-detail-unknown",
    "page-limit-invalid",
    "required-section-missing",
    "section-out-of-order",
    "timeline-table",
    "timeline-list",
    "timeline-subsection",
    "timeline-too-long",
    "methodology-missing",
    "methodology-multiple",
    "methodology-unknown",
    "methodology-subsection-missing",
    "forbidden-section",
    # research questions
    "research-questions-not-a-list",
    "research-questions-too-many",
    "research-question-unreferenced",
    # citations and references
    "citation-undefined",
    "reference-uncited",
    "author-name-typed-bracketed",
    "author-name-typed-in-text",
    "author-in-text-without-author",
    "citation-repeated",
    "reference-id-shape",
    "reference-id-too-long",
    "min-references",
    "min-references-invalid",
    "reference-density-low",
    "reference-density-invalid",
    # content
    "todo-marker",
    "length-over-limit",
    "first-person-pronoun",
    "repeated-sentence-start",
    "email-address",
    "matriculation-number",
    "metadata-author-key",
    "confidentiality-marker",
    "hindsight-leakage",
    # the review beside the proposal
    "review-questions-changed",
)


# ---------- loading ----------------------------------------------------------

def load_structure(path: Path | None) -> dict:
    if path is None:
        path = Path(__file__).resolve().parent.parent / "references" / "structure.json"
    return json.loads(path.read_text(encoding="utf-8"))


# A workspace overrides a value by naming the key path it has in structure.json.
# One rule, no aliases — which only works if a key that resolves to nothing is
# reported rather than ignored, so both maps below exist to produce errors.
OVERRIDABLE = {
    ("references", "min_count"),
    ("references", "min_per_1000_words"),
    ("sections", "required"),
    ("forbidden", "heading_patterns"),
    ("timeline", "detail"),
    ("length", "page_limit"),
    ("paths", "proposals"),
    ("research_questions", "min_count"),
    ("research_questions", "max_count"),
}

RETIRED_KEYS = {
    "min_references": "[references] min_count",
    "page_limit": "[length] page_limit",
    "timeline_detail": "[timeline] detail",
    "required_sections": "[sections] required",
    "forbidden_sections": "[forbidden] heading_patterns",
}


def overridden(overrides: dict, table: str, key: str) -> bool:
    block = overrides.get(table)
    return isinstance(block, dict) and key in block


def setting(structure: dict, overrides: dict, table: str, key: str):
    """The workspace value if the workspace set that leaf, else the default."""
    if overridden(overrides, table, key):
        return overrides[table][key]
    return structure.get(table, {}).get(key)


BRANCH_KEYS = {"title", "subsections", "enabled"}


def branch_problem(branch: object) -> str | None:
    """Why this workspace methodology branch cannot be applied, or None.

    `guidance` is required per subsection here but absent from the shipped
    branches: those carry their content contract as prose in guidelines.md, and
    a workspace has no prose file to carry one. Without it the write skill would
    be inventing what belongs under a heading it has never seen.
    """
    if not isinstance(branch, dict):
        return "must be a table"
    unknown = sorted(set(branch) - BRANCH_KEYS)
    if unknown:
        return f"unknown key(s) {', '.join(unknown)}"
    if branch.get("enabled") is False:
        return None                                   # disabling needs nothing else
    title = branch.get("title")
    if not isinstance(title, dict) or not (title.get("en") and title.get("de")):
        return "needs a `title` with both `en` and `de`"
    subs = branch.get("subsections")
    if not isinstance(subs, list) or not subs:
        return "needs at least one subsection"
    for i, sub in enumerate(subs, 1):
        if not isinstance(sub, dict) or not (sub.get("en") and sub.get("de")):
            return f"subsection {i} needs both `en` and `de`"
        if not sub.get("guidance"):
            return (f"subsection {i} (`{sub['en']}`) needs `guidance` saying what "
                    "belongs in it — the shipped branches carry that as prose, "
                    "a workspace branch has nowhere else to put it")
    return None


def merge_methodologies(structure: dict, overrides: dict) -> dict:
    """Shipped branches with the workspace declaration applied, invalid ones out."""
    merged = dict(structure["methodologies"])
    for key, branch in (overrides.get("methodologies") or {}).items():
        if branch_problem(branch) is not None:
            continue
        if isinstance(branch, dict) and branch.get("enabled") is False:
            merged.pop(key, None)
        else:
            merged[key] = branch
    return merged


def override_key_findings(overrides: dict) -> list[Finding]:
    """Every override key that will not be honoured, named.

    A workspace whose overrides silently stopped applying is worse off than one
    that fails: the settings look present and do nothing. A typo and a retired
    key are the same failure seen from the user's side, so both are reported.
    """
    out = []
    for name, value in overrides.items():
        if name.startswith("_"):
            continue
        if name in RETIRED_KEYS:
            out.append(error(
                "override-key-retired",
                f"workspace override `{name}` was replaced by `{RETIRED_KEYS[name]}` — "
                "move it there; it is not applied as written",
            ))
        elif name == "methodologies":
            # keyed by branch id rather than by a fixed leaf set, so it is
            # validated by shape; one bad branch never invalidates the others
            out += [
                error("methodology-branch-invalid",
                      f"workspace methodology `{key}`: {problem} — branch not applied")
                for key, branch in (value or {}).items()
                if (problem := branch_problem(branch)) is not None
            ]
        elif not isinstance(value, dict):
            out.append(error("override-key-unknown",
                             f"unknown workspace override `{name}` — it is not applied"))
        else:
            out += [
                error("override-key-unknown",
                      f"unknown workspace override `[{name}] {leaf}` — it is not applied")
                for leaf in value
                if (name, leaf) not in OVERRIDABLE
            ]
    return out


def resolve_guidelines(proposal: Path, explicit: Path | None) -> Path | None:
    """The governing override file: an explicit path, else `guidelines.md`
    beside the proposal, in its folder, else in the working directory, which is
    the workspace root. The first file found governs the whole run;
    deliberately no ancestor search."""
    if explicit is not None:
        return explicit
    for candidate in (proposal.parent / "guidelines.md", Path.cwd() / "guidelines.md"):
        if candidate.exists():
            return candidate
    return None


# The governing file's chain position, as the report names it. By position
# only: a report relayed into a bug report must carry no directory name.
GOVERNING_LABELS = {
    "beside-proposal": "beside the proposal",
    "working-directory": "working directory",
    "explicit": "explicit",
    "none": "none (defaults)",
}


def governing_position(proposal: Path, explicit: Path | None) -> str:
    """Which chain position governed the run: a key of GOVERNING_LABELS. A run
    started inside the proposal's folder finds no root file, so it says none
    rather than leaving the defaults silent (skill-check: Governing override
    file named by position)."""
    if explicit is not None:
        return "explicit"
    found = resolve_guidelines(proposal, None)
    if found is None:
        return "none"
    return "beside-proposal" if found == proposal.parent / "guidelines.md" else "working-directory"


def load_overrides(proposal: Path, explicit: Path | None) -> dict:
    candidate = resolve_guidelines(proposal, explicit)
    if candidate is None or not candidate.exists():
        return {}
    match = re.search(r"```toml\n(.*?)```", candidate.read_text(encoding="utf-8"), re.DOTALL)
    if not match:
        return {}
    try:
        return tomllib.loads(match.group(1))
    except tomllib.TOMLDecodeError as exc:
        return {"_parse_error": str(exc)}


def paths_value_problem(value: object) -> str | None:
    """Why this [paths] proposals value cannot be applied, or None. The
    constraint is a relative directory inside the workspace: layout is
    workspace-internal, so a value must never reach outside the root."""
    if not isinstance(value, str) or not value.strip():
        return "must be a directory name"
    if value.startswith("~"):
        return "must not be home-anchored"
    if Path(value).is_absolute() or value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", value):
        return "must be relative, not absolute"
    if ".." in Path(value).parts:
        return "must stay inside the workspace (no `..`)"
    return None


def location_value(structure: dict, overrides: dict) -> tuple[str, list[Finding]]:
    """The proposal location relative to the workspace root, and the finding
    for a configured value that cannot be applied, which leaves the default."""
    default = structure.get("paths", {}).get("proposals", ".")
    if not overridden(overrides, "paths", "proposals"):
        return default, []
    value = overrides["paths"]["proposals"]
    problem = paths_value_problem(value)
    if problem is None:
        return value, []
    return default, [error(
        "paths-proposals-invalid",
        f"guidelines.md: [paths] proposals {problem}, not `{value}` — "
        "the default location applies",
    )]


@dataclass(frozen=True)
class Workspace:
    """Where the workspace findings are measured from (design D17 of
    adopt-proposal-folders): the root is the directory of an explicitly passed
    override file, else the working directory. Both paths are resolved."""

    root: Path
    location: Path
    prefix: str       # the location as a report names it: `proposals/`, or empty
    configured: str   # the applied [paths] proposals value, empty for the default
    explicit: bool = False  # the root is an explicitly passed override file's directory


def workspace(root: Path, value: str, configured: bool, explicit: bool = False) -> Workspace:
    root = root.resolve()
    shown = Path(value).as_posix().strip("/")
    prefix = "" if shown in ("", ".") else shown + "/"
    return Workspace(root, (root / value).resolve(), prefix, value if configured else "",
                     explicit)


def placement_findings(proposal: Path, ws: Workspace) -> list[Finding]:
    """`proposal` (resolved) is expected at `<location>/<slug>/<slug>.md`
    (skill-check: Proposal-location value validated, misplacement reported).
    A folder directly in the location named unlike its proposal is the
    half-finished rename, reported as such instead (skill-check: Proposal folder
    named by its slug). Skills honor only proposal folders in the location, so a
    proposal anywhere else fails loudly here instead of half the skills
    silently disagreeing."""
    stem, folder = proposal.stem, proposal.parent
    if folder.parent == ws.location and folder.name != stem:
        name = _shown(folder.name)
        return [error(
            "proposal-folder-mismatch",
            f"`{_shown(proposal.name)}` sits in the folder `{name}`, which is not named "
            f"after it: the folder and the file name are both the slug, so `{name}` "
            f"and `{_shown(stem)}` must agree — a rename moves the folder and the proposal "
            "file together; finish it by renaming one of the two",
        )]
    if proposal == ws.location / stem / f"{stem}.md":
        return []
    return [error("proposal-misplaced", misplacement_message(proposal, ws))]


def misplacement_message(proposal: Path, ws: Workspace) -> str:
    """Where the proposal is expected, and what to do about it. The root and
    the folder alone cannot tell every case apart, so the message names each
    reading it cannot rule out: a root named like the proposal is its folder
    when the agent changed into it, and a flat workspace from before the folder
    layout otherwise; a folder named after the proposal that sits deeper than
    the location is misplaced, or the check was started above the workspace
    root."""
    stem, folder = proposal.stem, proposal.parent
    slug = _shown(stem)
    configured = (f", the location guidelines.md sets with [paths] proposals = "
                  f"`{ws.configured}`" if ws.configured else "")
    head = (f"`{_shown(proposal.name)}` is not at `{ws.prefix}{slug}/{slug}.md`, relative "
            f"to the workspace root{configured}")
    if folder == ws.root and folder.name == stem:
        if ws.explicit:
            return head + (
                f" — the workspace root is the directory of the override file passed "
                f"explicitly, `{slug}/`, which is named like the proposal: if it is the "
                "proposal's folder, pass the workspace root's override file instead, or "
                "none; otherwise move the proposal into a folder of its own there")
        return head + (
            f" — the check ran from `{slug}/`, which is named like the proposal: if it is "
            "the proposal's folder, run the check from the workspace root; if it is the "
            "workspace root, move the proposal into a folder of its own there")
    if folder.name == stem:
        return head + (
            " — every proposal lives in a folder of its own named after it, directly in "
            "the proposal location: move the folder there, or, if the check was not "
            "started from the workspace root, run it from there")
    return head + (" — every proposal lives in a folder of its own named after it; move "
                   "the proposal and the files of its family there")


# ---------- workspace family -------------------------------------------------
#
# One vocabulary for the proposal family (proposal-file-format: One folder per
# proposal, Proposal family under one handle). Every proposal lives in a folder
# of its own, named by its slug. Files that leave the folder carry that handle
# (HANDLE_SUFFIXES); files that stay are named by their role (ROLE_NAMES) or by
# a free label. The roles are those of the table in
# shared/blocks/workspace-files.md, and an L0 test holds the two equal both
# ways. family_member() and proposal_folder() are pure; family_members()
# classifies a listing of location-relative paths and is what the harness's
# verdicts share, so no verdict classifies a file differently from the warning
# a writer sees.

SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
FAMILY_ROLES = (
    "proposal", "notes", "harvest record", "review", "supervisor feedback",
    "handout", "built output", "kept file", "figure",
)
PROPOSAL, NOTES, HARVEST, REVIEW, FEEDBACK, HANDOUT, BUILT, KEPT, FIGURE = FAMILY_ROLES
# files that stay in the folder, matched by their exact name: a kept
# `peer-review.md` is never the review
ROLE_NAMES = {NOTES: "notes.md", HARVEST: "harvest.md", REVIEW: "review.md",
              FEEDBACK: "feedback.md"}
BUILT_EXTENSIONS = frozenset({"pdf", "typ", "tex", "docx"})
# the hand-in export; mirrored from publish.py, a pin test keeps them equal
HANDOUT_SUFFIX = ".handout.md"
# files that leave the folder, by what follows the handle: the folder's own
# under its slug, or previous outputs under an earlier one
HANDLE_SUFFIXES = {".md": PROPOSAL, HANDOUT_SUFFIX: HANDOUT,
                   **{f".{ext}": BUILT for ext in sorted(BUILT_EXTENSIONS)}}
# the figures folder inside a proposal's folder; a figure is `img/<name>.<ext>`
FIGURE_FOLDER = "img"
FIGURES = FIGURE_FOLDER + "/"
# no kept file takes one of these labels, nor the folder's own slug
RESERVED_LABELS = frozenset({"notes", "review", "feedback", "harvest", "handout",
                             FIGURE_FOLDER})
# never a proposal folder, whatever it holds; hidden names never are either
RESERVED_FOLDERS = frozenset({"bug-report", FIGURE_FOLDER})
# a notes file with these five section headings, in any order, makes its folder
# a proposal folder before any proposal exists; read only to classify
NOTES_HEADINGS = ("Decisions", "Open Points", "Next Focus", "Excluded Literature", "Log")
NOTES_HEADING_RE = re.compile(r"^## +(.+?)[ \t]*$", re.MULTILINE)
# allowed at the workspace root; never family members (Working material stays
# out of the workspace). Hidden names are never classified at all, which covers
# .gitignore, the installers' skill folders and their install record.
WORKSPACE_LEVEL = frozenset({
    "guidelines.md", "api-keys.env", "bug-report",
    "check-output.txt", "version-output.txt", "skills-lock.json",
})
# Mirrored from publish.py, a pin test keeps them equal. By its name alone a
# recipe file is never a stray; as a build definition publish never uses, it
# counts only with the target, which is the one recipe read the check makes.
BUILD_STEM = "proposal-build"
RECIPE_NAMES = frozenset({"makefile", "gnumakefile", "justfile"})
RECIPE_TARGET_RE = re.compile(rf"^{BUILD_STEM}\b[^\n]*:", re.MULTILINE)
ORPHAN_CAUSE = ("a rename that moved only part of the family is the usual cause; "
                "a file you placed there on purpose can be left as it is")


def is_build_definition(name: str) -> bool:
    """A workspace build definition by its name, as publish.py looks it up: the
    stem, or a recipe name case-folded with a leading dot stripped."""
    return (name == BUILD_STEM or name.startswith(BUILD_STEM + ".")
            or name.lower().lstrip(".") in RECIPE_NAMES)


def workspace_allowed(name: str) -> bool:
    """Allowed in the workspace and never a family member: hidden, workspace-
    level, a build definition, or anything inside an allowed folder."""
    parts = name.rstrip("/").split("/")
    top = parts[0]
    return (any(part.startswith(".") for part in parts) or top in WORKSPACE_LEVEL
            or is_build_definition(top))


def is_slug(name: str) -> bool:
    """Slug-shaped: lowercase ASCII letters and digits joined by single
    hyphens, one word or more (`idea`, `idea-2`)."""
    return bool(SLUG_RE.fullmatch(name))


def notes_shaped(text: str) -> bool:
    """Whether a notes file carries the five section headings, in any order.
    Classification, not validation: nothing is reported about the headings."""
    found = {m.group(1) for m in NOTES_HEADING_RE.finditer(text)}
    return set(NOTES_HEADINGS) <= found


def proposal_folder(name: str, files: Collection[str],
                    read: Callable[[str], str | None]) -> bool:
    """Whether the folder `name`, holding `files` (names relative to it), is a
    proposal folder: slug-shaped, not reserved, and holding a proposal named
    after it, a harvest record, or a notes file with the five headings.
    `read(name)` gives a file's text, or None when it cannot; an unreadable
    notes file keeps the folder one, which keeps every warning quiet."""
    if not is_slug(name) or name in RESERVED_FOLDERS:
        return False
    if f"{name}.md" in files or ROLE_NAMES[HARVEST] in files:
        return True
    if ROLE_NAMES[NOTES] not in files:
        return False
    text = read(ROLE_NAMES[NOTES])
    return text is None or notes_shaped(text)


def _label(name: str, slug: str) -> bool:
    """A free label for a kept file in the folder `slug`/."""
    return is_slug(name) and name != slug and name not in RESERVED_LABELS


def family_member(name: str, slug: str) -> str | None:
    """The role of `name`, a path relative to the proposal folder `slug`/ (a
    subfolder as `name/`), or None when it is no family member: hidden,
    workspace-level and build files, reserved labels, unclassified names. A
    file named by any slug-shaped handle is the folder's own or a previous
    output; a markdown file under another slug is a kept file by its name."""
    if workspace_allowed(name):
        return None
    top, sep, rest = name.partition("/")
    if sep:
        if top == FIGURE_FOLDER:
            return FIGURE if rest and "/" not in rest else None
        return KEPT if _label(top, slug) else None
    role = next((role for role, role_name in ROLE_NAMES.items() if name == role_name), None)
    stem, dot, ext = name.partition(".")
    if role is not None or not dot or not is_slug(stem) or not all(ext.split(".")):
        return role
    handle = HANDLE_SUFFIXES.get("." + ext)
    if handle is not None and (handle != PROPOSAL or stem == slug):
        return handle
    return KEPT if _label(stem, slug) else None


def family_members(paths: Iterable[str], read: Callable[[str], str | None] | None = None
                   ) -> dict[str, tuple[str, str]]:
    """(slug, role) of every family member among `paths`, file paths relative to
    the proposal location: a file of a proposal folder that classifies as a
    member of it. A file at the location's root or in any other folder is none.
    `read(path)` gives a path's text, or None when it cannot; it is asked only
    about a folder's `notes.md`, and without it every such folder counts."""
    folders: dict[str, list[str]] = {}
    for path in paths:
        top, sep, rest = path.partition("/")
        if sep and rest:
            folders.setdefault(top, []).append(rest)
    members = {}
    for folder, files in folders.items():
        def text(name: str, folder: str = folder) -> str | None:
            return read(f"{folder}/{name}") if read is not None else None
        if not proposal_folder(folder, files, text):
            continue
        members.update({f"{folder}/{rel}": (folder, role) for rel in files
                        if (role := family_member(rel, folder)) is not None})
    return members


def _readable_name(name: str) -> bool:
    """A name that is not valid UTF-8 (surrogate-escaped on POSIX) can never be
    slug-shaped, and printing it would end the check with a traceback."""
    try:
        name.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _shown(name: str) -> str:
    """A name the listings did not filter, as a report may print it: the
    proposal's own file name and its folder's name come from the path the check
    was given, so one that is not valid UTF-8 keeps its readable part, the
    undecodable bytes replaced."""
    return os.fsencode(name).decode("utf-8", "replace")


def _entries(directory: Path) -> list[str]:
    """The names in `directory`, a folder as `name/`, hidden names left out;
    nothing for a directory that is missing or cannot be listed."""
    try:
        return sorted(e.name + "/" if e.is_dir() else e.name for e in directory.iterdir()
                      if _readable_name(e.name) and not e.name.startswith("."))
    except OSError:
        return []


def _text(path: Path) -> str | None:
    """A file's text for one of the classifying reads, None when it cannot be
    read: a file this script does not own must never break the check."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _reader(folder: Path) -> Callable[[str], str | None]:
    return lambda name: _text(folder / name)


def proposal_shaped(text: str) -> bool:
    """Opens with a `# ` title followed by an emphasized subtitle paragraph and
    ends in a metadata block: the proposal's own frame, which a kept list ending
    in a metadata block lacks (design Q5)."""
    body, meta = split_proposal(text)
    frame = parse_frame(body)
    return meta.found and frame.title_is_first and frame.subtitle_emphasized


def _orphan(path: str, why: str) -> Finding:
    return warn("companion-orphaned", f"`{path}` {why} — {ORPHAN_CAUSE}")


def _own_folder_findings(proposal: Path, ws: Workspace) -> list[Finding]:
    """Inside the checked proposal's folder: a second proposal, recognized by
    its frame, and a proposal folder moved into this one."""
    folder = proposal.parent
    own = _shown(folder.name)
    shown = f"{ws.prefix}{own}" if folder.parent == ws.location else own
    place = f"the proposal location `{ws.prefix}`" if ws.prefix else "the proposal location"
    checked = _shown(proposal.name)
    found = []
    for name in _entries(folder):
        if _nested_folder(folder, name):
            found.append(_orphan(
                f"{shown}/{name}", f"is a proposal folder inside the folder of "
                f"`{checked}`; proposal folders sit directly in {place}, so it "
                "belongs there"))
        elif _second_proposal(folder / name, proposal):
            found.append(_orphan(
                f"{shown}/{name}", f"opens and ends like a proposal but sits in the folder of "
                f"`{checked}`; a proposal lives in a folder of its own, "
                f"`{ws.prefix}{name.partition('.')[0]}/{name}`"))
    return found


def _nested_folder(folder: Path, name: str) -> bool:
    """A subfolder, `img/` aside, that is a proposal folder itself."""
    sub = name.removesuffix("/")
    return (name.endswith("/") and sub != FIGURE_FOLDER
            and proposal_folder(sub, _entries(folder / sub), _reader(folder / sub)))


def _second_proposal(path: Path, proposal: Path) -> bool:
    """A markdown file named by another slug that carries the proposal frame."""
    stem, _, ext = path.name.partition(".")
    return (ext == "md" and path != proposal and is_slug(stem)
            and stem not in RESERVED_LABELS and proposal_shaped(_text(path) or ""))


def _location_folders(ws: Workspace, own: Path) -> dict[str, bool]:
    """Each slug-shaped, unreserved folder of the location but the checked
    proposal's own, and whether it is a proposal folder."""
    out = {}
    for name in _entries(ws.location):
        folder = name.removesuffix("/")
        if (name.endswith("/") and is_slug(folder) and folder not in RESERVED_FOLDERS
                and ws.location / folder != own):
            path = ws.location / folder
            out[folder] = proposal_folder(folder, _entries(path), _reader(path))
    return out


def _unsheltered_findings(ws: Workspace, folders: dict[str, bool]) -> list[Finding]:
    """The unambiguous companions in a slug-shaped folder that is no proposal
    folder (design D19): what a rename that moved only part of a family leaves."""
    found = []
    for folder in sorted(name for name, sheltered in folders.items() if not sheltered):
        names = set(_entries(ws.location / folder))
        found += [
            _orphan(f"{ws.prefix}{folder}/{name}",
                    f"lies in `{ws.prefix}{folder}/`, which holds no proposal, notes file or "
                    "harvest record")
            for name in (ROLE_NAMES[REVIEW], ROLE_NAMES[FEEDBACK], folder + HANDOUT_SUFFIX)
            if name in names
        ]
    return found


ROOT_STRAYS = frozenset({ROLE_NAMES[REVIEW], ROLE_NAMES[FEEDBACK], ROLE_NAMES[HARVEST], FIGURES})


OUTSIDE = "outside any proposal folder"


def _root_stray(name: str, base: Path, sheltered: Collection[str], prefix: str) -> str | None:
    """What makes a name at a root a stray family file, as the tail of its
    warning, or None when it is none. A name that starts with a proposal
    folder's slug belongs in that folder; a markdown file under a slug counts
    when it ends in a metadata block, a notes file when it carries the five
    headings."""
    owner = max((slug for slug in sheltered if name.startswith(slug + ".")), key=len,
                default=None)
    if owner is not None:
        return f"and it belongs in the proposal folder `{prefix}{owner}/`"
    if name in ROOT_STRAYS:
        return OUTSIDE
    stem, _, ext = name.partition(".")
    if name == ROLE_NAMES[NOTES]:
        return OUTSIDE if notes_shaped(_text(base / name) or "") else None
    if not is_slug(stem) or ext not in ("md", HANDOUT_SUFFIX[1:]):
        return None
    if ext == "md":
        if not split_proposal(_text(base / name) or "")[1].found:
            return None
        return f"{OUTSIDE}; a proposal lives in a folder of its own, `{prefix}{stem}/{name}`"
    return OUTSIDE


def _root_findings(base: Path, proposal: Path, sheltered: Collection[str],
                   ws: Workspace) -> list[Finding]:
    """Family files at the location's root or the workspace root, where no
    proposal's file belongs."""
    at_root = base == ws.root
    shown = "" if at_root else ws.prefix
    where = "at the workspace root" if at_root else "at the root of the proposal location"
    found = []
    for name in _entries(base):
        if workspace_allowed(name) or base / name == proposal:
            continue
        tail = _root_stray(name, base, sheltered, ws.prefix)
        if tail is not None:
            found.append(_orphan(f"{shown}{name}", f"lies {where}, {tail}"))
    return found


def family_findings(proposal: Path, ws: Workspace) -> list[Finding]:
    """Orphaned companions around the checked proposal, `proposal` resolved
    (skill-check: Orphaned companions reported as a warning). Lists the
    proposal's folder and its subfolders, the location's root, the workspace
    root and the location's slug-shaped folders; changes nothing, and opens a
    file only for the frame, metadata-block and notes-headings tests. Called
    only for a proposal whose folder sits directly in the location
    (workspace_findings)."""
    found = _own_folder_findings(proposal, ws)
    folders = _location_folders(ws, proposal.parent)
    sheltered = {folder for folder, is_one in folders.items() if is_one}
    sheltered.add(proposal.parent.name)
    found += _unsheltered_findings(ws, folders)
    for base in dict.fromkeys((ws.location, ws.root)):
        found += _root_findings(base, proposal, sheltered, ws)
    return found


def build_definitions(directory: Path) -> list[str]:
    """The workspace build definitions in `directory`, recognized as publish.py
    recognizes one: `proposal-build` with or without an extension, or a recipe
    file that declares the `proposal-build` target. An unreadable recipe is
    none."""
    try:
        entries = sorted((e for e in directory.iterdir() if _readable_name(e.name)),
                         key=lambda e: e.name)
    except OSError:
        return []
    return [entry.name for entry in entries if entry.is_file() and (
        entry.name == BUILD_STEM or entry.name.startswith(BUILD_STEM + ".")
        or (entry.name.lower().lstrip(".") in RECIPE_NAMES
            and RECIPE_TARGET_RE.search(_text(entry) or "")))]


def build_findings(ws: Workspace) -> list[Finding]:
    """A build definition at the location's root or the workspace root, where
    publish never looks (skill-check: Unused build definitions reported).
    Called only for a proposal whose folder sits directly in the location, so
    neither root is that folder (workspace_findings)."""
    found = []
    for base in dict.fromkeys((ws.location, ws.root)):
        at_root = base == ws.root
        shown = "" if at_root else ws.prefix
        where = "at the workspace root" if at_root else "at the root of the proposal location"
        found += [warn(
            "build-definition-unused",
            f"`{shown}{name}` {where} is a build definition the publish step never uses: "
            "it looks for one only in the proposal's folder — copy it into each "
            "proposal folder that should be built with it",
        ) for name in build_definitions(base)]
    return found


def workspace_findings(proposal_path: Path, structure: dict, overrides: dict,
                       root: Path, explicit: bool = False) -> list[Finding]:
    """The location value, the proposal's placement, its orphaned companions
    and unused build definitions, all measured from `root`, which is an
    explicitly passed override file's directory when `explicit`. A proposal
    whose folder does not sit directly in the location is misplaced, or the
    check started somewhere other than the workspace root: either way the
    roots it would list are not known to be the workspace's, so only the
    placement error is reported, and the scans follow once it is fixed."""
    value, found = location_value(structure, overrides)
    configured = overridden(overrides, "paths", "proposals") and not found
    ws = workspace(root, value, configured, explicit)
    proposal = proposal_path.resolve()
    found += placement_findings(proposal, ws)
    if proposal.parent.parent != ws.location:
        return found
    return found + family_findings(proposal, ws) + build_findings(ws)


# ---------- narrow metadata extraction ---------------------------------------

class Metadata:
    def __init__(self) -> None:
        self.found = False
        self.blank_line_before = False
        # retired keys (title/subtitle/lang moved into the body; author never
        # belonged) — kept as evidence for the retired-key and legacy findings
        self.title: str | None = None
        self.has_subtitle_key = False
        self.has_lang_key = False
        self.reference_ids: list[str] = []
        # ids whose entry declares neither an author nor an editor: an
        # author-in-text citation of one renders as the quoted title
        self.reference_ids_without_names: set[str] = set()
        # surnames per id, to catch a name typed in the prose next to its
        # own citation — anchored to the cited entry, never to capitalization
        self.reference_surnames: dict[str, set[str]] = {}
        # top-level `author:` — the writer's own name, rendered on the title page
        self.has_author_key = False


def surnames_in(entry: str) -> set[str]:
    """Family/literal names of one reference entry, particles included.

    Block and inline flow style both occur in the wild, so the value is read
    up to the next comma, brace or newline rather than to end of line.
    """
    names = set()
    for m in re.finditer(r"(?:^|[\s{,])(family|literal):\s*([^\n,}]+)", entry, re.MULTILINE):
        name = m.group(2).strip().strip("'\"")
        if name:
            names.add(name)
    for m in re.finditer(r"non-dropping-particle:\s*([^\n,}]+)", entry):
        particle = m.group(1).strip().strip("'\"")
        names |= {f"{particle} {n}" for n in list(names)}
    return names


def name_precedes(prefix: str, surnames: set[str]) -> bool:
    """True when `prefix` ends with a surname of the reference about to be cited.

    Anchoring to that reference's own authors is what makes this usable: a
    general "capitalized word before a citation" rule flags every sentence
    ending in a proper noun. The optional tail covers the rendered forms a
    writer copies from a PDF — "Smith et al.", "Smith and Klein", "Smith und
    Klein".
    """
    for name in surnames:
        tail = r"(?:\s+(?:et\s+al\.?|and\s+\S+|und\s+\S+))?"
        if re.search(rf"(?:^|[^\w'-])({re.escape(name)}){tail}[\s(]*$", prefix):
            return True
    return False


def split_proposal(text: str) -> tuple[str, Metadata]:
    """Split body from the trailing metadata block; extract narrow fields."""
    meta = Metadata()
    lines = text.rstrip("\n").split("\n")
    delim = [i for i, line in enumerate(lines) if re.fullmatch(r"---\s*", line)]
    if len(delim) >= 2 and delim[-1] == len(lines) - 1:
        start, end = delim[-2], delim[-1]
        block = "\n".join(lines[start + 1 : end])
        if re.search(r"^\s*\w[\w-]*\s*:", block, re.MULTILINE):
            meta.found = True
            meta.blank_line_before = start > 0 and lines[start - 1].strip() == ""
            body = "\n".join(lines[:start])
            meta.has_lang_key = bool(re.search(r"^lang:", block, re.MULTILINE))
            meta.has_subtitle_key = bool(re.search(r"^subtitle:", block, re.MULTILINE))
            if m := re.search(r"^title:\s*(.+)$", block, re.MULTILINE):
                meta.title = m.group(1).strip().strip("'\"")
            # column 0 only: `author:` inside a reference entry is indented
            meta.has_author_key = bool(re.search(r"^author:", block, re.MULTILINE))
            refs = re.search(r"^references:\s*$(.*)", block, re.MULTILINE | re.DOTALL)
            if refs:
                entries = re.split(r"^\s*-\s+id:\s*", refs.group(1), flags=re.MULTILINE)[1:]
                for entry in entries:
                    first, _, rest = entry.partition("\n")
                    key = first.split()[0] if first.split() else ""
                    if not key:
                        continue
                    meta.reference_ids.append(key)
                    if not re.search(r"^\s+(author|editor):", rest, re.MULTILINE):
                        meta.reference_ids_without_names.add(key)
                    meta.reference_surnames[key] = surnames_in(rest)
            return body, meta
    return text, meta


# ---------- checks -----------------------------------------------------------

def headings(body: str) -> list[tuple[int, str]]:
    return [
        (len(m.group(1)), m.group(2).strip())
        for m in re.finditer(r"^(#{1,6})\s+(.+)$", body, re.MULTILINE)
    ]


# ---------- document frame ----------------------------------------------------
#
# The frame is the part of the body that is document, not section: the leading
# `# <title>` line and the emphasized subtitle paragraph beneath it. pandoc
# promotes the H1 to the document title only when it is the file's first block —
# anything above it silently demotes the heading to a paragraph — so the frame
# rules are what keep that promotion from failing invisibly.

@dataclass(frozen=True)
class Frame:
    title: str | None        # text of the first H1, wherever it sits
    title_is_first: bool     # the H1 is the file's first content line
    h1_count: int
    subtitle: str | None     # first paragraph line after the title, emphasis stripped
    subtitle_emphasized: bool


# a paragraph wrapped entirely in single-star emphasis — the one canonical
# subtitle spelling; `**bold**` and partial emphasis deliberately do not match
SUBTITLE_EMPHASIS = re.compile(r"\*(?!\*)(.+)(?<!\*)\*")


def parse_frame(body: str) -> Frame:
    lines = body.split("\n")
    h1s = [(i, m.group(1).strip())
           for i, line in enumerate(lines) if (m := re.match(r"#\s+(.+)$", line))]
    first_content = next((i for i, line in enumerate(lines) if line.strip()), None)
    title = h1s[0][1] if h1s else None
    title_is_first = bool(h1s) and h1s[0][0] == first_content
    subtitle = None
    emphasized = False
    if title_is_first:
        after = next((line.strip() for line in lines[h1s[0][0] + 1:] if line.strip()), None)
        if after is not None and not after.startswith("#"):
            if m := SUBTITLE_EMPHASIS.fullmatch(after):
                subtitle, emphasized = m.group(1).strip(), True
            else:
                subtitle = after
    return Frame(title=title, title_is_first=title_is_first, h1_count=len(h1s),
                 subtitle=subtitle, subtitle_emphasized=emphasized)


def infer_language(frame: Frame, head_texts: list[str], structure: dict) -> str | None:
    """Deterministic language inference: exact subtitle match first, then a
    majority of canonical section-title matches. None when neither decides."""
    wordings = structure["subtitle"]["wordings"]
    if frame.subtitle:
        for lang in ("en", "de"):
            if frame.subtitle in wordings[lang]:
                return lang
    titles = structure["sections"]["titles"]
    counts = {}
    for lang in ("en", "de"):
        canonical = {titles[key][lang] for key in titles if key != "methodology"}
        canonical.add(structure["references"]["section_title"][lang])
        prefix = titles["methodology"][lang].split("{")[0]
        counts[lang] = sum(1 for h in head_texts
                           if h in canonical or h.startswith(prefix))
    if counts["en"] != counts["de"]:
        return max(counts, key=counts.get)
    return None


def timeline_body_errors(section: str, title: str, max_lines: int) -> list[Finding]:
    """The timeline is one short sentence, not a work plan. Structure only:
    whether it names a real timeframe is left to the agent pass, which also
    sees a Gantt chart pasted in as an image."""
    # a bare `---` is a metadata delimiter or a rule, never timeline prose;
    # stop there so a malformed metadata block cannot leak reference entries in
    lines = []
    for line in section.split("\n"):
        if re.fullmatch(r"---\s*", line):
            break
        if line.strip():
            lines.append(line)
    out = []
    if any(re.match(r"\s*\|", line) for line in lines):
        out.append(error("timeline-table",
                         f"table in `{title}` — the timeline is one short sentence"))
    if any(re.match(r"\s*([-*+]|\d+[.)])\s", line) for line in lines):
        out.append(error("timeline-list",
                         f"list in `{title}` — the timeline is one short sentence"))
    if any(re.match(r"#{1,6}\s", line) for line in lines):
        out.append(error("timeline-subsection",
                         f"subsection in `{title}` — the timeline takes no work packages"))
    if len(lines) > max_lines:
        out.append(error("timeline-too-long",
                         f"`{title}` runs {len(lines)} lines — at most {max_lines} allowed"))
    return out


def title_warnings(title: str, cfg: dict, lang: str = "en") -> list[Finding]:
    """The thesis title is printed on the study certificate — every finding says
    so, because that rationale is what makes a heuristic warning worth acting on.
    Only the mechanical tells live here: whether a proper noun in the title names
    a tool, a product or a vendor is agent judgement, never data."""
    certificate = "the title is printed on the study certificate"
    stripped = unicodedata.normalize("NFC", title.strip())
    if not stripped or re.fullmatch(r"\[TODO:[^\]]*\]", stripped):
        return []  # no title yet: the todo-marker finding already covers it
    low = stripped.lower()
    out = []

    opener = next((o for o in cfg["implementation_openers"] if low.startswith(o)), None)
    if opener:
        out.append(warn(
            "title-implementation-opener",
            f"title opens with `{opener}` — implementation framing states building "
            f"work, not a contribution; {certificate}",
        ))

    hits = [w for w in cfg["buzzwords"] if w in low]
    if hits:
        out.append(warn(
            "title-buzzword",
            f"title carries {', '.join(f'`{w}`' for w in hits)} — marketing tone; "
            f"{certificate}",
        ))

    if stripped.endswith("?"):
        out.append(warn(
            "title-question-form",
            "title is phrased as a question — an academic title states its subject; "
            f"{certificate}",
        ))

    min_words = cfg["min_words"].get(lang, cfg["min_words"]["en"])
    words = len(stripped.split())
    if words < min_words:
        out.append(warn(
            "title-too-short",
            f"title runs {words} words — at least {min_words} expected; it has to name "
            f"a contribution and its object standing alone, without the subtitle, and "
            f"{certificate}",
        ))
    elif words > cfg["max_words"]:
        out.append(warn(
            "title-too-long",
            f"title runs {words} words — at most {cfg['max_words']} expected; "
            f"{certificate}",
        ))

    return out


@dataclass(frozen=True)
class Context:
    """Everything the rules read, derived once. Rules take this and return
    findings; none of them reads a file or mutates anything."""

    body: str
    meta: Metadata
    frame: Frame
    lang: str
    lang_determined: bool  # False when inference decided nothing and en is a fallback
    structure: dict
    overrides: dict
    methodologies: dict    # shipped set with the workspace declaration applied
    detail: str            # effective timeline mode after validation
    head_texts: list[str]  # section headings — the leading title H1 is excluded
    titles: dict
    meth_tpl: str
    meth_prefix: str
    meth_heads: list[str]
    required: list[str]


# ---------- rules ------------------------------------------------------------
#
# One function per rule family, each returning its findings. The registry at the
# bottom fixes report order, so the order is stated in one readable place rather
# than implied by where a block happens to sit in a 250-line procedure.


def leading_metadata_block(body: str) -> bool:
    """A `---` block at the very top — the layout every other markdown tool
    puts it in, and the one thing that explains an otherwise baffling report:
    with the block unparsed, every reference in it counts as undefined."""
    lines = body.split("\n")
    if not lines or not re.fullmatch(r"---\s*", lines[0]):
        return False
    close = next((i for i in range(1, len(lines)) if re.fullmatch(r"---\s*", lines[i])), 0)
    return bool(close) and bool(
        re.search(r"^\s*\w[\w-]*\s*:", "\n".join(lines[1:close]), re.MULTILINE))


def rule_metadata_present(ctx: Context) -> list[Finding]:
    if not ctx.meta.found:
        if leading_metadata_block(ctx.body):
            return [error("metadata-block-missing",
                          "the `---` metadata block sits at the top of the file — this "
                          "format puts it at the end, after the body; move it there "
                          "(every citation and reference finding below follows from this)")]
        return [error("metadata-block-missing",
                      "no trailing metadata block found (file must end with a `---` YAML block)")]
    if not ctx.meta.blank_line_before:
        return [error("metadata-block-blank-line",
                      "no blank line before the trailing `---` block "
                      "(pandoc will treat it as body text)")]
    return []


def rule_reference_id_syntax(ctx: Context) -> list[Finding]:
    if not ctx.meta.found:
        return []
    out = [
        error("reference-id-boolean-literal",
              f"reference id `{rid}` is a YAML boolean literal — rename or quote it")
        for rid in ctx.meta.reference_ids if rid.lower() in BOOLEAN_LITERALS
    ]
    dupes = {r for r in ctx.meta.reference_ids if ctx.meta.reference_ids.count(r) > 1}
    out += [error("duplicate-reference-id", f"duplicate reference id `{rid}`")
            for rid in sorted(dupes)]
    return out


def rule_single_metadata_block(ctx: Context) -> list[Finding]:
    if not ctx.meta.found:
        return []
    body_lines = ctx.body.split("\n")
    delims = [i for i, line in enumerate(body_lines) if re.fullmatch(r"---\s*", line)]
    for a, b in pairwise(delims):
        block = "\n".join(body_lines[a + 1 : b])
        if re.search(r"^\s*\w[\w-]*\s*:", block, re.MULTILINE):
            return [error("metadata-block-multiple",
                          "additional metadata block found before the trailing one — "
                          "exactly one trailing block allowed")]
    return []


def rule_heading_style(ctx: Context) -> list[Finding]:
    """Word and LibreOffice exports underline their headings instead of
    prefixing them. Pandoc reads that as a heading and the section rules do
    not, so without this the report is five "required section missing" errors
    on a document whose sections are all present and correctly named."""
    if ctx.head_texts:
        return []
    lines = ctx.body.split("\n")
    underlined = [
        lines[i - 1].strip() for i, line in enumerate(lines)
        if i and re.fullmatch(r"(=|-|~){3,}\s*", line) and lines[i - 1].strip()
        and not re.match(r"\s*\w[\w-]*\s*:", lines[i - 1])
    ]
    if not underlined:
        return []
    return [error("heading-style-setext",
                  f"headings are underlined (`{underlined[0]}` over `===` or `---`) rather "
                  f"than prefixed with `#` — convert all {len(underlined)} to `#` headings; "
                  f"the section rules below cannot see them")]


def rule_retired_keys(ctx: Context) -> list[Finding]:
    """title/subtitle/lang left the metadata block for the body. Warning class,
    like `author`: a student feeding the file to bare pandoc may set `lang`
    deliberately, and then this finding is expected notice, not breakage."""
    if not ctx.meta.found:
        return []
    retired = [
        ("title", ctx.meta.title is not None, "the leading `# ` line"),
        ("subtitle", ctx.meta.has_subtitle_key, "the emphasized paragraph under the title"),
        ("lang", ctx.meta.has_lang_key, "inference from the subtitle and section titles"),
    ]
    return [
        warn("retired-metadata-key",
             f"metadata key `{key}:` is retired — its place is {home}; remove the key")
        for key, present, home in retired if present
    ]


def rule_legacy_format(ctx: Context) -> list[Finding]:
    """The retired layout of this very toolchain: title in the metadata block,
    canonical sections at H1. Without this the report is a cascade of missing
    sections and flagged keys that never names what actually happened."""
    if ctx.meta.title is None or ctx.frame.h1_count < 2:
        return []
    return [error(
        "legacy-format",
        f"this file uses the retired layout (title in the metadata block, sections "
        f"as `# ` headings) — move `{ctx.meta.title}` to a leading `# ` line, demote "
        f"every section heading one level, and end the body with the references "
        f"heading (the findings below follow from the old layout)",
    )]


def rule_frame(ctx: Context) -> list[Finding]:
    """The leading `# <title>` line must be the file's first content line and its
    only H1 — pandoc promotes it to the document title only in that position and
    silently demotes it to a plain paragraph otherwise, which builds a document
    with no title and no error."""
    frame = ctx.frame
    if frame.h1_count == 0:
        return [error("title-line-missing",
                      "no `# <title>` line found — the file opens with the thesis "
                      "title as its only `# ` heading")]
    out = []
    if not frame.title_is_first:
        out.append(error(
            "title-not-first",
            f"content precedes the `# {frame.title}` line — the title must be the "
            f"file's first content line, or the build silently produces a document "
            f"without a title"))
    if frame.h1_count > 1:
        out.append(error(
            "multiple-h1",
            f"{frame.h1_count} `# ` headings found — the title is the only H1; "
            f"sections use `## `"))
    if frame.title_is_first and frame.h1_count == 1:
        if frame.subtitle is None:
            out.append(error(
                "subtitle-missing",
                "no subtitle paragraph under the title — expected e.g. "
                "`*Master's Thesis Proposal*` as the first paragraph"))
        elif not frame.subtitle_emphasized:
            out.append(error(
                "subtitle-not-emphasized",
                f"subtitle `{frame.subtitle}` is not wrapped in `*…*` emphasis — "
                f"write it as `*{frame.subtitle}*`"))
    return out


def rule_references_section(ctx: Context) -> list[Finding]:
    """The body ends with an empty references heading: the rendered bibliography
    lands beneath it, and the raw file gains a visible marker that the trailing
    block is the bibliography database."""
    ref_title = ctx.structure["references"]["section_title"][ctx.lang]
    if ref_title not in ctx.head_texts:
        return [error("references-section-missing",
                      f"closing references section missing — end the body with "
                      f"`## {ref_title}` above the metadata block")]
    out = []
    if ctx.head_texts[-1] != ref_title:
        out.append(error("references-section-not-last",
                         f"`{ref_title}` is not the last section — it closes the body"))
    if section_text(ctx.body, ref_title).strip():
        out.append(error("references-section-not-empty",
                         f"`{ref_title}` carries content — the section stays empty; "
                         f"entries live in the metadata block and the build renders "
                         f"them here"))
    return out


def rule_language(ctx: Context) -> list[Finding]:
    if ctx.lang_determined:
        return []
    return [warn("language-undeterminable",
                 "language could not be inferred — neither the subtitle nor a "
                 "majority of section titles matches the English or German "
                 "canonical wordings; findings assume English")]


def rule_title(ctx: Context) -> list[Finding]:
    if not ctx.frame.title_is_first:
        return []
    return title_warnings(ctx.frame.title, ctx.structure["title"], ctx.lang)


def rule_timeline_mode(ctx: Context) -> list[Finding]:
    """`ctx.detail` has already fallen back to the default; this reports the
    value that caused the fallback, in its place in the report."""
    timeline_cfg = ctx.structure["timeline"]
    declared = setting(ctx.structure, ctx.overrides, "timeline", "detail")
    if declared in timeline_cfg["detail_modes"]:
        return []
    return [error("timeline-detail-unknown",
                  f"guidelines.md: unknown [timeline] detail `{declared}` — must be one of: "
                  f"{', '.join(timeline_cfg['detail_modes'])}")]


def rule_required_sections(ctx: Context) -> list[Finding]:
    return [
        error("required-section-missing", f"required section missing: `{title}`")
        for title in ctx.required if not any(h == title for h in ctx.head_texts)
    ]


def rule_section_order(ctx: Context) -> list[Finding]:
    # An overridden required-section list carries its own order; otherwise the
    # canonical order applies, with the methodology matched by title prefix
    # because its heading is a template.
    if overridden(ctx.overrides, "sections", "required"):
        expected = [(t, t, False) for t in ctx.required]
    else:
        expected = [
            (ctx.titles[key][ctx.lang],
             ctx.meth_prefix if key == "methodology" else ctx.titles[key][ctx.lang],
             key == "methodology")
            for key in ctx.structure["sections"]["order"]
        ]
    positions = []
    for label, needle, by_prefix in expected:
        idx = next(
            (i for i, h in enumerate(ctx.head_texts)
             if (h.startswith(needle) if by_prefix else h == needle)),
            None,
        )
        if idx is not None:
            # name the heading as written, not the `{methodology}` template
            positions.append((idx, ctx.head_texts[idx] if by_prefix else label))
    return [
        error("section-out-of-order", f"section out of order: `{cur}` before `{prev}`")
        for (prev_i, prev), (cur_i, cur) in pairwise(positions) if cur_i < prev_i
    ]


def rule_timeline_size(ctx: Context) -> list[Finding]:
    """The detailed mode is the escape hatch for a program that mandates a work
    plan, so the size guard only applies to the simple mode."""
    if ctx.detail != "simple":
        return []
    tl_title = ctx.titles["timeline"][ctx.lang]
    return timeline_body_errors(
        section_text(ctx.body, tl_title), tl_title,
        ctx.structure["timeline"]["max_body_lines"],
    )


def rule_methodology(ctx: Context) -> list[Finding]:
    """Canonical mode only: an overridden section list replaces the closed set."""
    if overridden(ctx.overrides, "sections", "required"):
        return []
    methodologies = ctx.methodologies
    meth_names = {m["title"][ctx.lang]: key for key, m in methodologies.items()}
    if not ctx.meth_heads:
        return [error("methodology-missing", f"methodology section missing (`{ctx.meth_tpl}`)")]
    if len(ctx.meth_heads) > 1:
        return [error("methodology-multiple",
                      "multiple methodology sections — exactly one methodology allowed")]
    chosen = ctx.meth_heads[0][len(ctx.meth_prefix):].strip()
    if chosen not in meth_names:
        return [error("methodology-unknown",
                      f"unknown methodology `{chosen}` — must be one of: "
                      f"{', '.join(sorted(meth_names))}")]
    return [
        error("methodology-subsection-missing",
              f"methodology subsection missing: `{sub[ctx.lang]}`")
        for sub in methodologies[meth_names[chosen]]["subsections"]
        if sub[ctx.lang] not in ctx.head_texts
    ]


def rule_forbidden_sections(ctx: Context) -> list[Finding]:
    forbidden = [p.lower() for p in
                 setting(ctx.structure, ctx.overrides, "forbidden", "heading_patterns")]
    if ctx.detail == "detailed":
        work_plan = {p.lower() for p in ctx.structure["forbidden"]["work_plan_patterns"]}
        forbidden = [p for p in forbidden if p not in work_plan]
    out = []
    for h in ctx.head_texts:
        for pattern in forbidden:
            if pattern in h.lower():
                out.append(error("forbidden-section",
                                 f"forbidden section: `{h}` (matches `{pattern}`)"))
                break
    return out


# ---------- research questions ------------------------------------------------
#
# One definition of "one research question", shared by the count rule and the
# review-currency comparison: an item starts at an unindented list marker and
# runs to the next one, a blank line, a heading or the section's end. Indented
# lines, nested list items included, continue it, and so does a lazy unindented
# line. The proposal side accepts ordered markers only; a review's record of
# the questions it judged also accepts bullets.

ORDERED_MARKER = re.compile(r"\d+[.)](?:\s|$)")
ANY_MARKER = re.compile(r"(?:\d+[.)]|[-*+])(?:\s|$)")
HEADING_LINE = re.compile(r"#{1,6}\s")
# `---`, `* * *`, `___`: tested before ANY_MARKER, which `* * *` would match
THEMATIC_BREAK = re.compile(r" {0,3}([-*_])(?:[ \t]*\1){2,}[ \t]*$")

# typographic variants an agent, an editor or a chat window swaps without
# changing what is asked: curly, low-9 and reversed single and double quotes;
# hyphen, non-breaking hyphen (NFKC already turns it into the hyphen), en dash,
# em dash and minus sign
QUOTE_DASH_FOLD = {
    **dict.fromkeys((0x2018, 0x2019, 0x201A, 0x201B), "'"),
    **dict.fromkeys((0x201C, 0x201D, 0x201E, 0x201F), '"'),
    **dict.fromkeys((0x2010, 0x2011, 0x2013, 0x2014, 0x2212), "-"),
}


def list_items(section: str, bullets: bool = False) -> list[str]:
    """The items of a section's unindented list, each with its continuation
    lines, marker removed and lines joined by newlines."""
    marker = ANY_MARKER if bullets else ORDERED_MARKER
    items: list[list[str]] = []
    current: list[str] | None = None
    for line in section.split("\n"):
        if m := marker.match(line):
            current = [line[m.end():]]
            items.append(current)
        elif not line.strip() or HEADING_LINE.match(line):
            current = None
        elif current is not None:
            current.append(line)
    return ["\n".join(parts) for parts in items]


def normalize_question(text: str) -> str:
    """A question as the currency comparison reads it: invisible format
    characters removed (category Cf: soft hyphen, zero-width space, word
    joiner, byte-order mark), compatibility forms normalized, whitespace
    collapsed, quote and dash variants folded. Letter case, wording and every
    other punctuation mark still count. The removal comes first: `split` sees
    no whitespace in those characters, and NFKC never produces one."""
    visible = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return " ".join(unicodedata.normalize("NFKC", visible).split()).translate(QUOTE_DASH_FOLD)


def research_questions(ctx: Context) -> list[str]:
    """The questions the proposal declares: the ordered-list items of its
    canonical research-questions section."""
    return list_items(section_text(ctx.body, ctx.titles["research_questions"][ctx.lang]))


def rule_research_questions(ctx: Context) -> list[Finding]:
    rq_title = ctx.titles["research_questions"][ctx.lang]
    rq_section = section_text(ctx.body, rq_title)
    meth_section = section_text(ctx.body, ctx.meth_heads[0]) if ctx.meth_heads else ""
    rq_items = research_questions(ctx)
    out = []
    if rq_section and not rq_items:
        out.append(error(
            "research-questions-not-a-list",
            "no ordered-list research questions found in the research-questions section",
        ))
    # .get(): an older structure file, or a workspace that clears the key,
    # disables the bound rather than crashing the whole check.
    rq_max = setting(ctx.structure, ctx.overrides, "research_questions", "max_count")
    if rq_max and len(rq_items) > rq_max:
        out.append(error(
            "research-questions-too-many",
            f"{len(rq_items)} research questions — at most {rq_max} allowed",
        ))
    out += [
        error("research-question-unreferenced",
              f"(RQ{n}) never referenced in the methodology section")
        for n in range(1, len(rq_items) + 1)
        if meth_section and f"(RQ{n})" not in meth_section
    ]
    return out


# ---------- review currency ---------------------------------------------------
#
# A review closes on a record of the research questions it judged (skill-review:
# research questions recorded in the review). The check compares that record
# with the questions the proposal declares now and warns when they differ. It
# reads the review and never writes to it; a review without a record, or one it
# cannot read, gives no finding.

RQ_RECORD_TITLES = ("Research questions reviewed", "Begutachtete Forschungsfragen")
RQ_RECORD_HEADING = re.compile(
    r"^#{1,6}[ \t]+(?:" + "|".join(map(re.escape, RQ_RECORD_TITLES)) + r")[ \t]*$",
    re.MULTILINE | re.IGNORECASE)


def review_path(proposal: Path) -> Path:
    """The review file the review skill writes for this proposal: the `review`
    entry of the family's role table, in the proposal's folder; the one place
    this script derives its name. It follows the folder whatever the
    proposal's name, so a stem that is not a slug, such as `My Proposal`, has
    its review read too."""
    return proposal.parent / ROLE_NAMES[REVIEW]


def rq_record_end(review: str, start: int) -> int:
    """Where a record whose heading ends at `start` ends: with its first list,
    at the next heading, at a thematic break, or at the first line after a
    blank line that is neither a list item nor indented. Notes below the
    record, bullets included, are therefore no recorded questions."""
    pos, listed, after_blank = start, False, False
    for line in review[start:].split("\n"):
        if HEADING_LINE.match(line) or THEMATIC_BREAK.match(line):
            return pos
        if ANY_MARKER.match(line):
            listed = True
        elif listed and after_blank and line.strip() and not line[0].isspace():
            return pos
        after_blank = not line.strip()
        pos += len(line) + 1
    return len(review)


def rq_record_spans(review: str) -> list[tuple[int, int, int]]:
    """(heading start, list start, end) of every research-questions record in
    a review, each ending with its first list (rq_record_end)."""
    return [(m.start(), m.end(), rq_record_end(review, m.end()))
            for m in RQ_RECORD_HEADING.finditer(review)]


def recorded_questions(review: str) -> list[str] | None:
    """The questions the last record lists — the record closes the file, so a
    review pasted in above it does not win. None when there is no record."""
    spans = rq_record_spans(review)
    if not spans:
        return None
    _, start, end = spans[-1]
    return list_items(review[start:end], bullets=True)


def question_changes(recorded: list[str], current: list[str]) -> list[tuple[int, str]]:
    """Each position where the two lists differ, as (position, kind): `changed`,
    `added` (the proposal has it, the record not) or `removed` (the reverse).
    Data, not text: the finding words it, and no consumer parses that wording."""
    out = []
    for n in range(1, max(len(recorded), len(current)) + 1):
        if n > len(recorded):
            out.append((n, "added"))
        elif n > len(current):
            out.append((n, "removed"))
        elif normalize_question(recorded[n - 1]) != normalize_question(current[n - 1]):
            out.append((n, "changed"))
    return out


def review_findings(proposal_path: Path, ctx: Context) -> list[Finding]:
    """`review-questions-changed` when the review's record differs from the
    questions the proposal declares. Positions only, never a question's text,
    so a report that leaves the workspace carries no proposal wording through
    it. A review that cannot be read is silent: this script runs inside six
    skills, and a file it does not own must never break them."""
    path = review_path(proposal_path)
    try:
        review = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    recorded = recorded_questions(review)
    current = research_questions(ctx)
    changes = question_changes(recorded, current) if recorded and current else []
    if not changes:
        return []
    named = ", ".join(f"RQ{n} {kind}" for n, kind in changes)
    return [warn("review-questions-changed",
                 f"`{path.name}` judged research questions that differ from the current "
                 f"ones ({named}) — the review may describe an earlier version of the "
                 "proposal; a fresh review replaces it, so leave the review file as it is")]


def mask_code(body: str) -> str:
    """Blank fenced blocks and inline code spans, preserving every offset.

    A proposal about Java writes `@Override`, and a scanner reading any `@Word`
    as a citation key calls that an undefined reference. Masking gives the
    student a markup fix — backticks, or a `\\@` escape — where the alternative
    was rewriting correct terminology to satisfy a wrong finding. Characters
    become spaces rather than disappearing so line numbers and the prefix a
    typed-name check reads stay the ones in the file.
    """
    out = []
    fence = ""
    for line in body.split("\n"):
        if m := re.match(r"\s*(`{3,}|~{3,})", line):
            marker = m.group(1)[0]
            fence = "" if fence == marker else (fence or marker)
            out.append("")
        elif fence:
            out.append("")
        else:
            out.append(re.sub(r"(`+)[^`]*\1", lambda m: " " * len(m.group(0)), line))
    return "\n".join(out)


# An `@` that no word character, period or backslash precedes, then the key:
# the period keeps e-mail addresses out, the backslash is the escape a student
# uses for an at-sign that is not a citation.
CITATION_KEY = re.compile(r"(?<![\w.\\])@([A-Za-z][\w:.-]*)")


def scan_citations(ctx: Context) -> tuple[dict[str, int], dict[str, int],
                                          list[tuple[str, int, bool]]]:
    """(cited, author-in-text, typed names) with the line each first occurred on."""
    cited: dict[str, int] = {}
    author_in_text: dict[str, int] = {}
    typed_names: list[tuple[str, int, bool]] = []
    for lineno, line in enumerate(mask_code(ctx.body).split("\n"), start=1):
        # a key inside a bracketed group renders as a bare number; one outside
        # is author-in-text and gets an author label prefixed
        depth = 0
        for m in re.finditer(r"\[|\]|" + CITATION_KEY.pattern, line):
            if m.group(0) == "[":
                depth += 1
            elif m.group(0) == "]":
                depth = max(0, depth - 1)
            else:
                key = m.group(1).rstrip(".,;:")
                cited.setdefault(key, lineno)
                if depth == 0:
                    author_in_text.setdefault(key, lineno)
                prefix = line[:m.start()].rstrip().removesuffix("[").rstrip()
                if name_precedes(prefix, ctx.meta.reference_surnames.get(key, set())):
                    typed_names.append((key, lineno, depth > 0))
    return cited, author_in_text, typed_names


def rule_citations(ctx: Context) -> list[Finding]:
    cited, author_in_text, typed_names = scan_citations(ctx)
    defined = set(ctx.meta.reference_ids)
    out = [
        error("citation-undefined",
              f"cited key `@{key}` not defined in references (line {cited[key]}) — "
              f"if it is code rather than a citation, mark it as code or escape it `\\@{key}`")
        for key in sorted(set(cited) - defined)
    ]
    out += [
        warn("reference-uncited",
             f"reference `{key}` defined but never cited — cite it where a claim rests on it, "
             f"or remove the entry; never add a sentence so that it is cited")
        for key in sorted(defined - set(cited))
    ]
    for key, lineno, bracketed in typed_names:
        if bracketed:
            out.append(warn(
                "author-name-typed-bracketed",
                f"author name typed before `[@{key}]` (line {lineno}) — the name is a copy "
                f"that stops tracking the entry; write `@{key}` alone instead",
            ))
        else:
            out.append(warn(
                "author-name-typed-in-text",
                f"author name typed before `@{key}` (line {lineno}) — it renders twice "
                f"(\"Smith et al. Smith et al. [1]\"); write `@{key}` alone",
            ))
    out += [
        warn("author-in-text-without-author",
             f"`@{key}` is cited author-in-text but its reference declares no author or editor "
             f"(line {author_in_text[key]}) — it renders as the quoted title; "
             f"use `[@{key}]` instead")
        for key in sorted(set(author_in_text) & ctx.meta.reference_ids_without_names)
    ]
    return out


def rule_reference_id_shape(ctx: Context) -> list[Finding]:
    """Key shape: AuthorYearFirstWord, e.g. Smith26Deep. An eval produced
    `RiveraYearSurvey` — the literal word "Year" where the year belongs — and
    nothing caught it. Warning class: an unusual author name can legitimately
    produce an unusual key, and the proposal still resolves."""
    out = []
    for rid in sorted(set(ctx.meta.reference_ids)):
        if rid.lower() in BOOLEAN_LITERALS:
            continue  # already an error; one complaint per key is enough
        if not re.fullmatch(r"[A-Za-z][A-Za-z]*\d{2}[A-Za-z]+", rid):
            out.append(warn(
                "reference-id-shape",
                f"reference id `{rid}` does not follow `AuthorYearFirstWord` "
                f"(e.g. `Smith26Deep`) — a two-digit year between name and title word",
            ))
        elif len(rid) >= KEY_MAX_LEN:
            out.append(warn(
                "reference-id-too-long",
                f"reference id `{rid}` is {len(rid)} characters — "
                f"keep keys under {KEY_MAX_LEN}",
            ))
    return out


def rule_min_references(ctx: Context) -> list[Finding]:
    defined = set(ctx.meta.reference_ids)
    min_refs = setting(ctx.structure, ctx.overrides, "references", "min_count")
    out = []
    if isinstance(min_refs, bool) or not isinstance(min_refs, int) or min_refs < 0:
        # same degradation as an unknown [timeline] detail: report, use default —
        # a negative value would silently disable the check
        out.append(error(
            "min-references-invalid",
            f"guidelines.md: [references] min_count must be a non-negative integer, "
            f"not `{min_refs}`",
        ))
        min_refs = ctx.structure["references"]["min_count"]
    if len(defined) < min_refs:
        out.append(error("min-references",
                         f"only {len(defined)} references — at least {min_refs} required"))
    return out


def bad_density(value: object) -> bool:
    """True when a value cannot drive the density expectation: wrong type,
    negative, or non-finite. `isfinite` only ever sees a float here — handing
    it a huge TOML integer would overflow the implicit conversion and crash
    the report this function exists to protect."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return True
    if isinstance(value, float) and not math.isfinite(value):
        return True
    return value < 0


def rule_reference_density(ctx: Context) -> list[Finding]:
    """The floor catches an empty bibliography; this scales with the document.

    The expectation derives from coverage, not a quota — see the guidance's
    Literature section — so it grows with the body's actual length: a short
    draft is never nagged, and a workspace with a larger page limit gets the
    scaled expectation without a second override.
    """
    default = ctx.structure.get("references", {}).get("min_per_1000_words")
    density = setting(ctx.structure, ctx.overrides, "references", "min_per_1000_words")
    if density is None:
        return []  # structure predates the constant, no override: advisory off
    out = []
    if bad_density(density):
        # degrade like a bad page_limit: report, use the default — 0 is valid
        # here (a program may opt out of the advisory), a negative is not
        out.append(error(
            "reference-density-invalid",
            f"guidelines.md: [references] min_per_1000_words must be a "
            f"finite non-negative number, not `{density}`",
        ))
        density = default if not bad_density(default) else 0
    floor = setting(ctx.structure, ctx.overrides, "references", "min_count")
    if isinstance(floor, bool) or not isinstance(floor, int) or floor < 0:
        floor = ctx.structure["references"]["min_count"]  # its own rule reports this
    defined = len(set(ctx.meta.reference_ids))
    if defined < floor:
        return out  # the floor error already names this defect; one finding per defect
    # one reference per word is where meaning ends: the cap keeps an absurd yet
    # finite density (1e308 is a valid TOML float) from overflowing the ceil
    density = min(density, 1000)
    words = body_words(ctx)
    # the epsilon round keeps IEEE noise (12500 * 4.4 / 1000 lands a hair above
    # 55) from demanding one reference more than the configured density
    expected = math.ceil(round(words * density / 1000, 9))
    if defined < expected:
        out.append(warn(
            "reference-density-low",
            f"{defined} references for ~{words} body words — the coverage "
            f"this length asks for needs at least {density:g} per 1000 words "
            f"({expected} here): ground each thematic cluster and research "
            f"question in the literature",
        ))
    return out


def rule_todo_markers(ctx: Context) -> list[Finding]:
    return [warn("todo-marker", f"open {todo}")
            for todo in re.findall(ctx.structure["todo"]["marker"], ctx.body)]


def body_words(ctx: Context) -> int:
    """The one definition of 'body words': the length estimate and the
    reference-density expectation must never disagree about it."""
    return sum(
        len(line.split())
        for line in ctx.body.split("\n")
        if line.strip() and not line.lstrip().startswith("#")
    )


def rule_length(ctx: Context) -> list[Finding]:
    """Estimated from word count: markdown has no pages."""
    length_cfg = ctx.structure.get("length")
    if not length_cfg:
        return []
    out = []
    page_limit = setting(ctx.structure, ctx.overrides, "length", "page_limit")
    if (
        isinstance(page_limit, bool)
        or not isinstance(page_limit, (int, float))
        or not math.isfinite(page_limit)
        or page_limit <= 0
    ):
        # a quoted, negative, or non-finite value must degrade like any other
        # bad override, never crash the report or silently disable the rule
        out.append(error(
            "page-limit-invalid",
            f"guidelines.md: [length] page_limit must be a positive number, "
            f"not `{page_limit}`",
        ))
        page_limit = length_cfg["page_limit"]
    words = body_words(ctx)
    estimated = words / length_cfg["words_per_page"]
    if estimated > page_limit:
        out.append(warn(
            "length-over-limit",
            f"estimated length ~{estimated:.1f} pages ({words} words at "
            f"{length_cfg['words_per_page']} words/page) exceeds the "
            f"{page_limit}-page limit — an estimate, not a rendered count; "
            f"delete low-information sentences rather than compressing wording",
        ))
    return out


# `Type I error` is required vocabulary in the Controlled Experiment contract,
# and `Phase I` reads the same way: a lone capital I behind a capitalised word
# is a Roman-numeral label, never the pronoun.
ROMAN_LABEL = re.compile(r"\b[A-Z][a-z]+ I\b")


def blank(m: re.Match) -> str:
    return " " * len(m.group(0))


def at(body: str, m: re.Match) -> str:
    """`(line N)` for a match in `body`. Every warning in the prose-pattern
    class carries one: without it, dismissing a false positive means reading
    the whole file to find what tripped it."""
    lineno = body.count("\n", 0, m.start()) + 1
    return f"(line {lineno})"


def rule_prose_patterns(ctx: Context) -> list[Finding]:
    out = []
    fp = (r"\b(I|[Ww]e|[Mm]y|[Oo]ur)\b" if ctx.lang == "en"
          else r"\b([Ii]ch|[Ww]ir|[Mm]ein\w*|[Uu]nser\w*)\b")
    if fps := list(re.finditer(fp, ROMAN_LABEL.sub(blank, ctx.body))):
        out.append(warn("first-person-pronoun",
                        f"first-person pronouns found ({len(fps)}×) — first "
                        f"`{fps[0].group(0)}` {at(ctx.body, fps[0])}; use third person"))
    for start_word in repeated_sentence_starts(ctx.body):
        out.append(warn("repeated-sentence-start",
                        f"three consecutive sentences start with `{start_word}`"))
        break
    if m := re.search(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", ctx.body):
        out.append(warn("email-address",
                        f"email address found {at(ctx.body, m)} — personal data is forbidden"))
    if m := (re.search(r"\b(matriculation|matrikel)\w*", ctx.body, re.IGNORECASE)
             or re.search(r"(?<!\d)\d{7,8}(?!\d)", ctx.body)):
        out.append(warn("matriculation-number",
                        f"possible matriculation number / personal data: "
                        f"`{m.group(0)}` {at(ctx.body, m)}"))
    if ctx.meta.has_author_key:
        # the exception (a program requiring a named title page) is declared in
        # workspace guidance prose, which is not machine-readable — so warn always
        out.append(warn(
            "metadata-author-key",
            "`author:` found — proposals are anonymous by default; remove it "
            "unless your program requires a named cover page",
        ))
    for pattern in ctx.structure["forbidden"]["confidentiality_patterns"]:
        if m := re.search(rf"\b{re.escape(pattern)}\b", ctx.body, re.IGNORECASE):
            out.append(warn(
                "confidentiality-marker",
                f"confidentiality marker `{pattern}` {at(ctx.body, m)} — "
                f"theses get published, remove it",
            ))
            break
    return out


# Result verbs with the work as subject, and the change words a reported number
# attaches to. A proposal describes work that has not happened, so a sentence in
# this shape is either a draft written after the work began or a proposal
# derived from a finished thesis.
RESULT_VERBS = {
    "en": r"\b(showed|shown|demonstrated|proved|proven|outperformed|revealed|"
          r"confirmed|achieved)\b",
    "de": r"\b(zeigte[n]?|gezeigt|nachgewiesen|bewiesen|übertraf[en]?|"
          r"bestätigte[n]?|erreichte[n]?)\b",
}
CHANGE_WORDS = {
    "en": r"\b(reduced|increased|decreased|lowered|raised|improved|faster|"
          r"slower|better|worse)\b",
    "de": r"\b(reduzierte[n]?|senkte[n]?|erhöhte[n]?|verbesserte[n]?|"
          r"schneller|langsamer|besser|schlechter)\b",
}
QUANTITY = r"\d+(?:[.,]\d+)?\s*(?:%|percent|Prozent)"
# `… the conditions under which faithfulness is actually demonstrated` is a plan
# sentence: present-tense passive states a property the work will look for,
# where the past tense (`was demonstrated`) states a result it already has.
PRESENT_PASSIVE = {
    "en": r"\b(is|are|be|being|am)\b(?:\s+\w+)?\s*$",
    "de": r"\b(ist|sind|wird|werden|sein)\b(?:\s+\w+)?\s*$",
}


# Back-references that carry a cited sentence's attribution into the next one.
# The guidance asks for exactly these instead of a repeated citation, and the
# cue has to open the sentence (see `continues_attribution`). `it` counts
# unless an expletive construction follows ("It was shown …" would launder a
# claim); German `es` stays out, being expletive far more often than not.
# Deliberately absent: every name a proposal gives the thesis itself — `this
# study`, `diese Arbeit`, and `the study`/`die Studie`, which the guidance
# prescribes for the thesis's own work. Plural "these studies" cannot be it.
EXPLETIVE = (r"(?:is|are|was|were|has been|had been|seems|seemed|appears|appeared|turns out|"
             r"turned out|remains|remained|follows|followed|(?:can|could|should|must|may|"
             r"might|will|would) be)")
CONTINUATION_CUES = {
    "en": rf"(?:they|their|its|it\b(?!\s+{EXPLETIVE}\b)|both studies|both|these studies|"
          r"the authors|these authors|the same study)\b",
    "de": r"(?:sie|ihre?[mnrs]?|deren|dessen|sein(?:e[mnrs]?)?|beide studien|beide|"
          r"diese studien|(?:die|den|der) autor(?:en|innen|:innen))\b",
}
# a reporting clause naming the cited authors attributes a sentence wherever
# it stands: "Most projects, they report, merge …", "…, so die Autoren."
REPORTING_CLAUSE = {
    "en": r"\b(?:they|the authors|these authors)\s+(?:report|reported|find|found|show|showed|"
          r"argue|argued|note|noted|observe|observed|conclude|concluded|state|stated)\b",
    "de": r"\b(?:so die autor(?:en|innen|:innen)|(?:ihnen|den autor(?:en|innen|:innen)) zufolge|"
          r"(?:berichten|zeigen|argumentieren|folgern) sie)\b",
}
# after a preposition only a possessive cue opens the sentence: "In their
# evaluation …", "Laut den Autoren …" — never "In both settings we …"
POSSESSIVE_CUES = {
    "en": r"(?:in|for|from|across|on|under|with|according to)\s+"
          r"(?:their|its|the authors|these authors|these studies|both studies)\b",
    "de": r"(?:in|bei|nach|laut|gemäß|mit|aus|unter)\s+(?:ihre?[mnrs]?|deren|dessen|"
          r"seine[mnrs]?|(?:den|der) autor(?:en|innen|:innen)|diesen studien|beiden studien)\b",
}
FIRST_PERSON = {
    "en": r"\b(?:we|our|ours|us)\b",
    "de": r"\b(?:wir|unser\w*|uns)\b",
}
LIST_ITEM = re.compile(r"\s*(?:[-*+]|\d+[.)])\s")
# One regex walks a line for brackets and for sentence ends at once: a period
# inside `[@key, S. 12]` is a locator, never a sentence end.
SENTENCE_END = re.compile(r"[\[\]]|(?<=[.!?])\s+")
# a period after one of these does not end the sentence (`S.`/`p.` only as the
# capital resp. small locator letter, so a sentence ending in "is." stays one)
ABBREVIATION = re.compile(
    r"(?:\b(?i:et al|e\.g|i\.e|cf|vs|z\. ?b|d\. ?h|u\. ?a|vgl|bzw|ca|fig|sec|eq|abb|kap|"
    r"tab|nr|pp)|\b[Sp])\.$"
)
# the first half of `z. B.`, `d. h.`, `u. a.` — joined only to a next piece
# that is itself one letter and a period
ABBREVIATION_HALF = re.compile(r"\b(?i:[zdu])\.$")
# German ordinals after an article or preposition: "im 2. Schritt", "am 3. Mai"
ORDINAL = re.compile(
    r"\b(?i:im|am|zum|vom|beim|der|die|das|den|dem|des|ein|eine|einem|einen|einer|ab|bis|"
    r"seit)\s+\d{1,3}\.$"
)


def joins_previous(before: str, piece: str) -> bool:
    """A sentence-end match that only closed an abbreviation or an ordinal."""
    return bool(ABBREVIATION.search(before) or ORDINAL.search(before)
                or (ABBREVIATION_HALF.search(before) and re.match(r"[A-Za-z]\.", piece)))


def append_piece(spans: list[tuple[int, str]], start: int, piece: str) -> None:
    piece = piece.strip()
    if not piece:
        return
    if spans and joins_previous(spans[-1][1], piece):
        spans[-1] = (spans[-1][0], f"{spans[-1][1]} {piece}")
    else:
        spans.append((start, piece))


def sentence_spans(text: str) -> list[tuple[int, str]]:
    """(offset, sentence) for every sentence of a text: split at sentence
    punctuation outside citation brackets, never inside an abbreviation."""
    spans: list[tuple[int, str]] = []
    start = depth = 0
    for m in SENTENCE_END.finditer(text):
        if m.group(0) == "[":
            depth += 1
        elif m.group(0) == "]":
            depth = max(0, depth - 1)
        elif not depth:
            append_piece(spans, start, text[start:m.start()])
            start = m.end()
    append_piece(spans, start, text[start:])
    return spans


def split_sentences(line: str) -> list[str]:
    return [sentence for _, sentence in sentence_spans(line.strip())]


def segment_sentences(segment: list[tuple[int, str]]) -> list[tuple[str, int]]:
    """A run of lines read as one text, so a wrapped sentence stays one; each
    sentence reports the line it starts on."""
    text, starts = "", []
    for lineno, part in segment:
        starts.append((len(text), lineno))
        text += part + " "
    return [(sentence, max(line for at, line in starts if at <= offset))
            for offset, sentence in sentence_spans(text)]


def prose_blocks(body: str, list_items_break: bool = True) -> list[list[tuple[str, int]]]:
    """Blocks of (sentence, line number). A blank line or a heading ends a
    block and a table row is a block of its own. A list item starts a block
    for attribution runs; for the repetition comparison (`list_items_break`
    false) consecutive items stay one block, so bullets do not hide repeats,
    while each item still ends its own last sentence."""
    blocks: list[list[tuple[str, int]]] = []
    segments: list[list[tuple[int, str]]] = []
    for lineno, line in enumerate(mask_code(body).split("\n"), start=1):
        text = line.strip()
        item = bool(LIST_ITEM.match(line))
        if not text or text.startswith(("#", "|")) or (item and list_items_break):
            if segments:
                blocks.append([s for seg in segments for s in segment_sentences(seg)])
            segments = []
            if not text or text.startswith("#"):
                continue
        if item or text.startswith("|") or not segments:
            segments.append([])
        segments[-1].append((lineno, text))
        if text.startswith("|"):
            blocks.append(segment_sentences(segments.pop()))
    if segments:
        blocks.append([s for seg in segments for s in segment_sentences(seg)])
    return blocks


def citation_keys(text: str) -> frozenset[str]:
    return frozenset(m.group(1).rstrip(".,;:") for m in CITATION_KEY.finditer(text))


def rule_repeated_citations(ctx: Context) -> list[Finding]:
    """The same references cited on adjacent sentences of one paragraph or list.

    The guidance asks for one citation per continuous use, carried on in
    words. A sentence citing a different set is a change of source, which the
    guidance asks to cite, so only an identical set counts. Whether an uncited
    follow-up still reads as attributed is not judged here.
    """
    out = []
    for block in prose_blocks(ctx.body, list_items_break=False):
        before: frozenset[str] = frozenset()
        for sentence, lineno in block:
            keys = citation_keys(sentence)
            if keys and keys == before:
                out.append(warn(
                    "citation-repeated",
                    f"`{', '.join(sorted(keys))}` (line {lineno}) repeats the citation "
                    f"of the sentence before it — cite it once, opening with the "
                    f"author-in-text form, and refer back in words (\"they\", \"their …\")",
                ))
            before = keys
    return out


def continues_attribution(sentence: str, lang: str) -> bool:
    """The sentence opens with a back-reference to a cited work or its authors:
    the cue first, after one connective set off by a comma ("However, they"),
    after a preposition as a possessive ("In their evaluation"), or — German
    verb-second order — as the subject after the finite verb ("Zudem zeigen
    sie"). A cue in object position does not open a sentence, and a sentence in
    the first person is the thesis speaking whatever else it mentions."""
    text = sentence.lower().lstrip("\"'„“”( ")
    if re.search(FIRST_PERSON[lang], text):
        return False
    if re.search(REPORTING_CLAUSE[lang], text):
        return True
    cue = CONTINUATION_CUES[lang]
    openers = [cue, rf"\w+,\s+{cue}", POSSESSIVE_CUES[lang]]
    if lang == "de":
        openers.append(r"\w+\s+\w+\s+(?:sie|beide)\b")
    return any(re.match(opener, text) for opener in openers)


def result_claim(sentence: str, lang: str) -> re.Match | None:
    """The result verb, or the change word beside a quantity, that states an
    outcome as obtained — unless present-tense passive makes it a plan."""
    m = re.search(RESULT_VERBS[lang], sentence, re.IGNORECASE)
    if m is None and re.search(QUANTITY, sentence):
        m = re.search(CHANGE_WORDS[lang], sentence, re.IGNORECASE)
    if m is None or re.search(PRESENT_PASSIVE[lang], sentence[:m.start()], re.IGNORECASE):
        return None
    return m


def rule_hindsight_leakage(ctx: Context) -> list[Finding]:
    """Results the proposal cannot have yet, in sentences attributed to nobody.

    The attribution anchor is the whole rule: reporting what prior work
    established is exactly what the contribution section does, so a check that
    could not tell `@Rivera23 showed …` from `we showed …` would fire on every
    correctly written proposal. A sentence is attributed when it cites, or when
    it continues a cited sentence in the same block through a back-reference —
    the form the guidance asks for instead of repeating the citation, which a
    per-sentence anchor would punish.
    """
    for block in prose_blocks(ctx.body):
        attributed = False
        for sentence, lineno in block:
            attributed = bool(CITATION_KEY.search(sentence)) or (
                attributed and continues_attribution(sentence, ctx.lang))
            m = None if attributed else result_claim(sentence, ctx.lang)
            if m is None:
                continue
            return [warn(
                "hindsight-leakage",
                f"`{m.group(0)}` (line {lineno}) states the work as already done, in a "
                f"sentence that neither cites a source nor continues a cited one — a "
                f"proposal plans work that has not happened; attribute the result (cite "
                f"it, or continue a cited sentence with \"they\" / \"their …\") or write "
                f"it as a plan",
            )]
    return []


# Report order. Errors and warnings are rendered in separate buckets, so what
# this sequence fixes is the order within each bucket.
RULES = (
    rule_metadata_present,
    rule_reference_id_syntax,
    rule_single_metadata_block,
    rule_retired_keys,
    rule_legacy_format,
    rule_heading_style,
    rule_frame,
    rule_language,
    rule_title,
    rule_timeline_mode,
    rule_required_sections,
    rule_section_order,
    rule_timeline_size,
    rule_methodology,
    rule_references_section,
    rule_forbidden_sections,
    rule_research_questions,
    rule_citations,
    rule_repeated_citations,
    rule_reference_id_shape,
    rule_min_references,
    rule_reference_density,
    rule_todo_markers,
    rule_length,
    rule_prose_patterns,
    rule_hindsight_leakage,
)


def build_context(body: str, meta: Metadata, structure: dict, overrides: dict) -> Context:
    """Derive once what every rule reads. An unrecognised timeline mode falls
    back to the default here silently; `rule_timeline_mode` reports it, so the
    finding keeps its place in the report rather than jumping to the front.
    The leading title H1 is dropped from `head_texts` here: the title is not a
    section, so it must never satisfy, order, or trip a section rule."""
    frame = parse_frame(body)

    timeline_cfg = structure["timeline"]
    detail = setting(structure, overrides, "timeline", "detail")
    if detail not in timeline_cfg["detail_modes"]:
        detail = timeline_cfg["detail"]

    all_heads = headings(body)
    head_texts = [t for _, t in (all_heads[1:] if frame.title_is_first else all_heads)]
    inferred = infer_language(frame, head_texts, structure)
    lang = inferred or "en"
    titles = structure["sections"]["titles"]
    meth_tpl = titles["methodology"][lang]
    meth_prefix = meth_tpl.split("{")[0]
    required_default = [
        titles[key][lang] for key in structure["sections"]["order"] if key != "methodology"
    ]
    return Context(
        body=body, meta=meta, frame=frame, lang=lang,
        lang_determined=inferred is not None,
        structure=structure, overrides=overrides,
        methodologies=merge_methodologies(structure, overrides),
        detail=detail, head_texts=head_texts, titles=titles, meth_tpl=meth_tpl,
        meth_prefix=meth_prefix,
        meth_heads=[h for h in head_texts if h.startswith(meth_prefix)],
        required=(setting(structure, overrides, "sections", "required")
                  if overridden(overrides, "sections", "required") else required_default),
    )


def check_findings(proposal_path: Path, structure: dict, overrides: dict,
                   root: Path | None = None, explicit: bool = False) -> list[Finding]:
    """Every mechanical finding for one proposal, in report order. The
    workspace findings are measured from `root`, by default the working
    directory, which is the workspace root a user's agent runs from;
    `explicit` says the root is an explicitly passed override file's
    directory instead."""
    text = proposal_path.read_text(encoding="utf-8")
    body, meta = split_proposal(text)

    findings: list[Finding] = []
    if "_parse_error" in overrides:
        findings.append(error(
            "guidelines-toml-parse",
            f"guidelines.md TOML block does not parse: {overrides['_parse_error']}",
        ))
        overrides = {}
    # before the rules: a key that will not be honoured explains every verdict
    # below it, and reading those first would waste the user's time.
    findings += override_key_findings(overrides)
    findings += workspace_findings(proposal_path, structure, overrides,
                                   root if root is not None else Path.cwd(), explicit)

    ctx = build_context(body, meta, structure, overrides)
    for rule in RULES:
        findings += rule(ctx)
    # last: it concerns the review beside the proposal, not the proposal's text
    findings += review_findings(proposal_path, ctx)
    return findings


def check(proposal_path: Path, structure: dict, overrides: dict) -> tuple[list[str], list[str]]:
    """Messages split into the two report buckets — the shape the report and the
    existing consumers expect."""
    findings = check_findings(proposal_path, structure, overrides)
    return (
        [f.message for f in findings if f.level == "error"],
        [f.message for f in findings if f.level == "warning"],
    )


def repeated_sentence_starts(body: str):
    """First words of runs of three consecutive same-start sentences.

    Sentences are split within paragraphs; headings and blank lines reset the run.
    """
    found: list[str] = []
    run: list[str] = []
    for line in body.split("\n"):
        if not line.strip() or line.startswith("#"):
            run = []
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line.strip()):
            words = sentence.split()
            if not words or not words[0][0].isalpha():
                continue
            run.append(words[0])
            if len(run) >= 3 and run[-1] == run[-2] == run[-3]:
                found.append(run[-1])
                run = []
    return found


def section_text(body: str, title: str) -> str:
    """Text of the section with the given heading, at whatever level it appears;
    stops at the next heading of the same or a shallower level."""
    m = re.search(rf"^(#{{1,6}})\s+{re.escape(title)}\s*$", body, re.MULTILINE)
    if not m:
        return ""
    level = len(m.group(1))
    rest = body[m.end():]
    stop = re.search(rf"^#{{1,{level}}}\s", rest, re.MULTILINE)
    return rest[: stop.start()] if stop else rest


# ---------- report -----------------------------------------------------------

def render_report(name: str, digest: str, findings: list[Finding], governing: str) -> str:
    """The human report. Its wording is the skill's user-facing output; the
    machine-readable mode exists so nothing has to parse it. `governing` is a
    key of GOVERNING_LABELS."""
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    lines = [f"# Check: {name}"]
    # identifies the exact content checked; a re-run with a differing digest
    # means the file changed between the runs (read-only mandate tripwire)
    lines.append(f"digest: sha256:{digest}")
    lines.append(f"guidelines: {GOVERNING_LABELS[governing]}")
    lines.append(
        "\n## Verified mechanically — errors" if errors
        else "\n## Verified mechanically — no errors"
    )
    lines += [f"- ERROR: {f.message}" for f in errors]
    if warnings:
        lines.append("\n## Verified mechanically — warnings (possible false positives)")
        lines += [f"- WARNING: {f.message}" for f in warnings]
    lines.append(
        "\n## Deferred to the agent pass\n"
        "- typos, grammar, and wording\n"
        "- content-level forbidden material (e.g. expected results in prose)\n"
        "- whether the timeline names a real timeframe, and work plans the "
        "structure check cannot see (e.g. a Gantt chart pasted in as an image)\n"
        "- all semantic quality rules (analytical RQs, argument soundness) — see review skill\n"
        "\nThis check is advisory: it gates nothing. A clean result is mechanical "
        "only — substance is not judged here; the review skill renders that verdict."
    )
    return "\n".join(lines)


def utf8_output() -> None:
    """Write stdout and stderr as UTF-8, whatever encoding the platform chose.

    A Windows pipe is encoded in the ANSI code page (cp1252 in Western Europe),
    so printing a character outside it raised UnicodeEncodeError. Each stream
    keeps its error handler, which reconfigure() would otherwise reset to
    strict, and its newline handling; a stream without reconfigure() (a
    caller's StringIO, or None without a console) is left alone. The same in
    every script family (tests/unit/test_utf8_output.py).
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors=stream.errors)


def main(argv: list[str] | None = None) -> int:
    utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--guidelines", type=Path, default=None)
    parser.add_argument("--structure", type=Path, default=None)
    parser.add_argument("--json", action="store_true",
                        help="emit findings as JSON instead of the human report")
    args = parser.parse_args(argv)

    structure = load_structure(args.structure)
    overrides = load_overrides(args.proposal, args.guidelines)
    # the workspace root: an explicit override file's directory, else here
    explicit = args.guidelines is not None
    root = args.guidelines.parent if explicit else Path.cwd()
    findings = check_findings(args.proposal, structure, overrides, root, explicit)
    governing = governing_position(args.proposal, args.guidelines)
    digest = hashlib.sha256(args.proposal.read_bytes()).hexdigest()
    exit_code = 1 if any(f.level == "error" for f in findings) else 0
    name = _shown(args.proposal.name)

    if args.json:
        print(json.dumps({
            "file": name,
            "digest": f"sha256:{digest}",
            "guidelines": governing,
            "exit_code": exit_code,
            "findings": [
                {"level": f.level, "rule": f.rule, "message": f.message} for f in findings
            ],
        }, ensure_ascii=False, indent=2))
    else:
        print(render_report(name, digest, findings, governing))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
