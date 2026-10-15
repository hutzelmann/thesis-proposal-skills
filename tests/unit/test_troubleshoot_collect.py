"""L0: the bug-report collector shipped in proposal-troubleshoot (no model calls).

Two properties carry the weight. The disclosure level is a privacy boundary, so
`minimal` is tested for what it must NOT contain rather than only for what it
does. And the git blob hash is checked against `git hash-object` itself, because
`scripts/identify_release.py` resolves reports by that hash — if the collector
computes it differently, every submitted report becomes unidentifiable.
"""

import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath

import collect
import pytest
from collect import (
    canonical_titles,
    describe_proposal,
    file_hashes,
    git_blob_hash,
    main,
    normalize_model_id,
    notes_log,
    redact_text,
    resolve_model,
    sibling_artifacts,
    strip_personal_data,
)
from helpers import CLEAN_DRAFT, fake_home, run_check, write_proposal

import install

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


SLUG = "quantum-basket-weaving"
# every word of the slug: none may leave the workspace below the full level
SLUG_WORDS = re.compile(r"quantum|basket|weaving", re.IGNORECASE)


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """A workspace root holding one proposal in its folder, with its notes
    file beside it, and the root as working directory."""
    proposal = write_proposal(tmp_path, SLUG, PROPOSAL)
    (proposal.parent / "notes.md").write_text(NOTES, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def proposal_in(workspace: Path) -> Path:
    return workspace / SLUG / f"{SLUG}.md"


def run(argv, cwd_proposal=f"{SLUG}/{SLUG}.md", **extra):
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
    out = "\n".join(describe_proposal(proposal_in(workspace), "minimal"))
    assert "Secret Sauce" not in out
    assert "vendor agreement" not in out
    assert "Fibre Tension" not in out  # the title heading is proposal text
    assert "fibre tension" not in out.lower()
    assert "10.1000/synthetic.0001" not in out
    assert "1 open TODO marker(s)" in out
    assert "8 of 9" not in out  # counts are reported, not fabricated


def test_minimal_reports_how_many_headings_are_canonical(workspace):
    out = "\n".join(describe_proposal(proposal_in(workspace), "minimal"))
    assert "3 of 4 section headings match a canonical title" in out
    assert "the title heading is not counted" in out
    assert "heading text withheld" in out


def test_structure_adds_headings_todos_and_dois_but_masks_the_title(workspace):
    out = "\n".join(describe_proposal(proposal_in(workspace), "structure"))
    assert "My Secret Sauce Section" in out
    assert "[TODO: settle the vendor agreement]" in out
    assert "10.1000/synthetic.0001" in out
    assert "Orbital looms are underexplored" not in out
    # the leading H1 is the unpublished thesis title — masked, never verbatim
    assert "# [title withheld]   (title)" in out
    assert "Fibre Tension" not in out


def test_full_adds_the_body_with_personal_data_removed(workspace):
    out = "\n".join(describe_proposal(proposal_in(workspace), "full"))
    assert "Orbital looms are underexplored" in out
    assert "Fibre Tension in Low-Gravity Basket Weaving" in out
    assert "Erika" not in out
    assert "Musterfrau" not in out.replace("musterfrau2027", "")


def test_the_proposal_filename_never_appears_verbatim(workspace):
    """The slug is derived from the topic, so it discloses at every level."""
    for level in ("minimal", "structure", "full"):
        out = "\n".join(describe_proposal(proposal_in(workspace), level))
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


FOLDER_CHECK_OUTPUT = (
    f"# Check: {SLUG}/{SLUG}.md\n"
    f"- WARNING: {SLUG}/review.md was written for an earlier round\n"
    f"- ERROR: move the proposal to {SLUG}/{SLUG}.md\n"
)


def test_minimal_stores_folder_paths_with_the_handle_replaced(workspace):
    """The folder is named by the slug, so its name in a path discloses the
    topic just as the file name does; role names carry nothing about the user
    and stay (skill-troubleshoot: Proposal handle redacted in every path)."""
    (workspace / "check-output.txt").write_text(FOLDER_CHECK_OUTPUT, encoding="utf-8")
    assert run(["--script-output", "check-output.txt"]) == 0
    bundle = workspace / "bug-report"
    stored = (bundle / "artifacts" / "check-output.txt").read_text(encoding="utf-8")
    assert "<proposal>/<proposal>.md" in stored
    assert "<proposal>/review.md" in stored
    assert SLUG_WORDS.search(stored) is None, "a word of the slug left the workspace"
    report = (bundle / "report.md").read_text(encoding="utf-8")
    assert "<proposal>/review.md" in report
    assert SLUG_WORDS.search(report) is None, "a word of the slug reached the report"


def test_a_folder_named_unlike_its_proposal_is_redacted_too(tmp_path, monkeypatch):
    """A rename that moved the folder but not the file leaves `<new>/<old>.md`;
    both names are slugs, and neither may leave the workspace."""
    folder = tmp_path / "orbital-loom-tension"
    folder.mkdir()
    (folder / f"{SLUG}.md").write_text(PROPOSAL, encoding="utf-8")
    (tmp_path / "check-output.txt").write_text(
        f"# Check: orbital-loom-tension/{SLUG}.md\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main([f"orbital-loom-tension/{SLUG}.md", "--script-output", "check-output.txt"]) == 0
    stored = (tmp_path / "bug-report" / "artifacts" / "check-output.txt").read_text(
        encoding="utf-8")
    assert "<proposal>/<proposal>.md" in stored
    assert re.search(r"orbital|loom|tension", stored) is None


def test_a_proposal_name_that_is_not_utf8_is_redacted_as_the_check_prints_it(
        tmp_path, monkeypatch):
    """The check prints a proposal name that is not valid UTF-8 with its
    undecodable bytes replaced (adopt-proposal-folders, task 6.6), so the
    readable part of the slug reaches the stored output in that form: the
    redaction must know it as well as the raw name, or `minimal` discloses the
    topic (skill-troubleshoot: Proposal handle redacted in every path)."""
    raw = b"sensorcaf\xe9"
    try:
        folder = tmp_path / os.fsdecode(raw)
        folder.mkdir()
        proposal = folder / os.fsdecode(raw + b".md")
        proposal.write_text(PROPOSAL, encoding="utf-8")
    except (OSError, UnicodeError):
        pytest.skip("this filesystem refuses a name that is not valid UTF-8")
    # a Log line naming the folder as its bytes stand: read with its
    # undecodable byte replaced, it is redacted in that form too
    (folder / "notes.md").write_bytes(b"## Log\n\n- 2026-10-15 drafted " + raw + b"/\n")
    report = run_check(proposal, root=tmp_path).stdout
    assert "sensorcaf\N{REPLACEMENT CHARACTER}" in report, "the check no longer prints it so"
    (tmp_path / "check-output.txt").write_text(report, encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main([os.path.relpath(proposal, tmp_path), "--script-output", "check-output.txt"]) == 0
    bundle = tmp_path / "bug-report"
    leaks = [path.relative_to(bundle).as_posix() for path in sorted(bundle.rglob("*"))
             if path.is_file() and b"sensorcaf" in path.read_bytes()]
    assert not leaks, f"the readable part of the slug left the workspace in {leaks}"
    stored = (bundle / "artifacts" / "check-output.txt").read_text(encoding="utf-8")
    assert stored.startswith("# Check: <proposal>.md")


# --------------------------------------------------------------------------
# notes-file log extraction
# --------------------------------------------------------------------------

def test_notes_log_extracts_only_the_log_section(workspace):
    """The Log excerpt comes from the notes file in the proposal's folder."""
    name, text = notes_log(proposal_in(workspace))
    assert name == "notes-log.md"
    assert "2026-08-03 four references added" in text
    assert "Chose prototype over SLR" not in text
    assert "wrong field" not in text, "the Log section ends at the next same-level heading"


LOG_NAMING_THE_PROPOSAL = f"""# Notes

## Decisions

- Chose prototype over SLR.

## Log

- 2026-10-14 renamed {SLUG}/ from the provisional handle; drafted {SLUG}/{SLUG}.md
- 2026-10-15 review written to {SLUG}/review.md
"""


@pytest.mark.parametrize("level", ["minimal", "structure"])
def test_the_stored_log_carries_no_word_of_the_slug_below_full(workspace, level):
    """A Log line names the proposal as the skills write it, by its folder
    and file; below `full` the stored excerpt replaces the handle as the
    stored script output does (skill-troubleshoot: Graded redaction with the
    most protective default)."""
    folder = proposal_in(workspace).parent
    (folder / "notes.md").write_text(LOG_NAMING_THE_PROPOSAL, encoding="utf-8")
    assert run(["--level", level]) == 0
    bundle = workspace / "bug-report"
    stored = (bundle / "artifacts" / "notes-log.md").read_text(encoding="utf-8")
    assert "drafted <proposal>/<proposal>.md" in stored
    assert "<proposal>/review.md" in stored
    leaks = [path.relative_to(bundle).as_posix() for path in sorted(bundle.rglob("*"))
             if path.is_file() and SLUG_WORDS.search(path.read_text(encoding="utf-8"))]
    assert not leaks, f"a word of the slug left the workspace in {leaks}"


def test_full_stores_the_log_as_written(workspace):
    """The most disclosing level carries the proposal text, its name included,
    so its Log excerpt is stored as the notes file holds it."""
    folder = proposal_in(workspace).parent
    (folder / "notes.md").write_text(LOG_NAMING_THE_PROPOSAL, encoding="utf-8")
    assert run(["--level", "full"]) == 0
    stored = (workspace / "bug-report" / "artifacts" / "notes-log.md").read_text(
        encoding="utf-8")
    assert f"drafted {SLUG}/{SLUG}.md" in stored
    assert "Chose prototype over SLR" not in stored, "only the Log section is stored"


NOTES_WITHOUT_LOG = """# Notes

## Topic

Fibre tension in orbital looms, measured on a prototype.

## Decisions

- Chose prototype over SLR.
"""


@pytest.mark.parametrize("level", ["minimal", "structure", "full"])
def test_a_notes_file_without_a_log_section_stores_nothing(workspace, level):
    """What a notes file holds besides its Log is the idea itself, which no
    level promises: without a Log section nothing of the file is stored, and
    the report says so, so the absence reads as a fact rather than a gap."""
    folder = proposal_in(workspace).parent
    (folder / "notes.md").write_text(NOTES_WITHOUT_LOG, encoding="utf-8")
    assert notes_log(proposal_in(workspace)) is None
    assert run(["--level", level]) == 0
    bundle = workspace / "bug-report"
    assert not (bundle / "artifacts" / "notes-log.md").exists()
    report = (bundle / "report.md").read_text(encoding="utf-8")
    assert ("[measured] notes file present as notes.md without a Log section; "
            "nothing of it stored") in report
    for path in bundle.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert "orbital looms" not in text, path
            assert "Chose prototype over SLR" not in text, path


def test_sibling_artifacts_inventoried_at_hash_level(workspace):
    """Supervise session: review file and feedback file appear with sizes and
    hashes under their role names, and none of their text (skill-troubleshoot
    spec: companion artifacts inventoried at hash level)."""
    feedback = "Verdict: idea stage. 1. Sharpen the question — proposal-ideate."
    folder = proposal_in(workspace).parent
    (folder / "review.md").write_text(
        "no viable thesis core\n1. secret finding text", encoding="utf-8")
    (folder / "feedback.md").write_text(feedback, encoding="utf-8")

    lines = sibling_artifacts(proposal_in(workspace))
    joined = "\n".join(lines)
    assert "review file present as review.md (" in joined
    assert "supervise feedback present as feedback.md (" in joined
    assert SLUG_WORDS.search(joined) is None
    assert "secret finding text" not in joined
    assert "Sharpen the question" not in joined
    assert joined.count("sha256:") == 2


def test_kept_and_old_style_names_are_no_role_files(workspace):
    """Role files are matched by their exact name: a kept file whose label
    merely contains a role is a kept file, and the flat layout's names are not
    read at all (design D3, D1)."""
    folder = proposal_in(workspace).parent
    (folder / "notes.md").unlink()
    for name in ("peer-review.md", "reading-notes.md", "supervisor-feedback.md",
                 f"{SLUG}.notes.md", f"{SLUG}-review.md", f"{SLUG}-feedback.md"):
        (folder / name).write_text("## Log\n\n- kept by hand\n", encoding="utf-8")
    assert sibling_artifacts(proposal_in(workspace)) == []
    assert notes_log(proposal_in(workspace)) is None


def test_sibling_artifacts_absent_in_student_workspace(workspace):
    assert sibling_artifacts(proposal_in(workspace)) == []
    assert sibling_artifacts(None) == []


def test_full_level_report_still_excludes_companion_text(workspace):
    (proposal_in(workspace).parent / "feedback.md").write_text(
        "Verdict: idea stage. Unique-feedback-phrase.", encoding="utf-8")
    assert run(["--level", "full"]) == 0
    report = (workspace / "bug-report" / "report.md").read_text(encoding="utf-8")
    assert "present as feedback.md (" in report
    assert "Unique-feedback-phrase" not in report


BUILD_SCRIPT = "# faculty-template-path-nobody-else-should-see\nprint('built')\n"


def test_workspace_build_definition_recorded(workspace):
    """Without this line a workspace-built document is indistinguishable from
    one the shipped pipeline produced, and the report reads as "works for me"."""
    (proposal_in(workspace).parent / "proposal-build.py").write_text(
        BUILD_SCRIPT, encoding="utf-8")
    joined = "\n".join(sibling_artifacts(proposal_in(workspace)))
    assert "proposal-build.py" in joined
    assert "sha256:" in joined
    assert "not built by the shipped pipeline" in joined
    assert "faculty-template-path-nobody-else-should-see" not in joined


def test_workspace_build_recipe_recorded_only_with_the_target(workspace):
    makefile = proposal_in(workspace).parent / "Makefile"
    makefile.write_text("all:\n\techo hi\n", encoding="utf-8")
    assert sibling_artifacts(proposal_in(workspace)) == []
    makefile.write_text("proposal-build:\n\tpandoc $(PROPOSAL_PATH)\n", encoding="utf-8")
    joined = "\n".join(sibling_artifacts(proposal_in(workspace)))
    assert "Makefile (target `proposal-build`)" in joined


def test_build_definition_at_the_workspace_root_is_not_publish_s(workspace):
    """publish looks only in the proposal's folder, so a definition at the root
    builds nothing and is not reported as the one that built the document."""
    (workspace / "proposal-build.py").write_text(BUILD_SCRIPT, encoding="utf-8")
    assert sibling_artifacts(proposal_in(workspace)) == []


def test_full_level_report_excludes_build_definition_content(workspace):
    (proposal_in(workspace).parent / "proposal-build.py").write_text(
        BUILD_SCRIPT, encoding="utf-8")
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


def test_companion_names_match_the_checks_role_table():
    """The collector restates check.py's role names, as it restates publish's
    build constants: the files it inventories are the ones the check calls
    the notes file, the review and the supervisor feedback."""
    import check

    assert check.ROLE_NAMES[check.NOTES] == collect.NOTES_FILE
    assert [name for _label, name in collect.COMPANION_FILES] == [
        check.ROLE_NAMES[check.REVIEW], check.ROLE_NAMES[check.FEEDBACK]]


def test_notes_log_absent_is_not_an_error(tmp_path):
    assert notes_log(write_proposal(tmp_path, "solo", PROPOSAL)) is None


# --------------------------------------------------------------------------
# model resolution against the vendored verdicts
# --------------------------------------------------------------------------

def test_vendored_verdicts_distinguish_untested_from_failing():
    data = json.loads((SKILL / "references" / "model-support.json").read_text(encoding="utf-8"))
    seen = {c for m in data["models"].values() for c in m["skills"].values()}
    assert "untested" in seen, "no untested cell present — the distinction is untested itself"
    assert seen <= {"solid", "flaky", "fail", "untested"}, f"unexpected classification in {seen}"
    assert "untested" in data["statuses"]


SHIPPED_SUPPORT = SKILL / "references" / "model-support.json"
PINS = Path(__file__).parent / "data" / "pinned_sentences"

# the roster as track-model-currency bumps it, plus two keys kept only as
# guards: the 5.0 opus for the version guard, deepseek-v4 for the colon-form
# revision guard. Synthetic, so a roster bump in the shipped file breaks nothing.
SYNTHETIC_KEYS = (
    "anthropic/claude-haiku-4.5",
    "anthropic/claude-sonnet-5.5",
    "anthropic/claude-opus-5.5",
    "anthropic/claude-opus-5",
    "openai/gpt-6-luna",
    "deepseek/deepseek-v4",
)


def write_support(path: Path, keys) -> Path:
    """A model-support.json shaped like the shipped one, holding `keys`."""
    data = {
        "statuses": {"solid": "every measured epoch passed", "fail": "every measured epoch failed"},
        "models": {
            key: {"verdict": "supported", "skills": {"proposal-write": "solid"}} for key in keys
        },
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture
def support_file(tmp_path):
    return write_support(tmp_path / "model-support.json", SYNTHETIC_KEYS)


def claude_code_spelling(key: str) -> str:
    """How Claude Code states an `anthropic/` roster key: no vendor, dashed version."""
    return re.sub(r"(?<=\d)\.(?=\d)", "-", key.removeprefix("anthropic/"))


@pytest.mark.parametrize("reported", [
    "anthropic/claude-opus-5.5",
    "openrouter/anthropic/claude-opus-5.5",
    "claude-opus-5.5",
])
def test_resolve_model_accepts_the_key_a_routing_prefix_and_the_bare_name(support_file, reported):
    key, record = resolve_model(reported, support_file)
    assert key == "anthropic/claude-opus-5.5"
    assert "verdict" in record


@pytest.mark.parametrize(("reported", "expected"), [
    ("claude-haiku-4-5-20251001", "anthropic/claude-haiku-4.5"),
    ("claude-haiku-4-5", "anthropic/claude-haiku-4.5"),
    (" Claude-Haiku-4-5 ", "anthropic/claude-haiku-4.5"),
    ("claude-sonnet-5-5", "anthropic/claude-sonnet-5.5"),
    ("claude-opus-5-5", "anthropic/claude-opus-5.5"),
])
def test_resolve_model_matches_claude_code_spellings(support_file, reported, expected):
    """Claude Code dashes the version digits and may append a date stamp."""
    assert resolve_model(reported, support_file)[0] == expected


@pytest.mark.parametrize(("reported", "expected"), [
    ("us.anthropic.claude-haiku-4-5-20251001-v1:0", "anthropic/claude-haiku-4.5"),
    ("global.anthropic.claude-haiku-4-5-20251001-v1:0", "anthropic/claude-haiku-4.5"),
    ("us-gov.anthropic.claude-haiku-4-5-20251001-v1:0", "anthropic/claude-haiku-4.5"),
    ("claude-haiku-4-5@20251001", "anthropic/claude-haiku-4.5"),
    ("claude-sonnet-5-5[1m]", "anthropic/claude-sonnet-5.5"),
    ("claude-sonnet-5-5 [1m]", "anthropic/claude-sonnet-5.5"),
    ("claude-haiku-4-5-20251001 [1m]", "anthropic/claude-haiku-4.5"),
    # a non-Anthropic vendor wraps its models the same way on a cloud
    ("openai.gpt-6-luna-1:0", "openai/gpt-6-luna"),
    ("us.openai.gpt-6-luna-v1:0", "openai/gpt-6-luna"),
    ("gpt-6-luna-2026-03-01", "openai/gpt-6-luna"),
])
def test_resolve_model_matches_cloud_and_variant_spellings(support_file, reported, expected):
    assert resolve_model(reported, support_file)[0] == expected


@pytest.mark.parametrize(("spelling", "kept"), [
    ("qwen3.8-max", "qwen3.8-max"),          # a first segment holding a digit is the name
    ("large-2411", "large-2411"),            # a year-month suffix may be a version
])
def test_wrappings_are_stripped_no_wider_than_a_host_spells_them(spelling, kept):
    assert normalize_model_id(spelling) == kept


def test_resolve_model_never_takes_the_verdict_of_another_version(tmp_path):
    """5.5 is not 5: a newer version than any recorded stays unevaluated."""
    only_five = write_support(tmp_path / "only-five.json", ["anthropic/claude-opus-5"])
    assert resolve_model("claude-opus-5-5", only_five) == (None, {})


def test_resolve_model_does_not_match_a_version_prefix(support_file):
    assert resolve_model("claude-haiku-4", support_file) == (None, {})


def test_only_the_colon_form_revision_is_dropped(support_file):
    """A bare `-vN` is a version, not a cloud revision (design D3)."""
    assert normalize_model_id("deepseek-v4") != normalize_model_id("deepseek-v3")
    assert resolve_model("deepseek-v3", support_file) == (None, {})


@pytest.mark.parametrize("alias", ["haiku", "sonnet", "opus"])
def test_an_alias_names_no_version_and_resolves_to_nothing(support_file, alias):
    assert resolve_model(alias, support_file) == (None, {})


def test_two_keys_with_one_spelling_resolve_to_nothing(tmp_path):
    """Choosing either would report a neighbouring entry's verdict as the user's."""
    both = write_support(
        tmp_path / "both.json", ["anthropic/claude-haiku-4.5", "bedrock/claude-haiku-4-5"]
    )
    assert resolve_model("claude-haiku-4-5-20251001", both) == (None, {})


def test_a_dated_snapshot_shares_its_version_s_verdict_and_nothing_more(tmp_path):
    """The accepted snapshot assumption (clarify-troubleshoot-model-subject,
    design D4): a full date is ignored in either direction, two dated snapshots
    of one version collide, and a short snapshot token stays part of the name."""
    dated = write_support(tmp_path / "dated.json", ["lab/example-4.5-20251001"])
    assert resolve_model("example-4-5", dated)[0] == "lab/example-4.5-20251001"
    two = write_support(
        tmp_path / "two.json", ["lab/example-4.5-20250101", "lab/example-4.5-20251001"]
    )
    assert resolve_model("example-4-5", two) == (None, {})
    token = write_support(tmp_path / "token.json", ["lab/example-pro-0813"])
    assert resolve_model("example-pro-0813", token)[0] == "lab/example-pro-0813"
    assert resolve_model("example-pro", token) == (None, {})


def test_resolve_model_returns_nothing_for_an_unknown_model():
    """Absence must not resolve to some neighbouring model's verdict."""
    key, record = resolve_model("some-model-we-never-measured")
    assert key is None
    assert record == {}


def test_every_shipped_key_resolves_to_itself_without_collisions():
    """Holds under any roster: the same normalisation runs on both sides, so the
    only failure is two keys sharing a spelling (design D4)."""
    keys = json.loads(SHIPPED_SUPPORT.read_text(encoding="utf-8"))["models"]
    spellings = [normalize_model_id(key) for key in keys]
    assert len(set(spellings)) == len(spellings), f"keys collide after normalisation: {spellings}"
    for key in keys:
        assert resolve_model(key)[0] == key


def test_every_shipped_anthropic_key_resolves_from_its_claude_code_spelling():
    keys = [k for k in json.loads(SHIPPED_SUPPORT.read_text(encoding="utf-8"))["models"]
            if k.startswith("anthropic/")]
    assert keys, "no anthropic/ key shipped — the property is vacuous"
    for key in keys:
        bare = claude_code_spelling(key)
        assert resolve_model(bare)[0] == key, bare
        assert resolve_model(bare + "-20251001")[0] == key, bare + "-20251001"


def test_the_pinned_rung_one_example_resolves_through_resolve_model(tmp_path):
    """Rung 1's prose is the runtime path and resolve_model its executable
    statement (design D1): the worked example the agent reads must resolve under
    the code's rule. Rewording the sentence breaks its pin; changing the rule so
    the example no longer resolves breaks this."""
    pin = PINS / "proposal-troubleshoot--model-match.txt"
    reported, key = re.findall(r"`([^`]+)`", pin.read_text(encoding="utf-8"))[:2]
    only_key = write_support(tmp_path / "only-key.json", [key])
    assert resolve_model(reported, only_key)[0] == key


def test_every_wrapping_the_rung_one_rule_names_is_stripped():
    """The pinned rule sentence lists wrappings by example; each one, put around a
    bare spelling, must normalise away. A prose example the code does not strip
    would have the agent match where resolve_model does not."""
    rule = (PINS / "proposal-troubleshoot--model-rule.txt").read_text(encoding="utf-8")
    wrappings = re.findall(r"`([^`]+)`", rule)
    assert len(wrappings) >= 5, wrappings
    bare = "example-4-5"
    for wrapping in wrappings:
        spelled = wrapping + bare if wrapping.endswith((".", "/")) else bare + wrapping
        assert normalize_model_id(spelled) == normalize_model_id(bare), spelled


def test_resolve_model_reports_a_known_failing_skill():
    """The measured fact troubleshoot_model_rung relies on, resolved from the
    spelling its prompt uses — so the eval's expectation and the data move together."""
    _, record = resolve_model("claude-haiku-4-5-20251001")
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
    folder_before = {p.name for p in proposal_in(workspace).parent.iterdir()}
    assert run([]) == 0
    bundle = workspace / "bug-report"
    assert (bundle / "report.md").is_file()
    assert (bundle / "hashes.txt").is_file()
    after = {p.name for p in workspace.iterdir()}
    assert after - before == {"bug-report"}, "the collector wrote outside its bundle"
    assert {p.name for p in proposal_in(workspace).parent.iterdir()} == folder_before


def test_bundle_lands_in_the_working_directory_not_the_proposal_folder(workspace):
    """The report directory stays at the workspace root, where a user looks for
    it and where `bug-report` is a reserved folder name (skill-troubleshoot:
    Report directory placement)."""
    assert run([]) == 0
    assert (workspace / "bug-report" / "report.md").is_file()
    assert not (proposal_in(workspace).parent / "bug-report").exists()


def test_the_proposal_is_never_modified(workspace):
    """A read-only skill may end in this offer; the file it examined must be
    untouched afterwards, digest and all."""
    proposal = proposal_in(workspace)
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


# --------------------------------------------------------------------------
# the reproduction seed: a workspace of its own
# --------------------------------------------------------------------------

def reproduction_seed() -> tuple[PurePosixPath, PurePosixPath]:
    """The reduced file and the directory its command runs from, as the
    skill's "The reproduction seed" section names them."""
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^## The reproduction seed\n(.*?)(?=^## )", text,
                      re.MULTILINE | re.DOTALL)
    assert match, "SKILL.md lost its reproduction-seed section"
    seeds = set(re.findall(r"`(bug-report/repro/[^`]*\.md)`", match.group(1)))
    assert len(seeds) == 1, f"the section names {sorted(seeds)} as the reduced file"
    root = re.search(r"run from `(bug-report/[^`]*?)/?`", match.group(1))
    assert root, "the section does not say which directory the command runs from"
    return PurePosixPath(seeds.pop()), PurePosixPath(root.group(1))


def test_the_reproduction_is_a_workspace_the_check_accepts(tmp_path):
    """The reduced file obeys the corpus's fixture rules (skill-troubleshoot:
    Reproduction seed only where reduction is possible), which put a proposal
    in a folder named by its slug; run as its command says, the check judges
    the defect, never the reproduction's own placement."""
    seed, root = reproduction_seed()
    relative = seed.relative_to(root)
    workspace = tmp_path / root
    proposal = workspace / relative
    proposal.parent.mkdir(parents=True)
    proposal.write_text(CLEAN_DRAFT, encoding="utf-8")
    (workspace / "command.txt").write_text(f"python3 check.py {relative}\n", encoding="utf-8")
    (tmp_path / "bug-report" / "report.md").write_text("# Bug report\n", encoding="utf-8")
    result = run_check(Path(relative), "--json", root=workspace)
    findings = json.loads(result.stdout)["findings"]
    placement = [f["rule"] for f in findings if f["rule"] in {
        "proposal-misplaced", "proposal-folder-mismatch", "companion-orphaned",
        "build-definition-unused"}]
    assert not placement, f"the reproduction itself draws {placement}"
    assert result.returncode == 0


def test_the_report_points_at_the_reproduction_the_skill_writes(workspace):
    """The report's reproduction line and the skill's prose name one layout,
    relative to the bundle the maintainer receives."""
    seed, root = reproduction_seed()
    assert run([]) == 0
    report = (workspace / "bug-report" / "report.md").read_text(encoding="utf-8")
    bundle_root = PurePosixPath("bug-report")
    assert f"`{seed.relative_to(bundle_root).as_posix()}`" in report
    assert f"run from `{root.relative_to(bundle_root).as_posix()}/`" in report


# --------------------------------------------------------------------------
# install route — installer record, plugin installs, skills CLI lock
# --------------------------------------------------------------------------

SHA = "0123456789abcdef0123456789abcdef01234567"


@pytest.fixture
def home(tmp_path, monkeypatch):
    """A fake home holding nothing yet, and a workspace outside it."""
    home = tmp_path / "home"
    home.mkdir()
    fake_home(monkeypatch, home)
    ws = tmp_path / "ws"
    ws.mkdir()
    monkeypatch.chdir(ws)
    return home


def plant_skill(root: Path, name: str = "proposal-check") -> None:
    (root / name).mkdir(parents=True, exist_ok=True)
    (root / name / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")


def plant_record(root: Path, **overrides) -> None:
    plant_skill(root)
    record = {"package": "thesis-proposal", "installer": 1, "revision": SHA,
              "installed_at": "2026-10-03T12:00:00+00:00", "scope": "all",
              "source": "default-branch", "directories": ["~/.agents/skills"],
              "skills": ["proposal-check"], **overrides}
    (root / collect.RECORD_NAME).write_text(json.dumps(record), encoding="utf-8")


def test_installer_record_is_reported_home_relative(home):
    plant_record(home / ".agents/skills")
    lines = collect.install_lines(Path.cwd(), None)
    assert (f"[measured] install record in ~/.agents/skills: revision {SHA}, scope all, "
            "source default-branch, installed 2026-10-03T12:00:00+00:00") in lines
    assert "[measured] install route: installer" in lines
    assert str(home) not in "\n".join(lines)


def test_record_values_of_an_unknown_shape_are_never_repeated(home):
    plant_record(home / ".claude/skills", revision="see https://evil.example/x",
                 scope="/home/erika", source="C:\\Users\\Erika", installed_at="yesterday")
    text = "\n".join(collect.install_lines(Path.cwd(), None))
    assert "revision unreadable, scope unreadable, source unreadable, installed unreadable" in text
    assert "evil" not in text
    assert "erika" not in text.lower()


def test_unparseable_record_is_reported_not_raised(home):
    root = home / ".claude/skills"
    plant_skill(root)
    (root / collect.RECORD_NAME).write_text("{not json", encoding="utf-8")
    lines = collect.install_lines(Path.cwd(), None)
    assert "[measured] install record in ~/.claude/skills is unreadable" in lines


@pytest.mark.usefixtures("home")
def test_workspace_record_is_reported_workspace_relative():
    plant_record(Path.cwd() / ".claude/skills", scope="folder")
    lines = collect.install_lines(Path.cwd(), None)
    assert any(ln.startswith("[measured] install record in ./.claude/skills:") for ln in lines)


def test_plugin_install_found_and_orphaned_versions_ignored(home):
    cache = home / ".claude/plugins/cache/thesis-proposal/thesis-proposal"
    plant_skill(cache / "old123")
    (cache / "old123" / collect.ORPHANED_MARKER).write_text("1", encoding="utf-8")
    assert "[measured] install route: unknown (hand-copied or installed by other means)" in \
        collect.install_lines(Path.cwd(), None)
    plant_skill(cache / "new456")
    lines = collect.install_lines(Path.cwd(), None)
    assert "[measured] plugin install found for Claude" in lines
    assert "[measured] install route: plugin" in lines
    roots = collect.skill_roots(Path.cwd())
    assert (cache / "new456").resolve() in roots
    assert (cache / "old123").resolve() not in roots


def test_plugin_keeping_the_repository_layout_is_found(home):
    plant_skill(home / ".codex/plugins/cache/thesis-proposal/thesis-proposal/abc/skills")
    assert "[measured] plugin install found for ChatGPT/Codex" in \
        collect.install_lines(Path.cwd(), None)


def test_two_routes_at_once_are_flagged(home):
    plant_record(home / ".claude/skills")
    plant_skill(home / ".copilot/installed-plugins/thesis-proposal/thesis-proposal")
    lines = collect.install_lines(Path.cwd(), None)
    assert "[measured] install route: installer + plugin" in lines
    assert any("load every skill twice" in ln for ln in lines)


def test_record_values_of_the_wrong_type_are_unreadable_not_a_crash(home):
    plant_record(home / ".agents/skills", scope=["all"], source={"a": 1}, revision=7)
    text = "\n".join(collect.install_lines(Path.cwd(), None))
    assert "revision unreadable, scope unreadable, source unreadable" in text


def test_a_workspace_above_home_never_shows_the_user_name(home):
    root = home / ".agents/skills"
    plant_record(root)
    assert collect.shown_root(root.resolve(), home.parent) == "~/.agents/skills"
    assert collect.shown_root(root.resolve(), home) == "~/.agents/skills"


def test_a_claude_plugin_button_install_is_found(home):
    plant_skill(home / collect.CLAUDE_SYNCED / "acct_org" / "thesis-proposal" / "abc" / "skills")
    lines = collect.install_lines(Path.cwd(), None)
    assert "[measured] plugin install found for Claude" in lines


def test_a_vs_code_plugin_clone_is_found(home):
    plant_skill(home / ".config/Code" / collect.VSCODE_PLUGIN / "skills")
    assert "[measured] plugin install found for VS Code" in collect.install_lines(Path.cwd(), None)


def test_a_global_terminal_install_is_the_cli_route(home):
    (home / ".agents").mkdir()
    (home / ".agents/.skill-lock.json").write_text('{"skills": {}}', encoding="utf-8")
    lines = collect.install_lines(Path.cwd(), None)
    assert "[measured] install route: CLI" in lines
    assert any("global lock present" in ln for ln in lines)


@pytest.mark.usefixtures("home")
def test_cli_lock_still_reported():
    lock = Path.cwd() / "skills-lock.json"
    lock.write_text("{}", encoding="utf-8")
    lines = collect.install_lines(Path.cwd(), lock)
    assert "[measured] install route: CLI" in lines


def test_report_carries_the_route_section(home):
    write_proposal(Path.cwd(), "p", PROPOSAL)
    plant_record(home / ".agents/skills")
    assert main(["p/p.md"]) == 0
    report = (Path.cwd() / "bug-report" / "report.md").read_text(encoding="utf-8")
    assert "[measured] install route: installer" in report
    assert str(home) not in report


def test_locations_match_the_repository_installer():
    """The collector restates the installer's names and directories (a skill
    never imports from outside its own folder); this keeps the two in step."""
    assert collect.RECORD_NAME == install.RECORD_NAME
    assert collect.PACKAGE == install.PACKAGE
    installer_dirs = {*install.SHARED_DIRS,
                      *(h.user_dir for h in install.HOST_DIRS),
                      *(h.folder_dir for h in install.HOST_DIRS if h.folder_dir)}
    assert installer_dirs <= set(collect.COPY_DIRS)
    assert {"default-branch", "url", "zip", "directory"} == collect.RECORD_SOURCES
    plugin_dirs = {rel for _, rel in collect.PLUGIN_CACHES}
    assert {rel for _, rel in install.PLUGIN_FOLDERS} <= plugin_dirs
    assert collect.CLAUDE_SYNCED == install.CLAUDE_SYNCED
    assert collect.VSCODE_PLUGIN == install.VSCODE_PLUGIN
    assert collect.NATIVE_DIRS == install.NATIVE_DIRS


def test_a_copy_in_an_apps_own_folder_is_hashed_and_named(home):
    """A hand copy in OpenCode's folder beside an installer install: its files are
    hashed, and the report names the folder home-relative (design D14)."""
    plant_record(home / ".agents/skills")
    opencode = home / ".config/opencode/skills"
    plant_skill(opencode)
    (opencode / "proposal-check" / "SKILL.md").write_text("hand edited\n", encoding="utf-8")
    lines = collect.install_lines(Path.cwd(), None)
    assert ("[measured] skill copies in ~/.config/opencode/skills (OpenCode's own skill "
            "folder), which may shadow the installed skills: proposal-check") in lines
    assert str(home) not in "\n".join(lines)
    assert opencode.resolve() / "proposal-check" in collect.installed_skills(Path.cwd())
    hashes, _ = collect.hash_lines(Path.cwd())
    blob = collect.git_blob_hash(b"hand edited\n")
    assert any(ln.startswith("proposal-check/SKILL.md ") and blob in ln for ln in hashes)


def test_a_collector_run_from_the_shadowing_copy_still_names_it(home, monkeypatch):
    """The student hand-copied the skills into OpenCode's folder, so OpenCode
    runs this collector from there: that folder is the shadowing copy, not the
    installed one, and the line naming it must still appear (design D14)."""
    plant_record(home / ".agents/skills")
    opencode = home / ".config/opencode/skills"
    plant_skill(opencode)
    plant_skill(opencode, "proposal-troubleshoot")
    monkeypatch.setattr(collect, "HERE", opencode / "proposal-troubleshoot" / "scripts")
    lines = collect.install_lines(Path.cwd(), None)
    assert ("[measured] skill copies in ~/.config/opencode/skills (OpenCode's own skill "
            "folder), which may shadow the installed skills: proposal-check, "
            "proposal-troubleshoot") in lines


@pytest.mark.usefixtures("home")
def test_a_copy_in_the_workspace_opencode_folder_is_named_workspace_relative():
    plant_skill(Path.cwd() / ".opencode/skill")
    lines = collect.install_lines(Path.cwd(), None)
    assert any(ln.startswith("[measured] skill copies in ./.opencode/skill (OpenCode")
               for ln in lines)


def test_a_folder_holding_only_unshipped_or_incomplete_entries_is_not_named(home):
    plant_skill(home / ".cursor/skills", "proposal-not-shipped")
    (home / ".cursor/skills/proposal-check").mkdir()
    assert not any(".cursor" in ln for ln in collect.install_lines(Path.cwd(), None))


@pytest.mark.skipif(os.name == "nt", reason="symlink creation needs privileges")
def test_a_link_from_an_apps_folder_into_the_installed_copy_is_hashed_once(home):
    installed = home / ".agents/skills"
    plant_record(installed)
    (home / ".codex/skills").mkdir(parents=True)
    (home / ".codex/skills/proposal-check").symlink_to(installed / "proposal-check",
                                                         target_is_directory=True)
    lines = collect.install_lines(Path.cwd(), None)
    assert not any(".codex" in ln for ln in lines), "a link into the installed copy is no copy"
    found = [p for p in collect.installed_skills(Path.cwd()) if p.name == "proposal-check"]
    assert (installed / "proposal-check").resolve() in found
    assert len([p for p in found if p.is_relative_to(home)]) == 1, "hashed once"
