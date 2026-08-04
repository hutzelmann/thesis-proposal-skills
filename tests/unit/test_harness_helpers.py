"""L0: pure scoring helpers from harness/l1_checks.py (no model calls)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "harness"))

import pytest  # noqa: E402
from l1_checks import (  # noqa: E402
    disallowed_errors,
    is_enumerated_review,
    parse_grade,
    select_draft,
    verdict_check_report,
    verdict_early_stop,
    verdict_ideate_scoped,
    verdict_import,
    verdict_provenance,
)

GOOD_IMPORT = """\
# Introduction to the Topic

Irrigation schedules ignore soil data [@Rivera23Survey].
@Tanaka24Lora measured LoRa range in field conditions.

---
title: Soil-Aware Irrigation Control
lang: en
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
    out = "- ERROR: only 1 references — at least 3 required\n- ERROR: forbidden section: `Work Plan`"
    assert disallowed_errors(out, ("references — at least",)) == [
        "- ERROR: forbidden section: `Work Plan`"
    ]
    assert disallowed_errors(out) and len(disallowed_errors(out)) == 2


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


def test_verdict_import_accepts_a_clean_import():
    passed, why = verdict_import(GOOD_IMPORT, CLEAN_CHECK, "soil-aware-irrigation.md")
    assert passed, why
    assert "soil-aware-irrigation.md" in why


def test_verdict_import_requires_a_produced_file():
    passed, why = verdict_import(None)
    assert not passed
    assert "no proposal file produced" in why


@pytest.mark.parametrize("mutation,needle", [
    (lambda t: t.replace("lang: en", "lang: en\nmatriculation: 00000000"), "00000000"),
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
        "seed.md": SEED,
        "guidelines.md": "override",
        "seed-review.md": "1. finding",
        "seed-handout.md": "handout",
    }
    chosen, why = select_draft(files, "seed.md", SEED)
    assert chosen is None
    assert "left untouched" in why


def test_select_draft_never_selects_a_notes_file_even_when_it_sorts_first():
    """`aa-topic.notes.md` sorts before `zz-topic.md`; the notes companion must
    still never be graded as the produced proposal."""
    files = {"aa-topic.notes.md": "## Decisions\n", "zz-topic.md": GOOD_IMPORT}
    chosen, _ = select_draft(files)
    assert chosen == "zz-topic.md"


def test_select_draft_notes_file_alone_is_no_draft():
    chosen, why = select_draft({"topic.notes.md": "## Decisions\n"})
    assert chosen is None
    assert "no draft produced" in why


def test_select_draft_excludes_notes_files_beside_a_seed():
    files = {"seed.md": SEED, "seed.notes.md": "## Log\n"}
    chosen, _ = select_draft(files, "seed.md", SEED)
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


def test_select_draft_seedless_accepts_a_review_shaped_slug():
    """A content-derived slug may legitimately end in `-review.md` (a proposal
    about code review); the artifact exclusion only applies beside a seed."""
    chosen, _ = select_draft({"ml-code-review.md": GOOD_IMPORT})
    assert chosen == "ml-code-review.md"


ORACLE_F15 = REPO / "tests" / "fixtures" / "f15-format-broken" / "expected.json"
BROKEN_F15 = (REPO / "tests" / "fixtures" / "f15-format-broken" / "broken-format.md").read_text()


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
    files = {"x.md": SCOPED_SEED,
             "x.notes.md": "## Decisions\nTarget group: Systems Software Group, Musterstadt."}
    passed, why = verdict_ideate_scoped(files, "x.md", SCOPED_CHAT)
    assert passed, why
    files["x.notes.md"] += "\nCANARY-B715"
    passed, why = verdict_ideate_scoped(files, "x.md", SCOPED_CHAT)
    assert not passed
    assert "x.notes.md" in why


PROVENANCE_TRANSCRIPT = """\
ASSISTANT: Quick admin block first — program, group, level, language, months, lookups?

STUDENT: CS bachelor, no group, English, four months, no lookups. I keep thinking about flaky end-to-end tests at my job.

ASSISTANT: Flaky in what way — what does a red build cost you today?

STUDENT: Retries hide real bugs, and everyone ignores red builds because they assume flakiness. I wonder if you could tell flaky failures apart from real ones using the CI history.

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

ASSISTANT: You could study container checkpoint migration latency on edge clusters — say, whether checkpoint compression makes live migration viable.

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


def test_verdict_early_stop_passes_notes_without_proposal():
    files = {"vague-topic.notes.md": "## Open Points\nStudent had no material today."}
    passed, why = verdict_early_stop(files)
    assert passed, why


def test_verdict_early_stop_fails_a_generated_proposal():
    files = {"vague-topic.notes.md": "## Log\nstalled", "vague-topic.md": GOOD_IMPORT}
    passed, why = verdict_early_stop(files)
    assert not passed
    assert "vague-topic.md" in why


def test_verdict_early_stop_fails_without_notes():
    passed, why = verdict_early_stop({})
    assert not passed
    assert "notes" in why


def test_verdict_ideate_scoped_inherits_the_structural_check():
    passed, why = verdict_ideate_scoped({"x.md": "# just notes\n"}, "x.md", SCOPED_CHAT)
    assert not passed
    assert "no metadata block" in why
