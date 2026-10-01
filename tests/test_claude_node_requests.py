# ABOUTME: Runs each Claude node that sends a Messages request through the real SDK and an in-process transport.
# ABOUTME: Asserts what each node actually puts on the wire for its widget values.

import asyncio

import pytest
import torch

from tests.claude_wire import Wire, message_body

SAMPLING = {"temperature", "top_p", "top_k"}


def _client(monkeypatch, wire, **kwargs):
    wire.install(monkeypatch)
    from claude.claude_api.client import ClaudeClient
    return ClaudeClient(api_key="test-key", **kwargs)


def _image():
    return torch.zeros((1, 8, 8, 3), dtype=torch.float32)


def _run_text_generation(client, **widgets):
    from claude.text_generation import ClaudeTextGeneration
    return asyncio.run(ClaudeTextGeneration.execute(prompt="hi", client=client, **widgets)).args[0]


def _run_conversation(client, **widgets):
    from claude.conversation import ClaudeConversation
    return asyncio.run(ClaudeConversation.execute(prompt="hi", client=client, **widgets)).args[0]


def _run_prompt_enhancer(client, **widgets):
    from claude.prompt_enhancer import ClaudePromptEnhancer
    return asyncio.run(ClaudePromptEnhancer.execute(prompt="a cat", client=client, **widgets)).args[0]


def _run_vision(client, **widgets):
    from claude.vision_analysis import ClaudeVisionAnalysis
    return asyncio.run(ClaudeVisionAnalysis.execute(image=_image(), question="what?", client=client, **widgets)).args[0]


TEXT_NODES = {
    "ClaudeTextGeneration": _run_text_generation,
    "ClaudeConversation": _run_conversation,
    "ClaudePromptEnhancer": _run_prompt_enhancer,
    "ClaudeVisionAnalysis": _run_vision,
}


@pytest.mark.parametrize("node", TEXT_NODES)
def test_temperature_widget_is_not_sent(monkeypatch, node):
    # Every offered model returns 400 on a non-default temperature, and
    # anthropic>=1.0 rejects the kwarg outright, so the widget must be ignored.
    wire = Wire()
    widgets = {} if node == "ClaudeVisionAnalysis" else {"temperature": 0.3}
    assert TEXT_NODES[node](_client(monkeypatch, wire), **widgets) == "ok"
    assert not SAMPLING & set(wire.bodies[-1])


# --- ClaudeStructuredOutput --------------------------------------------------
# Forced tool_choice returns 400 "tool_choice: type tool and any are not
# supported for this model" on sonnet-5-5 and opus-5-5 (measured 2026-10-01),
# so the node asks for output_config.format json_schema instead. The API
# rejects any object schema without "additionalProperties": false (measured
# 2026-10-01: 400 "For 'object' type, 'additionalProperties' must be
# explicitly set to false"), and ClaudeToolDefinition's default schema omits it.

PERSON_TOOL = [{
    "name": "extract_person",
    "description": "Extract a person",
    "input_schema": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "born": {"type": "object", "properties": {"year": {"type": "integer"}}},
            "pets": {"type": "array", "items": {"type": "object", "properties": {"kind": {"type": "string"}}}},
        },
        "required": ["name"],
    },
}]

STRICT_PERSON_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "born": {"type": "object", "properties": {"year": {"type": "integer"}}, "additionalProperties": False},
        "pets": {"type": "array", "items": {"type": "object", "properties": {"kind": {"type": "string"}},
                                            "additionalProperties": False}},
    },
    "required": ["name"],
    "additionalProperties": False,
}


def _run_structured(client, tool=PERSON_TOOL, **widgets):
    from claude.structured_output import ClaudeStructuredOutput
    return asyncio.run(ClaudeStructuredOutput.execute(prompt="Ada, born 1815", tool=tool, client=client, **widgets)).args


