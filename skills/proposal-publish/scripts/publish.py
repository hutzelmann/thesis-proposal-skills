#!/usr/bin/env python3
"""Build a proposal PDF (or fallback format) via pandoc.

Stdlib-only (Python >= 3.11). Engine resolution: typst (preferred) -> LaTeX
engine -> docx. Outputs (PDF + intermediate source) land next to the proposal;
build artifacts are added to the workspace .gitignore. --handout writes a
stripped markdown export (abstracts removed) instead of building.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
LATEX_ENGINES = ("tectonic", "xelatex", "lualatex", "pdflatex")
GITIGNORE_MARKER = "# proposal build artifacts (managed by proposal-publish)"
GITIGNORE_ENTRIES = ("*.pdf", "*.typ", "*.tex", "*.docx")

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


def proposal_lang(text: str) -> str:
    """Narrow extraction of the metadata `lang` value (not YAML parsing)."""
    m = re.search(r"^lang:\s*[\"']?([A-Za-z-]+)", text, re.MULTILINE)
    return m.group(1).lower() if m else "en"


def reference_section_title(lang: str) -> str:
    return "Literatur" if lang.startswith("de") else "References"


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
    present = {line.strip() for line in existing.splitlines()}
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


def pandoc_command(proposal: Path, kind: str, lang: str = "en") -> list[str]:
    """Converter invocation for one tier, minus its output and engine flags.

    Pure and side-effect free: the export tests and the typst CI script's drift
    guard read exactly what the shipped build path runs, instead of restating it.
    """
    base = [
        "pandoc", str(proposal),
        # order matters: author-intext expands "@key [see @other]" into a name
        # plus the intact two-citation group, which cite-split then brackets
        # before citeproc: @key gets its author name
        "--lua-filter", str(TEMPLATES / "author-intext.lua"),
        # before citeproc: one bracket per citation
        "--lua-filter", str(TEMPLATES / "cite-split.lua"),
        "--csl", str(TEMPLATES / "compact-numeric.csl"),
        "-M", f"reference-section-title={reference_section_title(lang)}",
        "--citeproc",
        "--lua-filter", str(TEMPLATES / "rq-filter.lua"),
        # last: numbers and styles [TODO: …] markers. After citeproc so a hint
        # never holds an unresolved citation, and after rq-filter because it
        # must not emit block content inside a research-question item
        "--lua-filter", str(TEMPLATES / "todo-filter.lua"),
    ]
    if kind == "typst":
        return [*base, "--template", str(TEMPLATES / "proposal.typ")]
    if kind == "latex":
        return [
            *base,
            "--number-sections",
            "--include-in-header", str(TEMPLATES / "latex-header.tex"),
            "-V", "papersize=a4", "-V", "geometry:margin=2.2cm", "-V", "fontsize=11pt",
        ]
    return base


def build(proposal: Path, kind: str, tool: str) -> list[Path]:
    stem = proposal.with_suffix("")
    lang = proposal_lang(proposal.read_text(encoding="utf-8"))
    cmd = pandoc_command(proposal, kind, lang)
    if kind == "typst":
        typ, pdf = stem.with_suffix(".typ"), stem.with_suffix(".pdf")
        run([*cmd, "-o", str(typ)])
        run(["typst", "compile", str(typ), str(pdf)])
        return [pdf, typ]
    if kind == "latex":
        tex, pdf = stem.with_suffix(".tex"), stem.with_suffix(".pdf")
        run([*cmd, "-s", "-o", str(tex)])
        run([*cmd, f"--pdf-engine={tool}", "-o", str(pdf)])
        return [pdf, tex]
    docx = stem.with_suffix(".docx")
    run([*cmd, "-o", str(docx)])
    return [docx]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--handout", action="store_true",
                        help="write a stripped markdown export instead of building")
    parser.add_argument("--force", action="store_true",
                        help="replace an existing handout that was edited after it was written")
    args = parser.parse_args(argv)
    proposal = args.proposal.resolve()

    if args.handout:
        target = proposal.with_name(proposal.stem + "-handout.md")
        export = strip_abstracts(proposal.read_text(encoding="utf-8"))
        # Every other output is an ignored build artifact this script owns. The
        # handout is not ignored, because it is meant to be kept and sent — so a
        # difference here is a hand edit, and discarding it is the user's call.
        edited = (not args.force and target.exists()
                  and target.read_text(encoding="utf-8") != export)
        if edited:
            print(
                f"{target.name} exists and differs from what would be written — "
                "it was edited after it was generated. Rename it, or re-run with "
                "--force to replace it.",
                file=sys.stderr,
            )
            return 2
        target.write_text(export, encoding="utf-8")
        print(
            f"handout written: {target.name} (abstracts stripped — "
            "rename to include your name before sending)"
        )
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
