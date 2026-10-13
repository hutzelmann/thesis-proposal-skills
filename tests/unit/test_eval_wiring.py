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

import asyncio
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest
import skill_evals
import support
from helpers import shipped_registry
from inspect_ai._util.registry import registry_info

# The full task set with the scorer names each one registers. Update this map
# in the same change that adds or renames a scorer — never to make a test pass.
EXPECTED_SCORERS = {
    "write_from_seed": ["write_l1", "write_l2_rq_quality", "write_l2_density"],
    "write_rich_seed": [
        "write_rich_seed_l1", "write_rich_seed_l2_citation_scope",
        "write_rich_seed_l2_synthesis",
    ],
    "write_repair_citations": [
        "write_repair_citations_l1", "write_repair_citations_l2_citation_scope",
        "write_repair_citations_l2_synthesis",
    ],
    "review_fixture": ["review_l1", "review_l2_quality", "no_spurious_offer"],
    "review_hollow": ["review_hollow_l1", "review_hollow_l2", "no_spurious_offer"],
    "title_alarm": ["title_l1", "title_l2_alarm"],
    "ideate_longrun": [
        "ideate_l1_seed", "ideate_l1_notes_progress",
        "ideate_l1_provenance", "ideate_l2_socratic",
    ],
    "ideate_stonewall": ["ideate_l1_early_stop", "ideate_l2_socratic"],
    "ideate_probing": ["ideate_l1_early_stop", "ideate_l2_socratic"],
    "ideate_noidea": ["ideate_l2_socratic"],
    "ideate_outofscope": ["ideate_l2_socratic"],
    "check_report": ["check_report_l1"],
    "customize_override": ["customize_l1"],
    "publish_build": ["publish_l1"],
    "import_messy": ["import_l1"],
    "reverse_from_harvest": ["reverse_l1"],
    "litsearch_expand": ["litsearch_l1"],
    "review_fixture_de": ["review_de_l1", "review_de_l2"],
    "check_report_compound": ["check_report_l1"],
    "check_report_hardened": ["check_report_l1"],
    "troubleshoot_model_rung": ["troubleshoot_model_rung_l1", "no_spurious_offer"],
    "supervise_feedback": [
        "supervise_l1_feedback", "supervise_l1_points", "supervise_l1_tier",
        "supervise_l1_no_personal_data", "supervise_l1_pointers",
        "supervise_l1_closing", "supervise_l1_literature",
        "supervise_l1_substance_only", "supervise_l1_markup", "supervise_l1_locators",
    ],
    "review_ready": ["review_ready_l1", "review_ready_l2"],
    "review_dependency": ["review_dependency_l1", "review_dependency_l2"],
    "review_converge": ["review_converge_l1", "review_converge_l2"],
    "supervise_ready": [
        "supervise_l1_feedback", "supervise_l1_points", "supervise_l1_tier",
        "supervise_l1_pointers", "supervise_l1_closing", "supervise_l1_markup",
        "supervise_ready_l1_block",
    ],
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
        if not name.endswith(
            ("_l2", "_l2_quality", "_l2_alarm", "_l2_rq_quality", "_l2_socratic", "_l2_density",
             "_l2_citation_scope", "_l2_synthesis")
        )
    }
    unmarked = {
        name for name in deterministic
        if "l1" not in name and name != "no_spurious_offer"
    }
    assert not unmarked, f"deterministic scorers missing the `l1` marker: {sorted(unmarked)}"


# ---------- baseline arm wiring (testing-harness spec) ------------------------

REGISTRY = shipped_registry()


def test_judge_and_persona_come_from_the_registry_roles():
    """The module holds no model ID of its own: both defaults resolve through
    `support.role_model` over the registry, each override on its own role."""
    judge = support.role_model(REGISTRY.roles, "judge", os.environ)
    persona = support.role_model(REGISTRY.roles, "persona", os.environ)
    resolved = (skill_evals.JUDGE_MODEL, skill_evals.PERSONA_MODEL)
    assert resolved == (judge, persona)


