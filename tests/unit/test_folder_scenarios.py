"""L0: the dev runner's folder-layout scenarios (testing-harness: Folder-layout
dev scenarios; adopt-proposal-folders, design D12, D22, D24 and Q7), with no
model.

Covered: what each new scenario stages and asks; the `hide` key's PATH, its
login-shell pre-check and the required-tool preconditions, which decide before
any model call whether a run can measure what it is meant to; and each
scenario's verdict over an after-state written by hand. Where a verdict runs
the check script, it runs for real.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import claude_runner
import pytest
from claude_runner import (
    EXIT_FAIL,
    EXIT_PASS,
    EXIT_RUNNER,
    EXIT_UNTESTED,
    EXTRACTION_TOOLS,
    SCENARIOS,
    RunnerFailure,
    calls_by_turn,
    feedback_files,
    hidden_tool_path,
    login_shell_finds,
    main,
    precondition_problems,
    stage,
    verdict,
)
from fixture_paths import fixture_dir
from helpers import NOTES_TEXT
from l1_checks import LATEX_ENGINES

NEW = ("ideate_from_scratch", "import_figures", "publish_figures_typst",
       "publish_figures_latex", "publish_figures_docx", "litsearch_keep")
F16 = "sensor-anomaly-triage"
F16_PROPOSAL = f"{F16}/{F16}.md"
W03 = "serverless-energy-scheduling"
STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"
posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX shells and links")
linux_only = pytest.mark.skipif(not sys.platform.startswith("linux"),
                                reason="the dev runner hides tools on Linux only")


def recorded_events() -> list[dict]:
    lines = (STREAMS / "recorded-result.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def files(ws: Path) -> list[str]:
    return sorted(p.relative_to(ws).as_posix() for p in ws.rglob("*")
                  if p.is_file() and not any(part.startswith(".")
                                             for part in p.relative_to(ws).parts))


def executable(path: Path, body: str = "#!/bin/sh\nexit 0\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def tool_use(name: str, **arguments) -> dict:
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "t", "name": name, "input": arguments}]}}


def tool_result(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t", "content": text}]}}


def turn_end(text: str = "Done.") -> dict:
    return {"type": "result", "subtype": "success", "result": text}


# ---------- the scenarios and what they stage --------------------------------------


@pytest.mark.parametrize("name", NEW)
def test_each_new_scenario_is_on_the_command_line(name):
    assert name in SCENARIOS
    assert name in claude_runner.build_parser().format_help()
    assert claude_runner.build_parser().parse_args([name]).scenario == name


HARNESS_README = Path(claude_runner.HARNESS) / "README.md"


def test_the_harness_readme_names_every_scenario_and_no_other():
    """Task 5.6: the scenario names in harness/README.md match SCENARIOS — every
    scenario is described there, and every `poe dev` command names one."""
    text = HARNESS_README.read_text(encoding="utf-8")
    missing = [name for name in SCENARIOS if f"`{name}`" not in text and f" {name} " not in text]
    assert missing == []
    named = {chunk.split()[0].strip("`.,;:()") for chunk in text.split("poe dev ")[1:]
             if chunk.strip()}
    commands = {name for name in named if name and name[0] not in "-<"}
    assert commands
    assert commands - {*SCENARIOS, claude_runner.CANARY} == set()


def test_ideation_from_scratch_stages_nothing_and_takes_three_turns():
    scenario = SCENARIOS["ideate_from_scratch"]
    assert not scenario.get("fixture")
    assert claude_runner.staging_plan(scenario) == {}
    first, topic, title = scenario["request"], *scenario["followups"]
    assert "topic" in first.lower()
    assert "don't look anything up" in first
    assert "rough topic" in topic.lower()
    assert "working title" in title.lower()
    assert "enough" in title.lower()


def test_import_figures_stages_the_source_pdf_alone(tmp_path):
    scenario = SCENARIOS["import_figures"]
    stage(scenario, tmp_path, install_skill=False)
    assert files(tmp_path) == ["submission.pdf"]
    source = fixture_dir("f16-figures-import") / "submission.pdf"
    assert (tmp_path / "submission.pdf").read_bytes() == source.read_bytes()
    assert scenario["requires"] == (EXTRACTION_TOOLS,)
    assert "extract" in scenario["request"].lower()


@pytest.mark.parametrize(("name", "hidden"), [
    ("publish_figures_typst", ()),
    ("publish_figures_latex", ("typst",)),
    ("publish_figures_docx", ("typst", *LATEX_ENGINES)),
])
def test_the_publish_scenarios_hide_by_tier(name, hidden, tmp_path):
    scenario = SCENARIOS[name]
    assert tuple(scenario.get("hide", ())) == hidden
    assert scenario["proposal"] == F16_PROPOSAL
    assert F16_PROPOSAL in scenario["request"]
    if hidden:
        assert "install nothing" in scenario["request"].lower()
    stage(scenario, tmp_path, install_skill=False)
    assert files(tmp_path) == [f"{F16}/img/a.png", f"{F16}/img/b.png", F16_PROPOSAL]


def test_the_keep_scenario_asks_to_keep_the_candidate_list():
    scenario = SCENARIOS["litsearch_keep"]
    assert scenario["fixture"] == "w03-snowball-seed"
    assert scenario["family"] == "keep"
    assert "keep the candidate list" in scenario["request"]


# ---------- the hidden-tool PATH and its pre-check ---------------------------------


@posix_only
def test_the_hidden_path_links_everything_but_the_hidden_tools(tmp_path):
    first, second = tmp_path / "usr-bin", tmp_path / "local-bin"
    for name in ("typst", "xelatex", "pandoc", "ls"):
        executable(first / name)
    executable(second / "ls")  # a later folder's duplicate: the first one wins
    executable(second / "lualatex")
    (first / "notes.txt").write_text("not executable", encoding="utf-8")
    path = hidden_tool_path(tmp_path / "bin", os.pathsep.join(
        [str(first), "", str(second), str(tmp_path / "gone")]), ("typst", "lualatex"))
    assert path == str(tmp_path / "bin")
    assert sorted(p.name for p in (tmp_path / "bin").iterdir()) == ["ls", "pandoc", "xelatex"]
    assert shutil.which("typst", path=path) is None
    assert shutil.which("pandoc", path=path) is not None
    assert (tmp_path / "bin" / "ls").resolve() == (first / "ls").resolve()


def fake_shell(tmp_path: Path, extra: Path | None = None, body: str = "") -> Path:
    """A shell that records its arguments and runs its script under /bin/sh,
    with `extra` put back on PATH the way a system profile appends /usr/bin."""
    prepend = f'PATH="{extra}:$PATH"; export PATH\n' if extra else ""
    return executable(tmp_path / "fake-shell", (
        "#!/bin/sh\n"
        f'printf "%s\\n" "$@" > "{tmp_path / "shell-args"}"\n'
        f"{body}{prepend}"
        'while [ $# -gt 1 ]; do shift; done\n'
        'exec /bin/sh -c "$1"\n'))


@posix_only
def test_a_login_shell_that_puts_a_hidden_tool_back_is_caught(tmp_path):
    """Scenario: Hidden tool still reachable."""
    executable(tmp_path / "system" / "typst")
    hidden = hidden_tool_path(tmp_path / "bin", "", ())
    env = {"PATH": hidden, "SHELL": str(fake_shell(tmp_path, tmp_path / "system")),
           "HOME": str(tmp_path)}
    assert login_shell_finds(env, ("typst", "xelatex")) == ["typst"]
    args = (tmp_path / "shell-args").read_text(encoding="utf-8").splitlines()
    assert args[:3] == ["-l", "-i", "-c"]


@posix_only
def test_a_login_shell_that_keeps_the_path_finds_nothing(tmp_path):
    executable(tmp_path / "system" / "typst")
    env = {"PATH": hidden_tool_path(tmp_path / "bin", "", ()),
           "SHELL": str(fake_shell(tmp_path)), "HOME": str(tmp_path)}
    assert login_shell_finds(env, ("typst",)) == []


@posix_only
def test_a_login_shell_that_does_not_finish_is_untested(tmp_path):
    env = {"PATH": "/usr/bin:/bin", "SHELL": str(fake_shell(tmp_path, body="exec sleep 5\n")),
           "HOME": str(tmp_path)}
    with pytest.raises(RunnerFailure) as caught:
        login_shell_finds(env, ("typst",), timeout=0.5)
    assert caught.value.untested
    assert "did not finish" in caught.value.message


def test_preconditions_name_a_missing_tool_and_a_leaking_one(tmp_path, monkeypatch):
    monkeypatch.setattr(claude_runner, "login_shell_finds", lambda _env, _tools: ["typst"])
    empty = tmp_path / "empty"
    empty.mkdir()
    problems = precondition_problems(SCENARIOS["import_figures"], {"PATH": str(empty)})
    assert problems == ["no pdfimages or mutool on the run's search path"]
    problems = precondition_problems(SCENARIOS["publish_figures_latex"], {"PATH": str(empty)})
    assert "no pandoc on the run's search path" in problems
    assert any("still finds typst" in p for p in problems)


# ---------- the run: preconditions before any model call ---------------------------


def fake_claude(monkeypatch, produce=None) -> list[dict]:
    """Replace `run_claude`; record its arguments, `path` included."""
    runs: list[dict] = []

    def run_claude(ws, request, _model, _timeout, **kwargs):
        runs.append({"request": request, "path": kwargs.get("path"), "ws": ws})
        if produce:
            produce(ws)
        return recorded_events()

    monkeypatch.setattr(claude_runner, "run_claude", run_claude)
    return runs


def logged(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


@linux_only
def test_a_hidden_tool_run_gets_the_hidden_path(monkeypatch, tmp_path):
    monkeypatch.setattr(claude_runner, "precondition_problems", lambda *_a: [])
    runs = fake_claude(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main(["publish_figures_latex", "--summary-log", str(log)]) == EXIT_FAIL
    [run] = runs
    assert run["path"] is not None
    assert shutil.which("typst", path=run["path"]) is None
    assert not Path(run["path"]).is_relative_to(run["ws"]), "the PATH lies outside the workspace"
    [line] = logged(log)
    assert "built via" in line["why"]


@linux_only
def test_a_leaking_hidden_tool_leaves_the_run_untested_and_unstarted(monkeypatch, tmp_path):
    monkeypatch.setattr(claude_runner, "login_shell_finds", lambda _env, _tools: ["typst"])
    runs = fake_claude(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main(["publish_figures_docx", "--summary-log", str(log)]) == EXIT_UNTESTED
    assert runs == []
    [line] = logged(log)
    assert "still finds typst" in line["why"]


def test_hiding_off_linux_is_a_runner_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(claude_runner.sys, "platform", "darwin")
    runs = fake_claude(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main(["publish_figures_latex", "--summary-log", str(log)]) == EXIT_RUNNER
    assert runs == []
    assert "Linux only" in logged(log)[0]["why"]


def test_an_import_without_an_extraction_tool_is_untested(monkeypatch, tmp_path):
    """Scenario: Import without an extraction tool."""
    monkeypatch.setattr(claude_runner.shutil, "which", lambda *_a, **_k: None)
    runs = fake_claude(monkeypatch)
    log = tmp_path / "log.jsonl"
    assert main(["import_figures", "--summary-log", str(log)]) == EXIT_UNTESTED
    assert runs == []
    assert "pdfimages or mutool" in logged(log)[0]["why"]


@linux_only
def test_preflight_only_on_claude_runs_the_preconditions_alone(monkeypatch, capsys):
    monkeypatch.setattr(claude_runner, "precondition_problems",
                        lambda *_a: ["a login shell under the run's environment still finds "
                                     "typst, which the scenario hides"])
    runs = fake_claude(monkeypatch)
    assert main(["publish_figures_latex", "--preflight-only"]) == EXIT_UNTESTED
    assert runs == []
    out = capsys.readouterr().out
    assert "still finds typst" in out
    assert "preflight: not ready" in out
    monkeypatch.setattr(claude_runner, "precondition_problems", lambda *_a: [])
    assert main(["publish_figures_latex", "--preflight-only"]) == EXIT_PASS
    assert "preflight: ready" in capsys.readouterr().out


def test_preflight_only_needs_a_scenario_with_preconditions_on_claude(capsys):
    with pytest.raises(SystemExit) as caught:
        main(["check_report", "--preflight-only"])
    assert caught.value.code == 2
    assert "--preflight-only" in capsys.readouterr().err


def test_hiding_is_refused_on_another_host(capsys):
    with pytest.raises(SystemExit) as caught:
        main(["publish_figures_latex", "--host", "codex", "--model", "gpt-fixture-a"])
    assert caught.value.code == 2
    assert "Claude host only" in capsys.readouterr().err


@pytest.mark.parametrize("host", [["codex"], ["copilot", "--max-ai-credits", "30"]],
                         ids=["codex", "copilot"])
def test_a_tier_scenario_is_refused_on_another_host(capsys, host):
    """The tier evidence is read from Claude's stream-json tool results; on
    Codex or Copilot the tool output sits elsewhere, so a correct build would
    read as a failure. The typst tier hides nothing and must be refused too."""
    with pytest.raises(SystemExit) as caught:
        main(["publish_figures_typst", "--host", *host, "--model", "gpt-fixture-a"])
    assert caught.value.code == 2
    err = capsys.readouterr().err
    assert "publish_figures_typst" in err
    assert "Claude host only" in err


# ---------- the verdicts over a written after-state --------------------------------

PROVISIONAL, FINAL = "flaky-test-quarantine", "quarantine-decisions-flaky-tests"
SEED = ("# Quarantine Decisions for Flaky Tests\n\n*Master's Thesis Proposal*\n\n"
        "A sketch.\n\n## References\n\n---\nreferences: []\n---\n")


def test_calls_are_numbered_by_the_turn_they_ran_in():
    events = [tool_use("Write", file_path="idea/notes.md"), turn_end(),
              tool_use("Bash", command="mv idea x"), turn_end(), turn_end()]
    assert calls_by_turn(events) == [(0, "Write", {"file_path": "idea/notes.md"}),
                                     (1, "Bash", {"command": "mv idea x"})]


def test_ideation_from_scratch_is_judged_on_its_moves_and_its_end_state(tmp_path):
    scenario = SCENARIOS["ideate_from_scratch"]
    (tmp_path / FINAL).mkdir()
    (tmp_path / FINAL / f"{FINAL}.md").write_text(SEED, encoding="utf-8")
    (tmp_path / FINAL / "notes.md").write_text(NOTES_TEXT, encoding="utf-8")
    moves = [tool_use("Write", file_path=str(tmp_path / "idea" / "notes.md")), turn_end(),
             tool_use("Bash", command=f"mv idea {PROVISIONAL}"), turn_end(),
             tool_use("Bash", command=f"mv {PROVISIONAL} {FINAL}"),
             tool_use("Write", file_path=str(tmp_path / FINAL / f"{FINAL}.md")), turn_end()]
    passed, why = verdict("ideate_from_scratch", scenario, tmp_path, "", "", moves)
    assert passed, why
    straight = [moves[0], moves[1], moves[3], tool_use("Bash", command=f"mv idea {FINAL}"),
                *moves[5:]]
    passed, why = verdict("ideate_from_scratch", scenario, tmp_path, "", "", straight)
    assert not passed
    assert "provisional" in why


def write_import(ws: Path, links: str) -> None:
    folder = ws / F16
    (folder / "img").mkdir(parents=True)
    (folder / "img" / "overview.png").write_bytes(b"\x89PNG")
    (folder / f"{F16}.md").write_text(
        f"# T\n\n*Master's Thesis Proposal*\n\n{links}\n\n---\nreferences: []\n---\n",
        encoding="utf-8")
    (folder / "notes.md").write_text(NOTES_TEXT, encoding="utf-8")


def test_import_figures_is_judged_on_the_folder_it_made(tmp_path):
    scenario = SCENARIOS["import_figures"]
    stage(scenario, tmp_path, install_skill=False)
    write_import(tmp_path, "![Overview](img/overview.png)\n\n"
                           "[TODO: re-add figure from page 4 as img/queue.png]")
    passed, why = verdict("import_figures", scenario, tmp_path, "")
    assert passed, why
    (tmp_path / F16 / "img" / "overview.png").unlink()
    passed, why = verdict("import_figures", scenario, tmp_path, "")
    assert not passed
    assert "does not resolve" in why


TWO_IMAGES = b"%PDF-1.7\n<< /Subtype /Image >>\n<< /Subtype /Image >>\n"


def build_typst(ws: Path) -> None:
    (ws / F16 / f"{F16}.pdf").write_bytes(TWO_IMAGES)
    (ws / F16 / f"{F16}.typ").write_text("#set page()\n", encoding="utf-8")


def test_publish_on_the_typst_tier_is_judged_on_its_evidence(tmp_path):
    scenario = SCENARIOS["publish_figures_typst"]
    stage(scenario, tmp_path, install_skill=False)
    build_typst(tmp_path)
    events = [tool_result(f"built via typst: {F16}.pdf, {F16}.typ"), turn_end()]
    passed, why = verdict("publish_figures_typst", scenario, tmp_path, "", "", events)
    assert passed, why
    assert "2 of 2 figures" in why


def test_a_build_on_the_wrong_tier_is_untested_not_failed(tmp_path):
    """A hidden tool reached another way is a measurement that did not hold."""
    scenario = SCENARIOS["publish_figures_latex"]
    stage(scenario, tmp_path, install_skill=False)
    build_typst(tmp_path)
    events = [tool_result(f"built via typst: {F16}.pdf, {F16}.typ"), turn_end()]
    with pytest.raises(RunnerFailure) as caught:
        verdict("publish_figures_latex", scenario, tmp_path, "", "", events)
    assert caught.value.untested
    assert "typst" in caught.value.message


def test_the_keep_scenario_passes_only_on_a_kept_list_in_the_folder(tmp_path):
    scenario = SCENARIOS["litsearch_keep"]
    stage(scenario, tmp_path, install_skill=False)
    passed, why = verdict("litsearch_keep", scenario, tmp_path, "")
    assert not passed
    assert "no kept file" in why
    (tmp_path / W03 / "candidates.yaml").write_text("- id: X\n", encoding="utf-8")
    passed, why = verdict("litsearch_keep", scenario, tmp_path, "")
    assert passed, why
    out, _ = claude_runner.completed_run(
        claude_runner.build_parser().parse_args(["litsearch_keep"]), None, scenario, tmp_path,
        scenario["request"], recorded_events(), None)
    assert "family" not in out  # part of the verdict, not an advisory


# ---------- the review lookup ------------------------------------------------------

MTD = "microservice-technical-debt"
REVIEW = "Verdict: needs revision.\n\n1. The research questions overlap.\n"


@pytest.mark.parametrize("elsewhere", ["review.md", f"{MTD}-review.md", f"other/{MTD}/review.md"])
def test_the_review_is_read_from_the_proposals_folder_only(elsewhere, tmp_path):
    """The review verdicts, and the judge's artifact, read `<slug>/review.md`."""
    scenario = SCENARIOS["review_fixture"]
    stage(scenario, tmp_path, install_skill=False)
    (tmp_path / elsewhere).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / elsewhere).write_text(REVIEW, encoding="utf-8")
    passed, why = verdict("review_fixture", scenario, tmp_path, "")
    assert not passed
    assert f"{MTD}/review.md not written" in why
    assert claude_runner.l2_artifact("review_fixture", scenario, tmp_path) is None
    (tmp_path / MTD / "review.md").write_text(REVIEW, encoding="utf-8")
    passed, why = verdict("review_fixture", scenario, tmp_path, "")
    assert passed, why
    assert claude_runner.l2_artifact("review_fixture", scenario, tmp_path) == REVIEW


