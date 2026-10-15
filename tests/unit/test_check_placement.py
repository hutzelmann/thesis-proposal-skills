"""L0: where the check expects a proposal, which override file governed it,
and the build definitions publish never uses (skill-check: Override file
resolution chain; Proposal-location value validated, misplacement reported;
Proposal folder named by its slug; Unused build definitions reported; Governing
override file named by position).

The placement root is the directory of an explicitly passed override file, else
the working directory, which is the workspace root (design D17 of
adopt-proposal-folders); every test here therefore says where the check runs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import check
import claude_runner
import pytest
from helpers import CLEAN_DRAFT, run_check, write_proposal

PROPOSALS = '[paths]\nproposals = "proposals/"\n'


def guidelines(directory: Path, toml: str) -> Path:
    path = directory / "guidelines.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Ours\n\n```toml\n{toml}```\n", encoding="utf-8")
    return path


def run_from(cwd: Path, proposal: Path | str, *extra: str) -> str:
    """The human report of the check run with `cwd` as working directory."""
    return run_check(Path(proposal), *extra, root=cwd).stdout


def findings_from(cwd: Path, proposal: Path | str, *extra: str) -> dict:
    return json.loads(run_from(cwd, proposal, "--json", *extra))


def by_rule(data: dict, rule: str) -> list[str]:
    return [f["message"] for f in data["findings"] if f["rule"] == rule]


MISPLACED, MISMATCH, UNUSED = ("proposal-misplaced", "proposal-folder-mismatch",
                               "build-definition-unused")


# ---------- the proposal in its folder -----------------------------------------


def test_a_proposal_in_its_folder_at_the_root_is_placed(tmp_path):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    data = findings_from(tmp_path, proposal)
    assert not by_rule(data, MISPLACED)
    assert not by_rule(data, MISMATCH)
    assert data["exit_code"] == 0


def test_a_flat_proposal_is_misplaced_and_its_folder_named(tmp_path):
    flat = tmp_path / "agents.md"
    flat.write_text(CLEAN_DRAFT, encoding="utf-8")
    assert run_check(flat, root=tmp_path).returncode == 1
    data = findings_from(tmp_path, flat)
    [message] = by_rule(data, MISPLACED)
    assert "`agents/agents.md`" in message
    assert str(tmp_path) not in message


def test_a_folder_outside_the_configured_location_is_misplaced(tmp_path):
    guidelines(tmp_path, PROPOSALS)
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    [message] = by_rule(findings_from(tmp_path, proposal), MISPLACED)
    assert "`proposals/agents/agents.md`" in message
    assert "[paths] proposals" in message


def test_a_folder_in_the_configured_location_is_placed(tmp_path):
    guidelines(tmp_path, PROPOSALS + "[references]\nmin_count = 8\n")
    proposal = write_proposal(tmp_path / "proposals", "agents", CLEAN_DRAFT)
    out = run_from(tmp_path, proposal)
    assert "at least 8 required" in out, "the root guidelines.md governs the run"
    data = findings_from(tmp_path, proposal)
    assert not by_rule(data, MISPLACED)
    assert not by_rule(data, MISMATCH)


def test_a_check_started_inside_the_proposals_folder_says_where_to_run_it(tmp_path):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    data = findings_from(proposal.parent, "agents.md")
    [message] = by_rule(data, MISPLACED)
    assert "workspace root" in message
    assert data["exit_code"] == 1


def test_a_root_named_like_the_proposal_is_not_taken_for_its_folder(tmp_path):
    """A flat workspace from before the folder layout, named like its one
    proposal, looks exactly like a run from inside the proposal's folder: the
    message offers both readings instead of sending the user one level up,
    where the old workspace would silently pass as a proposal folder."""
    root = tmp_path / "agents"
    root.mkdir()
    (root / "agents.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    guidelines(root, "[references]\nmin_count = 1\n")
    (root / "api-keys.env").write_text("", encoding="utf-8")
    [message] = by_rule(findings_from(root, "agents.md"), MISPLACED)
    assert "`agents/agents.md`" in message
    assert "if it is the proposal's folder, run the check from the workspace root" in message
    assert "folder of its own" in message


def test_an_override_file_in_the_folder_is_named_as_what_set_the_root(tmp_path):
    """An explicit override file sets the root (design D17); one passed from
    inside the proposal's folder makes that folder the root, which no working
    directory explains."""
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    explicit = guidelines(proposal.parent, "[references]\nmin_count = 1\n")
    data = findings_from(tmp_path, proposal, "--guidelines", str(explicit))
    [message] = by_rule(data, MISPLACED)
    assert "override file passed explicitly" in message
    assert "ran from" not in message
    assert str(tmp_path) not in message


def test_a_run_from_above_the_workspace_scans_nothing_there(tmp_path):
    """Started above the workspace root, the check would list the parent
    directory and its sibling folders as if they were the workspace: placement
    is reported, with the working directory named as a possible cause, and
    nothing is scanned from the wrong root."""
    proposal = write_proposal(tmp_path / "ws", "agents", CLEAN_DRAFT)
    (tmp_path / "other").mkdir()
    (tmp_path / "other" / "review.md").write_text("Verdict: revise.\n", encoding="utf-8")
    (tmp_path / "review.md").write_text("x\n", encoding="utf-8")
    (tmp_path / "proposal-build.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    data = findings_from(tmp_path, proposal)
    [message] = by_rule(data, MISPLACED)
    assert "`agents/agents.md`" in message
    assert "not started from the workspace root" in message
    assert not by_rule(data, "companion-orphaned")
    assert not by_rule(data, UNUSED)


def test_a_flat_proposal_is_told_to_move_not_to_change_directory(tmp_path):
    flat = tmp_path / "agents.md"
    flat.write_text(CLEAN_DRAFT, encoding="utf-8")
    [message] = by_rule(findings_from(tmp_path, flat), MISPLACED)
    assert "folder of its own" in message
    assert "workspace root, run" not in message
    assert "not started from" not in message


def test_inside_the_folder_the_workspace_scans_stay_quiet(tmp_path):
    """Run from inside a folder, the folder is no location root: its own role
    files and build definition are not reported as strays."""
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    for name in ("review.md", "notes.md", "proposal-build.sh"):
        (proposal.parent / name).write_text("x\n", encoding="utf-8")
    data = findings_from(proposal.parent, "agents.md")
    assert not by_rule(data, "companion-orphaned")
    assert not by_rule(data, UNUSED)


def test_unset_key_raises_no_location_finding(tmp_path):
    guidelines(tmp_path, "[references]\nmin_count = 1\n")
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    data = findings_from(tmp_path, proposal)
    assert not by_rule(data, MISPLACED)
    assert not by_rule(data, "paths-proposals-invalid")


# ---------- the folder named by its slug ----------------------------------------


def half_renamed(ws: Path) -> Path:
    """`<new>/<old>.md`: the folder moved, the proposal file did not."""
    path = ws / "context-repair-agents" / "ci-repair-agents.md"
    path.parent.mkdir(parents=True)
    path.write_text(CLEAN_DRAFT, encoding="utf-8")
    return path


def test_a_rename_that_stopped_halfway_is_a_folder_name_error(tmp_path):
    proposal = half_renamed(tmp_path)
    data = findings_from(tmp_path, proposal)
    [message] = by_rule(data, MISMATCH)
    assert "`context-repair-agents`" in message
    assert "`ci-repair-agents`" in message
    assert "folder and the proposal file together" in message
    assert not by_rule(data, MISPLACED)
    assert data["exit_code"] == 1


def test_the_folder_name_error_reaches_the_dev_runner(tmp_path):
    half_renamed(tmp_path)
    rules = [f["rule"] for f in claude_runner.run_check_json(
        tmp_path, "context-repair-agents/ci-repair-agents.md")]
    assert MISMATCH in rules
    assert MISPLACED not in rules


def test_a_folder_name_that_is_not_utf8_is_printed_safely(tmp_path):
    """The folder-name error and the nested-folder warning print the proposal
    folder's own name, which no listing filters: a name that is not valid UTF-8
    (an archive extracted on Linux) must not end the report in a traceback."""
    try:
        folder = tmp_path / os.fsdecode(b"caf\xe9")
        folder.mkdir()
    except (OSError, UnicodeError):
        pytest.skip("this filesystem refuses a name that is not valid UTF-8")
    proposal = folder / "agents.md"
    proposal.write_text(CLEAN_DRAFT, encoding="utf-8")
    (folder / "drift").mkdir()
    (folder / "drift" / "drift.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    for extra in ((), ("--json",)):
        result = run_check(proposal, *extra, root=tmp_path)
        assert result.returncode == 1
        result.stdout.encode("utf-8")
        assert "caf\N{REPLACEMENT CHARACTER}" in result.stdout
    data = findings_from(tmp_path, proposal)
    assert by_rule(data, MISMATCH)
    assert [m for m in by_rule(data, "companion-orphaned") if "/drift/`" in m]


UNDECODABLE = b"caf\xe9"
SHOWN = "caf\N{REPLACEMENT CHARACTER}"


def undecodable_proposal(ws: Path, folder: bytes | None) -> Path:
    """A proposal whose own file name is not valid UTF-8, in `folder` under
    `ws` (none: at `ws` itself)."""
    try:
        directory = ws / os.fsdecode(folder) if folder is not None else ws
        directory.mkdir(parents=True, exist_ok=True)
        proposal = directory / os.fsdecode(UNDECODABLE + b".md")
        proposal.write_text(CLEAN_DRAFT, encoding="utf-8")
    except (OSError, UnicodeError):
        pytest.skip("this filesystem refuses a name that is not valid UTF-8")
    return proposal


@pytest.mark.parametrize(("folder", "rule", "stem_shown"), [
    # in its own folder: placed; the nested-folder warning names it
    (UNDECODABLE, None, None),
    # the folder-name error names the file and its stem
    (b"agents", MISMATCH, f"`{SHOWN}` must agree"),
    # at the root: the placement error names the file and where it belongs
    (None, MISPLACED, f"`{SHOWN}/{SHOWN}.md`"),
])
def test_a_proposal_name_that_is_not_utf8_is_printed_safely(tmp_path, folder, rule,
                                                            stem_shown):
    """The report header, the JSON `file` field and every message that names
    the checked proposal print the proposal's own file name, which comes from
    the path the check was given and no listing filters: one that is not valid
    UTF-8 (an archive extracted on Linux) keeps its readable part, the
    undecodable bytes replaced, instead of ending the report in a traceback."""
    proposal = undecodable_proposal(tmp_path, folder)
    if folder == UNDECODABLE:
        (proposal.parent / "drift").mkdir()
        (proposal.parent / "drift" / "drift.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    report = run_from(tmp_path, proposal)
    report.encode("utf-8")
    assert report.startswith(f"# Check: {SHOWN}.md\n")
    raw = run_from(tmp_path, proposal, "--json")
    raw.encode("utf-8")
    data = json.loads(raw)
    assert data["file"] == f"{SHOWN}.md"
    if rule is None:
        assert not by_rule(data, MISPLACED)
        assert not by_rule(data, MISMATCH)
        nested = [m for m in by_rule(data, "companion-orphaned") if "/drift/`" in m]
        assert len(nested) == 1
        assert f"`{SHOWN}.md`" in nested[0]
    else:
        assert [m for m in by_rule(data, rule) if f"`{SHOWN}.md`" in m and stem_shown in m]


def test_the_folder_name_error_in_a_configured_location(tmp_path):
    guidelines(tmp_path, PROPOSALS)
    proposal = half_renamed(tmp_path / "proposals")
    data = findings_from(tmp_path, proposal)
    assert by_rule(data, MISMATCH)
    assert not by_rule(data, MISPLACED)


# ---------- the placement root -----------------------------------------------------


def test_an_explicit_override_file_sets_the_root(tmp_path):
    root = tmp_path / "ws"
    explicit = guidelines(root, "[references]\nmin_count = 1\n")
    proposal = write_proposal(root, "agents", CLEAN_DRAFT)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    data = findings_from(elsewhere, proposal, "--guidelines", str(explicit))
    assert not by_rule(data, MISPLACED)
    assert data["guidelines"] == "explicit"


def test_a_guidelines_file_in_the_folder_does_not_move_the_root(tmp_path):
    """Chain position 1 is inside the folder now (design Q3): it governs the
    run, while placement is still measured from the working directory."""
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    guidelines(proposal.parent, "[references]\nmin_count = 9\n")
    guidelines(tmp_path, PROPOSALS + "[references]\nmin_count = 8\n")
    out = run_from(tmp_path, proposal)
    # the first file found governs the whole run: the root's location and
    # minimum are not consulted
    assert "at least 9 required" in out
    assert "at least 8 required" not in out
    data = findings_from(tmp_path, proposal)
    assert not by_rule(data, MISPLACED)
    assert data["guidelines"] == "beside-proposal"


def test_paths_are_compared_resolved(tmp_path):
    real = tmp_path / "real"
    write_proposal(real, "agents", CLEAN_DRAFT)
    link = tmp_path / "link"
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("this platform refuses symbolic links")
    data = findings_from(link, Path("agents") / "agents.md")
    assert not by_rule(data, MISPLACED)
    assert not by_rule(data, MISMATCH)
    data = findings_from(link, real / "agents" / "agents.md")
    assert not by_rule(data, MISPLACED)


@pytest.mark.parametrize("value", ['"/srv/proposals"', '"../elsewhere"', '"~/proposals"', "5"])
def test_an_invalid_location_is_reported_and_the_default_applies(tmp_path, value):
    guidelines(tmp_path, f"[paths]\nproposals = {value}\n")
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    data = findings_from(tmp_path, proposal)
    [message] = by_rule(data, "paths-proposals-invalid")
    assert "guidelines.md: [paths] proposals" in message
    assert data["exit_code"] == 1
    assert not by_rule(data, MISPLACED), "the default location `.` applies"


def test_an_unknown_paths_leaf_is_reported(tmp_path):
    guidelines(tmp_path, '[paths]\nproposal = "proposals/"\n')  # typo
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    out = run_from(tmp_path, proposal)
    assert "unknown workspace override `[paths] proposal`" in out


# ---------- the governing override file -----------------------------------------


@pytest.mark.parametrize(("where", "position", "label"), [
    ("folder", "beside-proposal", "guidelines: beside the proposal"),
    ("root", "working-directory", "guidelines: working directory"),
    ("explicit", "explicit", "guidelines: explicit"),
    ("none", "none", "guidelines: none (defaults)"),
])
def test_the_governing_position_is_named_without_a_path(tmp_path, where, position, label):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    extra: tuple[str, ...] = ()
    if where == "folder":
        guidelines(proposal.parent, "[references]\nmin_count = 1\n")
    elif where == "root":
        guidelines(tmp_path, "[references]\nmin_count = 1\n")
    elif where == "explicit":
        explicit = guidelines(tmp_path / "rules", "[references]\nmin_count = 1\n")
        extra = ("--guidelines", str(explicit))
    human = run_from(tmp_path, proposal, *extra)
    assert label in human.splitlines()
    assert str(tmp_path) not in human
    data = findings_from(tmp_path, proposal, *extra)
    assert data["guidelines"] == position
    assert str(tmp_path) not in json.dumps(data)


def test_a_run_inside_the_folder_names_no_override_file(tmp_path):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    guidelines(tmp_path, "[references]\nmin_count = 99\n")
    human = run_from(proposal.parent, "agents.md")
    assert "guidelines: none (defaults)" in human.splitlines()
    assert "at least 99 required" not in human


def test_the_guidelines_line_follows_the_digest():
    lines = check.render_report("agents.md", "0" * 64, [], "working-directory").splitlines()
    assert lines[1].startswith("digest: ")
    assert lines[2] == "guidelines: working directory"


# ---------- build definitions publish never uses ---------------------------------


def test_a_build_definition_at_the_workspace_root_is_unused(tmp_path):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    (tmp_path / "proposal-build.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    data = findings_from(tmp_path, proposal)
    [message] = by_rule(data, UNUSED)
    assert "`proposal-build.sh`" in message
    assert "proposal's folder" in message
    assert data["exit_code"] == 0, "a warning never changes the exit code"
    assert not by_rule(data, "companion-orphaned")


def test_a_recipe_with_the_target_at_the_location_root_is_unused(tmp_path):
    guidelines(tmp_path, PROPOSALS)
    proposal = write_proposal(tmp_path / "proposals", "agents", CLEAN_DRAFT)
    (tmp_path / "proposals" / "Makefile").write_text(
        "proposal-build:\n\techo built\n", encoding="utf-8")
    [message] = by_rule(findings_from(tmp_path, proposal), UNUSED)
    assert "`proposals/Makefile`" in message


@pytest.mark.parametrize("name", [".justfile", "GNUmakefile", "proposal-build"])
def test_root_definitions_are_recognized_as_publish_recognizes_them(tmp_path, name):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    (tmp_path / name).write_text("proposal-build proposal:\n\techo built\n", encoding="utf-8")
    assert len(by_rule(findings_from(tmp_path, proposal), UNUSED)) == 1


def test_a_recipe_without_the_target_is_no_build_definition(tmp_path):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    (tmp_path / "Makefile").write_text("all:\n\techo hi\n", encoding="utf-8")
    data = findings_from(tmp_path, proposal)
    assert not by_rule(data, UNUSED)
    assert not by_rule(data, "companion-orphaned")


def test_a_definition_in_the_proposals_folder_is_used(tmp_path):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    (proposal.parent / "proposal-build.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (proposal.parent / "Makefile").write_text("proposal-build:\n\techo\n", encoding="utf-8")
    assert not by_rule(findings_from(tmp_path, proposal), UNUSED)


def test_an_unreadable_recipe_is_no_build_definition(tmp_path, monkeypatch):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    recipe = tmp_path / "justfile"
    recipe.write_text("proposal-build:\n", encoding="utf-8")
    real = Path.read_text

    def refuse(self, *args, **kwargs):
        if self.name == "justfile":
            raise PermissionError(self.name)
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", refuse)
    assert not by_rule(findings_from(tmp_path, proposal), UNUSED)


def test_unused_definitions_leave_the_files_alone(tmp_path):
    proposal = write_proposal(tmp_path, "agents", CLEAN_DRAFT)
    recipe = tmp_path / "Makefile"
    recipe.write_text("proposal-build:\n\techo\n", encoding="utf-8")
    before = recipe.read_bytes(), recipe.stat().st_mtime_ns
    findings_from(tmp_path, proposal)
    assert (recipe.read_bytes(), recipe.stat().st_mtime_ns) == before
