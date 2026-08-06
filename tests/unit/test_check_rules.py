"""L0: the check script's rules as individual functions.

Before the split these could only be reached by driving the whole 250-line
`check()` and grepping its report, so a failure named the script rather than the
rule. These call the rules directly.

The closed identifier set is tested here too: an identifier no rule can produce
is a rule that was deleted without its entry, and a duplicate identifier makes
two findings indistinguishable to every consumer keyed on it.
"""

import json

import check
import pytest
from helpers import FIXTURES, REPO, run_check

STRUCTURE = json.loads((REPO / "shared" / "structure.json").read_text(encoding="utf-8"))


def context(text: str, overrides: dict | None = None) -> check.Context:
    body, meta = check.split_proposal(text)
    return check.build_context(body, meta, STRUCTURE, overrides or {})


CLEAN = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text(encoding="utf-8")


# ---------- the closed identifier set ----------------------------------------


def test_rule_identifiers_are_unique():
    assert len(check.RULE_IDS) == len(set(check.RULE_IDS))


def test_every_declared_identifier_is_reachable():
    """Every id in the closed set must be produced somewhere — by a fixture
    oracle or by a test in this file. An unreachable id is a rule that was
    removed without its entry, or an entry that was never wired up."""
    produced = set()
    for oracle in sorted(FIXTURES.glob("*/expected.json")):
        rules = json.loads(oracle.read_text(encoding="utf-8"))["check"].get("rules", {})
        produced |= set(rules.get("errors", [])) | set(rules.get("warnings", []))
    produced |= COVERED_BY_UNIT_TESTS
    unreachable = set(check.RULE_IDS) - produced
    assert not unreachable, (
        f"identifiers no fixture or unit test produces: {sorted(unreachable)} — "
        "either the rule is gone or the entry was never wired up"
    )


def test_every_emitted_identifier_is_declared():
    """The inverse: a rule may not invent an identifier outside the closed set."""
    emitted = set()
    for proposal in sorted(FIXTURES.glob("*/*.md")):
        if proposal.name in ("README.md", "guidelines.md"):
            continue
        findings = check.check_findings(
            proposal, STRUCTURE, check.load_overrides(proposal, None)
        )
        emitted |= {f.rule for f in findings}
    undeclared = emitted - set(check.RULE_IDS)
    assert not undeclared, f"identifiers emitted but not declared: {sorted(undeclared)}"


# ---------- individual rules --------------------------------------------------


def rules_of(findings: list[check.Finding]) -> list[str]:
    return [f.rule for f in findings]


def test_metadata_present_reports_a_missing_block():
    ctx = context("# Introduction to the Topic\n\nbody\n")
    assert rules_of(check.rule_metadata_present(ctx)) == ["metadata-block-missing"]


def test_metadata_present_reports_a_missing_blank_line():
    ctx = context("# Topic\nbody\n---\ntitle: T\nlang: en\n---")
    assert rules_of(check.rule_metadata_present(ctx)) == ["metadata-block-blank-line"]


def test_reference_id_syntax_reports_boolean_literals_and_duplicates():
    text = (
        "# Topic\n\nbody\n\n---\ntitle: T\nlang: en\nreferences:\n"
        "- id: on\n  type: article-journal\n"
        "- id: Dup24One\n  type: article-journal\n"
        "- id: Dup24One\n  type: article-journal\n---"
    )
    assert rules_of(check.rule_reference_id_syntax(context(text))) == [
        "reference-id-boolean-literal", "duplicate-reference-id",
    ]


def test_title_rule_reports_a_missing_title():
    text = "# Topic\n\nbody\n\n---\nlang: en\nreferences: []\n---"
    assert rules_of(check.rule_title(context(text))) == ["metadata-title-missing"]


