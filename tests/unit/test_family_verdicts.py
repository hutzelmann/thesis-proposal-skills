"""L0: the proposal-family verdicts (testing-harness: Proposal-family coverage).

`verdict_family_only` judges which files a run added, `verdict_family_renamed`
whether a rename moved the whole family, and `verdict_no_orphans` reads the
check's own findings. The first two classify with check.py's family vocabulary,
never a second one; all three are pure, so no workspace is needed here.
"""

from l1_checks import verdict_family_only, verdict_family_renamed, verdict_no_orphans

SEED = "data-drift-detection.md"
METADATA = "\n\n---\nreferences: []\n---\n"
PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
OLD, NEW = "ci-repair-agent-configurations", "context-repair-agents"


def only(added, present=(), **kwargs):
    """`present` is everything after the run; the added files are part of it."""
    return verdict_family_only(list(added), sorted({*present, *added}), **kwargs)


# ---------- family-only --------------------------------------------------------


def test_a_dump_under_the_correct_slug_fails_unless_keeping_was_asked():
    passed, why = only(["ci-agents.candidates.yaml"], ["ci-agents.md"])
    assert not passed
    assert "ci-agents.candidates.yaml" in why
    assert only(["ci-agents.candidates.yaml"], ["ci-agents.md"], keep_licensed=True)[0]


def test_family_files_of_a_sheltered_slug_pass():
    added = ["ci-agents.md", "ci-agents.notes.md", "ci-agents-review.md",
             "ci-agents-feedback.md", "ci-agents-handout.md", "ci-agents.pdf",
             "img/ci-agents-pipeline.png"]
    passed, why = only(added)
    assert passed, why


def test_a_harvest_record_shelters_its_slug():
    assert only(["thesis-harvest.harvest.md", "img/thesis-harvest-figure.png"])[0]


def test_companions_of_an_unsheltered_slug_fail():
    passed, why = only(["old-agents-handout.md", "old-agents.pdf"], ["new-agents.md"])
    assert not passed
    assert "old-agents-handout.md" in why
    assert "old-agents.pdf" in why


def test_a_staged_kept_file_renamed_with_its_family_passes():
    staged = ["flaky-ci-triage.notes.md", "flaky-ci-triage.reading-list.md",
              "img/flaky-ci-triage-sketch.png"]
    renamed = ["flaky-triage.md", "flaky-triage.notes.md", "flaky-triage.reading-list.md",
               "img/flaky-triage-sketch.png"]
    passed, why = only(renamed, staged=staged)
    assert passed, why
    passed, why = only([*renamed, "flaky-triage.candidates.yaml"], staged=staged)
    assert not passed
    assert "flaky-triage.candidates.yaml" in why
    assert "reading-list" not in why


def test_a_kept_file_beside_a_staged_one_that_stayed_is_no_rename():
    staged = ["flaky-ci-triage.notes.md", "flaky-ci-triage.reading-list.md"]
    passed, why = only(["flaky-triage.md", "flaky-triage.reading-list.md"],
                       [*staged], staged=staged)
    assert not passed
    assert "flaky-triage.reading-list.md" in why


def test_a_review_under_a_slug_no_proposal_carries_fails_as_the_check_reports_it():
    """The verdict reads what the check reads: a `-review` file whose base
    slug has no proposal is a proposal only when it ends in a metadata block."""
    texts = {"ci-agent-configurations.md": "# Title\n" + METADATA,
             "ci-agents-review.md": "Verdict: revise.\n",
             "ml-code-review.md": "# Title\n" + METADATA}
    passed, why = only(["ci-agents-review.md"], ["ci-agent-configurations.md"],
                       staged=["ci-agent-configurations.md"], read=texts.__getitem__)
    assert not passed
    assert "ci-agents-review.md" in why
    assert "ci-agents" in why
    # a proposal that only reads like a review shelters itself
    assert only(["ml-code-review.md"], read=texts.__getitem__)[0]
    # beside its proposal a review is never read
    assert only(["ci-agents.md", "ci-agents-review.md"], read=never_read)[0]


def never_read(path: str) -> str:
    raise AssertionError(f"`{path}` was read, though its base slug has a proposal")


