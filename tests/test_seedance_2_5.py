# ABOUTME: Tests the Seedance 2.5 text-to-video, image-to-video, video-edit and video-extend nodes.
# ABOUTME: Seedance 2.5 accepts no API seed, so its seed widget must stay out of the payload.

"""
Seedance 2.5 differs from the wrapped 2.0 family in ways the tests below pin down:

- Duration runs 4-30s rather than 4-15s, and 4k joins the resolution list.
- No endpoint documents a `seed` parameter. The nodes still carry a seed so a
  fixed value can reuse a paid result, but it must never reach the API.
- video-edit and video-extend take the source clip as a `video` URL string,
  which is exactly what every video node in this package already outputs, so
  they chain directly without a new ComfyUI type.
- video-edit has no duration: output length follows the input clip.

Endpoint paths are asserted verbatim against WaveSpeed's published API reference.
"""

import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO

from wavespeed.seedance_2_5_text_to_video import Seedance25TextToVideoNode
from wavespeed.seedance_2_5_image_to_video import Seedance25ImageToVideoNode
from wavespeed.seedance_2_5_video_edit import Seedance25VideoEditNode
from wavespeed.seedance_2_5_video_extend import Seedance25VideoExtendNode

from wavespeed.wavespeed_api.requests.seedance_2_5_text_to_video import Seedance25TextToVideo
from wavespeed.wavespeed_api.requests.seedance_2_5_text_to_video_turbo import Seedance25TextToVideoTurbo
from wavespeed.wavespeed_api.requests.seedance_2_5_image_to_video import Seedance25ImageToVideo
from wavespeed.wavespeed_api.requests.seedance_2_5_image_to_video_turbo import Seedance25ImageToVideoTurbo
from wavespeed.wavespeed_api.requests.seedance_2_5_image_to_video_spicy import Seedance25ImageToVideoSpicy
from wavespeed.wavespeed_api.requests.seedance_2_5_video_edit import Seedance25VideoEdit
from wavespeed.wavespeed_api.requests.seedance_2_5_video_edit_turbo import Seedance25VideoEditTurbo
from wavespeed.wavespeed_api.requests.seedance_2_5_video_extend import Seedance25VideoExtend


ALL_NODES = [
    Seedance25TextToVideoNode,
    Seedance25ImageToVideoNode,
    Seedance25VideoEditNode,
    Seedance25VideoExtendNode,
]

BASE = "/api/v3/bytedance/seedance-2.5"


def _schema(node):
    return node.define_schema()


def _input(node, name):
    for spec in _schema(node).inputs:
        if getattr(spec, "id", None) == name:
            return spec
    raise AssertionError(f"{node.__name__} has no input {name!r}")


def _has_input(node, name):
    return any(getattr(s, "id", None) == name for s in _schema(node).inputs)


# --- Endpoint routing --------------------------------------------------------


@pytest.mark.parametrize("request_cls,path", [
    (Seedance25TextToVideo, f"{BASE}/text-to-video"),
    (Seedance25TextToVideoTurbo, f"{BASE}/text-to-video-turbo"),
    (Seedance25ImageToVideo, f"{BASE}/image-to-video"),
    (Seedance25ImageToVideoTurbo, f"{BASE}/image-to-video-turbo"),
    (Seedance25ImageToVideoSpicy, f"{BASE}/image-to-video-spicy"),
    (Seedance25VideoEdit, f"{BASE}/video-edit"),
    (Seedance25VideoEditTurbo, f"{BASE}/video-edit-turbo"),
    (Seedance25VideoExtend, f"{BASE}/video-extend"),
])
def test_request_routes_to_documented_endpoint(request_cls, path):
    assert request_cls(prompt="x", **_min_kwargs(request_cls)).get_api_path() == path


def _min_kwargs(request_cls):
    """Required fields beyond prompt, per endpoint."""
    name = request_cls.__name__
    if "ImageToVideo" in name:
        return {"image": "https://example.com/a.png"}
    if "VideoEdit" in name or "VideoExtend" in name:
        return {"video": "https://example.com/a.mp4"}
    return {}


