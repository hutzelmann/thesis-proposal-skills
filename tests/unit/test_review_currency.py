"""L0: the review-currency warning (skill-check spec: review currency warning).

A review records the research questions it judged; the check compares that
record with the questions the proposal declares now. Both sides go through one
extractor and one normalizer, so "what one research question is" has a single
definition — the count rule uses the same extractor.
"""

import json
from functools import partial
from pathlib import Path

import check
import pytest
from helpers import REPO, fixture_proposal, review_with_record, run_check, write_proposal

STRUCTURE = json.loads((REPO / "shared" / "structure.json").read_text(encoding="utf-8"))
CLEAN = fixture_proposal("f00-clean-en").read_text(encoding="utf-8")
QUESTIONS = [
    "How accurately can neural networks classify code changes into review-relevant categories?",
    "Which code features are most predictive of issues that human reviewers identify?",
    "How does model performance vary across different programming languages and project domains?",
]
DROPPED = "To what degree does the classifier reduce review time per pull request?"
REVIEW_BODY = (
    "**Verdict: ready** — no proposal blocker stands.\n\n"
    "## Proposal blockers\n\nNone.\n\n"
    "## Clarify early in the thesis\n\nNone.\n\n"
    "## Optional refinements\n\nNone.\n"
)
RULE = "review-questions-changed"

# Code points rather than literal characters: a hyphen variant or a no-break
# space cannot be told from its plain form on screen.
NBSP, LIGATURE_FI, FULLWIDTH_QUESTION = chr(0x00A0), chr(0xFB01), chr(0xFF1F)
LEFT_DOUBLE, RIGHT_DOUBLE, EN_DASH = chr(0x201C), chr(0x201D), chr(0x2013)
FOLDED = [
    *((code_point, "'") for code_point in (0x2018, 0x2019, 0x201A, 0x201B)),
    *((code_point, '"') for code_point in (0x201C, 0x201D, 0x201E, 0x201F)),
    *((code_point, "-") for code_point in (0x2010, 0x2011, 0x2013, 0x2014, 0x2212)),
]
# invisible format characters (general category Cf): soft hyphen, zero-width
# space, word joiner, zero-width no-break space (byte-order mark)
SOFT_HYPHEN, ZERO_WIDTH_SPACE = chr(0x00AD), chr(0x200B)
FORMAT = [0x00AD, 0x200B, 0x2060, 0xFEFF]


def items(text: str, *, bullets: bool = False) -> list[str]:
    """Extracted items, normalized, so a test states the questions it expects."""
    return [check.normalize_question(item) for item in check.list_items(text, bullets=bullets)]


# ---------- the shared extractor ----------------------------------------------


def test_one_line_items_are_extracted_in_order():
    assert items("1. Which A?\n2. Which B?\n3. Which C?\n") == ["Which A?", "Which B?", "Which C?"]


def test_an_indented_continuation_line_joins_its_item():
    assert items("1. Which A,\n   wrapped onto a second line?\n2. Which B?\n") == [
        "Which A, wrapped onto a second line?", "Which B?"]


def test_an_unindented_lazy_continuation_joins_its_item():
    assert items("1. Which A,\nwrapped lazily?\n2. Which B?\n") == [
        "Which A, wrapped lazily?", "Which B?"]


def test_a_nested_sub_list_stays_inside_its_parent_on_the_proposal_side():
    text = ("1. Which A?\n2. Which B, namely:\n"
            "   - in setting one\n   - in setting two\n3. Which C?\n")
    assert items(text) == [
        "Which A?", "Which B, namely: - in setting one - in setting two", "Which C?"]


def test_a_nested_sub_list_stays_inside_its_parent_on_the_record_side():
    text = "- Which A?\n- Which B, namely:\n  - in setting one\n  - in setting two\n- Which C?\n"
    assert items(text, bullets=True) == [
        "Which A?", "Which B, namely: - in setting one - in setting two", "Which C?"]


def test_an_item_ends_at_a_blank_line():
    assert items("1. Which A?\n\nProse after the list.\n") == ["Which A?"]


def test_both_ordered_marker_styles_start_an_item():
    assert items("1) Which A?\n2. Which B?\n") == ["Which A?", "Which B?"]


def test_bullet_markers_start_an_item_on_the_record_side_only():
    text = "- Which A?\n* Which B?\n+ Which C?\n"
    assert items(text) == []
    assert items(text, bullets=True) == ["Which A?", "Which B?", "Which C?"]


def test_an_indented_marker_never_starts_an_item():
    assert items("  1. Which A?\n  2. Which B?\n") == []
    assert items("1. Which A?\n   2. a nested step\n") == ["Which A? 2. a nested step"]