def test_an_unreadable_review_stays_a_proposal_as_in_the_check():
    def refuse(path: str) -> str:
        raise OSError(path)

    assert only(["ci-agents-review.md"], ["other-topic.md"], read=refuse)[0]
    assert only(["ci-agents-review.md"], ["other-topic.md"])[0]


def test_runs_that_end_before_seeding_pass():
    assert only(["flaky-ci-triage.notes.md"])[0]
    assert only(["ideation.notes.md"])[0]


def test_allowed_workspace_files_pass():
    added = ["api-keys.env", ".gitignore", "check-output.txt", "version-output.txt",
             "bug-report/report.md", "bug-report/repro/input.md", "guidelines.md",
             "proposal-build.sh", "skills-lock.json", ".agents/skills/x/SKILL.md"]
    passed, why = only(added)
    assert passed, why


def test_working_files_fail_and_every_one_is_named():
    added = ["candidates.yaml", "snowball-output.txt", "probe/run.py", "ci-agents.raw.json",
             "ci-agents.probe/run.sh"]
    passed, why = only(added, ["ci-agents.md"])
    assert not passed
    for name in added:
        assert name in why


def test_a_fresh_proposal_beside_the_seed_fails_naming_both():
    passed, why = only(["drift-detection.md"], [SEED], staged=[SEED], seed=SEED)
    assert not passed
    assert SEED in why
    assert "drift-detection.md" in why
    # without a seed to keep, a fresh proposal is a proposal like any other
    assert only(["drift-detection.md"], [SEED], staged=[SEED])[0]


def test_a_draft_written_into_the_seed_passes():
    assert only(["data-drift-detection.notes.md"], [SEED], staged=[SEED], seed=SEED)[0]


def test_nothing_added_passes():
    passed, why = only([], [SEED], staged=[SEED], seed=SEED)
    assert passed
    assert "no file added" in why


# ---------- family-renamed -----------------------------------------------------


def text(body: str) -> bytes:
    return body.encode("utf-8")


def family(slug: str) -> dict[str, bytes]:
    link = f"![Figure 1](img/{slug}-pipeline.png)"
    return {
        f"{slug}.md": text(f"# Title\n\n*Master's Thesis Proposal*\n\n{link}\n{METADATA}"),
        f"{slug}.notes.md": text(f"# {slug} — notes\n\n## Log\n\n- Added {link}.\n"),
        f"{slug}.harvest.md": text("# Harvest record\n"),
        f"{slug}-review.md": text(f"# Review of {OLD}\n\n1. Blocker.\n"),
        f"{slug}-handout.md": text(f"# Title\n{METADATA}"),
        f"img/{slug}-pipeline.png": PNG,
        "guidelines.md": text("Prose only.\n"),
    }


STAGED = {**family(OLD), f"{OLD}.pdf": b"%PDF-1.7 previous build"}


def renamed(**changes) -> dict[str, bytes]:
    """The complete rename, the previous build left in place, then `changes`
    (a path to new bytes, or to None to drop it)."""
    after = {**family(NEW), f"{OLD}.pdf": STAGED[f"{OLD}.pdf"]}
    after[f"{NEW}-review.md"] = STAGED[f"{OLD}-review.md"]  # a review's text is never edited
    for path, data in changes.items():
        if data is None:
            after.pop(path.replace("__", "/"), None)
        else:
            after[path.replace("__", "/")] = data
    return after


def test_a_complete_rename_passes_and_leaves_the_previous_build():
    passed, why = verdict_family_renamed(STAGED, renamed(), OLD)
    assert passed, why
    assert NEW in why


def test_a_figure_left_behind_fails():
    after = renamed(**{f"img__{NEW}-pipeline.png": None, f"img__{OLD}-pipeline.png": PNG})
    passed, why = verdict_family_renamed(STAGED, after, OLD)
    assert not passed
    assert f"img/{OLD}-pipeline.png" in why


def test_a_handout_left_behind_fails():
    after = renamed(**{f"{NEW}-handout.md": None,
                       f"{OLD}-handout.md": STAGED[f"{OLD}-handout.md"]})
    passed, why = verdict_family_renamed(STAGED, after, OLD)
    assert not passed
    assert f"{OLD}-handout.md" in why


