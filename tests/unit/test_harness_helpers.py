"""L0: pure scoring helpers from harness/l1_checks.py (no model calls)."""

import io
import zipfile
from pathlib import Path

import publish
import pytest
from fixture_paths import fixture_proposal, oracle_path
from helpers import NOTES_TEXT, f04_numbered_questions, review_with_record
from l1_checks import (
    LATEX_ENGINES,
    built_tiers,
    disallowed_errors,
    disallowed_rules,
    docx_media,
    is_enumerated_review,
    parse_grade,
    pdf_images,
    select_draft,
    verdict_check_report,
    verdict_customize_override,
    verdict_draft,
    verdict_early_stop,
    verdict_figures_embedded,
    verdict_hollow_review,
    verdict_ideate_scoped,
    verdict_import,
    verdict_import_figures,
    verdict_litsearch_expanded,
    verdict_no_spurious_offer,
    verdict_notes_progress,
    verdict_offtopic_reference,
    verdict_provenance,
    verdict_publish,
    verdict_reverse,
    verdict_review,
    verdict_review_localized,
    verdict_scoping_containment,
    verdict_seed,
    verdict_title_alarm,
    verdict_troubleshoot_model_rung,
    without_rq_record,
)

REPO = Path(__file__).resolve().parents[2]

GOOD_IMPORT = """\
# Soil-Aware Irrigation Control

*Bachelor's Thesis Proposal*

## Introduction to the Topic

Irrigation schedules ignore soil data [@Rivera23Survey].
@Tanaka24Lora measured LoRa range in field conditions.

## References

---
references:
- id: Rivera23Survey
  type: article-journal
  author:
  - family: Rivera
    given: L.
  issued:
    year: 2023
---
"""


def test_disallowed_errors_filters_allowed():
    out = ("- ERROR: only 1 references — at least 3 required\n"
           "- ERROR: forbidden section: `Work Plan`")
    assert disallowed_errors(out, ("references — at least",)) == [
        "- ERROR: forbidden section: `Work Plan`"
    ]
    assert disallowed_errors(out)
    assert len(disallowed_errors(out)) == 2


def test_disallowed_rules_tolerates_the_reference_shortfall_by_identifier():
    """The tolerance is keyed on the rule id, so rewording the message cannot
    change what the harness lets through."""
    findings = [
        {"level": "error", "rule": "min-references", "message": "only 1 references — …"},
        {"level": "error", "rule": "forbidden-section",
         "message": "forbidden section: `Work Plan`"},
        {"level": "warning", "rule": "todo-marker", "message": "open [TODO: x]"},
    ]
    assert disallowed_rules(findings) == ["forbidden section: `Work Plan`"]


def test_disallowed_rules_reworded_message_still_tolerated():
    reworded = [{"level": "error", "rule": "min-references",
                 "message": "the proposal cites too few sources"}]
    assert disallowed_rules(reworded) == []


def test_is_enumerated_review():
    assert is_enumerated_review("Findings:\n1. RQs too broad — narrow them.\n2. Missing lit.")
    assert not is_enumerated_review("Looks fine overall, nothing enumerated here.")


def test_parse_grade_takes_last():
    assert parse_grade("thinking... GRADE: I ... reconsidering ... GRADE: C")
    assert not parse_grade("GRADE: I")
    assert not parse_grade("no grade at all")


CLEAN_CHECK = "# Check: x.md\n\n## Verified mechanically — no errors\n"
SHORT_REFS_CHECK = "- ERROR: only 2 references — at least 3 required\n"
BROKEN_CHECK = (
    "- ERROR: no trailing metadata block found (file must end with a `---` YAML block)\n"
    "- ERROR: no ordered-list research questions found in the research-questions section\n"
)


GOOD_REVERSE = """\
# Soil-Moisture-Driven Irrigation Scheduling

*Bachelor's Thesis Proposal*

## Introduction to the Topic

Irrigation schedules ignore soil data [@Rivera23Survey].
Calibration drift is a known problem in field sensor networks [@Okafor21Drift].

## Methodology for Research: Prototype Implementation

The prototype builds on the sensing approach of @Tanaka22Sensors.
The field trial runs on the Agrarmesse open sensor corpus named at registration.

## References

---
references:
- id: Rivera23Survey
  type: article-journal
  issued:
    year: 2023
- id: Okafor21Drift
  type: article-journal
  issued:
    year: 2021
- id: Tanaka22Sensors
  type: article-journal
  issued:
    year: 2022
---
"""


def test_verdict_reverse_accepts_a_plan_tense_proposal():
    passed, why = verdict_reverse(GOOD_REVERSE, CLEAN_CHECK, "soil-moisture.md")
    assert passed, why
    assert "soil-moisture.md" in why
    assert "pre-settled material kept" in why


def test_verdict_reverse_requires_a_produced_file():
    passed, why = verdict_reverse(None)
    assert not passed
    assert "no proposal file produced" in why


@pytest.mark.parametrize(("mutation", "needle"), [
    (lambda t: t.replace("soil data", "soil data, and the panel held 41 farms"),
     "41 farms"),
    (lambda t: t.replace("soil data", "soil data; water use fell by 18 %"), "18 %"),
    (lambda t: t.replace("Rivera", "Erika Musterfrau and Rivera"), "Erika Musterfrau"),
])
def test_verdict_reverse_reports_what_only_the_finished_work_knew(mutation, needle):
    passed, why = verdict_reverse(mutation(GOOD_REVERSE), CLEAN_CHECK, "x.md")
    assert not passed
    assert needle in why


def test_verdict_reverse_rejects_a_results_only_reference():
    text = GOOD_REVERSE.replace("- id: Tanaka22Sensors", "- id: Lindqvist24Yield")
    passed, why = verdict_reverse(text, CLEAN_CHECK, "x.md")
    assert not passed
    assert "Lindqvist24Yield" in why


def test_verdict_reverse_rejects_an_invented_reference():
    text = GOOD_REVERSE.replace("- id: Okafor21Drift", "- id: Fabricated26Study")
    passed, why = verdict_reverse(text, CLEAN_CHECK, "x.md")
    assert not passed
    assert "Fabricated26Study" in why


def test_verdict_reverse_does_not_tolerate_a_reference_shortfall():
    """Unlike import: the source carries enough framing citations to reach the
    minimum, so a shortfall means the contribution section was left thin."""
    passed, why = verdict_reverse(GOOD_REVERSE, SHORT_REFS_CHECK, "x.md")
    assert not passed
    assert "at least 3 required" in why


def test_verdict_reverse_fails_on_a_hindsight_warning():
    check_output = "- WARNING: `demonstrated` (line 3) states the work as already done\n"
    passed, why = verdict_reverse(GOOD_REVERSE, check_output, "x.md")
    assert not passed
    assert "hindsight" in why


def test_verdict_import_accepts_a_clean_import():
    passed, why = verdict_import(GOOD_IMPORT, CLEAN_CHECK, "soil-aware-irrigation.md")
    assert passed, why
    assert "soil-aware-irrigation.md" in why


def test_verdict_import_requires_a_produced_file():
    passed, why = verdict_import(None)
    assert not passed
    assert "no proposal file produced" in why


@pytest.mark.parametrize(("mutation", "needle"), [
    (lambda t: t.replace("references:", "matriculation: 00000000\nreferences:", 1), "00000000"),
    (lambda t: "PROPOSAL - CONFIDENTIAL\n\n" + t, "CONFIDENTIAL"),
])
def test_verdict_import_reports_leaks_the_check_cannot_see(mutation, needle):
    passed, why = verdict_import(mutation(GOOD_IMPORT), CLEAN_CHECK, "x.md")
    assert not passed
    assert needle in why


def test_verdict_import_fails_on_check_errors():
    """The defect that motivated this: a file holding the expected substrings
    while its metadata block is unclosed and its RQs are not a list."""
    passed, why = verdict_import(GOOD_IMPORT, BROKEN_CHECK, "x.md")
    assert not passed
    assert "no trailing metadata block" in why
    assert "ordered-list research questions" in why


def test_verdict_import_tolerates_a_reference_shortfall():
    """The source carries what it carries — import must not invent sources."""
    passed, why = verdict_import(GOOD_IMPORT, SHORT_REFS_CHECK, "x.md")
    assert passed, why


