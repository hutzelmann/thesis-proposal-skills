"""L0 coverage for the `marker` caching mechanism (harness/openrouter_cache.py).

Two layers. The pure function is tested on plain request dicts. The wire tests
build models exactly as the matrix does (`matrix.build_model`) and capture the
keyword arguments Inspect's OpenRouter provider hands to the OpenAI SDK's
`chat.completions.create`: the request body as it would be sent, after Inspect's
own markers and the harness breakpoint. The SDK call is stubbed, so no test here
calls a model or opens a socket; the API key is a placeholder.
"""

from __future__ import annotations

import asyncio
import copy
import importlib

import matrix
import openrouter_cache as oc
import pytest
import support
from helpers import shipped_registry

EPHEMERAL = {"type": "ephemeral"}
PIN = {"provider": support.provider_pin()}


def _request(*messages, extra_body=None, tools=None) -> dict:
    request = {"model": "anthropic/claude-x", "messages": [dict(m) for m in messages]}
    if extra_body is not None:
        request["extra_body"] = extra_body
    if tools is not None:
        request["tools"] = tools
    return request


SYSTEM = {"role": "system", "content": "You have bash."}
USER = {"role": "user", "content": "Read the notes."}
CALL = {"role": "assistant", "content": "", "tool_calls": [{"id": "c1"}]}
RESULT = {"role": "tool", "content": "note one", "tool_call_id": "c1"}


def _marks(request: dict) -> list[tuple[int, int]]:
    """(message index, block index) of every cache_control on message content."""
    return [(i, j) for i, m in enumerate(request["messages"])
            if isinstance(m["content"], list)
            for j, block in enumerate(m["content"]) if "cache_control" in block]


# ---------- the pure function ---------------------------------------------------


def test_the_newest_tool_result_gets_the_breakpoint_as_a_one_block_list():
    request = _request(SYSTEM, USER, CALL, RESULT, extra_body=dict(PIN))
    assert oc.add_conversation_breakpoint(request)
    system, user, call, result = request["messages"]
    assert result["content"] == [{"type": "text", "text": "note one", "cache_control": EPHEMERAL}]
    assert user["content"] == [{"type": "text", "text": "Read the notes."}], (
        "every user and tool string is sent as a block list, marked or not")
    assert call["content"] == "", "assistant content stays as Inspect flattened it"
    assert system["content"] == "You have bash.", "the system message is Inspect's to mark"
    assert _marks(request) == [(3, 0)]


def test_list_content_is_marked_on_its_last_block():
    last = {"role": "user", "content": [{"type": "text", "text": "a"},
                                        {"type": "text", "text": "b"}]}
    request = _request(SYSTEM, last, extra_body=dict(PIN))
    assert oc.add_conversation_breakpoint(request)
    assert _marks(request) == [(1, 1)]


def test_the_walk_passes_textless_assistant_turns_and_empty_results():
    empty = {"role": "tool", "content": "", "tool_call_id": "c2"}
    request = _request(SYSTEM, USER, CALL, RESULT, CALL, empty, extra_body=dict(PIN))
    assert oc.add_conversation_breakpoint(request)
    assert _marks(request) == [(3, 0)]
    assert request["messages"][5]["content"] == "", "Anthropic rejects an empty text block"


@pytest.mark.parametrize("extra_body", [
    None,  # the judge, the persona, any unrouted row, any row after a rollback
    {"provider": {"order": ["anthropic"], "allow_fallbacks": False}},  # not the harness pin
], ids=["unpinned", "other-pin"])
def test_requests_the_harness_did_not_route_are_untouched(extra_body):
    request = _request(SYSTEM, USER, CALL, RESULT, extra_body=extra_body)
    before = copy.deepcopy(request)
    assert not oc.add_conversation_breakpoint(request)
    assert request == before


def test_an_unpinned_single_message_prompt_is_never_marked():
    """The judge's and the persona's one-shot prompts carry no pin."""
    request = _request({"role": "user", "content": "GRADE THIS DRAFT"})
    before = copy.deepcopy(request)
    assert not oc.add_conversation_breakpoint(request)
    assert request == before


def test_a_pinned_single_message_heads_a_conversation_and_is_marked():
    """A dialogue task's first turn: the model under test gets the skill prompt
    as one user message and no system message. Marking it lets the second turn
    read the skill body instead of writing it (spec: a request of the model
    under test heads a conversation, even as a single message)."""
    request = _request({"role": "user", "content": "SKILL PROMPT"}, extra_body=dict(PIN))
    assert oc.add_conversation_breakpoint(request)
    assert request["messages"] == [{"role": "user", "content": [
        {"type": "text", "text": "SKILL PROMPT", "cache_control": EPHEMERAL}]}]


