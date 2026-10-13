"""Pure decision logic for the model-support matrix.

Everything here takes plain values and returns plain values — no file IO, no
model calls — so every rule is exercisable by L0 tests (mirrors l1_checks.py).
The thin shells matrix.py and report.py do the IO and the Inspect calls.
"""

from __future__ import annotations

import tomllib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime

START_MARKER = "<!-- model-support:start -->"
END_MARKER = "<!-- model-support:end -->"

DEFAULT_EPOCHS = 3
_PASS_VALUES = ("C", 1, 1.0)

TIERS = ("cheap", "mid", "frontier")

# Floating aliases a pinned registry must never carry: a bare family name (the
# subscription CLI's alias), an OpenRouter `~`-prefixed alias, or `…-latest`.
FAMILY_ALIASES = frozenset({"haiku", "sonnet", "opus", "fable"})
# `claude --help` effort levels (Claude Code 2.1.284)
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
# roles that name a model; each may be replaced for one invocation by <ROLE>_MODEL
MODEL_ROLES = ("judge", "persona", "smoke", "dev_judge")
_ROLE_KEYS = frozenset({*MODEL_ROLES, "dev_judge_effort"})


@dataclass(frozen=True)
class Model:
    id: str
    family: str
    tier: str
    input_price: float
    output_price: float
    enabled: bool
    cache_read_price: float = 0.0  # $/Mtok; parse defaults it to input_price
    cache_write_price: float = 0.0  # $/Mtok; parse defaults it to input_price
    note: str = ""  # free-text caveat rendered into the summary Notes column
    # currency tracking (harness/model_currency.py): True derives the version
    # line from the ID, a string is an explicit line glob, False opts out
    track: str | bool = True
    price_endpoint: str = ""  # endpoint tag the price is read from, when not the vendor's


@dataclass(frozen=True)
class Price:
    """$/Mtok for one model ID, from its roster row or its role-price entry."""

    input_price: float
    output_price: float
    cache_read_price: float
    cache_write_price: float


@dataclass(frozen=True)
class RolePrice:
    """A price-only entry for a held role whose ID has left the roster."""

    input_price: float
    output_price: float
    cache_read_price: float
    cache_write_price: float
    price_endpoint: str = ""


@dataclass(frozen=True)
class Roles:
    judge: str
    persona: str
    smoke: str
    dev_judge: str
    dev_judge_effort: str


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
    judge_tokens: tuple[int, int]  # per cell-epoch, every task
    skills: dict[str, str] = field(default_factory=dict)
    tier_epochs: dict[str, int] = field(default_factory=dict)
    dialogue: tuple[str, ...] = ()  # persona-driven tasks; no baseline arm exists
    persona_tokens: tuple[int, int] = (0, 0)  # per dialogue cell-epoch


@dataclass(frozen=True)
class Registry:
    models: tuple[Model, ...]
    tasks: TaskConfig
    roles: Roles
    role_prices: dict[str, RolePrice] = field(default_factory=dict)
    prices_as_of: date | None = None
    lines_reviewed_as_of: date | None = None


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
class RoleCost:
    """One role model's share of an estimate: its budget over the cell-epochs
    it runs on. `usd` is None when the registry prices its ID nowhere."""

    role: str  # "judge" | "persona"
    model_id: str
    cell_epochs: int
    tokens: tuple[int, int]  # (input, output) budget per cell-epoch
    usd: float | None


@dataclass(frozen=True)
class CostReport:
    lines: tuple[CostLine, ...] = ()
    unknown_models: tuple[str, ...] = ()
    roles: tuple[RoleCost, ...] = ()  # estimates only; already inside `lines`

    @property
    def total(self) -> float:
        return sum(line.usd for line in self.lines)

    @property
    def unpriced_roles(self) -> tuple[str, ...]:
        """Role model IDs the run would call that no registry entry prices."""
        return tuple(dict.fromkeys(r.model_id for r in self.roles if r.usd is None))


def check_pinned(model_id: object, where: str) -> str:
    """A registry model ID must be a pinned full ID, never a floating alias."""
    if not isinstance(model_id, str) or not model_id:
        raise ValueError(f"{where}: model ID must be a non-empty string, got {model_id!r}")
    segments = model_id.split("/")
    if (
        segments[-1] in FAMILY_ALIASES
        or any(s.startswith("~") for s in segments)
        or model_id.endswith("-latest")
    ):
        raise ValueError(
            f"{where}: {model_id!r} is a floating alias — pin the full model ID "
            "(the version visible in the ID)"
        )
    return model_id