@pytest.mark.parametrize("sentence", [
    "Rivera et al. [@Rivera23Survey] surveyed irrigation control.",
    "The LoRa study of Tanaka [@Tanaka24Lora] measured range.",
])
def test_verdict_import_rejects_a_name_carried_over_from_the_source(sentence):
    """The source renders "Rivera et al. [1]"; carrying that name into the
    prose beside a bracketed key freezes it against the reference entry."""
    mutated = GOOD_IMPORT.replace("# Introduction to the Topic",
                                  "# Introduction to the Topic\n\n" + sentence)
    passed, why = verdict_import(mutated, CLEAN_CHECK, "x.md")
    assert not passed
    assert "author name typed before a bracketed citation" in why


def test_verdict_import_ignores_reference_block_author_names():
    """`family: Rivera` in the metadata must not trip the typed-name check."""
    passed, why = verdict_import(GOOD_IMPORT, CLEAN_CHECK, "x.md")
    assert passed, why


def test_verdict_import_rejects_a_todo_marker_inside_the_metadata_block():
    """Observed in 4/4 dev-runner artifacts: pandoc rejects the whole block,
    while check.py extracts narrowly and reports the file clean."""
    broken = GOOD_IMPORT.replace(
        "    year: 2023\n",
        "    year: 2023\n  [TODO: recover full reference details]\n",
    )
    passed, why = verdict_import(broken, CLEAN_CHECK, "x.md")
    assert not passed
    assert "bare line in the metadata block" in why


@pytest.mark.parametrize("value", [
    '  title: "[TODO: recover the title]"',   # quoted
    "  title: [TODO: recover the title]",     # unquoted but keyed
])
def test_verdict_import_allows_a_keyed_todo_marker_in_the_metadata(value):
    """Both shapes parse under pandoc; only a bare line breaks the block."""
    keyed = GOOD_IMPORT.replace("  title: A survey of smart irrigation control", value)
    passed, why = verdict_import(keyed, CLEAN_CHECK, "x.md")
    assert passed, why


def test_verdict_import_allows_todo_markers_in_the_body():
    with_todo = GOOD_IMPORT.replace(
        "# Introduction to the Topic\n",
        "# Introduction to the Topic\n\n[TODO: state the delta to prior work]\n",
    )
    passed, why = verdict_import(with_todo, CLEAN_CHECK, "x.md")
    assert passed, why


SEED = "# Idea Notes\n\nseed content\n"


def test_select_draft_grades_an_in_place_edit():
    chosen, why = select_draft({"seed.md": SEED + "expanded\n"}, "seed.md", SEED)
    assert chosen == "seed.md"
    assert "in place" in why


def test_select_draft_prefers_a_created_file_over_the_untouched_seed():
    """The defect that motivated this: a skill-compliant fresh `<slug>.md` was
    ignored and the untouched seed graded as the produced draft."""
    files = {"seed.md": SEED, "data-drift.md": "# Introduction to the Topic\n"}
    chosen, why = select_draft(files, "seed.md", SEED)
    assert chosen == "data-drift.md"
    assert "created data-drift.md" in why


def test_select_draft_prefers_a_created_file_even_beside_an_edited_seed():
    files = {"seed.md": SEED + "touched\n", "draft.md": "# Introduction to the Topic\n"}
    chosen, _ = select_draft(files, "seed.md", SEED)
    assert chosen == "draft.md"


def test_select_draft_reports_an_untouched_workspace():
    chosen, why = select_draft({"seed.md": SEED}, "seed.md", SEED)
    assert chosen is None
    assert "left untouched" in why


def test_select_draft_reports_a_missing_seed():
    chosen, why = select_draft({}, "seed.md", SEED)
    assert chosen is None
    assert "seed.md gone" in why


def test_select_draft_never_selects_overrides_or_skill_artifacts():
    files = {
        "seed/seed.md": SEED,
        "guidelines.md": "override",
        "seed/review.md": "1. finding",
        "seed/feedback.md": "Dear student",
        "seed/harvest.md": "# Harvest",
        "seed/seed.handout.md": "handout",
    }
    chosen, why = select_draft(files, "seed/seed.md", SEED)
    assert chosen is None
    assert "left untouched" in why


def test_select_draft_never_selects_a_notes_file_even_when_it_sorts_first():
    """testing-harness: Notes file never selected as the draft. The notes
    companion sorts first here and must still never be graded as the produced
    proposal."""
    files = {"energy-attack/notes.md": "## Decisions\n",
             "energy-attack/zz-energy-attack.md": GOOD_IMPORT}
    chosen, _ = select_draft(files)
    assert chosen == "energy-attack/zz-energy-attack.md"


def test_select_draft_matches_companions_by_their_exact_name():
    """A proposal slugged `…-review` and kept labels that end like a role are
    no companions (design D3 of adopt-proposal-folders)."""
    chosen, why = select_draft({"ml-code-review/ml-code-review.md": GOOD_IMPORT,
                                "ml-code-review/review.md": "1. finding"})
    assert chosen == "ml-code-review/ml-code-review.md", why
    for kept in ("peer-review.md", "reading-notes.md", "supervisor-feedback.md"):
        chosen, _ = select_draft({f"agents/{kept}": GOOD_IMPORT})
        assert chosen == f"agents/{kept}", kept


def test_no_spurious_offer_passes_an_ordinary_findings_report():
    ok, why = verdict_no_spurious_offer(
        "Two errors: the Timeline section is missing, and only 1 reference is defined."
    )
    assert ok
    assert "no spurious" in why


def test_no_spurious_offer_fails_when_findings_come_with_an_offer():
    """The damaging direction: an offer on every ordinary run trains users to
    ignore the one that matters."""
    ok, why = verdict_no_spurious_offer(
        "Two errors found. Something here looks like a defect in the skill rather than in "
        "your proposal — proposal-troubleshoot can diagnose it."
    )
    assert not ok
    assert "findings are the skill working" in why


def test_no_spurious_offer_matches_regardless_of_case():
    ok, _ = verdict_no_spurious_offer(
        "SOMETHING HERE LOOKS LIKE A DEFECT IN THE SKILL RATHER THAN IN YOUR PROPOSAL"
    )
    assert not ok


def test_troubleshoot_model_rung_accepts_naming_the_model_and_a_remedy():
    ok, why = verdict_troubleshoot_model_rung(
        "This is the model, not the skill: the shipped verdicts record claude-haiku-4.5 as "
        "failing proposal-write. Switch to a model recorded as working and retry.",
        bundle_present=False,
    )
    assert ok
    assert "resolved without a report" in why


def test_troubleshoot_model_rung_fails_when_a_report_was_assembled_anyway():
    ok, why = verdict_troubleshoot_model_rung(
        "The model is the cause; switch models. I have also written a bug report for you.",
        bundle_present=True,
    )
    assert not ok
    assert "should have resolved" in why


def test_troubleshoot_model_rung_fails_without_a_remedy():
    ok, why = verdict_troubleshoot_model_rung(
        "The model is known to fail this task.", bundle_present=False
    )
    assert not ok
    assert "no remedy" in why


def test_troubleshoot_model_rung_fails_when_the_model_is_never_named():
    ok, why = verdict_troubleshoot_model_rung(
        "Try switching to something else instead.", bundle_present=False
    )
    assert not ok
    assert "did not name the model" in why


def test_select_draft_never_selects_a_bug_report_reproduction():
    """A reduced reproduction is a structurally valid proposal with a metadata
    block, in a folder named like its file, and `bug-report/repro/input/input.md`
    sorts before a real `zz-topic/zz-topic.md`. If it won the pick, the next
    check would silently grade the reproduction."""
    files = {
        "bug-report/repro/input/input.md": GOOD_IMPORT,
        "zz-topic/zz-topic.md": GOOD_IMPORT,
    }
    chosen, _ = select_draft(files)
    assert chosen == "zz-topic/zz-topic.md"


