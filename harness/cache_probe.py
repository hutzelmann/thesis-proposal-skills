"""Cache reuse probe: does prompt caching cover the growing conversation?

A metered check for the Anthropic rows of the model-support matrix (testing-harness
spec: Cache reuse probe). It replays one fixed, synthetic multi-turn tool
conversation on each selected Anthropic registry model, built exactly as the
matrix builds it (`matrix.build_model` over `support.routing_for`), and records the
cache usage of every call. A mechanism passes on a model when cache reads make up
at least 80% of the prompt tokens on the calls after the first cache write
(`l1_checks.verdict_cache_reuse`).

The conversation never depends on the model: before each call the solver appends
a synthetic assistant tool call and a synthetic tool result, and the model's own
reply (at most MAX_TOKENS tokens) is discarded. Every second assistant turn
carries no text, as agent turns often do. All text is generated here,
deterministically; nothing comes from a real proposal.

The probe pins the Anthropic rows to the ZDR-compliant global Bedrock and Vertex
endpoints (support.PINNED_PROVIDERS) under the mechanism the matrix uses,
`marker` (support.CACHE_MECHANISM): one conversation breakpoint per request
(openrouter_cache.py). Probe 2 (2026-10-05) passed it on haiku-4.5 and
sonnet-5.5; re-run the probe after an Inspect upgrade, since the breakpoint wraps
a private Inspect function.

Before the first metered call the probe prints a worst-case estimate — every
prompt token charged at the cache-write price, plus MAX_TOKENS of output per call
— and waits for explicit confirmation, as a matrix run does. The log goes to its
own directory (logs/cache-probe), never beside the matrix logs report.py reads.

Usage:
    uv run poe cache-probe --estimate-only        # the estimate only; no model call
    uv run poe cache-probe                        # estimate, confirm, run
    uv run poe cache-probe --models <registry-id-suffix> --mechanism marker

Each model ends PASS, FAIL or UNTESTED. FAIL is a scored verdict against the
mechanism: a read share below 80%, no cache write, or a 400 rejecting the request
the mechanism shaped. UNTESTED is no verdict at all: a routing, account or API
error (a 404 from the provider pin, 401, 402, 429, 5xx), a run that did not
finish, or a partial replay. Probe 1 was one: its 404 came from OpenRouter routing.

Exit status: 0 every probed model passed, 1 a model failed or the prompt was
declined, 2 a usage error (no Anthropic row selected), 3 no model failed but one
went untested.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass

import matrix
import support
from l1_checks import verdict_cache_reuse

TURNS = 10  # metered calls per model
TURN_TOKENS = 1000  # estimated tokens appended before each call
# System prompt, user prompt and the bash/text_editor definitions, rounded up: the
# matrix's system-and-tools prefix measured 1,189 tokens (2026-10-04 logs) with a
# submit tool this probe does not send.
PREFIX_TOKENS = 1200
MAX_TOKENS = 16  # the model's replies are discarded
# Deliberately low: the replay's notes run nearer four characters a token (probe 2:
# about 750 tokens per estimated 1,000), so the estimate overstates the replay and
# the worst case stays a bound.
CHARS_PER_TOKEN = 3
MESSAGE_OVERHEAD = 8  # estimated tokens of role and tool-call framing per message
DEFAULT_TIERS = ("cheap", "mid")
DEFAULT_LOG_DIR = "logs/cache-probe"
# the mechanism the matrix uses; still `marker` while the matrix is rolled back
# (support.CACHE_MECHANISM None), so the probe can re-check it (design D2)
DEFAULT_MECHANISM = support.CACHE_MECHANISM or "marker"
# the matrix agent's system message (skill_evals.agent_solver), so the cached
# prefix is the one the matrix sends
SYSTEM_PROMPT = "You have bash and a text editor. Files live under ws/ (workspace) and skill/."
TASK_PROMPT = "Read the workspace notes one by one and say what each covers."
# Test-only: a model spec that replaces the built models (an offline mock).
MODEL_OVERRIDE: str | None = None
PASS, FAIL, UNTESTED = "PASS", "FAIL", "UNTESTED"
EXIT_UNTESTED = 3
# HTTP statuses that reject the request the mechanism shaped, a scored failure
# (design D3). Every other error leaves the mechanism untested.
MECHANISM_REJECTIONS = frozenset({400})
# how the OpenAI SDK's APIStatusError, which Inspect's OpenRouter provider raises,
# opens its message
_HTTP_STATUS = re.compile(r"\bError code: (\d{3})\b")

_VOCAB = (
    "the", "method", "section", "study", "data", "scope", "draft", "note", "source",
    "review", "chapter", "result", "claim", "table", "figure", "plan", "risk", "week",
    "goal", "question", "answer", "sample", "field", "case", "survey", "model", "test",
    "group", "value", "change", "topic", "reader", "author", "list", "point", "step",
    "and", "with", "from", "into", "under", "over", "after", "before", "while", "each",
    "first", "second", "third", "final", "open", "closed", "short", "long", "clear",
    "early", "late", "small", "large", "new", "old", "main", "side", "next",
)


@dataclass(frozen=True)
class Turn:
    """One synthetic agent step: an assistant tool call and the tool's result."""

    text: str  # assistant text before the call; empty on every second turn
    function: str  # "bash" or "text_editor"
    arguments: dict
    result: str


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / CHARS_PER_TOKEN)


