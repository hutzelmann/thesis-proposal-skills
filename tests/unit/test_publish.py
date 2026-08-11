"""L0: publish.py offline logic (skill-publish spec)."""

import fnmatch
import shutil
from pathlib import Path

import publish

REPO = Path(__file__).resolve().parents[2]


def which_factory(available):
    return lambda name: f"/usr/bin/{name}" if name in available else None


def test_engine_resolution_order():
    assert publish.resolve_engine(
        which_factory({"pandoc", "typst", "xelatex"})
    ) == ("typst", "typst")
    assert publish.resolve_engine(which_factory({"pandoc", "xelatex"})) == ("latex", "xelatex")
    assert publish.resolve_engine(which_factory({"pandoc", "tectonic"})) == ("latex", "tectonic")
    assert publish.resolve_engine(which_factory({"pandoc"})) == ("docx", "pandoc")
    assert publish.resolve_engine(which_factory(set())) is None


def test_proposal_lang_extraction():
    assert publish.proposal_lang("---\ntitle: T\nlang: de\n---\n") == "de"
    assert publish.proposal_lang('---\nlang: "de-AT"\n---\n') == "de-at"
    assert publish.proposal_lang("---\ntitle: T\n---\n") == "en"
    # a body mention must not match: the pattern is anchored to line starts
    assert publish.proposal_lang("The word lang: de appears mid-sentence.") == "en"


def test_reference_section_title_localized():
    assert publish.reference_section_title("en") == "References"
    assert publish.reference_section_title("de") == "Literatur"
    assert publish.reference_section_title("de-at") == "Literatur"


def test_pandoc_command_carries_reference_section_title():
    for kind in ("typst", "latex", "docx"):
        cmd = publish.pandoc_command(Path("proposal.md"), kind, "de")
        flag = cmd[cmd.index("-M") + 1]
        assert flag == "reference-section-title=Literatur"
        # the headline must exist before citeproc builds the reference list
        assert cmd.index("-M") < cmd.index("--citeproc")
    assert "reference-section-title=References" in publish.pandoc_command(Path("p.md"), "typst")


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
    first = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "*.pdf" in first
    assert publish.GITIGNORE_MARKER in first
    publish.ensure_gitignore(tmp_path)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == first


def test_ensure_gitignore_appends_only_missing(tmp_path):
    (tmp_path / ".gitignore").write_text("*.pdf\n", encoding="utf-8")
    publish.ensure_gitignore(tmp_path)
    content = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert content.count("*.pdf") == 1
    assert "*.typ" in content


SOURCE = (
    "Body text.\n\n---\nreferences:\n- id: A1\n  title: T\n"
    "  abstract: some abstract\n  DOI: 10.1/x\n---\n"
)


def seeded(tmp_path):
    proposal = tmp_path / "topic.md"
    proposal.write_text(SOURCE, encoding="utf-8")
    return proposal, tmp_path / "topic-handout.md"


def test_handout_written_when_absent(tmp_path):
    proposal, handout = seeded(tmp_path)
    assert publish.main([str(proposal), "--handout"]) == 0
    assert "abstract" not in handout.read_text(encoding="utf-8")


def test_handout_rewrite_of_identical_content_is_silent(tmp_path):
    """An unchanged rebuild must stay free — the guard is about hand edits."""
    proposal, handout = seeded(tmp_path)
    publish.main([str(proposal), "--handout"])
    assert publish.main([str(proposal), "--handout"]) == 0
    assert handout.exists()


def test_edited_handout_is_not_overwritten(tmp_path, capsys):
    """The handout is the one publish output that is not gitignored, because it
    is meant to be kept and sent. A difference is therefore a hand edit."""
    proposal, handout = seeded(tmp_path)
    publish.main([str(proposal), "--handout"])
    handout.write_text("Body text, fixed by hand.\n", encoding="utf-8")
    before = handout.read_text(encoding="utf-8")
    assert publish.main([str(proposal), "--handout"]) == 2
    assert handout.read_text(encoding="utf-8") == before
    assert "--force" in capsys.readouterr().err


def test_force_replaces_an_edited_handout(tmp_path):
    proposal, handout = seeded(tmp_path)
    publish.main([str(proposal), "--handout"])
    handout.write_text("Body text, fixed by hand.\n", encoding="utf-8")
    assert publish.main([str(proposal), "--handout", "--force"]) == 0
    assert "fixed by hand" not in handout.read_text(encoding="utf-8")


def test_strip_abstracts_block_scalar_with_blank_lines():
    text = (
        "Body.\n\n---\nreferences:\n- id: A1\n  title: T\n"
        "  abstract: >-\n    Para one.\n\n    Para two of abstract.\n"
        "  DOI: 10.1/x\n---\n"
    )
    stripped = publish.strip_abstracts(text)
    assert "Para two" not in stripped
    assert "Para one" not in stripped
    assert "DOI: 10.1/x" in stripped


# -- workspace-supplied build (skill-publish spec) -------------------------

def delegating(tmp_path, name="proposal-build.py", body="print('built')\n"):
    """A workspace holding a proposal and one build definition."""
    proposal, _ = seeded(tmp_path)
    (tmp_path / name).write_text(body, encoding="utf-8")
    return proposal


MAKEFILE = "all:\n\techo hi\n\nproposal-build:\n\tpandoc $(PROPOSAL_PATH) -o out.pdf\n"
JUSTFILE = "default:\n  echo hi\n\nproposal-build proposal:\n  pandoc {{proposal}}\n"


def test_build_file_discovered_with_and_without_suffix(tmp_path):
    proposal, _ = seeded(tmp_path)
    (tmp_path / "proposal-build").write_text("#!/bin/sh\n", encoding="utf-8")
    found = publish.find_workspace_build(proposal)
    assert [b.path.name for b in found] == ["proposal-build"]
    (tmp_path / "proposal-build.py").write_text("x = 1\n", encoding="utf-8")
    assert len(publish.find_workspace_build(proposal)) == 2