@pytest.mark.parametrize(("title", "rule"), [
    ("Development of a Soil Moisture Sensor Platform", "title-implementation-opener"),
    ("Revolutionizing Soil Moisture Sensing for Irrigation", "title-buzzword"),
    ("Can Soil Moisture Sensing Improve Irrigation Accuracy?", "title-question-form"),
    ("Soil Moisture", "title-too-short"),
    (" ".join(["Soil Moisture Sensing for Irrigation Control in Arid Regions"] * 4),
     "title-too-long"),
])
def test_title_rule_reports_each_mechanical_tell(title, rule):
    text = f"# Topic\n\nbody\n\n---\ntitle: {title}\nlang: en\nreferences: []\n---"
    assert rule in rules_of(check.rule_title(context(text)))


def test_title_rule_says_nothing_about_a_block_scalar():
    """A folded value continues on lines the narrow extraction never reads, so
    judging it would mean judging a fragment."""
    text = "# Topic\n\nbody\n\n---\ntitle: >\nlang: en\nreferences: []\n---"
    assert check.rule_title(context(text)) == []


def test_timeline_mode_reports_an_unknown_value():
    ctx = context(CLEAN, {"timeline_detail": "gantt"})
    assert rules_of(check.rule_timeline_mode(ctx)) == ["timeline-detail-unknown"]
    # and the effective mode falls back, so the size guard still runs
    assert ctx.detail == "simple"


def test_timeline_size_is_skipped_in_detailed_mode():
    with_table = CLEAN.replace(
        "# Timeline\n", "# Timeline\n\n| Phase | Weeks |\n|---|---|\n| One | 4 |\n"
    )
    assert "timeline-table" in rules_of(check.rule_timeline_size(context(with_table)))
    assert check.rule_timeline_size(
        context(with_table, {"timeline_detail": "detailed"})
    ) == []


def test_required_sections_names_each_missing_title():
    text = "# Introduction to the Topic\n\nbody\n\n---\ntitle: T\nlang: en\nreferences: []\n---"
    findings = check.rule_required_sections(context(text))
    assert set(rules_of(findings)) == {"required-section-missing"}
    assert len(findings) > 1


def test_methodology_rule_reports_an_unknown_methodology():
    text = CLEAN.replace(
        "# Methodology for Research: Prototype Implementation",
        "# Methodology for Research: Vibes-Driven Inquiry",
    )
    assert rules_of(check.rule_methodology(context(text))) == ["methodology-unknown"]


def test_methodology_rule_reports_a_missing_and_a_duplicated_section():
    without = CLEAN.replace("# Methodology for Research: Prototype Implementation", "# Approach")
    assert rules_of(check.rule_methodology(context(without))) == ["methodology-missing"]
    twice = CLEAN.replace(
        "# Methodology for Research: Prototype Implementation",
        "# Methodology for Research: Prototype Implementation\n\ntext\n\n"
        "# Methodology for Research: Case Study",
    )
    assert rules_of(check.rule_methodology(context(twice))) == ["methodology-multiple"]


def test_methodology_rule_reports_a_missing_subsection():
    without_sub = CLEAN.replace("## Requirements", "## Groundwork")
    assert rules_of(check.rule_methodology(context(without_sub))) == [
        "methodology-subsection-missing"
    ]


def test_methodology_rule_is_silent_when_the_workspace_overrides_the_sections():
    """An overridden section list replaces the closed set, so the canonical
    methodology rules no longer apply."""
    ctx = context(CLEAN, {"required_sections": ["Alpha", "Beta"]})
    assert check.rule_methodology(ctx) == []


def test_citations_rule_separates_undefined_keys_from_uncited_references():
    text = (
        "# Topic\n\nA claim [@Ghost99Missing].\n\n---\ntitle: T\nlang: en\nreferences:\n"
        "- id: Real24Work\n  type: article-journal\n  author:\n  - family: Doe\n---"
    )
    findings = check.rule_citations(context(text))
    assert rules_of(findings) == ["citation-undefined", "reference-uncited"]
    assert findings[0].level == "error"
    assert findings[1].level == "warning"


def test_citations_rule_flags_a_name_typed_before_its_own_citation():
    text = (
        "# Topic\n\nRivera et al. [@Rivera23Survey] surveyed it.\n\n"
        "---\ntitle: T\nlang: en\nreferences:\n"
        "- id: Rivera23Survey\n  type: article-journal\n  author:\n  - family: Rivera\n---"
    )
    assert "author-name-typed-bracketed" in rules_of(check.rule_citations(context(text)))