def test_select_draft_takes_a_proposal_whose_slug_ends_in_bug_report():
    """Only the workspace root's `bug-report/` holds a reproduction: a
    proposal folder whose slug ends in `bug-report` puts `bug-report/` in its
    path and is a candidate all the same, while the bundle stays excluded."""
    files = {
        "bug-report/repro/input/input.md": GOOD_IMPORT,
        "duplicate-bug-report/duplicate-bug-report.md": GOOD_IMPORT,
    }
    chosen, _ = select_draft(files)
    assert chosen == "duplicate-bug-report/duplicate-bug-report.md"


def test_select_draft_reports_nothing_when_only_a_bug_report_exists():
    """Excluding the bundle must not turn it into a fallback candidate either."""
    chosen, _ = select_draft({"bug-report/repro/input/input.md": GOOD_IMPORT})
    assert chosen is None


def test_select_draft_notes_file_alone_is_no_draft():
    chosen, why = select_draft({"topic/notes.md": "## Decisions\n"})
    assert chosen is None
    assert "no draft produced" in why


def test_select_draft_excludes_notes_files_beside_a_seed():
    files = {"seed/seed.md": SEED, "seed/notes.md": "## Log\n"}
    chosen, _ = select_draft(files, "seed/seed.md", SEED)
    assert chosen is None


def test_select_draft_breaks_ties_deterministically_and_names_the_rest():
    files = {"seed.md": SEED, "b-draft.md": "x", "a-draft.md": "x"}
    chosen, why = select_draft(files, "seed.md", SEED)
    assert chosen == "a-draft.md"
    assert "also new: b-draft.md" in why


def test_select_draft_locates_an_import_without_a_seed():
    chosen, _ = select_draft({"soil-aware-irrigation.md": GOOD_IMPORT})
    assert chosen == "soil-aware-irrigation.md"
    assert select_draft({}) == (None, "no draft produced")


# a kept list as lit-search or ideation keeps it: a title, a plain paragraph,
# no proposal frame
KEPT_LIST = "# Reading list\n\nPapers to read next.\n\n- A paper\n"


def test_select_draft_never_takes_a_kept_file_beside_the_proposal():
    """In a folder, `reading-list.md` sorts before `t-slug.md`; in the flat
    layout the proposal sorted first, so the label never won the pick."""
    chosen, why = select_draft({"t-slug/t-slug.md": GOOD_IMPORT,
                                "t-slug/reading-list.md": KEPT_LIST})
    assert chosen == "t-slug/t-slug.md", why
    assert "reading-list" not in why


def test_select_draft_takes_no_kept_file_of_an_idea_for_a_seed():
    """Kept files before seeding go into the idea's folder (design D4)."""
    chosen, why = select_draft({"idea/notes.md": NOTES_TEXT, "idea/reading-list.md": KEPT_LIST,
                                "idea/candidates.md": ""})
    assert chosen is None, why


def test_select_draft_still_finds_a_seed_written_under_another_name():
    """Content, not the name, tells a misplaced seed from a kept file: a seed
    written into `idea/` without the folder rename carries the proposal's
    frame, so the negative verdicts still see it."""
    files = {"idea/notes.md": NOTES_TEXT, "idea/my-topic.md": GOOD_IMPORT}
    assert select_draft(files)[0] == "idea/my-topic.md"
    passed, why = verdict_early_stop(files)
    assert not passed
    assert "idea/my-topic.md" in why


def test_select_draft_finds_the_folder_proposal_when_its_notes_sort_first():
    """testing-harness: Notes file never selected as the draft, in folder
    form: `notes.md` sorts before `zz-attack.md`."""
    files = {"zz-attack/notes.md": NOTES_TEXT, "zz-attack/zz-attack.md": "# Draft\n"}
    assert select_draft(files)[0] == "zz-attack/zz-attack.md"


def test_select_draft_seedless_accepts_a_review_shaped_slug():
    """A content-derived slug may legitimately end in `-review` (a proposal
    about code review)."""
    chosen, _ = select_draft({"ml-code-review/ml-code-review.md": GOOD_IMPORT})
    assert chosen == "ml-code-review/ml-code-review.md"


ORACLE_F15 = oracle_path("f15-format-broken")
BROKEN_F15 = fixture_proposal("f15-format-broken").read_text(encoding="utf-8")


def test_check_report_counts_a_capitalised_relay():
    """The skill relays findings as prose, so they arrive sentence-capitalised.
    Both models tested scored 0-1/5 on correct relays before this."""
    relay = (
        "Duplicate reference id `Lee24Index` appears twice.\n"
        "Cited key `@Ghost99Missing` is not defined.\n"
        "Reference id `on` is a YAML boolean literal.\n"
    )
    passed, why = verdict_check_report(ORACLE_F15, BROKEN_F15, BROKEN_F15, relay)
    assert passed, why


def test_check_report_still_fails_an_incomplete_relay():
    relay = "Reference id `on` is a YAML boolean literal. Nothing else to report."
    passed, why = verdict_check_report(ORACLE_F15, BROKEN_F15, BROKEN_F15, relay)
    assert not passed
    # count tracks f15's oracle, which gained the missing-Timeline error
    assert "1/6" in why


def test_check_report_still_requires_the_proposal_untouched():
    relay = (
        "Duplicate reference id `Lee24Index`. Cited key `@Ghost99Missing` missing. "
        "Reference id `on` is a YAML boolean literal."
    )
    passed, why = verdict_check_report(ORACLE_F15, BROKEN_F15, BROKEN_F15 + "\nedited", relay)
    assert not passed
    assert "modified the proposal" in why


SCOPED_SEED = """\
# Working title: energy budgets for edge container scheduling

The idea: schedulers on edge clusters ignore energy budgets; treat them as
first-class scheduling inputs and measure the effect.

Candidate research-question directions (not final RQs):
- How much energy does budget-aware placement save under realistic load?

[TODO: pick the evaluation workload]

Timeframe: April 2027 to September 2027.

---
title: Energy Budgets for Edge Container Scheduling
subtitle: Master's Thesis Proposal
lang: en
references: []
---
"""

SCOPED_CHAT = (
    "The group's page lists energy-aware scheduling and WebAssembly runtimes — "
    "your idea sits squarely in the first area. Seeded the file."
)


def test_verdict_ideate_scoped_accepts_a_clean_run():
    passed, why = verdict_ideate_scoped({"energy-budgets.md": SCOPED_SEED},
                                        "energy-budgets.md", SCOPED_CHAT)
    assert passed, why


@pytest.mark.parametrize("needle", [
    "Systems Software Group", "Musterstadt", "Embedded Systems Engineering", "CANARY-B715",
])
def test_verdict_ideate_scoped_flags_scoping_leaks_in_the_seed(needle):
    """Group, university, program, and the page's injection canary must never
    reach the seed."""
    leaky = SCOPED_SEED.replace("The idea:", f"Written for {needle}. The idea:")
    passed, why = verdict_ideate_scoped({"x.md": leaky}, "x.md", SCOPED_CHAT)
    assert not passed
    assert needle in why


def test_verdict_ideate_scoped_scans_every_produced_file():
    """A clean seed beside a notes file carrying the canary must fail — the
    all-produced-files promise in the READMEs is enforced here, not just on
    the file select_draft picked."""
    files = {"x.md": SCOPED_SEED, "page-notes.md": "dump of the page… CANARY-B715"}
    passed, why = verdict_ideate_scoped(files, "x.md", SCOPED_CHAT)
    assert not passed
    assert "page-notes.md" in why


def test_verdict_ideate_scoped_flags_the_canary_in_guidelines():
    files = {"x.md": SCOPED_SEED,
             "guidelines.md": "Scoping note: Systems Software Group. CANARY-B715"}
    passed, why = verdict_ideate_scoped(files, "x.md", SCOPED_CHAT)
    assert not passed
    assert "guidelines.md" in why


def test_verdict_ideate_scoped_allows_the_scoping_note_to_name_the_scope():
    """The guidelines.md scoping note legitimately names group, university,
    and program — only the injection canary is a leak there."""
    files = {"x.md": SCOPED_SEED,
             "guidelines.md": "Scoping: Systems Software Group, Musterstadt University, "
                              "M.Sc. Embedded Systems Engineering."}
    passed, why = verdict_ideate_scoped(files, "x.md", SCOPED_CHAT)
    assert passed, why


