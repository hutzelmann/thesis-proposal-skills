"""Cost-gated model-support matrix runner (thin shell over inspect_ai + support.py).

Estimates spend from registry pricing before any metered call, requires explicit
confirmation (--yes to bypass), then drives Inspect over the selected models and
tasks with per-cell epochs. Afterwards prints and persists actual spend and
merges observed token usage into the estimate history.

Usage:
    uv run poe matrix                     # all enabled models, scorable set
    uv run poe matrix --tier cheap
    uv run poe matrix --models claude-haiku-4.5 --tasks write_from_seed
    uv run poe smoke                      # first enabled cheap model, core set, 1 epoch
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import support

HARNESS = Path(__file__).resolve().parent
REGISTRY = HARNESS / "models.toml"
EVALS = "harness/skill_evals.py"
DEFAULT_LOG_DIR = "logs/evals"
USAGE_HISTORY = Path("logs/evals/matrix-usage.json")
TOKEN_LIMIT = 2_000_000  # per-sample backstop against runaway agent loops


def load_history(path: Path) -> dict[str, tuple[int, int]]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {task: (int(v["input"]), int(v["output"])) for task, v in raw.items()}


def save_history(path: Path, history: dict[str, tuple[int, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        task: {"input": tin, "output": tout} for task, (tin, tout) in sorted(history.items())
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def print_cost(title: str, report: support.CostReport) -> None:
    print(f"\n{title}")
    for line in report.lines:
        print(f"  {line.model_id:56s} ${line.usd:8.2f}")
    print(f"  {'TOTAL':56s} ${report.total:8.2f}")
    for unknown in report.unknown_models:
        print(f"  (unpriced, not in registry: {unknown})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tier", choices=support.TIERS)
    parser.add_argument("--models", nargs="+", help="registry IDs or ID suffixes")
    parser.add_argument("--tasks", nargs="+", help="subset of the scorable matrix set")
    parser.add_argument("--core", action="store_true", help="core (smoke) task set")
    parser.add_argument("--epochs", type=int, default=support.DEFAULT_EPOCHS)
    parser.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    parser.add_argument("--estimate-only", action="store_true", help="print estimate and exit")
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR)
    args = parser.parse_args()

    registry = support.parse_registry(REGISTRY.read_text(encoding="utf-8"))
    models = support.select_models(registry, tier=args.tier, ids=args.models)
    if not models:
        print("no enabled models match the selection", file=sys.stderr)
        return 2
    tasks = support.select_tasks(registry, names=args.tasks, core_only=args.core)
    history = load_history(USAGE_HISTORY)

    estimate = support.estimate_cost(models, tasks, registry, args.epochs, history)
    basis = "history + priors" if history else "priors"
    print(f"models: {', '.join(m.id for m in models)}")
    print(f"tasks:  {', '.join(tasks)}   epochs: {args.epochs} (heavy tasks 1 on frontier)")
    print_cost(f"Estimated cost ({basis}) — an estimate, not a cap:", estimate)
    if args.estimate_only:
        return 0
    if not args.yes:
        answer = input("\nProceed with this metered run? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("aborted before any metered call")
            return 1

    from inspect_ai import eval as inspect_eval  # deferred: import cost + telemetry

    logs = []
    for task in tasks:
        by_epochs: dict[int, list[str]] = {}
        for m in models:
            n = support.epochs_for(task, m.tier, registry.tasks, args.epochs)
            by_epochs.setdefault(n, []).append(m.id)
        for n, model_ids in sorted(by_epochs.items()):
            print(f"\n=== {task} × {len(model_ids)} models × {n} epoch(s) ===")
            logs.extend(
                inspect_eval(
                    f"{EVALS}@{task}",
                    model=model_ids,
                    epochs=n,
                    log_dir=args.log_dir,
                    token_limit=TOKEN_LIMIT,
                    fail_on_error=False,
                    retry_on_error=2,
                )
            )

    usage: dict[str, tuple[int, int, int]] = {}
    observed: dict[str, tuple[int, int]] = {}
    for log in logs:
        if log.stats is None:
            continue
        for model_id, mu in log.stats.model_usage.items():
            tin, tout, cread = usage.get(model_id, (0, 0, 0))
            usage[model_id] = (
                tin + mu.input_tokens,
                tout + mu.output_tokens,
                cread + (mu.input_tokens_cache_read or 0),
            )
        # History priors are PER EPOCH; log.stats aggregates across all epochs.
        # Take the max single-sample usage of the model under test (conservative;
        # judge calls on the same model inflate this slightly when they share it).
        # Input records the full context demand (fresh input + cache reads): a
        # later run may get no cache hits, so the estimate must price it all.
        per_epoch = [
            (mu.input_tokens + (mu.input_tokens_cache_read or 0), mu.output_tokens)
            for sample in (log.samples or [])
            if (mu := (sample.model_usage or {}).get(log.eval.model)) is not None
        ]
        if not per_epoch and (under_test := log.stats.model_usage.get(log.eval.model)):
            n = max(len(log.samples or []), 1)
            demand = under_test.input_tokens + (under_test.input_tokens_cache_read or 0)
            per_epoch = [(demand // n, under_test.output_tokens // n)]
        if per_epoch:
            prev_in, prev_out = observed.get(log.eval.task, (0, 0))
            observed[log.eval.task] = (
                max(prev_in, max(p for p, _ in per_epoch)),
                max(prev_out, max(o for _, o in per_epoch)),
            )

    actual = support.price_usage(usage, registry)
    print_cost("Actual cost (recorded token usage × registry pricing):", actual)
    save_history(USAGE_HISTORY, support.merge_history(history, observed))
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    summary_path = Path(args.log_dir) / f"matrix-cost-{stamp}.json"
    summary_path.write_text(
        json.dumps(
            {
                "timestamp": stamp,
                "models": [m.id for m in models],
                "tasks": tasks,
                "per_model": {line.model_id: line.usd for line in actual.lines},
                "total": round(actual.total, 4),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"\ncost summary persisted to {summary_path}")
    errored = sum(1 for log in logs if log.status != "success")
    if errored:
        print(f"warning: {errored} eval run(s) did not finish cleanly — check inspect view")
    return 0


if __name__ == "__main__":
    sys.exit(main())
