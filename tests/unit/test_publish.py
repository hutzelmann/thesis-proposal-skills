"""L0: publish.py offline logic (skill-publish spec)."""

import fnmatch
import itertools
import os
import shutil
import subprocess
from pathlib import Path

import publish
import pytest
from fixture_paths import fixture_dir, fixture_proposal
from helpers import winget_problems, write_proposal

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


STRUCTURE = publish.load_structure()

SOURCE = (
    "Body text.\n\n---\nreferences:\n- id: A1\n  title: T\n"
    "  abstract: some abstract\n  DOI: 10.1/x\n---\n"
)


def test_lang_inferred_from_the_subtitle_wording():
    de = "# Ein Titel für die Arbeit\n\n*Exposé zur Masterarbeit*\n\nText.\n"
    en = "# A Title for the Thesis\n\n*Master's Thesis Proposal*\n\nText.\n"
    assert publish.infer_lang(de, STRUCTURE) == "de"
    assert publish.infer_lang(en, STRUCTURE) == "en"


def test_lang_falls_back_to_section_title_majority():
    de = ("# Ein Titel für die Arbeit\n\n*[TODO: state the degree level]*\n\n"
          "## Einführung in das Thema\n\nText.\n\n## Literatur\n")
    assert publish.infer_lang(de, STRUCTURE) == "de"
    # nothing canonical anywhere: English is the fallback
    assert publish.infer_lang("# Words\n\nProse only.\n", STRUCTURE) == "en"


def test_reference_section_title_localized():
    assert publish.reference_section_title("en") == "References"
    assert publish.reference_section_title("de") == "Literatur"
    assert publish.reference_section_title("de-at") == "Literatur"


def test_pandoc_command_carries_lang_and_references_heading():
    for kind in ("typst", "latex", "docx"):
        cmd = publish.pandoc_command(Path("proposal.md"), kind, "de")
        metas = [cmd[i + 1] for i, tok in enumerate(cmd) if tok == "-M"]
        assert "lang=de" in metas
        assert "references-heading=Literatur" in metas
        # the headline metadata must exist before citeproc builds the list
        assert cmd.index("-M") < cmd.index("--citeproc")
        # and the subtitle filter must run before every other filter
        filters = [cmd[i + 1] for i, tok in enumerate(cmd) if tok == "--lua-filter"]
        assert Path(filters[0]).name == "subtitle-filter.lua"
    en_cmd = publish.pandoc_command(Path("p.md"), "typst")
    assert "references-heading=References" in en_cmd


# -- figures resolved against the proposal's folder (skill-publish spec) ----

def option_value(cmd: list[str], option: str) -> str | None:
    """The token that follows `option` in a command, or None without it."""
    return next((value for flag, value in itertools.pairwise(cmd) if flag == option), None)


@pytest.mark.parametrize("kind", ["typst", "latex", "docx"])
def test_pandoc_command_resolves_figures_against_the_proposal_folder(tmp_path, kind):
    """pandoc resolves `img/` links against its working directory unless told
    otherwise, which dropped every figure from LaTeX PDFs and Word documents
    built from the workspace root (design D11)."""
    proposal = tmp_path / "topic" / "topic.md"
    cmd = publish.pandoc_command(proposal, kind)
    assert option_value(cmd, "--resource-path") == str(proposal.parent)


@pytest.mark.parametrize("kind", ["typst", "latex", "docx"])
def test_resource_path_left_out_when_the_folder_path_holds_the_separator(tmp_path, kind):
    """pandoc splits `--resource-path` on the path-list separator, so a folder
    under `a:b/` would be searched as `…/a` and `b/…` — neither of them it."""
    proposal = tmp_path / f"with{os.pathsep}separator" / "topic" / "topic.md"
    assert "--resource-path" not in publish.pandoc_command(proposal, kind)


class FakeRun:
    """Stands in for subprocess.run: records each command with its working
    directory and answers with the given result."""

    def __init__(self, returncode: int = 0, stderr: str = "") -> None:
        self.calls: list[tuple[list[str], str | None]] = []
        self.returncode = returncode
        self.stderr = stderr

    def __call__(self, cmd, **kwargs):
        cwd = kwargs.get("cwd")
        self.calls.append((list(cmd), None if cwd is None else str(cwd)))
        return subprocess.CompletedProcess(cmd, self.returncode, "", self.stderr)

    def pandoc_calls(self) -> list[tuple[list[str], str | None]]:
        return [(cmd, cwd) for cmd, cwd in self.calls if cmd[0] == "pandoc"]