@pytest.mark.usefixtures("routable_openrouter")
def test_role_models_stay_unrouted_beside_a_routed_model_under_test():
    """Judge and persona prompts are one-shot and keep their serving (testing-
    harness spec: Prompt caching on Anthropic matrix rows), so neither a provider
    pin nor a cache breakpoint may reach them. The eval builds each from its
    bare role ID, and Inspect memoizes on config and model arguments, so even
    when the model under test shares the judge's ID and is routed, the role gets
    a distinct, unrouted Model. Without the pin, the `marker` wrapper leaves its
    requests alone (test_openrouter_cache.py pins the request body)."""
    import re

    import matrix
    from inspect_ai.model import get_model

    src = Path(skill_evals.__file__).read_text(encoding="utf-8")
    assert re.findall(r"get_model\(([^)]*)\)", src) == ["JUDGE_MODEL", "PERSONA_MODEL"]
    assert not re.search(r"routing_for|extra_body|cache_control", src)
    rows = {m.id: m for m in REGISTRY.models}
    for role_id in {REGISTRY.roles.judge, REGISTRY.roles.persona}:
        # a held role (priced by `[role_prices]`, no roster row) shares no model
        # under test's ID, so only its own Model is checked
        row = rows.get(role_id)
        routed = None if row is None else matrix.build_model(
            row, support.routing_for(row, support.CACHE_MECHANISM))
        role = get_model(role_id)
        if routed is not None and row.family == support.PINNED_FAMILY:
            assert routed.model_args["provider"], "an Anthropic row under test is routed"
            assert role is not routed
        assert role.config.extra_body is None
        assert "provider" not in role.model_args


def test_dialogue_tasks_reject_the_baseline_parameter():
    """The registry's dialogue list and the builders' signatures are the same
    fact twice; this test keeps them from drifting apart."""
    for task_name in REGISTRY.tasks.dialogue:
        with pytest.raises(TypeError):
            getattr(skill_evals, task_name)(baseline=True)


# ---------- matrix judge prompt parity (add-dev-runner-judge, design D6) -------

GOLDEN = Path(__file__).resolve().parent / "data" / "l2_prompts"
GOLDEN_INPUTS = json.loads((GOLDEN / "inputs.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("golden", sorted(GOLDEN.glob("*.txt")), ids=lambda p: p.stem)
def test_matrix_judge_sends_exactly_the_golden_prompt(golden, monkeypatch):
    """The rubric material is shared with the dev runner; the matrix judge must
    keep sending the bytes it sent before the sharing existed, or shipped
    verdicts move with no rubric edit under review."""
    sent: list[tuple[str, str]] = []

    class FakeJudge:
        def __init__(self, model_id: str):
            self.model_id = model_id

        async def generate(self, prompt: str):
            sent.append((self.model_id, prompt))
            return SimpleNamespace(completion="Reasoning.\nGRADE: C")

    monkeypatch.setattr(skill_evals, "get_model", FakeJudge)
    passed, _ = asyncio.run(skill_evals.judge(
        golden.name, GOLDEN_INPUTS["question"], GOLDEN_INPUTS["answer"],
        GOLDEN_INPUTS["criterion"]))
    assert passed
    [(model_id, prompt)] = sent
    assert model_id == skill_evals.JUDGE_MODEL
    assert prompt.encode("utf-8") == golden.read_bytes()


def test_golden_prompts_cover_every_rubric_file():
    rubrics = {p.name for p in (skill_evals.REPO / "harness" / "rubrics").glob("*.txt")}
    assert {p.name for p in GOLDEN.glob("*.txt")} == rubrics


def test_single_turn_tasks_build_a_skill_free_baseline():
    eligible = [
        t for t in (*REGISTRY.tasks.matrix, *REGISTRY.tasks.extended)
        if t not in REGISTRY.tasks.dialogue
    ]
    assert eligible, "no baseline-eligible task found"
    for task_name in eligible:
        task = getattr(skill_evals, task_name)(baseline=True)
        prompt = task.dataset[0].input
        assert "SKILL INSTRUCTIONS" not in prompt, f"{task_name}: baseline still carries the skill"
        assert "User request:" in prompt
