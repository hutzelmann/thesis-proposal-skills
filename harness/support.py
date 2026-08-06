"""Pure decision logic for the model-support matrix.

Everything here takes plain values and returns plain values — no file IO, no
model calls — so every rule is exercisable by L0 tests (mirrors l1_checks.py).
The thin shells matrix.py and report.py do the IO and the Inspect calls.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field

START_MARKER = "<!-- model-support:start -->"
END_MARKER = "<!-- model-support:end -->"

DEFAULT_EPOCHS = 3
_PASS_VALUES = ("C", 1, 1.0)

TIERS = ("cheap", "mid", "frontier")


@dataclass(frozen=True)
class Model:
    id: str
    family: str
    tier: str
    input_price: float
    output_price: float
    enabled: bool
    cache_read_price: float = 0.0  # $/Mtok; parse defaults it to input_price


@dataclass(frozen=True)
class TaskConfig:
    matrix: tuple[str, ...]
    core: tuple[str, ...]
    heavy: tuple[str, ...]
    extended: tuple[str, ...]
    excluded_l1: tuple[str, ...]
    excluded: tuple[str, ...]
    priors: dict[str, tuple[int, int]]
    judge_model: str
    judge_tokens: tuple[int, int]
    skills: dict[str, str] = field(default_factory=dict)
    tier_epochs: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Registry:
    models: tuple[Model, ...]
    tasks: TaskConfig


@dataclass(frozen=True)
class Verdict:
    status: str  # supported | flaky | failing | untested
    flaky_tasks: tuple[str, ...] = ()
    failing_tasks: tuple[str, ...] = ()
    untested_tasks: tuple[str, ...] = ()


@dataclass(frozen=True)
class CostLine:
    model_id: str
    usd: float


@dataclass(frozen=True)
class CostReport:
    lines: tuple[CostLine, ...] = ()
    unknown_models: tuple[str, ...] = ()

    @property
    def total(self) -> float:
        return sum(line.usd for line in self.lines)


def parse_registry(text: str) -> Registry:
    data = tomllib.loads(text)
    models = tuple(
        Model(
            id=m["id"],
            family=m["family"],
            tier=m["tier"],
            input_price=float(m["input_price"]),
            output_price=float(m["output_price"]),
            enabled=bool(m["enabled"]),
            cache_read_price=float(m.get("cache_read_price", m["input_price"])),
        )
        for m in data["models"]
    )
    for m in models:
        if m.tier not in TIERS:
            raise ValueError(f"unknown tier {m.tier!r} on {m.id}")
    t = data["tasks"]
    priors = {name: (int(p["input"]), int(p["output"])) for name, p in t["priors"].items()}
    if "default" not in priors:
        raise ValueError("tasks.priors must carry a 'default' entry")
    overlap = set(t["matrix"]) & set(t["excluded"])
    if overlap:
        raise ValueError(f"tasks both in matrix and excluded: {sorted(overlap)}")
    judge = t["judge"]
    tasks = TaskConfig(
        matrix=tuple(t["matrix"]),
        core=tuple(t["core"]),
        heavy=tuple(t["heavy"]),
        extended=tuple(t.get("extended", ())),
        excluded_l1=tuple(t["excluded_l1"]),
        excluded=tuple(t["excluded"]),
        priors=priors,
        judge_model=judge["model"],
        judge_tokens=(int(judge["input"]), int(judge["output"])),
        skills=dict(t.get("skills", {})),
        tier_epochs={tier: int(n) for tier, n in t.get("epochs", {}).items()},
    )
    for tier in tasks.tier_epochs:
        if tier not in TIERS:
            raise ValueError(f"unknown tier {tier!r} in tasks.epochs")
    unmapped = [task for task in tasks.matrix if task not in tasks.skills]
    if unmapped:
        raise ValueError(f"matrix tasks without a skills mapping: {unmapped}")
    return Registry(models=models, tasks=tasks)


def select_models(
    registry: Registry, tier: str | None = None, ids: list[str] | None = None
) -> list[Model]:
    """Enabled models, optionally narrowed by tier or by ID suffix match."""
    chosen = [m for m in registry.models if m.enabled]
    if tier is not None:
        if tier not in TIERS:
            raise ValueError(f"unknown tier {tier!r}")
        chosen = [m for m in chosen if m.tier == tier]
    if ids:
        matched = []
        for wanted in ids:
            hits = [m for m in chosen if m.id == wanted or m.id.endswith("/" + wanted)]
            if not hits:
                raise ValueError(f"no enabled registry model matches {wanted!r}")
            matched.extend(h for h in hits if h not in matched)
        chosen = matched
    return chosen


def select_tasks(
    registry: Registry, names: list[str] | None = None, core_only: bool = False
) -> list[str]:
    pool = registry.tasks.core if core_only else registry.tasks.matrix
    if names is None:
        return list(pool)
    allowed = set(registry.tasks.matrix) | set(registry.tasks.extended)
    for name in names:
        if name in registry.tasks.excluded:
            raise ValueError(f"task {name!r} is excluded from matrix runs")
        if name not in allowed:
            raise ValueError(f"task {name!r} is not in the scorable matrix or extended set")
    return list(names)


def epochs_for(task: str, tier: str, cfg: TaskConfig, default: int = DEFAULT_EPOCHS) -> int:
    if task in cfg.heavy and tier == "frontier":
        return 1
    return min(default, cfg.tier_epochs.get(tier, default))


def scorer_counts(scorer_name: str, task: str, cfg: TaskConfig) -> bool:
    return not (task in cfg.excluded_l1 and "l1" in scorer_name)


def epoch_pass(scores: dict[str, object], task: str, cfg: TaskConfig) -> bool | None:
    """One epoch's verdict: all counted scorers pass. None when nothing counts."""
    counted = {k: v for k, v in scores.items() if scorer_counts(k, task, cfg)}
    if not counted:
        return None
    return all(v in _PASS_VALUES for v in counted.values())


