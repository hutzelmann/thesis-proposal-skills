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
    ctx = context("# Topic\nbody\n---\nreferences: []\n---")
    assert rules_of(check.rule_metadata_present(ctx)) == ["metadata-block-blank-line"]


def test_reference_id_syntax_reports_boolean_literals_and_duplicates():
    text = (
        "# Topic\n\nbody\n\n---\nreferences:\n"
        "- id: on\n  type: article-journal\n"
        "- id: Dup24One\n  type: article-journal\n"
        "- id: Dup24One\n  type: article-journal\n---"
    )
    assert rules_of(check.rule_reference_id_syntax(context(text))) == [
        "reference-id-boolean-literal", "duplicate-reference-id",
    ]


@pytest.mark.parametrize(("title", "rule"), [
    ("Development of a Soil Moisture Sensor Platform", "title-implementation-opener"),
    ("Revolutionizing Soil Moisture Sensing for Irrigation", "title-buzzword"),
    ("Can Soil Moisture Sensing Improve Irrigation Accuracy?", "title-question-form"),
    ("Soil Moisture", "title-too-short"),
    (" ".join(["Soil Moisture Sensing for Irrigation Control in Arid Regions"] * 4),
     "title-too-long"),
])
def test_title_rule_reports_each_mechanical_tell(title, rule):
    text = f"# {title}\n\nbody\n\n---\nreferences: []\n---"
    assert rule in rules_of(check.rule_title(context(text)))


def test_title_rule_says_nothing_about_a_todo_title():
    """An unsettled title is the sanctioned incomplete state — the todo-marker
    finding already covers it, and tells on the placeholder text are noise."""
    text = "# [TODO: working title naming the contribution]\n\nbody\n\n---\nreferences: []\n---"
    assert check.rule_title(context(text)) == []


def test_timeline_mode_reports_an_unknown_value():
    ctx = context(CLEAN, {"timeline": {"detail": "gantt"}})
    assert rules_of(check.rule_timeline_mode(ctx)) == ["timeline-detail-unknown"]
    # and the effective mode falls back, so the size guard still runs
    assert ctx.detail == "simple"


def test_timeline_size_is_skipped_in_detailed_mode():
    with_table = CLEAN.replace(
        "## Timeline\n", "## Timeline\n\n| Phase | Weeks |\n|---|---|\n| One | 4 |\n"
    )
    assert "timeline-table" in rules_of(check.rule_timeline_size(context(with_table)))
    assert check.rule_timeline_size(
        context(with_table, {"timeline": {"detail": "detailed"}})
    ) == []


def test_required_sections_names_each_missing_title():
    text = "# Introduction to the Topic\n\nbody\n\n---\nreferences: []\n---"
    findings = check.rule_required_sections(context(text))
    assert set(rules_of(findings)) == {"required-section-missing"}
    assert len(findings) > 1


def test_methodology_rule_reports_an_unknown_methodology():
    text = CLEAN.replace(
        "## Methodology for Research: Prototype Implementation",
        "## Methodology for Research: Vibes-Driven Inquiry",
    )
    assert rules_of(check.rule_methodology(context(text))) == ["methodology-unknown"]


def test_methodology_rule_reports_a_missing_and_a_duplicated_section():
    without = CLEAN.replace("## Methodology for Research: Prototype Implementation", "## Approach")
    assert rules_of(check.rule_methodology(context(without))) == ["methodology-missing"]
    twice = CLEAN.replace(
        "## Methodology for Research: Prototype Implementation",
        "## Methodology for Research: Prototype Implementation\n\ntext\n\n"
        "## Methodology for Research: Case Study",
    )
    assert rules_of(check.rule_methodology(context(twice))) == ["methodology-multiple"]


def test_methodology_rule_reports_a_missing_subsection():
    without_sub = CLEAN.replace("### Requirements", "### Groundwork")
    assert rules_of(check.rule_methodology(context(without_sub))) == [
        "methodology-subsection-missing"
    ]


