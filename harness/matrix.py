"""Cost-gated model-support matrix runner (thin shell over inspect_ai + support.py).

Estimates spend from registry pricing before any metered call — the models under
test plus the judge and persona the run resolves, overrides included; a role
model the registry cannot price stops the run, `--yes` or not — warns about stale
pins from one free catalog request (never blocking), requires explicit
confirmation (--yes to bypass), then drives Inspect over the selected models and
tasks with per-cell epochs. Anthropic rows go to Inspect as Model objects pinned
to the ZDR-compliant global Bedrock/Vertex endpoints with prompt caching under
the mechanism the cache reuse probe passed (support.CACHE_MECHANISM, `marker`:
support.routing_for, and the breakpoint in openrouter_cache.py); every other row
stays a bare ID. `--smoke` runs the same path. Afterwards prints and persists
actual spend, per-model cache telemetry and role usage against its budget, and
merges observed token usage into the estimate history.

Usage:
    uv run poe matrix                     # all enabled models, scorable set
    uv run poe matrix --tier cheap
    uv run poe matrix --models <registry-id-suffix> --tasks write_from_seed
    uv run poe smoke-inspect              # --smoke: [roles].smoke × core set × 1 epoch

`--smoke` only selects; the estimate and the confirmation run as for any other
selection. The everyday smoke (`uv run poe smoke`) runs on the subscription dev
runner instead and never reaches this file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import model_currency
import openrouter_cache
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tier", choices=support.TIERS)
    parser.add_argument("--models", nargs="+", help="registry IDs or ID suffixes")
    parser.add_argument("--tasks", nargs="+", help="subset of the scorable matrix set")
    parser.add_argument("--core", action="store_true", help="core (smoke) task set")
    parser.add_argument("--epochs", type=int, default=None,
                        help=f"epochs per cell (default {support.DEFAULT_EPOCHS})")
    parser.add_argument("--smoke", action="store_true",
                        help="the metered smoke: the registry's smoke model ([roles].smoke) × "
                             "the core tasks × 1 epoch; selection only, the cost gate still runs")
    parser.add_argument("--baseline", action="store_true",
                        help="run the without-skill control arm (single-turn tasks only)")
    parser.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    parser.add_argument("--estimate-only", action="store_true", help="print estimate and exit")
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR)
    return parser


def print_roles(roles: tuple[support.RoleCost, ...]) -> None:
    """The role models the estimate charged, each at its registry budget."""
    if not roles:
        return
    print("  role models (included in the lines above):")
    for r in roles:
        scope = "dialogue cell-epoch" if r.role == "persona" else "cell-epoch"
        cost = "UNPRICED" if r.usd is None else f"${r.usd:.2f}"
        print(f"    {r.role:8s} {r.model_id:48s} {r.tokens[0]:,} in / {r.tokens[1]:,} out "
              f"per {scope} × {r.cell_epochs}  {cost}")


def print_estimate(estimate: support.CostReport, models, tasks, epochs: int, history) -> None:
    """Always shown before anything metered runs, `--yes` or not."""
    basis = "history + priors" if history else "priors"
    print(f"models: {', '.join(m.id for m in models)}")
    print(f"tasks:  {', '.join(tasks)}   epochs: {epochs} (heavy tasks 1 on frontier)")
    print_cost(f"Estimated cost ({basis}) — an estimate, not a cap:", estimate)
    print_roles(estimate.roles)


def unpriced_stop(unpriced: tuple[str, ...]) -> str:
    """Why the run stops, and the one remedy: an override the registry prices."""
    ids = ", ".join(unpriced)
    return (
        f"stopped before any metered call: role model {ids} has no registry pricing, so "
        "this run's cost cannot be estimated. Set the override (JUDGE_MODEL / "
        "PERSONA_MODEL) to an ID the registry prices — a roster ID, enabled or not, or "
        "a role's own ID — or unset it. --yes does not bypass this stop."
    )


def resolve_roles(registry: support.Registry) -> dict[str, str]:
    """The judge and persona this invocation calls, resolved exactly as
    skill_evals.py resolves them (it runs in this process and reads the same
    environment)."""
    return {name: support.role_model(registry.roles, name, os.environ)
            for name in ("judge", "persona")}


def confirm_spend(assume_yes: bool) -> bool:
    """Explicit approval for a metered run. False aborts before the first call."""
    if assume_yes:
        return True
    if input("\nProceed with this metered run? [y/N] ").strip().lower() in ("y", "yes"):
        return True
    print("aborted before any metered call")
    return False


def build_model(model: support.Model, routing: support.Routing):
    """The model as Inspect receives it: a Model carrying its own routing for a
    routed (Anthropic) row, the bare registry ID for every other row. Inspect
    logs a Model as `str(model)`, which is the registry ID, so report.py counts
    the log exactly as before. A routing that asks for the conversation
    breakpoint (`marker`) installs its wrapper, which acts on pinned requests
    only."""
    if not routing:
        return model.id
    from inspect_ai.model import get_model  # deferred: import cost

    if routing.conversation_breakpoint:
        openrouter_cache.install()
    return get_model(model.id, **routing.model_args)


def run_matrix(models, tasks, registry, args) -> list:
    """Drive Inspect over the selection, grouping models that share an epoch count."""
    from inspect_ai import eval as inspect_eval  # deferred: import cost + telemetry

    logs = []
    for task in tasks:
        by_epochs: dict[int, list] = {}
        for m in models:
            n = support.epochs_for(task, m.tier, registry.tasks, args.epochs)
            routed = build_model(m, support.routing_for(m, support.CACHE_MECHANISM))
            by_epochs.setdefault(n, []).append(routed)
        for n, model_ids in sorted(by_epochs.items()):
            arm = " (baseline arm)" if args.baseline else ""
            print(f"\n=== {task} × {len(model_ids)} models × {n} epoch(s){arm} ===")
            logs.extend(
                inspect_eval(
                    f"{EVALS}@{task}",
                    model=model_ids,
                    epochs=n,
                    log_dir=args.log_dir,
                    token_limit=TOKEN_LIMIT,
                    fail_on_error=False,
                    retry_on_error=2,
                    # recorded in the log's task_args — how report.py tells the
                    # arms apart; a dialogue task never reaches here (filtered
                    # in main, and its builder takes no such parameter)
                    task_args={"baseline": True} if args.baseline else {},
                    # model_args show a routed row's pin only; `marker` lives in
                    # process state, so the log names the mechanism here
                    metadata={"cache_mechanism": support.CACHE_MECHANISM},
                )
            )
    return logs


def collect_usage(logs) -> tuple[dict[str, support.Usage], dict[str, tuple[int, int]]]:
    """(billed usage per model, per-epoch observation per task) from finished logs."""
    logs = [log for log in logs if log.stats is not None]
    usage = support.billed_usage(log.stats.model_usage for log in logs)
    observed: dict[str, tuple[int, int]] = {}
    for log in logs:
        # History priors are PER EPOCH; log.stats aggregates across all epochs.
        # Take the max single-sample usage of the model under test (conservative;
        # judge calls on the same model inflate this slightly when they share it).
        # Input records the full context demand (support.context_demand): a later
        # run may get no cache hits, so the estimate must price it all.
        per_epoch = [
            support.context_demand(mu)
            for sample in (log.samples or [])
            if (mu := (sample.model_usage or {}).get(log.eval.model)) is not None
        ]
        if not per_epoch and (under_test := log.stats.model_usage.get(log.eval.model)):
            n = max(len(log.samples or []), 1)
            demand, out = support.context_demand(under_test)
            per_epoch = [(demand // n, out // n)]
        if per_epoch:
            prev_in, prev_out = observed.get(log.eval.task, (0, 0))
            observed[log.eval.task] = (
                max(prev_in, max(p for p, _ in per_epoch)),
                max(prev_out, max(o for _, o in per_epoch)),
            )
    return usage, observed


def _model_events(log) -> list:
    return [e for sample in (log.samples or []) for e in (getattr(sample, "events", None) or [])]


def collect_cache(logs, registry: support.Registry) -> dict[str, support.CacheStats]:
    """Cache telemetry per model under test, from the logs it was under test in:
    token counts from the log's model usage, providers from its model events (a
    routed row's calls only — see support.routed_events). A routed row whose log
    recorded no usage — every call failed, as at a routing 404 — still gets
    zeroed stats, so its `no_prompt` warning names it."""
    rows = {m.id: m for m in registry.models}
    stats: dict[str, support.CacheStats] = {}
    for log in logs:
        model_id = log.eval.model
        mu = log.stats.model_usage.get(model_id) if log.stats is not None else None
        routed = bool(support.routing_for(rows.get(model_id), support.CACHE_MECHANISM))
        if mu is None and not routed:
            continue
        tokens = (0, 0, 0) if mu is None else (
            mu.input_tokens, mu.input_tokens_cache_write or 0, mu.input_tokens_cache_read or 0)
        events = support.routed_events(_model_events(log), model_id, routed)
        found = support.CacheStats(model_id, *tokens, support.serving_providers(events))
        stats[model_id] = stats[model_id].merged(found) if model_id in stats else found
    return stats


def collect_role_observations(logs, roles: dict[str, str],
                              registry: support.Registry) -> list[support.RoleObservation]:
    """Each role model's heaviest cell-epoch across the run, per role line."""
    cfg = registry.tasks
    budgets = {"judge": cfg.judge_tokens, "persona": cfg.persona_tokens}
    merged: dict[tuple[str, str], support.RoleObservation] = {}
    for log in logs:
        called = {"judge": roles["judge"]}
        if log.eval.task in cfg.dialogue:
            called["persona"] = roles["persona"]
        for o in support.role_observations(log.samples or [], called, log.eval.model, budgets):
            prev = merged.get((o.role, o.model_id))
            if prev is not None:
                o = support.RoleObservation(o.role, o.model_id, max(o.input, prev.input),
                                            max(o.output, prev.output), o.budget)
            merged[(o.role, o.model_id)] = o
    return list(merged.values())


