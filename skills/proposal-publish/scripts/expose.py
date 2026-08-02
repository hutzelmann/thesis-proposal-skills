#!/usr/bin/env python3
"""Render a proposal markdown file into an Overleaf-ready LaTeX exposé project.

Stdlib-only (Python >= 3.11) and deliberately free of pandoc: the student
should be able to produce the project on a machine with nothing installed and
upload it to Overleaf, which runs the pdflatex -> bibtex -> pdflatex x2 cycle.

The markdown vocabulary this converts is exactly the one the proposal format
uses (documented in shared/guidelines/guidelines.md): ATX headings, paragraphs
of one sentence per line, ordered and unordered lists, pipe tables, images,
emphasis, inline code, and `[@key]` / `@key` citations. Anything outside that
vocabulary is passed through escaped rather than silently dropped.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "expose"

BABEL = {"en": "ngerman, english", "de": "english, ngerman"}

# Title-page fields: metadata key -> (placeholder, fallback shown when absent)
TITLE_FIELDS = {
    "title": ("{{TITLE}}", "[TODO: add title]"),
    "author": ("{{AUTHOR}}", "[TODO: add author]"),
    "student_id": ("{{STUDENT_ID}}", "[TODO: add student ID]"),
    "degree_program": ("{{DEGREE_PROGRAM}}", "[TODO: add degree program]"),
    "supervisor": ("{{SUPERVISOR}}", "[TODO: add first supervisor]"),
    "second_supervisor": ("{{SECOND_SUPERVISOR}}", "TBD"),
    "submission_date": ("{{SUBMISSION_DATE}}", "[TODO: add submission date]"),
}

LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


class ExposeError(Exception):
    """Raised for source problems the student must fix before publishing."""


# ---------- metadata ---------------------------------------------------------

def split_source(text: str) -> tuple[str, str]:
    """Return (body, metadata_block). Mirrors check.py's narrow extraction."""
    lines = text.rstrip("\n").split("\n")
    delim = [i for i, line in enumerate(lines) if re.fullmatch(r"---\s*", line)]
    if len(delim) < 2 or delim[-1] != len(lines) - 1:
        raise ExposeError("no trailing metadata block found — the file must end with a `---` block")
    start, end = delim[-2], delim[-1]
    return "\n".join(lines[:start]), "\n".join(lines[start + 1 : end])