def _parse_track(raw: object, model_id: str) -> str | bool:
    if raw is False or raw is True:
        return raw
    if isinstance(raw, str) and raw.count("*") == 1:
        return raw
    raise ValueError(
        f"track on {model_id}: expected false or a line glob with exactly one '*', got {raw!r}"
    )


def _parse_model(m: dict) -> Model:
    model_id = check_pinned(m.get("id"), "[[models]] id")
    model = Model(
        id=model_id,
        family=m["family"],
        tier=m["tier"],
        input_price=float(m["input_price"]),
        output_price=float(m["output_price"]),
        enabled=bool(m["enabled"]),
        cache_read_price=float(m.get("cache_read_price", m["input_price"])),
        cache_write_price=float(m.get("cache_write_price", m["input_price"])),
        note=str(m.get("note", "")),
        track=_parse_track(m.get("track", True), model_id),
        price_endpoint=str(m.get("price_endpoint", "")),
    )
    if model.tier not in TIERS:
        raise ValueError(f"unknown tier {model.tier!r} on {model.id}")
    return model


def _budget(table: dict) -> tuple[int, int]:
    return int(table["input"]), int(table["output"])


def _persona_tokens(t: dict) -> tuple[int, int]:
    """[tasks.persona] is read explicitly — unknown [tasks] keys are ignored, and a
    budget that silently stayed unread would price every persona call at $0."""
    persona = t.get("persona")
    if persona is None:
        if t.get("dialogue"):
            raise ValueError(
                "[tasks.persona] is missing: dialogue tasks call the persona, so the estimate "
                "needs its token budget per dialogue cell-epoch"
            )
        return (0, 0)
    if "model" in persona:
        raise ValueError(
            "[tasks.persona] carries only the persona's token budget; its model ID lives in "
            "[roles].persona — remove [tasks.persona].model"
        )
    return _budget(persona)


def _parse_tasks(t: dict, judge_model: str) -> TaskConfig:
    priors = {name: _budget(p) for name, p in t["priors"].items()}
    if "default" not in priors:
        raise ValueError("tasks.priors must carry a 'default' entry")
    overlap = set(t["matrix"]) & set(t["excluded"])
    if overlap:
        raise ValueError(f"tasks both in matrix and excluded: {sorted(overlap)}")
    judge = t["judge"]
    if "model" in judge:
        raise ValueError(
            "[tasks.judge] carries only the judge's token budget; its model ID lives in "
            "[roles].judge — remove [tasks.judge].model"
        )
    tasks = TaskConfig(
        matrix=tuple(t["matrix"]),
        core=tuple(t["core"]),
        heavy=tuple(t["heavy"]),
        extended=tuple(t.get("extended", ())),
        excluded_l1=tuple(t["excluded_l1"]),
        excluded=tuple(t["excluded"]),
        priors=priors,
        judge_model=judge_model,
        judge_tokens=_budget(judge),
        skills=dict(t.get("skills", {})),
        tier_epochs={tier: int(n) for tier, n in t.get("epochs", {}).items()},
        dialogue=tuple(t.get("dialogue", ())),
        persona_tokens=_persona_tokens(t),
    )
    for tier in tasks.tier_epochs:
        if tier not in TIERS:
            raise ValueError(f"unknown tier {tier!r} in tasks.epochs")
    unmapped = [task for task in tasks.matrix if task not in tasks.skills]
    if unmapped:
        raise ValueError(f"matrix tasks without a skills mapping: {unmapped}")
    return tasks


def _parse_roles(raw: dict) -> Roles:
    unknown = sorted(set(raw) - _ROLE_KEYS)
    if unknown:
        raise ValueError(f"[roles]: unknown key(s) {unknown}")
    missing = sorted({"judge", "smoke", "dev_judge", "dev_judge_effort"} - set(raw))
    if missing:
        raise ValueError(f"[roles]: missing {missing}")
    names = {name: check_pinned(raw.get(name, raw["judge"]), f"[roles].{name}")
             for name in MODEL_ROLES}
    effort = raw["dev_judge_effort"]
    if effort not in EFFORT_LEVELS:
        raise ValueError(
            f"[roles].dev_judge_effort: {effort!r} is not one of {', '.join(EFFORT_LEVELS)}"
        )
    return Roles(**names, dev_judge_effort=effort)


