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
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import pytest
import skill_evals
import support
from fixture_paths import staged_tree
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


SKILL_HOME = skill_evals.SKILL_HOME


def workspace_names(files) -> set[str]:
    """The staged names that are the user's workspace, the installed skills
    left out."""
    return {name for name in files if not name.startswith(f"{SKILL_HOME}/")}


@pytest.mark.parametrize("fixture", ["f16-figures-import", "w06-reverse-harvest",
                                     "w09-revised-round"])
def test_the_sandbox_root_is_the_fixtures_workspace(fixture):
    """The fixture is the workspace root (design D24 of adopt-proposal-folders),
    and the sandbox's root is the agent's working directory, so the fixture
    tree lands there as it lies, figures and companions included, its oracle
    and import source left behind; the skill is installed beside it the way a
    project-level install puts it, under a hidden folder no listing reads."""
    files = skill_evals.stage_files(fixture, "proposal-check")
    staged = workspace_names(files)
    assert staged == set(staged_tree(fixture))
    assert staged
    assert not {"expected.json", "submission.pdf"} & staged
    assert f"{SKILL_HOME}/proposal-check/scripts/check.py" in files
    assert f"{SKILL_HOME}/proposal-check/references/structure.json" in files


def materialize(files: dict[str, str], root: Path) -> None:
    """A sample's files written out as Inspect stages them: a value naming a
    host file is copied, any other value is the file's content."""
    for name, value in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        source = Path(value)
        if source.is_file():
            target.write_bytes(source.read_bytes())
        else:
            target.write_text(value, encoding="utf-8")


def request_of(prompt: str) -> str:
    return prompt.split("User request: ", 1)[1]


# the script-location paragraph's command, as every check-shipping skill writes it
CHECK_COMMAND = re.compile(r"python3 (\S+/scripts/check\.py) <location>/<slug>/<slug>\.md")
# tasks whose skill ships the check and whose request names a staged proposal
CHECKED_TASKS = {
    "write_from_seed": "W01_PROPOSAL",
    "write_rich_seed": "W08_PROPOSAL",
    "write_repair_citations": "F27_PROPOSAL",
    "check_report": "F15_PROPOSAL",
    "check_report_compound": "F15_PROPOSAL",
    "check_report_hardened": "F15_PROPOSAL",
}


@pytest.mark.parametrize(("task_name", "constant"), sorted(CHECKED_TASKS.items()))
def test_the_documented_check_finds_the_proposal_where_the_agent_works(task_name, constant,
                                                                       tmp_path):
    """The agent runs the skill's documented check command from its own working
    directory, which Inspect's bash tool never changes: the sandbox's root.
    That root must be the workspace root, the command's script path must
    resolve there, and the proposal must sit where the request names it,
    measured from there: otherwise every check the agent runs reports a
    misplaced proposal and loses the workspace's `guidelines.md`, though the
    scorer's own check is clean (testing-harness: Check run from the staged
    workspace's root)."""
    sample = getattr(skill_evals, task_name)().dataset[0]
    materialize(sample.files, tmp_path)
    script = CHECK_COMMAND.search(sample.input).group(1)
    proposal = getattr(skill_evals, constant)
    named = [token.rstrip(".,;:") for token in request_of(sample.input).split()
             if token.rstrip(".,;:").endswith(proposal)]
    assert named, f"the request does not name {proposal}"
    done = subprocess.run([sys.executable, script, named[0], "--json"], cwd=tmp_path,
                          capture_output=True, encoding="utf-8", timeout=60)
    assert done.returncode in (0, 1), done.stderr
    data = json.loads(done.stdout)
    rules = {finding["rule"] for finding in data["findings"]}
    assert "proposal-misplaced" not in rules, done.stdout
    assert "proposal-folder-mismatch" not in rules
    if (tmp_path / "guidelines.md").is_file():
        assert data["guidelines"] == "working-directory"


@pytest.mark.parametrize("task_name", sorted(EXPECTED_SCORERS))
def test_the_prompt_frames_the_working_directory_as_the_workspace(task_name):
    """No prompt sends the agent to a workspace below its working directory:
    the skill's instructions say scripts run from the workspace root, the
    working directory, and the sandbox gives the agent no other."""
    prompt = getattr(skill_evals, task_name)().dataset[0].input
    assert "ws/" not in prompt
    assert "Your working directory is the" in prompt


