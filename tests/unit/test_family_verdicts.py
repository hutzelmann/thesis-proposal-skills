"""L0: the proposal-family verdicts in proposal folders (testing-harness:
Proposal-family coverage).

`verdict_family_only` judges which files a run added, `verdict_family_renamed`
whether a rename moved the folder whole, and `verdict_no_orphans` reads the
check's own findings. The first two classify with check.py's family vocabulary
and its proposal-folder test, never a second one; all three are pure, so no
workspace is needed here. So are the two family verdicts of the folder-layout
dev scenarios: `verdict_kept_on_request` and `verdict_ideate_from_scratch`,
which reads the run's recorded tool calls as (turn, tool, input).
"""

from helpers import NOTES_TEXT
from l1_checks import (
    family_members_at,
    renamed_proposal,
    verdict_family_only,
    verdict_family_renamed,
    verdict_ideate_from_scratch,
    verdict_kept_on_request,
    verdict_no_orphans,
)

SEED = "data-drift-detection/data-drift-detection.md"
METADATA = "\n\n---\nreferences: []\n---\n"
PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
OLD, NEW = "ci-repair-agent-configurations", "context-repair-agents"


def only(added, present=(), **kwargs):
    """`present` is everything after the run; the added files are part of it."""
    return verdict_family_only(list(added), sorted({*present, *added}), **kwargs)


# ---------- the listing classifier -----------------------------------------------


def test_paths_classify_by_their_folder():
    texts = {"idea/notes.md": NOTES_TEXT, "meetings/notes.md": "# Minutes\n"}
    members = family_members_at(["ci-agents/ci-agents.md", "ci-agents/peer-review.md",
                                 "idea/notes.md", "meetings/notes.md", "review.md"],
                                texts.__getitem__)
    assert members == {
        "ci-agents/ci-agents.md": ("ci-agents", "proposal"),
        "ci-agents/peer-review.md": ("ci-agents", "kept file"),
        "idea/notes.md": ("idea", "notes"),
        "meetings/notes.md": None,
        "review.md": None,
    }


def test_an_unreadable_notes_file_keeps_its_folder_a_proposal_folder():
    def refuse(path: str) -> str:
        raise OSError(path)

    assert family_members_at(["idea/notes.md"], refuse)["idea/notes.md"] == ("idea", "notes")


# ---------- family-only --------------------------------------------------------


def test_search_dump_beside_the_proposal_fails_unless_keeping_was_asked():
    """Scenarios: Search dump left beside the proposal; Keeping licensed by the
    request."""
    passed, why = only(["ci-agents/candidates.yaml"], ["ci-agents/ci-agents.md"])
    assert not passed
    assert "ci-agents/candidates.yaml" in why
    assert only(["ci-agents/candidates.yaml"], ["ci-agents/ci-agents.md"], keep_licensed=True)[0]


def test_a_dump_at_the_location_root_fails_even_when_keeping_was_asked():
    passed, why = only(["ci-agents.candidates.yaml"], ["ci-agents/ci-agents.md"],
                       keep_licensed=True)
    assert not passed
    assert "ci-agents.candidates.yaml" in why


def test_family_files_in_a_proposal_folder_pass():
    added = ["ci-agents/ci-agents.md", "ci-agents/notes.md", "ci-agents/review.md",
             "ci-agents/feedback.md", "ci-agents/ci-agents.handout.md", "ci-agents/ci-agents.pdf",
             "ci-agents/img/pipeline.png"]
    passed, why = only(added)
    assert passed, why


def test_a_harvest_record_makes_its_folder_a_proposal_folder():
    assert only(["thesis-harvest/harvest.md", "thesis-harvest/img/figure.png"])[0]


def test_a_review_written_under_a_wrong_slug_fails():
    """Scenario: Review written under a wrong slug — in a folder that holds no
    proposal, notes file or harvest record, or at the location root."""
    for stray in ("old-agents/review.md", "review.md"):
        passed, why = only([stray], ["new-agents/new-agents.md"])
        assert not passed, stray
        assert stray in why


def test_a_staged_kept_file_renamed_with_its_folder_passes():
    """Scenario: Staged kept file renamed with its family."""
    staged = ["flaky-ci-triage/notes.md", "flaky-ci-triage/reading-list.md",
              "flaky-ci-triage/img/sketch.png"]
    renamed = ["flaky-triage/flaky-triage.md", "flaky-triage/notes.md",
               "flaky-triage/reading-list.md", "flaky-triage/img/sketch.png"]
    passed, why = only(renamed, staged=staged)
    assert passed, why
    passed, why = only([*renamed, "flaky-triage/candidates.yaml"], staged=staged)
    assert not passed
    assert "flaky-triage/candidates.yaml" in why
    assert "reading-list" not in why