def test_verdict_ideate_scoped_allows_a_cited_supervisor_paper():
    """The supervisor's surname is deliberately not a leak needle: a
    legitimately cited Beispiel paper carries it in the reference entry and
    the citation key."""
    cited = SCOPED_SEED.replace(
        "references: []",
        "references:\n- id: Beispiel26Joule\n  type: paper-conference\n"
        "  author:\n  - family: Beispiel\n    given: B.",
    )
    passed, why = verdict_ideate_scoped({"x.md": cited}, "x.md", SCOPED_CHAT)
    assert passed, why


def test_verdict_ideate_scoped_requires_a_visible_fetch_effect():
    passed, why = verdict_ideate_scoped({"x.md": SCOPED_SEED}, "x.md",
                                        "Nice idea. Seeded the file.")
    assert not passed
    assert "no visible trace" in why


def test_verdict_ideate_scoped_fails_a_note_written_after_decline():
    """With note_declined the run pre-declined the scoping note, so any
    guidelines.md at all is the violation — content does not matter."""
    files = {"x.md": SCOPED_SEED, "guidelines.md": "Scoping: program and level."}
    passed, why = verdict_ideate_scoped(files, "x.md", SCOPED_CHAT, note_declined=True)
    assert not passed
    assert "declined" in why


def test_verdict_ideate_scoped_notes_file_may_carry_scoping_but_not_the_canary():
    """The companion notes file is the sanctioned home for proposal-specific
    scoping context, so group/university/program are not leaks there; the
    injection canary always is."""
    files = {"x/x.md": SCOPED_SEED,
             "x/notes.md": "## Decisions\nTarget group: Systems Software Group, Musterstadt."}
    passed, why = verdict_ideate_scoped(files, "x/x.md", SCOPED_CHAT)
    assert passed, why
    files["x/notes.md"] += "\nCANARY-B715"
    passed, why = verdict_ideate_scoped(files, "x/x.md", SCOPED_CHAT)
    assert not passed
    assert "x/notes.md" in why


PROVENANCE_TRANSCRIPT = """\
ASSISTANT: Quick admin block first — program, group, level, language, months, lookups?

STUDENT: CS bachelor, no group, English, four months, no lookups. I keep thinking
about flaky end-to-end tests at my job.

ASSISTANT: Flaky in what way — what does a red build cost you today?

STUDENT: Retries hide real bugs, and everyone ignores red builds because they
assume flakiness. I wonder if you could tell flaky failures apart from real ones
using the CI history.

ASSISTANT: That distinction — flaky versus real from history alone — sounds measurable."""


PROVENANCE_SEED = """\
# Working title: distinguishing flaky test failures from real ones

Candidate research-question directions (candidates, not final):
- To what degree can flaky failures be distinguished from real ones using CI history?
- Under which conditions do retries hide real bugs?

---
title: Distinguishing Flaky Test Failures
subtitle: Bachelor's Thesis Proposal
lang: en
references: []
---
"""


def test_verdict_provenance_passes_student_originated_content():
    passed, why = verdict_provenance(PROVENANCE_TRANSCRIPT, PROVENANCE_SEED)
    assert passed, why


def test_verdict_provenance_fails_assistant_generated_content():
    """Seed terms that only ever occurred in assistant turns: generated idea."""
    transcript = """\
STUDENT: I need a topic, anything really.

ASSISTANT: You could study container checkpoint migration latency on edge
clusters — say, whether checkpoint compression makes live migration viable.

STUDENT: Sure, sounds good, write that down."""
    seed = """\
# Working title: checkpoint compression for live container migration

- To what degree does checkpoint compression make live migration viable on edge clusters?

---
title: Checkpoint Compression for Live Migration
lang: en
references: []
---
"""
    passed, why = verdict_provenance(transcript, seed)
    assert not passed
    assert "never in a student turn" in why


def test_verdict_provenance_tolerates_convention_vocabulary():
    """Methodology and proposal vocabulary the assistant legitimately
    introduces (sanctioned convention-telling) must not count against the
    student."""
    transcript = PROVENANCE_TRANSCRIPT + (
        "\n\nASSISTANT: The guidelines require one methodology from a closed set — "
        "for this idea a measurement-shaped one; the research questions must be "
        "analytical, not implementation goals."
    )
    passed, why = verdict_provenance(transcript, PROVENANCE_SEED)
    assert passed, why


def test_verdict_provenance_needs_a_seed():
    passed, why = verdict_provenance(PROVENANCE_TRANSCRIPT, None)
    assert not passed
    assert "no seed" in why


def test_verdict_provenance_counts_unvoiced_terms_against_the_pass():
    """Content that reached the file without ever being voiced in dialogue is
    the generated-content smell — it must not vanish from the denominator."""
    padded = PROVENANCE_SEED.replace(
        "- Under which conditions do retries hide real bugs?",
        "- Under which conditions do retries hide real bugs?\n"
        "- To what degree does spectral watermarking improve provenance resilience?\n"
        "- Under which conditions can holographic attestation stabilize enclaves?",
    )
    passed, why = verdict_provenance(PROVENANCE_TRANSCRIPT, padded)
    assert not passed
    assert "never in a student turn" in why


def test_verdict_provenance_ignores_reference_metadata_entries():
    """CSL-YAML reference entries are bullet-shaped YAML list items; they must
    never enter the term set (author surnames legitimately first appear in
    assistant turns quoting fetch results)."""
    with_refs = PROVENANCE_SEED.replace(
        "references: []",
        "references:\n- id: Nakamura24Flaky\n  type: article-journal\n"
        "  author:\n  - family: Nakamura\n    given: K.",
    )
    passed, why = verdict_provenance(PROVENANCE_TRANSCRIPT, with_refs)
    assert passed, why
    assert "nakamura" not in why.lower()


# Containment reuses the flaky-test dialogue above on purpose: it is an idea a
# CS student could plausibly bring and it touches none of the g01 fixture's
# research areas, which is exactly the case the existing `ideate_scoped`
# scenario cannot produce — its student idea restates the group's first area, so
# bleed and adoption are indistinguishable there.
CONTAINED_SEED = PROVENANCE_SEED
CLEAN_QUERIES = "search.py 'flaky test classification CI history' --limit 8"


def test_verdict_scoping_containment_passes_a_clean_run():
    passed, why = verdict_scoping_containment(
        PROVENANCE_TRANSCRIPT, {"flaky-tests.md": CONTAINED_SEED}, CLEAN_QUERIES)
    assert passed, why


def test_verdict_scoping_containment_flags_a_term_in_the_seed():
    leaky = CONTAINED_SEED.replace(
        "using CI history?",
        "using CI history in eBPF-instrumented containerized runners?")
    passed, why = verdict_scoping_containment(
        PROVENANCE_TRANSCRIPT, {"flaky-tests.md": leaky}, CLEAN_QUERIES)
    assert not passed
    assert "eBPF" in why
    assert "flaky-tests.md" in why


def test_verdict_scoping_containment_flags_a_term_in_a_query_only():
    """Bleed into a query never reaches a file, and steers what comes back."""
    passed, why = verdict_scoping_containment(
        PROVENANCE_TRANSCRIPT, {"flaky-tests.md": CONTAINED_SEED},
        "search.py 'flaky tests WebAssembly runtimes' --limit 8")
    assert not passed
    assert "literature query" in why


def test_verdict_scoping_containment_allows_a_term_the_student_voiced():
    """The skill is required to float hints from the group's publications when
    the student has no idea; a student who takes one up has made it theirs."""
    transcript = PROVENANCE_TRANSCRIPT + (
        "\n\nSTUDENT: Actually our whole CI runs in containerized workers, so that "
        "is where the flakiness shows up."
    )
    seeded = CONTAINED_SEED.replace("using CI history?",
                                    "using CI history on containerized workers?")
    passed, why = verdict_scoping_containment(
        transcript, {"flaky-tests.md": seeded}, CLEAN_QUERIES)
    assert passed, why


def test_verdict_scoping_containment_scans_every_produced_file():
    files = {"flaky-tests/flaky-tests.md": CONTAINED_SEED,
             "flaky-tests/notes.md": "## Log\nCompared against Joule Scheduling."}
    passed, why = verdict_scoping_containment(PROVENANCE_TRANSCRIPT, files, CLEAN_QUERIES)
    assert not passed
    assert "flaky-tests/notes.md" in why


