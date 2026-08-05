#!/usr/bin/env python3
# GENERATED from skills/proposal-check/scripts/check.py — edit there, then run scripts/sync_shared.py
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
from pathlib import Path

BOOLEAN_LITERALS = {"y", "n", "yes", "no", "on", "off", "true", "false"}
KEY_MAX_LEN = 20  # guidance: reference keys stay shorter than 20 characters


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


def timeline_body_errors(section: str, title: str, max_lines: int) -> list[str]:
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
        out.append(f"table in `{title}` — the timeline is one short sentence")
    if any(re.match(r"\s*([-*+]|\d+[.)])\s", line) for line in lines):
        out.append(f"list in `{title}` — the timeline is one short sentence")
    if any(re.match(r"#{1,6}\s", line) for line in lines):
        out.append(f"subsection in `{title}` — the timeline takes no work packages")
    if len(lines) > max_lines:
        out.append(f"`{title}` runs {len(lines)} lines — at most {max_lines} allowed")
    return out


# a `title:` whose value is only a YAML block-scalar indicator continues on the
# following lines, which the narrow one-line extraction never sees
BLOCK_SCALAR = re.compile(r"^[|>][+-]?\d*$")


def title_warnings(title: str, cfg: dict, lang: str = "en") -> list[str]:
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
        out.append(
            f"title opens with `{opener}` — implementation framing states building "
            f"work, not a contribution; {certificate}"
        )

    hits = [w for w in cfg["buzzwords"] if w in low]
    if hits:
        out.append(
            f"title carries {', '.join(f'`{w}`' for w in hits)} — marketing tone; "
            f"{certificate}"
        )

    if stripped.endswith("?"):
        out.append(
            "title is phrased as a question — an academic title states its subject; "
            f"{certificate}"
        )

    min_words = cfg["min_words"].get(lang, cfg["min_words"]["en"])
    words = len(stripped.split())
    if words < min_words:
        out.append(
            f"title runs {words} words — at least {min_words} expected; it has to name "
            f"a contribution and its object standing alone, without the subtitle, and "
            f"{certificate}"
        )
    elif words > cfg["max_words"]:
        out.append(
            f"title runs {words} words — at most {cfg['max_words']} expected; "
            f"{certificate}"
        )

    return out


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
        else:
            warnings.extend(title_warnings(meta.title, structure["title"], lang))
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

    # -- timeline detail mode
    timeline_cfg = structure["timeline"]
    detail = overrides.get("timeline_detail", timeline_cfg["default_detail"])
    if detail not in timeline_cfg["detail_modes"]:
        errors.append(
            f"guidelines.md: unknown timeline_detail `{detail}` — must be one of: "
            f"{', '.join(timeline_cfg['detail_modes'])}"
        )
        detail = timeline_cfg["default_detail"]

    # -- sections
    heads = headings(body)
    head_texts = [t for _, t in heads]
    titles = structure["sections"]["titles"]
    meth_tpl = titles["methodology"][lang]
    meth_prefix = meth_tpl.split("{")[0]
    required_default = [
        titles[key][lang] for key in structure["sections"]["order"] if key != "methodology"
    ]
    required = overrides.get("required_sections", required_default)
    for title in required:
        if not any(h == title for h in head_texts):
            errors.append(f"required section missing: `{title}`")

    # -- section order
    # An overridden required_sections list carries its own order; otherwise the
    # canonical order applies, with the methodology matched by title prefix
    # because its heading is a template.
    if "required_sections" in overrides:
        expected = [(t, t, False) for t in required]
    else:
        expected = [
            (titles[key][lang], meth_prefix if key == "methodology" else titles[key][lang],
             key == "methodology")
            for key in structure["sections"]["order"]
        ]
    positions = []
    for label, needle, by_prefix in expected:
        idx = next(
            (i for i, h in enumerate(head_texts)
             if (h.startswith(needle) if by_prefix else h == needle)),
            None,
        )
        if idx is not None:
            # name the heading as written, not the `{methodology}` template
            positions.append((idx, head_texts[idx] if by_prefix else label))
    for (prev_i, prev), (cur_i, cur) in zip(positions, positions[1:], strict=False):
        if cur_i < prev_i:
            errors.append(f"section out of order: `{cur}` before `{prev}`")

    # -- timeline stays coarse (the detailed mode is the escape hatch for a
    # program that mandates a work plan)
    if detail == "simple":
        tl_title = titles["timeline"][lang]
        errors.extend(
            timeline_body_errors(
                section_text(body, tl_title), tl_title, timeline_cfg["max_body_lines"]
            )
        )

    # -- methodology (canonical mode only)
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
    if detail == "detailed":
        work_plan = {p.lower() for p in structure["work_plan_heading_patterns"]}
        forbidden = [p for p in forbidden if p not in work_plan]
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
    typed_names: list[tuple[str, int, bool]] = []
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
                prefix = line[:m.start()].rstrip().removesuffix("[").rstrip()
                if name_precedes(prefix, meta.reference_surnames.get(key, set())):
                    typed_names.append((key, lineno, depth > 0))
    defined = set(meta.reference_ids)
    for key in sorted(set(cited) - defined):
        errors.append(f"cited key `@{key}` not defined in references (line {cited[key]})")
    for key in sorted(defined - set(cited)):
        warnings.append(f"reference `{key}` defined but never cited")
    for key, lineno, bracketed in typed_names:
        if bracketed:
            warnings.append(
                f"author name typed before `[@{key}]` (line {lineno}) — the name is a copy "
                f"that stops tracking the entry; write `@{key}` alone instead"
            )
        else:
            warnings.append(
                f"author name typed before `@{key}` (line {lineno}) — it renders twice "
                f"(\"Smith et al. Smith et al. [1]\"); write `@{key}` alone"
            )
    for key in sorted(set(author_in_text) & meta.reference_ids_without_names):
        warnings.append(
            f"`@{key}` is cited author-in-text but its reference declares no author or editor "
            f"(line {author_in_text[key]}) — it renders as the quoted title; use `[@{key}]` instead"
        )
    # key shape: AuthorYearFirstWord, e.g. Smith26Deep. An eval produced
    # `RiveraYearSurvey` — the literal word "Year" where the year belongs —
    # and nothing caught it. Warning class: an unusual author name can
    # legitimately produce an unusual key, and the proposal still resolves.
    for rid in sorted(set(meta.reference_ids)):
        if rid.lower() in BOOLEAN_LITERALS:
            continue  # already an error; one complaint per key is enough
        if not re.fullmatch(r"[A-Za-z][A-Za-z]*\d{2}[A-Za-z]+", rid):
            warnings.append(
                f"reference id `{rid}` does not follow `AuthorYearFirstWord` "
                f"(e.g. `Smith26Deep`) — a two-digit year between name and title word"
            )
        elif len(rid) >= KEY_MAX_LEN:
            warnings.append(
                f"reference id `{rid}` is {len(rid)} characters — keep keys under {KEY_MAX_LEN}"
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
    if meta.has_author_key:
        # the exception (a program requiring a named title page) is declared in
        # workspace guidance prose, which is not machine-readable — so warn always
        warnings.append(
            "`author:` found — proposals are anonymous by default; remove it "
            "unless your program requires a named cover page"
        )
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
    # identifies the exact content checked; a re-run with a differing digest
    # means the file changed between the runs (read-only mandate tripwire)
    print(f"digest: sha256:{hashlib.sha256(args.proposal.read_bytes()).hexdigest()}")
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
        "- whether the timeline names a real timeframe, and work plans the "
        "structure check cannot see (e.g. a Gantt chart pasted in as an image)\n"
        "- all semantic quality rules (analytical RQs, argument soundness) — see review skill\n"
        "\nThis check is advisory: it gates nothing."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
