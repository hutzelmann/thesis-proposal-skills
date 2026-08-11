#!/usr/bin/env python3
"""Build a proposal PDF (or fallback format) via pandoc.

Stdlib-only (Python >= 3.11). Engine resolution: typst (preferred) -> LaTeX
engine -> docx. Outputs (PDF + intermediate source) land next to the proposal;
build artifacts are added to the workspace .gitignore. --handout writes a
stripped markdown export (abstracts removed) instead of building.

A workspace may replace the built-in pipeline with a build definition of its
own beside the proposal. This script discovers one and hands over: it reports
what it found and exits 3 without building. It never runs the definition
itself -- executing workspace code is the agent's job, not a shipped script's.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
LATEX_ENGINES = ("tectonic", "xelatex", "lualatex", "pdflatex")
GITIGNORE_MARKER = "# proposal build artifacts (managed by proposal-publish)"
GITIGNORE_ENTRIES = ("*.pdf", "*.typ", "*.tex", "*.docx")

# Workspace-supplied build. BUILD_STEM matches `proposal-build` with or without
# a suffix, so a workspace picks whatever it likes; RECIPE_RUNNERS entries count
# only when the file declares the target, so an unrelated Makefile in the
# workspace is not mistaken for a proposal build.
BUILD_STEM = "proposal-build"
RECIPE_RUNNERS = {"makefile": "make", "gnumakefile": "make", "justfile": "just"}
# make writes `proposal-build:`, just writes `proposal-build proposal:` — one
# line-anchored pattern covers both. Narrow extraction, not recipe parsing.
RECIPE_TARGET_RE = re.compile(rf"^{BUILD_STEM}\b[^\n]*:", re.MULTILINE)
HANDOVER_EXIT = 3
PROPOSAL_ENV = "PROPOSAL_PATH"

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


@dataclass(frozen=True)
class WorkspaceBuild:
    """A build definition the workspace supplies beside the proposal."""

    path: Path
    target: str | None = None  # recipe files only
    runner: str | None = None  # advisory command name, never a dispatch table

    def describe(self) -> str:
        if self.target is None:
            return self.path.name
        return f"{self.path.name} (target `{self.target}`)"


def find_workspace_build(proposal: Path) -> list[WorkspaceBuild]:
    """Build definitions beside the proposal — never above it.

    One pass over the directory rather than a lookup per candidate name: on a
    case-insensitive filesystem `Makefile` and `makefile` are the same file, and
    a per-name lookup would find it twice and trip the ambiguity refusal.
    """
    found: list[WorkspaceBuild] = []
    for entry in sorted(proposal.parent.iterdir(), key=lambda p: p.name):
        if not entry.is_file():
            continue
        if entry.name == BUILD_STEM or entry.name.startswith(BUILD_STEM + "."):
            found.append(WorkspaceBuild(entry))
            continue
        runner = RECIPE_RUNNERS.get(entry.name.lower().lstrip("."))
        # errors="replace": a recipe file in some other encoding must not crash
        # a build, and the target pattern is pure ASCII either way
        if runner and RECIPE_TARGET_RE.search(
            entry.read_text(encoding="utf-8", errors="replace")
        ):
            found.append(WorkspaceBuild(entry, BUILD_STEM, runner))
    return found


def report_handover(found: list[WorkspaceBuild], proposal: Path) -> int:
    """Report the workspace build definition and hand over without building.

    Nothing here runs the definition: a shipped script must not execute a path
    it discovered in the workspace (tests/unit/test_audit_invariants.py). The
    agent that invoked this script runs it, which is also why the built-in
    pipeline is unreachable from here — a fallback would quietly produce the
    default layout for a workspace that asked for a different one.
    """
    if len(found) > 1:
        print(
            "more than one workspace build definition beside the proposal: "
            + ", ".join(b.describe() for b in found)
            + "\nnothing was built and none was chosen — keep one, or pass "
            "--builtin for the built-in pipeline.",
            file=sys.stderr,
        )
        return HANDOVER_EXIT
    definition = found[0]
    how = (
        f"Run it with {PROPOSAL_ENV}={proposal} set in the environment; it also "
        "receives that path as its first argument."
        if definition.runner is None
        else f"Run it with: {PROPOSAL_ENV}={proposal} {definition.runner} {definition.target}"
    )
    print(
        f"workspace build definition found: {definition.describe()} — publish built "
        f"nothing, and the built-in pipeline is not used.\n{how}\n"
        "This is a handover, not a failure. --builtin builds with the built-in "
        "pipeline instead.",
        file=sys.stderr,
    )
    return HANDOVER_EXIT


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
    parser.add_argument("--builtin", action="store_true",
                        help="ignore a workspace build definition and use the built-in pipeline")
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

    # After the handout branch, so the hand-in export is never delegated — it is
    # a transform of the proposal source, not a rendered document. Before engine
    # resolution, so a delegating workspace is never told to install a toolchain
    # it does not need.
    if not args.builtin and (found := find_workspace_build(proposal)):
        return report_handover(found, proposal)

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