def test_a_heading_ends_an_item():
    assert items("1. Which A?\n### Next part\n") == ["Which A?"]


# ---------- normalization ---------------------------------------------------


def test_normalization_absorbs_whitespace_and_compatibility_forms():
    typeset = f"Which{NBSP}{LIGATURE_FI}le  sizes\n   matter{FULLWIDTH_QUESTION}"
    assert check.normalize_question(typeset) == "Which file sizes matter?"


@pytest.mark.parametrize(("code_point", "plain"), FOLDED,
                         ids=[f"U+{code_point:04X}" for code_point, _ in FOLDED])
def test_normalization_folds_quote_and_dash_variants(code_point, plain):
    assert check.normalize_question(f"a planner{chr(code_point)}executor setup") == (
        f"a planner{plain}executor setup")


@pytest.mark.parametrize("code_point", FORMAT, ids=[f"U+{code_point:04X}" for code_point in FORMAT])
def test_normalization_removes_format_characters(code_point):
    """Word's optional hyphens and zero-width marks survive a pandoc or PDF
    import invisibly; a record copied without them asks the same question."""
    assert check.normalize_question(f"a plan{chr(code_point)}ner setup") == "a planner setup"
    assert check.normalize_question(f"a {chr(code_point)} planner") == "a planner"


def test_normalization_keeps_letter_case_and_other_punctuation():
    assert check.normalize_question("Which A?") != check.normalize_question("which A?")
    assert check.normalize_question("Which A?") != check.normalize_question("Which A.")
    assert check.normalize_question("A (B)") != check.normalize_question("A [B]")


# ---------- the review comparison ---------------------------------------------


# a review closing on a record of the questions it is given
record = partial(review_with_record, REVIEW_BODY)


def stage(tmp_path: Path, review: str | bytes | None, proposal: str = CLEAN,
          stem: str = "ml-code-review") -> Path:
    """A proposal in its folder, with `review` as its review file when one is
    given."""
    path = write_proposal(tmp_path, stem, proposal)
    target = check.review_path(path)
    if isinstance(review, bytes):
        target.write_bytes(review)
    elif review is not None:
        target.write_text(review, encoding="utf-8")
    return path


def currency(tmp_path: Path, review: str | bytes | None,
             proposal: str = CLEAN) -> list[check.Finding]:
    findings = check.check_findings(stage(tmp_path, review, proposal), STRUCTURE, {})
    return [f for f in findings if f.rule == RULE]


def test_the_review_path_is_the_role_file_in_the_proposals_folder():
    assert check.review_path(Path("topic/topic.md")) == Path("topic/review.md")


def test_the_review_path_follows_the_family_role_table(monkeypatch):
    """The name comes from the `review` entry of the family's role table
    (proposal-file-format: Proposal family under one handle), never from a
    second spelling, so a change to that table moves the review with it."""
    monkeypatch.setattr(check, "ROLE_NAMES", {**check.ROLE_NAMES, check.REVIEW: "assessment.md"})
    assert check.review_path(Path("topic/topic.md")) == Path("topic/assessment.md")


def test_a_proposal_named_outside_the_slug_shape_still_has_its_review_read(tmp_path):
    """The review path follows the folder whatever the file's name: a stem with
    a space or capitals has a review too, so deriving the path from a family
    vocabulary must not narrow it to slug-shaped names."""
    proposal = stage(tmp_path, record([*QUESTIONS, DROPPED]), stem="My Proposal")
    [found] = [f for f in check.check_findings(proposal, STRUCTURE, {}) if f.rule == RULE]
    assert "`review.md`" in found.message
    assert "(RQ4 removed)" in found.message


def test_question_changes_are_position_and_kind_pairs():
    """Structured data, so no consumer parses the warning's text for them."""
    assert check.question_changes(["A?", "B?", "C?", "D?"], ["A?", "b?", "C?"]) == [
        (2, "changed"), (4, "removed")]
    assert check.question_changes(["A?"], ["A?", "B?"]) == [(2, "added")]
    assert check.question_changes(["A?"], ["A?"]) == []


def test_a_removed_question_is_named_by_position(tmp_path):
    review = record([*QUESTIONS, DROPPED])
    proposal = stage(tmp_path, review)
    findings = check.check_findings(proposal, STRUCTURE, {})
    assert findings[-1].rule == RULE, "the warning comes after every rule finding"
    [found] = [f for f in findings if f.rule == RULE]
    assert found.level == "warning"
    assert "`review.md`" in found.message
    assert "(RQ4 removed)" in found.message
    assert "the review may describe an earlier version of the proposal" in found.message
    assert found.message.endswith(
        "; a fresh review replaces it, so leave the review file as it is"), found.message
    assert DROPPED not in found.message
    assert check.review_path(proposal).read_text(encoding="utf-8") == review


