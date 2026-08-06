"""Generate the model-support report from the newest eval logs.

Selects, per registry model × scorable task, the newest Inspect log in the log
directory, classifies each cell via support.py, and writes (1) the summary
table between the model-support markers in README.md and (2) the full grid to
docs/model-support.md. Idempotent: same logs in, same bytes out.

Usage: uv run poe report [--log-dir logs/evals]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import support

HARNESS = Path(__file__).resolve().parent
REPO = HARNESS.parent
REGISTRY = HARNESS / "models.toml"
README = REPO / "README.md"
GRID = REPO / "docs" / "model-support.md"


def newest_logs(log_dir: Path, registry: support.Registry) -> dict[tuple[str, str], object]:
    from inspect_ai.log import read_eval_log

    model_ids = {m.id for m in registry.models}
    chosen: dict[tuple[str, str], tuple[str, Path]] = {}
    for path in sorted(log_dir.glob("*.eval")):
        header = read_eval_log(str(path), header_only=True)
        task, model = header.eval.task, header.eval.model
        if task not in registry.tasks.matrix or model not in model_ids:
            continue
        started = getattr(header.stats, "started_at", "") or ""
        key = (model, task)
        if key not in chosen or started > chosen[key][0]:
            chosen[key] = (started, path)
    return {key: read_eval_log(str(path)) for key, (_, path) in chosen.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--log-dir", default="logs/evals")
    args = parser.parse_args()

    registry = support.parse_registry(REGISTRY.read_text(encoding="utf-8"))
    models = list(registry.models)  # spec: one row per registry model, disabled included
    tasks = list(registry.tasks.matrix)
    logs = newest_logs(Path(args.log_dir), registry)

    cells: dict[tuple[str, str], support.Cell] = {}
    usage_by_model: dict[str, dict[str, tuple[int, int, int]]] = {}
    newest_stamp = ""
    for (model_id, task), log in logs.items():
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

    verdicts = {
        m.id: support.model_verdict(
            {task: cells.get((m.id, task), support.Cell("untested")).classification for task in tasks}
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
    GRID.write_text(
        support.render_grid(models, tasks, cells, costs, timestamp), encoding="utf-8"
    )
    print(f"README summary + {GRID.relative_to(REPO)} regenerated from {len(logs)} log(s), "
          f"newest {timestamp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