CASE_STUDY = {
    "title": {"en": "Case Study", "de": "Fallstudie"},
    "subsections": [
        {"en": "Case and Context", "de": "Fall und Kontext", "guidance": "the case"},
        {"en": "Analysis", "de": "Analyse", "guidance": "how it is analysed"},
    ],
}


def test_workspace_branch_is_merged_over_the_shipped_set():
    """The closure stays; its contents are the workspace's to decide."""
    merged = check.merge_methodologies(STRUCTURE, {"methodologies": {"case": CASE_STUDY}})
    assert merged["case"]["title"]["en"] == "Case Study"
    assert set(STRUCTURE["methodologies"]) < set(merged)


def test_workspace_can_disable_a_shipped_branch():
    merged = check.merge_methodologies(
        STRUCTURE, {"methodologies": {"theoretical": {"enabled": False}}})
    assert "theoretical" not in merged
    assert "prototype" in merged


def test_workspace_declaring_nothing_gets_the_shipped_set():
    assert check.merge_methodologies(STRUCTURE, {}) == STRUCTURE["methodologies"]


@pytest.mark.parametrize(("branch", "needle"), [
    ({"subsections": [{"en": "A", "de": "A", "guidance": "g"}]}, "needs a `title`"),
    ({"title": {"en": "X"}, "subsections": [{"en": "A", "de": "A", "guidance": "g"}]},
     "needs a `title`"),
    ({"title": {"en": "X", "de": "X"}}, "at least one subsection"),
    ({"title": {"en": "X", "de": "X"}, "subsections": [{"en": "A", "de": "A"}]}, "guidance"),
    ({"title": {"en": "X", "de": "X"}, "subsections": [{"en": "A", "guidance": "g"}]},
     "needs both `en` and `de`"),
    ({"title": {"en": "X", "de": "X"}, "subsections": [], "colour": "red"}, "unknown key"),
])
def test_invalid_branch_is_named_and_not_applied(branch, needle):
    """A branch that cannot say what goes inside it would have the write skill
    inventing content for a heading it has never seen."""
    assert needle in check.branch_problem(branch)
    assert check.merge_methodologies(STRUCTURE, {"methodologies": {"x": branch}}) == \
        STRUCTURE["methodologies"]
    findings = check.override_key_findings({"methodologies": {"x": branch}})
    assert rules_of(findings) == ["methodology-branch-invalid"]


def test_methodology_rule_is_silent_when_the_workspace_overrides_the_sections():
    """An overridden section list replaces the closed set, so the canonical
    methodology rules no longer apply."""
    ctx = context(CLEAN, {"sections": {"required": ["Alpha", "Beta"]}})
    assert check.rule_methodology(ctx) == []


def test_citations_rule_separates_undefined_keys_from_uncited_references():
    text = (
        "# Topic\n\nA claim [@Ghost99Missing].\n\n---\nreferences:\n"
        "- id: Real24Work\n  type: article-journal\n  author:\n  - family: Doe\n---"
    )
    findings = check.rule_citations(context(text))
    assert rules_of(findings) == ["citation-undefined", "reference-uncited"]
    assert findings[0].level == "error"
    assert findings[1].level == "warning"


def test_citations_rule_flags_a_name_typed_before_its_own_citation():
    text = (
        "# Topic\n\nRivera et al. [@Rivera23Survey] surveyed it.\n\n"
        "---\nreferences:\n"
        "- id: Rivera23Survey\n  type: article-journal\n  author:\n  - family: Rivera\n---"
    )
    assert "author-name-typed-bracketed" in rules_of(check.rule_citations(context(text)))


def test_reference_id_shape_rule_catches_a_missing_year():
    """The observed defect: an eval produced `RiveraYearSurvey`, the literal
    word "Year" where the two-digit year belongs, and nothing caught it."""
    text = (
        "# Topic\n\nA claim [@RiveraYearSurvey].\n\n---\nreferences:\n"
        "- id: RiveraYearSurvey\n  type: article-journal\n---"
    )
    assert "reference-id-shape" in rules_of(check.rule_reference_id_shape(context(text)))