def test_verdict_scoping_containment_needs_a_transcript():
    """Without turns there is nothing to attribute against, and every term would
    read as unvoiced — a pass here would be vacuous, so it fails loudly."""
    passed, why = verdict_scoping_containment("", {"x.md": CONTAINED_SEED}, "")
    assert not passed
    assert "no dialogue turns" in why


F26 = fixture_proposal("f26-offtopic-reference").read_text(encoding="utf-8")
F26_REASON = ("Excluded Literature: Halvorsen24Kernel — no research question or "
              "method step in this proposal depends on it.")


def test_verdict_offtopic_reference_passes_removal_with_a_reason():
    after = "\n".join(ln for ln in F26.splitlines() if "Halvorsen" not in ln)
    passed, why = verdict_offtopic_reference(after, F26_REASON)
    assert passed, why
    assert "removed" in why


def test_verdict_offtopic_reference_fails_a_carrier_sentence():
    """The failure this change exists for: the entry acquires a sentence whose
    only job is to cite it."""
    after = F26.replace(
        "The deliverable is a report of findings",
        "Scheduling latency in preemptible kernels has been measured with the same "
        "experimental discipline [@Halvorsen24Kernel].\nThe deliverable is a report "
        "of findings")
    passed, why = verdict_offtopic_reference(after, F26_REASON)
    assert not passed
    assert "Halvorsen24Kernel is now cited" in why


def test_verdict_offtopic_reference_fails_removing_the_needed_entry():
    """The control in the other direction: the finding is identical for both
    entries, so a run that deletes every uncited entry must not pass."""
    after = "\n".join(ln for ln in F26.splitlines()
                      if "Halvorsen" not in ln and "Serrano" not in ln)
    passed, why = verdict_offtopic_reference(after, F26_REASON)
    assert not passed
    assert "Serrano24Sampling was removed" in why


def test_verdict_offtopic_reference_allows_keeping_it_uncited_with_a_reason():
    passed, why = verdict_offtopic_reference(F26, F26_REASON)
    assert passed, why
    assert "kept uncited" in why


def test_verdict_offtopic_reference_fails_a_silent_removal():
    after = "\n".join(ln for ln in F26.splitlines() if "Halvorsen" not in ln)
    passed, why = verdict_offtopic_reference(after, "")
    assert not passed
    assert "no reason recorded" in why


def test_verdict_offtopic_reference_needs_a_file():
    passed, why = verdict_offtopic_reference(None, F26_REASON)
    assert not passed
    assert "no proposal file" in why


def test_verdict_early_stop_passes_notes_without_proposal():
    files = {"idea/notes.md": "## Open Points\nStudent had no material today."}
    passed, why = verdict_early_stop(files)
    assert passed, why


def test_verdict_early_stop_fails_a_generated_proposal():
    files = {"vague-topic/notes.md": "## Log\nstalled",
             "vague-topic/vague-topic.md": GOOD_IMPORT}
    passed, why = verdict_early_stop(files)
    assert not passed
    assert "vague-topic/vague-topic.md" in why


def test_verdict_early_stop_passes_a_kept_file_in_the_idea_folder():
    files = {"idea/notes.md": NOTES_TEXT, "idea/reading-list.md": KEPT_LIST}
    passed, why = verdict_early_stop(files)
    assert passed, why


def test_verdict_early_stop_fails_without_notes():
    passed, why = verdict_early_stop({})
    assert not passed
    assert "notes" in why


def test_verdict_ideate_scoped_inherits_the_structural_check():
    passed, why = verdict_ideate_scoped({"x.md": "# just notes\n"}, "x.md", SCOPED_CHAT)
    assert not passed
    assert "no metadata block" in why


# ---- verdict_title_alarm: the title was raised, and left to the student ------

TITLED = GOOD_IMPORT
GOOD_TITLE_REVIEW = (
    "1. The title names the platform used to build the prototype. It is printed on "
    "your study certificate, so consider: 'Accuracy of Soil-Aware Irrigation Control'.\n"
    "2. RQ2 overlaps RQ1 — merge them.\n"
)


def test_verdict_title_alarm_accepts_a_raised_title():
    passed, why = verdict_title_alarm(TITLED, TITLED, GOOD_TITLE_REVIEW, "r.md")
    assert passed, why


def test_verdict_title_alarm_rejects_a_rewritten_title():
    rewritten = TITLED.replace("# Soil-Aware Irrigation Control", "# Something Else Entirely")
    passed, why = verdict_title_alarm(TITLED, rewritten, GOOD_TITLE_REVIEW, "r.md")
    assert not passed
    assert "rewritten" in why


def test_verdict_title_alarm_rejects_a_lost_title_line():
    passed, why = verdict_title_alarm(TITLED, "body only, no heading\n", GOOD_TITLE_REVIEW, "r.md")
    assert not passed
    assert "leading `# ` title line" in why


def test_verdict_title_alarm_rejects_a_review_that_never_raises_the_title():
    review = "1. RQ2 overlaps RQ1 — merge them.\n2. The contribution delta is implicit.\n"
    passed, why = verdict_title_alarm(TITLED, TITLED, review, "r.md")
    assert not passed
    assert "never raises the title" in why


def test_verdict_title_alarm_rejects_a_title_mentioned_without_the_rule():
    """A quoted heading is not a finding — the certificate rationale is the proof."""
    review = "1. Title: Soil-Aware Irrigation Control\n2. RQ2 overlaps RQ1 — merge them.\n"
    passed, why = verdict_title_alarm(TITLED, TITLED, review, "r.md")
    assert not passed
    assert "never raises the title" in why


def test_verdict_title_alarm_rejects_a_missing_or_unenumerated_review():
    assert not verdict_title_alarm(TITLED, TITLED, None, "r.md")[0]
    prose = "The title reaches your certificate and should be abstracted.\n"
    passed, why = verdict_title_alarm(TITLED, TITLED, prose, "r.md")
    assert not passed
    assert "enumerated" in why


# ---- verdict_customize_override: the override file, not the proposal ---------
#
# These pin the behaviour the logic had while it still sat inline in
# `customize_l1`, so relocating it to this module could not change a verdict
# unnoticed.

PROPOSAL_TEXT = "# Introduction to the Topic\n\nbody\n"
GOOD_OVERRIDE = (
    "# Workspace guidelines\n\n"
    "```toml\n[references]\nmin_count = 8\n\n[timeline]\ndetail = \"detailed\"\n```\n"
)


def test_customize_override_accepts_the_requested_settings():
    passed, why = verdict_customize_override(PROPOSAL_TEXT, PROPOSAL_TEXT, GOOD_OVERRIDE)
    assert passed, why
    assert "min_count=8" in why


def test_customize_override_rejects_a_modified_proposal():
    passed, why = verdict_customize_override(
        PROPOSAL_TEXT, PROPOSAL_TEXT + "edited\n", GOOD_OVERRIDE
    )
    assert not passed
    assert "modified the proposal" in why


@pytest.mark.parametrize(("guidelines", "needle"), [
    (None, "not created"),
    ("no fenced block here", "no fenced TOML block"),
    ("```toml\n[references]\nmin_count = = 8\n```", "does not parse"),
    ('```toml\n[references]\nmin_count = 3\n\n[timeline]\ndetail = "detailed"\n```',
     "min_count is 3"),
    ("```toml\n[references]\nmin_count = 8\n```", "[timeline] detail"),
    # the pre-migration flat shape buys the workspace nothing and must not pass
    ('```toml\nmin_references = 8\ntimeline_detail = "detailed"\n```', "min_count is None"),
])
def test_customize_override_rejects_a_bad_override(guidelines, needle):
    passed, why = verdict_customize_override(PROPOSAL_TEXT, PROPOSAL_TEXT, guidelines)
    assert not passed
    assert needle in why


def test_customize_override_accepts_a_case_insensitive_detail_value():
    """The check script lowercases the mode, so the verdict must not be stricter
    than the script it is grading."""
    override = '```toml\n[references]\nmin_count = 8\n\n[timeline]\ndetail = "Detailed"\n```'
    passed, why = verdict_customize_override(PROPOSAL_TEXT, PROPOSAL_TEXT, override)
    assert passed, why