PATH_OPTIONS = ("--lua-filter", "--csl", "--template", "--include-in-header", "-o")


TOOLS = {"typst": "typst", "latex": "xelatex", "docx": "pandoc"}


@pytest.mark.parametrize("kind", sorted(TOOLS))
def test_build_runs_pandoc_from_wherever_it_was_started(tmp_path, monkeypatch, kind):
    fake = FakeRun()
    monkeypatch.setattr(publish.subprocess, "run", fake)
    proposal = write_proposal(tmp_path, "topic", SOURCE).resolve()
    publish.build(proposal, kind, TOOLS[kind])
    calls = fake.pandoc_calls()
    assert calls, "build ran no pandoc"
    for cmd, cwd in calls:
        assert cwd is None, f"pandoc ran from {cwd} although the folder path is plain"
        assert option_value(cmd, "--resource-path") == str(proposal.parent)


@pytest.mark.parametrize("kind", sorted(TOOLS))
def test_build_runs_pandoc_from_the_folder_when_its_path_holds_the_separator(
        tmp_path, monkeypatch, kind):
    """The fallback for a folder pandoc cannot be told about: its default
    resource path is the working directory, so pandoc runs from the folder, and
    every path the command names is absolute so the change of directory moves
    nothing else (design D11)."""
    fake = FakeRun()
    monkeypatch.setattr(publish.subprocess, "run", fake)
    proposal = write_proposal(tmp_path / f"with{os.pathsep}separator", "topic", SOURCE).resolve()
    publish.build(proposal, kind, TOOLS[kind])
    calls = fake.pandoc_calls()
    assert calls, "build ran no pandoc"
    for cmd, cwd in calls:
        assert cwd == str(proposal.parent)
        assert "--resource-path" not in cmd
        named = [cmd[1]] + [value for flag, value in itertools.pairwise(cmd)
                            if flag in PATH_OPTIONS]
        relative = [p for p in named if not Path(p).is_absolute()]
        assert relative == [], f"relative paths in a command run from the folder: {relative}"


def test_build_given_a_relative_proposal_still_names_absolute_paths(tmp_path, monkeypatch):
    """The separator fallback changes pandoc's working directory, so a relative
    proposal path, as an agent passes it from the workspace root, is resolved
    before any command is built."""
    fake = FakeRun()
    monkeypatch.setattr(publish.subprocess, "run", fake)
    root = tmp_path / f"with{os.pathsep}separator"
    proposal = write_proposal(root, "topic", SOURCE).resolve()
    monkeypatch.chdir(root)
    outputs = publish.build(Path("topic") / "topic.md", "docx", "pandoc")
    (cmd, cwd), = fake.pandoc_calls()
    assert cwd == str(proposal.parent)
    assert cmd[1] == str(proposal)
    assert outputs == [proposal.with_suffix(".docx")]


PANDOC_WARNING = ("[WARNING] Could not fetch resource img/overview.png: "
                  "replacing image with description")


def test_run_relays_the_warnings_of_a_successful_build(monkeypatch, capsys):
    """A figure pandoc cannot find is only a warning; discarding it on success
    is how figures disappeared silently."""
    monkeypatch.setattr(publish.subprocess, "run", FakeRun(
        stderr=f"{PANDOC_WARNING}\n[INFO] Loaded something\n"))
    publish.run(["pandoc", "topic.md"])
    err = capsys.readouterr().err
    assert PANDOC_WARNING in err
    assert "[INFO]" not in err, "only warnings are relayed"


def test_run_keeps_a_warning_s_continuation_lines(monkeypatch, capsys):
    monkeypatch.setattr(publish.subprocess, "run", FakeRun(
        stderr="[WARNING] Could not convert TeX math x, rendering as TeX:\n"
               "  \\frac{1}{\n  ^\nunrelated trailing line\n"))
    publish.run(["pandoc", "topic.md"])
    err = capsys.readouterr().err
    assert "rendering as TeX" in err
    assert "\\frac{1}{" in err
    assert "unrelated trailing line" not in err


def test_run_is_silent_when_pandoc_warns_about_nothing(monkeypatch, capsys):
    monkeypatch.setattr(publish.subprocess, "run", FakeRun(stderr=""))
    publish.run(["pandoc", "topic.md"])
    assert capsys.readouterr().err == ""


def test_run_still_fails_with_the_converter_s_message(monkeypatch):
    monkeypatch.setattr(publish.subprocess, "run", FakeRun(
        returncode=1, stderr="error: file not found (searched at img/overview.png)"))
    with pytest.raises(SystemExit) as failure:
        publish.run(["typst", "compile", "topic.typ", "topic.pdf"])
    assert "img/overview.png" in str(failure.value.code)


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