def _parse_role_prices(raw: dict) -> dict[str, RolePrice]:
    return {
        check_pinned(model_id, "[role_prices]"): RolePrice(
            input_price=float(p["input_price"]),
            output_price=float(p["output_price"]),
            cache_read_price=float(p.get("cache_read_price", p["input_price"])),
            cache_write_price=float(p.get("cache_write_price", p["input_price"])),
            price_endpoint=str(p.get("price_endpoint", "")),
        )
        for model_id, p in raw.items()
    }


def _parse_date(data: dict, key: str) -> date:
    value = data.get(key)
    if not isinstance(value, date) or isinstance(value, datetime):
        raise ValueError(f"top-level {key} must be a TOML date (YYYY-MM-DD), got {value!r}")
    return value


def _check_roles(registry: Registry) -> None:
    """Cross-checks between roles, roster rows and role-price entries."""
    roles = registry.roles
    enabled = {m.id for m in registry.models if m.enabled}
    if roles.smoke not in enabled:
        raise ValueError(f"[roles].smoke: {roles.smoke!r} is not an enabled roster entry")
    roster = {m.id for m in registry.models}
    for model_id in registry.role_prices:
        if model_id in roster:
            raise ValueError(
                f"[role_prices.{model_id!r}] duplicates a roster entry — the roster row prices it"
            )
        if model_id not in (roles.judge, roles.persona):
            raise ValueError(
                f"[role_prices.{model_id!r}] is named by no role — delete the entry"
            )
    for name in ("judge", "persona"):
        model_id = getattr(roles, name)
        if model_price(registry, model_id) is None:
            raise ValueError(
                f"[roles].{name}: {model_id!r} is priced by neither a roster entry nor a "
                "[role_prices] entry — a metered role must be priced"
            )


def parse_registry(text: str) -> Registry:
    data = tomllib.loads(text)
    models = tuple(_parse_model(m) for m in data["models"])
    roles = _parse_roles(data.get("roles", {}))
    registry = Registry(
        models=models,
        tasks=_parse_tasks(data["tasks"], roles.judge),
        roles=roles,
        role_prices=_parse_role_prices(data.get("role_prices", {})),
        prices_as_of=_parse_date(data, "prices_as_of"),
        lines_reviewed_as_of=_parse_date(data, "lines_reviewed_as_of"),
    )
    _check_roles(registry)
    return registry


def model_price(registry: Registry, model_id: str) -> Price | None:
    """The one price lookup: the roster row with that ID (enabled or not), else
    the [role_prices] entry, else None."""
    for m in registry.models:
        if m.id == model_id:
            return Price(m.input_price, m.output_price, m.cache_read_price, m.cache_write_price)
    entry = registry.role_prices.get(model_id)
    if entry is not None:
        return Price(entry.input_price, entry.output_price, entry.cache_read_price,
                     entry.cache_write_price)
    return None


def is_subscription_model(model_id: str) -> bool:
    """A full model ID the subscription CLI serves: a `claude-` prefix, no
    provider segment, and a version digit. Rejects the CLI's bare aliases and
    every provider-qualified metered ID alike. A prefix rule rather than a
    roster row on purpose: a subscription ID never becomes a matrix row, and it
    is priced nowhere because no subscription ID reaches the matrix estimate."""
    return (model_id.startswith("claude-") and "/" not in model_id
            and any(ch.isdigit() for ch in model_id))


def role_model(roles: Roles, name: str, environ: Mapping[str, str]) -> str:
    """The model a role resolves to for this invocation: `<NAME>_MODEL` from the
    environment when set and non-empty, else the registry's role. An override
    replaces its own role only — a judge override never moves the persona."""
    if name not in MODEL_ROLES:
        raise ValueError(f"unknown model role {name!r}; expected one of {MODEL_ROLES}")
    return environ.get(f"{name.upper()}_MODEL") or getattr(roles, name)


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