def test_a_kept_file_beside_a_staged_one_that_stayed_is_no_rename():
    staged = ["flaky-ci-triage/notes.md", "flaky-ci-triage/reading-list.md"]
    passed, why = only(["flaky-triage/flaky-triage.md", "flaky-triage/reading-list.md"],
                       [*staged], staged=staged)
    assert not passed
    assert "flaky-triage/reading-list.md" in why


def test_kept_files_whose_labels_end_like_a_role_need_the_licence():
    added = ["ci-agents/peer-review.md", "ci-agents/reading-notes.md",
             "ci-agents/supervisor-feedback.md"]
    passed, why = only(added, ["ci-agents/ci-agents.md"])
    assert not passed
    for name in added:
        assert name in why


def test_ideation_that_ends_before_seeding_passes():
    """Scenario: Ideation that ends before seeding."""
    texts = {"idea/notes.md": NOTES_TEXT, "flaky-ci/notes.md": NOTES_TEXT}
    assert only(["idea/notes.md"], read=texts.__getitem__)[0]
    assert only(["flaky-ci/notes.md"], read=texts.__getitem__)[0]


def test_a_notes_file_without_the_headings_shelters_nothing():
    passed, why = only(["meetings/notes.md"], read={"meetings/notes.md": "# Minutes\n"}.get)
    assert not passed
    assert "meetings/notes.md" in why


def test_allowed_workspace_files_pass():
    added = ["api-keys.env", ".gitignore", "check-output.txt", "version-output.txt",
             "bug-report/report.md", "bug-report/repro/input/input.md",
             "bug-report/repro/command.txt", "guidelines.md",
             "skills-lock.json", ".agents/skills/x/SKILL.md",
             "ci-agents/proposal-build.sh", "ci-agents/.gitignore"]
    passed, why = only(added, ["ci-agents/ci-agents.md"])
    assert passed, why


def test_working_files_fail_and_every_one_is_named():
    added = ["candidates.yaml", "snowball-output.txt", "probe/run.py", "ci-agents.raw.json",
             "ci-agents/probe/run.sh", "ideation.notes.md", "ci-agents.notes.md"]
    passed, why = only(added, ["ci-agents/ci-agents.md"])
    assert not passed
    for name in added:
        assert name in why


def test_a_draft_written_beside_its_seed_fails_naming_both():
    """Scenario: Draft written beside its seed."""
    fresh = "drift-detection/drift-detection.md"
    passed, why = only([fresh], [SEED], staged=[SEED], seed=SEED)
    assert not passed
    assert SEED in why
    assert fresh in why
    # without a seed to keep, a fresh proposal is a proposal like any other
    assert only([fresh], [SEED], staged=[SEED])[0]


def test_a_draft_written_into_the_seed_passes():
    assert only(["data-drift-detection/notes.md"], [SEED], staged=[SEED], seed=SEED)[0]


def test_nothing_added_passes():
    passed, why = only([], [SEED], staged=[SEED], seed=SEED)
    assert passed
    assert "no file added" in why


# ---------- family-renamed -----------------------------------------------------


def text(body: str) -> bytes:
    return body.encode("utf-8")


def family(slug: str) -> dict[str, bytes]:
    link = "![Figure 1](img/pipeline.png)"
    return {
        f"{slug}/{slug}.md": text(f"# Title\n\n*Master's Thesis Proposal*\n\n{link}\n{METADATA}"),
        f"{slug}/notes.md": text(f"# Notes\n\n## Log\n\n- Added {link}.\n"),
        f"{slug}/harvest.md": text("# Harvest record\n"),
        f"{slug}/review.md": text(f"# Review of {OLD}\n\n1. Blocker.\n"),
        f"{slug}/img/pipeline.png": PNG,
    }


STAGED = {**family(OLD), f"{OLD}/{OLD}.pdf": b"%PDF-1.7 previous build",
          f"{OLD}/{OLD}.handout.md": text(f"# Title\n{METADATA}"), "guidelines.md": b"Prose.\n"}


