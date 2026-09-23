# ABOUTME: Locks Claude model-list currency and the per-model billing/context metadata.
# ABOUTME: Guards the three hand-copied dropdowns against drift from the canonical model list.

"""
Every Claude model has four pieces of metadata spread across separate files:
the dropdown options, pricing.json, TokenManager.CONTEXT_WINDOWS, and
ClaudeClient.THINKING_ONLY_MODELS. A model missing from any one of them is a
silent defect — a wrong price under-reports cost, a missing THINKING_ONLY entry
sends `temperature` and earns a 400.

Expected values come from Anthropic's published pricing and model-overview
tables, not from the repo's own dicts, so these are independent assertions.
"""

import json
import os

from claude.claude_api.client import ClaudeClient
from claude.claude_api.utils import TokenManager
from claude.nodes import ClaudeAPIClient
from claude.token_counter import ClaudeTokenCounter
from claude.vision_analysis import ClaudeVisionAnalysis


OPUS_5 = "claude-opus-5"
OPUS_5_5 = "claude-opus-5-5"
FABLE_5 = "claude-fable-5"
FABLE_5_1 = "claude-fable-5-1"
OPUS_4_7 = "claude-opus-4-7"
SONNET_4_6 = "claude-sonnet-4-6"
OPUS_4_6 = "claude-opus-4-6"


def _pricing():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "claude", "pricing.json")
    with open(path) as f:
        return json.load(f)["models"]


def _combo_options(node_cls, input_name="model"):
    """Pull a Combo input's options off a V3 node schema."""
    schema = node_cls.define_schema()
    for spec in schema.inputs:
        if getattr(spec, "id", None) == input_name:
            return list(spec.options)
    raise AssertionError(f"{node_cls.__name__} has no '{input_name}' combo input")


# --- Opus 5 is offered everywhere a Claude model can be chosen ---------------


def test_opus_5_in_client_node_dropdown():
    assert OPUS_5 in _combo_options(ClaudeAPIClient)


def test_opus_5_in_token_counter_dropdown():
    assert OPUS_5 in _combo_options(ClaudeTokenCounter)


def test_opus_5_in_vision_dropdown():
    assert OPUS_5 in _combo_options(ClaudeVisionAnalysis)


def test_opus_5_priced_at_published_rate():
    # https://platform.claude.com/docs/en/about-claude/pricing — $5 / $25 per MTok.
    entry = _pricing()[OPUS_5]
    assert entry["input_price_per_mtok"] == 5.0
    assert entry["output_price_per_mtok"] == 25.0
    assert entry["cache_read_price_per_mtok"] == 0.5


def test_opus_5_has_1m_context():
    assert TokenManager.CONTEXT_WINDOWS[OPUS_5] == 1_000_000


def test_opus_5_rejects_sampling_params():
    # Claude 4.7 and later 400 on a non-default temperature/top_p/top_k.
    assert OPUS_5 in ClaudeClient.THINKING_ONLY_MODELS


def test_fable_5_1_offered_in_every_dropdown():
    for node in (ClaudeAPIClient, ClaudeTokenCounter, ClaudeVisionAnalysis):
        assert FABLE_5_1 in _combo_options(node)


def test_fable_5_1_is_not_the_default():
    # $10 / $50 per MTok must be opted into, not handed to every new node.
    assert _combo_options(ClaudeAPIClient)[0] != FABLE_5_1


def test_fable_5_1_priced_at_published_rate():
    # https://platform.claude.com/docs/en/about-claude/pricing — $10 / $50 per
    # MTok; cache hits are 0.025x base on Fable 5.1 ($0.25), not the usual 0.1x.
    entry = _pricing()[FABLE_5_1]
    assert entry["input_price_per_mtok"] == 10.0
    assert entry["output_price_per_mtok"] == 50.0
    assert entry["cache_read_price_per_mtok"] == 0.25


def test_fable_5_1_has_1m_context():
    assert TokenManager.CONTEXT_WINDOWS[FABLE_5_1] == 1_000_000


def test_fable_5_1_rejects_sampling_params():
    assert FABLE_5_1 in ClaudeClient.THINKING_ONLY_MODELS


