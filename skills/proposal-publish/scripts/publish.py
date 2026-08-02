#!/usr/bin/env python3
"""Build the exposé deliverable from a proposal markdown file.

Stdlib-only (Python >= 3.11). The default output is an Overleaf-ready LaTeX
project (expose.tex + literature.bib + images/) rendered from the THI exposé
template — no pandoc, no typst, no local TeX required.

`--pdf` instead runs the older pandoc pipeline for a quick local preview
(typst -> LaTeX engine -> docx); `--handout` writes a stripped markdown export.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import expose as expose_mod

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
LATEX_ENGINES = ("tectonic", "xelatex", "lualatex", "pdflatex")
GITIGNORE_MARKER = "# proposal build artifacts (managed by proposal-publish)"
GITIGNORE_ENTRIES = ("*.pdf", "*.typ", "*.tex", "*.docx")
STRUCTURE = Path(__file__).resolve().parent.parent / "references" / "structure.json"

INSTALL_HINT = (
    "For PDF output install pandoc + typst (two single binaries):\n"
    "  Windows: winget install --id JohnMacFarlane.Pandoc Typst.Typst\n"
    "  macOS:   brew install pandoc typst\n"
    "  Linux:   pandoc + typst via your package manager\n"
    "An existing TeX installation also works as fallback (only pandoc needed)."
)


def resolve_engine(which=shutil.which) -> tuple[str, str] | None:
    """Return (kind, tool) for the best available pipeline, or None without pandoc."""
    if not which("pandoc"):
        return None
    if which("typst"):
        return ("typst", "typst")
    for engine in LATEX_ENGINES:
        if which(engine):
            return ("latex", engine)
    return ("docx", "pandoc")


def strip_abstracts(text: str) -> str:
    """Remove abstract fields (incl. indented continuation lines) from the metadata block."""
    lines = text.split("\n")
    out: list[str] = []
    skipping_indent: int | None = None
    blank_buffer: list[str] = []
    for line in lines:
        if skipping_indent is not None:
            if not line.strip():
                blank_buffer.append(line)  # may belong to a block-scalar abstract
                continue
            if (len(line) - len(line.lstrip())) > skipping_indent:
                blank_buffer = []  # blanks were inside the abstract — drop them
                continue
            out.extend(blank_buffer)
            blank_buffer = []
            skipping_indent = None
        if m := re.match(r"^(\s+)abstract:", line):
            skipping_indent = len(m.group(1))
            continue
        out.append(line)
    out.extend(blank_buffer)
    return "\n".join(out)


def ensure_gitignore(workspace: Path) -> None:
    gitignore = workspace / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    present = {l.strip() for l in existing.splitlines()}
    missing = [e for e in GITIGNORE_ENTRIES if e not in present]
    if not missing:
        return
    block = ("\n" if existing and not existing.endswith("\n") else "")
    if GITIGNORE_MARKER not in present:
        block += GITIGNORE_MARKER + "\n"
    block += "\n".join(missing) + "\n"
    gitignore.write_text(existing + block, encoding="utf-8")


def run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"build failed: {' '.join(cmd[:2])} …\n{result.stderr.strip()[-2000:]}")


def build(proposal: Path, kind: str, tool: str) -> list[Path]:
    stem = proposal.with_suffix("")
    base = [
        "pandoc", str(proposal),
        "--lua-filter", str(TEMPLATES / "cite-split.lua"),  # before citeproc: one bracket per citation
        "--csl", str(TEMPLATES / "compact-numeric.csl"),
        "--citeproc",
        "--lua-filter", str(TEMPLATES / "rq-filter.lua"),
    ]
    if kind == "typst":
        typ, pdf = stem.with_suffix(".typ"), stem.with_suffix(".pdf")
        run(base + ["--template", str(TEMPLATES / "proposal.typ"), "-o", str(typ)])
        run(["typst", "compile", str(typ), str(pdf)])
        return [pdf, typ]
    if kind == "latex":
        latex_opts = [
            "--number-sections",
            "--include-in-header", str(TEMPLATES / "latex-header.tex"),
            "-V", "papersize=a4", "-V", "geometry:margin=1in", "-V", "fontsize=11pt",
        ]
        tex, pdf = stem.with_suffix(".tex"), stem.with_suffix(".pdf")
        run(base + latex_opts + ["-s", "-o", str(tex)])
        run(base + latex_opts + [f"--pdf-engine={tool}", "-o", str(pdf)])
        return [pdf, tex]
    docx = stem.with_suffix(".docx")
    run(base + ["-o", str(docx)])
    return [docx]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--handout", action="store_true",
                        help="write a stripped markdown export instead of building")
    parser.add_argument("--pdf", action="store_true",
                        help="build a quick local PDF via pandoc instead of the LaTeX project")
    parser.add_argument("--out", type=Path, default=None,
                        help="directory for the LaTeX project (default: <slug>-expose/)")
    args = parser.parse_args()
    proposal = args.proposal.resolve()

    if not args.handout and not args.pdf:
        out_dir = (args.out or proposal.with_name(proposal.stem + "-expose")).resolve()
        structure = json.loads(STRUCTURE.read_text(encoding="utf-8"))
        try:
            notes = expose_mod.build(proposal, out_dir, structure)
        except expose_mod.ExposeError as exc:
            print(f"cannot build the exposé project: {exc}", file=sys.stderr)
            return 2
        print(f"LaTeX project written: {out_dir.name}/ (expose.tex, literature.bib, images/)")
        for note in notes:
            print(f"  note: {note}", file=sys.stderr)
        print("Upload the folder to Overleaf (New Project -> Upload Project) and set "
              "expose.tex as the main document; Overleaf runs pdflatex/bibtex for you.")
        return 0

    if args.handout:
        target = proposal.with_name(proposal.stem + "-handout.md")
        target.write_text(strip_abstracts(proposal.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"handout written: {target.name} (abstracts stripped — rename to include your name before sending)")
        return 0

    resolved = resolve_engine()
    if resolved is None:
        print("pandoc not found — no build possible.\n" + INSTALL_HINT, file=sys.stderr)
        return 2
    kind, tool = resolved
    if kind == "docx":
        print("no PDF engine found — falling back to docx.\n" + INSTALL_HINT, file=sys.stderr)
    elif kind == "latex":
        print("note: built via LaTeX — installing typst gives the preferred, faster pipeline "
              "(brew/winget/package manager: typst)", file=sys.stderr)
    outputs = build(proposal, kind, tool)
    ensure_gitignore(proposal.parent)
    print(f"built via {tool}: " + ", ".join(o.name for o in outputs))
    if kind != "docx":
        print("rename the PDF to include your name before sending it to your supervisor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