def turn_tokens(turn: Turn) -> int:
    """Estimated tokens a turn adds: two messages, their framing included."""
    return (estimate_tokens(turn.text) + estimate_tokens(json.dumps(turn.arguments))
            + estimate_tokens(turn.result) + 2 * MESSAGE_OVERHEAD)


def _note(turn: int, chars: int) -> str:
    """Exactly `chars` characters of a synthetic markdown note, the same on every
    run: numbered lines of vocabulary words in a fixed arithmetic order."""
    lines: list[str] = [f"# Notes {turn + 1:02d}", ""]
    k = 0
    while sum(len(line) + 1 for line in lines) < chars:
        words = [_VOCAB[(turn * 31 + n * 17 + n * n) % len(_VOCAB)]
                 for n in range(k * 12, k * 12 + 12)]
        lines.append(f"{k + 1:3d}  - {' '.join(words)}.")
        k += 1
    return "\n".join(lines)[:chars]


def build_replay(turns: int = TURNS, tokens_per_turn: int = TURN_TOKENS) -> list[Turn]:
    """The fixed conversation: each turn reads one note, alternating bash and the
    text editor, and fills its tool result up to `tokens_per_turn` estimated
    tokens. Pure and deterministic."""
    replay = []
    for k in range(turns):
        path = f"ws/notes/{_VOCAB[(k * 7 + 3) % len(_VOCAB)]}-{k + 1:02d}.md"
        if k % 2:
            head = Turn("", "text_editor", {"command": "view", "path": path}, "")
        else:
            head = Turn(f"Reading {path} next to see what it covers.", "bash",
                        {"cmd": f"cat {path}"}, "")
        room = tokens_per_turn - turn_tokens(head)
        replay.append(Turn(head.text, head.function, head.arguments,
                           _note(k, room * CHARS_PER_TOKEN)))
    return replay


def prompt_sizes(replay: list[Turn]) -> list[int]:
    """Estimated prompt tokens of each call: the prefix plus every turn so far."""
    sizes, total = [], PREFIX_TOKENS
    for turn in replay:
        total += turn_tokens(turn)
        sizes.append(total)
    return sizes


def worst_case_usd(sizes: list[int], price: support.Price, max_tokens: int = MAX_TOKENS) -> float:
    """Every prompt token written to the cache and none read, plus a full reply
    on every call: what one replay can cost at most."""
    written = sum(sizes) * price.cache_write_price
    return (written + len(sizes) * max_tokens * price.output_price) / 1e6


def worst_case_report(models: list[support.Model], registry: support.Registry,
                      sizes: list[int]) -> support.CostReport:
    """The estimate in the matrix's report shape, rounded up to the cent."""
    lines, unknown = [], []
    for m in models:
        price = support.model_price(registry, m.id)
        if price is None:
            unknown.append(m.id)
            continue
        usd = math.ceil(worst_case_usd(sizes, price) * 100 - 1e-9) / 100
        lines.append(support.CostLine(m.id, usd))
    return support.CostReport(tuple(lines), tuple(unknown))


