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
FLASH_3_7 = "gemini-3.7-flash"
FLASH_3_8 = "gemini-3.8-flash"
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


def test_gemini_3_7_and_3_8_flash_offered():
    assert FLASH_3_7 in TEXT_MODELS
    assert FLASH_3_8 in TEXT_MODELS


def test_3_7_and_3_8_flash_clamp_minimal_thinking_to_low():
    # Both model pages: "minimal is not supported and returns an error."
    from gemini.nodes import _build_thinking_config
    for model in (FLASH_3_7, FLASH_3_8):
        assert _build_thinking_config("minimal", model).thinking_level == "LOW"
    assert _build_thinking_config("minimal", FLASH_3_6).thinking_level == "MINIMAL"


def test_gemini_3_6_through_3_8_flash_priced_at_current_rate():
    # https://ai.google.dev/gemini-api/docs/pricing (read 2026-09-16): 3.6, 3.7
    # and 3.8 Flash are "$0.75 [in] / $3.75 [out] through December 31, 2026.
    # $1.50 / $7.50 starting January 1, 2027." Cost estimates use today's rate.
    for model in (FLASH_3_6, FLASH_3_7, FLASH_3_8):
        entry = _pricing()[model]
        assert entry["input_price_per_mtok"] == 0.75, model
        assert entry["output_price_per_mtok"] == 3.75, model


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
