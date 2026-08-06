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
import sys as _sys
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageUser, get_model
from inspect_ai.scorer import CORRECT, INCORRECT, Score, Target, accuracy, scorer
from inspect_ai.solver import Generate, TaskState, basic_agent, solver, system_message, use_tools
from inspect_ai.tool import bash, text_editor
from inspect_ai.util import sandbox

_sys.path.insert(0, str(Path(__file__).resolve().parent))
from l1_checks import (  # noqa: E402
    parse_grade,
    select_draft,
    verdict_check_report,
    verdict_draft,
    verdict_early_stop,
    verdict_import,
    verdict_no_spurious_offer,
    verdict_provenance,
    verdict_review,
    verdict_seed,
    verdict_title_alarm,
    verdict_troubleshoot_model_rung,
)
from sources import MESSY_REQUEST  # noqa: E402

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
    for sub in ("references", "scripts", "templates"):
        d = skill_dir / sub
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    files[f"skill/{sub}/{f.name}"] = str(f)
    for target, source in (extra_skill_files or {}).items():
        files[target] = source
    return files


def lit_search_sibling() -> dict[str, str]:
    """Stage lit-search as an installed sibling skill: ideate's grounding
    reference ../proposal-lit-search/SKILL.md resolves there from skill/,
    and the scripts that SKILL.md documents resolve next to it."""
    root = SKILLS / "proposal-lit-search"
    files = {"proposal-lit-search/SKILL.md": str(root / "SKILL.md")}
    for f in (root / "scripts").iterdir():
        if f.is_file() and f.suffix == ".py":
            files[f"proposal-lit-search/scripts/{f.name}"] = str(f)
    return files


def skill_prompt(skill: str, request: str) -> str:
    text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    return (
        "You are an AI agent operating a skill inside a user's proposal workspace.\n"
        "The workspace is the `ws/` directory (work there). The skill's reference "
        "files and scripts are under `skill/` (read-only; script paths inside the "
        "instructions resolve to `skill/scripts/`, references to `skill/references/`; "
        "sibling skills, when installed, sit next to `skill/` under their own name — "
        "a `../<sibling>/` path in the instructions is `<sibling>/` from your working "
        "directory).\n\n"
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


async def workspace_markdown() -> dict[str, str]:
    listing = await sandbox().exec(["bash", "-c", "ls ws/*.md 2>/dev/null"], timeout=10)
    files = {}
    for path in listing.stdout.splitlines():
        name = path.strip().removeprefix("ws/")
        text = await read_ws(name) if name else None
        if text is not None:
            files[name] = text
    return files


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
W01_SEED = (FIXTURES / "w01-ideate-seed" / W01_PROPOSAL).read_text(encoding="utf-8")


async def produced_draft() -> tuple[str | None, str, str]:
    """(filename, text, where): the skill may draft into a fresh <slug>.md."""
    files = await workspace_markdown()
    chosen, where = select_draft(files, W01_PROPOSAL, W01_SEED)
    return chosen, files.get(chosen, ""), where


@scorer(metrics=[accuracy()])
def write_l1():
    async def score(state: TaskState, target: Target) -> Score:
        chosen, text, where = await produced_draft()
        if not chosen:
            return Score(value=INCORRECT, explanation=where)
        ok, why = verdict_draft(text, await run_check(chosen))
        return Score(value=CORRECT if ok else INCORRECT, explanation=f"{why} ({where})")
    return score


@scorer(metrics=[accuracy()])
def write_l2_rq_quality():
    async def score(state: TaskState, target: Target) -> Score:
        _, text, _ = await produced_draft()
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
            # the skill ships its own check.py + structure.json (sync copies),
            # so standard staging serves the model and the scorer alike
            files=stage_files("w01-ideate-seed", "proposal-write"),
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


@scorer(metrics=[accuracy()])
def no_spurious_offer():
    """Negative coverage for the failure-path report offer: this fixture's oracle
    expects findings, so the run succeeded and no offer belongs in the answer.

    Rides along on tasks that already run rather than costing its own metered
    task — the behaviour under test is what the model says while doing its job.
    """
    async def score(state: TaskState, target: Target) -> Score:
        ok, why = verdict_no_spurious_offer(state.output.completion)
        return Score(value=CORRECT if ok else INCORRECT, explanation=why)
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
        scorer=[review_l1(), review_l2_quality(), no_spurious_offer()],
        sandbox="local",
    )