# Every scorer constant that names a workspace file, by the task that reads it.
# A proposal or harvest record must be staged where the constant says; a review
# is written by the run, so it must name the `review.md` of a staged proposal's
# folder (adopt-proposal-folders, task 5.4).
SCORER_PATHS = {
    "write_from_seed": ("W01_PROPOSAL",),
    "write_rich_seed": ("W08_PROPOSAL",),
    "write_repair_citations": ("F27_PROPOSAL",),
    "review_fixture": ("F05_PROPOSAL", "F05_REVIEW"),
    "review_hollow": ("F22_PROPOSAL", "F22_REVIEW"),
    "review_ready": ("READINESS_PROPOSAL", "READINESS_REVIEW"),
    "review_dependency": ("READINESS_PROPOSAL", "READINESS_REVIEW"),
    "review_converge": ("READINESS_PROPOSAL", "READINESS_REVIEW"),
    "title_alarm": ("F21_PROPOSAL", "F21_REVIEW"),
    "check_report": ("F15_PROPOSAL",),
    "check_report_compound": ("F15_PROPOSAL",),
    "check_report_hardened": ("F15_PROPOSAL",),
    "customize_override": ("F00_PROPOSAL",),
    "reverse_from_harvest": ("W06_HARVEST",),
    "litsearch_expand": ("W03_PROPOSAL",),
    "review_fixture_de": ("F04_PROPOSAL", "F04_REVIEW"),
    "supervise_ready": ("SUBMITTED_PROPOSAL",),
}
# a file the user's request names, by its path from the workspace root
REQUEST_PATH = re.compile(r"(?<![\w/.-])((?:[\w-]+/)*[\w-]+\.(?:md|txt|pdf))(?![\w/])")


def named_paths(task_name: str) -> list[tuple[str, str]]:
    """(what names it, the workspace path) for every file the task's request
    names and every scorer constant mapped to it."""
    prompt = getattr(skill_evals, task_name)().dataset[0].input
    named = [("the request", path) for path in REQUEST_PATH.findall(request_of(prompt))]
    return named + [(constant, getattr(skill_evals, constant))
                    for constant in SCORER_PATHS.get(task_name, ())]


def unstaged(task_name: str) -> list[str]:
    staged = workspace_names(getattr(skill_evals, task_name)().dataset[0].files)
    missing = []
    for source, path in named_paths(task_name):
        target = path
        if source.endswith("_REVIEW"):
            folder = PurePosixPath(path).parent
            ok = PurePosixPath(path).name == "review.md" and folder.name
            target = f"{folder}/{folder.name}.md" if ok else path
        if target not in staged:
            missing.append(f"{source}: {path}")
    return missing


@pytest.mark.parametrize("task_name", sorted(EXPECTED_SCORERS))
def test_every_workspace_path_a_task_names_is_staged(task_name):
    """The prompt and the scorers read the workspace where the fixture's tree
    put it: a flat name left over from before the folder layout would send the
    model, or the verdict, to a file that is not there."""
    assert unstaged(task_name) == []


def test_every_scorer_path_constant_belongs_to_a_task():
    constants = {name for name in vars(skill_evals)
                 if name.isupper() and name.endswith(("_PROPOSAL", "_REVIEW", "_HARVEST"))}
    mapped = {c for names in SCORER_PATHS.values() for c in names}
    assert constants == mapped


# ---------- the sandbox's workspace listings (adopt-proposal-folders, task 5.4) -----


class LocalSandbox:
    """Inspect's local sandbox in miniature: every command runs for real with
    `root` as the sandbox's working directory, so a listing is measured, not
    assumed."""

    def __init__(self, root: Path):
        self.root = root
        self.calls: list[tuple[list[str], str | None]] = []

    async def exec(self, cmd, timeout=None, cwd=None, **_kwargs):
        self.calls.append((list(cmd), cwd))
        # the sandbox's `python3` is this interpreter, on every platform
        cmd = [sys.executable, *cmd[1:]] if cmd[0] == "python3" else list(cmd)
        done = subprocess.run(cmd, cwd=self.root / cwd if cwd else self.root,
                              capture_output=True, encoding="utf-8", timeout=timeout)
        return SimpleNamespace(stdout=done.stdout, stderr=done.stderr,
                               returncode=done.returncode, success=done.returncode == 0)

    async def read_file(self, path, text=True):
        target = self.root / path
        return target.read_text(encoding="utf-8") if text else target.read_bytes()


NOTES = "# Notes\n\n## Decisions\n\n## Open Points\n\n## Next Focus\n\n" \
        "## Excluded Literature\n\n## Log\n"