def scalar(block: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", block, re.MULTILINE)
    if not m:
        return None
    value = m.group(1).strip()
    if value.startswith(("'", '"')) and value.endswith(("'", '"')) and len(value) > 1:
        value = value[1:-1]
    return value or None


def abbreviations(block: str) -> list[tuple[str, str]]:
    """Parse the optional `abbreviations:` mapping into (short, long) pairs."""
    m = re.search(r"^abbreviations:\s*$((?:\n[ \t]+.+|\n\s*)*)", block, re.MULTILINE)
    if not m:
        return []
    pairs = []
    for line in m.group(1).split("\n"):
        entry = re.match(r"^\s+([A-Za-z0-9][\w.+-]*)\s*:\s*(.+?)\s*$", line)
        if entry:
            pairs.append((entry.group(1), entry.group(2).strip().strip("'\"")))
    return pairs


def references(block: str) -> list[dict]:
    """Parse the CSL-YAML `references:` list. Narrow extraction, no YAML parser."""
    m = re.search(r"^references:\s*(?:\[\s*\])?\s*$((?:\n.*)*)", block, re.MULTILINE)
    if not m:
        return []
    entries: list[dict] = []
    current: dict | None = None
    in_authors = False
    for raw in m.group(1).split("\n"):
        if re.match(r"^\s*-\s+id:\s*\S+", raw):
            current = {"authors": []}
            current["id"] = re.match(r"^\s*-\s+id:\s*(\S+)", raw).group(1)
            entries.append(current)
            in_authors = False
            continue
        if current is None:
            continue
        if re.match(r"^\s+author:\s*$", raw):
            in_authors = True
            continue
        if in_authors:
            if fam := re.match(r"^\s*-\s+family:\s*(.+?)\s*$", raw):
                current["authors"].append({"family": fam.group(1).strip("'\"")})
                continue
            if lit := re.match(r"^\s*-\s+literal:\s*(.+?)\s*$", raw):
                current["authors"].append({"literal": lit.group(1).strip("'\"")})
                continue
            if giv := re.match(r"^\s+given:\s*(.+?)\s*$", raw):
                if current["authors"]:
                    current["authors"][-1]["given"] = giv.group(1).strip("'\"")
                continue
            if re.match(r"^\s+\w[\w-]*:", raw):
                in_authors = False
        for field in ("type", "title", "container-title", "DOI", "URL", "publisher"):
            if fm := re.match(rf"^\s+{re.escape(field)}:\s*(.+?)\s*$", raw):
                current[field] = fm.group(1).strip().strip("'\"")
        if ym := re.match(r"^\s+year:\s*(\d{4})", raw):
            current["year"] = ym.group(1)
    return entries


# ---------- BibTeX -----------------------------------------------------------

CSL_TO_BIBTEX = {
    "article-journal": "article",
    "paper-conference": "inproceedings",
    "book": "book",
    "chapter": "incollection",
    "thesis": "phdthesis",
    "report": "techreport",
    "webpage": "misc",
    "article": "misc",
}


def bib_author(entry: dict) -> str | None:
    names = []
    for a in entry.get("authors", []):
        if "literal" in a:
            names.append(f"{{{a['literal']}}}")
        elif "given" in a:
            names.append(f"{a['family']}, {a['given']}")
        else:
            names.append(a["family"])
    return " and ".join(names) or None


def to_bibtex(entries: list[dict]) -> str:
    out = [
        "% ============================================================",
        "%  literature.bib — generated by the proposal-publish skill",
        "%  Edit the references block of the source markdown, not this file.",
        "% ============================================================",
        "",
    ]
    for e in entries:
        kind = CSL_TO_BIBTEX.get(e.get("type", ""), "misc")
        fields: list[tuple[str, str]] = []
        if author := bib_author(e):
            fields.append(("author", author))
        if "title" in e:
            fields.append(("title", f"{{{e['title']}}}"))  # braces preserve capitalisation
        container = e.get("container-title")
        if container:
            fields.append(("journal" if kind == "article" else "booktitle", container))
        if "year" in e:
            fields.append(("year", e["year"]))
        if "publisher" in e:
            fields.append(("publisher", e["publisher"]))
        if "DOI" in e:
            fields.append(("doi", e["DOI"]))
        elif "URL" in e:
            fields.append(("url", e["URL"]))
        if kind == "misc" and not container and "URL" not in e and "DOI" not in e:
            fields.append(("note", "no venue recorded"))
        body = ",\n".join(f"    {k:<10}= {{{v}}}" for k, v in fields)
        out.append(f"@{kind}{{{e['id']},\n{body},\n}}\n")
    return "\n".join(out)


# ---------- markdown -> LaTeX ------------------------------------------------

def escape(text: str) -> str:
    return "".join(LATEX_SPECIALS.get(c, c) for c in text)


def inline(text: str) -> str:
    """Convert inline markdown to LaTeX, protecting citations from escaping."""
    shelf: list[str] = []

    def stash(latex: str) -> str:
        shelf.append(latex)
        return f"\x00{len(shelf) - 1}\x00"

    # Citations first: `[@a; @b]` -> \cite{a,b}; bare `@a` -> \citet{a}.
    # Keys may legitimately contain dots, so trailing sentence punctuation is
    # stripped off the match and re-emitted after the command — otherwise
    # "@Smith26Deep." cites the non-existent key "Smith26Deep.".
    def bracketed(m: re.Match) -> str:
        keys = [k.rstrip(".,;:") for k in re.findall(r"@([A-Za-z][\w:.-]*)", m.group(1))]
        return stash(r"\cite{" + ",".join(keys) + "}") if keys else m.group(0)

    def author_in_text(m: re.Match) -> str:
        key = m.group(1)
        trailing = len(key) - len(key.rstrip(".,;:"))
        stripped = key[: len(key) - trailing] if trailing else key
        return stash(r"\citet{" + stripped + "}") + key[len(stripped):]

    text = re.sub(r"\[([^\]]*@[^\]]*)\]", bracketed, text)
    text = re.sub(r"(?<![\w.])@([A-Za-z][\w:.-]*)", author_in_text, text)
    # Inline code before escaping, so its contents survive verbatim.
    text = re.sub(r"`([^`]+)`", lambda m: stash(r"\texttt{" + escape(m.group(1)) + "}"), text)

    text = escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\\emph{\1}", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: shelf[int(m.group(1))], text)


def gantt(rows: list[tuple[str, int, int]], span: int) -> str:
    """Render work-plan rows as the template's pgfgantt chart."""
    palette = ["barblue", "barpurple", "barteal", "bargreen", "barorange"]
    lines = [
        r"\noindent",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{ganttchart}[",
        "    x unit=0.6cm, y unit title=0.55cm, y unit chart=0.6cm,",
        "    canvas/.append style={draw=none},",
        "    vgrid={*1{draw=gridcolor, thin}}, hgrid={*1{draw=gridcolor, thin}},",
        "    title/.style={draw=none, fill=none},",
        r"    title label font=\bfseries\footnotesize\color{black!70},",
        "    include title in canvas=false,",
        r"    bar height=0.5, bar label font=\footnotesize,",
        "    bar/.append style={draw=none},",
        "    milestone/.append style={fill=barred, draw=barred, rounded corners=1pt, xscale=0.7},",
        r"    milestone label font=\tiny\itshape,",
        "    link/.style={-latex, thick, draw=linkgray!60}, link bulge=4,",
        f"]{{1}}{{{span}}}",
        "",
        f"    \\gantttitle{{Thesis Schedule in Weeks}}{{{span}}} \\\\",
        f"    \\gantttitlelist{{1,...,{span}}}{{1}} \\\\",
        "",
    ]
    for i, (label, start, end) in enumerate(rows):
        colour = palette[i % len(palette)]
        if start == end:
            lines.append(f"    \\ganttmilestone{{{inline(label)}}}{{{start}}} \\\\")
        else:
            lines.append(
                f"    \\ganttbar[bar/.append style={{fill={colour}}}]"
                f"{{{inline(label)}}}{{{start}}}{{{end}}} \\\\"
            )
    lines += ["", r"\end{ganttchart}", "}% end resizebox"]
    return "\n".join(lines)


WEEK_RANGE = re.compile(r"(\d+)\s*(?:[-–—]|to|bis)\s*(\d+)")


def parse_work_plan_table(table: list[list[str]]) -> tuple[list[tuple[str, int, int]], int] | None:
    """Extract (label, start_week, end_week) rows from a work-plan pipe table.

    Accepts either a single `Weeks` column holding a range ("5–8", "12") or a
    separate start and end column. Returns None when no row yields a range, so
    the caller can fall back to rendering a plain table.
    """
    if len(table) < 2:
        return None
    header = [c.lower() for c in table[0]]
    rows: list[tuple[str, int, int]] = []
    for cells in table[1:]:
        if not cells:
            continue
        label = cells[0].strip()
        start = end = None
        for idx, cell in enumerate(cells[1:], start=1):
            if m := WEEK_RANGE.search(cell):
                start, end = int(m.group(1)), int(m.group(2))
                break
            if cell.strip().isdigit():
                header_name = header[idx] if idx < len(header) else ""
                if start is None and "end" not in header_name:
                    start = int(cell.strip())
                elif end is None:
                    end = int(cell.strip())
        if start is None:
            continue
        if end is None:
            end = start
        if end < start:
            start, end = end, start
        if label:
            rows.append((label, start, end))
    if not rows:
        return None
    return rows, max(end for _, _, end in rows)


def render_table(table: list[list[str]]) -> str:
    width = max(len(r) for r in table)
    spec = "l" * width
    out = [r"\begin{center}", f"\\begin{{tabular}}{{{spec}}}", r"\toprule"]
    head = table[0] + [""] * (width - len(table[0]))
    out.append(" & ".join(rf"\textbf{{{inline(c)}}}" for c in head) + r" \\")
    out.append(r"\midrule")
    for row in table[1:]:
        padded = row + [""] * (width - len(row))
        out.append(" & ".join(inline(c) for c in padded) + r" \\")
    out += [r"\bottomrule", r"\end{tabular}", r"\end{center}"]
    return "\n".join(out)


def convert_body(body: str, work_plan_title: str, meth_prefix: str) -> tuple[str, list[str]]:
    """Convert the markdown body to LaTeX. Returns (latex, notes).

    `meth_prefix` is the methodology heading stem ("Methodology: "); the branch
    name after it is dropped, because the template renders a plain "Methodology"
    section while the source keeps the branch for the check script.
    """
    notes: list[str] = []
    out: list[str] = []
    lines = body.split("\n")
    i = 0
    in_work_plan = False
    list_stack: list[str] = []

    def close_lists() -> None:
        while list_stack:
            out.append(rf"\end{{{list_stack.pop()}}}")

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if heading := re.match(r"^(#{1,6})\s+(.+?)\s*$", line):
            close_lists()
            level, title = len(heading.group(1)), heading.group(2).strip()
            if level == 1:
                shown = meth_prefix.rstrip(": ") if title.startswith(meth_prefix) else title
                in_work_plan = title == work_plan_title
                out += ["", rf"\section{{{inline(shown)}}}", ""]
            else:
                cmd = "subsection" if level == 2 else "subsubsection"
                out += ["", rf"\{cmd}{{{inline(title)}}}", ""]
            i += 1
            continue

        if not stripped:
            close_lists()
            out.append("")
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and re.match(
            r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]
        ):
            table: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = lines[i].strip().strip("|")
                if not re.match(r"^[\s:|-]+$", row):
                    table.append([c.strip() for c in row.split("|")])
                i += 1
            close_lists()
            parsed = parse_work_plan_table(table) if in_work_plan else None
            if parsed:
                rows, span = parsed
                out += ["", gantt(rows, span), ""]
            else:
                if in_work_plan:
                    notes.append(
                        "work-plan table has no week ranges — rendered as a plain table "
                        "instead of a Gantt chart; give each row a `Weeks` column like `5-8`"
                    )
                out += ["", render_table(table), ""]
            continue

        if item := re.match(r"^\s*(\d+)[.)]\s+(.+)$", line):
            if "enumerate" not in list_stack:
                close_lists()
                out.append(r"\begin{enumerate}")
                list_stack.append("enumerate")
            out.append(rf"    \item {inline(item.group(2).strip())}")
            i += 1
            continue

        if item := re.match(r"^\s*[-*+]\s+(.+)$", line):
            if "itemize" not in list_stack:
                close_lists()
                out.append(r"\begin{itemize}")
                list_stack.append("itemize")
            out.append(rf"    \item {inline(item.group(1).strip())}")
            i += 1
            continue

        if figure := re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped):
            close_lists()
            caption, path = figure.group(1), figure.group(2)
            caption = re.sub(r"^Figure\s*\d+:\s*", "", caption).strip()
            out += [
                "",
                r"\begin{figure}[H]",
                r"    \centering",
                rf"    \includegraphics[width=0.9\textwidth]{{{path}}}",
                rf"    \caption{{{inline(caption)}}}" if caption else "",
                r"\end{figure}",
                "",
            ]
            i += 1
            continue

        if stripped.startswith("<!--"):
            i += 1
            continue

        close_lists()
        out.append(inline(stripped))
        i += 1

    close_lists()
    latex = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", latex).strip() + "\n", notes


