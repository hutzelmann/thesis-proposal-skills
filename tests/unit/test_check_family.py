"""L0: the proposal family as the check sees it, one folder per proposal
(skill-check: Orphaned companions reported as a warning; proposal-file-format:
One folder per proposal, Proposal family under one handle).

`is_slug`, `family_member` and `proposal_folder` are pure; `family_members`
classifies a listing of location-relative paths for the harness's verdicts; the
warning lists the proposal's folder, the location root, the workspace root and
the location's slug-shaped folders, and opens a file only for the frame, the
metadata-block and the notes-headings tests. Every workspace here is a
`tmp_path`, checked from its root as a user's agent checks it: the supported
setups the rule must stay quiet on (a workspace build, source documents, a code
repository, installer folders) would bloat or confuse the fixture corpus if
committed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import check
import publish
import pytest
from helpers import CLEAN_DRAFT, NOTES_TEXT, check_fixture, run_check, write_proposal

RULE = "companion-orphaned"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
# a kept list that ends in a metadata block but opens with a plain paragraph
# below its title, as w15's reading list does
KEPT_LIST = ("# Reading list\n\nPapers to read before the next meeting.\n\n- A paper\n\n"
             "---\nreferences: []\n---\n")
OLD, NEW = "ci-agents", "ci-agent-configurations"


def write(ws: Path, rel: str, content: str | bytes = "") -> Path:
    path = ws / rel
    if rel.endswith("/"):
        path.mkdir(parents=True, exist_ok=True)
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def with_figure(text: str, link: str) -> str:
    """CLEAN_DRAFT with one figure link before its first section."""
    return text.replace("\n## ", f"\n![Pipeline]({link})\n\n## ", 1)


def proposal(ws: Path, slug: str, link: str | None = None) -> Path:
    return write_proposal(ws, slug, with_figure(CLEAN_DRAFT, link) if link else CLEAN_DRAFT)


def report(path: Path, root: Path | None = None) -> dict:
    return json.loads(run_check(path, "--json", root=root).stdout)


def orphans(path: Path, root: Path | None = None) -> list[str]:
    """The orphan warnings of a check run from the workspace root (by default
    the folder above the proposal's folder)."""
    found = [f for f in report(path, root)["findings"] if f["rule"] == RULE]
    assert all(f["level"] == "warning" for f in found), found
    return [f["message"] for f in found]


def named(messages: list[str], needle: str) -> list[str]:
    return [m for m in messages if needle in m]


def assert_explained(message: str) -> None:
    assert "on purpose" in message, message
    assert "left as it is" in message, message


# ---------- the vocabulary ----------------------------------------------------


def test_the_roles_are_the_block_roles_in_table_order():
    assert check.FAMILY_ROLES == (
        "proposal", "notes", "harvest record", "review", "supervisor feedback",
        "handout", "built output", "kept file", "figure",
    )


def test_role_files_are_named_by_their_role():
    assert check.ROLE_NAMES == {
        check.NOTES: "notes.md", check.HARVEST: "harvest.md",
        check.REVIEW: "review.md", check.FEEDBACK: "feedback.md",
    }


def test_the_handle_carries_the_files_that_leave_the_folder():
    assert check.HANDLE_SUFFIXES == {
        ".md": check.PROPOSAL, ".handout.md": check.HANDOUT, ".pdf": check.BUILT,
        ".typ": check.BUILT, ".tex": check.BUILT, ".docx": check.BUILT,
    }


def test_reserved_names():
    labels, folders = check.RESERVED_LABELS, check.RESERVED_FOLDERS
    assert labels == {"notes", "review", "feedback", "harvest", "handout", "img"}
    assert folders == {"bug-report", "img"}


@pytest.mark.parametrize(("name", "shaped"), [
    ("idea", True), ("idea-2", True), ("flaky-ci-triage", True), ("f00", True),
    ("Meetings", False), ("my_notes", False), ("-idea", False), ("idea--2", False),
    ("idea-", False), (".hidden", False), ("", False),
])
def test_slug_shaped_names(name, shaped):
    assert check.is_slug(name) is shaped


# ---------- the proposal folder ------------------------------------------------


def no_reads(name: str) -> str:
    raise AssertionError(f"`{name}` was read, though the folder test needed no text")


@pytest.mark.parametrize(("folder", "files", "texts", "sheltered"), [
    ("ci-agents", ["ci-agents.md"], {}, True),
    ("idea", ["notes.md", "reading-list.md"], {"notes.md": NOTES_TEXT}, True),
    ("idea-2", ["notes.md"], {"notes.md": NOTES_TEXT}, True),
    # Q1: a harvest record alone, written by a reverse run awaiting inspection
    ("my-thesis", ["harvest.md"], {}, True),
    ("meetings", ["notes.md"], {"notes.md": "# Meetings\n\n## Monday\n"}, False),
    ("literature", ["img/scan.png"], {}, False),
    ("old-slug", ["review.md", "candidates.yaml", "img/pipeline.png"], {}, False),
    # reserved and hidden names never name a proposal folder
    ("bug-report", ["bug-report.md", "notes.md"], {"notes.md": NOTES_TEXT}, False),
    ("img", ["img.md"], {}, False),
    (".hidden", [".hidden.md"], {}, False),
    ("Meetings", ["Meetings.md"], {}, False),
    ("my_notes", ["my_notes.md"], {}, False),
    # a nested file named after the folder is no proposal of it
    ("ci-agents", ["drafts/ci-agents.md"], {}, False),
])
def test_the_proposal_folder_test(folder, files, texts, sheltered):
    read = texts.get if texts else no_reads
    assert check.proposal_folder(folder, files, read) is sheltered


def test_a_notes_file_counts_with_all_five_headings_in_any_order():
    shuffled = ("## Log\n\n## Next Focus\n\n## Decisions\n\n## Excluded Literature\n\n"
                "## Open Points\n")
    assert check.notes_shaped(shuffled)
    assert check.notes_shaped(NOTES_TEXT + "\n## My own heading\n")
    assert not check.notes_shaped(NOTES_TEXT.replace("## Next Focus\n", ""))
    assert not check.notes_shaped(NOTES_TEXT.replace("## ", "### "))


def test_an_unreadable_notes_file_keeps_its_folder_a_proposal_folder():
    """Classification must never make the warning louder on a read failure."""
    assert check.proposal_folder("idea", ["notes.md"], lambda _name: None)


# ---------- role classification inside a folder --------------------------------


@pytest.mark.parametrize(("name", "role"), [
    ("ci-agents.md", "proposal"),
    ("notes.md", "notes"),
    ("harvest.md", "harvest record"),
    ("review.md", "review"),
    ("feedback.md", "supervisor feedback"),
    ("ci-agents.handout.md", "handout"),
    ("ci-agents.pdf", "built output"),
    ("ci-agents.typ", "built output"),
    ("ci-agents.tex", "built output"),
    ("ci-agents.docx", "built output"),
    ("candidates.yaml", "kept file"),
    ("reading-list.md", "kept file"),
    ("search-summary.md", "kept file"),
    ("probe/", "kept file"),
    ("probe/run.sh", "kept file"),
    ("img/pipeline.png", "figure"),
    ("img/sketch.svg", "figure"),
    # previous outputs a rename leaves under the old slug
    ("old-slug.pdf", "built output"),
    ("old-slug.handout.md", "handout"),
    # role files are matched by their exact name: these labels only end like one
    ("peer-review.md", "kept file"),
    ("reading-notes.md", "kept file"),
    ("supervisor-feedback.md", "kept file"),
    # a flat name of the old layout is no role file inside a folder
    ("ci-agents-review.md", "kept file"),
])
def test_family_member_classifies_every_role(name, role):
    assert check.family_member(name, "ci-agents") == role


@pytest.mark.parametrize("name", [
    # reserved labels, the slug among them (design D16)
    "notes.txt", "review.yaml", "feedback.json", "harvest.txt", "handout.md", "img.png",
    "ci-agents.candidates.yaml", "ci-agents.yaml", "ci-agents.notes.md", "ci-agents/",
    # hidden, workspace-level and build files
    ".gitignore", ".probe/run.sh", "guidelines.md", "proposal-build.sh", "Makefile",
    # no label shape, or not a figure
    "README.md", "My Notes.md", "Exposé.docx", "notes", "img/", "img/sub/x.png",
])
def test_family_member_leaves_everything_else_alone(name):
    assert check.family_member(name, "ci-agents") is None


def test_the_listing_classifier_keys_members_by_their_path():
    paths = ["ci-agents/ci-agents.md", "ci-agents/notes.md", "ci-agents/img/pipeline.png",
             "ci-agents/peer-review.md", "idea/notes.md", "idea/reading-list.md",
             "meetings/notes.md", "old-slug/review.md", "ci-agents.md", "review.md",
             "guidelines.md", "bug-report/report.md"]
    texts = {"idea/notes.md": NOTES_TEXT, "meetings/notes.md": "# Minutes\n"}
    assert check.family_members(paths, texts.get) == {
        "ci-agents/ci-agents.md": ("ci-agents", "proposal"),
        "ci-agents/notes.md": ("ci-agents", "notes"),
        "ci-agents/img/pipeline.png": ("ci-agents", "figure"),
        "ci-agents/peer-review.md": ("ci-agents", "kept file"),
        "idea/notes.md": ("idea", "notes"),
        "idea/reading-list.md": ("idea", "kept file"),
    }


def test_the_listing_classifier_reads_only_notes_files():
    reads = []

    def read(path: str) -> str:
        reads.append(path)
        return NOTES_TEXT

    check.family_members(["a/a.md", "a/review.md", "b/notes.md", "b/x.md", "c/review.md"], read)
    assert reads == ["b/notes.md"]


def test_build_definition_recognition_matches_publish():
    """check.py mirrors publish.py rather than importing it (each skill ships
    alone), so the pin is the only thing keeping the two in step: a build
    definition publish runs is one the check never reports as unused in the
    folder, and one it recognizes at a root is one publish would have run."""
    assert check.BUILD_STEM == publish.BUILD_STEM
    assert set(publish.RECIPE_RUNNERS) == check.RECIPE_NAMES
    assert check.RECIPE_TARGET_RE.pattern == publish.RECIPE_TARGET_RE.pattern
    assert check.RECIPE_TARGET_RE.flags == publish.RECIPE_TARGET_RE.flags


def test_the_handout_name_matches_publish():
    """The built outputs publish ignores are the ones the check classifies."""
    ignored = {pattern.removeprefix("*.") for pattern in publish.GITIGNORE_ENTRIES}
    assert check.HANDOUT_SUFFIX == publish.HANDOUT_SUFFIX
    assert ignored == check.BUILT_EXTENSIONS


# ---------- findings: what is reported -----------------------------------------


def test_leftovers_of_a_partial_rename(tmp_path):
    new = proposal(tmp_path, NEW)
    write(tmp_path, f"{OLD}/review.md", "Verdict: revise.\n")
    write(tmp_path, f"{OLD}/candidates.yaml", "- id: x\n")
    write(tmp_path, f"{OLD}/img/pipeline.png", PNG)
    found = orphans(new)
    assert len(found) == 1, found
    assert f"`{OLD}/review.md`" in found[0]
    assert "rename" in found[0]
    assert_explained(found[0])
    assert report(new)["exit_code"] == 0


def test_dump_at_the_location_root_names_its_folder(tmp_path):
    own = proposal(tmp_path, OLD)
    write(tmp_path, f"{OLD}.candidates.yaml", "- id: x\n")
    found = orphans(own)
    assert len(found) == 1, found
    assert f"`{OLD}.candidates.yaml`" in found[0]
    assert f"`{OLD}/`" in found[0]
    assert_explained(found[0])


def test_dump_at_the_workspace_root_names_the_folder_in_the_location(tmp_path):
    write(tmp_path, "guidelines.md", '# Ours\n\n```toml\n[paths]\nproposals = "proposals/"\n```\n')
    placed = proposal(tmp_path / "proposals", OLD)
    write(tmp_path, f"{OLD}.candidates.yaml", "- id: x\n")
    write(tmp_path, "unrelated.config.yaml", "x: 1\n")
    found = orphans(placed, root=tmp_path)
    assert len(found) == 1, found
    assert f"`{OLD}.candidates.yaml`" in found[0]
    assert f"`proposals/{OLD}/`" in found[0]
    assert "workspace root" in found[0]


def test_a_flat_proposal_beside_the_folders_is_reported_and_its_old_review_is_not(tmp_path):
    own = proposal(tmp_path, "agents")
    write(tmp_path, "drift.md", CLEAN_DRAFT)
    write(tmp_path, "drift-review.md", "Verdict: revise.\n")
    found = orphans(own)
    assert len(found) == 1, found
    assert "`drift.md`" in found[0]
    assert "`drift/drift.md`" in found[0], "the message names the folder it would go into"
    assert_explained(found[0])


def test_family_files_at_the_root_are_reported(tmp_path):
    own = proposal(tmp_path, "agents")
    for name in ("review.md", "feedback.md", "harvest.md", "old.handout.md"):
        write(tmp_path, name, "x\n")
    write(tmp_path, "notes.md", NOTES_TEXT)
    write(tmp_path, "img/pipeline.png", PNG)
    found = orphans(own)
    for name in ("review.md", "feedback.md", "harvest.md", "old.handout.md", "notes.md", "img/"):
        assert len(named(found, f"`{name}`")) == 1, (name, found)
    assert len(found) == 6, found


def test_role_files_in_a_folder_without_a_proposal_are_reported(tmp_path):
    own = proposal(tmp_path, NEW)
    write(tmp_path, f"{OLD}/feedback.md", "Dear student\n")
    write(tmp_path, f"{OLD}/{OLD}.handout.md", CLEAN_DRAFT)
    write(tmp_path, f"{OLD}/notes.md", "# My notes\n")
    write(tmp_path, f"{OLD}/{OLD}.pdf", b"%PDF-1.7\n")
    found = orphans(own)
    assert {m.split("`")[1] for m in found} == {f"{OLD}/feedback.md", f"{OLD}/{OLD}.handout.md"}


def test_a_second_proposal_in_the_folder_is_reported(tmp_path):
    own = proposal(tmp_path, "agents")
    write(tmp_path, "agents/drift.md", CLEAN_DRAFT)
    found = orphans(own)
    assert len(found) == 1, found
    assert "`agents/drift.md`" in found[0]
    assert_explained(found[0])


def test_a_folder_moved_into_another_proposal_folder_is_reported(tmp_path):
    own = proposal(tmp_path, "agents")
    write(tmp_path, "agents/drift/drift.md", CLEAN_DRAFT)
    write(tmp_path, "agents/drift/notes.md", NOTES_TEXT)
    found = orphans(own)
    assert len(found) == 1, found
    assert "`agents/drift/`" in found[0]
    assert "proposal location" in found[0]


@pytest.mark.parametrize("shelter", [("notes.md", NOTES_TEXT), ("harvest.md", "# Harvest\n")])
def test_a_nested_folder_with_a_notes_file_or_harvest_record_is_reported(tmp_path, shelter):
    own = proposal(tmp_path, "agents")
    write(tmp_path, f"agents/drift/{shelter[0]}", shelter[1])
    assert len(orphans(own)) == 1


# ---------- findings: what stays quiet -----------------------------------------


@pytest.mark.parametrize("old_folder", [True, False], ids=["old folder exists", "no old slug"])
def test_a_stale_figure_link_is_not_judged_by_a_slug(tmp_path, old_folder):
    own = proposal(tmp_path, NEW, link=f"img/{OLD}-pipeline.png")
    write(tmp_path, f"{NEW}/img/{OLD}-pipeline.png", PNG)
    if old_folder:
        write(tmp_path, f"{OLD}/candidates.yaml", "- id: x\n")
    assert orphans(own) == []


def test_a_proposal_whose_name_ends_like_a_companion_is_quiet(tmp_path):
    own = proposal(tmp_path, "ml-code-review")
    write(tmp_path, "ml-code-review/review.md", "Verdict: revise.\n")
    assert orphans(own) == []


def test_files_under_a_base_slug_without_a_folder_are_quiet(tmp_path):
    own = proposal(tmp_path, "ml-code-review")
    write(tmp_path, "ml-code.pdf", b"%PDF-1.7\n")
    write(tmp_path, "ml-code.candidates.yaml", "- id: x\n")
    assert orphans(own) == []


TOOL_FILES = {
    # a LaTeX source compiled at the root: biber's run file, synctex's index,
    # and with them the source and its PDF
    "latex": ("thesis.tex", "thesis.pdf", "thesis.synctex.gz", "thesis.run.xml", "thesis.aux",
              "thesis.bcf"),
    "code": ("tsconfig.app.json", "tsconfig.spec.json", "jest.config.js", "jest.setup.js"),
}


@pytest.mark.parametrize("kind", TOOL_FILES)
def test_tool_files_under_a_one_word_name_are_quiet(tmp_path, kind):
    own = proposal(tmp_path, "ci-agents")
    for name in TOOL_FILES[kind]:
        write(tmp_path, name, "x\n")
    assert orphans(own) == []


def test_an_idea_not_yet_seeded_is_quiet(tmp_path):
    own = proposal(tmp_path, "other-topic")
    write(tmp_path, "idea/notes.md", NOTES_TEXT)
    write(tmp_path, "idea/reading-list.md", KEPT_LIST)
    write(tmp_path, "idea/img/sketch.png", PNG)
    assert orphans(own) == []


def test_a_harvest_awaiting_inspection_is_quiet(tmp_path):
    own = proposal(tmp_path, "other-topic")
    write(tmp_path, "my-thesis/harvest.md", "# Harvest record\n")
    write(tmp_path, "my-thesis/review.md", "x\n")
    assert orphans(own) == []


def test_previous_outputs_after_a_rename_are_quiet(tmp_path):
    own = proposal(tmp_path, NEW)
    write(tmp_path, f"{NEW}/{OLD}.pdf", b"%PDF-1.7\n")
    write(tmp_path, f"{NEW}/{OLD}.handout.md", CLEAN_DRAFT)
    assert orphans(own) == []


def test_a_handout_renamed_as_publish_advises_is_quiet(tmp_path):
    """publish's hint asks for the student's name in front and the
    `.handout.md` ending kept: that name is a previous output, while the same
    text renamed to a plain `.md` carries the proposal's frame."""
    own = proposal(tmp_path, "agents")
    write(tmp_path, "agents/musterfrau-agents.handout.md", CLEAN_DRAFT)
    assert orphans(own) == []
    write(tmp_path, "agents/musterfrau-agents.md", CLEAN_DRAFT)
    assert len(orphans(own)) == 1


def test_a_kept_list_ending_in_a_metadata_block_is_quiet(tmp_path):
    own = proposal(tmp_path, "flaky-ci-triage")
    write(tmp_path, "flaky-ci-triage/reading-list.md", KEPT_LIST)
    assert orphans(own) == []


def test_kept_files_whose_labels_end_like_a_role_are_quiet(tmp_path):
    own = proposal(tmp_path, "agents")
    for name in ("peer-review.md", "reading-notes.md", "supervisor-feedback.md"):
        write(tmp_path, f"agents/{name}", "x\n")
    assert orphans(own) == []


def test_unrelated_folders_and_notes_are_quiet(tmp_path):
    own = proposal(tmp_path, "agents")
    write(tmp_path, "meetings/notes.md", "# Meetings\n\n## Monday\n")
    write(tmp_path, "literature/img/scan.png", PNG)
    write(tmp_path, "notes.md", "# My own notes\n")
    # a folder whose name is no slug is never looked into
    write(tmp_path, "Old Drafts/review.md", "x\n")
    assert orphans(own) == []


def test_workspace_build_and_installer_files_are_quiet(tmp_path):
    own = proposal(tmp_path, "ci-agents")
    for name in ("guidelines.md", "api-keys.env", "bug-report/report.md", "check-output.txt",
                 "version-output.txt", ".gitignore", ".agents/skills/proposal-check/SKILL.md",
                 ".agents/skills/.thesis-proposal-install.json", "skills-lock.json",
                 "ci-agents/proposal-build.sh", "ci-agents/faculty.typ", "ci-agents/proposal.pdf",
                 "ci-agents/.gitignore"):
        write(tmp_path, name, "x\n")
    assert orphans(own) == []


def test_source_documents_and_project_files_are_quiet(tmp_path):
    own = proposal(tmp_path, "ci-agents")
    for name in ("submission.pdf", "expose.docx", "thesis.pdf", "erika-musterfrau-expose.pdf",
                 "vite.config.ts", "data.tar.gz"):
        write(tmp_path, name, "x\n")
    assert orphans(own) == []


def test_a_name_that_is_not_utf8_is_skipped(tmp_path):
    """The listing is the check's only contact with files it was not asked
    about: a name that is not valid UTF-8 (an archive extracted on Linux) can
    never be slug-shaped, and printing it would lose every finding."""
    own = proposal(tmp_path, "ci-agents")
    try:
        (tmp_path / os.fsdecode(b"ci-agents.\xe4bersicht.txt")).write_text("x\n", encoding="utf-8")
        (own.parent / os.fsdecode(b"\xe4bersicht.md")).write_text("x\n", encoding="utf-8")
    except (OSError, UnicodeError):
        pytest.skip("this filesystem refuses a name that is not valid UTF-8")
    assert orphans(own) == []
    for extra in ((), ("--json",)):
        result = run_check(own, *extra)
        assert result.returncode == 0
        result.stdout.encode("utf-8")


# ---------- the report ---------------------------------------------------------


def leftover_workspace(ws: Path) -> Path:
    new = proposal(ws, NEW)
    write(ws, f"{OLD}/review.md", "Verdict: revise.\n")
    write(ws, f"{OLD}/candidates.yaml", "- id: x\n")
    write(ws, f"{OLD}/img/pipeline.png", PNG)
    write(ws, f"{OLD}.candidates.yaml", "- id: x\n")
    write(ws, "drift.md", CLEAN_DRAFT)
    return new


def test_warnings_leave_the_exit_code_alone(tmp_path):
    new = leftover_workspace(tmp_path)
    human = run_check(new)
    assert human.returncode == 0, human.stdout
    assert f"{OLD}/review.md" in human.stdout.split("warnings (possible false positives)")[1]
    data = report(new)
    assert data["exit_code"] == 0
    rules = [f for f in data["findings"] if f["rule"] == RULE]
    assert len(rules) == 2, rules
    assert {f["level"] for f in rules} == {"warning"}


def test_the_check_changes_nothing_in_the_workspace(tmp_path):
    new = leftover_workspace(tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run_check(new)
    run_check(new, "--json")
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before


def test_the_orphan_fixture_reports_its_leftovers_and_nothing_else():
    """w13's oracle pins which warnings appear by fragment; this pins that they
    are exactly the four leftovers, one finding each, and that no other file of
    the workspace is named: not the workspace-level and installer-managed
    files, not the unseeded `idea/`, not the leftover figure (testing-harness:
    Orphan oracle holds)."""
    data = json.loads(check_fixture("w13-orphaned-companions", "--json").stdout)
    found = [f for f in data["findings"] if f["rule"] in (RULE, "build-definition-unused")]
    named = sorted((f["rule"], f["message"].split("`")[1]) for f in found)
    assert named == [
        ("build-definition-unused", "proposal-build.sh"),
        (RULE, "build-log-triage.md"),
        (RULE, "ci-repair-agent-configurations.candidates.yaml"),
        (RULE, "ci-repair-agents/review.md"),
    ], named
    messages = [f["message"] for f in found]
    for quiet in ("guidelines.md", ".agents", ".thesis-proposal-install", "skills-lock.json",
                  "idea/", "img/pipeline.png"):
        assert not [m for m in messages if quiet in m], quiet


def test_the_rename_fixture_is_quiet():
    data = json.loads(check_fixture("w14-family-rename", "--json").stdout)
    assert not [f for f in data["findings"]
                if f["rule"] in (RULE, "proposal-misplaced", "proposal-folder-mismatch")]


def test_the_workspace_rules_are_declared_in_their_group():
    ids = list(check.RULE_IDS)
    at = ids.index("proposal-misplaced")
    assert ids[at:at + 4] == ["proposal-misplaced", "proposal-folder-mismatch", RULE,
                              "build-definition-unused"]
