# ABOUTME: Verifies the Messages API requests ClaudeClient builds, through the real Anthropic SDK.
# ABOUTME: Covers sampling params, adaptive thinking, effort, prompt caching, token counting and error propagation.

"""
Facts these tests encode, each from Anthropic, not from our code:
- Every offered model (Claude 5 and later) returns 400 on a non-default
  temperature/top_p/top_k (measured 2026-10-01 on sonnet-5-5; model pages), and
  anthropic>=1.0 removed those kwargs from messages.create (MIGRATION.md).
- Effort goes in output_config.effort (build-with-claude/effort).
- Automatic prompt caching is a top-level cache_control={"type": "ephemeral"}
  (pricing / prompt-caching docs); the 2024 prompt-caching beta header is obsolete.
- Token counting is GA at POST /v1/messages/count_tokens.
"""

import asyncio

import anthropic
import pytest

from claude.models import TEXT_MODELS
from tests.claude_wire import Wire, error_body, message_body

ADAPTIVE = {"type": "adaptive", "display": "summarized"}
USER = [{"role": "user", "content": "hi"}]


def _client(monkeypatch, wire, **kwargs):
    wire.install(monkeypatch)
    from claude.claude_api.client import ClaudeClient
    client = ClaudeClient(api_key="test-key", **kwargs)
    client.INITIAL_RETRY_DELAY = 0
    return client


def _stream(client, **kwargs):
    return "".join(client.send_request_streaming(messages=USER, **kwargs))


# --- Sampling params and thinking --------------------------------------------


@pytest.mark.parametrize("model", TEXT_MODELS)
def test_request_has_no_sampling_params_and_adaptive_thinking(monkeypatch, model):
    wire = Wire()
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER, model=model))
    body = wire.bodies[-1]
    assert body["model"] == model
    assert not {"temperature", "top_p", "top_k"} & set(body)
    assert body["thinking"] == ADAPTIVE


@pytest.mark.parametrize("model", TEXT_MODELS)
def test_streaming_request_has_no_sampling_params_and_adaptive_thinking(monkeypatch, model):
    wire = Wire()
    client = _client(monkeypatch, wire)
    assert _stream(client, model=model) == "ok"
    body = wire.bodies[-1]
    assert body["stream"] is True
    assert not {"temperature", "top_p", "top_k"} & set(body)
    assert body["thinking"] == ADAPTIVE


# --- Effort ------------------------------------------------------------------


@pytest.mark.parametrize("effort", ["low", "medium", "high", "xhigh", "max"])
def test_effort_is_sent_in_output_config(monkeypatch, effort):
    wire = Wire()
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER, effort=effort))
    assert wire.bodies[-1]["output_config"] == {"effort": effort}


def test_no_effort_sends_no_output_config(monkeypatch):
    wire = Wire()
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER, effort=None))
    assert "output_config" not in wire.bodies[-1]


def test_effort_merges_with_a_caller_output_format(monkeypatch):
    wire = Wire()
    client = _client(monkeypatch, wire)
    fmt = {"type": "json_schema", "schema": {"type": "object"}}
    asyncio.run(client.send_request(messages=USER, effort="low", output_config={"format": fmt}))
    assert wire.bodies[-1]["output_config"] == {"format": fmt, "effort": "low"}


def test_streaming_sends_effort(monkeypatch):
    wire = Wire()
    client = _client(monkeypatch, wire)
    _stream(client, effort="medium")
    assert wire.bodies[-1]["output_config"] == {"effort": "medium"}


# --- Prompt caching ----------------------------------------------------------


def test_caching_enabled_sends_top_level_cache_control(monkeypatch):
    wire = Wire()
    client = _client(monkeypatch, wire, enable_caching=True)
    asyncio.run(client.send_request(messages=USER))
    _stream(client)
    for body in wire.bodies:
        assert body["cache_control"] == {"type": "ephemeral"}


def test_caching_disabled_sends_no_cache_control(monkeypatch):
    wire = Wire()
    client = _client(monkeypatch, wire, enable_caching=False)
    asyncio.run(client.send_request(messages=USER))
    _stream(client)
    for body in wire.bodies:
        assert "cache_control" not in body