def seeded(root):
    """A workspace root holding one proposal in its folder, and the path its
    hand-in export takes: `<slug>.handout.md` beside it, named after the
    proposal because it leaves the folder (proposal-file-format)."""
    proposal = write_proposal(root, "topic", SOURCE)
    return proposal, proposal.with_name("topic.handout.md")


def test_handout_written_when_absent(tmp_path):
    proposal, handout = seeded(tmp_path)
    assert publish.main([str(proposal), "--handout"]) == 0
    assert "abstract" not in handout.read_text(encoding="utf-8")


def test_handout_takes_the_dotted_name_only(tmp_path, capsys):
    proposal, handout = seeded(tmp_path)
    assert publish.main([str(proposal), "--handout"]) == 0
    assert sorted(p.name for p in proposal.parent.iterdir()) == [handout.name, "topic.md"]
    assert "handout written: topic.handout.md" in capsys.readouterr().out


def test_handout_rename_advice_keeps_the_handout_ending(tmp_path, capsys):
    """Renamed in its folder to `<name>-topic.md`, the export keeps the
    proposal's frame and would be reported as a second proposal, with advice to
    give it a folder of its own; under `<name>-topic.handout.md` it stays a
    previous output, which the check leaves alone."""
    proposal, _ = seeded(tmp_path)
    assert publish.main([str(proposal), "--handout"]) == 0
    out = capsys.readouterr().out
    assert "rename to include your name" in out
    assert "keep the `.handout.md` ending" in out
    assert "`<your-name>-topic.handout.md`" in out