def test_min_references_respects_a_workspace_override():
    ctx = context(CLEAN)
    assert check.rule_min_references(ctx) == []
    raised = context(CLEAN, {"references": {"min_count": 99}})
    assert rules_of(check.rule_min_references(raised)) == ["min-references"]


def sized_proposal(refs: int, words: int) -> str:
    """A proposal whose only interesting properties are its body word count and
    its number of defined references — the two inputs of the density rule."""
    entries = "".join(f"- id: Ref{i:02d}Topic\n  type: article-journal\n"
                      for i in range(refs))
    block = f"---\nreferences:\n{entries}---" if refs else "---\nreferences: []\n---"
    return "# Topic\n\n" + ("word " * words).strip() + "\n\n" + block


def test_reference_density_warns_on_a_full_length_thin_bibliography():
    # 2000 words at the default 4/1000 expect 8; 5 defined references fall short
    ctx = context(sized_proposal(refs=5, words=2000))
    found = check.rule_reference_density(ctx)
    assert rules_of(found) == ["reference-density-low"]
    assert "5 references" in found[0].message
    assert "(8 here)" in found[0].message


def test_reference_density_leaves_short_drafts_alone():
    # 300 words expect ceil(1.2) = 2 — at or below the floor, nothing to say
    assert check.rule_reference_density(context(sized_proposal(refs=3, words=300))) == []


def test_reference_density_meets_the_expectation_exactly():
    # 1000 words expect exactly 4: the bound is strict shortfall, not <=
    assert check.rule_reference_density(context(sized_proposal(refs=4, words=1000))) == []


def test_reference_density_is_suppressed_while_the_floor_error_fires():
    # 2 references sit under the floor of 3: min-references already names the
    # defect, so the advisory stays silent — one finding per defect
    assert check.rule_reference_density(context(sized_proposal(refs=2, words=2000))) == []


def test_reference_density_respects_a_workspace_override():
    text = sized_proposal(refs=5, words=1000)
    assert check.rule_reference_density(context(text)) == []  # 5 >= ceil(4)
    raised = context(text, {"references": {"min_per_1000_words": 8}})
    assert rules_of(check.rule_reference_density(raised)) == ["reference-density-low"]


def test_reference_density_zero_disables_the_advisory():
    ctx = context(sized_proposal(refs=3, words=5000),
                  {"references": {"min_per_1000_words": 0}})
    assert check.rule_reference_density(ctx) == []


def test_reference_density_rejects_a_negative_or_non_numeric_override():
    for bad in ("4", -1, True, float("inf")):
        ctx = context(sized_proposal(refs=3, words=300),
                      {"references": {"min_per_1000_words": bad}})
        assert rules_of(check.rule_reference_density(ctx)) == \
            ["reference-density-invalid"], bad


def test_reference_density_survives_extreme_but_valid_overrides():
    # 1e308 is a finite TOML float and a 400-digit TOML integer is a finite
    # int: both pass the validity gate, and neither may crash the run — the
    # cap at one reference per word keeps the arithmetic in range
    for huge in (1.0e308, 10**400):
        ctx = context(sized_proposal(refs=3, words=100),
                      {"references": {"min_per_1000_words": huge}})
        assert rules_of(check.rule_reference_density(ctx)) == \
            ["reference-density-low"], huge


def test_reference_density_fractional_override_met_exactly_stays_silent():
    # 12500 * 4.4 / 1000 lands a hair above 55 in IEEE doubles; the epsilon
    # round keeps an exactly-met configured density from tripping the warning
    ctx = context(sized_proposal(refs=55, words=12500),
                  {"references": {"min_per_1000_words": 4.4}})
    assert check.rule_reference_density(ctx) == []