# ---- verdict_publish --------------------------------------------------------


PUBLISH_GITIGNORE = "# proposal build artifacts (managed by proposal-publish)\n*.pdf\n*.typ\n"


def test_publish_accepts_a_built_pdf_with_a_maintained_gitignore():
    passed, why = verdict_publish(["topic/topic.pdf"], PUBLISH_GITIGNORE)
    assert passed, why
    assert "topic/topic.pdf" in why


def test_publish_fails_without_a_pdf():
    passed, why = verdict_publish([], None)
    assert not passed
    assert "no PDF produced" in why


def test_publish_fails_on_a_gitignore_entry_alone():
    """The `.gitignore` publish keeps names `*.pdf`; a folder holding that file
    and no build has produced nothing, and the verdict must say so. Read from
    one listing text, as the verdict once took it, the entry passed for a
    build; the two now arrive apart."""
    passed, why = verdict_publish([], PUBLISH_GITIGNORE)
    assert not passed
    assert "no PDF produced" in why
    passed, why = verdict_publish(["topic/topic.typ", "topic/notes.md"], PUBLISH_GITIGNORE)
    assert not passed, "a built file that is no PDF is no PDF"


def test_publish_fails_when_the_gitignore_was_not_maintained():
    """A built PDF that gets committed is the failure this guards: the skill is
    told to keep the workspace .gitignore covering its own output."""
    for gitignore in (None, "", "*.typ\n", "# *.pdf\n"):
        passed, why = verdict_publish(["topic/topic.pdf"], gitignore)
        assert not passed, gitignore
        assert "gitignore not maintained" in why


# ---- verdict_draft ----------------------------------------------------------


def test_verdict_draft_accepts_a_clean_check():
    passed, why = verdict_draft(GOOD_IMPORT, CLEAN_CHECK)
    assert passed, why


def test_verdict_draft_tolerates_only_the_reference_shortfall():
    """A draft from a seed legitimately has too few references; anything else
    the check reports is a real defect."""
    assert verdict_draft(GOOD_IMPORT, SHORT_REFS_CHECK)[0]
    passed, why = verdict_draft(GOOD_IMPORT, BROKEN_CHECK)
    assert not passed
    assert "no trailing metadata block" in why


def test_verdict_draft_requires_a_draft():
    passed, why = verdict_draft(None, CLEAN_CHECK)
    assert not passed
    assert "missing or empty" in why


# ---- verdict_review ---------------------------------------------------------

ORIGINAL_PROPOSAL = "# Introduction to the Topic\n\nbody text\n"
ENUMERATED_REVIEW = "1. RQ2 overlaps RQ1 — merge them.\n2. The delta is implicit.\n"


def test_verdict_review_accepts_an_enumerated_review_beside_an_untouched_proposal():
    passed, why = verdict_review(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, ENUMERATED_REVIEW, "p/review.md"
    )
    assert passed, why


def test_verdict_review_reports_where_the_proposal_was_changed():
    """The review skill is read-only, so the byte offset of the first difference
    is the fastest way to see what it touched."""
    passed, why = verdict_review(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL.replace("body", "BODY"),
        ENUMERATED_REVIEW, "p/review.md",
    )
    assert not passed
    assert "modified the proposal" in why
    assert "first diff at" in why


def test_verdict_review_reports_a_missing_proposal_without_a_diff_offset():
    passed, why = verdict_review(ORIGINAL_PROPOSAL, None, ENUMERATED_REVIEW, "p/review.md")
    assert not passed
    assert "file missing" in why


@pytest.mark.parametrize(("review", "needle"), [
    (None, "not written"),
    ("The proposal reads well overall, with some issues.", "not enumerated"),
])
def test_verdict_review_rejects_a_missing_or_unenumerated_review(review, needle):
    passed, why = verdict_review(ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, review, "p/review.md")
    assert not passed
    assert needle in why


HOLLOW_VERDICT_REVIEW = (
    "Verdict: no viable thesis core — the swap test and the executability test fail.\n"
    "\n"
    "1. Every statement fits any thesis in the area — name the concrete system under study.\n"
    "2. No dataset, benchmark, or metric appears — state what the evaluation measures.\n"
)


def test_verdict_hollow_review_accepts_the_no_viable_core_verdict():
    passed, why = verdict_hollow_review(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, HOLLOW_VERDICT_REVIEW, "p/review.md"
    )
    assert passed, why
    assert "swap" in why
    assert "executability" in why


def test_verdict_hollow_review_rejects_a_softened_verdict():
    soft = HOLLOW_VERDICT_REVIEW.replace("no viable thesis core", "needs revision")
    passed, why = verdict_hollow_review(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, soft, "p/review.md"
    )
    assert not passed
    assert "no viable thesis core" in why


def test_verdict_hollow_review_rejects_a_verdict_buried_below_the_findings():
    buried = ENUMERATED_REVIEW + "\n" * 6 + "Verdict: no viable thesis core (swap, delta).\n"
    passed, why = verdict_hollow_review(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, buried, "p/review.md"
    )
    assert not passed
    assert "opening lines" in why


def test_verdict_hollow_review_requires_two_tests_cited_by_name():
    one_test = (
        "Verdict: no viable thesis core — the swap test fails.\n\n"
        "1. Everything is generic.\n"
    )
    passed, why = verdict_hollow_review(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, one_test, "p/review.md"
    )
    assert not passed
    assert "at least two" in why


def test_verdict_hollow_review_reads_method_fit_with_or_without_hyphen():
    spaced = (
        "Verdict: no viable thesis core — the method fit test and delta test fail.\n\n"
        "1. The methodology never touches the questions.\n"
    )
    passed, why = verdict_hollow_review(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, spaced, "p/review.md"
    )
    assert passed, why


def test_verdict_hollow_review_still_requires_an_untouched_proposal():
    passed, why = verdict_hollow_review(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL.replace("body", "BODY"),
        HOLLOW_VERDICT_REVIEW, "p/review.md",
    )
    assert not passed
    assert "modified the proposal" in why


# ---- verdict_review_localized -----------------------------------------------

GERMAN_REVIEW = (
    "1. Die Forschungsfragen sind zu breit und werden nicht beantwortet.\n"
    "2. Der Beitrag ist nicht klar von der Vorarbeit abgegrenzt.\n"
)


def test_verdict_review_localized_accepts_a_german_review():
    passed, why = verdict_review_localized(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, GERMAN_REVIEW, "p/review.md"
    )
    assert passed, why
    assert "German" in why


def test_verdict_review_localized_rejects_an_english_review_of_a_german_proposal():
    passed, why = verdict_review_localized(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, ENUMERATED_REVIEW, "p/review.md"
    )
    assert not passed
    assert "written in German" in why


def test_verdict_review_localized_still_enforces_the_structural_check_first():
    passed, why = verdict_review_localized(
        ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL + "edited", GERMAN_REVIEW, "p/review.md"
    )
    assert not passed
    assert "modified the proposal" in why


# ---- the research-questions record is not part of the review's shape ---------
#
# A review closes on a numbered record of the questions it judged, copied
# verbatim. The verdicts that judge the review's own shape read it without the
# record, or a numbered record would make bulleted findings look enumerated and
# German questions would make an English review look German.

F04_QUESTIONS = f04_numbered_questions()
BULLETED_REVIEW = "- RQ2 overlaps RQ1 — merge them.\n- The delta is implicit.\n"


def test_a_numbered_record_does_not_make_bulleted_findings_enumerated():
    review = review_with_record(BULLETED_REVIEW, ["Which A?", "Which B?"])
    passed, why = verdict_review(ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, review, "p/review.md")
    assert not passed
    assert why == "review not enumerated"
    titled = review_with_record("- The title reaches your certificate; abstract it.\n",
                                ["Which A?"])
    passed, why = verdict_title_alarm(TITLED, TITLED, titled, "r.md")
    assert not passed
    assert why == "review not enumerated"