def test_no_obsolete_prompt_caching_beta_header(monkeypatch):
    wire = Wire()
    client = _client(monkeypatch, wire, enable_caching=True)
    asyncio.run(client.send_request(messages=USER))
    assert "anthropic-beta" not in wire.requests[-1].headers


def test_cache_tokens_are_tracked(monkeypatch):
    usage = {"input_tokens": 3, "output_tokens": 5,
             "cache_read_input_tokens": 700, "cache_creation_input_tokens": 900}
    wire = Wire((200, message_body(usage=usage)))
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER))
    stats = client.get_usage_stats()
    assert stats["cache_read_tokens"] == 700
    assert stats["cache_creation_tokens"] == 900


# --- Token counting ----------------------------------------------------------


def test_count_tokens_uses_the_ga_endpoint(monkeypatch):
    wire = Wire((200, {"input_tokens": 42}))
    client = _client(monkeypatch, wire, model="claude-opus-5")
    assert asyncio.run(client.count_tokens(USER, system="be brief")) == 42
    request = wire.requests[-1]
    assert request.url.path == "/v1/messages/count_tokens"
    assert "beta" not in str(request.url)
    body = wire.bodies[-1]
    assert body["model"] == "claude-opus-5"
    assert body["system"] == "be brief"


# --- Errors reach the caller as the SDK's own exception -----------------------


def test_bad_request_raises_the_sdk_error(monkeypatch):
    wire = Wire(error_body(400, "invalid_request_error", "`temperature` is deprecated for this model."))
    client = _client(monkeypatch, wire)
    with pytest.raises(anthropic.BadRequestError, match="temperature` is deprecated"):
        asyncio.run(client.send_request(messages=USER))
    assert len(wire.requests) == 1, "a 4xx must not be retried"


def test_exhausted_rate_limit_retries_raise_the_last_error(monkeypatch):
    wire = Wire(error_body(429, "rate_limit_error", "slow down"))
    client = _client(monkeypatch, wire)
    with pytest.raises(anthropic.RateLimitError, match="slow down"):
        asyncio.run(client.send_request(messages=USER))
    assert len(wire.requests) == client.MAX_RETRIES


def test_streaming_error_raises_the_sdk_error(monkeypatch):
    wire = Wire(error_body(400, "invalid_request_error", "bad stream"))
    client = _client(monkeypatch, wire)
    with pytest.raises(anthropic.BadRequestError, match="bad stream"):
        _stream(client)


# --- Usage cost is priced by the model that answered ---------------------------
# Expected prices are Anthropic's published per-MTok rates (about-claude/pricing,
# read 2026-10-01, Sonnet 5.5 cache hit re-read 2026-10-14): base input / 5m
# cache write / cache hit / output.
#   Sonnet 5.5: $2 / $2.50 / $0.10 / $10      Opus 5: $5 / $6.25 / $0.50 / $25

MTOK = 1_000_000
ONE_MTOK_EACH = {"input_tokens": MTOK, "output_tokens": MTOK,
                 "cache_read_input_tokens": MTOK, "cache_creation_input_tokens": MTOK}


def test_usage_cost_uses_the_answering_models_prices(monkeypatch):
    wire = Wire((200, message_body(model="claude-sonnet-5-5", usage=ONE_MTOK_EACH)))
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER))
    stats = client.get_usage_stats()
    assert stats["input_cost_usd"] == 2.0
    assert stats["output_cost_usd"] == 10.0
    # Sonnet 5.5 cache hits are $0.10/MTok (pricing page footnote 2, 2026-10-14).
    assert stats["cache_read_cost_usd"] == 0.1
    assert stats["cache_write_cost_usd"] == 2.5
    assert stats["total_cost_usd"] == 14.6
    assert stats["cache_savings_usd"] == 1.9


def test_usage_cost_sums_calls_on_different_models(monkeypatch):
    usage = {"input_tokens": MTOK, "output_tokens": MTOK,
             "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
    wire = Wire((200, message_body(model="claude-sonnet-5-5", usage=usage)),
                (200, message_body(model="claude-opus-5", usage=usage)))
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER))
    _stream(client, model="claude-opus-5")
    stats = client.get_usage_stats()
    assert stats["input_cost_usd"] == 7.0
    assert stats["output_cost_usd"] == 35.0
    assert stats["total_cost_usd"] == 42.0