def test_unrelated_names_are_not_build_definitions(tmp_path):
    proposal, _ = seeded(tmp_path)
    for name in ("build.sh", "proposal-build-old.sh", "myproposal-build.py"):
        (tmp_path / name).write_text("x\n", encoding="utf-8")
    assert publish.find_workspace_build(proposal) == []


def test_directory_named_like_a_candidate_is_ignored(tmp_path):
    proposal, _ = seeded(tmp_path)
    (tmp_path / "proposal-build.d").mkdir()
    assert publish.find_workspace_build(proposal) == []


def test_recipe_file_counts_only_with_the_target(tmp_path):
    """An unrelated Makefile must not stop a workspace from publishing."""
    proposal, _ = seeded(tmp_path)
    (tmp_path / "Makefile").write_text("all:\n\techo hi\n", encoding="utf-8")
    assert publish.find_workspace_build(proposal) == []
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    found = publish.find_workspace_build(proposal)
    assert [(b.path.name, b.target, b.runner) for b in found] == [
        ("Makefile", "proposal-build", "make")
    ]


def test_justfile_with_a_parameterized_target(tmp_path):
    proposal, _ = seeded(tmp_path)
    (tmp_path / ".justfile").write_text(JUSTFILE, encoding="utf-8")
    found = publish.find_workspace_build(proposal)
    assert [(b.path.name, b.runner) for b in found] == [(".justfile", "just")]


def test_one_recipe_file_is_found_once(tmp_path):
    """Discovery walks the directory instead of looking each candidate name up.
    A per-name lookup would find `makefile` twice on a case-insensitive
    filesystem and trip the ambiguity refusal on a single file."""
    proposal, _ = seeded(tmp_path)
    (tmp_path / "makefile").write_text(MAKEFILE, encoding="utf-8")
    assert len(publish.find_workspace_build(proposal)) == 1


def test_definition_in_an_ancestor_is_not_discovered(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (tmp_path / "proposal-build.py").write_text("x = 1\n", encoding="utf-8")
    proposal, _ = seeded(workspace)
    assert publish.find_workspace_build(proposal) == []


def test_handover_names_the_definition_and_the_contract(tmp_path, capsys):
    proposal = delegating(tmp_path)
    assert publish.main([str(proposal)]) == publish.HANDOVER_EXIT
    err = capsys.readouterr().err
    assert "proposal-build.py" in err
    assert "PROPOSAL_PATH=" in err
    assert "first argument" in err
    assert "handover, not a failure" in err


def test_handover_for_a_recipe_names_the_runner_and_target(tmp_path, capsys):
    proposal = delegating(tmp_path, "Makefile", MAKEFILE)
    assert publish.main([str(proposal)]) == publish.HANDOVER_EXIT
    err = capsys.readouterr().err
    assert "make proposal-build" in err


def test_handover_writes_nothing(tmp_path):
    """No document, no intermediate source, and no ignore entry for artifacts
    this run did not produce — the workspace owns its own ignore rules."""
    proposal = delegating(tmp_path)
    publish.main([str(proposal)])
    written = {p.name for p in tmp_path.iterdir()}
    assert written == {"topic.md", "proposal-build.py"}


def test_handover_offers_no_toolchain_guidance(tmp_path, capsys):
    """A delegating workspace needs neither pandoc nor typst."""
    proposal = delegating(tmp_path)
    publish.main([str(proposal)])
    assert "pandoc" not in capsys.readouterr().err


def test_two_definitions_are_refused_without_choosing(tmp_path, capsys):
    proposal = delegating(tmp_path)
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    assert publish.main([str(proposal)]) == publish.HANDOVER_EXIT
    err = capsys.readouterr().err
    assert "more than one" in err
    assert "proposal-build.py" in err
    assert "Makefile" in err
    assert not list(tmp_path.glob("*.pdf"))


def test_builtin_flag_skips_discovery(tmp_path, monkeypatch, capsys):
    """--builtin is the one escape from the refusal: explicit, never automatic."""
    proposal = delegating(tmp_path)
    monkeypatch.setattr(publish, "resolve_engine", lambda: None)
    assert publish.main([str(proposal), "--builtin"]) == 2
    assert "pandoc not found" in capsys.readouterr().err


def test_handout_is_never_delegated(tmp_path):
    """The hand-in export is a transform of the proposal source, not a rendered
    document, so a layout definition has nothing to say about it."""
    proposal = delegating(tmp_path)
    assert publish.main([str(proposal), "--handout"]) == 0
    assert (tmp_path / "topic-handout.md").exists()


def test_gitignore_entries_never_match_a_build_definition():
    """A build definition is a source file and must stay committable."""
    names = ["proposal-build", "proposal-build.py", "proposal-build.sh",
             "proposal-build.cmd", "Makefile", "justfile", ".justfile"]
    for name in names:
        for entry in publish.GITIGNORE_ENTRIES:
            assert not fnmatch.fnmatch(name, entry), f"{entry} would ignore {name}"


def test_w05_fixture_hands_over(tmp_path, capsys):
    """End-to-end over the shipped fixture: a workspace holding a build
    definition gets a handover, not a document."""
    staged = tmp_path / "w05"
    shutil.copytree(REPO / "tests" / "fixtures" / "w05-workspace-build", staged)
    proposal = staged / "deterministic-container-rebuilds.md"
    assert publish.main([str(proposal)]) == publish.HANDOVER_EXIT
    assert "proposal-build.py" in capsys.readouterr().err
    assert not list(staged.glob("*.pdf"))
    assert not (staged / ".gitignore").exists()
