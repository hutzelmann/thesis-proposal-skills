"""L0: the bug-report collector shipped in proposal-troubleshoot (no model calls).

Two properties carry the weight. The disclosure level is a privacy boundary, so
`minimal` is tested for what it must NOT contain rather than only for what it
does. And the git blob hash is checked against `git hash-object` itself, because
`scripts/identify_release.py` resolves reports by that hash — if the collector
computes it differently, every submitted report becomes unidentifiable.
"""

import json
import subprocess
from pathlib import Path

import pytest
from collect import (
    canonical_titles,
    describe_proposal,
    file_hashes,
    git_blob_hash,
    main,
    notes_log,
    redact_text,
    resolve_model,
    sibling_artifacts,
    strip_personal_data,
)

REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "skills" / "proposal-troubleshoot"

PROPOSAL = """# Fibre Tension in Low-Gravity Basket Weaving

*Master's Thesis Proposal*

## Introduction to the Topic

Orbital looms are underexplored [@musterfrau2027].

## My Secret Sauce Section

The topic is fibre tension. [TODO: settle the vendor agreement]

## Timeline

Start October 2027, submission March 2028.

## References

---
author: Erika Musterfrau
references:
  - id: musterfrau2027
    DOI: 10.1000/synthetic.0001
---
"""