def test_usage_from_an_unpriced_model_is_reported_not_guessed(monkeypatch):
    wire = Wire((200, message_body(model="claude-unknown-9", usage=ONE_MTOK_EACH)))
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER))
    stats = client.get_usage_stats()
    assert stats["total_cost_usd"] == 0.0
    assert stats["unpriced_models"] == ["claude-unknown-9"]
    assert stats["input_tokens"] == MTOK


def test_reset_clears_cost(monkeypatch):
    wire = Wire((200, message_body(usage=ONE_MTOK_EACH)))
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER))
    client.reset_usage_stats()
    stats = client.get_usage_stats()
    assert stats["total_cost_usd"] == 0.0
    assert stats["input_tokens"] == 0


# --- Haiku 5.5 long-context tier ------------------------------------------------
# about-claude/pricing "Long context pricing", read 2026-10-14: a Haiku 5.5
# request whose prompt (input + cache reads + cache writes) is over 100,000
# tokens is billed entirely at the long-context rates.
#   up to 100K: $0.10 in / $0.125 5m write / $0.01 cache hit / $0.50 out
#   over 100K:  $0.50 in / $0.625 5m write / $0.05 cache hit / $2.50 out


def _haiku_stats(monkeypatch, input_tokens, cache_read, cache_write, output_tokens):
    usage = {"input_tokens": input_tokens, "output_tokens": output_tokens,
             "cache_read_input_tokens": cache_read, "cache_creation_input_tokens": cache_write}
    wire = Wire((200, message_body(model="claude-haiku-5-5", usage=usage)))
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER))
    return client.get_usage_stats()


def test_haiku_prompt_of_exactly_100k_tokens_is_billed_at_base_rates(monkeypatch):
    # 42,000 + 50,000 + 8,000 = 100,000 prompt tokens.
    stats = _haiku_stats(monkeypatch, 42_000, 50_000, 8_000, 2_000)
    assert stats["input_cost_usd"] == 0.0042     # 42,000 x $0.10/M
    assert stats["cache_read_cost_usd"] == 0.0005  # 50,000 x $0.01/M
    assert stats["cache_write_cost_usd"] == 0.001  # 8,000 x $0.125/M
    assert stats["output_cost_usd"] == 0.001     # 2,000 x $0.50/M
    assert stats["total_cost_usd"] == 0.0067
    assert stats["cache_savings_usd"] == 0.0045  # 50,000 x ($0.10 - $0.01)/M


def test_haiku_prompt_of_100001_tokens_is_billed_at_long_context_rates(monkeypatch):
    # 42,001 + 50,000 + 8,000 = 100,001 prompt tokens.
    stats = _haiku_stats(monkeypatch, 42_001, 50_000, 8_000, 2_000)
    assert stats["input_cost_usd"] == 0.021      # 42,001 x $0.50/M = 0.0210005
    assert stats["cache_read_cost_usd"] == 0.0025  # 50,000 x $0.05/M
    assert stats["cache_write_cost_usd"] == 0.005  # 8,000 x $0.625/M
    assert stats["output_cost_usd"] == 0.005     # 2,000 x $2.50/M
    assert stats["total_cost_usd"] == 0.0335
    assert stats["cache_savings_usd"] == 0.0225  # 50,000 x ($0.50 - $0.05)/M


def test_haiku_cache_tokens_count_toward_the_long_context_threshold(monkeypatch):
    # input_tokens alone (42,000) is far below 100K; the cache read tips it over.
    stats = _haiku_stats(monkeypatch, 42_000, 50_001, 8_000, 2_000)
    assert stats["input_cost_usd"] == 0.021      # 42,000 x $0.50/M
    assert stats["output_cost_usd"] == 0.005     # 2,000 x $2.50/M


def test_long_prompts_on_other_models_keep_flat_rates(monkeypatch):
    # Only Haiku 5.5 has a long-context tier ("Claude 4.6 and later models
    # (except Claude Haiku 5.5) include the full 1M token context window at
    # standard pricing").
    usage = {"input_tokens": 200_000, "output_tokens": 0,
             "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0}
    wire = Wire((200, message_body(model="claude-sonnet-5-5", usage=usage)))
    client = _client(monkeypatch, wire)
    asyncio.run(client.send_request(messages=USER))
    assert client.get_usage_stats()["input_cost_usd"] == 0.4  # 200,000 x $2/M
