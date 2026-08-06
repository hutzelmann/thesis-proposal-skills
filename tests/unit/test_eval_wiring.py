"""L0: the eval harness is wired correctly — without spending a metered call.

`harness/skill_evals.py` only ever executes under `inspect eval`, so coverage
omits it and no test can observe a scorer's verdict without paying for a model
run. What a test *can* observe is the wiring: that every task builds, and that
its scorers keep the names they had.

The names are the reason this file exists. `harness/support.py` decides whether
a scorer counts toward a model-support cell by looking for `l1` in its
registered name (`scorer_counts`), so a scorer that quietly loses its marker
changes published model verdicts with nothing failing. The scorer factory made
that name an argument rather than a function name, which is exactly the kind of
indirection this pins down.
"""

import pytest
import skill_evals
from inspect_ai._util.registry import registry_info

# The full task set with the scorer names each one registers. Update this map
# in the same change that adds or renames a scorer — never to make a test pass.
EXPECTED_SCORERS = {
    "write_from_seed": ["write_l1", "write_l2_rq_quality"],
    "review_fixture": ["review_l1", "review_l2_quality", "no_spurious_offer"],
    "title_alarm": ["title_l1", "title_l2_alarm"],
    "ideate_longrun": [
        "ideate_l1_seed", "ideate_l1_notes_progress",
        "ideate_l1_provenance", "ideate_l2_socratic",
    ],
    "ideate_stonewall": ["ideate_l1_early_stop", "ideate_l2_socratic"],
    "ideate_noidea": ["ideate_l2_socratic"],
    "ideate_outofscope": ["ideate_l2_socratic"],
    "check_report": ["check_report_l1"],
    "customize_override": ["customize_l1"],
    "publish_build": ["publish_l1"],
    "import_messy": ["import_l1"],
    "litsearch_expand": ["litsearch_l1"],
    "review_fixture_de": ["review_de_l1", "review_de_l2"],
    "check_report_hardened": ["check_report_l1"],
    "troubleshoot_model_rung": ["troubleshoot_model_rung_l1", "no_spurious_offer"],
}


@pytest.mark.parametrize("task_name", sorted(EXPECTED_SCORERS))
def test_task_builds_with_the_expected_scorers(task_name):
    task = getattr(skill_evals, task_name)()
    names = [registry_info(s).name for s in task.scorer]
    assert names == EXPECTED_SCORERS[task_name]


@pytest.mark.parametrize("task_name", sorted(EXPECTED_SCORERS))
def test_task_stages_exactly_one_sample(task_name):
    task = getattr(skill_evals, task_name)()
    assert len(task.dataset) == 1
    assert task.dataset[0].files, "no files staged into the sandbox"


def test_l1_scorers_keep_the_marker_the_classifier_reads():
    """`support.scorer_counts` excludes L1 scorers on tasks listed in
    `excluded_l1`. A deterministic scorer without `l1` in its name would keep
    counting on those tasks and fail models the exclusion was meant to spare."""
    deterministic = {
        name for names in EXPECTED_SCORERS.values() for name in names
        if not name.endswith(("_l2", "_l2_quality", "_l2_alarm", "_l2_rq_quality", "_l2_socratic"))
    }
    unmarked = {
        name for name in deterministic
        if "l1" not in name and name != "no_spurious_offer"
    }
    assert not unmarked, f"deterministic scorers missing the `l1` marker: {sorted(unmarked)}"
