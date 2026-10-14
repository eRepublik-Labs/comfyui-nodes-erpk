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
from gemini.nodes import (
    IMAGE_MODELS,
    TEXT_MODELS,
    _google_search_supported,
    _resolve_aspect_ratio,
    _resolve_image_size,
)


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


def test_multi_resolution_models_pass_through():
    for model in ("gemini-3.1-flash-image", "gemini-3-pro-image"):
        assert _resolve_image_size(model, "4K") == "4K"
        assert _resolve_image_size(model, "2K") == "2K"


def test_default_never_sends_image_size():
    for model in IMAGE_MODELS:
        assert _resolve_image_size(model, "default") is None


def test_client_and_node_image_lists_agree():
    assert IMAGE_MODELS == GeminiClient.IMAGE_MODELS


# --- Per-model image options (ai.google.dev/gemini-api/docs/image-generation
# and the per-model pages, read 2026-10-01) -----------------------------------


def test_half_k_only_on_3_1_flash_image():
    # The widget says 0.5K like the docs, but the API rejects that string:
    # 400 "Unsupported image_size '0.5K'. Supported values are: 1K, 2K, 4K,
    # 512, 512P, 512PX." (gemini-3.1-flash-image, probed 2026-10-01).
    assert _resolve_image_size("gemini-3.1-flash-image", "0.5K") == "512"
    # 3 Pro Image documents 1K/2K/4K; 0.5K is raised to its smallest size.
    assert _resolve_image_size("gemini-3-pro-image", "0.5K") == "1K"
    assert _resolve_image_size(NANO_BANANA_2_LITE, "0.5K") == "1K"


def test_google_search_not_sent_to_lite_image():
    # Lite page capability table: "Search grounding: Not supported".
    assert _google_search_supported(NANO_BANANA_2_LITE) is False
    assert _google_search_supported("gemini-3.1-flash-image") is True
    assert _google_search_supported("gemini-3-pro-image") is True


def test_lite_image_clamps_extreme_ratios_to_nearest():
    # The lite page lists 1:1 3:2 2:3 3:4 4:3 4:5 5:4 9:16 16:9 21:9; the
    # 1:4/4:1/1:8/8:1 ratios are 3.1 Flash Image additions.
    assert _resolve_aspect_ratio(NANO_BANANA_2_LITE, "1:4") == "9:16"
    assert _resolve_aspect_ratio(NANO_BANANA_2_LITE, "1:8") == "9:16"
    assert _resolve_aspect_ratio(NANO_BANANA_2_LITE, "4:1") == "21:9"
    assert _resolve_aspect_ratio(NANO_BANANA_2_LITE, "8:1") == "21:9"
    assert _resolve_aspect_ratio(NANO_BANANA_2_LITE, "4:5") == "4:5"


def test_3_1_flash_image_keeps_extreme_ratios():
    for ratio in ("1:4", "4:1", "1:8", "8:1"):
        assert _resolve_aspect_ratio("gemini-3.1-flash-image", ratio) == ratio


def test_default_ratio_sends_nothing():
    for model in IMAGE_MODELS:
        assert _resolve_aspect_ratio(model, "default") is None


# --- Gemini 4 Argon (ai.google.dev/gemini-api/docs/latest-model and
# /docs/models/gemini-4-argon, read 2026-10-14) -------------------------------

ARGON = "gemini-4-argon"


def test_argon_offered_on_text_nodes():
    assert ARGON in TEXT_MODELS


def test_argon_clamps_minimal_thinking_to_low():
    # 400 "Thinking level MINIMAL is not supported for this model" (probed
    # 2026-10-14); the thinking page lists low/medium/high only.
    from gemini.nodes import _build_thinking_config
    assert _build_thinking_config("minimal", ARGON).thinking_level == "LOW"
    for level in ("low", "medium", "high"):
        assert _build_thinking_config(level, ARGON).thinking_level == level.upper()


def test_argon_priced_at_intro_rate():
    # Pricing page: "$2.00 / $10.00 per 1M tokens through November 30, 2026;
    # $4.00 / $20.00 from December 1". Cost estimates use today's rate.
    entry = _pricing()[ARGON]
    assert entry["input_price_per_mtok"] == 2.0
    assert entry["output_price_per_mtok"] == 10.0
    assert "2026-12-01" in entry["name"] and "4.00/20.00" in entry["name"]


# Argon's latest-model page: "set HTTP client timeouts to at least 15 minutes".
FIFTEEN_MINUTES_MS = 15 * 60 * 1000
FIVE_MINUTES_MS = 5 * 60 * 1000


def test_argon_gets_a_fifteen_minute_timeout():
    from gemini.gemini_api.cooperative_call import resolve_timeout_ms
    assert resolve_timeout_ms(ARGON) == FIFTEEN_MINUTES_MS


def test_other_models_keep_the_five_minute_default():
    from gemini.gemini_api.cooperative_call import resolve_timeout_ms
    assert resolve_timeout_ms(FLASH_3_8) == FIVE_MINUTES_MS
    assert resolve_timeout_ms() == FIVE_MINUTES_MS


def test_a_longer_configured_timeout_is_not_lowered_for_argon(monkeypatch):
    import erpk.settings as erpk_settings
    from erpk.gemini.gemini_api.cooperative_call import resolve_timeout_ms
    monkeypatch.setattr(erpk_settings, "get_comfy_setting", lambda *a, **k: 1_200_000)
    assert resolve_timeout_ms(ARGON) == 1_200_000
    monkeypatch.setattr(erpk_settings, "get_comfy_setting", lambda *a, **k: 60_000)
    assert resolve_timeout_ms(ARGON) == FIFTEEN_MINUTES_MS
    assert resolve_timeout_ms(FLASH_3_8) == 60_000