def test_tier_variants_only_override_the_endpoint():
    # A turbo variant must inherit the base payload untouched.
    base = Seedance25TextToVideo(prompt="x", duration=7, resolution="4k")
    turbo = Seedance25TextToVideoTurbo(prompt="x", duration=7, resolution="4k")
    assert base.build_payload() == turbo.build_payload()
    assert base.get_api_path() != turbo.get_api_path()


# --- The seed must never reach the API ---------------------------------------


@pytest.mark.parametrize("request_cls", [
    Seedance25TextToVideo, Seedance25TextToVideoTurbo,
    Seedance25ImageToVideo, Seedance25ImageToVideoTurbo, Seedance25ImageToVideoSpicy,
    Seedance25VideoEdit, Seedance25VideoEditTurbo, Seedance25VideoExtend,
])
def test_no_seed_in_payload(request_cls):
    # Seedance 2.5 documents no seed parameter on any endpoint.
    payload = request_cls(prompt="x", **_min_kwargs(request_cls)).build_payload()
    assert "seed" not in payload


@pytest.mark.parametrize("node", ALL_NODES)
def test_node_carries_a_cache_control_seed(node):
    seed = _input(node, "seed")
    assert seed.control_after_generate is not None


@pytest.mark.parametrize("node", ALL_NODES)
def test_fingerprint_is_seed_gated(node):
    import math
    assert math.isnan(node.fingerprint_inputs(seed=-1))
    assert node.fingerprint_inputs(seed=11) == 11


@pytest.mark.parametrize("node", ALL_NODES)
def test_nodes_are_not_idempotent(node):
    assert _schema(node).not_idempotent is True


@pytest.mark.parametrize("node", ALL_NODES)
def test_nodes_output_a_video_url(node):
    assert [o.id for o in _schema(node).outputs] == ["video_url"]


@pytest.mark.parametrize("node", ALL_NODES)
def test_execute_is_async(node):
    assert inspect.iscoroutinefunction(node.execute.__func__)


# --- Parameter surface -------------------------------------------------------


@pytest.mark.parametrize("node", [
    Seedance25TextToVideoNode, Seedance25ImageToVideoNode, Seedance25VideoExtendNode,
])
def test_duration_spans_4_to_30(node):
    d = _input(node, "duration")
    assert (d.min, d.max) == (4, 30)


def test_video_edit_has_no_duration():
    # Output length follows the input clip; the endpoint takes no duration.
    assert not _has_input(Seedance25VideoEditNode, "duration")


@pytest.mark.parametrize("node", ALL_NODES)
def test_resolution_offers_4k(node):
    assert list(_input(node, "resolution").options) == ["480p", "720p", "1080p", "4k"]


@pytest.mark.parametrize("node", ALL_NODES)
def test_generate_audio_defaults_on(node):
    assert _input(node, "generate_audio").default is True


def test_only_text_to_video_takes_aspect_ratio():
    # Image and video inputs carry their own aspect ratio.
    assert _has_input(Seedance25TextToVideoNode, "aspect_ratio")
    for node in (Seedance25ImageToVideoNode, Seedance25VideoEditNode, Seedance25VideoExtendNode):
        assert not _has_input(node, "aspect_ratio")


def test_video_nodes_take_a_video_url_string():
    # Chains directly from any video node's video_url output.
    for node in (Seedance25VideoEditNode, Seedance25VideoExtendNode):
        assert _has_input(node, "video_url")


def test_image_to_video_accepts_tensor_or_url():
    assert _has_input(Seedance25ImageToVideoNode, "start_frame")
    assert _has_input(Seedance25ImageToVideoNode, "start_frame_url")
    assert _has_input(Seedance25ImageToVideoNode, "last_frame")


# --- Registration ------------------------------------------------------------


@pytest.mark.parametrize("node", ALL_NODES)
def test_node_is_registered(node):
    from wavespeed import NODES
    assert node in NODES