def select_probe_models(registry: support.Registry, ids: list[str] | None) -> list[support.Model]:
    """The Anthropic rows to probe: by default the enabled ones of the cheap and
    mid tiers; named ones must be Anthropic rows (only they are routed)."""
    if not ids:
        return [m for m in support.select_models(registry)
                if m.tier in DEFAULT_TIERS and m.family == support.PINNED_FAMILY]
    chosen = support.select_models(registry, ids=ids)
    other = [m.id for m in chosen if m.family != support.PINNED_FAMILY]
    if other:
        raise ValueError(f"not an Anthropic row, so not routed or cached: {', '.join(other)}")
    return chosen


def call_usage(events) -> list[tuple[int, int, int]]:
    """Per-call (uncached input, cache write, cache read) of the model events
    already selected (support.routed_events) that returned usage, in order. A
    call that raised leaves an event without usage: it is not a call made."""
    calls = []
    for e in events:
        u = getattr(getattr(e, "output", None), "usage", None)
        if u is not None:
            calls.append((u.input_tokens, u.input_tokens_cache_write or 0,
                          u.input_tokens_cache_read or 0))
    return calls


@dataclass(frozen=True)
class ProbeResult:
    model_id: str
    status: str  # PASS, FAIL or UNTESTED
    explanation: str
    providers: dict[str, int]
    usd: float | None
    log: str

    @property
    def passed(self) -> bool:
        return self.status == PASS


def _message(error: object) -> str:
    return str(getattr(error, "message", None) or error)


def http_status(message: str) -> int | None:
    """The HTTP status an error message reports, or None."""
    match = _HTTP_STATUS.search(message)
    return int(match.group(1)) if match else None


def incomplete(log, calls: list[tuple[int, int, int]]) -> tuple[str, str] | None:
    """(status, reason) when a probe log cannot be scored, or None. Run with
    fail_on_error=False, Inspect marks a log 'success' even when its sample
    raised, so the sample's own error and the call count are checked too: a
    partial replay is never scored, and an error is never hidden behind 'no call
    wrote the cache'. Only a rejection of the request's shape (a 400) is FAIL;
    any other error, an unfinished run and a partial replay are UNTESTED."""
    if log.status != "success":
        error = getattr(log, "error", None) or log.status
        return UNTESTED, f"the probe run did not finish: {_message(error)}"
    errors = [s.error for s in (log.samples or []) if getattr(s, "error", None) is not None]
    if errors:
        message = _message(errors[0])
        status = FAIL if http_status(message) in MECHANISM_REJECTIONS else UNTESTED
        return status, (f"the replay errored after {len(calls)} of {TURNS} answered call(s): "
                        f"{message}")
    if len(calls) != TURNS:
        return UNTESTED, f"the replay recorded {len(calls)} of {TURNS} calls"
    return None


def summarize(log, registry: support.Registry) -> ProbeResult:
    """One model's verdict, serving providers and actual cost from its probe log."""
    model_id = log.eval.model
    # the probe's one model is the only caller of its ID, so nothing is filtered out
    events = support.routed_events(
        (e for sample in (log.samples or []) for e in (sample.events or [])), model_id,
        routed=False)
    usage, _ = matrix.collect_usage([log])
    actual = support.price_usage(usage, registry)
    usd = next((line.usd for line in actual.lines if line.model_id == model_id), None)
    calls = call_usage(events)
    found = incomplete(log, calls)
    if found is None:
        passed, explanation = verdict_cache_reuse(calls)
        status = PASS if passed else FAIL
    else:
        status, explanation = found
    return ProbeResult(model_id, status, explanation, support.serving_providers(events), usd,
                       str(getattr(log, "location", "") or ""))


def exit_status(results: list[ProbeResult]) -> int:
    """0 all passed; 1 any scored failure; else EXIT_UNTESTED (no result counts)."""
    statuses = {r.status for r in results}
    if FAIL in statuses:
        return 1
    return 0 if statuses == {PASS} else EXIT_UNTESTED


