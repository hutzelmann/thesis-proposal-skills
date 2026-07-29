"""Spike task S1: minimal end-to-end eval proving the authoritative OpenRouter path.

Model under test writes a research question; a judge model grades whether it is
analytical rather than an implementation goal — the core L2 rubric dimension.
"""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate

JUDGE_MODEL = "openrouter/anthropic/claude-haiku-4.5"

GRADING_TEMPLATE = """You are grading a research question for a thesis proposal.

[BEGIN DATA]
[Question]: {question}
[Submission]: {answer}
[Criterion]: {criterion}
[END DATA]

A research question passes only if it is analytical — it asks "to what degree",
"to what extent", "under which conditions", or compares/evaluates — and would
require analysis or measurement to answer. It fails if it is an implementation
goal ("how can X be implemented/designed/built") or answerable yes/no.

{instructions}
"""


@task
def rq_quality() -> Task:
    return Task(
        dataset=[
            Sample(
                input=(
                    "State exactly one research question for a Master's thesis "
                    "about machine learning support for code review. "
                    "Reply with only the research question."
                ),
                target=(
                    "An analytical research question requiring analysis, comparison, "
                    "or evaluation — not an implementation goal, not yes/no answerable."
                ),
            )
        ],
        solver=generate(),
        scorer=model_graded_qa(template=GRADING_TEMPLATE, model=JUDGE_MODEL),
    )
