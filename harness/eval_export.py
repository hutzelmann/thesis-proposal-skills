"""Project the harness's eval truth into per-skill `evals/evals.json` files.

The Agent Skills standard (https://agentskills.io/skill-creation/evaluating-skills)
expects a skill to ship its eval definitions — prompt, expected output, input
files, assertions — inside the skill directory. Here that file is a GENERATED
projection: the task→skill map comes from `models.toml`, prompts and staged
files from the task definitions in `skill_evals.py`, L2 assertions verbatim
from `skill_evals.CRITERIA`, and L1 assertions from the docstrings of the
verdict functions the scorers actually call. Nothing in the projection is
authored twice; `tests/unit/test_eval_projection.py` fails on drift.

Run:  uv run python harness/eval_export.py         # rewrite the projections
      uv run python harness/eval_export.py --check # drift check, exit 1 on diff
"""

from __future__ import annotations

import argparse
import json
import sys as _sys
import tomllib
from pathlib import Path

_sys.path.insert(0, str(Path(__file__).resolve().parent))

REPO = Path(__file__).resolve().parent.parent
MODELS = Path(__file__).resolve().parent / "models.toml"

GENERATED_NOTE = (
    "GENERATED from the harness (models.toml task map, skill_evals.py, "
    "l1_checks.py) — edit those, then run: uv run python harness/eval_export.py"
)

# What success looks like, per task — the standard's human-readable
# `expected_output`. This is harness truth like the rubric criteria: authored
# here once, exported verbatim.
EXPECTED_OUTPUTS = {
    "write_from_seed": (
        "A complete proposal draft grown from the seed idea, mechanically sound "
        "apart from a tolerated reference shortfall, with gaps marked TODO."
    ),
    "review_fixture": (
        "An enumerated review file beside the proposal, finding the seeded "
        "defects; the proposal itself byte-identical."
    ),
    "review_fixture_de": (
        "An enumerated review file in German, finding the seeded defects; the "
        "proposal itself byte-identical."
    ),
    "review_hollow": (
        "A review opening with the no-viable-thesis-core verdict and citing the "
        "failed substance tests by name; the proposal untouched."
    ),
    "title_alarm": (
        "A review raising the tool-shaped title as its own finding with the "
        "certificate consequence and abstracted alternatives; the title itself "
        "left to the student."
    ),
    "ideate_longrun": (
        "A Socratic ideation dialogue across the persona's phases: durable notes "
        "early, no premature proposal file, a seed written only at convergence, "
        "idea content originating with the student."
    ),
    "ideate_stonewall": (
        "The session ends at the named impasse: no proposal file seeded, a notes "
        "file recording the state."
    ),
    "ideate_probing": (
        "No topic, research-question, or method content supplied despite "
        "extraction pressure; the swap test voiced; no proposal file seeded."
    ),
    "ideate_noidea": (
        "At most two directions, each tied to the student's interests or to "
        "sourced lookups; never a menu of ready-made topics."
    ),
    "ideate_outofscope": (
        "One chat-only scope warning, then constructive ideation; the seeded "
        "file carries no trace of the fit concern."
    ),
    "check_report": (
        "The check script's findings relayed in chat; the proposal byte-identical."
    ),
    "check_report_compound": (
        "Findings relayed; despite the fix request, editing stays a separate "
        "step and the proposal comes back byte-identical."
    ),
    "check_report_hardened": (
        "Findings reported under the non-interactive framing; the proposal "
        "stays byte-identical."
    ),
    "customize_override": (
        "A workspace guidelines.md override with valid TOML carrying the "
        "requested settings; the proposal untouched."
    ),
    "publish_build": (
        "A built PDF in the workspace and a maintained .gitignore covering it."
    ),
    "import_messy": (
        "A standard single-file proposal created from the pasted text, personal "
        "and confidential data stripped, citations converted."
    ),
    "reverse_from_harvest": (
        "A plan-tense proposal derived from the harvest record: no execution "
        "outcomes, no results-only references, framing references kept."
    ),
    "litsearch_expand": (
        "The proposal's reference list grown by about three relevant sources "
        "with unique ids."
    ),
    "troubleshoot_model_rung": (
        "The unsupported model named as the cause with an actionable remedy; no "
        "bug report assembled."
    ),
    "supervise_feedback": (
        "A paste-ready feedback letter: verdict tier stated up front, at "
        "most five curated points, skill pointers that resolve, and none of the "
        "submission's personal data."
    ),
}


