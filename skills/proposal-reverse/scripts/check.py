#!/usr/bin/env python3
# GENERATED from skills/proposal-check/scripts/check.py
# Edit there, then run scripts/sync_shared.py
"""Deterministic low-level checks for a thesis proposal file.

Stdlib-only (Python >= 3.11). Reads the proposal's markdown — leading `# ` title
line, emphasized subtitle paragraph, sections, and the trailing references
metadata block (narrow extraction — no general YAML parsing) — plus the
canonical skeleton from references/structure.json and an optional workspace
guidelines.md TOML override block. The proposal's language is inferred from the
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
import re
import sys
import tomllib
import unicodedata
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
    "research-question-unreferenced",
    # citations and references
    "citation-undefined",
    "reference-uncited",
    "author-name-typed-bracketed",
    "author-name-typed-in-text",
    "author-in-text-without-author",
    "reference-id-shape",
    "reference-id-too-long",
    "min-references",
    "min-references-invalid",
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
    ("sections", "required"),
    ("forbidden", "heading_patterns"),
    ("timeline", "detail"),
    ("length", "page_limit"),
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


def load_overrides(proposal: Path, explicit: Path | None) -> dict:
    candidate = explicit or proposal.parent / "guidelines.md"
    if not candidate.exists():
        return {}
    match = re.search(r"```toml\n(.*?)```", candidate.read_text(encoding="utf-8"), re.DOTALL)
    if not match:
        return {}
    try:
        return tomllib.loads(match.group(1))
    except tomllib.TOMLDecodeError as exc:
        return {"_parse_error": str(exc)}


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


def rule_research_questions(ctx: Context) -> list[Finding]:
    rq_title = ctx.titles["research_questions"][ctx.lang]
    rq_section = section_text(ctx.body, rq_title)
    meth_section = section_text(ctx.body, ctx.meth_heads[0]) if ctx.meth_heads else ""
    rq_items = re.findall(r"^\d+[.)]\s+", rq_section, re.MULTILINE)
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


def scan_citations(ctx: Context) -> tuple[dict[str, int], dict[str, int],
                                          list[tuple[str, int, bool]]]:
    """(cited, author-in-text, typed names) with the line each first occurred on."""
    cited: dict[str, int] = {}
    author_in_text: dict[str, int] = {}
    typed_names: list[tuple[str, int, bool]] = []
    for lineno, line in enumerate(mask_code(ctx.body).split("\n"), start=1):
        # a key inside a bracketed group renders as a bare number; one outside
        # is author-in-text and gets an author label prefixed. `\@` is the
        # escape a student uses for an at-sign that is not a citation.
        depth = 0
        for m in re.finditer(r"\[|\]|(?<![\w.\\])@([A-Za-z][\w:.-]*)", line):
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
        warn("reference-uncited", f"reference `{key}` defined but never cited")
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


def rule_todo_markers(ctx: Context) -> list[Finding]:
    return [warn("todo-marker", f"open {todo}")
            for todo in re.findall(ctx.structure["todo"]["marker"], ctx.body)]


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
    words = sum(
        len(line.split())
        for line in ctx.body.split("\n")
        if line.strip() and not line.lstrip().startswith("#")
    )
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


def prose_sentences(body: str):
    """(sentence, line number) for every prose sentence, headings skipped."""
    for lineno, line in enumerate(mask_code(body).split("\n"), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line.strip()):
            if sentence:
                yield sentence, lineno


def rule_hindsight_leakage(ctx: Context) -> list[Finding]:
    """Results the proposal cannot have yet, in sentences that cite nobody.

    The citation anchor is the whole rule: reporting what prior work
    established is exactly what the contribution section does, so a check that
    could not tell `@Rivera23 showed …` from `we showed …` would fire on every
    correctly written proposal.
    """
    verbs = RESULT_VERBS[ctx.lang]
    change = CHANGE_WORDS[ctx.lang]
    for sentence, lineno in prose_sentences(ctx.body):
        if re.search(r"(?<![\w.\\])@[A-Za-z]", sentence):
            continue
        m = re.search(verbs, sentence, re.IGNORECASE)
        if m is None and re.search(QUANTITY, sentence):
            m = re.search(change, sentence, re.IGNORECASE)
        if m is None:
            continue
        if re.search(PRESENT_PASSIVE[ctx.lang], sentence[:m.start()], re.IGNORECASE):
            continue
        return [warn(
            "hindsight-leakage",
            f"`{m.group(0)}` (line {lineno}) states the work as already done, "
            f"in a sentence citing no source — a proposal plans work that has "
            f"not happened; attribute the result or write it as a plan",
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
    rule_reference_id_shape,
    rule_min_references,
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


def check_findings(proposal_path: Path, structure: dict, overrides: dict) -> list[Finding]:
    """Every mechanical finding for one proposal, in report order."""
    body, meta = split_proposal(proposal_path.read_text(encoding="utf-8"))

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

    ctx = build_context(body, meta, structure, overrides)
    for rule in RULES:
        findings += rule(ctx)
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

def render_report(name: str, digest: str, findings: list[Finding]) -> str:
    """The human report. Its wording is the skill's user-facing output; the
    machine-readable mode exists so nothing has to parse it."""
    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    lines = [f"# Check: {name}"]
    # identifies the exact content checked; a re-run with a differing digest
    # means the file changed between the runs (read-only mandate tripwire)
    lines.append(f"digest: sha256:{digest}")
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--guidelines", type=Path, default=None)
    parser.add_argument("--structure", type=Path, default=None)
    parser.add_argument("--json", action="store_true",
                        help="emit findings as JSON instead of the human report")
    args = parser.parse_args(argv)

    structure = load_structure(args.structure)
    overrides = load_overrides(args.proposal, args.guidelines)
    findings = check_findings(args.proposal, structure, overrides)
    digest = hashlib.sha256(args.proposal.read_bytes()).hexdigest()
    exit_code = 1 if any(f.level == "error" for f in findings) else 0

    if args.json:
        print(json.dumps({
            "file": args.proposal.name,
            "digest": f"sha256:{digest}",
            "exit_code": exit_code,
            "findings": [
                {"level": f.level, "rule": f.rule, "message": f.message} for f in findings
            ],
        }, ensure_ascii=False, indent=2))
    else:
        print(render_report(args.proposal.name, digest, findings))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