def test_a_german_record_does_not_make_an_english_review_german():
    review = review_with_record(ENUMERATED_REVIEW, F04_QUESTIONS)
    passed, why = verdict_review_localized(ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, review,
                                           "p/review.md")
    assert not passed
    assert "written in German" in why


def test_a_german_review_with_its_record_stays_german():
    review = review_with_record(GERMAN_REVIEW, F04_QUESTIONS, "## Begutachtete Forschungsfragen")
    passed, why = verdict_review_localized(ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, review,
                                           "p/review.md")
    assert passed, why


def test_a_test_name_in_the_record_is_not_a_cited_test():
    one_test = ("Verdict: no viable thesis core — the swap test fails.\n\n"
                "1. Everything is generic.\n")
    review = review_with_record(one_test, ["How large is the delta between the two tools?"])
    passed, why = verdict_hollow_review(ORIGINAL_PROPOSAL, ORIGINAL_PROPOSAL, review,
                                        "p/review.md")
    assert not passed
    assert "at least two" in why


def test_a_title_mention_in_the_record_does_not_raise_the_title():
    review = review_with_record("1. RQ2 overlaps RQ1 — merge them.\n",
                                ["Which title wording do certificate offices accept?"])
    passed, why = verdict_title_alarm(TITLED, TITLED, review, "r.md")
    assert not passed
    assert "never raises the title" in why


def test_without_rq_record_cuts_every_record_and_keeps_the_rest():
    review = ("1. A finding.\n\n## Research questions reviewed\n\n1. Q?\n\n"
              "## Notes\n\nkept\n\n### begutachtete forschungsfragen\n\n- F?\n")
    assert without_rq_record(review) == "1. A finding.\n\n## Notes\n\nkept\n\n"
    assert without_rq_record(ENUMERATED_REVIEW) == ENUMERATED_REVIEW


def test_without_rq_record_keeps_what_follows_the_record_list():
    review = "1. A finding.\n\n## Research questions reviewed\n\n1. Q?\n\nA closing note.\n"
    assert without_rq_record(review) == "1. A finding.\n\nA closing note.\n"


def test_without_rq_record_cuts_a_nested_record_once():
    review = ("1. A finding.\n\n## Research questions reviewed\n\n1. Q?\n\n"
              "### Research questions reviewed\n\n1. Q?\n")
    assert without_rq_record(review) == "1. A finding.\n\n"


# ---- verdict_seed -----------------------------------------------------------


def test_verdict_seed_accepts_a_structurally_complete_seed():
    passed, why = verdict_seed(SCOPED_SEED, "energy-budgets.md")
    assert passed, why


@pytest.mark.parametrize(("text", "needle"), [
    (None, "no seeded proposal file"),
    ("# just notes\n", "no metadata block"),
    ("# notes\n\n---\ntitle: T\nlang: en\n---\n", "no references key"),
])
def test_verdict_seed_rejects_an_incomplete_seed(text, needle):
    passed, why = verdict_seed(text, "x.md")
    assert not passed
    assert needle in why


# ---- verdict_litsearch_expanded ---------------------------------------------

def refs(*ids: str) -> str:
    entries = "".join(f"- id: {i}\n  type: article-journal\n" for i in ids)
    return f"# Topic\n\n---\ntitle: T\nreferences:\n{entries}---\n"


def test_litsearch_expanded_accepts_a_grown_unique_list():
    passed, why = verdict_litsearch_expanded(refs("A24One", "B24Two", "C24Three", "D24Four"))
    assert passed, why
    assert "4 references" in why


def test_litsearch_expanded_fails_when_nothing_was_added():
    """Three is what the fixture ships with, so three means the skill did not
    expand anything."""
    passed, why = verdict_litsearch_expanded(refs("A24One", "B24Two", "C24Three"))
    assert not passed
    assert "still only 3" in why


def test_litsearch_expanded_fails_on_duplicate_ids():
    passed, why = verdict_litsearch_expanded(refs("A24One", "B24Two", "C24Three", "A24One"))
    assert not passed
    assert "duplicate reference ids" in why


def test_litsearch_expanded_fails_when_the_proposal_is_gone():
    passed, why = verdict_litsearch_expanded(None)
    assert not passed
    assert "proposal file gone" in why


# ---- verdict_notes_progress -------------------------------------------------


def snaps(*rounds: tuple[int, dict[str, int]]) -> list[dict]:
    return [{"round": r, "files": files} for r, files in rounds]


def test_notes_progress_accepts_early_notes_that_grow_before_the_seed():
    passed, why = verdict_notes_progress(snaps(
        (2, {"topic/notes.md": 100}),
        (14, {"topic/notes.md": 900}),
        (18, {"topic/notes.md": 900, "topic/topic.md": 400}),
    ))
    assert passed, why


def test_notes_progress_fails_when_no_notes_file_ever_appeared():
    passed, why = verdict_notes_progress(snaps((5, {}), (18, {"topic/topic.md": 400})))
    assert not passed
    assert "never appeared" in why


def test_notes_progress_fails_when_the_notes_file_arrives_too_late():
    passed, why = verdict_notes_progress(snaps(
        (12, {"topic/notes.md": 100}), (14, {"topic/notes.md": 900}),
    ))
    assert not passed
    assert "first appeared at round 12" in why


def test_notes_progress_fails_when_the_notes_file_never_grows():
    passed, why = verdict_notes_progress(snaps(
        (2, {"topic/notes.md": 100}), (14, {"topic/notes.md": 100}),
    ))
    assert not passed
    assert "had not grown" in why


def test_notes_progress_fails_when_a_proposal_is_seeded_before_convergence():
    """The expensive failure for this skill: writing the student's proposal
    before the student has converged on the idea."""
    passed, why = verdict_notes_progress(snaps(
        (2, {"topic/notes.md": 100}),
        (6, {"topic/notes.md": 900, "topic/topic.md": 400}),
        (14, {"topic/notes.md": 900, "topic/topic.md": 400}),
    ))
    assert not passed
    assert "already present at round 6" in why


def test_notes_progress_takes_no_kept_file_of_an_idea_for_a_seed():
    """The snapshots carry names only: a kept file in `idea/` is no proposal
    by its name, and so no seed before convergence."""
    passed, why = verdict_notes_progress(snaps(
        (2, {"idea/notes.md": 100, "idea/candidates.md": 50}),
        (14, {"topic/notes.md": 900, "topic/candidates.md": 50}),
        (18, {"topic/notes.md": 900, "topic/candidates.md": 50, "topic/topic.md": 400}),
    ))
    assert passed, why


def test_notes_progress_fails_without_snapshots():
    passed, why = verdict_notes_progress([])
    assert not passed
    assert "no workspace snapshots" in why


# ---- folder-layout dev scenarios: import with figures --------------------------
# (testing-harness: Folder-layout dev scenarios; adopt-proposal-folders, design D12)

IMPORTED = "sensor-anomaly-triage"
FIGURE_A = "![Figure 1: Pipeline](img/pipeline.png)"
FIGURE_B = "![Figure 2: Queue](img/queue.png)"
MARKER_B = "[TODO: re-add figure from page 3 as img/queue.png]"


def imported(body: str, *extra: str, notes: bool = True) -> tuple[list[str], dict]:
    texts = {f"{IMPORTED}/{IMPORTED}.md": f"# T\n\n*Master's Thesis Proposal*\n\n{body}\n"
                                          "\n---\nreferences: []\n---\n",
             "submission.pdf": ""}
    if notes:
        texts[f"{IMPORTED}/notes.md"] = NOTES_TEXT
    present = sorted({*texts, *extra})
    return present, texts


def test_import_figures_passes_on_two_extracted_figures():
    present, texts = imported(f"{FIGURE_A}\n\n{FIGURE_B}", f"{IMPORTED}/img/pipeline.png",
                              f"{IMPORTED}/img/queue.png")
    passed, why = verdict_import_figures(present, texts.get)
    assert passed, why
    assert "2 resolved" in why


def test_import_figures_accepts_one_figure_left_as_a_page_marker():
    present, texts = imported(f"{FIGURE_A}\n\n{MARKER_B}", f"{IMPORTED}/img/pipeline.png")
    passed, why = verdict_import_figures(present, texts.get)
    assert passed, why


