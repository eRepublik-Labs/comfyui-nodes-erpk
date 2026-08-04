# ABOUTME: Locks chat-latest into the OpenAI model list with the right parameter classification.
# ABOUTME: chat-latest is non-reasoning, so reasoning_effort and verbosity must not be sent.

"""
chat-latest is the Instant model used in ChatGPT, exposed on the API as its own
Specialized-models entry ($5 / $30 per MTok) distinct from the versioned
gpt-5.x-chat-latest rows. It supports Chat Completions and Responses, streaming,
structured outputs, function calling and image input — but it does no reasoning,
so it carries neither reasoning_effort nor verbosity.

gpt-5.3-codex is deliberately absent: OpenAI marks v1/chat/completions as "Not
supported" for it, and the text path here calls chat.completions.create, so
listing it would put a dropdown entry in front of users that 404s on every call.
"""

from openai.openai_api.client import OpenAIClient
from openai.nodes import TEXT_MODELS, VISION_MODELS


CHAT_LATEST = "chat-latest"


def test_chat_latest_in_models():
    assert CHAT_LATEST in OpenAIClient.MODELS


def test_chat_latest_offered_in_node_dropdown():
    assert CHAT_LATEST in TEXT_MODELS


def test_chat_latest_uses_max_completion_tokens():
    # max_tokens is deprecated API-wide; this model takes max_completion_tokens.
    assert CHAT_LATEST in OpenAIClient.NEW_TOKEN_PARAM_MODELS


def test_chat_latest_is_not_a_reasoning_model():
    # Sending reasoning_effort to a non-reasoning model is rejected.
    assert CHAT_LATEST not in OpenAIClient.REASONING_MODELS


def test_chat_latest_does_not_take_verbosity():
    # verbosity is not among its supported features.
    assert CHAT_LATEST not in OpenAIClient.VERBOSITY_MODELS


def test_chat_latest_supports_vision():
    # Image input is supported, so it belongs in the vision dropdown.
    assert CHAT_LATEST in VISION_MODELS


def test_responses_only_models_are_not_offered():
    # The text path calls chat.completions.create; a Responses-only model would
    # 404 on every call, so it must not reach the dropdown.
    assert "gpt-5.3-codex" not in TEXT_MODELS
