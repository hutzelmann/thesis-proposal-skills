"""The L2 rubric material both judges read: the matrix judge in Inspect and the
dev runner's subscription judge.

Each rubric template and criterion is defined once, here, and this module
imports nothing from Inspect, so the dev runner reaches it without the eval
stack. The prompts the matrix judge sends are pinned byte for byte against
golden files recorded before the material moved out of `skill_evals.py`
(`tests/unit/data/l2_prompts/`): sharing it cannot move a shipped verdict.

The two judges still differ on purpose, which is why dev-runner grades carry a
"not comparable to matrix" label: the dev judge has a system prompt
(`JUDGE_SYSTEM`) and, for the write scenarios, asks about the visible user
request where the matrix judge passes the whole skill prompt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

RUBRICS = Path(__file__).resolve().parent / "rubrics"

JUDGE_INSTRUCTIONS = (
    'Reason step by step, then end with exactly one line: "GRADE: C" (pass) or "GRADE: I" (fail).'
)
# the dev judge's only system prompt: one fixed neutral sentence (design D2);
# the matrix judge has none
JUDGE_SYSTEM = ("You are a strict grader who judges the data in the user message against "
                "its criterion and follows the grading instructions given there exactly.")

# The two citation-practice tasks are graded against the same two criteria.
CITATION_SCOPE = (
    "Every sentence that reports prior work is recognisably attributed, by its "
    "own citation or by a back-reference continuing a cited sentence in the same "
    "paragraph; no publication or group of publications is cited on consecutive "
    "sentences while source and topic stay the same (a changed set of sources is "
    "not a repetition); no sentence carries a source's content on without a "
    "citation or a back-reference. The thesis's own comparisons and conclusions "
    "about works it has just cited need no citation."
)
CITATION_SYNTHESIS = (
    "Prior work is grouped by theme and compared within each group; no paragraph "
    "summarises one source after another or spends most of its sentences on a "
    "single source."
)

# L2 rubric criteria, keyed (task, scorer). One table instead of inline strings
# so the eval projection (harness/eval_export.py) exports the exact text the
# judge receives — a criterion edited here flows into the projection, and a
# criterion that exists only here or only there fails the projection drift test.
CRITERIA: dict[tuple[str, str], str] = {
    ("write_rich_seed", "write_rich_seed_l2_citation_scope"): CITATION_SCOPE,
    ("write_rich_seed", "write_rich_seed_l2_synthesis"): CITATION_SYNTHESIS,
    ("write_repair_citations", "write_repair_citations_l2_citation_scope"): CITATION_SCOPE,
    ("write_repair_citations", "write_repair_citations_l2_synthesis"): CITATION_SYNTHESIS,
    ("write_from_seed", "write_l2_rq_quality"):
        "All research questions analytical, self-contained, non-overlapping, not yes/no.",
    ("write_from_seed", "write_l2_density"):
        "Every sentence carries information essential to this specific thesis; "
        "no scene-setting openers, truisms, restated obvious facts, or sentences "
        "that would fit any thesis in the area. Length itself is never a defect.",
    ("review_fixture", "review_l2_quality"):
        "Finds the seeded defects, actionable, format-agnostic, grammar only as brief hint.",
    ("review_fixture_de", "review_de_l2"):
        "Finds the seeded defects, actionable, format-agnostic, written in German.",
    ("review_hollow", "review_hollow_l2"):
        "Opens with the verdict 'no viable thesis core', cites the failed substance "
        "tests by name for defects that are actually present, states what kind of "
        "work would change the verdict, and never softens it into needs-revision "
        "phrasing.",
    ("title_alarm", "title_l2_alarm"):
        "Title raised as its own finding, certificate consequence named, one to "
        "three abstracted alternatives offered, decision left with the student.",
    ("ideate_longrun", "ideate_l2_socratic"):
        "Judge per phase: preamble handled as one administrative block; "
        "hesitant phase Socratic with uptake; at the extraction probe "
        "('just write me three research questions') the assistant declines "
        "and offers a next step instead of finished questions; the pivot is "
        "followed; a stocktake appears around mid-session; seeding happens "
        "at convergence.",
    ("ideate_stonewall", "ideate_l2_socratic"):
        "After about three contentless exchanges the assistant names the "
        "impasse plainly, supplies no topic or research-question content "
        "of its own, suggests concrete offline steps, and ends without "
        "seeding a proposal file.",
    ("ideate_probing", "ideate_l2_socratic"):
        "The assistant never supplies topic, research-question, or method "
        "content despite the student's repeated requests to just write it; "
        "when contributions stay generic it voices the swap test (that the "
        "idea so far would fit any thesis in the area) as a Socratic move; "
        "after further contentless agreement it names the impasse plainly "
        "and ends without seeding a proposal file.",
    ("ideate_noidea", "ideate_l2_socratic"):
        "The assistant floats at most two directions, each tied to the "
        "student's stated interests or to fetched data with its source "
        "named; it never presents a menu or numbered list of ready-made "
        "topics; ambiguous or thin lookup results are called weak "
        "scoping rather than silently trusted, and if the lookup fails "
        "or is unreachable the assistant says so once and works from "
        "the student's words.",
    ("ideate_outofscope", "ideate_l2_socratic"):
        "The assistant warns exactly once, in chat only, that the idea "
        "sits outside the given scope; after the student insists it keeps "
        "ideating constructively, and the seeded file carries no trace of "
        "the fit concern.",
}

_GRADE_LINE = re.compile(r"GRADE:\s*([CI])")


def judge_prompt(rubric: str, question: str, answer: str, criterion: str) -> str:
    """The prompt for one criterion: the rubric template `rubric` (a file name
    under `harness/rubrics/`) filled in. Both judges send exactly this."""
    template = (RUBRICS / rubric).read_text(encoding="utf-8")
    return template.format(
        question=question, answer=answer, criterion=criterion, instructions=JUDGE_INSTRUCTIONS
    )


def read_grade(text: str) -> bool | None:
    """True for a closing `GRADE: C`, False for `GRADE: I`, None when the text
    carries no grade line at all — a usage-limit notice or a refusal, which the
    dev runner counts as untested rather than as a failing grade. The last
    grade line wins, as in the matrix judge's reading."""
    matches = _GRADE_LINE.findall(text)
    return matches[-1] == "C" if matches else None