def classify_cell(passes: list[bool]) -> str:
    if not passes:
        return "untested"
    if all(passes):
        return "solid"
    if any(passes):
        return "flaky"
    return "fail"


def model_verdict(cells: dict[str, str]) -> Verdict:
    flaky = tuple(sorted(t for t, c in cells.items() if c == "flaky"))
    failing = tuple(sorted(t for t, c in cells.items() if c == "fail"))
    untested = tuple(sorted(t for t, c in cells.items() if c == "untested"))
    if failing:
        status = "failing"
    elif flaky:
        status = "flaky"
    elif len(untested) == len(cells):
        status = "untested"
    elif untested:
        status = "partial"  # spec: "supported" only when ALL scorable cells are solid
    else:
        status = "supported"
    return Verdict(status, flaky, failing, untested)


def _prior(
    task: str, cfg: TaskConfig, history: dict[str, tuple[int, int]] | None
) -> tuple[int, int]:
    if history and task in history:
        return history[task]
    return cfg.priors.get(task, cfg.priors["default"])


def estimate_cost(
    models: list[Model],
    tasks: list[str],
    registry: Registry,
    epochs_default: int = DEFAULT_EPOCHS,
    history: dict[str, tuple[int, int]] | None = None,
) -> CostReport:
    cfg = registry.tasks
    judge = next((m for m in registry.models if m.id == cfg.judge_model), None)
    j_in, j_out = cfg.judge_tokens
    judge_usd_per_epoch = (
        (j_in * judge.input_price + j_out * judge.output_price) / 1e6 if judge else 0.0
    )
    lines = []
    for m in models:
        usd = 0.0
        for task in tasks:
            n = epochs_for(task, m.tier, cfg, epochs_default)
            p_in, p_out = _prior(task, cfg, history)
            usd += n * (p_in * m.input_price + p_out * m.output_price) / 1e6
            usd += n * judge_usd_per_epoch
        lines.append(CostLine(m.id, round(usd, 2)))
    unknown = () if judge else (cfg.judge_model,)
    return CostReport(tuple(lines), unknown)


def price_usage(usage: dict[str, tuple[int, ...]], registry: Registry) -> CostReport:
    """Price actual token usage: model_id -> (input, output[, cache_read]) tokens.

    input excludes cache reads (Inspect reports them separately); cache reads
    are billed at the model's cache_read_price.
    """
    by_id = {m.id: m for m in registry.models}
    lines = []
    unknown = []
    for model_id, tokens in sorted(usage.items()):
        tin, tout = tokens[0], tokens[1]
        cread = tokens[2] if len(tokens) > 2 else 0
        m = by_id.get(model_id)
        if m is None:
            unknown.append(model_id)
            continue
        usd = (tin * m.input_price + tout * m.output_price + cread * m.cache_read_price) / 1e6
        lines.append(CostLine(model_id, round(usd, 4)))
    return CostReport(tuple(lines), tuple(unknown))


def merge_history(
    history: dict[str, tuple[int, int]], observed: dict[str, tuple[int, int]]
) -> dict[str, tuple[int, int]]:
    """Keep the conservative (max) per-task tokens across runs."""
    merged = dict(history)
    for task, (tin, tout) in observed.items():
        old_in, old_out = merged.get(task, (0, 0))
        merged[task] = (max(old_in, tin), max(old_out, tout))
    return merged


def splice_readme(text: str, replacement: str) -> str:
    if text.count(START_MARKER) != 1 or text.count(END_MARKER) != 1:
        raise ValueError("README must carry exactly one model-support marker pair")
    head, rest = text.split(START_MARKER, 1)
    _, tail = rest.split(END_MARKER, 1)
    return head + START_MARKER + "\n" + replacement.strip() + "\n" + END_MARKER + tail


@dataclass(frozen=True)
class Cell:
    classification: str
    passes: int = 0
    epochs: int = 0
    reduced: bool = field(default=False)


