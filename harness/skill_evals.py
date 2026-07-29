"""L1/L2 skill evals over the fixture corpus (testing-harness spec).

Each task stages a fixture workspace plus the skill's reference material into
a sandbox, lets the model under test act on a user request with bash/editor
tools, then scores:
- L1 (deterministic): expected artifacts exist, the check script's verdict
  matches tolerance, the proposal was (not) modified as the skill demands.
- L2 (rubric): a judge model grades semantic quality via harness/rubrics/.

Run (model under test is Inspect's --model):
  uv run inspect eval harness/skill_evals.py@review_fixture \
      --model openrouter/deepseek/deepseek-v4-flash --log-dir logs/evals
Judge override: JUDGE_MODEL env (default openrouter/anthropic/claude-haiku-4.5).
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import get_model
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer
from inspect_ai.solver import TaskState, basic_agent, system_message
from inspect_ai.tool import bash, text_editor
from inspect_ai.util import sandbox

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
FIXTURES = REPO / "tests" / "fixtures"
RUBRICS = Path(__file__).resolve().parent / "rubrics"

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "openrouter/anthropic/claude-haiku-4.5")
JUDGE_INSTRUCTIONS = (
    'Reason step by step, then end with exactly one line: "GRADE: C" (pass) or "GRADE: I" (fail).'
)

# allowed residual check errors for a draft written from a nearly-empty seed
DRAFT_ALLOWED_ERRORS = ("references — at least",)


# ---------- helpers (pure, unit-tested) --------------------------------------

def disallowed_errors(check_output: str, allowed: tuple[str, ...] = ()) -> list[str]:
    lines = [l for l in check_output.splitlines() if l.startswith("- ERROR:")]
    return [l for l in lines if not any(a in l for a in allowed)]


def is_enumerated_review(text: str) -> bool:
    return bool(re.search(r"^\s*(1[.)]|#+\s*1)", text, re.MULTILINE)) or bool(
        re.search(r"^\d+[.)]\s", text, re.MULTILINE)
    )


def parse_grade(completion: str) -> bool:
    m = re.findall(r"GRADE:\s*([CI])", completion)
    return bool(m) and m[-1] == "C"


# ---------- staging ----------------------------------------------------------

def stage_files(fixture: str, skill: str, extra_skill_files: dict[str, str] | None = None) -> dict[str, str]:
    """Map sandbox paths -> host paths: fixture workspace at ws/, skill assets at skill/."""
    files: dict[str, str] = {}
    for f in (FIXTURES / fixture).iterdir():
        if f.is_file() and f.suffix in (".md", ".json") and f.name != "expected.json":
            files[f"ws/{f.name}"] = str(f)
        if f.is_dir() and f.name == "img":
            for img in f.iterdir():
                files[f"ws/img/{img.name}"] = str(img)
    skill_dir = SKILLS / skill
    for sub in ("references", "scripts"):
        d = skill_dir / sub
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    files[f"skill/{sub}/{f.name}"] = str(f)
    for target, source in (extra_skill_files or {}).items():
        files[target] = source
    return files


def skill_prompt(skill: str, request: str) -> str:
    text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    return (
        "You are an AI agent operating a skill inside a user's proposal workspace.\n"
        "The workspace is the `ws/` directory (work there). The skill's reference "
        "files and scripts are under `skill/` (read-only; script paths inside the "
        "instructions resolve to `skill/scripts/`, references to `skill/references/`).\n\n"
        f"=== SKILL INSTRUCTIONS ===\n{text}\n=== END SKILL INSTRUCTIONS ===\n\n"
        f"User request: {request}\n"
        "Fulfil exactly this request — nothing beyond it — following the skill "
        "instructions. End with the chat answer you would give the user."
    )


def agent_solver():
    return basic_agent(
        init=system_message(
            "You have bash and a text editor. Files live under ws/ (workspace) and skill/."
        ),
        tools=[bash(timeout=120), text_editor()],
        max_attempts=1,
        message_limit=40,
    )


async def read_ws(path: str) -> str | None:
    try:
        return await sandbox().read_file(f"ws/{path}")
    except Exception:
        return None


async def run_check(proposal: str) -> str:
    result = await sandbox().exec(
        ["python3", "skill/scripts/check.py", f"ws/{proposal}"], timeout=60
    )
    return result.stdout


async def judge(rubric: str, question: str, answer: str, criterion: str) -> tuple[bool, str]:
    template = (RUBRICS / rubric).read_text(encoding="utf-8")
    prompt = template.format(
        question=question, answer=answer, criterion=criterion, instructions=JUDGE_INSTRUCTIONS
    )
    output = await get_model(JUDGE_MODEL).generate(prompt)
    return parse_grade(output.completion), output.completion[-400:]


# ---------- task: write from ideate seed -------------------------------------

W01_PROPOSAL = "data-drift-detection.md"


@scorer(metrics=[accuracy()])
def write_l1():
    async def score(state: TaskState, target: Target) -> Score:
        text = await read_ws(W01_PROPOSAL)
        if not text:
            return Score(value=INCORRECT, explanation="seed proposal file gone")
        check_out = await run_check(W01_PROPOSAL)
        bad = disallowed_errors(check_out, DRAFT_ALLOWED_ERRORS)
        if bad:
            return Score(value=INCORRECT, explanation="check errors: " + "; ".join(bad))
        return Score(value=CORRECT, explanation="draft mechanically sound")
    return score


@scorer(metrics=[accuracy()])
def write_l2_rq_quality():
    async def score(state: TaskState, target: Target) -> Score:
        text = await read_ws(W01_PROPOSAL) or ""
        passed, why = await judge(
            "rq_quality.txt", state.input_text, text,
            "All research questions analytical, self-contained, non-overlapping, not yes/no.",
        )
        return Score(value=CORRECT if passed else INCORRECT, explanation=why)
    return score


@task
def write_from_seed() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-write",
                "Please turn my idea notes into a full proposal draft. The file is "
                f"ws/{W01_PROPOSAL}. Keep my idea, mark anything missing as TODO.",
            ),
            files=stage_files(
                "w01-ideate-seed", "proposal-write",
                {"skill/scripts/check.py": str(SKILLS / "proposal-check" / "scripts" / "check.py"),
                 "skill/references/structure.json": str(SKILLS / "proposal-check" / "references" / "structure.json")},
            ),
        )],
        solver=agent_solver(),
        scorer=[write_l1(), write_l2_rq_quality()],
        sandbox="local",
    )


# ---------- task: review a fixture -------------------------------------------

F05_PROPOSAL = "microservice-technical-debt.md"
F05_REVIEW = "microservice-technical-debt-review.md"


@scorer(metrics=[accuracy()])
def review_l1():
    async def score(state: TaskState, target: Target) -> Score:
        original = (FIXTURES / "f05-slr-interviews" / F05_PROPOSAL).read_text(encoding="utf-8")
        current = await read_ws(F05_PROPOSAL)
        review = await read_ws(F05_REVIEW)
        if current != original:
            return Score(value=INCORRECT, explanation="review modified the proposal")
        if not review:
            return Score(value=INCORRECT, explanation=f"{F05_REVIEW} not written")
        if not is_enumerated_review(review):
            return Score(value=INCORRECT, explanation="review not enumerated")
        return Score(value=CORRECT, explanation="review file present, proposal untouched")
    return score


@scorer(metrics=[accuracy()])
def review_l2_quality():
    async def score(state: TaskState, target: Target) -> Score:
        review = await read_ws(F05_REVIEW) or ""
        oracle = json.loads(
            (FIXTURES / "f05-slr-interviews" / "expected.json").read_text(encoding="utf-8")
        )
        passed, why = await judge(
            "review_quality.txt", "; ".join(oracle["semantic"]), review,
            "Finds the seeded defects, actionable, format-agnostic, grammar only as brief hint.",
        )
        return Score(value=CORRECT if passed else INCORRECT, explanation=why)
    return score


@task
def review_fixture() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-review",
                f"Please review my proposal ws/{F05_PROPOSAL} — is it ready for my supervisor?",
            ),
            files=stage_files("f05-slr-interviews", "proposal-review"),
        )],
        solver=agent_solver(),
        scorer=[review_l1(), review_l2_quality()],
        sandbox="local",
    )


# ---------- task: check report fidelity --------------------------------------

F15_PROPOSAL = "broken-format.md"


def assistant_text(state: TaskState) -> str:
    """All assistant-authored chat text — the check report may be relayed mid-conversation."""
    parts = []
    for message in state.messages:
        if getattr(message, "role", None) == "assistant" and message.text:
            parts.append(message.text)
    return "\n".join(parts)


@scorer(metrics=[accuracy()])
def check_report_l1():
    async def score(state: TaskState, target: Target) -> Score:
        oracle = json.loads(
            (FIXTURES / "f15-format-broken" / "expected.json").read_text(encoding="utf-8")
        )
        original = (FIXTURES / "f15-format-broken" / F15_PROPOSAL).read_text(encoding="utf-8")
        current = await read_ws(F15_PROPOSAL)
        if current != original:
            return Score(
                value=INCORRECT,
                explanation="check modified the proposal — advisory skill must only report",
            )
        answer = assistant_text(state)
        hits = sum(1 for n in oracle["check"]["errors_contain"] if n.split("`")[0].strip() in answer)
        if hits >= 3:
            return Score(value=CORRECT, explanation=f"{hits}/5 oracle errors surfaced, file untouched")
        return Score(value=INCORRECT, explanation=f"only {hits}/5 oracle errors surfaced")
    return score


@task
def check_report() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-check", f"Please check my proposal ws/{F15_PROPOSAL}."
            ),
            files=stage_files("f15-format-broken", "proposal-check"),
        )],
        solver=agent_solver(),
        scorer=[check_report_l1()],
        sandbox="local",
    )
