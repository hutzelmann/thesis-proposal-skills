"""Generate the model-support report from the newest eval logs.

Selects, per registry model × scorable task, the newest Inspect log in the log
directory, classifies each cell via support.py, and writes (1) the summary
table between the model-support markers in README.md and (2) the full grid to
docs/model-support.md. Idempotent: same logs in, same bytes out.

Usage: uv run poe report [--log-dir logs/evals]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import support

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parent
REGISTRY = HARNESS / "models.toml"
README = REPO / "README.md"
GRID = REPO / "docs" / "model-support.md"
# vendored into proposal-troubleshoot by scripts/sync_shared.py; the skill runs
# in a user workspace and can reach neither this repository nor the network
SUPPORT_JSON = REPO / "shared" / "model-support.json"


def _is_baseline(header) -> bool:
    return bool((getattr(header.eval, "task_args", None) or {}).get("baseline"))


def newest_logs(
    log_dir: Path, registry: support.Registry
) -> tuple[dict[tuple[str, str], object], dict[tuple[str, str], object]]:
    """(with-skill logs, baseline logs), newest per (model, task). Baseline logs
    are identified by their recorded task_args and kept strictly apart: they
    never enter support classification (testing-harness spec), only the delta
    view. With-skill selection spans matrix ∪ extended so an on-demand extended
    pair can render a delta without joining the matrix."""
    from inspect_ai.log import read_eval_log

    model_ids = {m.id for m in registry.models}
    tasks = set(registry.tasks.matrix) | set(registry.tasks.extended)
    chosen: dict[tuple[bool, str, str], tuple[str, Path]] = {}
    for path in sorted(log_dir.glob("*.eval")):
        header = read_eval_log(str(path), header_only=True)
        task, model = header.eval.task, header.eval.model
        if task not in tasks or model not in model_ids:
            continue
        started = getattr(header.stats, "started_at", "") or ""
        key = (_is_baseline(header), model, task)
        if key not in chosen or started > chosen[key][0]:
            chosen[key] = (started, path)
    with_skill = {
        (model, task): read_eval_log(str(path))
        for (baseline, model, task), (_, path) in chosen.items() if not baseline
    }
    baseline_logs = {
        (model, task): read_eval_log(str(path))
        for (baseline, model, task), (_, path) in chosen.items() if baseline
    }
    return with_skill, baseline_logs


def arm_stats(log, task: str, registry: support.Registry) -> support.ArmStats:
    """Collapse one log into the plain values the delta view needs."""
    passes: list[bool] = []
    scorer_passes: dict[str, list[bool]] = {}
    for sample in log.samples or []:
        if sample.error is not None:
            passes.append(False)
            continue
        scores = {name: score.value for name, score in (sample.scores or {}).items()}
        verdict = support.epoch_pass(scores, task, registry.tasks)
        if verdict is not None:
            passes.append(verdict)
        for name, value in scores.items():
            scorer_passes.setdefault(name, []).append(support.score_passes(value))
    tokens = 0
    duration = None
    if log.stats is not None:
        tokens = sum(
            mu.input_tokens + mu.output_tokens for mu in log.stats.model_usage.values()
        )
        duration = support.duration_seconds(log.stats.started_at, log.stats.completed_at)
    return support.ArmStats(
        passes=tuple(passes),
        scorer_passes={k: tuple(v) for k, v in scorer_passes.items()},
        tokens=tokens,
        duration_s=duration,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log-dir", default="logs/evals")
    args = parser.parse_args(argv)

    registry = support.parse_registry(REGISTRY.read_text(encoding="utf-8"))
    models = list(registry.models)  # spec: one row per registry model, disabled included
    tasks = list(registry.tasks.matrix)
    logs, baseline_logs = newest_logs(Path(args.log_dir), registry)

    cells: dict[tuple[str, str], support.Cell] = {}
    usage_by_model: dict[str, dict[str, tuple[int, int, int]]] = {}
    durations: dict[str, float] = {}
    newest_stamp = ""
    for (model_id, task), log in logs.items():
        if task not in registry.tasks.matrix:
            continue  # extended-task logs feed only the delta view below
        passes: list[bool] = []
        for sample in log.samples or []:
            if sample.error is not None:
                passes.append(False)
                continue
            scores = {name: score.value for name, score in (sample.scores or {}).items()}
            verdict = support.epoch_pass(scores, task, registry.tasks)
            if verdict is not None:
                passes.append(verdict)
        cells[(model_id, task)] = support.Cell(
            classification=support.classify_cell(passes),
            passes=sum(passes),
            epochs=len(passes),
            reduced=0 < len(passes) < support.DEFAULT_EPOCHS,
        )
        if log.stats is not None:
            acc = usage_by_model.setdefault(model_id, {})
            for used_id, mu in log.stats.model_usage.items():
                tin, tout, cread = acc.get(used_id, (0, 0, 0))
                acc[used_id] = (
                    tin + mu.input_tokens,
                    tout + mu.output_tokens,
                    cread + (mu.input_tokens_cache_read or 0),
                )
            newest_stamp = max(newest_stamp, log.stats.started_at or "")
            span = support.duration_seconds(log.stats.started_at, log.stats.completed_at)
            if span is not None:
                durations[model_id] = durations.get(model_id, 0.0) + span

    delta_pairs = {
        key: (arm_stats(logs[key], key[1], registry), arm_stats(base_log, key[1], registry))
        for key, base_log in baseline_logs.items() if key in logs
    }

    verdicts = {
        m.id: support.model_verdict(
            {
                task: cells.get((m.id, task), support.Cell("untested")).classification
                for task in tasks
            }
        )
        for m in models
    }
    costs = {
        model_id: support.price_usage(acc, registry).total
        for model_id, acc in usage_by_model.items()
    }
    timestamp = newest_stamp[:10] if newest_stamp else "never"

    summary = support.render_summary(models, verdicts, timestamp, registry.tasks.skills)
    README.write_text(
        support.splice_readme(README.read_text(encoding="utf-8"), summary), encoding="utf-8"
    )
    GRID.parent.mkdir(parents=True, exist_ok=True)
    grid_text = support.render_grid(models, tasks, cells, costs, timestamp, durations)
    delta_text = support.render_baseline_delta(delta_pairs, registry.tasks.skills)
    if delta_text:
        grid_text += "\n" + delta_text
    GRID.write_text(grid_text, encoding="utf-8")
    SUPPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    exported = support.export_support(
        models, tasks, cells, verdicts, timestamp, registry.tasks.skills
    )
    SUPPORT_JSON.write_text(
        json.dumps(exported, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"README summary + {GRID.relative_to(REPO).as_posix()} "
          f"+ {SUPPORT_JSON.relative_to(REPO).as_posix()} "
          f"regenerated from {len(logs)} log(s), newest {timestamp}")
    print("run scripts/sync_shared.py to materialize the vendored copy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
