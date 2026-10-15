"""L0: citation-practice verdicts from harness/l1_checks.py (no model calls)."""

from pathlib import Path

import check
import claude_runner
import l1_checks
from fixture_paths import fixture_proposal
from helpers import write_proposal
from l1_checks import (
    repeated_citation_runs,
    verdict_citation_repair,
    verdict_citation_runs,
    verdict_cited_draft,
    verdict_repaired_draft,
)

METADATA = """
## References

---
references:
- id: Alder24Flaky
  type: article-journal
  title: Never Cited In The Body @Alder24Flaky
---
"""


def proposal(body: str) -> str:
    head = "# Title\n\n*Master's Thesis Proposal*\n\n## Introduction to the Topic\n\n"
    return f"{head}{body}\n{METADATA}"


def test_same_key_on_adjacent_sentences_fails_with_its_line():
    text = proposal(
        "Flaky tests fail without a code change [@Alder24Flaky].\n"
        "Most of them depend on timing [@Alder24Flaky]."
    )
    passed, why = verdict_citation_runs(text)
    assert not passed
    assert "line 8: Alder24Flaky" in why


def test_repetition_inside_one_line_counts():
    text = proposal("Flaky tests fail at random [@Alder24Flaky]. They cost time [@Alder24Flaky].")
    assert repeated_citation_runs(text) == [(7, ("Alder24Flaky",))]


def test_identical_group_on_adjacent_sentences_fails():
    text = proposal(
        "Reruns hide flakiness [@Alder24Flaky; @Brandt25Rerun].\n"
        "Quarantine hides it too [@Brandt25Rerun; @Alder24Flaky]."
    )
    assert repeated_citation_runs(text) == [(8, ("Alder24Flaky", "Brandt25Rerun"))]


def test_source_switch_passes():
    """[4] then [4, 7] is a change of source, which the guidance asks to cite."""
    text = proposal(
        "@Alder24Flaky classify flaky tests by root cause.\n"
        "Timing dominates in two independent samples [@Alder24Flaky; @Brandt25Rerun].\n"
        "Reruns are the usual response [@Brandt25Rerun]."
    )
    passed, why = verdict_citation_runs(text)
    assert passed, why
    assert "3 cited sentences, 2 adjacent cited pairs" in why


def test_paragraph_break_resets_the_comparison():
    text = proposal(
        "Flaky tests fail without a code change [@Alder24Flaky].\n\n"
        "Their dominant cause is timing [@Alder24Flaky]."
    )
    assert verdict_citation_runs(text)[0]


def test_bullets_do_not_hide_a_repetition_but_headings_reset():
    """Turning over-cited sentences into bullet items must not pass the task;
    a heading still starts a fresh comparison."""
    text = proposal(
        "Flaky tests are common [@Alder24Flaky].\n"
        "- Timing is the main cause [@Alder24Flaky]\n"
        "- Network access is the second [@Alder24Flaky]\n"
        "## Contribution to the State-of-the-Art\n"
        "Reruns hide them [@Alder24Flaky]."
    )
    assert [line for line, _ in repeated_citation_runs(text)] == [8, 9]


def test_uncited_sentence_between_breaks_adjacency():
    text = proposal(
        "@Alder24Flaky classify flaky tests.\n"
        "They find timing to be the main cause.\n"
        "Reruns are the usual response [@Alder24Flaky]."
    )
    assert verdict_citation_runs(text)[0]


def test_locators_abbreviations_and_wrapped_lines_keep_a_repetition_visible():
    text = proposal(
        "Rivera et al. report flaky reruns [@Alder24Flaky, p. 3].\n"
        "Most reruns, e.g. those on CI, hide\n"
        "timing faults [@Alder24Flaky, S. 4]."
    )
    assert [line for line, _ in repeated_citation_runs(text)] == [8]


def test_metadata_block_and_code_are_ignored():
    text = proposal("Annotations like `@Alder24Flaky` are code.\nTests use `@Alder24Flaky` too.")
    assert repeated_citation_runs(text) == []