NOTES = """# Notes

## Decisions

- Chose prototype over SLR.

## Log

- 2026-08-01 seeded
- 2026-08-03 four references added

## Excluded Literature

- 10.1000/irrelevant.9999 — wrong field.
"""


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    (tmp_path / "quantum-basket-weaving.md").write_text(PROPOSAL, encoding="utf-8")
    (tmp_path / "quantum-basket-weaving.notes.md").write_text(NOTES, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def run(argv, cwd_proposal="quantum-basket-weaving.md", **extra):
    args = [cwd_proposal, *argv]
    return main(args, **extra)


# --------------------------------------------------------------------------
# hashing — the contract with identify_release.py
# --------------------------------------------------------------------------

def test_git_blob_hash_matches_git_itself(tmp_path):
    target = tmp_path / "sample.md"
    target.write_bytes(b"# heading\n\nbody text\n")
    expected = subprocess.run(
        ["git", "hash-object", str(target)], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert git_blob_hash(target.read_bytes()) == expected


def test_git_blob_hash_of_empty_content_matches_gits_empty_blob():
    assert git_blob_hash(b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"


def test_crlf_content_reports_both_a_raw_and_a_normalized_blob(tmp_path):
    """A Windows checkout holds CRLF while git stored LF; without the normalized
    hash such a file would match no revision and read as locally modified."""
    target = tmp_path / "crlf.md"
    target.write_bytes(b"line one\r\nline two\r\n")
    hashes = file_hashes(target)
    assert "git_blob_lf" in hashes
    assert hashes["git_blob"] != hashes["git_blob_lf"]
    assert hashes["git_blob_lf"] == git_blob_hash(b"line one\nline two\n")


def test_lf_content_reports_no_redundant_normalized_blob(tmp_path):
    target = tmp_path / "lf.md"
    target.write_bytes(b"line one\nline two\n")
    assert "git_blob_lf" not in file_hashes(target)


# --------------------------------------------------------------------------
# disclosure levels
# --------------------------------------------------------------------------

def test_minimal_carries_no_proposal_prose(workspace):
    out = "\n".join(describe_proposal(workspace / "quantum-basket-weaving.md", "minimal"))
    assert "Secret Sauce" not in out
    assert "vendor agreement" not in out
    assert "Fibre Tension" not in out  # the title heading is proposal text
    assert "fibre tension" not in out.lower()
    assert "10.1000/synthetic.0001" not in out
    assert "1 open TODO marker(s)" in out
    assert "8 of 9" not in out  # counts are reported, not fabricated


def test_minimal_reports_how_many_headings_are_canonical(workspace):
    out = "\n".join(describe_proposal(workspace / "quantum-basket-weaving.md", "minimal"))
    assert "3 of 4 section headings match a canonical title" in out
    assert "the title heading is not counted" in out
    assert "heading text withheld" in out


def test_structure_adds_headings_todos_and_dois_but_masks_the_title(workspace):
    out = "\n".join(describe_proposal(workspace / "quantum-basket-weaving.md", "structure"))
    assert "My Secret Sauce Section" in out
    assert "[TODO: settle the vendor agreement]" in out
    assert "10.1000/synthetic.0001" in out
    assert "Orbital looms are underexplored" not in out
    # the leading H1 is the unpublished thesis title — masked, never verbatim
    assert "# [title withheld]   (title)" in out
    assert "Fibre Tension" not in out


def test_full_adds_the_body_with_personal_data_removed(workspace):
    out = "\n".join(describe_proposal(workspace / "quantum-basket-weaving.md", "full"))
    assert "Orbital looms are underexplored" in out
    assert "Fibre Tension in Low-Gravity Basket Weaving" in out
    assert "Erika" not in out
    assert "Musterfrau" not in out.replace("musterfrau2027", "")


def test_the_proposal_filename_never_appears_verbatim(workspace):
    """The slug is derived from the topic, so it discloses at every level."""
    for level in ("minimal", "structure", "full"):
        out = "\n".join(describe_proposal(workspace / "quantum-basket-weaving.md", level))
        assert "quantum-basket-weaving" not in out, f"leaked at level {level}"


def test_strip_personal_data_removes_addresses_and_numbers():
    stripped = strip_personal_data("Reach me at erika@example.org, matriculation 00000000.")
    assert "erika@example.org" not in stripped
    assert "00000000" not in stripped


# --------------------------------------------------------------------------
# redaction of captured script output
# --------------------------------------------------------------------------

def test_redaction_keeps_canonical_titles_and_drops_user_wording():
    allowed = canonical_titles()
    assert "Timeline" in allowed, "the shipped skeleton did not load"
    text = (
        "# Check: quantum-basket-weaving.md\n"
        "- ERROR: required section missing: `Timeline`\n"
        "- ERROR: forbidden section: `My Secret Sauce Section`\n"
        "- WARNING: open [TODO: settle the vendor agreement]\n"
    )
    out = redact_text(text, allowed, {"quantum-basket-weaving.md", "quantum-basket-weaving"})
    assert "`Timeline`" in out, "a canonical title carries no user content and must survive"
    assert "Secret Sauce" not in out
    assert "vendor agreement" not in out
    assert "quantum-basket-weaving" not in out
    assert "required section missing" in out, "the finding category must survive redaction"


def test_redaction_survives_a_missing_skeleton():
    """Losing the allowlist must redact more, never less."""
    out = redact_text("- ERROR: missing: `Timeline`", set(), set())
    assert "`Timeline`" not in out


# --------------------------------------------------------------------------
# notes-file log extraction
# --------------------------------------------------------------------------

def test_notes_log_extracts_only_the_log_section(workspace):
    name, text = notes_log(workspace / "quantum-basket-weaving.md")
    assert name == "notes-log.md"
    assert "2026-08-03 four references added" in text
    assert "Chose prototype over SLR" not in text
    assert "wrong field" not in text, "the Log section ends at the next same-level heading"


def test_sibling_artifacts_inventoried_at_hash_level(workspace):
    """Supervise session: review file and send-package appear with sizes and
    hashes under placeholder names, and none of their text (skill-troubleshoot
    spec: companion artifacts inventoried at hash level)."""
    letter = "Verdict: idea stage. 1. Sharpen the question — proposal-ideate."
    (workspace / "quantum-basket-weaving-review.md").write_text(
        "no viable thesis core\n1. secret finding text", encoding="utf-8")
    package = workspace / "quantum-basket-weaving-package"
    package.mkdir()
    (package / "letter.md").write_text(letter, encoding="utf-8")
    (package / "quantum-basket-weaving.md").write_text(PROPOSAL, encoding="utf-8")

    lines = sibling_artifacts(workspace / "quantum-basket-weaving.md")
    joined = "\n".join(lines)
    assert "<proposal>-review.md" in joined
    assert "<proposal>-package/" in joined
    assert "letter.md" in joined
    assert "quantum-basket-weaving" not in joined
    assert "secret finding text" not in joined
    assert "Sharpen the question" not in joined
    assert joined.count("sha256:") == 3


def test_sibling_artifacts_absent_in_student_workspace(workspace):
    assert sibling_artifacts(workspace / "quantum-basket-weaving.md") == []
    assert sibling_artifacts(None) == []


def test_full_level_report_still_excludes_companion_text(workspace):
    package = workspace / "quantum-basket-weaving-package"
    package.mkdir()
    (package / "letter.md").write_text("Verdict: idea stage. Unique-letter-phrase.",
                                       encoding="utf-8")
    assert run(["--level", "full"]) == 0
    report = (workspace / "bug-report" / "report.md").read_text(encoding="utf-8")
    assert "<proposal>-package/" in report
    assert "Unique-letter-phrase" not in report


BUILD_SCRIPT = "# faculty-template-path-nobody-else-should-see\nprint('built')\n"


def test_workspace_build_definition_recorded(workspace):
    """Without this line a workspace-built document is indistinguishable from
    one the shipped pipeline produced, and the report reads as "works for me"."""
    (workspace / "proposal-build.py").write_text(BUILD_SCRIPT, encoding="utf-8")
    joined = "\n".join(sibling_artifacts(workspace / "quantum-basket-weaving.md"))
    assert "proposal-build.py" in joined
    assert "sha256:" in joined
    assert "not built by the shipped pipeline" in joined
    assert "faculty-template-path-nobody-else-should-see" not in joined


def test_workspace_build_recipe_recorded_only_with_the_target(workspace):
    makefile = workspace / "Makefile"
    makefile.write_text("all:\n\techo hi\n", encoding="utf-8")
    assert sibling_artifacts(workspace / "quantum-basket-weaving.md") == []
    makefile.write_text("proposal-build:\n\tpandoc $(PROPOSAL_PATH)\n", encoding="utf-8")
    joined = "\n".join(sibling_artifacts(workspace / "quantum-basket-weaving.md"))
    assert "Makefile (target `proposal-build`)" in joined


def test_full_level_report_excludes_build_definition_content(workspace):
    (workspace / "proposal-build.py").write_text(BUILD_SCRIPT, encoding="utf-8")
    assert run(["--level", "full"]) == 0
    report = (workspace / "bug-report" / "report.md").read_text(encoding="utf-8")
    assert "proposal-build.py" in report
    assert "faculty-template-path-nobody-else-should-see" not in report


def test_build_definition_names_match_publishs_own():
    """The collector restates publish.py's constants rather than importing
    across skills. Pinning them here is what keeps the two from drifting."""
    import collect
    import publish

    assert collect.BUILD_STEM == publish.BUILD_STEM
    assert frozenset(publish.RECIPE_RUNNERS) == collect.BUILD_RECIPE_NAMES
    assert collect.BUILD_TARGET_RE.pattern == publish.RECIPE_TARGET_RE.pattern


def test_notes_log_absent_is_not_an_error(tmp_path):
    lonely = tmp_path / "solo.md"
    lonely.write_text(PROPOSAL, encoding="utf-8")
    assert notes_log(lonely) is None


# --------------------------------------------------------------------------
# model resolution against the vendored verdicts
# --------------------------------------------------------------------------

def test_vendored_verdicts_distinguish_untested_from_failing():
    data = json.loads((SKILL / "references" / "model-support.json").read_text(encoding="utf-8"))
    seen = {c for m in data["models"].values() for c in m["skills"].values()}
    assert "untested" in seen, "no untested cell present — the distinction is untested itself"
    assert seen <= {"solid", "flaky", "fail", "untested"}, f"unexpected classification in {seen}"
    assert "untested" in data["statuses"]


def test_resolve_model_matches_a_bare_name_by_suffix():
    """An agent reports `claude-opus-5`; the roster keys it with a vendor prefix."""
    key, record = resolve_model("claude-opus-5")
    assert key == "anthropic/claude-opus-5"
    assert "verdict" in record


def test_resolve_model_accepts_the_full_key_and_a_routing_prefix():
    assert resolve_model("anthropic/claude-opus-5")[0] == "anthropic/claude-opus-5"
    assert resolve_model("openrouter/anthropic/claude-opus-5")[0] == "anthropic/claude-opus-5"


def test_resolve_model_returns_nothing_for_an_unknown_model():
    """Absence must not resolve to some neighbouring model's verdict."""
    key, record = resolve_model("some-model-we-never-measured")
    assert key is None
    assert record == {}


def test_resolve_model_reports_a_known_failing_skill():
    _, record = resolve_model("claude-haiku-4.5")
    assert record["skills"]["proposal-write"] == "fail"


# --------------------------------------------------------------------------
# bundle writing
# --------------------------------------------------------------------------

def test_dry_run_writes_nothing(workspace, capsys):
    assert run(["--dry-run"]) == 0
    assert not (workspace / "bug-report").exists()
    assert "would write into" in capsys.readouterr().out


def test_write_produces_the_bundle_and_nothing_outside_it(workspace):
    before = {p.name for p in workspace.iterdir()}
    assert run([]) == 0
    bundle = workspace / "bug-report"
    assert (bundle / "report.md").is_file()
    assert (bundle / "hashes.txt").is_file()
    after = {p.name for p in workspace.iterdir()}
    assert after - before == {"bug-report"}, "the collector wrote outside its bundle"


def test_the_proposal_is_never_modified(workspace):
    """A read-only skill may end in this offer; the file it examined must be
    untouched afterwards, digest and all."""
    proposal = workspace / "quantum-basket-weaving.md"
    before = proposal.read_bytes()
    assert run([]) == 0
    assert proposal.read_bytes() == before


@pytest.mark.usefixtures("workspace")
def test_refuses_to_overwrite_an_existing_bundle(capsys):
    assert run([]) == 0
    assert run([]) == 3
    assert "already exists" in capsys.readouterr().err


def test_force_replaces_rather_than_merges(workspace):
    assert run([]) == 0
    stale = workspace / "bug-report" / "artifacts" / "stale-from-an-earlier-run.txt"
    stale.write_text("old", encoding="utf-8")
    assert run(["--force"]) == 0
    assert not stale.exists(), "a half-stale bundle reads as a whole one"


def test_force_refuses_a_directory_that_is_not_a_bundle(workspace, capsys):
    victim = workspace / "bug-report"
    victim.mkdir()
    (victim / "important.txt").write_text("not a bundle", encoding="utf-8")
    assert run(["--force"]) == 3
    assert (victim / "important.txt").is_file()
    assert "not a bug-report bundle" in capsys.readouterr().err


def test_report_tags_every_environment_fact_as_measured(workspace):
    assert run([]) == 0
    report = (workspace / "bug-report" / "report.md").read_text(encoding="utf-8")
    assert "[measured] python " in report
    assert "[self-reported] model:" in report
    assert "[self-reported] replay" not in report  # placeholder wording, not a claim


def test_captured_script_output_is_redacted_in_artifacts_too(workspace):
    """The stored copy must obey the level exactly as the report does — writing it
    verbatim would hand out at minimal precisely what minimal withholds."""
    captured = workspace / "check-output.txt"
    captured.write_text(
        "# Check: quantum-basket-weaving.md\n- WARNING: open [TODO: settle the vendor agreement]\n",
        encoding="utf-8",
    )
    assert run(["--script-output", "check-output.txt"]) == 0
    stored = (workspace / "bug-report" / "artifacts" / "check-output.txt").read_text(
        encoding="utf-8"
    )
    assert "vendor agreement" not in stored
    assert "quantum-basket-weaving" not in stored


def test_full_level_keeps_captured_output_verbatim(workspace):
    captured = workspace / "check-output.txt"
    captured.write_text("- WARNING: open [TODO: settle the vendor agreement]\n", encoding="utf-8")
    assert run(["--level", "full", "--script-output", "check-output.txt"]) == 0
    stored = (workspace / "bug-report" / "artifacts" / "check-output.txt").read_text(
        encoding="utf-8"
    )
    assert "vendor agreement" in stored


@pytest.mark.usefixtures("workspace")
def test_missing_proposal_is_reported_rather_than_guessed(capsys):
    assert main(["no-such-file.md"]) == 2
    assert "not found" in capsys.readouterr().err


def test_runs_without_a_proposal_at_all(workspace):
    """An ideation session that crashed before seeding is still reportable."""
    assert main([]) == 0
    report = (workspace / "bug-report" / "report.md").read_text(encoding="utf-8")
    assert "no proposal file was named" in report


def test_hashes_cover_scripts_and_references_not_only_instructions(workspace):
    assert run([]) == 0
    lines = (workspace / "bug-report" / "hashes.txt").read_text(encoding="utf-8")
    assert "proposal-troubleshoot/scripts/collect.py" in lines
    assert "proposal-troubleshoot/references/model-support.json" in lines
    assert "__pycache__" not in lines


def test_hash_lines_carry_no_absolute_paths(workspace):
    assert run([]) == 0
    lines = (workspace / "bug-report" / "hashes.txt").read_text(encoding="utf-8")
    assert str(Path.home()) not in lines
    assert not any(ln.startswith("/") for ln in lines.splitlines())