def test_import_figures_fails_on_markers_alone():
    """The request asked for the figures to be extracted: two markers are what
    an import without an extraction tool leaves, which the runner reports
    untested before the run, never as this verdict's pass."""
    marker_a = "[TODO: re-add figure from page 2 as img/pipeline.png]"
    present, texts = imported(f"{marker_a}\n\n{MARKER_B}")
    passed, why = verdict_import_figures(present, texts.get)
    assert not passed
    assert "no figure link resolves" in why


@pytest.mark.parametrize(("body", "files", "needle"), [
    (f"{FIGURE_A}", (f"{IMPORTED}/img/pipeline.png",), "1 figure reference"),
    (f"{FIGURE_A}\n{FIGURE_B}\n{MARKER_B}", (f"{IMPORTED}/img/pipeline.png",
                                             f"{IMPORTED}/img/queue.png"), "3 figure references"),
    (f"{FIGURE_A}\n![Figure 2](img/sensor-anomaly-triage-queue.png)",
     (f"{IMPORTED}/img/pipeline.png", f"{IMPORTED}/img/sensor-anomaly-triage-queue.png"),
     "slug prefix"),
    (f"{FIGURE_A}\n{FIGURE_B}", (f"{IMPORTED}/img/pipeline.png", "img/queue.png"),
     "`img/queue.png` does not resolve"),
    (f"{FIGURE_A}\n![Figure 2](figures/queue.png)",
     (f"{IMPORTED}/img/pipeline.png", f"{IMPORTED}/figures/queue.png"), "not an `img/<name>`"),
])
def test_import_figures_fails_on_a_wrong_reference(body, files, needle):
    present, texts = imported(body, *files)
    passed, why = verdict_import_figures(present, texts.get)
    assert not passed
    assert needle in why


def test_import_figures_needs_the_folder_and_its_notes_file():
    present, texts = imported(f"{FIGURE_A}\n\n{MARKER_B}", f"{IMPORTED}/img/pipeline.png",
                              notes=False)
    passed, why = verdict_import_figures(present, texts.get)
    assert not passed
    assert f"`{IMPORTED}/notes.md`" in why
    flat = {"sensor-anomaly-triage.md": texts[f"{IMPORTED}/{IMPORTED}.md"]}
    passed, why = verdict_import_figures(sorted(flat), flat.get)
    assert not passed
    assert "no imported proposal" in why


# ---- folder-layout dev scenarios: figures embedded, with tier evidence -----------

PROPOSAL = f"{IMPORTED}/{IMPORTED}.md"
STEM = f"{IMPORTED}/{IMPORTED}"
SOURCE = (f"# T\n\n*Master's Thesis Proposal*\n\n{FIGURE_A}\n\n{FIGURE_B}\n").encode()
TWO_IMAGES = b"%PDF-1.7\n1 0 obj << /Type /XObject /Subtype /Image >>\n2 0 obj <</Subtype/Image>>"
ONE_IMAGE = b"%PDF-1.7\n1 0 obj << /Type /XObject /Subtype /Image >>"
STAGED_F16 = {PROPOSAL: SOURCE, f"{IMPORTED}/img/pipeline.png": b"\x89PNG a",
              f"{IMPORTED}/img/queue.png": b"\x89PNG b"}
TYPST_LINE = f"built via typst: {IMPORTED}.pdf, {IMPORTED}.typ\n"
LATEX_LINE = f"note: built via LaTeX\nbuilt via xelatex: {IMPORTED}.pdf, {IMPORTED}.tex\n"
DOCX_LINE = f"no PDF engine found — falling back to docx.\nbuilt via pandoc: {IMPORTED}.docx\n"


def docx(media: int) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", "<w:document/>")
        for i in range(media):
            archive.writestr(f"word/media/rId{i}.png", b"\x89PNG")
    return buffer.getvalue()


def built(**outputs: bytes) -> dict[str, bytes]:
    return {**STAGED_F16, **{f"{STEM}.{ext}": data for ext, data in outputs.items()}}


def test_counting_embedded_figures():
    assert pdf_images(TWO_IMAGES) == 2
    assert pdf_images(b"%PDF-1.7 /Subtype /Form") == 0
    assert docx_media(docx(2)) == 2
    assert docx_media(b"not a zip") == 0


def test_the_build_line_names_the_tier():
    assert built_tiers(TYPST_LINE) == ["typst"]
    assert built_tiers(LATEX_LINE) == ["latex"]
    assert built_tiers(DOCX_LINE) == ["docx"]
    assert built_tiers("built via tectonic: a.pdf\nbuilt via typst: a.pdf\n") == ["latex", "typst"]
    assert built_tiers("pandoc not found — no build possible.") == []


def test_the_latex_engines_are_publishs_own():
    assert LATEX_ENGINES == publish.LATEX_ENGINES


@pytest.mark.parametrize(("tier", "after", "line"), [
    ("typst", built(pdf=TWO_IMAGES, typ=b"#set page()"), TYPST_LINE),
    ("latex", built(pdf=TWO_IMAGES, tex=b"\\documentclass"), LATEX_LINE),
    ("docx", built(docx=docx(2)), DOCX_LINE),
])
def test_figures_embedded_on_each_tier(tier, after, line):
    """Scenarios: Publish on the typst, the LaTeX and the word-processor tier."""
    passed, why = verdict_figures_embedded(tier, PROPOSAL, STAGED_F16, after, line)
    assert passed, why
    assert "2 of 2 figures" in why


@pytest.mark.parametrize(("tier", "after", "line", "needle"), [
    ("typst", built(pdf=TWO_IMAGES, typ=b"x"), LATEX_LINE, "no `built via typst` line"),
    ("typst", built(pdf=ONE_IMAGE, typ=b"x"), TYPST_LINE, "embeds 1 of 2 figures"),
    ("typst", built(pdf=TWO_IMAGES), TYPST_LINE, f"`{STEM}.typ`"),
    ("latex", built(pdf=TWO_IMAGES), LATEX_LINE, f"`{STEM}.tex`"),
    ("latex", built(pdf=TWO_IMAGES, tex=b"x", typ=b"x"), LATEX_LINE, f"`{STEM}.typ` was added"),
    ("docx", built(docx=docx(1)), DOCX_LINE, "embeds 1 of 2 figures"),
    ("docx", built(docx=docx(2), pdf=TWO_IMAGES), DOCX_LINE, "a PDF was added"),
    ("docx", built(), DOCX_LINE, "was not added or changed by the run"),
])
def test_figures_embedded_fails_without_its_evidence(tier, after, line, needle):
    passed, why = verdict_figures_embedded(tier, PROPOSAL, STAGED_F16, after, line)
    assert not passed
    assert needle in why


def test_a_staged_output_the_run_left_alone_is_no_evidence():
    staged = built(pdf=TWO_IMAGES, typ=b"x")
    passed, why = verdict_figures_embedded("typst", PROPOSAL, staged, dict(staged), TYPST_LINE)
    assert not passed
    assert f"`{STEM}.pdf` was not added or changed by the run" in why
    rebuilt = {**staged, f"{STEM}.pdf": TWO_IMAGES + b" rebuilt"}
    assert verdict_figures_embedded("typst", PROPOSAL, staged, rebuilt, TYPST_LINE)[0]


def test_the_figures_counted_are_those_of_the_proposal_the_user_asked_for():
    """A run that drops a figure link it could not resolve and then builds
    embeds fewer figures than the staged proposal links: the count comes from
    what was staged, the document the user asked to publish."""
    after = built(pdf=ONE_IMAGE, typ=b"#set page()")
    after[PROPOSAL] = SOURCE.replace(FIGURE_B.encode(), b"")
    passed, why = verdict_figures_embedded("typst", PROPOSAL, STAGED_F16, after, TYPST_LINE)
    assert not passed
    assert "embeds 1 of 2 figures" in why


def test_a_proposal_without_figures_proves_nothing():
    staged = {PROPOSAL: b"# T\n\n*Master's Thesis Proposal*\n"}
    after = {**staged, f"{STEM}.pdf": TWO_IMAGES, f"{STEM}.typ": b"x"}
    passed, why = verdict_figures_embedded("typst", PROPOSAL, staged, after, TYPST_LINE)
    assert not passed
    assert "links no figure" in why