def test_handout_written_beside_the_proposal_from_the_workspace_root(tmp_path, monkeypatch):
    _, handout = seeded(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert publish.main(["topic/topic.md", "--handout"]) == 0
    assert handout.is_file()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["topic"]


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
    """A workspace holding a proposal with one build definition in its folder."""
    proposal, _ = seeded(tmp_path)
    (proposal.parent / name).write_text(body, encoding="utf-8")
    return proposal


MAKEFILE = "all:\n\techo hi\n\nproposal-build:\n\tpandoc $(PROPOSAL_PATH) -o out.pdf\n"
JUSTFILE = "default:\n  echo hi\n\nproposal-build proposal:\n  pandoc {{proposal}}\n"


def test_build_file_discovered_with_and_without_suffix(tmp_path):
    proposal, _ = seeded(tmp_path)
    (proposal.parent / "proposal-build").write_text("#!/bin/sh\n", encoding="utf-8")
    found = publish.find_workspace_build(proposal)
    assert [b.path.name for b in found] == ["proposal-build"]
    (proposal.parent / "proposal-build.py").write_text("x = 1\n", encoding="utf-8")
    assert len(publish.find_workspace_build(proposal)) == 2


def test_unrelated_names_are_not_build_definitions(tmp_path):
    proposal, _ = seeded(tmp_path)
    for name in ("build.sh", "proposal-build-old.sh", "myproposal-build.py"):
        (proposal.parent / name).write_text("x\n", encoding="utf-8")
    assert publish.find_workspace_build(proposal) == []


def test_directory_named_like_a_candidate_is_ignored(tmp_path):
    proposal, _ = seeded(tmp_path)
    (proposal.parent / "proposal-build.d").mkdir()
    assert publish.find_workspace_build(proposal) == []


def test_recipe_file_counts_only_with_the_target(tmp_path):
    """An unrelated Makefile must not stop a workspace from publishing."""
    proposal, _ = seeded(tmp_path)
    makefile = proposal.parent / "Makefile"
    makefile.write_text("all:\n\techo hi\n", encoding="utf-8")
    assert publish.find_workspace_build(proposal) == []
    makefile.write_text(MAKEFILE, encoding="utf-8")
    found = publish.find_workspace_build(proposal)
    assert [(b.path.name, b.target, b.runner) for b in found] == [
        ("Makefile", "proposal-build", "make")
    ]


def test_justfile_with_a_parameterized_target(tmp_path):
    proposal, _ = seeded(tmp_path)
    (proposal.parent / ".justfile").write_text(JUSTFILE, encoding="utf-8")
    found = publish.find_workspace_build(proposal)
    assert [(b.path.name, b.runner) for b in found] == [(".justfile", "just")]


def test_one_recipe_file_is_found_once(tmp_path):
    """Discovery walks the directory instead of looking each candidate name up.
    A per-name lookup would find `makefile` twice on a case-insensitive
    filesystem and trip the ambiguity refusal on a single file."""
    proposal, _ = seeded(tmp_path)
    (proposal.parent / "makefile").write_text(MAKEFILE, encoding="utf-8")
    assert len(publish.find_workspace_build(proposal)) == 1


def test_definition_at_the_workspace_root_is_not_discovered(tmp_path):
    """Beside the proposal means in its folder: a definition at the workspace
    root, above it, is never used (proposal-check names it instead)."""
    (tmp_path / "proposal-build.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    proposal, _ = seeded(tmp_path)
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
    written = {p.name for p in proposal.parent.iterdir()}
    assert written == {"topic.md", "proposal-build.py"}
    assert [p.name for p in tmp_path.iterdir()] == ["topic"]


def test_handover_offers_no_toolchain_guidance(tmp_path, capsys):
    """A delegating workspace needs neither pandoc nor typst."""
    proposal = delegating(tmp_path)
    publish.main([str(proposal)])
    assert "pandoc" not in capsys.readouterr().err


def test_two_definitions_are_refused_without_choosing(tmp_path, capsys):
    proposal = delegating(tmp_path)
    (proposal.parent / "Makefile").write_text(MAKEFILE, encoding="utf-8")
    assert publish.main([str(proposal)]) == publish.HANDOVER_EXIT
    err = capsys.readouterr().err
    assert "more than one" in err
    assert "proposal-build.py" in err
    assert "Makefile" in err
    assert not list(tmp_path.rglob("*.pdf"))


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
    assert proposal.with_name("topic.handout.md").exists()


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
    fixture = "w05-workspace-build"
    staged = tmp_path / "w05"
    shutil.copytree(fixture_dir(fixture), staged)
    proposal = staged / fixture_proposal(fixture).relative_to(fixture_dir(fixture))
    assert publish.main([str(proposal)]) == publish.HANDOVER_EXIT
    assert "proposal-build.py" in capsys.readouterr().err
    assert not list(staged.rglob("*.pdf"))
    assert not list(staged.rglob(".gitignore"))


# -- the ignore file follows the proposal into its folder -------------------

def test_gitignore_written_into_the_proposal_folder(tmp_path, monkeypatch):
    """Run from the workspace root as an agent runs it: the ignore entries land
    in the proposal's folder, beside the outputs they cover, and nothing is
    written at the root."""
    proposal, _ = seeded(tmp_path)
    monkeypatch.setattr(publish, "resolve_engine", lambda: ("docx", "pandoc"))
    monkeypatch.setattr(publish, "build", lambda path, *_: [path.with_suffix(".docx")])
    monkeypatch.chdir(tmp_path)
    assert publish.main(["topic/topic.md"]) == 0
    ignore = proposal.parent / ".gitignore"
    assert "*.docx" in ignore.read_text(encoding="utf-8").splitlines()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["topic"]


# -- install guidance (skill-publish: Engine resolution order) ---------------

GUIDE_PDF_URL = ("https://github.com/hutzelmann/thesis-proposal-skills/blob/main/"
                 "docs/install.md#pdf-export")


def tools_missing_section() -> str:
    text = (REPO / "skills" / "proposal-publish" / "SKILL.md").read_text(encoding="utf-8")
    return text[text.index("## When tools are missing"):text.index("## Hand-in guidance")]


def test_winget_rule_flags_the_forms_that_install_the_wrong_thing():
    """`--id A B` searches for B restricted to id A and installs nothing;
    without `-e` a substring match may pick another package."""
    assert winget_problems("winget install --id JohnMacFarlane.Pandoc Typst.Typst")
    assert winget_problems("winget install --id Typst.Typst")
    assert winget_problems("winget install -e JohnMacFarlane.Pandoc Typst.Typst")
    assert winget_problems("`winget install --id Typst.Typst -e`") == []
    assert winget_problems("`winget install --source winget --exact --id Typst.Typst`") == []


def test_install_hint_gives_one_exact_winget_command_per_tool():
    assert winget_problems(publish.INSTALL_HINT) == []
    for package in ("JohnMacFarlane.Pandoc", "Typst.Typst"):
        assert f"winget install --id {package} -e" in publish.INSTALL_HINT


def test_install_hint_links_the_guide_for_machines_without_a_package_manager():
    assert GUIDE_PDF_URL in publish.INSTALL_HINT


def test_skill_tool_guidance_gives_valid_winget_commands_and_the_guide_link():
    section = tools_missing_section()
    assert "winget install" in section
    assert winget_problems(section) == []
    assert GUIDE_PDF_URL in section