def test_a_reworded_question_is_named_without_quoting_either_version(tmp_path):
    reworded = QUESTIONS[1].replace("most predictive", "most indicative")
    [found] = currency(tmp_path, record([QUESTIONS[0], reworded, QUESTIONS[2]]))
    assert "(RQ2 changed)" in found.message
    for wording in (QUESTIONS[1], reworded, "predictive", "indicative"):
        assert wording not in found.message


def test_an_added_question_is_named_by_position(tmp_path):
    [found] = currency(tmp_path, record(QUESTIONS[:2]))
    assert "(RQ3 added)" in found.message


def test_every_differing_position_is_named(tmp_path):
    [found] = currency(tmp_path, record([QUESTIONS[0], QUESTIONS[2]]))
    assert "(RQ2 changed, RQ3 added)" in found.message


def test_a_change_of_letter_case_counts(tmp_path):
    [found] = currency(tmp_path, record([QUESTIONS[0].lower(), *QUESTIONS[1:]]))
    assert "(RQ1 changed)" in found.message


def test_the_same_questions_in_another_layout_are_current(tmp_path):
    wrapped = QUESTIONS[0].replace(" classify ", "\n  classify ")
    no_break = QUESTIONS[1].replace(" ", NBSP)
    assert currency(tmp_path, record([wrapped, no_break, QUESTIONS[2]], marker="-")) == []


def test_quote_and_dash_variants_are_current(tmp_path):
    typeset = (QUESTIONS[0].replace("neural", f"{LEFT_DOUBLE}neural{RIGHT_DOUBLE}")
               .replace("review-relevant", f"review{EN_DASH}relevant"))
    plain = QUESTIONS[0].replace("neural", '"neural"')
    assert typeset != plain
    proposal = CLEAN.replace(QUESTIONS[0], typeset)
    assert currency(tmp_path, record([plain, *QUESTIONS[1:]]), proposal) == []


def test_format_characters_are_current(tmp_path):
    """A soft hyphen in the proposal and a zero-width space in the record, on
    either side of an otherwise verbatim copy, change no question."""
    hyphenated = QUESTIONS[0].replace("classify", f"clas{SOFT_HYPHEN}sify")
    spaced = QUESTIONS[1].replace("predictive", f"predic{ZERO_WIDTH_SPACE}tive")
    proposal = CLEAN.replace(QUESTIONS[0], hyphenated)
    assert currency(tmp_path, record([QUESTIONS[0], spaced, QUESTIONS[2]]), proposal) == []


def test_a_nested_item_copied_with_its_question_is_current(tmp_path):
    nested = QUESTIONS[1] + "\n   - in Python projects\n   - in Java projects"
    proposal = CLEAN.replace(QUESTIONS[1], nested)
    assert currency(tmp_path, record([QUESTIONS[0], nested, QUESTIONS[2]]), proposal) == []
    body, meta = check.split_proposal(proposal)
    ctx = check.build_context(body, meta, STRUCTURE, {})
    assert len(check.research_questions(ctx)) == 3
    assert "research-question-unreferenced" not in {
        f.rule for f in check.rule_research_questions(ctx)}


@pytest.mark.parametrize("title", [
    "## Begutachtete Forschungsfragen",
    "### research questions reviewed",
    "# BEGUTACHTETE FORSCHUNGSFRAGEN",
])
def test_either_title_at_any_level_and_case_is_read(tmp_path, title):
    assert currency(tmp_path, record(QUESTIONS, title=title)) == []
    [found] = currency(tmp_path, record(QUESTIONS[:2], title=title))
    assert "(RQ3 added)" in found.message


def test_the_last_record_wins(tmp_path):
    stale_first = record([*QUESTIONS, DROPPED]) + "\n" + record(QUESTIONS)
    assert currency(tmp_path, stale_first) == []
    current_first = record(QUESTIONS) + "\n" + record([*QUESTIONS, DROPPED])
    [found] = currency(tmp_path, current_first)
    assert "(RQ4 removed)" in found.message


def test_the_record_ends_at_the_next_heading(tmp_path):
    review = record(QUESTIONS) + "\n## Notes\n\n1. A numbered note that is no question.\n"
    assert currency(tmp_path, review) == []


# What a student or a misplaced hint leaves below a record that matches: none of
# it is a recorded question, list-shaped or not.
BELOW_THE_RECORD = {
    "notes with bullets": ('\nLanguage: a few typos recur, for example:\n'
                           '- "recieve" for "receive"\n- "seperate" for "separate"\n'),
    "breaks after a blank line": "\n---\n\n* * *\n\n- a bullet after the breaks\n",
    "break right after the list": "* * *\n- a bullet after the break\n",
    "lower heading": "\n### Notes\n\n- a bullet under a lower heading\n",
}