class _RecordingModels:
    """Stands in for client.models: records the request generate_content gets."""

    def __init__(self):
        self.config = None

    def generate_content(self, model, contents, config):
        self.config = config
        from types import SimpleNamespace
        return SimpleNamespace(text="OK", candidates=[], usage_metadata=None)


def _client_recording_requests():
    from types import SimpleNamespace
    client = GeminiClient.__new__(GeminiClient)
    client.model_name = FLASH_3_8
    client.system_instruction = None
    client.safety_settings = None
    client.client = SimpleNamespace(models=_RecordingModels())
    return client


def test_argon_request_carries_the_long_http_timeout():
    # The genai.Client timeout is fixed at construction; the per-request
    # http_options is what lets one Argon call outlive it.
    client = _client_recording_requests()
    client._generate_content_sync("Say OK.", model=ARGON)
    assert client.client.models.config.http_options.timeout == FIFTEEN_MINUTES_MS
    client._generate_content_sync("Say OK.", model=FLASH_3_8)
    assert client.client.models.config.http_options.timeout == FIVE_MINUTES_MS


def test_argon_chat_turn_carries_the_long_http_timeout():
    import asyncio
    from types import SimpleNamespace
    from gemini.nodes import GeminiChat

    sent = {}

    class _Session:
        def send_message(self, message, config):
            sent["config"] = config
            return SimpleNamespace(text="OK")

    asyncio.run(GeminiChat.execute(prompt="Say OK.", client=object(), model=ARGON,
                                   chat_session=_Session()))
    assert sent["config"].http_options.timeout == FIFTEEN_MINUTES_MS


def _text_input(node_cls, name):
    return [i for i in node_cls.define_schema().inputs if i.id == name][0]


def test_argon_guidance_is_in_the_text_node_tooltips():
    # Google: raise max_output_tokens to at least 32,768; temperature, top_p
    # and top_k "are ignored" by Argon.
    from gemini.nodes import GeminiChat, GeminiTextGeneration, GeminiVision
    for node_cls in (GeminiTextGeneration, GeminiChat, GeminiVision):
        assert "32768" in _text_input(node_cls, "max_tokens").tooltip
        assert _text_input(node_cls, "max_tokens").max >= 65536
        for name in ("temperature", "top_p", "top_k"):
            assert "ignored by gemini 4 argon" in _text_input(node_cls, name).tooltip.lower(), name
        assert "4 Argon" in _text_input(node_cls, "thinking_level").tooltip


# --- Nano Banana 2.1 (ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1
# and /docs/image-generation, read 2026-10-14) --------------------------------

NANO_BANANA_2_1 = "gemini-nano-banana-2.1"


def test_nano_banana_2_1_offered():
    assert NANO_BANANA_2_1 in IMAGE_MODELS


def test_nano_banana_2_1_has_no_half_k_tier():
    # "512" -> 400 "Image size 512 is not supported for this model" (probed
    # 2026-10-14); the model page lists 1K, 2K and 4K.
    assert _resolve_image_size(NANO_BANANA_2_1, "0.5K") == "1K"
    for size in ("1K", "2K", "4K"):
        assert _resolve_image_size(NANO_BANANA_2_1, size) == size


def test_nano_banana_2_1_takes_all_fourteen_ratios():
    # Image-generation page lists all 14; 1:1, 8:1, 21:9 and 1:4 probed 200.
    for ratio in ("1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3",
                  "4:5", "5:4", "8:1", "9:16", "16:9", "21:9"):
        assert _resolve_aspect_ratio(NANO_BANANA_2_1, ratio) == ratio


def test_nano_banana_2_1_supports_google_search():
    # Model page: web and image search supported; probed 200 with google_search.
    assert _google_search_supported(NANO_BANANA_2_1) is True



def test_3_pro_image_clamps_extreme_ratios_to_nearest():
    # 400 "Aspect ratio 1:8 is not supported for this model" (probed
    # 2026-10-14). The image-generation page's Pro Image table lists ten:
    # 1:1 2:3 3:2 3:4 4:3 4:5 5:4 9:16 16:9 21:9.
    assert _resolve_aspect_ratio("gemini-3-pro-image", "1:4") == "9:16"
    assert _resolve_aspect_ratio("gemini-3-pro-image", "1:8") == "9:16"
    assert _resolve_aspect_ratio("gemini-3-pro-image", "4:1") == "21:9"
    assert _resolve_aspect_ratio("gemini-3-pro-image", "8:1") == "21:9"
    for ratio in ("1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"):
        assert _resolve_aspect_ratio("gemini-3-pro-image", ratio) == ratio


def test_aspect_ratio_tooltips_name_both_ten_ratio_models():
    from gemini.nodes import GeminiImageEdit, GeminiImageGeneration
    for node_cls in (GeminiImageGeneration, GeminiImageEdit):
        tooltip = [i for i in node_cls.define_schema().inputs if i.id == "aspect_ratio"][0].tooltip
        assert "3.1 Flash Lite and 3 Pro have no 1:4, 4:1, 1:8 or 8:1" in tooltip


def test_image_temperature_tooltip_states_the_1_0_ceiling():
    # models.get reports max_temperature 1.0 for the image models, yet 1.5 is
    # accepted with a 200 (probed 2026-10-14), so the widget's 1.0-2.0 range is
    # a silent no-op the tooltip must name.
    from gemini.nodes import GeminiImageEdit, GeminiImageGeneration
    for node_cls in (GeminiImageGeneration, GeminiImageEdit):
        temp = [i for i in node_cls.define_schema().inputs if i.id == "temperature"][0]
        assert temp.max == 2.0
        assert "maximum temperature of 1.0" in temp.tooltip