# ---------- task: title alarm on a tool-shaped title -------------------------
#
# The half of the title rule no offline test can reach: the deterministic script
# matches openers, buzzwords, question form and length, but cannot know that
# `Kubernetes` is the instrument of this prototype rather than its object.

F21_PROPOSAL = "kubernetes-build-dashboard.md"
F21_REVIEW = "kubernetes-build-dashboard-review.md"


@scorer(metrics=[accuracy()])
def title_l1():
    async def score(state: TaskState, target: Target) -> Score:
        original = (FIXTURES / "f21-bad-title" / F21_PROPOSAL).read_text(encoding="utf-8")
        ok, why = verdict_title_alarm(
            original, await read_ws(F21_PROPOSAL), await read_ws(F21_REVIEW), F21_REVIEW
        )
        return Score(value=CORRECT if ok else INCORRECT, explanation=why)
    return score


@scorer(metrics=[accuracy()])
def title_l2_alarm():
    async def score(state: TaskState, target: Target) -> Score:
        review = await read_ws(F21_REVIEW) or ""
        oracle = json.loads(
            (FIXTURES / "f21-bad-title" / "expected.json").read_text(encoding="utf-8")
        )
        passed, why = await judge(
            "title_alarm.txt", "; ".join(oracle["semantic"]), review,
            "Title raised as its own finding, certificate consequence named, one to "
            "three abstracted alternatives offered, decision left with the student.",
        )
        return Score(value=CORRECT if passed else INCORRECT, explanation=why)
    return score


@task
def title_alarm() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-review",
                f"Please review my proposal ws/{F21_PROPOSAL} — is it ready for my supervisor?",
            ),
            files=stage_files("f21-bad-title", "proposal-review"),
        )],
        solver=agent_solver(),
        scorer=[title_l1(), title_l2_alarm()],
        sandbox="local",
    )


# ---------- tasks: ideate persona dialogues -----------------------------------
#
# One long composite run (preamble -> hesitant -> extraction probe -> pivot ->
# convergence -> seeding, ~18 rounds, workspace snapshots between rounds) plus
# short adversarial probes (stonewaller, no-idea, out-of-scope). The former
# 5-round cooperative-only tasks (ideate_socratic, ideate_anecdote) are retired:
# their coverage lives in the long run's hesitant phase.

PERSONAS = Path(__file__).resolve().parent / "personas"
PERSONA_MODEL = os.environ.get("PERSONA_MODEL", JUDGE_MODEL)

IDEATE_REQUEST = "Hi, I need to find a thesis topic and don't know where to start."


def _visible_user_text(text: str) -> str:
    """The opening sample input wraps the whole SKILL.md around the student's
    actual request; the transcript must carry only the request, or the skill's
    own prose would count as student words for provenance and the judge."""
    if "=== END SKILL INSTRUCTIONS ===" in text:
        tail = text.split("=== END SKILL INSTRUCTIONS ===", 1)[1]
        m = re.search(r"User request: (.*)", tail)
        return m.group(1).strip() if m else ""
    return text


def dialogue_transcript(state: TaskState) -> str:
    lines = []
    for message in state.messages:
        role = getattr(message, "role", "")
        if role in ("user", "assistant") and getattr(message, "text", ""):
            text = _visible_user_text(message.text) if role == "user" else message.text
            if text:
                lines.append(f"{'STUDENT' if role == 'user' else 'ASSISTANT'}: {text}")
    return "\n\n".join(lines)


async def _ws_sizes() -> dict[str, int]:
    """Byte sizes of workspace markdown — cheap mechanical growth signal."""
    result = await sandbox().exec(["bash", "-c", "wc -c ws/*.md 2>/dev/null"], timeout=10)
    sizes: dict[str, int] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].startswith("ws/"):
            sizes[parts[1].removeprefix("ws/")] = int(parts[0])
    return sizes


