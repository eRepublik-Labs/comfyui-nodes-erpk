# ABOUTME: Tests the MiniMax H3 text-to-video, image-to-video and reference-to-video nodes.
# ABOUTME: MiniMax H3 takes a real API seed, unlike Seedance 2.5's cache-control-only seed.

"""
MiniMax H3 is the first MiniMax family in this package. Three endpoints, no tier
variants, so three nodes with no dispatch layer.

The distinction these tests pin down hardest is the seed. Seedance 2.5 documents
no seed, so its nodes keep the value out of the payload. MiniMax H3 documents one
and honours it, so here the seed must reach the API. Getting that backwards
either silently ignores reproducibility or re-bills a run that could have been
reused.

Reference-to-video accepts more references than any other node here: 9 images
against the 4 the Seedance helpers cap at.
"""

import inspect
import pytest

IO = pytest.importorskip("comfy_api.latest").IO

from wavespeed.minimax_h3_text_to_video import MinimaxH3TextToVideoNode
from wavespeed.minimax_h3_image_to_video import MinimaxH3ImageToVideoNode
from wavespeed.minimax_h3_reference_to_video import MinimaxH3ReferenceToVideoNode

from wavespeed.wavespeed_api.requests.minimax_h3_text_to_video import MinimaxH3TextToVideo
from wavespeed.wavespeed_api.requests.minimax_h3_image_to_video import MinimaxH3ImageToVideo
from wavespeed.wavespeed_api.requests.minimax_h3_reference_to_video import MinimaxH3ReferenceToVideo


ALL_NODES = [
    MinimaxH3TextToVideoNode,
    MinimaxH3ImageToVideoNode,
    MinimaxH3ReferenceToVideoNode,
]

BASE = "/api/v3/wavespeed-ai/minimax-h3"


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


@pytest.mark.parametrize("request_cls,path,extra", [
    (MinimaxH3TextToVideo, f"{BASE}/text-to-video", {}),
    (MinimaxH3ImageToVideo, f"{BASE}/image-to-video", {"image": "https://example.com/a.png"}),
    (MinimaxH3ReferenceToVideo, f"{BASE}/reference-to-video", {"reference_images": ["https://example.com/a.png"]}),
])
def test_request_routes_to_documented_endpoint(request_cls, path, extra):
    assert request_cls(prompt="x", **extra).get_api_path() == path


# --- The seed IS sent, unlike Seedance 2.5 -----------------------------------


@pytest.mark.parametrize("request_cls,extra", [
    (MinimaxH3TextToVideo, {}),
    (MinimaxH3ImageToVideo, {"image": "https://example.com/a.png"}),
    (MinimaxH3ReferenceToVideo, {"reference_images": ["https://example.com/a.png"]}),
])
def test_seed_reaches_the_api(request_cls, extra):
    payload = request_cls(prompt="x", seed=1234, **extra).build_payload()
    assert payload["seed"] == 1234


@pytest.mark.parametrize("node", ALL_NODES)
def test_fingerprint_is_seed_gated(node):
    import math
    assert math.isnan(node.fingerprint_inputs(seed=-1))
    assert node.fingerprint_inputs(seed=9) == 9


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


@pytest.mark.parametrize("node", ALL_NODES)
def test_duration_spans_3_to_15(node):
    d = _input(node, "duration")
    assert (d.min, d.max) == (3, 15)


@pytest.mark.parametrize("node", ALL_NODES)
def test_resolution_tops_out_at_768p(node):
    # MiniMax H3 offers no 1080p or 4k.
    assert list(_input(node, "resolution").options) == ["480p", "768p"]


@pytest.mark.parametrize("node", ALL_NODES)
def test_no_generate_audio_toggle(node):
    # Audio is produced in a single pass and steered by an Audio: line in the
    # prompt, so a boolean here would be a lie.
    assert not _has_input(node, "generate_audio")


def test_image_to_video_has_no_aspect_ratio():
    # The output canvas follows the first-frame image.
    assert not _has_input(MinimaxH3ImageToVideoNode, "aspect_ratio")


@pytest.mark.parametrize("node", [MinimaxH3TextToVideoNode, MinimaxH3ReferenceToVideoNode])
def test_aspect_ratio_offers_all_seven(node):
    assert list(_input(node, "aspect_ratio").options) == [
        "16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "9:21",
    ]


def test_image_to_video_accepts_tensor_or_url():
    for name in ("first_frame", "first_frame_url", "last_frame", "last_frame_url"):
        assert _has_input(MinimaxH3ImageToVideoNode, name)


# --- Reference-to-video caps -------------------------------------------------


def test_reference_images_cap_at_nine():
    urls = [f"https://example.com/{i}.png" for i in range(12)]
    assert len(MinimaxH3ReferenceToVideoNode._normalize_url_list(urls, 9)) == 9


def test_reference_videos_and_audios_cap_at_three():
    urls = [f"https://example.com/{i}.mp4" for i in range(6)]
    assert len(MinimaxH3ReferenceToVideoNode._normalize_url_list(urls, 3)) == 3


def test_reference_to_video_exposes_all_three_reference_kinds():
    for name in ("reference_images", "reference_videos", "reference_audios"):
        assert _has_input(MinimaxH3ReferenceToVideoNode, name)


# --- Registration ------------------------------------------------------------


@pytest.mark.parametrize("node", ALL_NODES)
def test_node_is_registered(node):
    from wavespeed import NODES
    assert node in NODES