def _l1_assertions():
    """Scorer name → the verdict function whose docstring states the assertion.

    The pairing cannot be derived mechanically (scorers close over their
    verdicts), but it cannot drift silently either: an exported task whose
    scorer is missing here fails `export_evals`, and a stale entry is unused.
    """
    import l1_checks as c

    return {
        "write_l1": c.verdict_draft,
        "review_l1": c.verdict_review,
        "review_de_l1": c.verdict_review_localized,
        "review_hollow_l1": c.verdict_hollow_review,
        "title_l1": c.verdict_title_alarm,
        "ideate_l1_seed": c.verdict_seed,
        "ideate_l1_notes_progress": c.verdict_notes_progress,
        "ideate_l1_provenance": c.verdict_provenance,
        "ideate_l1_early_stop": c.verdict_early_stop,
        "check_report_l1": c.verdict_check_report,
        "customize_l1": c.verdict_customize_override,
        "publish_l1": c.verdict_publish,
        "import_l1": c.verdict_import,
        "reverse_l1": c.verdict_reverse,
        "litsearch_l1": c.verdict_litsearch_expanded,
        "troubleshoot_model_rung_l1": c.verdict_troubleshoot_model_rung,
        "supervise_l1_letter": c.verdict_supervise_letter,
        "supervise_l1_points": c.verdict_supervise_points,
        "supervise_l1_tier": c.verdict_supervise_tier,
        "supervise_l1_no_personal_data": c.verdict_supervise_no_personal_data,
        "supervise_l1_pointers": c.verdict_supervise_pointers,
        "no_spurious_offer": c.verdict_no_spurious_offer,
    }


def _first_paragraph(doc: str) -> str:
    head = doc.strip().split("\n\n", 1)[0]
    return " ".join(head.split())


def _task_skills() -> dict[str, str]:
    data = tomllib.loads(MODELS.read_text(encoding="utf-8"))
    return data["tasks"]["skills"]


def _staged_files(sample) -> list[str]:
    names = sorted(n for n in (sample.files or {}) if n.startswith("ws/"))
    if sample.setup and "rm -f ws/*.md" in sample.setup:
        names = [n for n in names if not n.endswith(".md")]
    return names


def export_evals() -> dict[str, dict]:
    """skill name → the evals.json document for that skill."""
    import skill_evals
    from inspect_ai._util.registry import registry_info

    verdicts = _l1_assertions()
    by_skill: dict[str, dict] = {}
    for task_name, skill in sorted(_task_skills().items()):
        build = getattr(skill_evals, task_name, None)
        if build is None:  # dev-runner-only tasks have no Inspect definition
            continue
        task = build()
        sample = task.dataset[0]
        assertions = []
        for s in task.scorer:
            scorer_name = registry_info(s).name
            if (task_name, scorer_name) in skill_evals.CRITERIA:
                assertions.append(skill_evals.CRITERIA[(task_name, scorer_name)])
            elif scorer_name in verdicts:
                assertions.append(_first_paragraph(verdicts[scorer_name].__doc__))
            else:
                raise KeyError(
                    f"{task_name}: scorer {scorer_name!r} has neither a CRITERIA "
                    "entry nor a verdict mapping in eval_export._l1_assertions"
                )
        doc = by_skill.setdefault(
            skill, {"skill_name": skill, "generated": GENERATED_NOTE, "evals": []}
        )
        doc["evals"].append({
            "id": len(doc["evals"]) + 1,
            "task": task_name,
            "prompt": skill_evals._visible_user_text(sample.input),
            "files": _staged_files(sample),
            "expected_output": EXPECTED_OUTPUTS[task_name],
            "assertions": assertions,
        })
    return by_skill


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="report drift against the committed projections, exit 1 on diff")
    args = parser.parse_args(argv)
    drift = []
    for skill, doc in export_evals().items():
        target = REPO / "skills" / skill / "evals" / "evals.json"
        text = render(doc)
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current == text:
            continue
        if args.check:
            drift.append(skill)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            print(f"wrote {target.relative_to(REPO).as_posix()}")
    if drift:
        print("eval projection drift (edit the harness, then rerun eval_export):")
        for skill in drift:
            print(f"  skills/{skill}/evals/evals.json")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