def select_baseline_tasks(
    registry: Registry, tasks: list[str], explicit: bool = False
) -> list[str]:
    """The subset of a selection that has a baseline arm. A dialogue task named
    explicitly is an error (there is no meaningful without-skill control for a
    persona conversation); one merely present in a default selection is dropped."""
    rejected = [t for t in tasks if t in registry.tasks.dialogue]
    if rejected and explicit:
        raise ValueError(f"no baseline arm exists for dialogue task(s): {rejected}")
    return [t for t in tasks if t not in registry.tasks.dialogue]


def epochs_for(task: str, tier: str, cfg: TaskConfig, default: int = DEFAULT_EPOCHS) -> int:
    if task in cfg.heavy and tier == "frontier":
        return 1
    return min(default, cfg.tier_epochs.get(tier, default))


def scorer_counts(scorer_name: str, task: str, cfg: TaskConfig) -> bool:
    return not (task in cfg.excluded_l1 and "l1" in scorer_name)


def score_passes(value: object) -> bool:
    """One scorer value's verdict, shared by cell classification and arm stats."""
    return value in _PASS_VALUES


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


def _budget_usd(price: Price | None, tokens: tuple[int, int]) -> float:
    """A per-cell-epoch budget at full input price: the uncached ceiling."""
    if price is None:
        return 0.0
    return (tokens[0] * price.input_price + tokens[1] * price.output_price) / 1e6


def _role_cells(models: list[Model], tasks: list[str], cfg: TaskConfig,
                epochs_default: int) -> tuple[int, int]:
    """(every cell-epoch, dialogue cell-epochs) the selection runs."""
    cells = dialogue = 0
    for m in models:
        for task in tasks:
            n = epochs_for(task, m.tier, cfg, epochs_default)
            cells += n
            dialogue += n if task in cfg.dialogue else 0
    return cells, dialogue


def _role_costs(models: list[Model], tasks: list[str], registry: Registry,
                epochs_default: int, judge: str, persona: str) -> tuple[RoleCost, ...]:
    """The judge on every cell-epoch, the persona on dialogue cell-epochs only; a
    role with no cell-epoch in the selection is not called and not listed."""
    cfg = registry.tasks
    cells, dialogue = _role_cells(models, tasks, cfg, epochs_default)
    costs = []
    for role, model_id, n, tokens in (("judge", judge, cells, cfg.judge_tokens),
                                      ("persona", persona, dialogue, cfg.persona_tokens)):
        if n == 0:
            continue
        price = model_price(registry, model_id)
        usd = None if price is None else round(n * _budget_usd(price, tokens), 2)
        costs.append(RoleCost(role, model_id, n, tokens, usd))
    return tuple(costs)


def estimate_cost(
    models: list[Model],
    tasks: list[str],
    registry: Registry,
    epochs_default: int = DEFAULT_EPOCHS,
    history: dict[str, tuple[int, int]] | None = None,
    judge: str | None = None,
    persona: str | None = None,
) -> CostReport:
    """Each model's line carries its own cell-epochs plus the role budgets those
    cell-epochs call. `judge`/`persona` are the IDs the run resolves (environment
    overrides included — `role_model`); left out, the registry's roles. Every price
    comes from `model_price`; an unpriced role is charged nothing here and is
    reported in `unpriced_roles`, which the caller must treat as a stop."""
    cfg = registry.tasks
    judge = judge or registry.roles.judge
    persona = persona or registry.roles.persona
    judge_usd = _budget_usd(model_price(registry, judge), cfg.judge_tokens)
    persona_usd = _budget_usd(model_price(registry, persona), cfg.persona_tokens)
    lines = []
    for m in models:
        usd = 0.0
        for task in tasks:
            n = epochs_for(task, m.tier, cfg, epochs_default)
            p_in, p_out = _prior(task, cfg, history)
            usd += n * (p_in * m.input_price + p_out * m.output_price) / 1e6
            usd += n * judge_usd
            usd += n * persona_usd if task in cfg.dialogue else 0.0
        lines.append(CostLine(m.id, round(usd, 2)))
    roles = _role_costs(models, tasks, registry, epochs_default, judge, persona)
    return CostReport(tuple(lines), roles=roles)


Usage = tuple[int, int, int, int]  # (input, output, cache_read, cache_write), price_usage's order