def test_reference_id_shape_rule_catches_a_missing_year():
    """The observed defect: an eval produced `RiveraYearSurvey`, the literal
    word "Year" where the two-digit year belongs, and nothing caught it."""
    text = (
        "# Topic\n\nA claim [@RiveraYearSurvey].\n\n---\ntitle: T\nlang: en\nreferences:\n"
        "- id: RiveraYearSurvey\n  type: article-journal\n---"
    )
    assert "reference-id-shape" in rules_of(check.rule_reference_id_shape(context(text)))


def test_min_references_respects_a_workspace_override():
    ctx = context(CLEAN)
    assert check.rule_min_references(ctx) == []
    raised = context(CLEAN, {"min_references": 99})
    assert rules_of(check.rule_min_references(raised)) == ["min-references"]


def test_prose_patterns_rule_reports_personal_data_and_first_person():
    text = (
        "# Topic\n\nI ran the study myself and you can reach me at a.b@example.org.\n\n"
        "---\ntitle: T\nlang: en\nreferences: []\n---"
    )
    found = rules_of(check.rule_prose_patterns(context(text)))
    assert "first-person-pronoun" in found
    assert "email-address" in found


# Identifiers this file produces that no fixture happens to carry. Listed
# explicitly so `test_every_declared_identifier_is_reachable` stays honest
# rather than being weakened to a subset check.
COVERED_BY_UNIT_TESTS = {
    "metadata-block-missing",
    "metadata-title-missing",
    "title-question-form",
    "title-too-long",
    "timeline-detail-unknown",
    "timeline-table",
    "timeline-list",
    "timeline-subsection",
    "timeline-too-long",
    "methodology-missing",
    "methodology-multiple",
    "methodology-unknown",
    "methodology-subsection-missing",
    "metadata-block-multiple",
    "guidelines-toml-parse",
    "research-questions-not-a-list",
    "research-question-unreferenced",
    "author-name-typed-bracketed",
    "author-name-typed-in-text",
    "author-in-text-without-author",
    "reference-id-shape",
    "reference-id-too-long",
    "email-address",
    "first-person-pronoun",
    "repeated-sentence-start",
    "length-over-limit",
    "forbidden-section",
    "section-out-of-order",
}


def test_json_mode_matches_the_human_report(tmp_path):
    """Same run, two renderings: the exit code and the finding count must agree,
    or a consumer reading one would disagree with a student reading the other."""
    proposal = tmp_path / "p.md"
    proposal.write_text(CLEAN.replace("# Timeline", "# Timeline and Milestones"),
                        encoding="utf-8")
    human = run_check(proposal)
    findings = check.check_findings(proposal, STRUCTURE, {})
    errors = [f for f in findings if f.level == "error"]
    assert human.returncode == (1 if errors else 0)
    assert human.stdout.count("- ERROR:") == len(errors)
    assert human.stdout.count("- WARNING:") == len(findings) - len(errors)


def test_warnings_alone_still_exit_zero(tmp_path):
    """The check is advisory: it gates nothing on warnings."""
    proposal = tmp_path / "p.md"
    proposal.write_text(CLEAN, encoding="utf-8")
    findings = check.check_findings(proposal, STRUCTURE, {})
    assert not [f for f in findings if f.level == "error"]
    assert run_check(proposal).returncode == 0


def test_json_mode_suppresses_the_human_report(tmp_path, capsys):
    proposal = tmp_path / "p.md"
    proposal.write_text(CLEAN, encoding="utf-8")
    check.main([str(proposal), "--json"])
    out = capsys.readouterr().out
    assert "## Verified mechanically" not in out
    payload = json.loads(out)
    assert payload["digest"].startswith("sha256:")
    assert payload["exit_code"] == 0
    assert all({"level", "rule", "message"} <= set(f) for f in payload["findings"])