def renamed(**changes) -> dict[str, bytes]:
    """The complete rename — the folder moved, the proposal file renamed, the
    previous outputs left under the old slug — then `changes` (a path, `__`
    for `/`, to new bytes, or to None to drop it)."""
    after = {path.replace(f"{OLD}/", f"{NEW}/", 1): data for path, data in STAGED.items()}
    after[f"{NEW}/{NEW}.md"] = after.pop(f"{NEW}/{OLD}.md")
    for path, data in changes.items():
        if data is None:
            after.pop(path.replace("__", "/"), None)
        else:
            after[path.replace("__", "/")] = data
    return after


def test_a_complete_rename_passes_and_names_the_previous_outputs():
    """Scenario: Handout left behind by a rename — the hand-in export and the
    build stay in the new folder under the old slug as previous outputs."""
    passed, why = verdict_family_renamed(STAGED, renamed(), OLD)
    assert passed, why
    assert f"`{NEW}/`" in why
    assert f"{NEW}/{OLD}.pdf" in why
    assert f"{NEW}/{OLD}.handout.md" in why


def test_previous_outputs_may_also_be_rebuilt_under_the_new_slug():
    after = renamed(**{f"{NEW}__{OLD}.pdf": None, f"{NEW}__{NEW}.pdf": b"%PDF-1.7 rebuilt"})
    assert verdict_family_renamed(STAGED, after, OLD)[0]


def test_a_figure_left_behind_fails_naming_the_file_and_the_old_folder():
    """Scenario: Figure left behind by a rename."""
    after = renamed(**{f"{NEW}__img__pipeline.png": None, f"{OLD}__img__pipeline.png": PNG})
    passed, why = verdict_family_renamed(STAGED, after, OLD)
    assert not passed
    assert f"{OLD}/img/pipeline.png" in why
    assert f"`{OLD}/`" in why


def test_a_proposal_file_left_under_the_old_slug_fails_naming_it():
    """Scenario: Proposal file left under the old slug."""
    after = renamed(**{f"{NEW}__{NEW}.md": None, f"{NEW}__{OLD}.md": STAGED[f"{OLD}/{OLD}.md"]})
    passed, why = verdict_family_renamed(STAGED, after, OLD)
    assert not passed
    assert f"{NEW}/{OLD}.md" in why
    assert renamed_proposal(STAGED, after, OLD)[0] is None


def test_a_changed_figure_fails():
    passed, why = verdict_family_renamed(STAGED, renamed(**{f"{NEW}__img__pipeline.png": b"x"}),
                                         OLD)
    assert not passed
    assert f"{NEW}/img/pipeline.png" in why


def test_a_changed_figure_link_fails():
    relinked = STAGED[f"{OLD}/{OLD}.md"].replace(b"img/pipeline.png", b"img/other.png")
    passed, why = verdict_family_renamed(STAGED, renamed(**{f"{NEW}__{NEW}.md": relinked}), OLD)
    assert not passed
    assert f"{NEW}/{NEW}.md" in why


def test_a_missing_harvest_record_fails():
    passed, why = verdict_family_renamed(STAGED, renamed(**{f"{NEW}__harvest.md": None}), OLD)
    assert not passed
    assert f"{NEW}/harvest.md" in why


def test_no_proposal_under_a_new_slug_fails():
    passed, why = verdict_family_renamed(STAGED, dict(STAGED), OLD)
    assert not passed
    assert "no proposal under a new slug" in why


def test_two_new_proposals_are_ambiguous():
    other = text(f"# Other\n\n*Master's Thesis Proposal*\n{METADATA}")
    passed, why = verdict_family_renamed(
        STAGED, renamed(**{"other-slug__other-slug.md": other}), OLD)
    assert not passed
    assert "other-slug/other-slug.md" in why


def test_a_seeding_rename_without_a_staged_proposal_passes():
    """At seeding the proposal is new: only the notes file, a kept file and a
    sketch were staged in the provisional folder."""
    staged = {"flaky-ci-triage/notes.md": text(NOTES_TEXT + "[sketch](img/sketch.png)\n"),
              "flaky-ci-triage/reading-list.md": text("- A paper\n"),
              "flaky-ci-triage/img/sketch.png": PNG}
    after = {"flaky-triage/flaky-triage.md": text(f"# Flaky Triage\n{METADATA}"),
             **{path.replace("flaky-ci-triage/", "flaky-triage/"): data
                for path, data in staged.items()}}
    passed, why = verdict_family_renamed(staged, after, "flaky-ci-triage")
    assert passed, why
    left = {**after, "flaky-ci-triage/reading-list.md": text("- A paper\n")}
    left.pop("flaky-triage/reading-list.md")
    passed, why = verdict_family_renamed(staged, left, "flaky-ci-triage")
    assert not passed
    assert "flaky-ci-triage/reading-list.md" in why