def test_opus_5_5_offered_in_every_dropdown():
    for node in (ClaudeAPIClient, ClaudeTokenCounter, ClaudeVisionAnalysis):
        assert OPUS_5_5 in _combo_options(node)


def test_opus_5_5_priced_at_published_rate():
    # https://platform.claude.com/docs/en/about-claude/pricing — $4 / $20 per
    # MTok; cache hits are 0.05x base on Opus 5.5 ($0.20), not the usual 0.1x.
    entry = _pricing()[OPUS_5_5]
    assert entry["input_price_per_mtok"] == 4.0
    assert entry["output_price_per_mtok"] == 20.0
    assert entry["cache_read_price_per_mtok"] == 0.2


def test_token_counter_fallback_prices_every_offered_model(monkeypatch):
    # When pricing.json cannot be read the counter falls back to a hardcoded
    # table; a model missing there reports $0 instead of its real cost.
    import claude.token_counter as token_counter
    from claude.models import TEXT_MODELS

    def unreadable(*args, **kwargs):
        raise OSError("pricing.json unreadable")

    monkeypatch.setattr(token_counter, "open", unreadable, raising=False)
    pricing, _ = ClaudeTokenCounter.load_pricing()
    assert set(TEXT_MODELS) <= set(pricing)
    assert pricing[OPUS_5_5] == {"input": 4.0, "output": 20.0}


def test_opus_5_5_has_1m_context():
    assert TokenManager.CONTEXT_WINDOWS[OPUS_5_5] == 1_000_000


def test_opus_5_5_rejects_sampling_params():
    # Measured 2026-09-23: temperature=0.7 returns 400
    # "`temperature` is deprecated for this model."
    assert OPUS_5_5 in ClaudeClient.THINKING_ONLY_MODELS


# --- Defects in the existing model metadata ---------------------------------


def test_fable_5_rejects_sampling_params():
    # Fable 5 is a Claude 4.7-and-later model: sending temperature returns 400.
    assert FABLE_5 in ClaudeClient.THINKING_ONLY_MODELS


def test_opus_4_7_priced_at_published_rate():
    # Published rate is $5 / $25 per MTok. $15 / $75 is Opus 4.1's rate.
    entry = _pricing()[OPUS_4_7]
    assert entry["input_price_per_mtok"] == 5.0
    assert entry["output_price_per_mtok"] == 25.0
    assert entry["cache_read_price_per_mtok"] == 0.5


def test_4_6_family_has_1m_context():
    # "Claude 4.6 and later models include the full 1M token context window at
    # standard pricing" — no beta header, no long-context premium.
    assert TokenManager.CONTEXT_WINDOWS[SONNET_4_6] == 1_000_000
    assert TokenManager.CONTEXT_WINDOWS[OPUS_4_6] == 1_000_000


def test_only_4_5_family_is_capped_at_200k():
    capped = {m for m, w in TokenManager.CONTEXT_WINDOWS.items() if w == 200_000}
    assert capped == {"claude-haiku-4-5-20251001", "claude-sonnet-4-5-20250929"}


# --- Drift guards: the four metadata sources must agree ----------------------


def test_every_dropdown_offers_the_same_models():
    canonical = _combo_options(ClaudeAPIClient)
    assert _combo_options(ClaudeTokenCounter) == canonical
    # The vision node prepends a sentinel that defers to the client's model.
    assert _combo_options(ClaudeVisionAnalysis) == ["(inherit from client)"] + canonical


def test_every_offered_model_is_priced():
    priced = set(_pricing())
    assert set(_combo_options(ClaudeAPIClient)) <= priced


def test_every_offered_model_has_a_context_window():
    assert set(_combo_options(ClaudeAPIClient)) <= set(TokenManager.CONTEXT_WINDOWS)


def test_pricing_fallback_matches_pricing_json():
    # token_counter's hardcoded fallback is used when pricing.json fails to load;
    # if it drifts, a read failure silently changes every cost estimate.
    fallback, _ = ClaudeTokenCounter.load_pricing.__func__(ClaudeTokenCounter)
    published = _pricing()
    for model, prices in published.items():
        assert fallback[model]["input"] == prices["input_price_per_mtok"], model
        assert fallback[model]["output"] == prices["output_price_per_mtok"], model