def print_cache(stats: dict[str, support.CacheStats], registry: support.Registry,
                warnings: list[support.CacheWarning]) -> None:
    if not stats:
        return
    print("\nPrompt caching per model under test (hit rate = cache reads ÷ all prompt tokens):")
    for s in stats.values():
        print(f"  {s.model_id:56s} hit {s.hit_rate:6.1%}   write {s.cache_write:,}   "
              f"read {s.cache_read:,}   uncached {s.input:,}")
        price = support.model_price(registry, s.model_id)
        if price is not None:
            actual, uncached = support.prompt_costs(s, price)
            print(f"  {'':56s} prompt-side ${actual:.2f} (uncached-equivalent ${uncached:.2f}, "
                  f"saved ${uncached - actual:.2f})")
        print(f"  {'':56s} providers: {support.format_providers(s.providers)}")
    for warning in warnings:
        print(warning)


def print_role_observations(observations: list[support.RoleObservation]) -> None:
    if not observations:
        return
    print("\nRole models, heaviest cell-epoch observed vs registry budget:")
    for o in observations:
        flag = "   EXCEEDS BUDGET — raise it in harness/models.toml" if o.exceeded else ""
        print(f"  {o.role:14s} {o.model_id:48s} in {o.input:,} / {o.budget[0]:,}   "
              f"out {o.output:,} / {o.budget[1]:,}{flag}")