def _skill_names(tasks: tuple[str, ...], skills: dict[str, str]) -> str:
    return ", ".join(sorted({skills.get(t, t) for t in tasks}))


def _verdict_text(v: Verdict, skills: dict[str, str]) -> tuple[str, str]:
    if v.status == "supported":
        return "✅ supported", ""
    if v.status == "partial":
        return "🟡 partial", f"untested on {len(v.untested_tasks)} task(s); tested cells solid"
    if v.status == "flaky":
        return "⚠️ flaky", "flaky on: " + _skill_names(v.flaky_tasks, skills)
    if v.status == "failing":
        notes = "fails: " + _skill_names(v.failing_tasks, skills)
        if v.flaky_tasks:
            notes += "; flaky on: " + _skill_names(v.flaky_tasks, skills)
        return "❌ not recommended", notes
    return "❔ untested", ""


def render_summary(
    models: list[Model],
    verdicts: dict[str, Verdict],
    timestamp: str,
    skills: dict[str, str] | None = None,
) -> str:
    lines = [
        f"Model support, measured by the metered eval matrix on **{timestamp}** "
        f"(3 epochs per cell unless noted; details in docs/model-support.md):",
        "",
        "| Model (pinned version) | Verdict | Notes |",
        "|---|---|---|",
    ]
    for m in models:
        v = verdicts.get(m.id, Verdict("untested"))
        label, notes = _verdict_text(v, skills or {})
        short = m.id.removeprefix("openrouter/")
        if not m.enabled:
            notes = (notes + "; " if notes else "") + "disabled in registry"
        lines.append(f"| `{short}` | {label} | {notes} |")
    return "\n".join(lines)


_ROLLUP_ORDER = ("fail", "flaky", "solid", "untested")


def rollup_cells(classifications: list[str]) -> str:
    """One classification for a skill covered by several tasks: worst wins, but
    `untested` never masquerades as a pass — it only survives when nothing else
    was measured. A skill reading a blank cell as supported would clear a model
    nothing is known about.
    """
    present = set(classifications)
    for status in _ROLLUP_ORDER:
        if status in present:
            return status
    return "untested"


def export_support(
    models: list[Model],
    tasks: list[str],
    cells: dict[tuple[str, str], Cell],
    verdicts: dict[str, Verdict],
    timestamp: str,
    skills: dict[str, str] | None = None,
) -> dict:
    """Machine-readable support data for vendoring into a skill that cannot read
    this repository. Per model: the overall verdict, the raw per-task cells, and
    a per-skill rollup — the skill-level view is what a user-side consumer needs,
    since it reasons about `proposal-write`, not about `write_from_seed`.

    Keys drop the `openrouter/` routing prefix, as the rendered tables do: it is
    how this harness reaches a model, not part of the model's identity, and a
    user's agent never reports itself with it.
    """
    skills = skills or {}
    out_models: dict[str, dict] = {}
    for m in models:
        task_cells = {
            task: cells.get((m.id, task), Cell("untested")).classification for task in tasks
        }
        by_skill: dict[str, list[str]] = {}
        for task, classification in task_cells.items():
            by_skill.setdefault(skills.get(task, task), []).append(classification)
        out_models[m.id.removeprefix("openrouter/")] = {
            "verdict": verdicts.get(m.id, Verdict("untested")).status,
            "enabled": m.enabled,
            "tasks": dict(sorted(task_cells.items())),
            "skills": {name: rollup_cells(vals) for name, vals in sorted(by_skill.items())},
        }
    return {
        "generated": timestamp,
        "statuses": {
            "solid": "every measured epoch passed",
            "flaky": "some epochs passed, some failed",
            "fail": "every measured epoch failed",
            "untested": "never measured — not evidence of support",
        },
        "models": dict(sorted(out_models.items())),
    }


def render_grid(
    models: list[Model],
    tasks: list[str],
    cells: dict[tuple[str, str], Cell],
    costs: dict[str, float],
    timestamp: str,
) -> str:
    header = "| Model | " + " | ".join(tasks) + " | run cost |"
    sep = "|---" * (len(tasks) + 2) + "|"
    lines = [
        "# Model support grid",
        "",
        f"Generated from the newest eval logs on {timestamp}. "
        "Cells show passed/total epochs; `*` marks budget-reduced epochs; "
        "`—` marks untested cells.",
        "",
        header,
        sep,
    ]
    for m in models:
        row = [f"`{m.id.removeprefix('openrouter/')}`"]
        for task in tasks:
            cell = cells.get((m.id, task))
            if cell is None or cell.classification == "untested":
                row.append("—")
            else:
                mark = "*" if cell.reduced else ""
                row.append(f"{cell.passes}/{cell.epochs}{mark}")
        cost = costs.get(m.id)
        row.append(f"${cost:.2f}" if cost is not None else "—")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"