def test_reference_density_is_off_when_the_structure_predates_the_constant():
    # an older references/structure.json has no min_per_1000_words: the
    # advisory disables rather than crashing on the missing default
    structure = json.loads(json.dumps(STRUCTURE))
    del structure["references"]["min_per_1000_words"]
    body, meta = check.split_proposal(sized_proposal(refs=3, words=5000))
    ctx = check.build_context(body, meta, structure, {})
    assert check.rule_reference_density(ctx) == []
    # an invalid override on top of the old structure still degrades: the
    # error is reported and the missing default falls back to disabled
    invalid = check.build_context(
        body, meta, structure, {"references": {"min_per_1000_words": -1}})
    assert rules_of(check.rule_reference_density(invalid)) == \
        ["reference-density-invalid"]


def test_prose_patterns_rule_reports_personal_data_and_first_person():
    text = (
        "# Topic\n\nI ran the study myself and you can reach me at a.b@example.org.\n\n"
        "---\nreferences: []\n---"
    )
    found = rules_of(check.rule_prose_patterns(context(text)))
    assert "first-person-pronoun" in found
    assert "email-address" in found


# ---------- false positives found by adversarial probing (2026-08-13) --------
#
# Five ordinary documents the checker read wrongly. The expensive one is first:
# on a proposal about Java annotations, `@Override` in prose was reported as an
# undefined citation key, and the write skill's "fix every error it reports"
# turned that into a model rewriting the author's terminology and another
# deleting a real reference to quiet the fallout. The rest are cheaper but the
# same shape — a correct document told it is wrong.

ANNOTATIONS = (
    "# Topic\n\n{token} is excluded because it carries no runtime dispatch "
    "[@Dyer14Mining].\n\n---\nreferences:\n"
    "- id: Dyer14Mining\n  type: paper-conference\n  author:\n  - family: Dyer\n---"
)


@pytest.mark.parametrize("token", ["`@Override`", "``@Override``", "\\@Override"])
def test_citations_rule_ignores_an_at_word_marked_as_code_or_escaped(token):
    """Markup is the student's way out: a `@Word` that is code says so, and the
    checker believes it. Without this the only way out was editing the prose."""
    assert check.rule_citations(context(ANNOTATIONS.format(token=token))) == []


def test_citations_rule_ignores_an_at_word_inside_a_fenced_block():
    text = ANNOTATIONS.format(token="Dispatch").replace(
        "# Topic\n", "# Topic\n\n```java\n@Override\npublic void run() {}\n```\n")
    assert check.rule_citations(context(text)) == []


def test_citations_rule_still_reports_a_bare_at_word():
    """The escape hatch must not weaken the real check: unmarked, it is a key."""
    ctx = context(ANNOTATIONS.format(token="@Override"))
    assert rules_of(check.rule_citations(ctx)) == ["citation-undefined"]


def test_prose_patterns_rule_does_not_read_type_i_error_as_a_pronoun():
    """`Type I error` is required vocabulary in the Controlled Experiment
    subsection contract, so the warning fired on the repo's own branch."""
    text = ("# Topic\n\nThe Type I error rate is controlled with a Bonferroni "
            "correction.\n\n---\nreferences: []\n---")
    assert check.rule_prose_patterns(context(text)) == []


def test_prose_patterns_rule_locates_the_number_it_read_as_a_matriculation():
    """A seven-digit corpus size trips the matriculation regex. This warning
    class tolerates false positives — what made this one expensive is that it
    named neither the token nor the line, so dismissing it meant a full read."""
    text = ("# Topic\n\nThe corpus holds 2400000 annotated declarations.\n\n"
            "---\nreferences: []\n---")
    findings = check.rule_prose_patterns(context(text))
    assert rules_of(findings) == ["matriculation-number"]
    assert "`2400000`" in findings[0].message
    assert "(line 3)" in findings[0].message


def test_prose_patterns_rule_locates_the_first_pronoun_it_counted():
    text = ("# Topic\n\nBackground.\n\nSmith and I ran the study.\n\n"
            "---\nreferences: []\n---")
    findings = check.rule_prose_patterns(context(text))
    assert rules_of(findings) == ["first-person-pronoun"]
    assert "(line 5)" in findings[0].message