def billed_usage(model_usages: Iterable[Mapping[str, object]]) -> dict[str, Usage]:
    """Sum Inspect ModelUsage maps (model ID -> usage) into price_usage's tuples.
    The one accumulation behind both cost reports — matrix.collect_usage and
    report.py — so neither can drop a token kind the other prices: Inspect
    reports cache reads and cache writes apart from input."""
    totals: dict[str, Usage] = {}
    for usage in model_usages:
        for model_id, mu in usage.items():
            tin, tout, cread, cwrite = totals.get(model_id, (0, 0, 0, 0))
            totals[model_id] = (
                tin + mu.input_tokens,
                tout + mu.output_tokens,
                cread + (mu.input_tokens_cache_read or 0),
                cwrite + (mu.input_tokens_cache_write or 0),
            )
    return totals


def price_usage(usage: dict[str, tuple[int, ...]], registry: Registry) -> CostReport:
    """Price actual token usage: model_id -> (input, output[, cache_read[,
    cache_write]]) tokens.

    input excludes cache reads and cache writes (Inspect reports both separately);
    each is billed at its own price, a cache write at the entry's
    cache_write_price (its input price unless the registry says otherwise).
    """
    lines = []
    unknown = []
    for model_id, tokens in sorted(usage.items()):
        tin, tout, cread, cwrite = (*tokens, 0, 0)[:4]
        m = model_price(registry, model_id)
        if m is None:
            unknown.append(model_id)
            continue
        usd = (tin * m.input_price + tout * m.output_price + cread * m.cache_read_price
               + cwrite * m.cache_write_price) / 1e6
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


# ---------- prompt caching on Anthropic rows: routing and telemetry ------------

# How Anthropic rows are cached (testing-harness spec: Prompt caching on Anthropic
# matrix rows): `marker`, the upstream pin plus one conversation breakpoint added
# to Inspect's own markers (harness/openrouter_cache.py).
MECHANISMS = ("marker",)
# The one mechanism the matrix routes Anthropic rows with; the spec admits only a
# mechanism the cache reuse probe has passed. Probe 2 (2026-10-05) passed `marker`
# on haiku-4.5 (88.8% reads) and sonnet-5.5 (86.4%), served by Bedrock; the
# unprobed `auto` was deleted (fix-openrouter-caching, task 8.1). None rolls
# back: every row, Anthropic included, is then sent exactly as before.
CACHE_MECHANISM: str | None = "marker"
PINNED_FAMILY = "anthropic"
# OpenRouter provider slugs of the pin, tried in this order with no fallback
# beyond them. The account's zero-data-retention guardrail removes first-party
# `anthropic` (probe 1, 2026-10-05: a routing 404); these global endpoints are
# the ones it and the regional-surcharge filter keep. A bare slug never pins a
# surcharged regional endpoint, and an explicit order turns off OpenRouter's
# sticky routing, so Bedrock serves every turn it can and Vertex only on failover.
PINNED_PROVIDERS = ("amazon-bedrock", "google-vertex")
# The name OpenRouter records in a response's `provider` field for each slug:
# the endpoints' `provider_name` (tests/unit/data/model_catalog/endpoints/).
PROVIDER_NAMES = {"amazon-bedrock": "Amazon Bedrock", "google-vertex": "Google"}
CACHE_HIT_WARN = 0.5  # below the probe's 80%: real cells carry one-shot judge calls
UNRECORDED = "unrecorded"  # model events whose raw call the log did not keep


def provider_pin() -> dict:
    """The OpenRouter `provider` routing object of a routed row, built fresh."""
    return {"order": list(PINNED_PROVIDERS), "allow_fallbacks": False}


@dataclass(frozen=True)
class Routing:
    """Per-model OpenRouter settings: model arguments for `get_model` and
    whether its conversation gets a cache breakpoint (`marker`). Empty for every
    non-Anthropic row, whose requests stay exactly as before."""

    model_args: dict = field(default_factory=dict)
    conversation_breakpoint: bool = False

    def __bool__(self) -> bool:
        return bool(self.model_args or self.conversation_breakpoint)

    @property
    def pins(self) -> tuple[str, ...]:
        """The upstream provider slugs the routing pins, in order; () if none."""
        return tuple(self.model_args.get("provider", {}).get("order") or ())

    def serves(self, provider_name: str) -> bool:
        """Whether a provider name recorded in a response is one of the pins."""
        names = {PROVIDER_NAMES.get(slug, slug).casefold() for slug in self.pins}
        return provider_name.casefold() in names | {slug.casefold() for slug in self.pins}