# ---------- assembly ---------------------------------------------------------

def glossary_blocks(pairs: list[tuple[str, str]]) -> tuple[str, str]:
    """Return (preamble, print) LaTeX. Both empty when there are no abbreviations."""
    if not pairs:
        return "", ""
    entries = "\n".join(
        rf"\newglossaryentry{{{short}}}{{name={{{short}}}, description={{{escape(long)}}}}}"
        for short, long in pairs
    )
    preamble = "\\usepackage[toc]{glossaries}\n\\makeglossaries\n\n" + entries
    widest = max((p[0] for p in pairs), key=len)
    printed = "\n".join([
        r"\thispagestyle{myPageStyle}",
        rf"\glssetwidest{{{widest}}}",
        r"\setglossarystyle{alttree}",
        r"\printglossary[title=List of Abbreviations, toctitle=List of Abbreviations]",
        r"\cleardoublepage",
    ])
    return preamble, printed


def build(source: Path, out_dir: Path, structure: dict) -> list[str]:
    """Write the LaTeX project into out_dir. Returns human-readable notes."""
    text = source.read_text(encoding="utf-8")
    body_md, meta = split_source(text)
    lang = (scalar(meta, "lang") or "en").strip()
    if lang not in BABEL:
        lang = "en"
    work_plan_title = structure["sections"]["titles"]["work_plan"][lang]
    meth_prefix = structure["sections"]["titles"]["methodology"][lang].split("{")[0]

    latex_body, notes = convert_body(body_md, work_plan_title, meth_prefix)
    entries = references(meta)
    if not entries:
        notes.append("no references found — the bibliography will be empty")
    glossary_pre, glossary_print = glossary_blocks(abbreviations(meta))

    template = (TEMPLATE_DIR / "expose.tex.in").read_text(encoding="utf-8")
    filled = template
    for key, (placeholder, fallback) in TITLE_FIELDS.items():
        value = scalar(meta, key) or fallback
        if value.startswith("[TODO:"):
            notes.append(f"title page: `{key}` missing — placeholder kept in the .tex")
        filled = filled.replace(placeholder, escape(value))
    filled = (
        filled.replace("{{BABEL_LANGS}}", BABEL[lang])
        .replace("{{SOURCE_FILE}}", source.name)
        .replace("{{GLOSSARY_PREAMBLE}}", glossary_pre)
        .replace("{{GLOSSARY_PRINT}}", glossary_print)
        .replace("{{BODY}}", latex_body)
    )
    if remaining := re.findall(r"\{\{([A-Z_]+)\}\}", filled):
        raise ExposeError(f"template placeholders left unfilled: {', '.join(sorted(set(remaining)))}")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "expose.tex").write_text(filled, encoding="utf-8")
    (out_dir / "literature.bib").write_text(to_bibtex(entries), encoding="utf-8")
    images_out = out_dir / "images"
    images_out.mkdir(exist_ok=True)
    shutil.copy(TEMPLATE_DIR / "images" / "thiRGB.jpg", images_out / "thiRGB.jpg")
    local_images = source.parent / "img"
    if local_images.is_dir():
        for image in local_images.iterdir():
            if image.is_file():
                shutil.copy(image, images_out / image.name)
        notes.append(f"copied {sum(1 for f in local_images.iterdir() if f.is_file())} figure(s) "
                     "from img/ into images/ — figure paths in the .tex point at images/")
    return notes