@pytest.mark.parametrize("below", BELOW_THE_RECORD.values(), ids=BELOW_THE_RECORD.keys())
def test_what_follows_the_record_list_is_no_recorded_question(tmp_path, below):
    assert currency(tmp_path, record(QUESTIONS) + below) == []


def test_a_loose_record_list_is_read_whole(tmp_path):
    assert currency(tmp_path, record(QUESTIONS).replace("\n2. ", "\n\n2. ")) == []
    stale = record([*QUESTIONS, DROPPED]).replace("\n4. ", "\n\n4. ")
    [found] = currency(tmp_path, stale)
    assert "(RQ4 removed)" in found.message


def test_an_introductory_line_before_the_record_list_is_skipped(tmp_path):
    review = record(QUESTIONS).replace("\n\n1. ", "\n\nThe questions this review judged:\n\n1. ")
    assert currency(tmp_path, review) == []
    [found] = currency(tmp_path, review.replace(QUESTIONS[2], DROPPED))
    assert "(RQ3 changed)" in found.message


@pytest.mark.parametrize("review", [
    None,
    REVIEW_BODY,
    REVIEW_BODY + "\n## Research questions reviewed\n\nNone recorded.\n",
    b"**Verdict: ready**\n\n## Research questions reviewed\n\n1. caf\xe9?\n",
], ids=["no review", "no record", "empty record", "not UTF-8"])
def test_silent_reviews(tmp_path, review):
    assert currency(tmp_path, review) == []


def test_a_directory_at_the_review_path_is_silent(tmp_path):
    proposal = stage(tmp_path, None)
    check.review_path(proposal).mkdir()
    findings = check.check_findings(proposal, STRUCTURE, {})
    assert RULE not in {f.rule for f in findings}


def test_a_proposal_without_ordered_questions_is_silent(tmp_path):
    prose = CLEAN
    for n, question in enumerate(QUESTIONS, 1):
        prose = prose.replace(f"{n}. {question}", question)
    findings = check.check_findings(stage(tmp_path, record(QUESTIONS[:2]), prose), STRUCTURE, {})
    assert RULE not in {f.rule for f in findings}
    assert "research-questions-not-a-list" in {f.rule for f in findings}


# ---------- exit code and digest ----------------------------------------------


def json_report(proposal: Path) -> dict:
    return json.loads(run_check(proposal, "--json").stdout)


def pair(tmp_path: Path, proposal: str = CLEAN) -> tuple[Path, Path]:
    """The same proposal in two workspaces: alone, and beside a review of a
    broader version."""
    return (stage(tmp_path / "bare", None, proposal),
            stage(tmp_path / "stale", record([*QUESTIONS, DROPPED]), proposal))


def test_the_warning_changes_neither_exit_code_nor_digest(tmp_path):
    bare, stale = pair(tmp_path)
    plain, warned = json_report(bare), json_report(stale)
    assert RULE in {f["rule"] for f in warned["findings"]}
    assert (warned["exit_code"], warned["digest"]) == (plain["exit_code"], plain["digest"])
    human_plain, human_warned = run_check(bare), run_check(stale)
    assert human_warned.returncode == human_plain.returncode == plain["exit_code"]
    assert "(RQ4 removed)" in human_warned.stdout
    digest = next(line for line in human_plain.stdout.splitlines() if line.startswith("digest:"))
    assert digest in human_warned.stdout


def test_an_error_exit_stays_an_error_exit(tmp_path):
    bare, stale = pair(tmp_path, CLEAN.replace("## Timeline", "## Zeitplan"))
    plain, warned = json_report(bare), json_report(stale)
    assert plain["exit_code"] == warned["exit_code"] == 1
    assert run_check(stale).returncode == 1


# ---------- the review skill names the titles the script reads ----------------


def record_bullet(skill_md: str) -> str:
    """The `## Output` bullet that tells the review to write the record."""
    output = skill_md.split("\n## Output\n", 1)[1].split("\n## ", 1)[0]
    bullets = [line for line in output.splitlines() if line.startswith("- ")]
    found = [line for line in bullets if "verbatim" in line]
    assert len(found) == 1, f"expected one record bullet in the review's Output, found {found}"
    return found[0]


def test_the_review_skill_names_every_record_title_the_script_reads():
    """Drift guard: a title the review prose stops naming is a record the check
    can no longer find, and every later review would read as written before
    the record existed."""
    bullet = record_bullet((REPO / "skills" / "proposal-review" / "SKILL.md")
                           .read_text(encoding="utf-8"))
    missing = [t for t in check.RQ_RECORD_TITLES if f"`## {t}`" not in bullet]
    assert not missing, f"the review's record bullet no longer names: {missing}"