# ---------- no orphans ---------------------------------------------------------


def test_no_orphan_finding_passes_and_one_fails_naming_it():
    clean = [{"level": "warning", "rule": "title-buzzword", "message": "a title word"}]
    assert verdict_no_orphans(clean)[0]
    orphan = {"level": "warning", "rule": "companion-orphaned",
              "message": "`old/review.md` lies in `old/`"}
    passed, why = verdict_no_orphans([*clean, orphan])
    assert not passed
    assert "old/review.md" in why


def test_a_folder_name_error_over_the_renamed_proposal_fails():
    """Proposal-family coverage: the check over the renamed proposal reports
    neither an orphan warning nor a folder-name error."""
    mismatch = {"level": "error", "rule": "proposal-folder-mismatch",
                "message": "`new/old.md` lies in `new/`, named unlike its file"}
    passed, why = verdict_no_orphans([mismatch])
    assert not passed
    assert "proposal-folder-mismatch" in why
    assert "new/old.md" in why


def test_a_check_that_did_not_run_fails():
    """An absent orphan finding is evidence only when the check ran."""
    passed, why = verdict_no_orphans([{"rule": "check-failed",
                                       "message": "Traceback (most recent call last): …"}])
    assert not passed
    assert "did not run" in why
    assert "Traceback" in why


# ---------- kept on request (testing-harness: Folder-layout dev scenarios) ----------


def test_a_candidate_list_kept_in_the_proposals_folder_passes():
    """Scenario: Candidate list kept on request."""
    passed, why = verdict_kept_on_request(["ci-agents/candidates.yaml"],
                                          ["ci-agents/ci-agents.md"], ["ci-agents/ci-agents.md"],
                                          "ci-agents")
    assert passed, why
    assert "ci-agents/candidates.yaml" in why


def test_a_request_to_keep_that_kept_nothing_fails():
    passed, why = verdict_kept_on_request([], ["ci-agents/ci-agents.md"],
                                          ["ci-agents/ci-agents.md"], "ci-agents")
    assert not passed
    assert "no kept file" in why


def test_a_kept_list_outside_the_proposals_folder_fails():
    """At the location root, under the slug as its label, or in a subfolder,
    the list is no `<label>.<ext>` of the proposal's folder."""
    for stray in ("ci-agents.candidates.yaml", "candidates.yaml", "ci-agents/ci-agents.yaml",
                  "ci-agents/lists/candidates.yaml", "other/candidates.yaml"):
        passed, why = verdict_kept_on_request([stray], ["ci-agents/ci-agents.md"],
                                              ["ci-agents/ci-agents.md"], "ci-agents")
        assert not passed, stray
        assert "no kept file" in why, stray


def test_a_kept_list_beside_a_working_file_fails_on_family_only():
    passed, why = verdict_kept_on_request(
        ["ci-agents/candidates.yaml", "snowball-output.txt"], ["ci-agents/ci-agents.md"],
        ["ci-agents/ci-agents.md"], "ci-agents")
    assert not passed
    assert "snowball-output.txt" in why


# ---------- ideation from scratch (testing-harness: Folder-layout dev scenarios) ----


SEED_BODY = ("# Quarantine Decisions for Flaky Tests\n\n*Master's Thesis Proposal*\n\n"
             "A sketch.\n\n## References\n" + METADATA)
WS = "/tmp/devrun-ideate_from_scratch-x"
PROVISIONAL, FINAL = "flaky-test-quarantine", "quarantine-decisions-flaky-tests"


def write(turn: int, path: str, tool: str = "Write") -> tuple[int, str, dict]:
    return turn, tool, {"file_path": f"{WS}/{path}", "content": "…"}


def shell(turn: int, command: str) -> tuple[int, str, dict]:
    return turn, "Bash", {"command": command}


GOOD_CALLS = [
    write(0, "idea/notes.md"),
    shell(1, f"test ! -e {WS}/{PROVISIONAL} && mv {WS}/idea {WS}/{PROVISIONAL}"),
    write(1, f"{PROVISIONAL}/notes.md", "Edit"),
    shell(2, f"test ! -e {FINAL} && mv {PROVISIONAL} {FINAL} && ls {FINAL}/"),
    write(2, f"{FINAL}/{FINAL}.md"),
    write(2, f"{FINAL}/notes.md", "Edit"),
]
END_STATE = {f"{FINAL}/{FINAL}.md": SEED_BODY, f"{FINAL}/notes.md": NOTES_TEXT}