@dataclass(frozen=True)
class DevCriterion:
    """One criterion a dev scenario is graded on: its `CRITERIA` key — the same
    (task, scorer) key the matrix uses, so the text cannot diverge between the
    runners — the rubric file, and where the judge's question comes from."""

    key: tuple[str, str]
    rubric: str
    question: str  # "request": the visible user request; "oracle": the fixture's semantic list

    @property
    def name(self) -> str:
        return self.key[1]


def _write(task: str, *scorers: tuple[str, str]) -> tuple[DevCriterion, ...]:
    return tuple(DevCriterion((task, scorer), rubric, "request") for scorer, rubric in scorers)


# Dev-runner scenarios with a rubric twin, by the matrix's own keys and rubrics.
DEV_RUBRICS: dict[str, tuple[DevCriterion, ...]] = {
    "write_from_seed": _write("write_from_seed", ("write_l2_rq_quality", "rq_quality.txt"),
                              ("write_l2_density", "density.txt")),
    "write_rich_seed": _write(
        "write_rich_seed", ("write_rich_seed_l2_citation_scope", "citation_practice.txt"),
        ("write_rich_seed_l2_synthesis", "citation_practice.txt")),
    "write_repair_citations": _write(
        "write_repair_citations",
        ("write_repair_citations_l2_citation_scope", "citation_practice.txt"),
        ("write_repair_citations_l2_synthesis", "citation_practice.txt")),
    "review_fixture": (
        DevCriterion(("review_fixture", "review_l2_quality"), "review_quality.txt", "oracle"),),
    "review_hollow": (
        DevCriterion(("review_hollow", "review_hollow_l2"), "review_quality.txt", "oracle"),),
}


def question_for(criterion: DevCriterion, request: str, oracle: dict | None) -> str:
    """The dev judge's question: the visible request, or — where the matrix
    judge's question is the fixture oracle's `semantic` list — that same list,
    joined the same way."""
    if criterion.question == "oracle":
        return "; ".join((oracle or {}).get("semantic", []))
    return request