def test_minimum_cited_guards_a_vacuous_pass():
    text = proposal("Nothing here cites anything.")
    passed, why = verdict_citation_runs(text, min_cited=5)
    assert not passed
    assert "proves nothing" in why


def test_missing_file_fails():
    assert not verdict_citation_runs(None)[0]
    assert not verdict_citation_repair("", None)[0]


BEFORE = proposal(
    "Flaky tests fail without a code change [@Alder24Flaky].\n"
    "Most of them depend on timing [@Alder24Flaky].\n"
    "Reruns hide them [@Brandt25Rerun]."
)


def test_repair_passes_when_repetition_goes_and_sources_stay():
    after = proposal(
        "@Alder24Flaky show that flaky tests fail without a code change.\n"
        "Most of the failures they classify depend on timing.\n"
        "Reruns hide them [@Brandt25Rerun]."
    )
    passed, why = verdict_citation_repair(BEFORE, after)
    assert passed, why


def test_repair_fails_when_a_source_loses_every_citation():
    after = proposal(
        "Flaky tests fail without a code change.\n"
        "Most of them depend on timing.\n"
        "Reruns hide them [@Brandt25Rerun]."
    )
    passed, why = verdict_citation_repair(BEFORE, after)
    assert not passed
    assert "no longer cited anywhere: Alder24Flaky" in why


def test_repair_fails_when_the_repetition_stays():
    passed, why = verdict_citation_repair(BEFORE, BEFORE)
    assert not passed
    assert "repeat the previous sentence's citation" in why


F27 = fixture_proposal("f27-citation-runs").read_text(encoding="utf-8")
W08 = fixture_proposal("w08-rich-seed").read_text(encoding="utf-8")


def test_f27_carries_all_three_shapes():
    """The fixture is the repair task's input; if it stopped over-citing, the
    task would pass any run that leaves it alone."""
    runs = repeated_citation_runs(F27)
    keys = {k for _, group in runs for k in group}
    assert {"Halloran24Update", "Vasquez23Semver", "Ito24Breaking", "Morandi25Breakage"} <= keys
    assert len(runs) == 9


def test_f27_untouched_fails_the_repair():
    passed, why = verdict_citation_repair(F27, F27)
    assert not passed
    assert "9 sentence(s)" in why


def test_w08_seed_itself_repeats_nothing():
    """List items are blocks of their own, so the seed's anchor list is not a
    run — the temptation is in the notes, not in the seed's own citations."""
    assert repeated_citation_runs(W08) == []


# A repair of f27 the way the guidance asks for it: each run opened with the
# author-in-text form, findings carried in words, the source switch kept.
F27_REPAIRS = {
    "Dependency-update bots open a pull request whenever a library a project depends on "
    "publishes a new version [@Halloran24Update].\n"
    "Most projects merge these pull requests without review once the build passes "
    "[@Halloran24Update].\n"
    "The bots reduced the median age of outdated dependencies by 40 % in the projects that "
    "adopted them [@Halloran24Update].\n"
    "At the same time, one update in eight broke the build or the tests of the receiving "
    "project [@Halloran24Update].":
    "@Halloran24Update find that most projects merge the pull requests of dependency-update "
    "bots without review once the build passes.\n"
    "In their sample, the bots cut the median age of outdated dependencies by 40 %, while one "
    "update in eight broke the build or the tests of the receiving project.",
    "A minor or patch release regularly removes or changes public interfaces "
    "[@Vasquez23Semver; @Ito24Breaking].\n"
    "Projects therefore cannot rely on the version number to decide which updates are safe "
    "to merge [@Vasquez23Semver; @Ito24Breaking].":
    "Both studies find minor and patch releases that remove or change public interfaces, so "
    "projects cannot rely on the version number to decide which updates are safe to merge.",
    "The classifier uses removed exports, changed function signatures, and changed default "
    "values as features [@Morandi25Breakage].\n"
    "It achieved an F1 score of 0.71 on held-out updates from the projects it was trained on "
    "[@Morandi25Breakage].\n"
    "Its F1 score dropped to 0.52 on projects outside the training set [@Morandi25Breakage].\n"
    "The evaluation did not use the receiving project's own build history "
    "[@Morandi25Breakage].":
    "Their features are removed exports, changed function signatures, and changed default "
    "values, and their F1 score falls from 0.71 within the training projects to 0.52 outside "
    "them; the receiving project's own build history plays no part.",
}