def routing_for(model: Model | None, mechanism: str | None) -> Routing:
    """Anthropic rows: the pinned providers only, in order, no fallback beyond
    them — so successive turns reach the cache they wrote — plus the
    conversation breakpoint (`marker`). No mechanism (None: rolled back) routes
    nothing. Built fresh on every call, so no caller can mutate another's
    routing."""
    if mechanism is not None and mechanism not in MECHANISMS:
        raise ValueError(f"unknown caching mechanism {mechanism!r}; expected one of {MECHANISMS}")
    if mechanism is None or model is None or model.family != PINNED_FAMILY:
        return Routing()
    return Routing({"provider": provider_pin()}, conversation_breakpoint=True)


@dataclass(frozen=True)
class CacheStats:
    """One model's prompt-token split in a run. `input` is uncached input (Inspect
    reports cache reads and cache writes apart from it)."""

    model_id: str
    input: int
    cache_write: int
    cache_read: int
    providers: dict[str, int] = field(default_factory=dict)

    @property
    def prompt(self) -> int:
        return self.input + self.cache_write + self.cache_read

    @property
    def hit_rate(self) -> float:
        return self.cache_read / self.prompt if self.prompt else 0.0

    def merged(self, other: CacheStats) -> CacheStats:
        providers = dict(self.providers)
        for name, n in other.providers.items():
            providers[name] = providers.get(name, 0) + n
        return CacheStats(self.model_id, self.input + other.input,
                          self.cache_write + other.cache_write,
                          self.cache_read + other.cache_read, dict(sorted(providers.items())))


def prompt_costs(stats: CacheStats, price: Price) -> tuple[float, float]:
    """(actual, uncached-equivalent) $ for the prompt side of `stats`: what was
    billed, and what the same tokens cost with no caching at all."""
    actual = (stats.input * price.input_price + stats.cache_write * price.cache_write_price
              + stats.cache_read * price.cache_read_price) / 1e6
    return actual, stats.prompt * price.input_price / 1e6


def format_providers(counts: Mapping[str, int]) -> str:
    """`Anthropic ×3, unrecorded ×9`, in the order given; `none` when empty."""
    return ", ".join(f"{name} ×{n}" for name, n in counts.items()) or "none"


CACHE_WARNING_KINDS = ("no_prompt", "low_hit", "off_pin")


@dataclass(frozen=True)
class CacheWarning:
    """One cache-telemetry finding on a routed row. `kind` is one of
    CACHE_WARNING_KINDS; `detail` is the human sentence after the model ID."""

    model_id: str
    kind: str
    detail: str

    def __str__(self) -> str:
        return f"warning: {self.model_id} {self.detail}"


def cache_warnings(stats: Iterable[CacheStats], registry: Registry,
                   mechanism: str | None) -> list[CacheWarning]:
    """Findings for rows `mechanism` routes (Anthropic roster rows) only: a
    cache-hit rate below CACHE_HIT_WARN, no prompt tokens at all, or a recorded
    call served by a provider outside the pin (every pinned provider, Vertex on
    failover included, is on it). A non-Anthropic row, an ID priced only by
    [role_prices], and every row while the mechanism is rolled back (None) have
    no pin and are never warned."""
    rows = {m.id: m for m in registry.models}
    found = []
    for s in stats:
        routing = routing_for(rows.get(s.model_id), mechanism)
        if not routing.pins:
            continue
        if not s.prompt:
            found.append(CacheWarning(
                s.model_id, "no_prompt", "recorded no prompt tokens — its cache-hit rate is "
                "unknown; if every call failed (a routing 404?), see the sample errors"))
        elif s.hit_rate < CACHE_HIT_WARN:
            found.append(CacheWarning(
                s.model_id, "low_hit", f"cache-hit rate {s.hit_rate:.1%} is below "
                f"{CACHE_HIT_WARN:.0%} — prompt caching may have regressed"))
        off = {name: n for name, n in sorted(s.providers.items())
               if name != UNRECORDED and not routing.serves(name)}
        if off:
            found.append(CacheWarning(s.model_id, "off_pin", f"had calls served off its pin "
                                      f"({', '.join(routing.pins)}): {format_providers(off)}"))
    return found


def _call_pinned(event: object) -> bool | None:
    """Whether a model event's recorded request named a provider pin; None when
    the log kept no raw call for it."""
    call = getattr(event, "call", None)
    if call is None:
        return None
    body = (getattr(call, "request", None) or {}).get("extra_body")
    return isinstance(body, dict) and "provider" in body