def _cache_record(s: support.CacheStats, registry: support.Registry) -> dict:
    record = {"hit_rate": round(s.hit_rate, 4), "input": s.input, "cache_write": s.cache_write,
              "cache_read": s.cache_read, "providers": s.providers}
    price = support.model_price(registry, s.model_id)
    if price is not None:
        actual, uncached = support.prompt_costs(s, price)
        record |= {"prompt_usd": round(actual, 4), "uncached_prompt_usd": round(uncached, 4)}
    return record


def cost_summary(models, tasks, actual: support.CostReport, stamp: str,
                 cache: dict[str, support.CacheStats] | None = None,
                 roles: dict[str, str] | None = None,
                 registry: support.Registry | None = None,
                 warnings: list[support.CacheWarning] | None = None,
                 mechanism: str | None = None) -> dict:
    """The persisted run summary. Keys added later (`per_model_cache`,
    `cache_warnings`, `cache_mechanism`, `roles`) sit beside the original ones,
    which keep their shape, so earlier summaries still read."""
    summary = {
        "timestamp": stamp,
        "models": [m.id for m in models],
        "tasks": tasks,
        "per_model": {line.model_id: line.usd for line in actual.lines},
        "total": round(actual.total, 4),
    }
    if cache is not None and registry is not None:
        summary["per_model_cache"] = {mid: _cache_record(s, registry) for mid, s in cache.items()}
        summary["cache_warnings"] = [asdict(w) for w in warnings or []]
        summary["cache_mechanism"] = mechanism
    if roles is not None:
        summary["roles"] = dict(roles)
    return summary


