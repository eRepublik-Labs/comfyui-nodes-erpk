# ABOUTME: Tests the model Combo on the Claude text nodes.
# ABOUTME: Default inherits the client's model; an explicit choice is forwarded.

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from claude.models import INHERIT_FROM_CLIENT, TEXT_MODELS

WIDGET_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")


def _node(module, name):
    import importlib
    return getattr(importlib.import_module(f"claude.{module}"), name)


NODES = [
    ("text_generation", "ClaudeTextGeneration"),
    ("prompt_enhancer", "ClaudePromptEnhancer"),
    ("conversation", "ClaudeConversation"),
]


@pytest.mark.parametrize("module,name", NODES)
def test_model_combo_is_last_widget_and_inherits_by_default(module, name):
    inputs = _node(module, name).define_schema().inputs
    widgets = [i for i in inputs if i.io_type in WIDGET_TYPES]
    assert widgets[-1].id == "model"
    assert widgets[-1].default == INHERIT_FROM_CLIENT
    assert list(widgets[-1].options) == [INHERIT_FROM_CLIENT] + TEXT_MODELS


def _client():
    client = MagicMock()
    client.enable_streaming = False
    response = MagicMock()
    response.content = [MagicMock(type="text", text="ok")]
    client.send_request = AsyncMock(return_value=response)
    return client


def test_text_generation_forwards_explicit_model():
    node = _node("text_generation", "ClaudeTextGeneration")
    client = _client()
    asyncio.run(node.execute(prompt="hi", client=client, model="claude-opus-4-7"))
    assert client.send_request.call_args.kwargs["model"] == "claude-opus-4-7"


def test_text_generation_inherit_sends_no_model():
    node = _node("text_generation", "ClaudeTextGeneration")
    client = _client()
    asyncio.run(node.execute(prompt="hi", client=client, model=INHERIT_FROM_CLIENT))
    assert "model" not in client.send_request.call_args.kwargs


def test_prompt_enhancer_forwards_explicit_model():
    node = _node("prompt_enhancer", "ClaudePromptEnhancer")
    client = _client()
    asyncio.run(node.execute(prompt="a cat", client=client, model="claude-opus-4-7"))
    assert client.send_request.call_args.kwargs["model"] == "claude-opus-4-7"


def test_conversation_forwards_explicit_model():
    node = _node("conversation", "ClaudeConversation")
    client = _client()
    asyncio.run(node.execute(prompt="hi", client=client, model="claude-opus-4-7"))
    assert client.send_request.call_args.kwargs["model"] == "claude-opus-4-7"
