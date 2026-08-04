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
FABLE_5 = "claude-fable-5"
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