def scratch(calls=GOOD_CALLS, files=END_STATE):
    return verdict_ideate_from_scratch(list(calls), sorted(files), files.get)


def test_ideation_from_scratch_passes_on_the_recorded_moves():
    passed, why = scratch()
    assert passed, why
    assert f"`idea/` -> `{PROVISIONAL}/`" in why
    assert f"`{FINAL}/{FINAL}.md`" in why


def test_the_moves_may_be_written_in_one_shell_call():
    calls = [write(0, "idea/notes.md"), shell(1, f"mv idea/ ./{PROVISIONAL}/"),
             shell(2, f"git mv {PROVISIONAL} {FINAL}; cat > {FINAL}/{FINAL}.md <<'EOF'\n# T\nEOF")]
    passed, why = scratch(calls)
    assert passed, why


def test_a_seed_written_straight_into_the_final_folder_fails():
    calls = [write(0, "idea/notes.md"), shell(2, f"mv idea {FINAL}"),
             write(2, f"{FINAL}/{FINAL}.md")]
    passed, why = scratch(calls)
    assert not passed
    assert "provisional" in why


def test_a_provisional_slug_that_is_already_the_final_one_counts():
    """The agent picks both slugs, so the topic phrase may already yield the
    working title's slug: the move in the topic-phrase turn is the provisional
    step, and no seeding rename is needed. The explanation says that one was
    not exercised."""
    calls = [write(0, "idea/notes.md"), shell(1, f"test ! -e {FINAL} && mv idea {FINAL}"),
             write(1, f"{FINAL}/notes.md", "Edit"), write(2, f"{FINAL}/{FINAL}.md")]
    passed, why = scratch(calls)
    assert passed, why
    assert f"`idea/` -> `{FINAL}/`" in why
    assert "no seeding rename" in why


def test_a_provisional_move_after_the_seed_does_not_count():
    calls = [write(0, "idea/notes.md"), write(2, f"{FINAL}/{FINAL}.md"),
             shell(2, f"mv idea {PROVISIONAL}")]
    passed, why = scratch(calls)
    assert not passed
    assert "before the seed" in why


def test_notes_written_fresh_under_the_final_slug_fail():
    calls = [write(0, "idea/notes.md"), shell(1, f"mv idea {PROVISIONAL}"),
             write(2, f"{FINAL}/notes.md"), write(2, f"{FINAL}/{FINAL}.md"),
             shell(2, f"rm -r {PROVISIONAL}")]
    passed, why = scratch(calls)
    assert not passed
    assert f"`{FINAL}/notes.md` written fresh" in why
    calls[2] = shell(2, f"printf '## Log\\n' > {FINAL}/notes.md")
    passed, why = scratch(calls)
    assert not passed
    assert "written fresh" in why


def test_notes_rewritten_after_the_folder_moved_are_not_fresh():
    calls = [*GOOD_CALLS, write(2, f"{FINAL}/notes.md")]
    passed, why = scratch(calls)
    assert passed, why


def test_notes_not_written_in_the_first_turn_fail():
    calls = [shell(0, "ls"), write(1, "idea/notes.md"), *GOOD_CALLS[1:]]
    passed, why = scratch(calls)
    assert not passed
    assert "first turn" in why


def test_a_notes_file_missing_a_heading_fails():
    notes = NOTES_TEXT.replace("## Next Focus", "## Next steps")
    passed, why = scratch(files={**END_STATE, f"{FINAL}/notes.md": notes})
    assert not passed
    assert "Next Focus" in why


def test_leftover_idea_or_provisional_folders_fail():
    for left in ("idea/reading-list.md", f"{PROVISIONAL}/sketch.md"):
        passed, why = scratch(files={**END_STATE, left: "- a paper\n"})
        assert not passed, left
        assert f"`{left.partition('/')[0]}/`" in why, left


def test_a_file_outside_the_proposal_folder_fails():
    passed, why = scratch(files={**END_STATE, "guidelines.md": "Prose.\n"})
    assert not passed
    assert "guidelines.md" in why


def test_no_seed_or_two_seeds_fail():
    passed, why = scratch(files={f"{PROVISIONAL}/notes.md": NOTES_TEXT})
    assert not passed
    assert "no seeded proposal" in why
    other = {"other-topic/other-topic.md": SEED_BODY}
    passed, why = scratch(files={**END_STATE, **other})
    assert not passed
    assert "other-topic/other-topic.md" in why