def test_a_changed_figure_fails():
    passed, why = verdict_family_renamed(STAGED, renamed(**{f"img__{NEW}-pipeline.png": b"x"}),
                                         OLD)
    assert not passed
    assert f"img/{NEW}-pipeline.png" in why


def test_a_stale_link_in_the_notes_fails():
    stale = family(OLD)[f"{OLD}.notes.md"]
    passed, why = verdict_family_renamed(STAGED, renamed(**{f"{NEW}.notes.md": stale}), OLD)
    assert not passed
    assert f"{NEW}.notes.md" in why
    assert f"img/{OLD}-" in why


def test_a_stale_link_in_the_proposal_fails():
    stale = family(OLD)[f"{OLD}.md"]
    passed, why = verdict_family_renamed(STAGED, renamed(**{f"{NEW}.md": stale}), OLD)
    assert not passed
    assert f"{NEW}.md" in why


def test_a_missing_harvest_record_fails():
    passed, why = verdict_family_renamed(STAGED, renamed(**{f"{NEW}.harvest.md": None}), OLD)
    assert not passed
    assert f"{NEW}.harvest.md" in why


def test_no_proposal_under_a_new_slug_fails():
    passed, why = verdict_family_renamed(STAGED, dict(STAGED), OLD)
    assert not passed
    assert "no proposal under a new slug" in why


def test_two_new_proposals_are_ambiguous():
    passed, why = verdict_family_renamed(STAGED, renamed(**{"other-slug.md": text("# T\n")}),
                                         OLD)
    assert not passed
    assert "other-slug.md" in why


def test_a_new_slug_that_extends_the_old_one_is_not_a_leftover():
    longer = OLD + "-v2"
    after = {path.replace(OLD, longer, 1) if path != f"{OLD}.pdf" else path: data
             for path, data in STAGED.items()}
    after = {p: (d.replace(text(f"img/{OLD}-"), text(f"img/{longer}-"))
                 if p.endswith(".md") else d) for p, d in after.items()}
    passed, why = verdict_family_renamed(STAGED, after, OLD)
    assert passed, why


def test_a_seeding_rename_without_a_staged_proposal_passes():
    """At seeding the proposal is new: only the notes file, a kept file and a
    sketch were staged under the provisional slug."""
    staged = {"flaky-ci-triage.notes.md": text("[sketch](img/flaky-ci-triage-sketch.png)\n"),
              "flaky-ci-triage.reading-list.md": text("- A paper\n"),
              "img/flaky-ci-triage-sketch.png": PNG}
    after = {"flaky-triage.md": text(f"# Flaky Triage\n{METADATA}"),
             "flaky-triage.notes.md": text("[sketch](img/flaky-triage-sketch.png)\n"),
             "flaky-triage.reading-list.md": text("- A paper\n"),
             "img/flaky-triage-sketch.png": PNG}
    passed, why = verdict_family_renamed(staged, after, "flaky-ci-triage")
    assert passed, why
    left = {**after, "flaky-ci-triage.reading-list.md": text("- A paper\n")}
    left.pop("flaky-triage.reading-list.md")
    passed, why = verdict_family_renamed(staged, left, "flaky-ci-triage")
    assert not passed
    assert "flaky-ci-triage.reading-list.md" in why


# ---------- no orphans ---------------------------------------------------------


def test_no_orphan_finding_passes_and_one_fails_naming_it():
    clean = [{"level": "warning", "rule": "title-buzzword", "message": "a title word"}]
    assert verdict_no_orphans(clean)[0]
    orphan = {"level": "warning", "rule": "companion-orphaned",
              "message": "`old-review.md` carries the slug `old`"}
    passed, why = verdict_no_orphans([*clean, orphan])
    assert not passed
    assert "old-review.md" in why


def test_a_check_that_did_not_run_fails():
    """An absent orphan finding is evidence only when the check ran."""
    passed, why = verdict_no_orphans([{"rule": "check-failed",
                                       "message": "Traceback (most recent call last): …"}])
    assert not passed
    assert "did not run" in why
    assert "Traceback" in why