def repaired_f27() -> str:
    text = F27
    for before, after in F27_REPAIRS.items():
        assert before in text, before[:60]
        text = text.replace(before, after)
    return text


def run_verdict(name, tmp_path, edit=None, new_file=None):
    scenario = claude_runner.SCENARIOS[name]
    claude_runner.stage(scenario, tmp_path)
    if edit is not None:
        (tmp_path / scenario["proposal"]).write_text(edit, encoding="utf-8")
    if new_file is not None:  # a fresh proposal, in a folder of its own
        write_proposal(tmp_path, "drafted", new_file)
    return claude_runner.verdict(name, scenario, tmp_path, chat="")


def test_repair_scenario_passes_a_cued_repair(tmp_path):
    passed, why = run_verdict("write_repair_citations", tmp_path, edit=repaired_f27())
    assert passed, why
    assert "every source still cited" in why


def test_repair_scenario_fails_an_untouched_draft(tmp_path):
    passed, why = run_verdict("write_repair_citations", tmp_path)
    assert not passed
    assert "left untouched" in why


def test_repair_scenario_fails_deletion(tmp_path):
    stripped = F27.replace(" [@Halloran24Update]", "")
    passed, why = run_verdict("write_repair_citations", tmp_path, edit=stripped)
    assert not passed
    assert "no longer cited anywhere: Halloran24Update" in why


def test_rich_seed_scenario_judges_the_produced_draft(tmp_path):
    passed, why = run_verdict("write_rich_seed", tmp_path, new_file=repaired_f27())
    assert passed, why
    assert "created drafted/drafted.md" in why


def test_rich_seed_scenario_fails_repetition_in_the_draft(tmp_path):
    passed, why = run_verdict("write_rich_seed", tmp_path, new_file=F27)
    assert not passed
    assert "repeat the previous sentence's citation" in why


CLEAN_CHECK = "## Verified mechanically — no errors\n"
BROKEN_CHECK = "- ERROR: required section missing: `Timeline`\n"


def test_verdict_cited_draft_needs_both_halves():
    assert verdict_cited_draft(repaired_f27(), CLEAN_CHECK)[0]
    passed, why = verdict_cited_draft(repaired_f27(), BROKEN_CHECK)
    assert not passed
    assert "check errors" in why
    passed, why = verdict_cited_draft(F27, CLEAN_CHECK)
    assert not passed
    assert "repeat the previous sentence's citation" in why


def test_verdict_cited_draft_refuses_a_draft_that_barely_cites():
    passed, why = verdict_cited_draft(proposal("One claim [@Alder24Flaky]."), CLEAN_CHECK)
    assert not passed
    assert "proves nothing" in why


def test_verdict_splits_with_the_shipped_check_script():
    """The verdict and the `citation-repeated` warning a writer sees share one
    implementation: l1_checks loads the sync source of check.py by path."""
    shipped = Path(__file__).resolve().parents[2] / "skills/proposal-check/scripts/check.py"
    assert Path(l1_checks.CHECK_SCRIPT.__file__).resolve() == shipped


def test_verdict_and_warning_agree_on_the_fixtures():
    for text in (F27, W08, repaired_f27()):
        body, meta = check.split_proposal(text)
        warned = check.rule_repeated_citations(
            check.build_context(body, meta, check.load_structure(None), {}))
        assert len(warned) == len(repeated_citation_runs(text))


def test_verdict_repaired_draft_needs_both_halves():
    assert verdict_repaired_draft(F27, repaired_f27(), CLEAN_CHECK)[0]
    assert not verdict_repaired_draft(F27, repaired_f27(), BROKEN_CHECK)[0]
    passed, why = verdict_repaired_draft(F27, F27.replace(" [@Ruiz25Dataset]", ""), CLEAN_CHECK)
    assert not passed
    assert "no longer cited anywhere: Ruiz25Dataset" in why