@solver
def persona_dialogue(persona_file: str, rounds: int = 5,
                     final_cue: str = (
                         "Sorry, I have to run to a lecture. Please capture where "
                         "we got to so I can continue next time."
                     )):
    """Scripted student persona drives `rounds` assistant turns, then the final
    cue. After every assistant turn the workspace is snapshotted into the store
    (key `ws_snapshots`) so scorers can assert when files appeared and grew."""
    persona = (PERSONAS / persona_file).read_text(encoding="utf-8")

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        student = get_model(PERSONA_MODEL)
        snapshots = []
        for round_no in range(rounds):
            state = await generate(state)
            snapshots.append({"round": round_no + 1, "files": await _ws_sizes()})
            if round_no == rounds - 1:
                break
            reply = await student.generate(
                persona + "\n\n=== CONVERSATION SO FAR ===\n" + dialogue_transcript(state)
            )
            state.messages.append(ChatMessageUser(content=reply.completion.strip()))
        state.messages.append(ChatMessageUser(content=final_cue))
        state = await generate(state)
        snapshots.append({"round": rounds + 1, "files": await _ws_sizes()})
        state.store.set("ws_snapshots", snapshots)
        return state

    return solve


async def _selected_seed() -> tuple[str | None, str, str]:
    files = await workspace_markdown()
    chosen, where = select_draft(files)
    return chosen, files.get(chosen, "") if chosen else "", where


@scorer(metrics=[accuracy()])
def ideate_l1_seed():
    async def score(state: TaskState, target: Target) -> Score:
        chosen, text, where = await _selected_seed()
        ok, why = verdict_seed(text or None, chosen or "")
        return Score(value=CORRECT if ok else INCORRECT, explanation=f"{why} ({where})")
    return score


@scorer(metrics=[accuracy()])
def ideate_l1_notes_progress(notes_by_round: int = 8, growth_by_round: int = 14,
                             no_proposal_before: int = 17):
    """Mechanical dialogue-state assertions from the solver's snapshots: the
    notes file appears early and has grown by the pivot phase; no proposal file
    before convergence. Defaults follow longrun-lara.txt: topic at reply 2,
    pivot at reply 10 (growth observable by round 14), convergence complete at
    reply 16, so a seed belongs in rounds 17-19 — anything before 17 predates
    the student's confirmation."""
    async def score(state: TaskState, target: Target) -> Score:
        snaps = state.store.get("ws_snapshots", [])
        if not snaps:
            return Score(value=INCORRECT, explanation="no workspace snapshots recorded")

        def notes_size(snap):
            return sum(v for n, v in snap["files"].items() if n.endswith(".notes.md"))

        problems = []
        with_notes = [s for s in snaps if notes_size(s)]
        if not with_notes:
            problems.append("notes file never appeared")
        else:
            first = with_notes[0]
            if first["round"] > notes_by_round:
                problems.append(f"notes file first appeared at round {first['round']} (expected by {notes_by_round})")
            by_pivot = [s for s in with_notes if s["round"] <= growth_by_round]
            if not any(notes_size(s) > notes_size(first) for s in by_pivot[1:]):
                problems.append(f"notes file had not grown by round {growth_by_round}")
        early_seed = next(
            (s["round"] for s in snaps
             if select_draft(dict.fromkeys(s["files"], ""))[0] and s["round"] < no_proposal_before),
            None,
        )
        if early_seed:
            problems.append(f"proposal file already present at round {early_seed} (before convergence)")
        if problems:
            return Score(value=INCORRECT, explanation="; ".join(problems))
        return Score(value=CORRECT, explanation=f"notes from round {with_notes[0]['round']}, grew by the pivot, proposal only at the end")
    return score


@scorer(metrics=[accuracy()])
def ideate_l1_provenance():
    async def score(state: TaskState, target: Target) -> Score:
        chosen, text, where = await _selected_seed()
        ok, why = verdict_provenance(dialogue_transcript(state), text or None)
        return Score(value=CORRECT if ok else INCORRECT, explanation=f"{why} ({where})")
    return score


@scorer(metrics=[accuracy()])
def ideate_l1_early_stop():
    async def score(state: TaskState, target: Target) -> Score:
        ok, why = verdict_early_stop(await workspace_markdown())
        return Score(value=CORRECT if ok else INCORRECT, explanation=why)
    return score


@scorer(metrics=[accuracy()])
def ideate_l2_socratic(criterion: str):
    async def score(state: TaskState, target: Target) -> Score:
        _, seed, _ = await _selected_seed()
        passed, why = await judge(
            "socratic.txt", dialogue_transcript(state), seed or "(no file created)", criterion
        )
        return Score(value=CORRECT if passed else INCORRECT, explanation=why)
    return score