def record_spend(logs, models, tasks, registry, history, log_dir: str,
                 roles: dict[str, str] | None = None) -> None:
    """Price what was actually consumed, report cache telemetry and role usage,
    persist it, and fold the observation back into the estimate history."""
    roles = roles or resolve_roles(registry)
    usage, observed = collect_usage(logs)
    actual = support.price_usage(usage, registry)
    print_cost("Actual cost (recorded token usage × registry pricing):", actual)
    cache = collect_cache(logs, registry)
    warnings = support.cache_warnings(cache.values(), registry, support.CACHE_MECHANISM)
    print_cache(cache, registry, warnings)
    print_role_observations(collect_role_observations(logs, roles, registry))
    save_history(USAGE_HISTORY, support.merge_history(history, observed))
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    summary_path = Path(log_dir) / f"matrix-cost-{stamp}.json"
    summary = cost_summary(models, tasks, actual, stamp, cache, roles, registry, warnings,
                           support.CACHE_MECHANISM)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\ncost summary persisted to {summary_path}")
    # under fail_on_error=False a log whose samples raised still reads `success`
    errored = sum(1 for log in logs if log.status != "success"
                  or any(getattr(s, "error", None) for s in log.samples or []))
    if errored:
        print(f"warning: {errored} eval run(s) did not finish cleanly or had errored "
              "samples — check inspect view")


# selection flags `--smoke` replaces; passing one beside it is a usage error
SMOKE_EXCLUSIVE = ("models", "tier", "tasks", "core", "epochs")


def select(parser: argparse.ArgumentParser, args: argparse.Namespace,
           registry: support.Registry) -> tuple[list[support.Model], list[str]]:
    """The models and tasks to run, and `args.epochs` resolved. `--smoke` is a
    fixed selection — the smoke role's model, the core tasks, one epoch — and
    refuses any other selection flag rather than silently overriding it."""
    if not args.smoke:
        if args.epochs is None:
            args.epochs = support.DEFAULT_EPOCHS
        return (support.select_models(registry, tier=args.tier, ids=args.models),
                support.select_tasks(registry, names=args.tasks, core_only=args.core))
    # by identity: `0 in (None, False)` holds, so `--epochs 0` would pass a membership test
    clashing = [f"--{name}" for name in SMOKE_EXCLUSIVE
                if getattr(args, name) is not None and getattr(args, name) is not False]
    if clashing:
        parser.error(f"--smoke fixes the selection ([roles].smoke × core tasks × 1 epoch); "
                     f"drop {', '.join(clashing)}")
    args.epochs = 1
    smoke = support.role_model(registry.roles, "smoke", os.environ)
    return (support.select_models(registry, ids=[smoke]),
            support.select_tasks(registry, core_only=True))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    registry = support.parse_registry(REGISTRY.read_text(encoding="utf-8"))
    models, tasks = select(parser, args, registry)
    if not models:
        print("no enabled models match the selection", file=sys.stderr)
        return 2
    if args.baseline:
        tasks = support.select_baseline_tasks(registry, tasks, explicit=bool(args.tasks))
        if not tasks:
            print("no selected task has a baseline arm", file=sys.stderr)
            return 2
    history = load_history(USAGE_HISTORY)

    roles = resolve_roles(registry)
    estimate = support.estimate_cost(models, tasks, registry, args.epochs, history,
                                     judge=roles["judge"], persona=roles["persona"])
    print_estimate(estimate, models, tasks, args.epochs, history)
    if estimate.unpriced_roles:  # before the prompt, and --yes does not skip it
        print(unpriced_stop(estimate.unpriced_roles), file=sys.stderr)
        return 2
    # directly above the confirmation prompt; informs, never blocks or re-prices
    print()
    for line in model_currency.gate_warnings(registry, models, environ=os.environ):
        print(line)
    if args.estimate_only:
        return 0
    if not confirm_spend(args.yes):
        return 1

    logs = run_matrix(models, tasks, registry, args)
    record_spend(logs, models, tasks, registry, history, args.log_dir, roles)
    return 0


if __name__ == "__main__":
    sys.exit(main())