def print_results(results: list[ProbeResult], mechanism: str) -> None:
    print(f"\nCache reuse probe, mechanism {mechanism}:")
    for r in results:
        cost = "unpriced" if r.usd is None else f"${r.usd:.4f}"
        print(f"  {r.status}  {r.model_id}")
        print(f"        {r.explanation}")
        if r.status == UNTESTED:
            print("        no caching verdict: nothing was scored; resolve the error, re-probe")
        print(f"        providers: {support.format_providers(r.providers)}   actual cost: {cost}")
        if r.log:
            print(f"        log: {r.log}")


def probe_task(replay: list[Turn]):
    """A one-sample Inspect task whose solver replays the conversation on the
    model under test, one metered call per turn."""
    from inspect_ai import Task
    from inspect_ai.dataset import Sample
    from inspect_ai.model import (
        ChatMessageAssistant,
        ChatMessageSystem,
        ChatMessageTool,
        ChatMessageUser,
        GenerateConfig,
        get_model,
    )
    from inspect_ai.solver import solver
    from inspect_ai.tool import ToolCall, bash, text_editor

    @solver
    def replay_solver():
        async def solve(state, _generate):  # the replay never generates into the state
            model = get_model()  # the model under test, as matrix.build_model built it
            tools = [bash(timeout=120), text_editor()]
            config = GenerateConfig(max_tokens=MAX_TOKENS)
            messages = [ChatMessageSystem(content=SYSTEM_PROMPT),
                        ChatMessageUser(content=TASK_PROMPT)]
            for k, turn in enumerate(replay, 1):
                call_id = f"probe_call_{k:02d}"
                messages.append(ChatMessageAssistant(content=turn.text, tool_calls=[
                    ToolCall(id=call_id, function=turn.function, arguments=turn.arguments)]))
                messages.append(ChatMessageTool(content=turn.result, tool_call_id=call_id,
                                                function=turn.function))
                await model.generate(messages, tools=tools, config=config)
            return state

        return solve

    return Task(dataset=[Sample(input=TASK_PROMPT)], solver=replay_solver(), name="cache_probe")


def run_probe(models: list[support.Model], replay: list[Turn], args) -> list:
    from inspect_ai import eval as inspect_eval  # deferred: import cost + telemetry

    if MODEL_OVERRIDE is not None:
        built = [MODEL_OVERRIDE]
    else:
        built = [matrix.build_model(m, support.routing_for(m, args.mechanism)) for m in models]
    return inspect_eval(
        probe_task(replay),
        model=built,
        log_dir=args.log_dir,
        log_model_api=True,  # every call's raw response: the serving provider
        fail_on_error=False,
        retry_on_error=0,  # a retry would re-pay the replay; an error is reported
        # the routing in model_args shows the pin only; `marker` lives in process
        # state, so the log names the mechanism here
        metadata={"cache_mechanism": args.mechanism},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", nargs="+",
                        help="registry IDs or ID suffixes (default: the enabled Anthropic rows "
                             f"of the {' and '.join(DEFAULT_TIERS)} tiers)")
    parser.add_argument("--mechanism", choices=support.MECHANISMS, default=DEFAULT_MECHANISM,
                        help=f"caching mechanism to measure (default {DEFAULT_MECHANISM})")
    parser.add_argument("--estimate-only", action="store_true", help="print estimate and exit")
    parser.add_argument("--yes", action="store_true", help="skip the cost confirmation")
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = support.parse_registry(matrix.REGISTRY.read_text(encoding="utf-8"))
    try:
        models = select_probe_models(registry, args.models)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    if not models:
        print("no enabled Anthropic row matches the selection", file=sys.stderr)
        return 2
    replay = build_replay()
    sizes = prompt_sizes(replay)
    print(f"models:    {', '.join(m.id for m in models)}")
    print(f"mechanism: {args.mechanism}   calls per model: {len(sizes)}   "
          f"prompt tokens per call (estimated): {sizes[0]:,} … {sizes[-1]:,}")
    print(f"providers: {' then '.join(support.PINNED_PROVIDERS)}, no fallback beyond them")
    matrix.print_cost("Worst-case cost (every prompt token written to the cache, none read):",
                      worst_case_report(models, registry, sizes))
    if args.estimate_only:
        return 0
    if not matrix.confirm_spend(args.yes):
        return 1
    results = [summarize(log, registry) for log in run_probe(models, replay, args)]
    print_results(results, args.mechanism)
    return exit_status(results)


if __name__ == "__main__":
    sys.exit(main())