def routed_events(events: Iterable[object], model_id: str, routed: bool) -> list:
    """The model events of `model_id`. For a routed row, a recorded call whose
    request names no pin came from another Model of the same ID — the judge or
    the persona, whose serving this change leaves alone — and is dropped; an
    unrecorded call is kept for the `unrecorded` bucket."""
    return [
        e for e in events
        if getattr(e, "event", None) == "model" and getattr(e, "model", None) == model_id
        and not (routed and _call_pinned(e) is False)
    ]


def serving_providers(events: Iterable[object]) -> dict[str, int]:
    """Count the upstream provider OpenRouter recorded in each event's raw
    response; events with no recorded call land in `unrecorded`."""
    counts: dict[str, int] = {}
    for e in events:
        call = getattr(e, "call", None)
        response = getattr(call, "response", None) if call is not None else None
        provider = response.get("provider") if isinstance(response, dict) else None
        name = provider if isinstance(provider, str) and provider else UNRECORDED
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


@dataclass(frozen=True)
class RoleObservation:
    """A role model's heaviest cell-epoch beside its budget. Roles sharing one ID
    (the persona defaults to the judge) cannot be told apart and share a line."""

    role: str  # "judge", "persona" or "judge/persona"
    model_id: str
    input: int  # uncached input + cache writes + cache reads: full demand
    output: int
    budget: tuple[int, int]

    @property
    def exceeded(self) -> bool:
        return self.input > self.budget[0] or self.output > self.budget[1]


def context_demand(usage: object) -> tuple[int, int]:
    """(full prompt demand, output) of one ModelUsage: uncached input plus cache
    writes plus cache reads, since Inspect reports both cache counts apart from
    input and a later run may get no cache hit at all."""
    return (usage.input_tokens + (usage.input_tokens_cache_write or 0)
            + (usage.input_tokens_cache_read or 0), usage.output_tokens)


def role_observations(
    samples: Iterable[object],
    role_ids: Mapping[str, str],
    under_test: str,
    budgets: Mapping[str, tuple[int, int]],
) -> list[RoleObservation]:
    """Per-cell-epoch usage (the maximum over `samples`) of each role model the
    task calls, from per-sample model usage. A role whose ID is the model under
    test is mixed into that model's own usage and yields no observation."""
    by_id: dict[str, list[str]] = {}
    for role, model_id in role_ids.items():
        if model_id != under_test:
            by_id.setdefault(model_id, []).append(role)
    samples = list(samples)
    found = []
    for model_id, roles in by_id.items():
        seen = [context_demand(u) for s in samples
                if (u := (getattr(s, "model_usage", None) or {}).get(model_id)) is not None]
        if not seen:
            continue
        budget = (sum(budgets[r][0] for r in roles), sum(budgets[r][1] for r in roles))
        found.append(RoleObservation("/".join(roles), model_id, max(i for i, _ in seen),
                                     max(o for _, o in seen), budget))
    return found


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
    """The README table: current models only. A disabled registry row keeps its
    verdict in the grid document and the exported data, which
    proposal-troubleshoot reads, but most readers want the models they can pick
    today, so it has no README row."""
    lines = [
        f"Model support, measured by the metered eval matrix on **{timestamp}** "
        f"(3 epochs per cell unless noted; details in docs/model-support.md):",
        "",
        "| Model (pinned version) | Verdict | Notes |",
        "|---|---|---|",
    ]
    for m in (m for m in models if m.enabled):
        v = verdicts.get(m.id, Verdict("untested"))
        label, notes = _verdict_text(v, skills or {})
        short = m.id.removeprefix("openrouter/")
        if m.note:
            notes = (notes + "; " if notes else "") + m.note
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


def duration_seconds(started_at: str | None, completed_at: str | None) -> float | None:
    """Wall-clock span between two ISO timestamps from a log's stats, if both exist."""
    if not started_at or not completed_at:
        return None
    try:
        span = datetime.fromisoformat(completed_at) - datetime.fromisoformat(started_at)
    except ValueError:
        return None
    return span.total_seconds()