def test_structured_output_requests_a_json_schema_not_a_forced_tool(monkeypatch):
    wire = Wire((200, message_body(text='{"name": "Ada"}')))
    _run_structured(_client(monkeypatch, wire), temperature=0.0, max_tokens=2048)
    body = wire.bodies[-1]
    assert body["max_tokens"] == 2048
    assert body["output_config"]["format"] == {"type": "json_schema", "schema": STRICT_PERSON_SCHEMA}
    assert "tool_choice" not in body
    assert "tools" not in body
    assert not SAMPLING & set(body)


def test_structured_output_tells_claude_what_the_json_is_for(monkeypatch):
    # The tool's name and description used to reach Claude via the tools list.
    wire = Wire((200, message_body(text="{}")))
    _run_structured(_client(monkeypatch, wire), system_prompt="Be terse.")
    assert wire.bodies[-1]["system"] == "Be terse.\n\nThe JSON you return is extract_person: Extract a person"


def test_structured_output_does_not_mutate_the_tool_definition(monkeypatch):
    import copy
    tool = copy.deepcopy(PERSON_TOOL)
    _run_structured(_client(monkeypatch, Wire((200, message_body(text="{}")))), tool=tool)
    assert tool == PERSON_TOOL


def test_structured_output_returns_the_json_and_the_thinking(monkeypatch):
    wire = Wire((200, message_body(text='{"name":"Ada","born":{"year":1815}}', thinking="She was born in 1815.")))
    json_output, thinking = _run_structured(_client(monkeypatch, wire))
    assert json_output == '{\n  "name": "Ada",\n  "born": {\n    "year": 1815\n  }\n}'
    assert thinking == "She was born in 1815."


def test_structured_output_rejects_an_explicit_additional_properties_true(monkeypatch):
    tool = [dict(PERSON_TOOL[0], input_schema={"type": "object", "properties": {}, "additionalProperties": True})]
    wire = Wire()
    with pytest.raises(ValueError, match="additionalProperties"):
        _run_structured(_client(monkeypatch, wire), tool=tool)
    assert wire.requests == []


def test_structured_output_truncated_by_max_tokens_says_so(monkeypatch):
    wire = Wire((200, message_body(text='{"name": "Ad', stop_reason="max_tokens")))
    with pytest.raises(ValueError, match="max_tokens"):
        _run_structured(_client(monkeypatch, wire))


# --- effort widget and max_tokens ceiling -------------------------------------
# Effort levels low..max are accepted by every offered model (measured
# 2026-10-01 on sonnet-5-5; build-with-claude/effort). "(model default)" omits
# the field so each model keeps its own default (high; medium on Opus 5.5).
# Every offered model allows 128K output tokens (GET /v1/models max_tokens).

WIDGET_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")
EFFORT_OPTIONS = ["(model default)", "low", "medium", "high", "xhigh", "max"]

# Widget order before this change. widgets_values is positional, so these must
# stay in place and `effort` may only be appended after them.
PRIOR_WIDGETS = {
    "ClaudeTextGeneration": ["prompt", "system_prompt", "temperature", "max_tokens", "use_streaming", "seed", "model"],
    "ClaudeConversation": ["prompt", "system_prompt", "auto_trim", "reset_conversation", "temperature", "max_tokens", "seed", "model"],
    "ClaudePromptEnhancer": ["prompt", "style", "detail_level", "temperature", "max_tokens", "use_streaming", "seed", "model"],
    "ClaudeVisionAnalysis": ["question", "model", "detail_level", "max_tokens", "seed"],
    "ClaudeStructuredOutput": ["prompt", "system_prompt", "temperature", "max_tokens", "seed"],
}
DEFAULT_MAX_TOKENS = {
    "ClaudeTextGeneration": 1024,
    "ClaudeConversation": 2048,
    "ClaudePromptEnhancer": 1024,
    "ClaudeVisionAnalysis": 2048,
    "ClaudeStructuredOutput": 4096,
}


def _node_class(name):
    import importlib
    module = {
        "ClaudeTextGeneration": "text_generation",
        "ClaudeConversation": "conversation",
        "ClaudePromptEnhancer": "prompt_enhancer",
        "ClaudeVisionAnalysis": "vision_analysis",
        "ClaudeStructuredOutput": "structured_output",
    }[name]
    return getattr(importlib.import_module(f"claude.{module}"), name)


