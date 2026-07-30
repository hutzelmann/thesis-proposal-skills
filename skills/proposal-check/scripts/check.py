#!/usr/bin/env python3
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
import json
import re
import sys
import tomllib
from pathlib import Path

BOOLEAN_LITERALS = {"y", "n", "yes", "no", "on", "off", "true", "false"}


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


def split_proposal(text: str) -> tuple[str, Metadata]:
    """Split body from the trailing metadata block; extract narrow fields."""
    meta = Metadata()
    lines = text.rstrip("\n").split("\n")
    delim = [i for i, l in enumerate(lines) if re.fullmatch(r"---\s*", l)]
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
            return body, meta
    return text, meta


# ---------- checks -----------------------------------------------------------

def headings(body: str) -> list[tuple[int, str]]:
    return [
        (len(m.group(1)), m.group(2).strip())
        for m in re.finditer(r"^(#{1,6})\s+(.+)$", body, re.MULTILINE)
    ]


def check(proposal_path: Path, structure: dict, overrides: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = proposal_path.read_text(encoding="utf-8")
    body, meta = split_proposal(text)
    lang = meta.lang if meta.lang in ("en", "de") else "en"

    if "_parse_error" in overrides:
        errors.append(f"guidelines.md TOML block does not parse: {overrides['_parse_error']}")
        overrides = {}

    # -- format guardrails
    if not meta.found:
        errors.append("no trailing metadata block found (file must end with a `---` YAML block)")
    else:
        if not meta.blank_line_before:
            errors.append("no blank line before the trailing `---` block (pandoc will treat it as body text)")
        for rid in meta.reference_ids:
            if rid.lower() in BOOLEAN_LITERALS:
                errors.append(f"reference id `{rid}` is a YAML boolean literal — rename or quote it")
        dupes = {r for r in meta.reference_ids if meta.reference_ids.count(r) > 1}
        for rid in sorted(dupes):
            errors.append(f"duplicate reference id `{rid}`")
        if meta.title is None:
            warnings.append("metadata block has no `title:`")
        body_lines = body.split("\n")
        delims = [i for i, l in enumerate(body_lines) if re.fullmatch(r"---\s*", l)]
        for a, b in zip(delims, delims[1:], strict=False):
            block = "\n".join(body_lines[a + 1 : b])
            if re.search(r"^\s*\w[\w-]*\s*:", block, re.MULTILINE):
                errors.append(
                    "additional metadata block found before the trailing one — "
                    "exactly one trailing block allowed"
                )
                break

    # -- sections
    heads = headings(body)
    head_texts = [t for _, t in heads]
    titles = structure["sections"]["titles"]
    meth_tpl = titles["methodology"][lang]
    required_default = [
        titles[key][lang] for key in structure["sections"]["order"] if key != "methodology"
    ]
    required = overrides.get("required_sections", required_default)
    for title in required:
        if not any(h == title for h in head_texts):
            errors.append(f"required section missing: `{title}`")

    # -- methodology (canonical mode only)
    meth_prefix = meth_tpl.split("{")[0]
    meth_heads = [h for h in head_texts if h.startswith(meth_prefix)]
    methodologies = structure["methodologies"]
    meth_names = {m["title"][lang]: key for key, m in methodologies.items()}
    if "required_sections" not in overrides:
        if not meth_heads:
            errors.append(f"methodology section missing (`{meth_tpl}`)")
        elif len(meth_heads) > 1:
            errors.append("multiple methodology sections — exactly one methodology allowed")
        else:
            chosen = meth_heads[0][len(meth_prefix):].strip()
            if chosen not in meth_names:
                errors.append(
                    f"unknown methodology `{chosen}` — must be one of: {', '.join(sorted(meth_names))}"
                )
            else:
                for sub in methodologies[meth_names[chosen]]["subsections"]:
                    if sub[lang] not in head_texts:
                        errors.append(f"methodology subsection missing: `{sub[lang]}`")

    # -- forbidden headings
    forbidden = [p.lower() for p in overrides.get(
        "forbidden_sections", structure["forbidden_heading_patterns"]
    )]
    for h in head_texts:
        for pattern in forbidden:
            if pattern in h.lower():
                errors.append(f"forbidden section: `{h}` (matches `{pattern}`)")
                break

    # -- research questions
    rq_title = titles["research_questions"][lang]
    rq_section = section_text(body, rq_title)
    meth_section = section_text(body, meth_heads[0]) if meth_heads else ""
    rq_items = re.findall(r"^\d+[.)]\s+", rq_section, re.MULTILINE)
    if rq_section and not rq_items:
        errors.append("no ordered-list research questions found in the research-questions section")
    for n in range(1, len(rq_items) + 1):
        if meth_section and f"(RQ{n})" not in meth_section:
            errors.append(f"(RQ{n}) never referenced in the methodology section")

    # -- citations
    cited: dict[str, int] = {}
    author_in_text: dict[str, int] = {}
    for lineno, line in enumerate(body.split("\n"), start=1):
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
    defined = set(meta.reference_ids)
    for key in sorted(set(cited) - defined):
        errors.append(f"cited key `@{key}` not defined in references (line {cited[key]})")
    for key in sorted(defined - set(cited)):
        warnings.append(f"reference `{key}` defined but never cited")
    for key in sorted(set(author_in_text) & meta.reference_ids_without_names):
        warnings.append(
            f"`@{key}` is cited author-in-text but its reference declares no author or editor "
            f"(line {author_in_text[key]}) — it renders as the quoted title; use `[@{key}]` instead"
        )
    min_refs = overrides.get("min_references", structure["min_references"])
    if len(defined) < min_refs:
        errors.append(f"only {len(defined)} references — at least {min_refs} required")

    # -- TODO markers
    todos = re.findall(structure["todo_marker"], body)
    for todo in todos:
        warnings.append(f"open {todo}")

    # -- warning-class patterns
    fp = (r"\b(I|[Ww]e|[Mm]y|[Oo]ur)\b" if lang == "en"
          else r"\b([Ii]ch|[Ww]ir|[Mm]ein\w*|[Uu]nser\w*)\b")
    if fps := re.findall(fp, body):
        warnings.append(f"first-person pronouns found ({len(fps)}×) — use third person")
    for start_word in repeated_sentence_starts(body):
        warnings.append(f"three consecutive sentences start with `{start_word}`")
        break
    if re.search(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b", body):
        warnings.append("email address found — personal data is forbidden")
    if re.search(r"\b(matriculation|matrikel)", body, re.IGNORECASE) or re.search(r"(?<!\d)\d{7,8}(?!\d)", body):
        warnings.append("possible matriculation number / personal data")
    for pattern in structure["confidentiality_patterns"]:
        if re.search(rf"\b{re.escape(pattern)}\b", body, re.IGNORECASE):
            warnings.append(
                f"confidentiality marker `{pattern}` — theses get published, remove it"
            )
            break

    return errors, warnings


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

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--guidelines", type=Path, default=None)
    parser.add_argument("--structure", type=Path, default=None)
    args = parser.parse_args()

    structure = load_structure(args.structure)
    overrides = load_overrides(args.proposal, args.guidelines)
    errors, warnings = check(args.proposal, structure, overrides)

    print(f"# Check: {args.proposal.name}")
    print("\n## Verified mechanically — errors" if errors else "\n## Verified mechanically — no errors")
    for e in errors:
        print(f"- ERROR: {e}")
    if warnings:
        print("\n## Verified mechanically — warnings (possible false positives)")
        for w in warnings:
            print(f"- WARNING: {w}")
    print(
        "\n## Deferred to the agent pass\n"
        "- typos, grammar, and wording\n"
        "- content-level forbidden material (e.g. expected results in prose)\n"
        "- all semantic quality rules (analytical RQs, argument soundness) — see review skill\n"
        "\nThis check is advisory: it gates nothing."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
