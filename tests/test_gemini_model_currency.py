# ABOUTME: Locks the Gemini 3.5/3.6 text models and Nano Banana 2 Lite into the node dropdowns.
# ABOUTME: Covers the 1K-only output constraint that separates the lite image model from its siblings.

"""
Expected values come from Google's published model and pricing tables, not from
the repo's own dicts.

gemini-3.1-flash-lite-image (Nano Banana 2 Lite) is the first image model whose
resolution constraint is "1K only" rather than "fixed at 1024px". The existing
gate was a hardcoded `model != "gemini-2.5-flash-image"` comparison, which
cannot express a third rule.
"""

import json
import os

from gemini.gemini_api.client import GeminiClient
from gemini.nodes import IMAGE_MODELS, TEXT_MODELS, _resolve_image_size


FLASH_3_6 = "gemini-3.6-flash"
FLASH_LITE_3_5 = "gemini-3.5-flash-lite"
NANO_BANANA_2_LITE = "gemini-3.1-flash-lite-image"


def _pricing():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gemini", "pricing.json")
    with open(path) as f:
        return json.load(f)["models"]


# --- Text models -------------------------------------------------------------


def test_gemini_3_6_flash_offered():
    assert FLASH_3_6 in TEXT_MODELS


def test_gemini_3_5_flash_lite_offered():
    assert FLASH_LITE_3_5 in TEXT_MODELS


def test_gemini_3_6_flash_priced():
    # https://ai.google.dev/gemini-api/docs/pricing — $1.50 in / $7.50 out per 1M.
    entry = _pricing()[FLASH_3_6]
    assert entry["input_price_per_mtok"] == 1.50
    assert entry["output_price_per_mtok"] == 7.50


def test_gemini_3_5_flash_lite_priced():
    # $0.30 in / $2.50 out per 1M.
    entry = _pricing()[FLASH_LITE_3_5]
    assert entry["input_price_per_mtok"] == 0.30
    assert entry["output_price_per_mtok"] == 2.50


def test_every_text_model_is_priced():
    assert set(TEXT_MODELS) <= set(_pricing())


# --- Image model -------------------------------------------------------------


def test_nano_banana_2_lite_offered():
    assert NANO_BANANA_2_LITE in IMAGE_MODELS


def test_lite_image_model_clamps_to_1k():
    # Nano Banana 2 Lite emits 1K only; 2K/4K are rejected by the API.
    assert _resolve_image_size(NANO_BANANA_2_LITE, "2K") == "1K"
    assert _resolve_image_size(NANO_BANANA_2_LITE, "4K") == "1K"
    assert _resolve_image_size(NANO_BANANA_2_LITE, "1K") == "1K"


def test_fixed_resolution_model_sends_no_image_size():
    # gemini-2.5-flash-image is fixed at 1024px and takes no image_size.
    assert _resolve_image_size("gemini-2.5-flash-image", "2K") is None
    assert _resolve_image_size("gemini-2.5-flash-image", "default") is None


def test_multi_resolution_models_pass_through():
    for model in ("gemini-3.1-flash-image", "gemini-3-pro-image"):
        assert _resolve_image_size(model, "4K") == "4K"
        assert _resolve_image_size(model, "2K") == "2K"


def test_default_never_sends_image_size():
    for model in IMAGE_MODELS:
        assert _resolve_image_size(model, "default") is None


def test_client_and_node_image_lists_agree():
    assert IMAGE_MODELS == GeminiClient.IMAGE_MODELS