def _widgets(name):
    return [i for i in _node_class(name).define_schema().inputs if i.io_type in WIDGET_TYPES]


@pytest.mark.parametrize("name", PRIOR_WIDGETS)
def test_effort_is_appended_after_every_existing_widget(name):
    widgets = _widgets(name)
    assert [w.id for w in widgets] == PRIOR_WIDGETS[name] + ["effort"]
    effort = widgets[-1]
    assert list(effort.options) == EFFORT_OPTIONS
    assert effort.default == "(model default)"
    assert effort.optional is True


@pytest.mark.parametrize("name", PRIOR_WIDGETS)
def test_max_tokens_reaches_the_128k_output_limit_with_default_unchanged(name):
    spec = next(w for w in _widgets(name) if w.id == "max_tokens")
    assert spec.max == 128_000
    assert spec.default == DEFAULT_MAX_TOKENS[name]


def _run(name, client, **widgets):
    if name == "ClaudeStructuredOutput":
        return _run_structured(client, **widgets)
    return TEXT_NODES[name](client, **widgets)


@pytest.mark.parametrize("name", PRIOR_WIDGETS)
def test_effort_choice_is_sent(monkeypatch, name):
    wire = Wire((200, message_body(text="{}")))
    _run(name, _client(monkeypatch, wire), effort="xhigh")
    assert wire.bodies[-1]["output_config"]["effort"] == "xhigh"


@pytest.mark.parametrize("name", PRIOR_WIDGETS)
def test_model_default_effort_sends_no_effort(monkeypatch, name):
    wire = Wire((200, message_body(text="{}")))
    _run(name, _client(monkeypatch, wire), effort="(model default)")
    assert "effort" not in wire.bodies[-1].get("output_config", {})


def test_streaming_text_generation_sends_effort(monkeypatch):
    wire = Wire()
    client = _client(monkeypatch, wire, enable_streaming=True)
    assert _run_text_generation(client, use_streaming=True, effort="low") == "ok"
    assert wire.bodies[-1]["stream"] is True
    assert wire.bodies[-1]["output_config"] == {"effort": "low"}


# --- Streaming and per-node model overrides -----------------------------------


def test_prompt_enhancer_streams_with_the_chosen_model(monkeypatch):
    wire = Wire()
    client = _client(monkeypatch, wire, enable_streaming=True)
    assert _run_prompt_enhancer(client, use_streaming=True, model="claude-opus-5") == "ok"
    body = wire.bodies[-1]
    assert body["stream"] is True
    assert body["model"] == "claude-opus-5"


def test_conversation_trims_against_the_overridden_models_context(monkeypatch):
    # Client model with a small window, node override with 1M: trimming must
    # use the model that is actually called, so nothing is dropped here.
    from claude.claude_api.utils import TokenManager
    monkeypatch.setitem(TokenManager.CONTEXT_WINDOWS, "tiny-window-model", 3_000)
    # Trimming always keeps the 4 most recent messages, so the history needs more.
    turns = [{"role": role, "content": role[0] * 8_000} for role in ("user", "assistant") * 3]
    history = {"messages": turns, "system": None}
    wire = Wire()
    client = _client(monkeypatch, wire, model="tiny-window-model")
    _run_conversation(client, conversation_history=history, model="claude-opus-5", max_tokens=1024)
    body = wire.bodies[-1]
    assert body["model"] == "claude-opus-5"
    assert len(body["messages"]) == 7


def test_conversation_info_reports_usage_of_the_1m_window():
    # Every offered model has a 1M-token context window.
    from claude.conversation import ClaudeConversationInfo
    history = {"messages": [{"role": "user", "content": "x" * 400_000}], "system": None}
    info = ClaudeConversationInfo.execute(conversation_history=history).args[0]
    assert "~10.0% of 1,000,000-token window" in info
