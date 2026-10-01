# ABOUTME: Locks Claude model-list currency and the per-model billing/context metadata.
# ABOUTME: Guards the three hand-copied dropdowns against drift from the canonical model list.

"""
Every Claude model has three pieces of metadata spread across separate files:
the dropdown options, pricing.json and TokenManager.CONTEXT_WINDOWS. A model
missing from any one of them is a silent defect: a wrong price under-reports
cost, a missing context window trims conversations against the wrong limit.

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
SONNET_5_5 = "claude-sonnet-5-5"
SONNET_5 = "claude-sonnet-5"

# Withdrawn 2026-10-01 (Alex's call): every remaining model is Claude 5 or later.
REMOVED = (
    "claude-opus-4-8",
    "claude-opus-4-7",
    "claude-sonnet-4-6",
    "claude-opus-4-6",
    "claude-haiku-4-5-20251001",
    "claude-sonnet-4-5-20250929",
)


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




# --- Sonnet 5.5 is the default ----------------------------------------------


def test_sonnet_5_5_is_the_default_everywhere():
    from claude.models import DEFAULT_TEXT_MODEL
    from claude.token_counter import ClaudeTokenCounter as Counter
    assert DEFAULT_TEXT_MODEL == SONNET_5_5
    assert ClaudeClient.DEFAULT_MODEL == SONNET_5_5
    assert TokenManager().model == SONNET_5_5
    for node in (ClaudeAPIClient, Counter):
        spec = next(i for i in node.define_schema().inputs if i.id == "model")
        assert spec.default == SONNET_5_5


def test_sonnet_5_5_offered_in_every_dropdown():
    for node in (ClaudeAPIClient, ClaudeTokenCounter, ClaudeVisionAnalysis):
        assert SONNET_5_5 in _combo_options(node)


def test_sonnet_5_5_priced_at_published_rate():
    # https://platform.claude.com/docs/en/about-claude/pricing and the Sonnet 5.5
    # model page: $2 / $10 per MTok, cache hits $0.20 (0.1x).
    entry = _pricing()[SONNET_5_5]
    assert entry["input_price_per_mtok"] == 2.0
    assert entry["output_price_per_mtok"] == 10.0
    assert entry["cache_read_price_per_mtok"] == 0.2


def test_sonnet_5_5_has_1m_context():
    # GET /v1/models/claude-sonnet-5-5 reports max_input_tokens 1000000.
    assert TokenManager.CONTEXT_WINDOWS[SONNET_5_5] == 1_000_000


# --- Withdrawn models are gone from every metadata source -------------------


def test_removed_models_are_not_offered():
    for node in (ClaudeAPIClient, ClaudeTokenCounter, ClaudeVisionAnalysis):
        assert not set(REMOVED) & set(_combo_options(node)), node.__name__


def test_removed_models_have_no_metadata_left():
    for model in REMOVED:
        assert model not in _pricing(), model
        assert model not in TokenManager.CONTEXT_WINDOWS, model


def test_removed_models_absent_from_pricing_fallback(monkeypatch):
    import claude.token_counter as token_counter

    def unreadable(*args, **kwargs):
        raise OSError("pricing.json unreadable")

    monkeypatch.setattr(token_counter, "open", unreadable, raising=False)
    pricing, _ = ClaudeTokenCounter.load_pricing()
    assert not set(REMOVED) & set(pricing)


# --- Sonnet 5 and Fable 5 --------------------------------------------------


def test_sonnet_5_and_fable_5_priced_at_published_rate():
    # https://platform.claude.com/docs/en/about-claude/pricing
    models = _pricing()
    assert models[SONNET_5]["input_price_per_mtok"] == 2.0
    assert models[SONNET_5]["output_price_per_mtok"] == 10.0
    assert models[FABLE_5]["input_price_per_mtok"] == 10.0
    assert models[FABLE_5]["output_price_per_mtok"] == 50.0


def test_sonnet_5_and_fable_5_have_1m_context():
    assert TokenManager.CONTEXT_WINDOWS[SONNET_5] == 1_000_000
    assert TokenManager.CONTEXT_WINDOWS[FABLE_5] == 1_000_000











# --- Drift guards: the three metadata sources must agree ----------------------


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


def test_every_offered_model_has_a_published_5m_cache_write_price():
    # https://platform.claude.com/docs/en/about-claude/pricing "5m cache writes"
    # column, read 2026-10-01. ClaudeUsageStats bills cache creation at this rate.
    published = {
        SONNET_5_5: 2.5, SONNET_5: 2.5, OPUS_5_5: 5.0, OPUS_5: 6.25, FABLE_5_1: 12.5, FABLE_5: 12.5,
    }
    pricing = _pricing()
    assert set(published) == set(_combo_options(ClaudeAPIClient))
    for model, price in published.items():
        assert pricing[model]["cache_write_5m_price_per_mtok"] == price, model
