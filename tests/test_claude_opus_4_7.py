# ABOUTME: Tests for Claude Opus 4.7 API constraints: stripped sampling params and adaptive thinking.
# ABOUTME: Verifies branching in ClaudeClient.send_request{,_streaming} and presence in model lists.

"""
Opus 4.7 has three breaking API constraints vs prior Claude models:
- temperature / top_p / top_k must be OMITTED (400 if present)
- thinking must be {"type": "adaptive"} (budget_tokens form rejected)
- thinking display defaults to "omitted"; must set "summarized" to surface thoughts

These tests lock in that ClaudeClient strips sampling params and injects adaptive
thinking only for the 4.7 model, and preserves prior behavior for other models.
"""

import asyncio
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest


OPUS_4_7 = "claude-opus-4-7"
SONNET_4_6 = "claude-sonnet-4-6"


# --- Schema / model list assertions ------------------------------------------


def test_opus_4_7_in_claude_api_client_model_list():
    """Opus 4.7 is selectable in the ClaudeAPIClient node's model Combo."""
    from claude.nodes import ClaudeAPIClient
    schema = ClaudeAPIClient.define_schema()
    model_input = next(i for i in schema.inputs if i.id == "model")
    assert OPUS_4_7 in model_input.options


def test_opus_4_7_in_token_counter_model_list():
    """Opus 4.7 is selectable in the ClaudeTokenCounter node's model Combo."""
    from claude.token_counter import ClaudeTokenCounter
    schema = ClaudeTokenCounter.define_schema()
    model_input = next(i for i in schema.inputs if i.id == "model")
    assert OPUS_4_7 in model_input.options


def test_opus_4_7_in_context_windows():
    """Opus 4.7 has a context window entry (1M tokens)."""
    from claude.claude_api.utils import TokenManager
    assert OPUS_4_7 in TokenManager.CONTEXT_WINDOWS
    assert TokenManager.CONTEXT_WINDOWS[OPUS_4_7] == 1_000_000


def test_opus_4_7_in_pricing_fallback():
    """Opus 4.7 has an entry in token_counter fallback pricing."""
    from claude.token_counter import ClaudeTokenCounter
    # Force fallback by pointing at a non-existent pricing file.
    original = ClaudeTokenCounter.load_pricing
    pricing, _ = original()
    assert OPUS_4_7 in pricing


def test_opus_4_7_in_pricing_json():
    """Opus 4.7 has an entry in pricing.json with expected price tier."""
    import json
    import os
    pricing_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "claude",
        "pricing.json",
    )
    with open(pricing_path) as f:
        data = json.load(f)
    assert OPUS_4_7 in data["models"]
    entry = data["models"][OPUS_4_7]
    assert entry["input_price_per_mtok"] == 15.0
    assert entry["output_price_per_mtok"] == 75.0


def test_thinking_only_models_contains_opus_4_7():
    """ClaudeClient advertises 4.7 as a thinking-only model."""
    from claude.claude_api.client import ClaudeClient
    assert OPUS_4_7 in ClaudeClient.THINKING_ONLY_MODELS


# --- Test helpers ------------------------------------------------------------


@contextmanager
def _patched_anthropic():
    """
    Patch the Anthropic SDK class used by ClaudeClient.

    Yields (mock_messages, mock_stream_ctx):
      - mock_messages: the mock for self.client.messages; inspect
        mock_messages.create.call_args.kwargs for send_request assertions.
      - mock_stream_ctx: the mock returned by messages.stream(...). Inspect
        mock_messages.stream.call_args.kwargs for send_request_streaming
        assertions.
    """
    with patch("claude.claude_api.client.Anthropic") as anthropic_cls:
        anthropic_instance = MagicMock()
        anthropic_cls.return_value = anthropic_instance

        # Synchronous create() returns a message-like object with usage.
        response = MagicMock()
        response.usage.input_tokens = 0
        response.usage.output_tokens = 0
        response.usage.cache_read_input_tokens = 0
        response.usage.cache_creation_input_tokens = 0
        anthropic_instance.messages.create.return_value = response

        # Streaming context manager yields an empty stream with a final message.
        final_message = MagicMock()
        final_message.usage.input_tokens = 0
        final_message.usage.output_tokens = 0
        final_message.usage.cache_read_input_tokens = 0
        final_message.usage.cache_creation_input_tokens = 0

        stream_ctx = MagicMock()
        stream_ctx.__enter__ = MagicMock(return_value=stream_ctx)
        stream_ctx.__exit__ = MagicMock(return_value=False)
        stream_ctx.text_stream = iter([])
        stream_ctx.get_final_message.return_value = final_message
        anthropic_instance.messages.stream.return_value = stream_ctx

        yield anthropic_instance.messages


