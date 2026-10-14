# ABOUTME: Tests the Gemini Omni reference-to-video node.
# ABOUTME: Covers request shape, input content order and cache control.

"""
Expected values come from the Omni Flash guide (ai.google.dev/gemini-api/docs/omni,
read 2026-10-14). The API's validation error for an unknown video_config.task lists
'upscale' too, but gemini-omni-1.1-flash rejects it for every input shape: 400
"The value 'upscale' is not supported for 'generation_config.video_config.task'"
(probed 2026-10-14 with text-only, inline-video and uploaded-video inputs), and
the guide lists only the other five tasks.
"""

import base64
import inspect
import io
import math

import pytest
from PIL import Image

from gemini.omni_nodes import (
    RESOLUTIONS,
    GeminiOmniReferenceToVideo,
    _build_omni_video_request,
    _image_parts,
    _text_part,
)


def _input(node_cls, name):
    for spec in node_cls.define_schema().inputs:
        if spec.id == name:
            return spec
    raise AssertionError(f"{node_cls.__name__} has no input named {name}")


# --- Content parts (guide's input arrays) ------------------------------------


def test_image_part_is_inline_png():
    part = _image_parts([Image.new("RGB", (4, 4), "red")])[0]
    assert part["type"] == "image"
    assert part["mime_type"] == "image/png"
    assert base64.b64decode(part["data"])[:8] == b"\x89PNG\r\n\x1a\n"


def test_one_image_part_per_reference_in_order():
    parts = _image_parts([Image.new("RGB", (4, 4), c) for c in ("red", "blue")])
    colours = [Image.open(io.BytesIO(base64.b64decode(p["data"]))).getpixel((0, 0)) for p in parts]
    assert colours == [(255, 0, 0), (0, 0, 255)]


def test_text_part():
    assert _text_part("Continue the scene.") == {"type": "text", "text": "Continue the scene."}


# --- Reference to video ------------------------------------------------------


def test_reference_request_uses_reference_task_and_aspect_ratio():
    request = _build_omni_video_request("reference_to_video", "720p", aspect_ratio="9:16")
    assert request["generation_config"]["video_config"]["task"] == "reference_to_video"
    assert request["response_format"]["aspect_ratio"] == "9:16"


def test_reference_images_input_is_required():
    assert not getattr(_input(GeminiOmniReferenceToVideo, "reference_images"), "optional", False)


def test_reference_node_offers_resolution_and_aspect_ratio():
    assert list(_input(GeminiOmniReferenceToVideo, "resolution").options) == RESOLUTIONS
    assert list(_input(GeminiOmniReferenceToVideo, "aspect_ratio").options) == ["16:9", "9:16"]


# --- Cache control and registration -------------------------------------------


@pytest.mark.parametrize("node_cls", [GeminiOmniReferenceToVideo])
def test_seed_is_cache_control_only_and_gated(node_cls):
    assert _input(node_cls, "seed").default == -1
    assert math.isnan(node_cls.fingerprint_inputs(seed=-1))
    assert node_cls.fingerprint_inputs(seed=7) == 7


@pytest.mark.parametrize("node_cls", [GeminiOmniReferenceToVideo])
def test_outputs_a_video_path(node_cls):
    assert [o.id for o in node_cls.define_schema().outputs] == ["video_path"]


@pytest.mark.parametrize("node_cls", [GeminiOmniReferenceToVideo])
def test_execute_is_async(node_cls):
    assert inspect.iscoroutinefunction(node_cls.execute.__func__)


@pytest.mark.parametrize("node_cls", [GeminiOmniReferenceToVideo])
def test_registered(node_cls):
    from gemini import NODES
    assert node_cls in NODES