def hindsight(prose: str, lang: str = "en") -> list[str]:
    # the subtitle wording is what fixes the language now that `lang` is inferred
    subtitle = "*Exposé zur Masterarbeit*" if lang == "de" else "*Master's Thesis Proposal*"
    text = (f"# Topic\n\n{subtitle}\n\n{prose}\n\n---\nreferences: []\n---")
    return rules_of(check.rule_hindsight_leakage(context(text)))


def test_hindsight_rule_reports_an_uncited_result_claim():
    findings = check.rule_hindsight_leakage(context(
        "# Topic\n\nThe evaluation demonstrated that scheduling cuts water use.\n\n"
        "---\nreferences: []\n---"))
    assert rules_of(findings) == ["hindsight-leakage"]
    assert "`demonstrated`" in findings[0].message
    assert "(line 3)" in findings[0].message


def test_hindsight_rule_ignores_a_result_attributed_to_prior_work():
    """Reporting what prior work established is what the contribution section
    is for. Without the citation anchor the rule fires on every correct
    proposal, which is the whole reason it is anchored there."""
    assert hindsight("@Rivera23Survey demonstrated that scheduling cuts water use.") == []
    assert hindsight("Scheduling cuts water use [@Rivera23Survey], as shown there.") == []


def test_hindsight_rule_ignores_a_planned_measurement():
    assert hindsight(
        "A field trial compares water use under scheduling against a fixed timetable."
    ) == []


def test_hindsight_rule_ignores_present_tense_passive():
    """A review fixture states what it will look for — `the conditions under
    which faithfulness is actually demonstrated`. Present-tense passive names a
    property the work goes looking for; the past tense states a result it has."""
    assert hindsight(
        "The comparison identifies the conditions under which faithfulness to "
        "the classifier is actually demonstrated (RQ2)."
    ) == []
    assert hindsight("Faithfulness was demonstrated for every model.") == [
        "hindsight-leakage"
    ]


def test_hindsight_rule_reports_a_quantified_outcome():
    assert hindsight("Scheduling reduced water use by 14 %.") == ["hindsight-leakage"]


def test_hindsight_rule_ignores_a_bare_number_without_a_change_word():
    """A planned threshold is a plan detail, not a finding."""
    assert hindsight("Significance is tested at the 5 % level.") == []


def test_hindsight_rule_reads_german_result_verbs():
    assert hindsight("Die Auswertung zeigte einen deutlichen Effekt.", "de") == [
        "hindsight-leakage"
    ]


def test_hindsight_rule_ignores_prose_inside_a_code_block():
    assert hindsight("```\nWe demonstrated the effect.\n```") == []


def test_metadata_present_names_a_block_that_sits_at_the_top():
    """Frontmatter at the top is what every other markdown tool expects, so a
    student arrives at it honestly — and gets five errors none of which say so."""
    text = ("---\nreferences: []\n---\n\n"
            "# Introduction to the Topic\n\nbody\n")
    findings = check.rule_metadata_present(context(text))
    assert rules_of(findings) == ["metadata-block-missing"]
    assert "top of the file" in findings[0].message


def test_heading_style_rule_names_underlined_headings():
    """A Word or LibreOffice export underlines its headings. Pandoc reads them,
    the section rules do not, and the report was five missing sections."""
    text = ("Introduction to the Topic\n=========================\n\nbody\n\n"
            "Timeline\n--------\n\nApril 2027 to September 2027.\n")
    findings = check.rule_heading_style(context(text))
    assert rules_of(findings) == ["heading-style-setext"]
    assert "Introduction to the Topic" in findings[0].message


def test_heading_style_rule_is_silent_on_prefixed_headings():
    assert check.rule_heading_style(context(CLEAN)) == []


