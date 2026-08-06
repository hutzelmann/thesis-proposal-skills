#!/usr/bin/env python3
# GENERATED from skills/proposal-check/scripts/check.py
# Edit there, then run scripts/sync_shared.py
"""Deterministic low-level checks for a thesis proposal file.

Stdlib-only (Python >= 3.11). Reads the proposal's markdown, its trailing
metadata block (narrow extraction — no general YAML parsing), the canonical
skeleton from references/structure.json, and an optional workspace
guidelines.md TOML override block.

Output: two-bucket report (mechanical errors / mechanical warnings) plus a
fixed note on what is deferred to the agent pass. Exit 1 only on mechanical
errors — the check is advisory, warnings never fail the run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
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
    # title
    "metadata-title-missing",
    "title-implementation-opener",
    "title-buzzword",
    "title-question-form",
    "title-too-short",
    "title-too-long",
    # structure
    "timeline-detail-unknown",
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
    # content
    "todo-marker",
    "length-over-limit",
    "first-person-pronoun",
    "repeated-sentence-start",
    "email-address",
    "matriculation-number",
    "metadata-author-key",
    "confidentiality-marker",
)


# ---------- loading ----------------------------------------------------------

def load_structure(path: Path | None) -> dict:
    if path is None:
        path = Path(__file__).resolve().parent.parent / "references" / "structure.json"
    return json.loads(path.read_text(encoding="utf-8"))


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
        self.lang = "en"
        self.title: str | None = None
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
            if m := re.search(r"^lang:\s*(\S+)", block, re.MULTILINE):
                meta.lang = m.group(1).strip("'\"")
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


# a `title:` whose value is only a YAML block-scalar indicator continues on the
# following lines, which the narrow one-line extraction never sees
BLOCK_SCALAR = re.compile(r"^[|>][+-]?\d*$")


def title_warnings(title: str, cfg: dict, lang: str = "en") -> list[Finding]:
    """The thesis title is printed on the study certificate — every finding says
    so, because that rationale is what makes a heuristic warning worth acting on.
    Only the mechanical tells live here: whether a proper noun in the title names
    a tool, a product or a vendor is agent judgement, never data."""
    certificate = "the title is printed on the study certificate"
    stripped = unicodedata.normalize("NFC", title.strip())
    if not stripped or BLOCK_SCALAR.fullmatch(stripped):
        return []  # folded/literal block: the value is on lines we did not read
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
    lang: str
    structure: dict
    overrides: dict
    detail: str            # effective timeline mode after validation
    head_texts: list[str]
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


def rule_metadata_present(ctx: Context) -> list[Finding]:
    if not ctx.meta.found:
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


def rule_title(ctx: Context) -> list[Finding]:
    if not ctx.meta.found:
        return []
    if ctx.meta.title is None:
        return [warn("metadata-title-missing", "metadata block has no `title:`")]
    return title_warnings(ctx.meta.title, ctx.structure["title"], ctx.lang)


def rule_timeline_mode(ctx: Context) -> list[Finding]:
    """`ctx.detail` has already fallen back to the default; this reports the
    value that caused the fallback, in its place in the report."""
    timeline_cfg = ctx.structure["timeline"]
    declared = ctx.overrides.get("timeline_detail", timeline_cfg["default_detail"])
    if declared in timeline_cfg["detail_modes"]:
        return []
    return [error("timeline-detail-unknown",
                  f"guidelines.md: unknown timeline_detail `{declared}` — must be one of: "
                  f"{', '.join(timeline_cfg['detail_modes'])}")]


def rule_required_sections(ctx: Context) -> list[Finding]:
    return [
        error("required-section-missing", f"required section missing: `{title}`")
        for title in ctx.required if not any(h == title for h in ctx.head_texts)
    ]


def rule_section_order(ctx: Context) -> list[Finding]:
    # An overridden required_sections list carries its own order; otherwise the
    # canonical order applies, with the methodology matched by title prefix
    # because its heading is a template.
    if "required_sections" in ctx.overrides:
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
    if "required_sections" in ctx.overrides:
        return []
    methodologies = ctx.structure["methodologies"]
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
    forbidden = [p.lower() for p in ctx.overrides.get(
        "forbidden_sections", ctx.structure["forbidden_heading_patterns"]
    )]
    if ctx.detail == "detailed":
        work_plan = {p.lower() for p in ctx.structure["work_plan_heading_patterns"]}
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
    out += [
        error("research-question-unreferenced",
              f"(RQ{n}) never referenced in the methodology section")
        for n in range(1, len(rq_items) + 1)
        if meth_section and f"(RQ{n})" not in meth_section
    ]
    return out


def scan_citations(ctx: Context) -> tuple[dict[str, int], dict[str, int],
                                          list[tuple[str, int, bool]]]:
    """(cited, author-in-text, typed names) with the line each first occurred on."""
    cited: dict[str, int] = {}
    author_in_text: dict[str, int] = {}
    typed_names: list[tuple[str, int, bool]] = []
    for lineno, line in enumerate(ctx.body.split("\n"), start=1):
        # a key inside a bracketed group renders as a bare number; one outside
        # is author-in-text and gets an author label prefixed
        depth = 0
        for m in re.finditer(r"\[|\]|(?<![\w.])@([A-Za-z][\w:.-]*)", line):
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
              f"cited key `@{key}` not defined in references (line {cited[key]})")
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
    min_refs = ctx.overrides.get("min_references", ctx.structure["min_references"])
    if len(defined) < min_refs:
        return [error("min-references",
                      f"only {len(defined)} references — at least {min_refs} required")]
    return []


def rule_todo_markers(ctx: Context) -> list[Finding]:
    return [warn("todo-marker", f"open {todo}")
            for todo in re.findall(ctx.structure["todo_marker"], ctx.body)]


def rule_length(ctx: Context) -> list[Finding]:
    """Estimated from word count: markdown has no pages."""
    length_cfg = ctx.structure.get("length")
    if not length_cfg:
        return []
    page_limit = ctx.overrides.get("page_limit", length_cfg["page_limit"])
    words = sum(
        len(line.split())
        for line in ctx.body.split("\n")
        if line.strip() and not line.lstrip().startswith("#")
    )
    estimated = words / length_cfg["words_per_page"]
    if estimated <= page_limit:
        return []
    return [warn(
        "length-over-limit",
        f"estimated length ~{estimated:.1f} pages ({words} words at "
        f"{length_cfg['words_per_page']} words/page) exceeds the "
        f"{page_limit}-page limit — an estimate, not a rendered count; "
        f"delete low-information sentences rather than compressing wording",
    )]


def rule_prose_patterns(ctx: Context) -> list[Finding]:
    out = []
    fp = (r"\b(I|[Ww]e|[Mm]y|[Oo]ur)\b" if ctx.lang == "en"
          else r"\b([Ii]ch|[Ww]ir|[Mm]ein\w*|[Uu]nser\w*)\b")
    if fps := re.findall(fp, ctx.body):
        out.append(warn("first-person-pronoun",
                        f"first-person pronouns found ({len(fps)}×) — use third person"))
    for start_word in repeated_sentence_starts(ctx.body):
        out.append(warn("repeated-sentence-start",
                        f"three consecutive sentences start with `{start_word}`"))
        break
    if re.search(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", ctx.body):
        out.append(warn("email-address", "email address found — personal data is forbidden"))
    if re.search(r"\b(matriculation|matrikel)", ctx.body, re.IGNORECASE) or re.search(
        r"(?<!\d)\d{7,8}(?!\d)", ctx.body
    ):
        out.append(warn("matriculation-number",
                        "possible matriculation number / personal data"))
    if ctx.meta.has_author_key:
        # the exception (a program requiring a named title page) is declared in
        # workspace guidance prose, which is not machine-readable — so warn always
        out.append(warn(
            "metadata-author-key",
            "`author:` found — proposals are anonymous by default; remove it "
            "unless your program requires a named cover page",
        ))
    for pattern in ctx.structure["confidentiality_patterns"]:
        if re.search(rf"\b{re.escape(pattern)}\b", ctx.body, re.IGNORECASE):
            out.append(warn(
                "confidentiality-marker",
                f"confidentiality marker `{pattern}` — theses get published, remove it",
            ))
            break
    return out


# Report order. Errors and warnings are rendered in separate buckets, so what
# this sequence fixes is the order within each bucket.
RULES = (
    rule_metadata_present,
    rule_reference_id_syntax,
    rule_single_metadata_block,
    rule_title,
    rule_timeline_mode,
    rule_required_sections,
    rule_section_order,
    rule_timeline_size,
    rule_methodology,
    rule_forbidden_sections,
    rule_research_questions,
    rule_citations,
    rule_reference_id_shape,
    rule_min_references,
    rule_todo_markers,
    rule_length,
    rule_prose_patterns,
)


def build_context(body: str, meta: Metadata, structure: dict, overrides: dict) -> Context:
    """Derive once what every rule reads. An unrecognised timeline mode falls
    back to the default here silently; `rule_timeline_mode` reports it, so the
    finding keeps its place in the report rather than jumping to the front."""
    lang = meta.lang if meta.lang in ("en", "de") else "en"

    timeline_cfg = structure["timeline"]
    detail = overrides.get("timeline_detail", timeline_cfg["default_detail"])
    if detail not in timeline_cfg["detail_modes"]:
        detail = timeline_cfg["default_detail"]

    head_texts = [t for _, t in headings(body)]
    titles = structure["sections"]["titles"]
    meth_tpl = titles["methodology"][lang]
    meth_prefix = meth_tpl.split("{")[0]
    required_default = [
        titles[key][lang] for key in structure["sections"]["order"] if key != "methodology"
    ]
    return Context(
        body=body, meta=meta, lang=lang, structure=structure, overrides=overrides,
        detail=detail, head_texts=head_texts, titles=titles, meth_tpl=meth_tpl,
        meth_prefix=meth_prefix,
        meth_heads=[h for h in head_texts if h.startswith(meth_prefix)],
        required=overrides.get("required_sections", required_default),
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
