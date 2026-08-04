# ABOUTME: Tests the Gemini Omni Flash video node's request shape and cache-control seed.
# ABOUTME: Omni Flash rejects temperature/system instructions and takes no API seed.

"""
Gemini Omni Flash is the first model in this package reached through the
Interactions API (client.interactions.create) rather than generate_content or
generate_videos, and it rejects most of the knobs the other Gemini nodes send:
system instructions, temperature, top_p, stop sequences and negative prompts
are all unsupported.

It also accepts no seed. Per the repo's caching invariant, a node that must be
able to re-run on demand needs a seed to gate fingerprint_inputs, so the node
carries a cache-control-only seed that is deliberately never sent to the API.
"""

import pytest

from gemini.omni_nodes import (
    OMNI_MODEL,
    GeminiOmniVideoGeneration,
    _build_omni_video_request,
)


def _config(**kwargs):
    kwargs.setdefault("aspect_ratio", "16:9")
    kwargs.setdefault("has_image", False)
    return _build_omni_video_request(**kwargs)


def test_model_id_is_the_preview_string():
    # The models overview shows "gemini-omni-flash"; the model reference page and
    # the API guide both give the -preview suffix, which is what the API accepts.
    assert OMNI_MODEL == "gemini-omni-flash-preview"


def test_text_only_request_uses_text_to_video_task():
    cfg = _config()
    assert cfg["generation_config"]["video_config"]["task"] == "text_to_video"


def test_image_input_switches_to_image_to_video_task():
    cfg = _config(has_image=True)
    assert cfg["generation_config"]["video_config"]["task"] == "image_to_video"


def test_aspect_ratio_is_passed_through():
    assert _config(aspect_ratio="9:16")["response_format"]["aspect_ratio"] == "9:16"


def test_response_format_requests_video():
    assert _config()["response_format"]["type"] == "video"


def test_synchronous_fast_path_is_requested():
    # The docs recommend background/store/stream all false for unary generation.
    cfg = _config()
    assert cfg["background"] is False
    assert cfg["store"] is False
    assert cfg["stream"] is False


@pytest.mark.parametrize("unsupported", ["temperature", "top_p", "system_instruction", "stop_sequences", "negative_prompt"])
def test_unsupported_parameters_are_never_sent(unsupported):
    assert unsupported not in _config()


# --- Node schema and caching ------------------------------------------------


def _schema():
    return GeminiOmniVideoGeneration.define_schema()


def _input(name):
    for spec in _schema().inputs:
        if getattr(spec, "id", None) == name:
            return spec
    raise AssertionError(f"no input named {name}")


def test_node_outputs_a_video_path():
    assert [o.id for o in _schema().outputs] == ["video_path"]


def test_aspect_ratio_offers_only_supported_values():
    assert list(_input("aspect_ratio").options) == ["16:9", "9:16"]


def test_node_has_a_seed_for_cache_control():
    assert _input("seed") is not None


def test_fingerprint_is_seed_gated():
    # A fixed seed reuses the paid result; -1 (randomize) re-runs every queue.
    import math
    assert math.isnan(GeminiOmniVideoGeneration.fingerprint_inputs(seed=-1))
    assert GeminiOmniVideoGeneration.fingerprint_inputs(seed=7) == 7


def test_node_exposes_async_execute():
    import inspect
    assert inspect.iscoroutinefunction(GeminiOmniVideoGeneration.execute.__func__)


def test_node_is_registered():
    from gemini import NODES
    assert GeminiOmniVideoGeneration in NODES
