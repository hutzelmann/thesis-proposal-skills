"""Mechanism `marker`: one prompt-cache breakpoint on the growing conversation.

Inspect 0.3.250's OpenRouter provider marks the last system block and the last
tool definition of every `anthropic/*` request, and adds a rolling message
breakpoint only where message content is already a list (`_add_anthropic_cache_
markers` in inspect_ai/model/_providers/openrouter.py). It sends tool results and
assistant turns as strings, so in an agent loop the conversation itself is never
cached. This module wraps that function so that a request the harness routed
(testing-harness spec: Prompt caching on Anthropic matrix rows) also carries one
breakpoint on its newest user or tool message (fix-openrouter-caching, design D3).

The wrapper scopes itself. It changes only a request that carries the harness's
provider pin (`support.provider_pin`, which only `support.routing_for` produces).
The judge and the persona (built from their bare role IDs), every other family,
and every matrix request sent while the mechanism is rolled back
(`support.CACHE_MECHANISM` None) carry no pin and pass through byte-identical, so
a one-shot judge or persona prompt is never marked. A pinned request is the
model under test's, and even a single message heads a conversation whose later
turns read it back (a dialogue task's first turn), so it is marked.

`matrix.build_model` installs the wrapper when it builds a model whose routing
asks for the breakpoint: every routed Anthropic row of a matrix run and of a
cache reuse probe run. Probe 2 (2026-10-05) passed it on haiku-4.5 and
sonnet-5.5, served by Bedrock.
"""

from __future__ import annotations

import functools
import importlib

import support

INSPECT_MODULE = "inspect_ai.model._providers.openrouter"
INSPECT_FUNCTION = "_add_anthropic_cache_markers"
MAX_BREAKPOINTS = 4  # Anthropic's limit per request; Inspect's own markers use at most 3
MARKABLE_ROLES = ("user", "tool")  # assistant content stays the string Inspect flattens it to
_INSTALLED = "harness_conversation_breakpoint"  # attribute set on the wrapper


def pinned(request: dict) -> bool:
    """Whether the harness routed this request: its `extra_body` carries the
    harness pin."""
    extra = request.get("extra_body")
    return isinstance(extra, dict) and extra.get("provider") == support.provider_pin()


def count_breakpoints(request: dict) -> int:
    """cache_control markers already on message content blocks and tool definitions."""
    blocks = [block for message in request.get("messages") or []
              if isinstance(message.get("content"), list) for block in message["content"]]
    tools = request.get("tools")  # the SDK's NOT_GIVEN sentinel when there are none
    blocks += tools if isinstance(tools, list) else []
    return sum(1 for block in blocks if isinstance(block, dict) and "cache_control" in block)


def _target(messages: list) -> int | None:
    """Index of the newest user or tool message with content, or None. The walk
    passes assistant turns (a textless tool call included) and the system
    message, which Inspect marks itself."""
    for index in range(len(messages) - 1, -1, -1):
        message = messages[index]
        if message.get("role") in MARKABLE_ROLES and message.get("content"):
            return index
    return None


def _as_blocks(message: dict) -> None:
    """A user or tool message's non-empty string content as one text block, so
    the prefix is sent in the same form on every call, whichever message carried
    the breakpoint on the previous one. Empty strings stay: Anthropic rejects
    empty text blocks."""
    content = message.get("content")
    if message.get("role") in MARKABLE_ROLES and isinstance(content, str) and content:
        message["content"] = [{"type": "text", "text": content}]


def add_conversation_breakpoint(request: dict) -> bool:
    """Put one cache breakpoint on the newest user or tool message of a pinned
    request, with string content turned into a one-block text list. Mutates
    `request` and returns whether it added the breakpoint; a request it does
    not act on is left untouched."""
    messages = request.get("messages")
    if not (pinned(request) and isinstance(messages, list)):
        return False
    if count_breakpoints(request) >= MAX_BREAKPOINTS:
        return False
    target = _target(messages)
    if target is None:
        return False
    content = messages[target]["content"]
    if isinstance(content, list) and "cache_control" in content[-1]:
        return False
    for message in messages:
        _as_blocks(message)
    messages[target]["content"][-1]["cache_control"] = {"type": "ephemeral"}
    return True


def installed() -> bool:
    """Whether Inspect's marker function is currently the harness wrapper."""
    current = getattr(importlib.import_module(INSPECT_MODULE), INSPECT_FUNCTION, None)
    return bool(getattr(current, _INSTALLED, False))


def install() -> None:
    """Wrap Inspect's marker function: the original runs first, then the
    conversation breakpoint. Idempotent. The provider looks the function up at
    call time, so the wrapper takes effect for every later request. A missing
    function raises: an Inspect upgrade that moves it must fail loudly, never
    drop caching silently."""
    module = importlib.import_module(INSPECT_MODULE)
    original = getattr(module, INSPECT_FUNCTION, None)
    if not callable(original):
        raise RuntimeError(
            f"{INSPECT_MODULE}.{INSPECT_FUNCTION} is gone: the Inspect upgrade moved the "
            "function the `marker` caching mechanism wraps (fix-openrouter-caching, design D3)")
    if getattr(original, _INSTALLED, False):
        return

    @functools.wraps(original)
    def with_conversation_breakpoint(request: dict) -> None:
        original(request)
        add_conversation_breakpoint(request)

    setattr(with_conversation_breakpoint, _INSTALLED, True)
    setattr(module, INSPECT_FUNCTION, with_conversation_breakpoint)