def test_the_four_marker_cap_holds():
    marked = {"role": "system", "content": [{"type": "text", "text": "s",
                                             "cache_control": EPHEMERAL}]}
    tools = [{"type": "function", "cache_control": EPHEMERAL}] * 3
    request = _request(marked, USER, CALL, RESULT, extra_body=dict(PIN), tools=tools)
    assert oc.count_breakpoints(request) == 4
    before = copy.deepcopy(request)
    assert not oc.add_conversation_breakpoint(request)
    assert request == before
    request["tools"] = tools[:2]
    assert oc.add_conversation_breakpoint(request), "three markers leave room for one"
    assert oc.count_breakpoints(request) == 4


def test_an_already_marked_last_block_is_not_marked_twice():
    last = {"role": "tool", "content": [{"type": "text", "text": "r", "cache_control": EPHEMERAL}]}
    request = _request(SYSTEM, CALL, last, extra_body=dict(PIN))
    assert not oc.add_conversation_breakpoint(request)
    assert oc.count_breakpoints(request) == 1


def test_a_conversation_of_system_and_assistant_turns_only_has_nothing_to_mark():
    request = _request(SYSTEM, {"role": "assistant", "content": "hello"}, extra_body=dict(PIN))
    before = copy.deepcopy(request)
    assert not oc.add_conversation_breakpoint(request)
    assert request == before


# ---------- install and the guard on Inspect's private symbol -------------------


def test_the_wrapped_inspect_symbol_exists():
    """Guard: an Inspect upgrade that renames or moves the marker function must
    fail offline, not silently drop the conversation breakpoint."""
    module = importlib.import_module(oc.INSPECT_MODULE)
    assert callable(getattr(module, oc.INSPECT_FUNCTION, None))


def test_install_wraps_once_and_calls_inspect_first(inspect_markers):
    module = importlib.import_module(oc.INSPECT_MODULE)
    assert not oc.installed()
    oc.install()
    oc.install()
    wrapper = getattr(module, oc.INSPECT_FUNCTION)
    assert oc.installed()
    assert wrapper.__wrapped__ is inspect_markers, "wrapped once, around Inspect's own function"
    request = _request(SYSTEM, USER, CALL, RESULT, extra_body=dict(PIN))
    wrapper(request)
    assert request["messages"][0]["content"][0]["cache_control"] == EPHEMERAL, "Inspect's marker"
    assert _marks(request) == [(0, 0), (3, 0)]


@pytest.mark.usefixtures("inspect_markers")
def test_install_refuses_when_inspect_moved_the_symbol(monkeypatch):
    module = importlib.import_module(oc.INSPECT_MODULE)
    monkeypatch.delattr(module, oc.INSPECT_FUNCTION)
    with pytest.raises(RuntimeError, match=oc.INSPECT_FUNCTION):
        oc.install()


# ---------- the request body on the wire --------------------------------------------

REGISTRY = shipped_registry()
# a routed row, picked by family rather than through the judge's ID, which a weekly
# bump can hold off the roster (track-model-currency, `[role_prices]`)
ANTHROPIC = next(m for m in REGISTRY.models
                 if m.enabled and m.family == support.PINNED_FAMILY)
OTHER = next(m for m in REGISTRY.models if m.enabled and m.family != support.PINNED_FAMILY)