def _ideate_sample() -> Sample:
    return Sample(
        input=skill_prompt("proposal-ideate", IDEATE_REQUEST),
        files=stage_files("w03-snowball-seed", "proposal-ideate", lit_search_sibling()),
        setup="rm -f ws/*.md",  # empty workspace: ideate starts from nothing
    )


@task
def ideate_longrun() -> Task:
    """~18-round composite run; phases are scripted in the persona by reply
    number so graders can attribute failures to a phase."""
    return Task(
        dataset=[_ideate_sample()],
        solver=[
            use_tools(bash(timeout=120), text_editor()),
            persona_dialogue("longrun-lara.txt", rounds=18,
                             final_cue="Yes — please create the file now."),
        ],
        scorer=[
            ideate_l1_seed(),
            ideate_l1_notes_progress(),
            ideate_l1_provenance(),
            ideate_l2_socratic(
                "Judge per phase: preamble handled as one administrative block; "
                "hesitant phase Socratic with uptake; at the extraction probe "
                "('just write me three research questions') the assistant declines "
                "and offers a next step instead of finished questions; the pivot is "
                "followed; a stocktake appears around mid-session; seeding happens "
                "at convergence."
            ),
        ],
        sandbox="local",
    )


@task
def ideate_stonewall() -> Task:
    """Student contributes nothing: the early stop must fire — impasse named,
    state saved to notes, no proposal file generated."""
    return Task(
        dataset=[_ideate_sample()],
        solver=[
            use_tools(bash(timeout=120), text_editor()),
            persona_dialogue("stonewall-kim.txt", rounds=6,
                             final_cue="Okay... so what happens now?"),
        ],
        scorer=[
            ideate_l1_early_stop(),
            ideate_l2_socratic(
                "After about three contentless exchanges the assistant names the "
                "impasse plainly, supplies no topic or research-question content "
                "of its own, suggests concrete offline steps, and ends without "
                "seeding a proposal file."
            ),
        ],
        sandbox="local",
    )


@task
def ideate_noidea() -> Task:
    """No topic at all, professor named without URL: hints must stay few and
    sourced, never a topic menu; noisy name lookups must be called weak."""
    return Task(
        dataset=[_ideate_sample()],
        solver=[
            use_tools(bash(timeout=120), text_editor()),
            persona_dialogue("noidea-sam.txt", rounds=6),
        ],
        scorer=[
            ideate_l2_socratic(
                "The assistant floats at most two directions, each tied to the "
                "student's stated interests or to fetched data with its source "
                "named; it never presents a menu or numbered list of ready-made "
                "topics; ambiguous or thin lookup results are called weak "
                "scoping rather than silently trusted, and if the lookup fails "
                "or is unreachable the assistant says so once and works from "
                "the student's words."
            ),
        ],
        sandbox="local",
    )


@task
def ideate_outofscope() -> Task:
    """Student insists on an idea clearly outside the given scope: one chat-only
    warning, then ideation continues; no fit concern in any produced file."""
    return Task(
        dataset=[_ideate_sample()],
        solver=[
            use_tools(bash(timeout=120), text_editor()),
            # the cue requests seeding so the clean-seed half of the criterion
            # is observable, not vacuously true on a notes-only session
            persona_dialogue("outofscope-toni.txt", rounds=8,
                             final_cue="Okay, that's enough for today — please "
                                       "create the file with what we have."),
        ],
        scorer=[
            ideate_l2_socratic(
                "The assistant warns exactly once, in chat only, that the idea "
                "sits outside the given scope; after the student insists it keeps "
                "ideating constructively, and the seeded file carries no trace of "
                "the fit concern."
            ),
        ],
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


# ---------- task: customize writes the override file --------------------------

@scorer(metrics=[accuracy()])
def customize_l1():
    async def score(state: TaskState, target: Target) -> Score:
        import tomllib
        original = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text(encoding="utf-8")
        if await read_ws("ml-code-review.md") != original:
            return Score(value=INCORRECT, explanation="customize modified the proposal")
        guidelines = await read_ws("guidelines.md")
        if not guidelines:
            return Score(value=INCORRECT, explanation="guidelines.md not created")
        m = re.search(r"```toml\n(.*?)```", guidelines, re.DOTALL)
        if not m:
            return Score(value=INCORRECT, explanation="no fenced TOML block")
        try:
            data = tomllib.loads(m.group(1))
        except tomllib.TOMLDecodeError as exc:
            return Score(value=INCORRECT, explanation=f"TOML does not parse: {exc}")
        if data.get("min_references") != 8:
            return Score(value=INCORRECT, explanation=f"min_references is {data.get('min_references')!r}, not 8")
        detail = str(data.get("timeline_detail", "<absent>")).lower()
        if detail != "detailed":
            return Score(
                value=INCORRECT,
                explanation=f"timeline_detail is {detail!r}, not 'detailed' — the work plan stays blocked",
            )
        return Score(
            value=CORRECT,
            explanation='valid TOML: min_references=8, timeline_detail="detailed"',
        )
    return score


@task
def customize_override() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-customize",
                "My supervisor requires a detailed work plan with milestones in the "
                "proposal, not just a one-line timeline, and at least 8 references. "
                "Please adjust the rules for this workspace.",
            ),
            files=stage_files("f00-clean-en", "proposal-customize"),
        )],
        solver=agent_solver(),
        scorer=[customize_l1()],
        sandbox="local",
    )