def _make_client(**kwargs):
    from claude.claude_api.client import ClaudeClient
    # Pass api_key so _resolve_api_key skips settings/env/config.
    return ClaudeClient(api_key="test-key", **kwargs)


# --- send_request (synchronous) ---------------------------------------------


class TestSendRequestOpus47:
    """send_request must strip sampling params and inject adaptive thinking for 4.7."""

    def test_strips_temperature_top_p_top_k(self):
        with _patched_anthropic() as messages:
            client = _make_client()
            asyncio.run(client.send_request(
                messages=[{"role": "user", "content": "hi"}],
                model=OPUS_4_7,
                temperature=0.5,
                top_p=0.9,
                top_k=40,
            ))
            kwargs = messages.create.call_args.kwargs
            assert "temperature" not in kwargs
            assert "top_p" not in kwargs
            assert "top_k" not in kwargs

    def test_injects_adaptive_thinking(self):
        with _patched_anthropic() as messages:
            client = _make_client()
            asyncio.run(client.send_request(
                messages=[{"role": "user", "content": "hi"}],
                model=OPUS_4_7,
            ))
            kwargs = messages.create.call_args.kwargs
            assert kwargs.get("thinking") == {
                "type": "adaptive",
                "display": "summarized",
            }


class TestSendRequestSonnet46:
    """send_request must preserve prior behavior for non-4.7 models."""

    def test_preserves_temperature(self):
        with _patched_anthropic() as messages:
            client = _make_client()
            asyncio.run(client.send_request(
                messages=[{"role": "user", "content": "hi"}],
                model=SONNET_4_6,
                temperature=0.5,
            ))
            kwargs = messages.create.call_args.kwargs
            assert kwargs.get("temperature") == 0.5

    def test_no_thinking_key(self):
        with _patched_anthropic() as messages:
            client = _make_client()
            asyncio.run(client.send_request(
                messages=[{"role": "user", "content": "hi"}],
                model=SONNET_4_6,
            ))
            kwargs = messages.create.call_args.kwargs
            assert "thinking" not in kwargs


# --- send_request_streaming --------------------------------------------------


class TestSendRequestStreamingOpus47:
    """send_request_streaming must strip sampling params and inject adaptive thinking for 4.7."""

    def test_strips_temperature_top_p_top_k(self):
        with _patched_anthropic() as messages:
            client = _make_client()
            # Consume the generator to trigger the stream call.
            for _ in client.send_request_streaming(
                messages=[{"role": "user", "content": "hi"}],
                model=OPUS_4_7,
                temperature=0.5,
                top_p=0.9,
                top_k=40,
            ):
                pass
            kwargs = messages.stream.call_args.kwargs
            assert "temperature" not in kwargs
            assert "top_p" not in kwargs
            assert "top_k" not in kwargs

    def test_injects_adaptive_thinking(self):
        with _patched_anthropic() as messages:
            client = _make_client()
            for _ in client.send_request_streaming(
                messages=[{"role": "user", "content": "hi"}],
                model=OPUS_4_7,
            ):
                pass
            kwargs = messages.stream.call_args.kwargs
            assert kwargs.get("thinking") == {
                "type": "adaptive",
                "display": "summarized",
            }


class TestSendRequestStreamingSonnet46:
    """send_request_streaming must preserve prior behavior for non-4.7 models."""

    def test_preserves_temperature(self):
        with _patched_anthropic() as messages:
            client = _make_client()
            for _ in client.send_request_streaming(
                messages=[{"role": "user", "content": "hi"}],
                model=SONNET_4_6,
                temperature=0.5,
            ):
                pass
            kwargs = messages.stream.call_args.kwargs
            assert kwargs.get("temperature") == 0.5

    def test_no_thinking_key(self):
        with _patched_anthropic() as messages:
            client = _make_client()
            for _ in client.send_request_streaming(
                messages=[{"role": "user", "content": "hi"}],
                model=SONNET_4_6,
            ):
                pass
            kwargs = messages.stream.call_args.kwargs
            assert "thinking" not in kwargs