@pytest.fixture
def sandbox_ws(tmp_path, monkeypatch):
    """A staged workspace at the sandbox's root: a proposal folder with its
    companions, a folder that is no proposal folder, root files, and the
    installed skill under its hidden folder. Written as bytes: text mode turns
    each `\\n` into `\\r\\n` on Windows, and the snapshot sizes are measured on
    disk."""
    files = {
        "ml-code-review/ml-code-review.md": "# Proposal\n",
        "ml-code-review/notes.md": NOTES,
        "ml-code-review/feedback.md": "Verdict: ready.\n",
        "ml-code-review/review.md": "1. Finding.\n",
        "ml-code-review/img/a.png": "png",
        "meetings/feedback.md": "not a proposal's\n",
        "guidelines.md": "Prose.\n",
        "feedback.md": "at the root\n",
        f"{SKILL_HOME}/proposal-supervise/SKILL.md": "hidden\n",
        f"{SKILL_HOME}/proposal-supervise/references/notes.md": NOTES,
    }
    for rel, text in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_bytes(text.encode("utf-8"))
    box = LocalSandbox(tmp_path)
    monkeypatch.setattr(skill_evals, "sandbox", lambda *_a, **_k: box)
    return box


@pytest.mark.usefixtures("sandbox_ws")
def test_the_workspace_listing_walks_the_folders():
    markdown = asyncio.run(skill_evals.workspace_markdown())
    assert sorted(markdown) == [
        "feedback.md", "guidelines.md", "meetings/feedback.md", "ml-code-review/feedback.md",
        "ml-code-review/ml-code-review.md", "ml-code-review/notes.md",
        "ml-code-review/review.md"]
    assert markdown["ml-code-review/notes.md"] == NOTES


@pytest.mark.usefixtures("sandbox_ws")
def test_the_snapshot_sizes_walk_the_folders():
    sizes = asyncio.run(skill_evals._ws_sizes())
    assert sizes["ml-code-review/notes.md"] == len(NOTES.encode())
    assert "ml-code-review/img/a.png" not in sizes, "markdown only"
    assert not [name for name in sizes if name.startswith(".")]


@pytest.mark.usefixtures("sandbox_ws")
def test_supervise_reads_role_files_of_a_proposal_folder_only():
    assert asyncio.run(skill_evals.supervise_feedback_files()) == {
        "ml-code-review/feedback.md": "Verdict: ready.\n"}
    assert asyncio.run(skill_evals.supervise_notes_text()) == NOTES
    assert asyncio.run(skill_evals.supervise_proposal_text()) == "# Proposal\n"


def test_the_ideate_sample_starts_from_an_empty_workspace():
    """The dialogue tasks start ideation from nothing: no workspace file is
    staged, only the skill and its literature-search sibling, so no setup has
    to empty anything."""
    sample = skill_evals._ideate_sample()
    assert sample.setup is None
    assert workspace_names(sample.files) == set()
    assert f"{SKILL_HOME}/proposal-lit-search/SKILL.md" in sample.files
    assert f"{SKILL_HOME}/proposal-ideate/references/guidelines.md" in sample.files


def publish_verdict() -> tuple[bool, str]:
    return skill_evals.verdict_publish(*asyncio.run(skill_evals.publish_listing()))


def test_the_publish_listing_reads_the_proposals_folder(sandbox_ws):
    folder = sandbox_ws.root / "ml-code-review"
    (folder / "ml-code-review.pdf").write_bytes(b"%PDF")
    (folder / ".gitignore").write_text("*.pdf\n*.typ\n", encoding="utf-8")
    built, gitignore = asyncio.run(skill_evals.publish_listing())
    assert "ml-code-review/ml-code-review.pdf" in built
    assert gitignore == "*.pdf\n*.typ\n"
    assert publish_verdict()[0]
    # a build and its .gitignore at the workspace root are not the folder's
    for name in ("ml-code-review.pdf", ".gitignore"):
        (folder / name).rename(sandbox_ws.root / name)
    assert not publish_verdict()[0]


def test_a_gitignore_without_a_build_is_no_publish(sandbox_ws):
    """The `.gitignore` names `*.pdf`; with no PDF beside it the run built
    nothing, which a listing line must not stand in for."""
    folder = sandbox_ws.root / "ml-code-review"
    (folder / ".gitignore").write_text("*.pdf\n*.typ\n", encoding="utf-8")
    passed, why = publish_verdict()
    assert not passed
    assert "no PDF produced" in why
    (folder / "ml-code-review.pdf").write_bytes(b"")
    assert not publish_verdict()[0], "an empty file is no build"


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
