"""L0: publish.py offline logic (skill-publish spec)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skills" / "proposal-publish" / "scripts"))

import publish  # noqa: E402


def which_factory(available):
    return lambda name: f"/usr/bin/{name}" if name in available else None


def test_engine_resolution_order():
    assert publish.resolve_engine(which_factory({"pandoc", "typst", "xelatex"})) == ("typst", "typst")
    assert publish.resolve_engine(which_factory({"pandoc", "xelatex"})) == ("latex", "xelatex")
    assert publish.resolve_engine(which_factory({"pandoc", "tectonic"})) == ("latex", "tectonic")
    assert publish.resolve_engine(which_factory({"pandoc"})) == ("docx", "pandoc")
    assert publish.resolve_engine(which_factory(set())) is None


def test_strip_abstracts_removes_continuations():
    text = (
        "Body text.\n\n---\nreferences:\n- id: A1\n  title: T\n"
        "  abstract: first line\n    continued deeper line\n  DOI: 10.1/x\n---\n"
    )
    stripped = publish.strip_abstracts(text)
    assert "abstract" not in stripped
    assert "continued" not in stripped
    assert "DOI: 10.1/x" in stripped
    assert "Body text." in stripped


def test_ensure_gitignore_idempotent(tmp_path):
    publish.ensure_gitignore(tmp_path)
    first = (tmp_path / ".gitignore").read_text()
    assert "*.pdf" in first and publish.GITIGNORE_MARKER in first
    publish.ensure_gitignore(tmp_path)
    assert (tmp_path / ".gitignore").read_text() == first


def test_ensure_gitignore_appends_only_missing(tmp_path):
    (tmp_path / ".gitignore").write_text("*.pdf\n")
    publish.ensure_gitignore(tmp_path)
    content = (tmp_path / ".gitignore").read_text()
    assert content.count("*.pdf") == 1
    assert "*.typ" in content


def test_strip_abstracts_block_scalar_with_blank_lines():
    text = (
        "Body.\n\n---\nreferences:\n- id: A1\n  title: T\n"
        "  abstract: >-\n    Para one.\n\n    Para two of abstract.\n"
        "  DOI: 10.1/x\n---\n"
    )
    stripped = publish.strip_abstracts(text)
    assert "Para two" not in stripped and "Para one" not in stripped
    assert "DOI: 10.1/x" in stripped