COMPLETION = {
    "id": "gen-offline", "object": "chat.completion", "created": 0, "model": "offline",
    "choices": [{"index": 0, "finish_reason": "stop",
                 "message": {"role": "assistant", "content": "ok"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
}


@pytest.fixture
def wire(monkeypatch, request):
    """`send(model, messages)` generates once and returns the keyword arguments
    the provider passed to `chat.completions.create`, deep-copied at the call.
    Inspect's marker function is restored afterwards (a test may install the
    wrapper)."""
    request.getfixturevalue("routable_openrouter")
    from inspect_ai.model import GenerateConfig, get_model
    from inspect_ai.tool import bash, text_editor
    from openai.types.chat import ChatCompletion

    sent: list[dict] = []

    async def create(**kwargs):
        sent.append(copy.deepcopy(kwargs))
        return ChatCompletion.model_validate(COMPLETION)

    def send(model, messages, tools=True) -> dict:
        model = get_model(model) if isinstance(model, str) else model
        monkeypatch.setattr(model.api.client.chat.completions, "create", create)
        asyncio.run(model.generate(messages, tools=[bash(timeout=60), text_editor()] if tools
                                   else [], config=GenerateConfig(max_tokens=16)))
        return sent[-1]

    return send


def _conversation():
    from inspect_ai.model import (
        ChatMessageAssistant,
        ChatMessageSystem,
        ChatMessageTool,
        ChatMessageUser,
    )
    from inspect_ai.tool import ToolCall

    def call(k, text, fn, args):
        return ChatMessageAssistant(content=text, tool_calls=[
            ToolCall(id=f"c{k}", function=fn, arguments=args)])

    return [
        ChatMessageSystem(content="You have bash and a text editor."),
        ChatMessageUser(content="Read the notes."),
        call(1, "Reading the first note.", "bash", {"cmd": "cat ws/a.md"}),
        ChatMessageTool(content="note one", tool_call_id="c1", function="bash"),
        call(2, "", "text_editor", {"command": "view", "path": "ws/b.md"}),
        ChatMessageTool(content="note two", tool_call_id="c2", function="text_editor"),
    ]


def _routed(mechanism: str):
    return matrix.build_model(ANTHROPIC, support.routing_for(ANTHROPIC, mechanism))


def _count(body: dict) -> int:
    return oc.count_breakpoints(body)


def test_marker_sends_the_pin_and_one_breakpoint_on_the_newest_tool_result(wire):
    body = wire(_routed("marker"), _conversation())
    assert body["model"] == ANTHROPIC.id.removeprefix("openrouter/")
    assert body["extra_body"] == {"provider": {"order": ["amazon-bedrock", "google-vertex"],
                                               "allow_fallbacks": False}}
    system, user, first, result, textless, last = body["messages"]
    assert system["content"][-1]["cache_control"] == EPHEMERAL, "Inspect's system marker"
    assert user["content"] == [{"type": "text", "text": "Read the notes."}]
    assert result["content"] == [{"type": "text", "text": "note one"}]
    assert (first["content"], textless["content"]) == ("Reading the first note.", "")
    assert last == {"role": "tool", "tool_call_id": "c2", "content": [
        {"type": "text", "text": "note two", "cache_control": EPHEMERAL}]}
    assert body["tools"][-1]["cache_control"] == EPHEMERAL, "Inspect's last-tool marker"
    assert "cache_control" not in body["tools"][0]
    assert _count(body) == 3, "system, last tool, and the one conversation breakpoint"


def test_marker_marks_the_last_block_of_list_content_beside_inspects_own_mark(wire):
    from inspect_ai.model import ChatMessageUser, ContentText

    conversation = [*_conversation(), ChatMessageUser(content=[ContentText(text="a"),
                                                               ContentText(text="b")])]
    body = wire(_routed("marker"), conversation)
    last = body["messages"][-1]["content"]
    assert [block.get("cache_control") for block in last] == [EPHEMERAL, EPHEMERAL], (
        "Inspect marks the penultimate block of a list, the harness the last one")
    assert _count(body) == 4, "Anthropic's limit, reached and not exceeded"


def test_an_unpinned_anthropic_model_is_sent_as_before_with_the_wrapper_installed(wire):
    """The judge's bare ID, and every Anthropic row after a rollback."""
    before = wire(ANTHROPIC.id, _conversation())
    oc.install()
    after = wire(ANTHROPIC.id, _conversation())
    for body in (before, after):
        body.pop("extra_headers")  # carries a fresh request ID on every call
    assert after == before
    assert "provider" not in after.get("extra_body", {})
    assert all(isinstance(m["content"], str) for m in after["messages"][1:])
    assert _count(after) == 2


def test_a_single_message_judge_prompt_is_sent_unmarked(wire):
    oc.install()
    body = wire(ANTHROPIC.id, "GRADE THIS DRAFT", tools=False)
    assert body["messages"] == [{"role": "user", "content": "GRADE THIS DRAFT"}]
    assert "provider" not in body.get("extra_body", {})


def test_a_routed_first_dialogue_turn_is_sent_marked(wire):
    """The model under test's single-message first turn heads the dialogue."""
    body = wire(_routed("marker"), "SKILL PROMPT")
    assert body["messages"] == [{"role": "user", "content": [
        {"type": "text", "text": "SKILL PROMPT", "cache_control": EPHEMERAL}]}]
    assert body["extra_body"] == PIN
    assert _count(body) == 2, "the last tool and the first turn"


def test_a_non_anthropic_row_is_sent_without_pin_or_markers(wire):
    oc.install()
    assert matrix.build_model(OTHER, support.routing_for(OTHER, "marker")) == OTHER.id
    body = wire(OTHER.id, _conversation())
    assert "provider" not in body.get("extra_body", {})
    assert all(isinstance(m["content"], str) for m in body["messages"])
    assert _count(body) == 0


@pytest.mark.usefixtures("routable_openrouter")
def test_build_model_installs_the_wrapper_for_a_routed_row_only():
    matrix.build_model(OTHER, support.routing_for(OTHER, "marker"))
    matrix.build_model(ANTHROPIC, support.routing_for(ANTHROPIC, None))
    assert not oc.installed(), "an unrouted row needs no wrapper"
    built = _routed("marker")
    assert oc.installed()
    assert str(built) == ANTHROPIC.id, "report.py counts a log only under its registry ID"
    assert built.config.extra_body is None
    assert built.model_args == {"provider": support.provider_pin()}