def test_heading_style_rule_does_not_read_a_metadata_block_as_a_heading():
    """The closing `---` of a metadata block underlines the line above it. That
    line is a key, not a heading, and a document with no headings at all must
    not be told its headings are the wrong style."""
    text = "no headings here\n\n---\nreferences: []\n---"
    assert check.rule_heading_style(context(text)) == []


# ---------- document frame, references section, language inference -----------

FRAMED = ("# Adaptive Irrigation Scheduling for Greenhouses\n\n"
          "*Master's Thesis Proposal*\n\n"
          "## Introduction to the Topic\n\nbody\n\n"
          "## References\n\n---\nreferences: []\n---")


def test_frame_rule_accepts_the_canonical_frame():
    assert check.rule_frame(context(FRAMED)) == []


def test_frame_rule_reports_a_missing_title_line():
    text = "body without a title\n\n---\nreferences: []\n---"
    assert rules_of(check.rule_frame(context(text))) == ["title-line-missing"]


def test_frame_rule_reports_content_above_the_title():
    """pandoc promotes the H1 to the document title only as the first block;
    anything above it silently builds a document without a title."""
    text = FRAMED.replace("# Adaptive", "A stray import artifact.\n\n# Adaptive")
    assert "title-not-first" in rules_of(check.rule_frame(context(text)))


def test_frame_rule_reports_a_second_h1():
    text = FRAMED.replace("## Introduction to the Topic", "# Introduction to the Topic")
    assert "multiple-h1" in rules_of(check.rule_frame(context(text)))


def test_frame_rule_reports_a_missing_subtitle():
    text = FRAMED.replace("*Master's Thesis Proposal*\n\n", "")
    assert rules_of(check.rule_frame(context(text))) == ["subtitle-missing"]


def test_frame_rule_reports_an_unemphasized_subtitle():
    text = FRAMED.replace("*Master's Thesis Proposal*", "Master's Thesis Proposal")
    assert rules_of(check.rule_frame(context(text))) == ["subtitle-not-emphasized"]


def test_references_section_must_exist_be_last_and_stay_empty():
    missing = FRAMED.replace("## References\n\n", "")
    assert rules_of(check.rule_references_section(context(missing))) == [
        "references-section-missing"
    ]
    not_last = FRAMED.replace(
        "## Introduction to the Topic\n\nbody\n\n## References",
        "## References\n\n## Introduction to the Topic\n\nbody",
    )
    assert "references-section-not-last" in rules_of(
        check.rule_references_section(context(not_last)))
    filled = FRAMED.replace("## References\n", "## References\n\nHand-written entry.\n")
    assert "references-section-not-empty" in rules_of(
        check.rule_references_section(context(filled)))


def test_references_section_expects_the_german_title_for_a_german_proposal():
    text = ("# Typprüfung von Einheiten in wissenschaftlicher Software\n\n"
            "*Exposé zur Masterarbeit*\n\n## Einführung in das Thema\n\nbody\n\n"
            "## Literatur\n\n---\nreferences: []\n---")
    assert check.rule_references_section(context(text)) == []


def test_retired_keys_are_reported_individually():
    text = FRAMED.replace("references: []",
                          "title: T\nsubtitle: S\nlang: en\nreferences: []")
    findings = check.rule_retired_keys(context(text))
    assert rules_of(findings) == ["retired-metadata-key"] * 3


def test_legacy_format_is_named_as_a_shape():
    """The retired layout of this very toolchain must be named, not reported as
    a cascade of missing sections and flagged keys."""
    text = ("# Introduction to the Topic\n\nbody\n\n# Timeline\n\nOne line.\n\n"
            "---\ntitle: Automated Index Selection\nlang: en\nreferences: []\n---")
    findings = check.rule_legacy_format(context(text))
    assert rules_of(findings) == ["legacy-format"]
    assert "Automated Index Selection" in findings[0].message


def test_language_is_inferred_from_the_subtitle_first():
    """Subtitle wording beats section titles: here every section is English and
    the subtitle alone is German."""
    de = FRAMED.replace("*Master's Thesis Proposal*", "*Exposé zur Bachelorarbeit*")
    ctx = context(de)
    assert ctx.lang == "de"
    assert ctx.lang_determined
    assert check.rule_language(ctx) == []