# ---------- task: publish builds a PDF ---------------------------------------

@scorer(metrics=[accuracy()])
def publish_l1():
    async def score(state: TaskState, target: Target) -> Score:
        listing = await sandbox().exec(["bash", "-c", "ls -la ws/*.pdf 2>/dev/null; cat ws/.gitignore 2>/dev/null"], timeout=10)
        if ".pdf" not in listing.stdout:
            return Score(value=INCORRECT, explanation="no PDF produced: " + listing.stdout[:200])
        if "*.pdf" not in listing.stdout:
            return Score(value=INCORRECT, explanation="workspace .gitignore not maintained")
        return Score(value=CORRECT, explanation="PDF built, gitignore maintained")
    return score


@task
def publish_build() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt("proposal-publish", "Please build a PDF of my proposal."),
            files=stage_files("f00-clean-en", "proposal-publish"),
        )],
        solver=agent_solver(),
        scorer=[publish_l1()],
        sandbox="local",
    )


# ---------- task: import from messy pasted text -------------------------------

@scorer(metrics=[accuracy()])
def import_l1():
    async def score(state: TaskState, target: Target) -> Score:
        files = await workspace_markdown()
        # same selection as the dev runner (shared verdict module)
        produced, _ = select_draft(files)
        if not produced:
            passed, why = verdict_import(None)
            return Score(value=INCORRECT, explanation=why)
        # the skill ships its own check copy, so the scorer uses that one
        passed, why = verdict_import(files[produced], await run_check(produced), produced)
        return Score(value=CORRECT if passed else INCORRECT, explanation=why)
    return score


@task
def import_messy() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt("proposal-import", MESSY_REQUEST),
            files={
                "ws/README-placeholder.txt": "workspace",
                "skill/scripts/check.py": str(
                    SKILLS / "proposal-import" / "scripts" / "check.py"),
                "skill/references/structure.json": str(
                    SKILLS / "proposal-import" / "references" / "structure.json"),
            },
        )],
        solver=agent_solver(),
        scorer=[import_l1()],
        sandbox="local",
    )


# ---------- task: literature search expands references (live network) ---------

W03_PROPOSAL = "serverless-energy-scheduling.md"


@scorer(metrics=[accuracy()])
def litsearch_l1():
    async def score(state: TaskState, target: Target) -> Score:
        text = await read_ws(W03_PROPOSAL)
        if not text:
            return Score(value=INCORRECT, explanation="proposal file gone")
        ids = re.findall(r"^\s*-\s+id:\s*(\S+)", text, re.MULTILINE)
        if len(ids) <= 3:
            return Score(value=INCORRECT, explanation=f"still only {len(ids)} references")
        if len(ids) != len(set(ids)):
            return Score(value=INCORRECT, explanation="duplicate reference ids")
        return Score(value=CORRECT, explanation=f"{len(ids)} references, ids unique")
    return score


@task
def litsearch_expand() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-lit-search",
                f"Please find about three more relevant sources for ws/{W03_PROPOSAL} "
                "and add them to my references.",
            ),
            files=stage_files("w03-snowball-seed", "proposal-lit-search"),
        )],
        solver=agent_solver(),
        scorer=[litsearch_l1()],
        sandbox="local",
    )


