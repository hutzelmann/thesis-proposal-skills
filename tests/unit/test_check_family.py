"""L0: the proposal family as the check sees it (skill-check: Orphaned companions
reported as a warning; proposal-file-format: Proposal family under one handle).

`family_handles` and `family_member` are pure and name-only; `family_findings`
lists a workspace and opens another file only to tell a proposal from a
companion. Every workspace here is a `tmp_path`: the supported setups the rule
must stay quiet on (a workspace build, source documents, a code repository,
installer folders) would bloat or confuse the fixture corpus if committed.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import check
import publish
import pytest
from helpers import CLEAN_DRAFT, FIXTURES, run_check

RULE = "companion-orphaned"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


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


def proposal(ws: Path, name: str, link: str | None = None) -> Path:
    return write(ws, name, with_figure(CLEAN_DRAFT, link) if link else CLEAN_DRAFT)


def orphans(path: Path, overrides: dict | None = None,
            guidelines: Path | None = None) -> list[check.Finding]:
    text = path.read_text(encoding="utf-8")
    found = check.family_findings(path, overrides or {}, guidelines, text)
    assert all(f.rule == RULE and f.level == "warning" for f in found), found
    return found


def named(findings: list[check.Finding], needle: str) -> list[check.Finding]:
    return [f for f in findings if needle in f.message]


# ---------- the vocabulary ----------------------------------------------------


def test_the_roles_are_the_block_roles_in_table_order():
    assert check.FAMILY_ROLES == (
        "proposal", "notes", "harvest record", "review", "supervisor feedback",
        "handout", "built output", "kept file", "figure",
    )
    assert check.IDEATION_NOTES == "ideation.notes.md"


@pytest.mark.parametrize(("name", "handles", "expected"), [
    ("ci-agents.md", set(), ("ci-agents", "proposal")),
    ("ci-agents.notes.md", set(), ("ci-agents", "notes")),
    ("ci-agents.harvest.md", set(), ("ci-agents", "harvest record")),
    ("ci-agents-review.md", {"ci-agents"}, ("ci-agents", "review")),
    # the base slug has no file here, so the name alone cannot call it a companion
    ("ml-code-review.md", set(), ("ml-code-review", "proposal")),
    ("ci-agents-feedback.md", {"ci-agents"}, ("ci-agents", "supervisor feedback")),
    ("ci-agents-feedback.md", set(), ("ci-agents-feedback", "proposal")),
    # a handout is a companion by its suffix alone
    ("ci-agents-handout.md", set(), ("ci-agents", "handout")),
    ("ci-agents.pdf", set(), ("ci-agents", "built output")),
    ("ci-agents.typ", set(), ("ci-agents", "built output")),
    ("ci-agents.tex", set(), ("ci-agents", "built output")),
    ("ci-agents.docx", set(), ("ci-agents", "built output")),
    ("ci-agents.reading-list.md", set(), ("ci-agents", "kept file")),
    ("ci-agents.candidates.yaml", set(), ("ci-agents", "kept file")),
    ("ci-agents.probe/", set(), ("ci-agents", "kept file")),
    ("img/ci-agents-pipeline.png", {"ci-agents"}, ("ci-agents", "figure")),
    # longest match: `ci-agents-v2` owns its figures although `ci-agents` prefixes them
    ("img/ci-agents-v2-sketch.png", {"ci-agents", "ci-agents-v2"}, ("ci-agents-v2", "figure")),
])
def test_family_member_classifies_every_role(name, handles, expected):
    assert check.family_member(name, frozenset(handles)) == expected


@pytest.mark.parametrize("name", [
    "ideation.notes.md",
    # hidden: installer folders and records, ignore files
    ".gitignore", ".agents/skills/proposal-check/SKILL.md", ".claude/skills/",
    ".kiro/skills/", ".opencode/skill/", ".opencode/skills/",
    ".thesis-proposal-install.json", ".ci-agents.candidates.yaml",
    # workspace-level files and troubleshooting captures
    "guidelines.md", "api-keys.env", "bug-report/", "bug-report/report.md",
    "check-output.txt", "version-output.txt", "skills-lock.json",
    # workspace build definitions
    "proposal-build", "proposal-build.sh", "proposal-build.ps1", "Makefile", "justfile",
    "GNUmakefile",
    # no slug-shaped part, or no family shape
    "README.md", "Exposé.docx", "My Thesis.md", "expected.json", "ci-agents.yaml",
    "img/screenshot.png", "img/ci-agents-pipeline.png",
])
def test_family_member_leaves_everything_else_alone(name):
    assert check.family_member(name, frozenset()) is None


def test_build_definition_names_match_publish():
    """check.py mirrors publish.py rather than importing it (each skill ships
    alone), so the pin is the only thing keeping the two in step: a build
    definition publish runs is one the check never reports, and the reverse."""
    assert check.BUILD_STEM == publish.BUILD_STEM
    assert set(publish.RECIPE_RUNNERS) == check.RECIPE_NAMES


@pytest.mark.parametrize("recipe", ["justfile", ".justfile", "Makefile", ".makefile",
                                    "GNUmakefile", "proposal-build.sh"])
def test_a_build_definition_publish_runs_keeps_built_outputs_quiet(tmp_path, recipe):
    """The lookup, not only the name sets: publish strips a leading dot and
    folds case, so a hidden `.justfile` is a workspace build to both."""
    own = proposal(tmp_path, "ci-agents.md")
    write(tmp_path, recipe, "proposal-build:\n\techo built\n")
    write(tmp_path, "old-slug-review.md", "Verdict: revise.\n")
    write(tmp_path, "old-slug.pdf", b"%PDF-1.7\n")
    assert [build.path.name for build in publish.find_workspace_build(own)] == [recipe]
    found = orphans(own)
    assert not named(found, "old-slug.pdf"), found
    assert named(found, "`old-slug-review.md`")


def test_family_handles_collects_slugs_of_family_shaped_names():
    names = ["ci-agents.md", "ci-agents.notes.md", "idea.reading-list.md", "img/x-y.png",
             ".hidden.md", "guidelines.md", "ideation.notes.md", "old-handout.md",
             "README.md", "proposal-build.sh", "vite.config.ts"]
    assert check.family_handles(names) == {"ci-agents", "idea", "old", "vite"}


# ---------- the listing classifier ---------------------------------------------


def never_read(name: str) -> bool:
    raise AssertionError(f"`{name}` was read, though its base slug has a proposal")


def test_a_review_beside_its_proposal_is_a_review_unread():
    members = check.family_members(["ci-agents.md", "ci-agents-review.md", "ci-agents.pdf",
                                    "ci-agents-feedback.md"], never_read)
    assert members["ci-agents-review.md"] == ("ci-agents", "review")
    assert members["ci-agents-feedback.md"] == ("ci-agents", "supervisor feedback")


@pytest.mark.parametrize("beside", ["ml-code.pdf", "ml-code.candidates.yaml", "ml-code.notes.md",
                                    "ml-code.harvest.md", "img/ml-code-arch.png"])
def test_a_base_slug_without_a_proposal_leaves_the_decision_to_the_metadata_block(beside):
    """skill-check: a `-review` or `-feedback` file whose base slug has no
    proposal is one when it ends in a metadata block. Another family file under
    the base slug is not that proposal."""
    names = ["ml-code-review.md", beside]
    assert check.family_members(names, lambda _name: True)["ml-code-review.md"] == (
        "ml-code-review", "proposal")
    assert check.family_members(names, lambda _name: False)["ml-code-review.md"] == (
        "ml-code", "review")


def test_the_checked_proposal_is_a_proposal_whatever_its_name():
    names = ["llm-code.md", "llm-code-review.md", "llm-code-review-review.md",
             "img/llm-code-review-arch.png"]
    assert check.family_members(names, lambda _name: False, own="llm-code-review.md") == {
        "llm-code.md": ("llm-code", "proposal"),
        "llm-code-review.md": ("llm-code-review", "proposal"),
        "llm-code-review-review.md": ("llm-code-review", "review"),
        "img/llm-code-review-arch.png": ("llm-code-review", "figure"),
    }


def test_companion_names_are_decided_shortest_first():
    """A base that is itself a `-review` name is settled before it is asked
    about, so only the file whose base has no proposal is read."""
    reads = []

    def ends_in_block(name: str) -> bool:
        reads.append(name)
        return name == "a-b-review.md"

    members = check.family_members(["a-b-review-review.md", "a-b-review.md"], ends_in_block)
    assert members == {"a-b-review.md": ("a-b-review", "proposal"),
                       "a-b-review-review.md": ("a-b-review", "review")}
    assert reads == ["a-b-review.md"]


# ---------- findings: what is reported ----------------------------------------


def test_partial_rename_reports_each_leftover_naming_the_old_slug(tmp_path):
    new = proposal(tmp_path, "ci-agent-configurations.md")
    write(tmp_path, "ci-agents-review.md", "Verdict: revise.\n")
    write(tmp_path, "ci-agents.candidates.yaml", "- id: x\n")
    write(tmp_path, "img/ci-agents-pipeline.png", PNG)
    found = orphans(new)
    assert len(found) == 3, found
    for leftover in ("ci-agents-review.md", "ci-agents.candidates.yaml",
                     "img/ci-agents-pipeline.png"):
        hits = named(found, f"`{leftover}`")
        assert len(hits) == 1, (leftover, found)
        message = hits[0].message
        assert "`ci-agents`" in message
        assert "rename" in message
        assert "on purpose" in message


def test_an_orphaned_review_without_a_metadata_block_is_a_companion(tmp_path):
    new = proposal(tmp_path, "new-title.md")
    write(tmp_path, "old-title-review.md", "Verdict: revise.\n")
    found = orphans(new)
    assert [f.message for f in named(found, "`old-title-review.md`")]
    assert "`old-title`" in found[0].message


def test_an_unreadable_review_stays_a_proposal_and_quiet(tmp_path, monkeypatch):
    """The one read this finding makes may fail; the file then keeps the
    listing's reading, a proposal, and nothing is reported."""
    new = proposal(tmp_path, "new-title.md")
    write(tmp_path, "old-title-review.md", "Verdict: revise.\n")
    text = new.read_text(encoding="utf-8")
    real = Path.read_text

    def refuse(self, *args, **kwargs):
        if self.name == "old-title-review.md":
            raise PermissionError(self.name)
        return real(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", refuse)
    assert check.family_findings(new, {}, None, text) == []


def test_a_leftover_handout_is_reported_although_it_ends_in_a_metadata_block(tmp_path):
    new = proposal(tmp_path, "new-title.md")
    write(tmp_path, "old-title-handout.md", CLEAN_DRAFT)
    found = orphans(new)
    assert len(named(found, "`old-title-handout.md`")) == 1
    assert "`old-title`" in found[0].message


def test_two_kept_files_make_an_unsheltered_slug_reportable(tmp_path):
    new = proposal(tmp_path, "new-title.md")
    write(tmp_path, "old-title.candidates.yaml", "- id: x\n")
    write(tmp_path, "old-title.probe/")
    write(tmp_path, "old-title.pdf", b"%PDF-1.7\n")
    found = orphans(new)
    assert {f.message.split("`")[1] for f in found} == {
        "old-title.candidates.yaml", "old-title.probe/", "old-title.pdf"}


def test_built_outputs_stay_quiet_under_a_workspace_build(tmp_path):
    new = proposal(tmp_path, "new-title.md")
    write(tmp_path, "proposal-build.sh", "#!/bin/sh\n")
    write(tmp_path, "old-title.candidates.yaml", "- id: x\n")
    write(tmp_path, "old-title.sources.txt", "x\n")
    write(tmp_path, "old-title.pdf", b"%PDF-1.7\n")
    found = orphans(new)
    assert not named(found, "old-title.pdf")
    assert len(found) == 2, found


def test_a_dump_at_the_root_of_a_configured_location_is_reported(tmp_path):
    guidelines = write(tmp_path, "guidelines.md",
                       '# Ours\n\n```toml\n[paths]\nproposals = "proposals/"\n```\n')
    placed = proposal(tmp_path, "proposals/ci-agents.md")
    write(tmp_path, "ci-agents.candidates.yaml", "- id: x\n")
    write(tmp_path, "unrelated.config.yaml", "x: 1\n")
    overrides = check.load_overrides(placed, guidelines)
    found = orphans(placed, overrides, guidelines)
    assert len(found) == 1, found
    assert "`ci-agents.candidates.yaml`" in found[0].message
    assert "`ci-agents`" in found[0].message
    assert "outside" in found[0].message


def test_the_root_is_listed_only_when_a_location_is_configured(tmp_path):
    guidelines = write(tmp_path, "guidelines.md", "# Ours\n\nProse only.\n")
    placed = proposal(tmp_path, "proposals/ci-agents.md")
    write(tmp_path, "ci-agents.candidates.yaml", "- id: x\n")
    assert orphans(placed, check.load_overrides(placed, guidelines), guidelines) == []


def test_stale_link_names_the_old_slug_when_a_family_file_carries_it(tmp_path):
    new = proposal(tmp_path, "new-title.md", link="img/old-title-pipeline.png")
    write(tmp_path, "old-title-review.md", "Verdict: revise.\n")
    links = named(orphans(new), "links")
    assert len(links) == 1, links
    message = links[0].message
    assert "`img/old-title-pipeline.png`" in message
    assert "`new-title`" in message
    assert "`old-title`" in message


def test_stale_link_without_a_resolvable_old_slug_names_only_path_and_own_slug(tmp_path):
    new = proposal(tmp_path, "new-title.md", link="img/old-title-pipeline.png")
    write(tmp_path, "img/old-title-pipeline.png", PNG)
    found = orphans(new)
    assert len(found) == 1, found
    message = found[0].message
    assert "`img/old-title-pipeline.png`" in message
    assert "`new-title`" in message
    assert "`old-title`" not in message


def test_a_link_under_the_own_slug_is_quiet(tmp_path):
    new = proposal(tmp_path, "new-title.md", link="img/new-title-pipeline.png")
    write(tmp_path, "img/new-title-pipeline.png", PNG)
    assert orphans(new) == []


# ---------- findings: what stays quiet ----------------------------------------


def test_an_idea_not_yet_seeded_is_sheltered_by_its_notes(tmp_path):
    other = proposal(tmp_path, "other-topic.md")
    write(tmp_path, "flaky-ci.notes.md", "# Notes\n")
    write(tmp_path, "flaky-ci.reading-list.md", "- a paper\n")
    write(tmp_path, "img/flaky-ci-sketch.png", PNG)
    assert orphans(other) == []


def test_a_lone_harvest_record_is_sheltered(tmp_path):
    other = proposal(tmp_path, "other-topic.md")
    write(tmp_path, "my-thesis.harvest.md", "# Harvest\n")
    write(tmp_path, "my-thesis.pdf", b"%PDF-1.7\n")
    assert orphans(other) == []


def test_a_review_beside_its_proposal_is_quiet(tmp_path):
    own = proposal(tmp_path, "ci-agents.md")
    write(tmp_path, "ci-agents-review.md", "Verdict: revise.\n")
    write(tmp_path, "ci-agents.notes.md", "# Notes\n")
    write(tmp_path, "ci-agents.pdf", b"%PDF-1.7\n")
    assert orphans(own) == []


def test_a_proposal_named_like_a_review_is_a_proposal(tmp_path):
    own = proposal(tmp_path, "ml-code-review.md")
    write(tmp_path, "agents.md", CLEAN_DRAFT)
    assert orphans(own) == []


@pytest.mark.parametrize("beside", ["ml-code.pdf", "ml-code.candidates.yaml"])
def test_a_review_named_proposal_beside_a_file_under_its_base_slug_is_quiet(tmp_path, beside):
    """skill-check: Proposal whose name ends like a companion. A built output
    or kept file under `ml-code` is no proposal of `ml-code`, so f00's
    `ml-code-review.md` stays a proposal and nothing is reported."""
    own = write(tmp_path, "ml-code-review.md",
                (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text(encoding="utf-8"))
    write(tmp_path, beside, "x\n")
    assert orphans(own) == []


def test_a_checked_proposal_slugged_like_anothers_review_shelters_its_own_family(tmp_path):
    proposal(tmp_path, "llm-code.md")
    own = proposal(tmp_path, "llm-code-review.md")
    write(tmp_path, "llm-code-review-review.md", "Verdict: revise.\n")
    write(tmp_path, "img/llm-code-review-arch.png", PNG)
    assert orphans(own) == []


TOOL_FILES = {
    # a LaTeX source compiled beside the proposal: biber's run file, synctex's
    # index, and with them the source and its PDF
    "latex": ("thesis.tex", "thesis.pdf", "thesis.synctex.gz", "thesis.run.xml", "thesis.aux",
              "thesis.bcf"),
    "code": ("tsconfig.app.json", "tsconfig.spec.json", "jest.config.js", "jest.setup.js"),
}


@pytest.mark.parametrize("kind", TOOL_FILES)
def test_tool_files_under_a_one_word_name_are_quiet(tmp_path, kind):
    """Kept files make a slug reportable only under two or more words, the
    shape of every slug a skill derives (Content-derived slug filenames)."""
    own = proposal(tmp_path, "ci-agents.md")
    for name in TOOL_FILES[kind]:
        write(tmp_path, name, "x\n")
    assert orphans(own) == []


@pytest.mark.parametrize("kind", TOOL_FILES)
def test_tool_files_at_the_root_of_a_configured_location_are_quiet(tmp_path, kind):
    guidelines = write(tmp_path, "guidelines.md",
                       '# Ours\n\n```toml\n[paths]\nproposals = "proposals/"\n```\n')
    placed = proposal(tmp_path, "proposals/ci-agents.md")
    for name in TOOL_FILES[kind]:
        write(tmp_path, name, "x\n")
    assert orphans(placed, check.load_overrides(placed, guidelines), guidelines) == []


def test_a_companion_under_a_one_word_slug_is_still_reported(tmp_path):
    """The word bound applies to kept files only: a review a user-named
    `expose.md` left behind is still an orphan."""
    new = proposal(tmp_path, "my-expose.md")
    write(tmp_path, "expose-review.md", "Verdict: revise.\n")
    found = orphans(new)
    assert len(found) == 1, found
    assert "`expose`" in found[0].message


def test_a_name_that_is_not_utf8_is_skipped(tmp_path):
    """The listing is the check's only contact with files it was not asked
    about: a name that is not valid UTF-8 (an archive extracted on Linux) can
    never be slug-shaped, and printing it would lose every finding."""
    own = proposal(tmp_path, "ci-agents.md")
    write(tmp_path, "old-notes.extra.txt", "x\n")
    try:
        (tmp_path / os.fsdecode(b"old-notes.\xe4bersicht.txt")).write_text("x\n", encoding="utf-8")
    except (OSError, UnicodeError):
        pytest.skip("this filesystem refuses a name that is not valid UTF-8")
    assert orphans(own) == []
    for extra in ((), ("--json",)):
        report = run_check(own, *extra)
        assert report.returncode == 0
        report.stdout.encode("utf-8")


def test_a_workspace_build_with_its_inputs_and_outputs_is_quiet(tmp_path):
    own = proposal(tmp_path, "ci-agents.md")
    for name in ("proposal-build.sh", "faculty.typ", "proposal.pdf"):
        write(tmp_path, name, "x\n")
    write(tmp_path, "img/logo.png", PNG)
    assert orphans(own) == []


def test_source_documents_and_project_files_are_quiet(tmp_path):
    own = proposal(tmp_path, "ci-agents.md")
    for name in ("submission.pdf", "expose.docx", "thesis.pdf", "erika-musterfrau-expose.pdf",
                 "vite.config.ts", "data.tar.gz"):
        write(tmp_path, name, "x\n")
    write(tmp_path, "img/screenshot.png", PNG)
    assert orphans(own) == []


def test_workspace_build_and_installer_files_are_quiet(tmp_path):
    own = proposal(tmp_path, "ci-agents.md")
    for name in ("guidelines.md", "api-keys.env", "bug-report/report.md", "proposal-build.sh",
                 "faculty.typ", "proposal.pdf", "check-output.txt", "version-output.txt",
                 ".gitignore", ".agents/skills/proposal-check/SKILL.md",
                 ".agents/skills/.thesis-proposal-install.json", "skills-lock.json",
                 "ideation.notes.md", "Makefile", "justfile"):
        write(tmp_path, name, "x\n")
    assert orphans(own) == []


# ---------- the report ---------------------------------------------------------


def leftover_workspace(ws: Path) -> Path:
    new = proposal(ws, "new-title.md", link="img/old-title-pipeline.png")
    write(ws, "old-title-review.md", "Verdict: revise.\n")
    write(ws, "old-title.candidates.yaml", "- id: x\n")
    write(ws, "img/old-title-pipeline.png", PNG)
    return new


def test_warnings_leave_the_exit_code_alone(tmp_path):
    new = leftover_workspace(tmp_path)
    human = run_check(new)
    assert human.returncode == 0, human.stdout
    assert human.stdout.count("- WARNING:") >= 4
    assert "old-title-review.md" in human.stdout.split("warnings (possible false positives)")[1]
    data = json.loads(run_check(new, "--json").stdout)
    assert data["exit_code"] == 0
    rules = [f for f in data["findings"] if f["rule"] == RULE]
    assert len(rules) == 4
    assert {f["level"] for f in rules} == {"warning"}


def test_the_check_changes_nothing_in_the_workspace(tmp_path):
    leftover_workspace(tmp_path)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    run_check(tmp_path / "new-title.md")
    run_check(tmp_path / "new-title.md", "--json")
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert after == before


def test_the_orphan_fixture_reports_its_leftovers_and_nothing_else():
    """w13's oracle pins which warnings appear; this pins that no other file of
    the workspace is named (testing-harness: Orphan oracle holds)."""
    w13 = FIXTURES / "w13-orphaned-companions"
    data = json.loads(run_check(w13 / "ci-repair-agent-configurations.md", "--json").stdout)
    messages = [f["message"] for f in data["findings"] if f["rule"] == RULE]
    assert len(messages) == 4, messages
    for quiet in ("guidelines.md", "ideation.notes.md", ".agents", ".thesis-proposal-install"):
        assert not [m for m in messages if quiet in m], quiet


def test_the_rename_fixture_is_quiet():
    w14 = FIXTURES / "w14-family-rename"
    data = json.loads(run_check(w14 / "ci-repair-agent-configurations.md", "--json").stdout)
    assert not [f for f in data["findings"] if f["rule"] == RULE]


def test_the_rule_is_declared_in_the_workspace_family_group():
    ids = list(check.RULE_IDS)
    assert ids.index(RULE) == ids.index("proposal-misplaced") + 1