def test_language_falls_back_to_a_section_title_majority():
    text = ("# Titel der Arbeit über Softwaretechnik\n\n"
            "*[TODO: state the degree level]*\n\n"
            "## Einführung in das Thema\n\nbody\n\n## Literatur\n\n"
            "---\nreferences: []\n---")
    ctx = context(text)
    assert ctx.lang == "de"
    assert ctx.lang_determined


def test_undeterminable_language_warns_and_defaults_to_english():
    text = ("# Topic Title Here Now\n\n*Something Else Entirely*\n\n"
            "## Freeform\n\nbody\n\n---\nreferences: []\n---")
    ctx = context(text)
    assert ctx.lang == "en"
    assert not ctx.lang_determined
    assert rules_of(check.rule_language(ctx)) == ["language-undeterminable"]


def test_the_title_heading_is_not_a_section():
    """A title colliding with section machinery must trip nothing: it is not a
    heading in `head_texts`, so forbidden patterns, the methodology prefix, and
    required-section matching never see it."""
    text = ("# Methodology for Research: Milestones and Gantt Planning\n\n"
            "*Master's Thesis Proposal*\n\n"
            "## Introduction to the Topic\n\nbody\n\n"
            "## References\n\n---\nreferences: []\n---")
    ctx = context(text)
    assert check.rule_forbidden_sections(ctx) == []
    assert rules_of(check.rule_methodology(ctx)) == ["methodology-missing"]
    assert "Methodology for Research" not in ctx.head_texts


def test_length_rejects_a_non_positive_or_non_numeric_page_limit():
    """Bad override degrades to the default with an error — the clean fixture
    stays under the default, so the error is the only finding."""
    for bad in ("5", -1, 0, float("nan"), True):
        ctx = context(CLEAN, {"length": {"page_limit": bad}})
        assert rules_of(check.rule_length(ctx)) == ["page-limit-invalid"], bad


def test_min_references_rejects_a_negative_or_non_integer_override():
    for bad in ("8", -5, True):
        ctx = context(CLEAN, {"references": {"min_count": bad}})
        assert rules_of(check.rule_min_references(ctx)) == ["min-references-invalid"], bad


# Identifiers this file produces that no fixture happens to carry. Listed
# explicitly so `test_every_declared_identifier_is_reachable` stays honest
# rather than being weakened to a subset check.
COVERED_BY_UNIT_TESTS = {
    # no fixture carries a broken override file: a fixture's guidelines.md is
    # part of its oracle, so a retired key there would be a fixture defect
    "override-key-retired",
    "override-key-unknown",
    "methodology-branch-invalid",
    "metadata-block-missing",
    "title-line-missing",
    "title-not-first",
    "multiple-h1",
    "subtitle-missing",
    "subtitle-not-emphasized",
    "references-section-missing",
    "references-section-not-last",
    "references-section-not-empty",
    "retired-metadata-key",
    "legacy-format",
    "language-undeterminable",
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
    "heading-style-setext",
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
    # no fixture states its own results: a proposal that did would be a
    # fixture defect, so the rule is reachable only from this file
    "hindsight-leakage",
    "repeated-sentence-start",
    "length-over-limit",
    "page-limit-invalid",
    "min-references-invalid",
    # every fixture defines at least as many references as its length expects
    # (the 995-word f19 carries 15 against an expectation of 4), so the
    # advisory never fires in the corpus; both ids are produced only from here
    "reference-density-low",
    "reference-density-invalid",
    "forbidden-section",
    "section-out-of-order",
}


def test_json_mode_matches_the_human_report(tmp_path):
    """Same run, two renderings: the exit code and the finding count must agree,
    or a consumer reading one would disagree with a student reading the other."""
    proposal = tmp_path / "p.md"
    proposal.write_text(CLEAN.replace("## Timeline", "## Timeline and Milestones"),
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
