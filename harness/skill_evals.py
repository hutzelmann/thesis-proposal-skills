"""L1/L2 skill evals over the fixture corpus (testing-harness spec).

Each task stages a fixture workspace plus the skill's reference material into
a sandbox, lets the model under test act on a user request with bash/editor
tools, then scores:
- L1 (deterministic): expected artifacts exist, the check script's verdict
  matches tolerance, the proposal was (not) modified as the skill demands.
- L2 (rubric): a judge model grades semantic quality via harness/rubrics/.

Run (model under test is Inspect's --model, a roster ID from harness/models.toml;
prefer `uv run poe matrix --models … --tasks …`, which shows the cost gate first):
  uv run inspect eval harness/skill_evals.py@review_fixture \
      --model openrouter/<vendor>/<model> --log-dir logs/evals
Judge and dialogue persona come from [roles] in harness/models.toml. JUDGE_MODEL
and PERSONA_MODEL override one role each for one invocation; overriding the judge
does not move the persona.
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
from l1_checks import (
    NOTES_SUFFIX,
    load_closing_note,
    parse_grade,
    select_draft,
    verdict_check_report,
    verdict_cited_draft,
    verdict_customize_override,
    verdict_draft,
    verdict_early_stop,
    verdict_hollow_review,
    verdict_import,
    verdict_litsearch_expanded,
    verdict_no_spurious_offer,
    verdict_notes_progress,
    verdict_provenance,
    verdict_publish,
    verdict_repaired_draft,
    verdict_reverse,
    verdict_review,
    verdict_review_localized,
    verdict_seed,
    verdict_supervise_closing,
    verdict_supervise_feedback,
    verdict_supervise_literature,
    verdict_supervise_locators,
    verdict_supervise_markup,
    verdict_supervise_no_personal_data,
    verdict_supervise_pointers,
    verdict_supervise_points,
    verdict_supervise_substance_only,
    verdict_supervise_tier,
    verdict_title_alarm,
    verdict_troubleshoot_model_rung,
)

# The rubric material lives in l2_rubrics.py, shared with the dev runner's
# subscription judge; CRITERIA stays importable from here for eval_export.py.
from l2_rubrics import CITATION_SCOPE, CITATION_SYNTHESIS, CRITERIA, judge_prompt
from sources import MESSY_REQUEST
from support import parse_registry, role_model

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
FIXTURES = REPO / "tests" / "fixtures"

# every model ID this module uses comes from the registry's [roles] table
ROLES = parse_registry(
    (Path(__file__).resolve().parent / "models.toml").read_text(encoding="utf-8")
).roles
JUDGE_MODEL = role_model(ROLES, "judge", os.environ)

# ---------- staging ----------------------------------------------------------

def stage_files(fixture: str, skill: str,
                extra_skill_files: dict[str, str] | None = None) -> dict[str, str]:
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


def plain_prompt(request: str) -> str:
    """The baseline arm's prompt: identical workspace framing and request, no
    skill instructions. Staging stays identical — `skill/` carries scorer
    infrastructure (check script, references) the verdicts need either way;
    what the baseline removes is the instructions, not the files."""
    return (
        "You are an AI agent operating in a user's proposal workspace.\n"
        "The workspace is the `ws/` directory (work there).\n\n"
        f"User request: {request}\n"
        "Fulfil exactly this request — nothing beyond it. End with the chat "
        "answer you would give the user."
    )


def skill_prompt(skill: str, request: str) -> str:
    # the real host substitutes ${CLAUDE_SKILL_DIR} before the model sees the
    # body; here the skill's assets are staged under `skill/`, so the same
    # substitution keeps every documented script path resolvable in the sandbox
    text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    text = text.replace("${CLAUDE_SKILL_DIR}", "skill")
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


async def workspace_files(pattern: str) -> dict[str, str]:
    """Workspace files matching a shell glob, keyed by name relative to ws/."""
    listing = await sandbox().exec(["bash", "-c", f"ls ws/{pattern} 2>/dev/null"], timeout=10)
    files = {}
    for path in listing.stdout.splitlines():
        name = path.strip().removeprefix("ws/")
        text = await read_ws(name) if name else None
        if text is not None:
            files[name] = text
    return files


async def workspace_markdown() -> dict[str, str]:
    return await workspace_files("*.md")


async def run_check(proposal: str) -> str:
    result = await sandbox().exec(
        ["python3", "skill/scripts/check.py", f"ws/{proposal}"], timeout=60
    )
    return result.stdout


def verdict_scorer(name: str):
    """Turn an async `(state, *args) -> (passed, explanation)` function into an
    Inspect scorer.

    The adapter owns Inspect's mandatory `(state, target)` signature once, so a
    scorer body states only its verdict. The name is passed explicitly and MUST
    keep its `_l1` / `_l2` marker: the matrix classifier decides whether a
    scorer counts toward a cell by looking for `l1` in the registered name
    (`harness/support.py` — `scorer_counts`), so a renamed scorer silently
    changes model-support verdicts.
    """
    def decorate(fn):
        @scorer(metrics=[accuracy()], name=name)
        def build(*args, **kwargs):
            async def score(state: TaskState, _target: Target) -> Score:
                ok, why = await fn(state, *args, **kwargs)
                return Score(value=CORRECT if ok else INCORRECT, explanation=why)
            return score
        return build
    return decorate


def proposal_task(skill: str, fixture: str, request: str, scorers: list,
                  extra_skill_files: dict[str, str] | None = None,
                  files: dict[str, str] | None = None,
                  baseline: bool = False) -> Task:
    """The shape every single-turn skill task shares: one sample built from a
    fixture workspace and the skill's own assets, the standard agent loop, and a
    local sandbox. Only `scorers` and the request differ between them.
    `baseline` runs the without-skill control arm (testing-harness spec): same
    staging, same request, same scorers, no skill instructions."""
    return Task(
        dataset=[Sample(
            input=plain_prompt(request) if baseline else skill_prompt(skill, request),
            files=files if files is not None else stage_files(fixture, skill, extra_skill_files),
        )],
        solver=agent_solver(),
        scorer=scorers,
        sandbox="local",
    )


async def judge(rubric: str, question: str, answer: str, criterion: str) -> tuple[bool, str]:
    # byte-identical to the prompt before the rubric material was shared
    # (tests/unit/test_eval_wiring.py pins it against tests/unit/data/l2_prompts/)
    prompt = judge_prompt(rubric, question, answer, criterion)
    output = await get_model(JUDGE_MODEL).generate(prompt)
    return parse_grade(output.completion), output.completion[-400:]


# ---------- task: write from ideate seed -------------------------------------

W01_PROPOSAL = "data-drift-detection.md"
W01_SEED = (FIXTURES / "w01-ideate-seed" / W01_PROPOSAL).read_text(encoding="utf-8")


async def drafted(seed_name: str, seed_text: str) -> tuple[str | None, str, str]:
    """(filename, text, where): the skill may draft into a fresh <slug>.md."""
    files = await workspace_markdown()
    chosen, where = select_draft(files, seed_name, seed_text)
    return chosen, files.get(chosen, ""), where


async def produced_draft() -> tuple[str | None, str, str]:
    return await drafted(W01_PROPOSAL, W01_SEED)


@verdict_scorer("write_l1")
async def write_l1(_state: TaskState) -> tuple[bool, str]:
    chosen, text, where = await produced_draft()
    if not chosen:
        return False, where
    ok, why = verdict_draft(text, await run_check(chosen))
    return ok, f"{why} ({where})"


@verdict_scorer("write_l2_rq_quality")
async def write_l2_rq_quality(state: TaskState) -> tuple[bool, str]:
    _, text, _ = await produced_draft()
    return await judge(
        "rq_quality.txt", state.input_text, text,
        CRITERIA[("write_from_seed", "write_l2_rq_quality")],
    )


@verdict_scorer("write_l2_density")
async def write_l2_density(state: TaskState) -> tuple[bool, str]:
    _, text, _ = await produced_draft()
    return await judge(
        "density.txt", state.input_text, text,
        CRITERIA[("write_from_seed", "write_l2_density")],
    )


@task
def write_from_seed(baseline: bool = False) -> Task:
    # the skill ships its own check.py + structure.json (sync copies), so
    # standard staging serves the model and the scorer alike
    return proposal_task(
        "proposal-write", "w01-ideate-seed",
        "Please turn my idea notes into a full proposal draft. The file is "
        f"ws/{W01_PROPOSAL}. Keep my idea, mark anything missing as TODO.",
        [write_l1(), write_l2_rq_quality(), write_l2_density()],
        baseline=baseline,
    )


# ---------- tasks: citation practice ------------------------------------------
# Neither request mentions citations: the rule has to reach the draft through
# the skill's own guidance. The dev runner carries the same two scenarios.

W08_PROPOSAL = "flaky-test-prediction.md"
W08_SEED = (FIXTURES / "w08-rich-seed" / W08_PROPOSAL).read_text(encoding="utf-8")
F27_PROPOSAL = "dependency-update-breakage.md"
F27_DRAFT = (FIXTURES / "f27-citation-runs" / F27_PROPOSAL).read_text(encoding="utf-8")


@verdict_scorer("write_rich_seed_l1")
async def write_rich_seed_l1(_state: TaskState) -> tuple[bool, str]:
    chosen, text, where = await drafted(W08_PROPOSAL, W08_SEED)
    if not chosen:
        return False, where
    ok, why = verdict_cited_draft(text, await run_check(chosen))
    return ok, f"{why} ({where})"


@verdict_scorer("write_rich_seed_l2_citation_scope")
async def write_rich_seed_l2_citation_scope(state: TaskState) -> tuple[bool, str]:
    _, text, _ = await drafted(W08_PROPOSAL, W08_SEED)
    return await judge("citation_practice.txt", state.input_text, text, CITATION_SCOPE)


@verdict_scorer("write_rich_seed_l2_synthesis")
async def write_rich_seed_l2_synthesis(state: TaskState) -> tuple[bool, str]:
    _, text, _ = await drafted(W08_PROPOSAL, W08_SEED)
    return await judge("citation_practice.txt", state.input_text, text, CITATION_SYNTHESIS)


@task
def write_rich_seed(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-write", "w08-rich-seed",
        f"Please turn my idea notes in ws/{W08_PROPOSAL} into a full proposal draft. "
        "Keep my idea, mark anything missing as TODO. I cannot answer any questions — "
        "decide and tell me what you did.",
        [write_rich_seed_l1(), write_rich_seed_l2_citation_scope(),
         write_rich_seed_l2_synthesis()],
        baseline=baseline,
    )


@verdict_scorer("write_repair_citations_l1")
async def write_repair_citations_l1(_state: TaskState) -> tuple[bool, str]:
    chosen, text, where = await drafted(F27_PROPOSAL, F27_DRAFT)
    if not chosen:
        return False, where
    ok, why = verdict_repaired_draft(F27_DRAFT, text, await run_check(chosen))
    return ok, f"{why} ({where})"


@verdict_scorer("write_repair_citations_l2_citation_scope")
async def write_repair_citations_l2_citation_scope(state: TaskState) -> tuple[bool, str]:
    _, text, _ = await drafted(F27_PROPOSAL, F27_DRAFT)
    return await judge("citation_practice.txt", state.input_text, text, CITATION_SCOPE)


@verdict_scorer("write_repair_citations_l2_synthesis")
async def write_repair_citations_l2_synthesis(state: TaskState) -> tuple[bool, str]:
    _, text, _ = await drafted(F27_PROPOSAL, F27_DRAFT)
    return await judge("citation_practice.txt", state.input_text, text, CITATION_SYNTHESIS)


@task
def write_repair_citations(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-write", "f27-citation-runs",
        f"Please do a writing pass over ws/{F27_PROPOSAL} so it is ready for my "
        "supervisor. I cannot answer any questions — decide and tell me what you did.",
        [write_repair_citations_l1(), write_repair_citations_l2_citation_scope(),
         write_repair_citations_l2_synthesis()],
        baseline=baseline,
    )


# ---------- task: review a fixture -------------------------------------------

F05_PROPOSAL = "microservice-technical-debt.md"
F05_REVIEW = "microservice-technical-debt-review.md"


@verdict_scorer("review_l1")
async def review_l1(_state: TaskState) -> tuple[bool, str]:
    original = (FIXTURES / "f05-slr-interviews" / F05_PROPOSAL).read_text(encoding="utf-8")
    return verdict_review(
        original, await read_ws(F05_PROPOSAL), await read_ws(F05_REVIEW), F05_REVIEW
    )


@verdict_scorer("review_l2_quality")
async def review_l2_quality(_state: TaskState) -> tuple[bool, str]:
    review = await read_ws(F05_REVIEW) or ""
    oracle = json.loads(
        (FIXTURES / "f05-slr-interviews" / "expected.json").read_text(encoding="utf-8")
    )
    return await judge(
        "review_quality.txt", "; ".join(oracle["semantic"]), review,
        CRITERIA[("review_fixture", "review_l2_quality")],
    )


@verdict_scorer("no_spurious_offer")
async def no_spurious_offer(state: TaskState) -> tuple[bool, str]:
    """Negative coverage for the failure-path report offer: this fixture's oracle
    expects findings, so the run succeeded and no offer belongs in the answer.

    Rides along on tasks that already run rather than costing its own metered
    task — the behaviour under test is what the model says while doing its job.
    """
    return verdict_no_spurious_offer(state.output.completion)


@task
def review_fixture(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-review", "f05-slr-interviews",
        f"Please review my proposal ws/{F05_PROPOSAL} — is it ready for my supervisor?",
        [review_l1(), review_l2_quality(), no_spurious_offer()],
        baseline=baseline,
    )


# ---------- task: hollow proposal gets the no-viable-core verdict -------------
#
# f22 passes the mechanical check with zero findings by construction: it exists
# to prove that "clean" carries no substance signal, and that the review says so.

F22_PROPOSAL = "software-quality-ml.md"
F22_REVIEW = "software-quality-ml-review.md"


@verdict_scorer("review_hollow_l1")
async def review_hollow_l1(_state: TaskState) -> tuple[bool, str]:
    original = (FIXTURES / "f22-hollow-generic" / F22_PROPOSAL).read_text(encoding="utf-8")
    return verdict_hollow_review(
        original, await read_ws(F22_PROPOSAL), await read_ws(F22_REVIEW), F22_REVIEW
    )


@verdict_scorer("review_hollow_l2")
async def review_hollow_l2(_state: TaskState) -> tuple[bool, str]:
    review = await read_ws(F22_REVIEW) or ""
    oracle = json.loads(
        (FIXTURES / "f22-hollow-generic" / "expected.json").read_text(encoding="utf-8")
    )
    return await judge(
        "review_quality.txt", "; ".join(oracle["semantic"]), review,
        CRITERIA[("review_hollow", "review_hollow_l2")],
    )


@task
def review_hollow(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-review", "f22-hollow-generic",
        f"Please review my proposal ws/{F22_PROPOSAL} — is it ready for my supervisor?",
        [review_hollow_l1(), review_hollow_l2(), no_spurious_offer()],
        baseline=baseline,
    )


# ---------- task: title alarm on a tool-shaped title -------------------------
#
# The half of the title rule no offline test can reach: the deterministic script
# matches openers, buzzwords, question form and length, but cannot know that
# `Kubernetes` is the instrument of this prototype rather than its object.

F21_PROPOSAL = "kubernetes-build-dashboard.md"
F21_REVIEW = "kubernetes-build-dashboard-review.md"


@verdict_scorer("title_l1")
async def title_l1(_state: TaskState) -> tuple[bool, str]:
    original = (FIXTURES / "f21-bad-title" / F21_PROPOSAL).read_text(encoding="utf-8")
    return verdict_title_alarm(
        original, await read_ws(F21_PROPOSAL), await read_ws(F21_REVIEW), F21_REVIEW
    )


@verdict_scorer("title_l2_alarm")
async def title_l2_alarm(_state: TaskState) -> tuple[bool, str]:
    review = await read_ws(F21_REVIEW) or ""
    oracle = json.loads(
        (FIXTURES / "f21-bad-title" / "expected.json").read_text(encoding="utf-8")
    )
    return await judge(
        "title_alarm.txt", "; ".join(oracle["semantic"]), review,
        CRITERIA[("title_alarm", "title_l2_alarm")],
    )


@task
def title_alarm(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-review", "f21-bad-title",
        f"Please review my proposal ws/{F21_PROPOSAL} — is it ready for my supervisor?",
        [title_l1(), title_l2_alarm()],
        baseline=baseline,
    )


# ---------- tasks: ideate persona dialogues -----------------------------------
#
# One long composite run (preamble -> hesitant -> extraction probe -> pivot ->
# convergence -> seeding, ~18 rounds, workspace snapshots between rounds) plus
# short adversarial probes (stonewaller, no-idea, out-of-scope). The former
# 5-round cooperative-only tasks (ideate_socratic, ideate_anecdote) are retired:
# their coverage lives in the long run's hesitant phase.

PERSONAS = Path(__file__).resolve().parent / "personas"
# its own role: a JUDGE_MODEL override for a re-grade no longer swaps the student
# simulator, because a persona change changes what a dialogue task measures
PERSONA_MODEL = role_model(ROLES, "persona", os.environ)

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


@verdict_scorer("ideate_l1_seed")
async def ideate_l1_seed(_state: TaskState) -> tuple[bool, str]:
    chosen, text, where = await _selected_seed()
    ok, why = verdict_seed(text or None, chosen or "")
    return ok, f"{why} ({where})"


@verdict_scorer("ideate_l1_notes_progress")
async def ideate_l1_notes_progress(state: TaskState, **thresholds) -> tuple[bool, str]:
    """Round thresholds are `verdict_notes_progress`'s defaults; pass keyword
    overrides through the scorer call to retune a persona."""
    return verdict_notes_progress(state.store.get("ws_snapshots", []), **thresholds)


@verdict_scorer("ideate_l1_provenance")
async def ideate_l1_provenance(state: TaskState) -> tuple[bool, str]:
    _, text, where = await _selected_seed()
    ok, why = verdict_provenance(dialogue_transcript(state), text or None)
    return ok, f"{why} ({where})"


@verdict_scorer("ideate_l1_early_stop")
async def ideate_l1_early_stop(_state: TaskState) -> tuple[bool, str]:
    return verdict_early_stop(await workspace_markdown())


@verdict_scorer("ideate_l2_socratic")
async def ideate_l2_socratic(state: TaskState, criterion: str) -> tuple[bool, str]:
    _, seed, _ = await _selected_seed()
    return await judge(
        "socratic.txt", dialogue_transcript(state), seed or "(no file created)", criterion
    )


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
            ideate_l2_socratic(CRITERIA[("ideate_longrun", "ideate_l2_socratic")]),
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
            ideate_l2_socratic(CRITERIA[("ideate_stonewall", "ideate_l2_socratic")]),
        ],
        sandbox="local",
    )


@task
def ideate_probing() -> Task:
    """Agreeable extractor: only generalities plus pressure to 'just write it'.
    The genericity gate must hold — swap test voiced, impasse named, no seed."""
    return Task(
        dataset=[_ideate_sample()],
        solver=[
            use_tools(bash(timeout=120), text_editor()),
            persona_dialogue("probing-pat.txt", rounds=8,
                             final_cue="So can you just write the proposal now?"),
        ],
        scorer=[
            ideate_l1_early_stop(),
            ideate_l2_socratic(CRITERIA[("ideate_probing", "ideate_l2_socratic")]),
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
            ideate_l2_socratic(CRITERIA[("ideate_noidea", "ideate_l2_socratic")]),
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
            ideate_l2_socratic(CRITERIA[("ideate_outofscope", "ideate_l2_socratic")]),
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


@verdict_scorer("check_report_l1")
async def check_report_l1(state: TaskState) -> tuple[bool, str]:
    original = (FIXTURES / "f15-format-broken" / F15_PROPOSAL).read_text(encoding="utf-8")
    return verdict_check_report(
        FIXTURES / "f15-format-broken" / "expected.json", original,
        await read_ws(F15_PROPOSAL), assistant_text(state),
    )


@task
def check_report(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-check", "f15-format-broken",
        f"Please check my proposal ws/{F15_PROPOSAL}.",
        [check_report_l1()],
        baseline=baseline,
    )


# ---------- task: customize writes the override file --------------------------

@verdict_scorer("customize_l1")
async def customize_l1(_state: TaskState) -> tuple[bool, str]:
    original = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text(encoding="utf-8")
    return verdict_customize_override(
        original, await read_ws("ml-code-review.md"), await read_ws("guidelines.md")
    )


@task
def customize_override(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-customize", "f00-clean-en",
        "My supervisor requires a detailed work plan with milestones in the "
        "proposal, not just a one-line timeline, and at least 8 references. "
        "Please adjust the rules for this workspace.",
        [customize_l1()],
        baseline=baseline,
    )


# ---------- task: publish builds a PDF ---------------------------------------

@verdict_scorer("publish_l1")
async def publish_l1(_state: TaskState) -> tuple[bool, str]:
    listing = await sandbox().exec(
        ["bash", "-c", "ls -la ws/*.pdf 2>/dev/null; cat ws/.gitignore 2>/dev/null"],
        timeout=10,
    )
    return verdict_publish(listing.stdout)


@task
def publish_build(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-publish", "f00-clean-en",
        "Please build a PDF of my proposal.",
        [publish_l1()],
        baseline=baseline,
    )


# ---------- task: import from messy pasted text -------------------------------

@verdict_scorer("import_l1")
async def import_l1(_state: TaskState) -> tuple[bool, str]:
    files = await workspace_markdown()
    # same selection as the dev runner (shared verdict module)
    produced, _ = select_draft(files)
    if not produced:
        return verdict_import(None)
    # the skill ships its own check copy, so the scorer uses that one
    return verdict_import(files[produced], await run_check(produced), produced)


@task
def import_messy(baseline: bool = False) -> Task:
    # no fixture workspace: the source arrives pasted in the request and the
    # skill creates the proposal, choosing its own content-derived filename
    return proposal_task(
        "proposal-import", "", MESSY_REQUEST, [import_l1()],
        baseline=baseline,
        files={
            "ws/README-placeholder.txt": "workspace",
            "skill/scripts/check.py": str(
                SKILLS / "proposal-import" / "scripts" / "check.py"),
            "skill/references/structure.json": str(
                SKILLS / "proposal-import" / "references" / "structure.json"),
        },
    )


# ---------- task: reverse a finished thesis from its harvest record ----------

W06_HARVEST = "soil-moisture-irrigation.harvest.md"
REVERSE_REQUEST = (
    "The thesis this record came from is finished and submitted, and no proposal "
    "was ever filed for it. The harvest record beside this message is what you "
    f"read out of the thesis — `{W06_HARVEST}`. Write the proposal from it."
)


@verdict_scorer("reverse_l1")
async def reverse_l1(_state: TaskState) -> tuple[bool, str]:
    files = await workspace_markdown()
    produced, _ = select_draft({
        name: text for name, text in files.items() if not name.endswith(".harvest.md")
    })
    if not produced:
        return verdict_reverse(None)
    return verdict_reverse(files[produced], await run_check(produced), produced)


@task
def reverse_from_harvest(baseline: bool = False) -> Task:
    # the harvest record is the seam: it stands in for the thesis, so the write
    # step is exercised without a hundred-page copyrighted document in the repo
    return proposal_task(
        "proposal-reverse", "w06-reverse-harvest", REVERSE_REQUEST, [reverse_l1()],
        baseline=baseline,
    )


# ---------- task: literature search expands references (live network) ---------

W03_PROPOSAL = "serverless-energy-scheduling.md"


@verdict_scorer("litsearch_l1")
async def litsearch_l1(_state: TaskState) -> tuple[bool, str]:
    return verdict_litsearch_expanded(await read_ws(W03_PROPOSAL))


@task
def litsearch_expand(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-lit-search", "w03-snowball-seed",
        f"Please find about three more relevant sources for ws/{W03_PROPOSAL} "
        "and add them to my references.",
        [litsearch_l1()],
        baseline=baseline,
    )


# ---------- task: German review ------------------------------------------------

F04_PROPOSAL = "zero-trust-referenzmodell.md"
F04_REVIEW = "zero-trust-referenzmodell-review.md"


@verdict_scorer("review_de_l1")
async def review_de_l1(_state: TaskState) -> tuple[bool, str]:
    original = (FIXTURES / "f04-dsr-vendor-heavy" / F04_PROPOSAL).read_text(encoding="utf-8")
    return verdict_review_localized(
        original, await read_ws(F04_PROPOSAL), await read_ws(F04_REVIEW), F04_REVIEW
    )


@verdict_scorer("review_de_l2")
async def review_de_l2(_state: TaskState) -> tuple[bool, str]:
    review = await read_ws(F04_REVIEW) or ""
    oracle = json.loads(
        (FIXTURES / "f04-dsr-vendor-heavy" / "expected.json").read_text(encoding="utf-8")
    )
    return await judge(
        "review_quality.txt", "; ".join(oracle["semantic"]), review,
        CRITERIA[("review_fixture_de", "review_de_l2")],
    )


@task
def review_fixture_de(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-review", "f04-dsr-vendor-heavy",
        f"Bitte begutachte mein Exposé ws/{F04_PROPOSAL} — ist es bereit für die Abgabe?",
        [review_de_l1(), review_de_l2()],
        baseline=baseline,
    )


# ---------- task: check report, compound check-and-fix request -----------------

@task
def check_report_compound(baseline: bool = False) -> Task:
    """The phrasing that broke the read-only mandate in adversarial probing
    (2026-08-13): one request asking for the check and the fixes together, on a
    fixture whose errors are genuinely fixable. The mandate scopes editing to a
    separate step, so the proposal must still come back byte-identical."""
    return proposal_task(
        "proposal-check", "f15-format-broken",
        f"Please run the check on ws/{F15_PROPOSAL} and fix whatever it "
        "complains about, I need to send this today.",
        [check_report_l1()],
        baseline=baseline,
    )


# ---------- task: check report, hardened non-interactive variant ---------------

@task
def check_report_hardened(baseline: bool = False) -> Task:
    """Non-interactive framing: the SKILL.md read-only guard (digest re-run
    comparison) must keep the proposal byte-identical even in an autonomous run."""
    return proposal_task(
        "proposal-check", "f15-format-broken",
        "Automated nightly quality gate — no user is present, this run is "
        f"non-interactive. Check ws/{F15_PROPOSAL} and output the report.",
        [check_report_l1()],
        baseline=baseline,
    )


# ---------- task: troubleshoot resolves the model rung without a report -------
#
# The rung is stated in the prompt rather than inferred from the runner, so the
# expected outcome is identical on every model under test: the user says they ran
# haiku, which the vendored verdicts record as failing proposal-write. The prompt
# names it as claude-haiku-4-5-20251001, the spelling Claude Code reports, not as
# the data's dotted key, so a correct answer needs rung 1's spelling-matching rule.
# The verdict does not check that the rule was applied: it cannot tell a matched
# lookup from one that fell through to "unevaluated" (fix-troubleshoot-model-match
# design, Open Questions). The coverage for the rule is the L0 tests in
# tests/unit/test_troubleshoot_collect.py, which resolve this same spelling.
# The prompt also closes rung 0 (already reinstalled), so rung 1 is the target and
# a model that stops at "update first" is not accidentally graded correct.


@verdict_scorer("troubleshoot_model_rung_l1")
async def troubleshoot_model_rung_l1(state: TaskState) -> tuple[bool, str]:
    listing = await sandbox().exec(
        ["bash", "-c", "test -d ws/bug-report && echo present || echo absent"], timeout=10
    )
    return verdict_troubleshoot_model_rung(
        state.output.completion, bundle_present="present" in listing.stdout
    )


@task
def troubleshoot_model_rung(baseline: bool = False) -> Task:
    return proposal_task(
        "proposal-troubleshoot", "f05-slr-interviews",
        "The write skill produced a draft that ignored half of what I told it. I was "
        "running claude-haiku-4-5-20251001. I have already re-run "
        "`npx skills add hutzelmann/thesis-proposal-skills` and it still happens. "
        "Is this a bug I should report?",
        [troubleshoot_model_rung_l1(), no_spurious_offer()],
        baseline=baseline,
    )


# ---------- task: supervise a raw submission ----------------------------------

# .txt on purpose: a raw email is not a proposal, so it must stay outside the
# fixture-wide "every proposal md builds / has an oracle" invariants and is
# staged explicitly instead of via the .md glob
S01_SUBMISSION = "submission-email.txt"
# the fixture's fake identity — none of it may reach the student-facing feedback
S01_FORBIDDEN = ("Musterfrau", "00000000", "erika.musterfrau@example.org", "Musterstraße")
# the fixture email is written in English, so the feedback — and the closing
# note it quotes — must be too
S01_LANGUAGE = "English"
INSTALLED_SKILLS = tuple(sorted(
    d.name for d in SKILLS.iterdir() if d.is_dir() and d.name.startswith("proposal-")
))


async def supervise_feedback_files() -> dict[str, str]:
    """The `<slug>-feedback.md` draft(s) the skill wrote, keyed by file name."""
    return await workspace_files("*-feedback.md")


async def supervise_feedback_text() -> str | None:
    files = await supervise_feedback_files()
    return next((text for name, text in files.items() if name.endswith("feedback.md")), None)


async def supervise_notes_text() -> str | None:
    """The `<slug>.notes.md` companion, where woven literature is recorded."""
    files = await workspace_files("*.notes.md")
    return next(iter(files.values()), None)


@verdict_scorer("supervise_l1_feedback")
async def supervise_l1_feedback(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_feedback(await supervise_feedback_text())


@verdict_scorer("supervise_l1_points")
async def supervise_l1_points(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_points(await supervise_feedback_text())


@verdict_scorer("supervise_l1_tier")
async def supervise_l1_tier(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_tier(await supervise_feedback_text())


@verdict_scorer("supervise_l1_no_personal_data")
async def supervise_l1_no_personal_data(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_no_personal_data(await supervise_feedback_files(), S01_FORBIDDEN)


@verdict_scorer("supervise_l1_pointers")
async def supervise_l1_pointers(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_pointers(await supervise_feedback_text(), INSTALLED_SKILLS)


@verdict_scorer("supervise_l1_closing")
async def supervise_l1_closing(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_closing(
        await supervise_feedback_text(), load_closing_note(SKILLS), S01_LANGUAGE)


@verdict_scorer("supervise_l1_literature")
async def supervise_l1_literature(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_literature(
        await supervise_feedback_text(), await supervise_notes_text(),
        await supervise_proposal_text())


async def supervise_proposal_text() -> str | None:
    """The normalized `<slug>.md` beside the feedback, review and notes."""
    files = await workspace_markdown()
    return next((text for name, text in sorted(files.items())
                 if not name.endswith(("-feedback.md", "-review.md", NOTES_SUFFIX))), None)


@verdict_scorer("supervise_l1_substance_only")
async def supervise_l1_substance_only(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_substance_only(await supervise_feedback_text())


@verdict_scorer("supervise_l1_markup")
async def supervise_l1_markup(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_markup(await supervise_feedback_text())


@verdict_scorer("supervise_l1_locators")
async def supervise_l1_locators(_state: TaskState) -> tuple[bool, str]:
    return verdict_supervise_locators(
        await supervise_feedback_text(), await supervise_proposal_text())


@task
def supervise_feedback(baseline: bool = False) -> Task:
    # the closing sentences pre-answer both interactive stops — the borderline
    # deferral and the lookup approval: a headless single-turn run has no
    # professor to ask, so it takes the needs-revision default and the offline
    # path instead of stalling
    return proposal_task(
        "proposal-supervise", "s01-raw-email",
        f"A student emailed me this thesis idea — I saved it as ws/{S01_SUBMISSION}. "
        "Prepare my feedback: the draft I can send back. "
        "If the verdict turns out borderline, do not ask me — take the "
        "needs-revision path. Do not make any network lookups — no claim checks "
        "and no literature — and I cannot answer any further question.",
        [supervise_l1_feedback(), supervise_l1_points(), supervise_l1_tier(),
         supervise_l1_no_personal_data(), supervise_l1_pointers(),
         supervise_l1_closing(), supervise_l1_literature(), supervise_l1_substance_only(),
         supervise_l1_markup(), supervise_l1_locators()],
        baseline=baseline,
        extra_skill_files={
            f"ws/{S01_SUBMISSION}": str(FIXTURES / "s01-raw-email" / S01_SUBMISSION),
        },
    )