@dataclass(frozen=True)
class ArmStats:
    """One arm (with-skill or baseline) of a task on one model, from its newest log."""

    passes: tuple[bool, ...]  # task-level verdict per epoch
    scorer_passes: dict[str, tuple[bool, ...]]  # raw per-scorer results, unfiltered
    tokens: int  # full prompt demand + output across the run, judge included (context_demand)
    duration_s: float | None = None

    @property
    def pass_rate(self) -> float:
        return sum(self.passes) / len(self.passes) if self.passes else 0.0


def _scorer_flags(with_arm: ArmStats, base_arm: ArmStats) -> list[str]:
    """The standard's pattern analysis: a scorer passing in both arms measures
    nothing the skill adds (dead-assertion candidate); one failing in both arms
    measures something no arm can do (too-hard candidate)."""
    flags = []
    for name in sorted(set(with_arm.scorer_passes) & set(base_arm.scorer_passes)):
        w, b = with_arm.scorer_passes[name], base_arm.scorer_passes[name]
        if w and b and all(w) and all(b):
            flags.append(f"`{name}` passes in both arms — dead-assertion candidate")
        elif w and b and not any(w) and not any(b):
            flags.append(f"`{name}` fails in both arms — too-hard candidate")
    return flags


def render_baseline_delta(
    pairs: dict[tuple[str, str], tuple[ArmStats, ArmStats]],
    skills: dict[str, str] | None = None,
) -> str:
    """Markdown section for (model, task) cells measured in both arms:
    what the skill buys (pass rate) against what it costs (tokens, time).
    Empty string when no pair exists — the baseline arm is on-demand."""
    if not pairs:
        return ""
    skills = skills or {}
    lines = [
        "## Baseline delta",
        "",
        "With-skill vs without-skill, from the newest log of each arm "
        "(baseline runs are on-demand — missing rows were simply not run):",
        "",
        "| Model | Task | Pass rate (with / without / Δ) | Tokens (with / without / Δ) "
        "| Runtime s (with / without) |",
        "|---|---|---|---|---|",
    ]
    flags_by_cell = []
    for (model_id, task), (with_arm, base_arm) in sorted(pairs.items()):
        short = model_id.removeprefix("openrouter/")
        delta = with_arm.pass_rate - base_arm.pass_rate
        tok_delta = with_arm.tokens - base_arm.tokens
        dur = tuple(
            f"{a.duration_s:.0f}" if a.duration_s is not None else "—"
            for a in (with_arm, base_arm)
        )
        lines.append(
            f"| `{short}` | {task} "
            f"| {with_arm.pass_rate:.2f} / {base_arm.pass_rate:.2f} / {delta:+.2f} "
            f"| {with_arm.tokens} / {base_arm.tokens} / {tok_delta:+d} "
            f"| {dur[0]} / {dur[1]} |"
        )
        cell_flags = _scorer_flags(with_arm, base_arm)
        if cell_flags:
            name = skills.get(task, task)
            flags_by_cell.append((short, name, cell_flags))
    for short, name, cell_flags in flags_by_cell:
        lines.append("")
        lines.append(f"Assertion flags for `{short}` on {name}:")
        lines.extend(f"- {flag}" for flag in cell_flags)
    return "\n".join(lines) + "\n"


def render_grid(
    models: list[Model],
    tasks: list[str],
    cells: dict[tuple[str, str], Cell],
    costs: dict[str, float],
    timestamp: str,
    durations: dict[str, float] | None = None,
) -> str:
    """`durations` (seconds per model, summed over its newest logs) adds a
    runtime column beside run cost — the timing half of the standard's
    benchmark shape. Omitted, the grid keeps its historical columns."""
    timing = durations is not None
    header = "| Model | " + " | ".join(tasks) + " | run cost |"
    if timing:
        header += " runtime |"
    sep = "|---" * (len(tasks) + 2 + int(timing)) + "|"
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
        row = [f"`{m.id.removeprefix('openrouter/')}`" + ("" if m.enabled else " (disabled)")]
        for task in tasks:
            cell = cells.get((m.id, task))
            if cell is None or cell.classification == "untested":
                row.append("—")
            else:
                mark = "*" if cell.reduced else ""
                row.append(f"{cell.passes}/{cell.epochs}{mark}")
        cost = costs.get(m.id)
        row.append(f"${cost:.2f}" if cost is not None else "—")
        if timing:
            secs = (durations or {}).get(m.id)
            row.append(f"{secs:.0f}s" if secs is not None else "—")
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"