# ---------- supervise: the submission as a source ----------------------------------

F28 = "ci-repair-agent-configurations"


def test_feedback_counts_only_in_a_proposal_folder(tmp_path):
    """Scenario: Feedback found in the proposal's folder — and nowhere else."""
    (tmp_path / "stray").mkdir()
    (tmp_path / "stray" / "feedback.md").write_text("Verdict: ready.\n", encoding="utf-8")
    (tmp_path / "feedback.md").write_text("Verdict: ready.\n", encoding="utf-8")
    assert feedback_files(tmp_path) == {}
    (tmp_path / F28).mkdir()
    (tmp_path / F28 / f"{F28}.md").write_text(SEED, encoding="utf-8")
    (tmp_path / F28 / "feedback.md").write_text("Verdict: ready.\n", encoding="utf-8")
    assert sorted(feedback_files(tmp_path)) == [f"{F28}/feedback.md"]


def test_the_supervise_intake_leaves_the_saved_submission_alone(tmp_path):
    """Scenario: Submission saved outside any folder."""
    scenario = SCENARIOS["supervise_ready"]
    stage(scenario, tmp_path, install_skill=False)
    assert files(tmp_path) == [f"{F28}.md"]
    passed, why = verdict("supervise_ready", scenario, tmp_path, "")
    assert not passed  # nothing was written: no feedback, no review, no verifier
    assert "changed or moved" not in why
    (tmp_path / f"{F28}.md").write_text("edited\n", encoding="utf-8")
    passed, why = verdict("supervise_ready", scenario, tmp_path, "")
    assert not passed
    assert f"`{F28}.md`" in why
    assert "changed or moved" in why