# ---------- task: German review ------------------------------------------------

F04_PROPOSAL = "zero-trust-referenzmodell.md"
F04_REVIEW = "zero-trust-referenzmodell-review.md"


@scorer(metrics=[accuracy()])
def review_de_l1():
    async def score(state: TaskState, target: Target) -> Score:
        original = (FIXTURES / "f04-dsr-vendor-heavy" / F04_PROPOSAL).read_text(encoding="utf-8")
        current = await read_ws(F04_PROPOSAL)
        review = await read_ws(F04_REVIEW)
        ok, why = verdict_review(original, current, review, F04_REVIEW)
        if not ok:
            return Score(value=INCORRECT, explanation=why)
        german_signals = sum(1 for w in (" der ", " die ", " und ", " nicht ", " werden ")
                             if w in (review or ""))
        if german_signals < 2:
            return Score(value=INCORRECT, explanation="review does not appear to be written in German")
        return Score(value=CORRECT, explanation="German review file present, proposal untouched")
    return score


@scorer(metrics=[accuracy()])
def review_de_l2():
    async def score(state: TaskState, target: Target) -> Score:
        review = await read_ws(F04_REVIEW) or ""
        oracle = json.loads(
            (FIXTURES / "f04-dsr-vendor-heavy" / "expected.json").read_text(encoding="utf-8")
        )
        passed, why = await judge(
            "review_quality.txt", "; ".join(oracle["semantic"]), review,
            "Finds the seeded defects, actionable, format-agnostic, written in German.",
        )
        return Score(value=CORRECT if passed else INCORRECT, explanation=why)
    return score


@task
def review_fixture_de() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-review",
                f"Bitte begutachte mein Exposé ws/{F04_PROPOSAL} — ist es bereit für die Abgabe?",
            ),
            files=stage_files("f04-dsr-vendor-heavy", "proposal-review"),
        )],
        solver=agent_solver(),
        scorer=[review_de_l1(), review_de_l2()],
        sandbox="local",
    )


# ---------- task: check report, hardened non-interactive variant ---------------

@task
def check_report_hardened() -> Task:
    """Non-interactive framing: the SKILL.md read-only guard (digest re-run
    comparison) must keep the proposal byte-identical even in an autonomous run."""
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-check",
                "Automated nightly quality gate — no user is present, this run is "
                f"non-interactive. Check ws/{F15_PROPOSAL} and output the report.",
            ),
            files=stage_files("f15-format-broken", "proposal-check"),
        )],
        solver=agent_solver(),
        scorer=[check_report_l1()],
        sandbox="local",
    )


# ---------- task: troubleshoot resolves the model rung without a report -------
#
# The rung is stated in the prompt rather than inferred from the runner, so the
# expected outcome is identical on every model under test: the user says they ran
# claude-haiku-4.5, which the vendored verdicts record as failing proposal-write.
# The prompt also closes rung 0 (already reinstalled), so rung 1 is the target and
# a model that stops at "update first" is not accidentally graded correct.


@scorer(metrics=[accuracy()])
def troubleshoot_model_rung_l1():
    async def score(state: TaskState, target: Target) -> Score:
        listing = await sandbox().exec(
            ["bash", "-c", "test -d ws/bug-report && echo present || echo absent"], timeout=10
        )
        bundle_present = "present" in listing.stdout
        ok, why = verdict_troubleshoot_model_rung(state.output.completion, bundle_present)
        return Score(value=CORRECT if ok else INCORRECT, explanation=why)
    return score


@task
def troubleshoot_model_rung() -> Task:
    return Task(
        dataset=[Sample(
            input=skill_prompt(
                "proposal-troubleshoot",
                "The write skill produced a draft that ignored half of what I told it. I was "
                "running claude-haiku-4.5. I have already re-run "
                "`npx skills add hutzelmann/thesis-proposal-skills` and it still happens. "
                "Is this a bug I should report?",
            ),
            files=stage_files("f05-slr-interviews", "proposal-troubleshoot"),
        )],
        solver=agent_solver(),
        scorer=[troubleshoot_model_rung_l1(), no_spurious_offer()],
        sandbox="local",
    )
