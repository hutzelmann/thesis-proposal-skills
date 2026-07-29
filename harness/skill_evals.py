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
from inspect_ai.model import ChatMessageUser, get_model
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer
from inspect_ai.solver import Generate, TaskState, basic_agent, solver, system_message, use_tools
from inspect_ai.tool import bash, text_editor
from inspect_ai.util import sandbox

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from l1_checks import (  # noqa: E402
    DRAFT_ALLOWED_ERRORS, disallowed_errors, is_enumerated_review, parse_grade,
    verdict_check_report, verdict_draft, verdict_review, verdict_seed,
)

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
FIXTURES = REPO / "tests" / "fixtures"
RUBRICS = Path(__file__).resolve().parent / "rubrics"

JUDGE_MODEL = os.environ.get("JUDGE_MODEL", "openrouter/anthropic/claude-haiku-4.5")
JUDGE_INSTRUCTIONS = (
    'Reason step by step, then end with exactly one line: "GRADE: C" (pass) or "GRADE: I" (fail).'
)

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
        check_out = await run_check(W01_PROPOSAL) if text else ""
        ok, why = verdict_draft(text, check_out)
        return Score(value=CORRECT if ok else INCORRECT, explanation=why)
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
        ok, why = verdict_review(original, current, review, F05_REVIEW)
        return Score(value=CORRECT if ok else INCORRECT, explanation=why)
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


# ---------- task: ideate socratic dialogue ------------------------------------

PERSONAS = Path(__file__).resolve().parent / "personas"
PERSONA_MODEL = os.environ.get("PERSONA_MODEL", JUDGE_MODEL)
IDEATE_ROUNDS = int(os.environ.get("IDEATE_ROUNDS", "5"))


def dialogue_transcript(state: TaskState) -> str:
    lines = []
    for message in state.messages:
        role = getattr(message, "role", "")
        if role in ("user", "assistant") and getattr(message, "text", ""):
            lines.append(f"{'STUDENT' if role == 'user' else 'ASSISTANT'}: {message.text}")
    return "\n\n".join(lines)


@solver
def persona_dialogue(persona_file: str, rounds: int = IDEATE_ROUNDS):
    persona = (PERSONAS / persona_file).read_text(encoding="utf-8")

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        student = get_model(PERSONA_MODEL)
        for round_no in range(rounds):
            state = await generate(state)
            if round_no == rounds - 1:
                break
            reply = await student.generate(
                persona + "\n\n=== CONVERSATION SO FAR ===\n" + dialogue_transcript(state)
            )
            state.messages.append(ChatMessageUser(content=reply.completion.strip()))
        state.messages.append(ChatMessageUser(content=(
            "Sorry, I have to run to a lecture. Please capture where we got to "
            "so I can continue next time."
        )))
        return await generate(state)

    return solve


@scorer(metrics=[accuracy()])
def ideate_l1_seed():
    async def score(state: TaskState, target: Target) -> Score:
        listing = await sandbox().exec(["bash", "-c", "ls ws/*.md 2>/dev/null"], timeout=10)
        files = [f for f in listing.stdout.split() if f.strip()]
        text = await sandbox().read_file(files[0]) if files else None
        ok, why = verdict_seed(text, files[0] if files else "")
        return Score(value=CORRECT if ok else INCORRECT, explanation=why)
    return score


@scorer(metrics=[accuracy()])
def ideate_l2_socratic():
    async def score(state: TaskState, target: Target) -> Score:
        listing = await sandbox().exec(["bash", "-c", "ls ws/*.md 2>/dev/null"], timeout=10)
        files = [f for f in listing.stdout.split() if f.strip()]
        seed = await sandbox().read_file(files[0]) if files else "(no file created)"
        passed, why = await judge(
            "socratic.txt", dialogue_transcript(state), seed,
            "Socratic throughout: gaps surfaced indirectly, never asked directly for missing input.",
        )
        return Score(value=CORRECT if passed else INCORRECT, explanation=why)
    return score


@task
def ideate_socratic() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-ideate",
                "Hi... I need to find a thesis topic. I was thinking something with "
                "app development and maybe sustainability? A friend of mine built a "
                "CO2 tracking app once and that seemed cool. I don't really know "
                "where to start.",
            ),
            files=stage_files("w03-snowball-seed", "proposal-ideate"),
            setup="rm -f ws/*.md",  # empty workspace: ideate starts from nothing
        )],
        solver=[use_tools(bash(timeout=120), text_editor()), persona_dialogue("hesitant-bachelor.txt")],
        scorer=[ideate_l1_seed(), ideate_l2_socratic()],
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
        original = (FIXTURES / "f15-format-broken" / F15_PROPOSAL).read_text(encoding="utf-8")
        current = await read_ws(F15_PROPOSAL)
        ok, why = verdict_check_report(
            FIXTURES / "f15-format-broken" / "expected.json", original, current,
            assistant_text(state),
        )
        return Score(value=CORRECT if ok else INCORRECT, explanation=why)
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
