"""L0: the rubric material both judges read (testing-harness spec: Subscription
text roles (dev runner), Rubrics).

`harness/l2_rubrics.py` is the one definition of every rubric template,
criterion and the judge prompt. The matrix judge's prompts are pinned byte for
byte against golden files recorded before the material moved
(`data/l2_prompts/`), so sharing it with the dev runner cannot move a shipped
verdict.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import l2_rubrics
import pytest
from l2_rubrics import CRITERIA, DEV_RUBRICS, RUBRICS, judge_prompt, question_for, read_grade

GOLDEN = Path(__file__).resolve().parent / "data" / "l2_prompts"
INPUTS = json.loads((GOLDEN / "inputs.json").read_text(encoding="utf-8"))
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.mark.parametrize("golden", sorted(GOLDEN.glob("*.txt")), ids=lambda p: p.stem)
def test_judge_prompt_matches_the_golden_prompt(golden):
    prompt = judge_prompt(golden.name, INPUTS["question"], INPUTS["answer"], INPUTS["criterion"])
    assert prompt.encode("utf-8") == golden.read_bytes()


def test_every_rubric_file_has_a_golden_prompt():
    assert sorted(p.name for p in GOLDEN.glob("*.txt")) == sorted(
        p.name for p in RUBRICS.glob("*.txt"))


@pytest.mark.parametrize(("text", "grade"), [
    ("Reasoning.\nGRADE: C", True),
    ("Reasoning.\nGRADE: I", False),
    ("GRADE: C at first, then on reflection\nGRADE: I", False),
    ("GRADE: I\nrevised: GRADE: C", True),
    ("I cannot grade this — usage limit reached.", None),
    ("", None),
])
def test_read_grade_distinguishes_pass_fail_and_no_grade(text, grade):
    assert read_grade(text) is grade


def test_every_dev_criterion_is_a_matrix_criterion_with_an_existing_rubric():
    for scenario, entries in DEV_RUBRICS.items():
        assert entries, scenario
        for entry in entries:
            assert entry.key in CRITERIA, (scenario, entry.key)
            assert (RUBRICS / entry.rubric).is_file(), (scenario, entry.rubric)
            assert entry.name == entry.key[1]


def test_dev_rubrics_cover_exactly_the_scenarios_with_a_rubric_twin():
    assert set(DEV_RUBRICS) == {"write_from_seed", "write_rich_seed", "write_repair_citations",
                                "review_fixture", "review_hollow", "review_ready",
                                "review_dependency", "review_converge"}
    assert {e.name for e in DEV_RUBRICS["write_from_seed"]} == {
        "write_l2_rq_quality", "write_l2_density"}
    for scenario in ("write_rich_seed", "write_repair_citations"):
        assert [CRITERIA[e.key] for e in DEV_RUBRICS[scenario]] == [
            l2_rubrics.CITATION_SCOPE, l2_rubrics.CITATION_SYNTHESIS]


def test_write_scenarios_ask_about_the_visible_request():
    oracle = {"semantic": ["never used for a write scenario"]}
    for scenario in ("write_from_seed", "write_rich_seed", "write_repair_citations"):
        for entry in DEV_RUBRICS[scenario]:
            assert entry.question == "request"
            assert question_for(entry, "Please draft it.", oracle) == "Please draft it."


def test_review_scenarios_ask_about_the_oracle_semantic_list():
    """The same list, joined the same way, as the matrix review scorers."""
    for scenario, fixture in (("review_fixture", "f05-slr-interviews"),
                              ("review_hollow", "f22-hollow-generic"),
                              ("review_ready", "f28-open-decisions"),
                              ("review_dependency", "f29-doubtful-dependency"),
                              ("review_converge", "w09-revised-round")):
        oracle = json.loads((FIXTURES / fixture / "expected.json").read_text(encoding="utf-8"))
        [entry] = DEV_RUBRICS[scenario]
        assert entry.question == "oracle"
        assert question_for(entry, "ignored request", oracle) == "; ".join(oracle["semantic"])


def test_judge_system_is_one_fixed_sentence():
    assert l2_rubrics.JUDGE_SYSTEM.count(".") == 1
    assert l2_rubrics.JUDGE_SYSTEM.endswith(".")


def test_module_imports_nothing_from_inspect():
    tree = ast.parse(Path(l2_rubrics.__file__).read_text(encoding="utf-8"))
    imported = [
        alias.name for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    ] + [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not [name for name in imported if name.split(".")[0] == "inspect_ai"]
