# ABOUTME: Tests the MiniMax H3 nodes: three official-edition video nodes plus the open-weights image and chaining nodes.
# ABOUTME: The official edition takes no API seed; the open-weights endpoints do.

"""
WaveSpeed hosts two MiniMax H3 editions. The three video generators
(text/image/reference-to-video) call MiniMax's own `minimax/h3` endpoints:
768p or 2k, 4-15s, six aspect ratios, and NO seed parameter, so their seed is
cache-control only and never sent, the Seedance 2.5 convention. The image,
video-edit, video-extend and LoRA-stack nodes call the open-weights
`wavespeed-ai/minimax-h3` endpoints, which document a seed and, for the image
endpoints, a `-lora` twin that adds one optional `loras` array.

The seed plumbing is the fact these tests pin hardest, because the two editions
are opposite: sending a seed the official API does not document is a silent
no-op at best; dropping the open-weights seed throws away reproducibility.

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
from wavespeed.minimax_h3_lora_stack import MinimaxH3LoraStackNode
from wavespeed.minimax_h3_text_to_image import MinimaxH3TextToImageNode
from wavespeed.minimax_h3_image_edit import MinimaxH3ImageEditNode
from wavespeed.minimax_h3_video_edit import MinimaxH3VideoEditNode
from wavespeed.minimax_h3_video_extend import MinimaxH3VideoExtendNode
from wavespeed.wavespeed_api.requests.minimax_h3_text_to_image import MinimaxH3TextToImage
from wavespeed.wavespeed_api.requests.minimax_h3_image_edit import MinimaxH3ImageEdit
from wavespeed.wavespeed_api.requests.minimax_h3_video_edit import MinimaxH3VideoEdit
from wavespeed.wavespeed_api.requests.minimax_h3_video_extend import MinimaxH3VideoExtend


ALL_NODES = [
    MinimaxH3TextToVideoNode,
    MinimaxH3ImageToVideoNode,
    MinimaxH3ReferenceToVideoNode,
]

BASE = "/api/v3/wavespeed-ai/minimax-h3"
OFFICIAL = "/api/v3/minimax/h3"


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
    (MinimaxH3TextToVideo, f"{OFFICIAL}/text-to-video", {}),
    (MinimaxH3ImageToVideo, f"{OFFICIAL}/image-to-video", {"image": "https://example.com/a.png"}),
    (MinimaxH3ReferenceToVideo, f"{OFFICIAL}/reference-to-video", {"reference_images": ["https://example.com/a.png"]}),
])
def test_request_routes_to_documented_endpoint(request_cls, path, extra):
    assert request_cls(prompt="x", **extra).get_api_path() == path


# --- The official edition takes no seed ---------------------------------------


@pytest.mark.parametrize("request_cls,extra", [
    (MinimaxH3TextToVideo, {}),
    (MinimaxH3ImageToVideo, {"image": "https://example.com/a.png"}),
    (MinimaxH3ReferenceToVideo, {"reference_images": ["https://example.com/a.png"]}),
])
def test_official_requests_have_no_seed_field(request_cls, extra):
    assert "seed" not in request_cls.model_fields
    assert "loras" not in request_cls.model_fields
    assert "seed" not in request_cls(prompt="x", **extra).build_payload()


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
def test_duration_spans_4_to_15(node):
    # minimax/h3 model pages: "Supported values: 4 ... 15".
    d = _input(node, "duration")
    assert (d.min, d.max) == (4, 15)


@pytest.mark.parametrize("node", ALL_NODES)
def test_resolution_offers_768p_and_2k(node):
    # minimax/h3 model pages: "Supported values: 768p or 2k".
    assert list(_input(node, "resolution").options) == ["768p", "2k"]


@pytest.mark.parametrize("node", ALL_NODES)
def test_video_nodes_keep_a_cache_only_seed_and_no_lora_socket(node):
    # Same widget positions as before the edition switch; trailing loras/model
    # widgets removed, which is migration-safe.
    ids = [s.id for s in _schema(node).inputs]
    assert "seed" in ids and "loras" not in ids and "model" not in ids
    assert ids[-1] == "seed"


@pytest.mark.parametrize("node", ALL_NODES)
def test_no_generate_audio_toggle(node):
    # Audio is produced in a single pass and steered by an Audio: line in the
    # prompt, so a boolean here would be a lie.
    assert not _has_input(node, "generate_audio")


def test_image_to_video_has_no_aspect_ratio():
    # The output canvas follows the first-frame image.
    assert not _has_input(MinimaxH3ImageToVideoNode, "aspect_ratio")


@pytest.mark.parametrize("node", [MinimaxH3TextToVideoNode, MinimaxH3ReferenceToVideoNode])
def test_aspect_ratio_offers_the_official_six(node):
    # 9:21 exists only on the open-weights edition; kept out so the API never
    # sees a value it does not document.
    assert list(_input(node, "aspect_ratio").options) == [
        "16:9", "9:16", "1:1", "4:3", "3:4", "21:9",
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


# --- LoRA twins ---------------------------------------------------------------

LORAS = [{"path": "https://example.com/a.safetensors", "scale": 0.8}]


def test_lora_stack_builds_the_documented_shape():
    loras = MinimaxH3LoraStackNode._build_loras(
        "https://example.com/a.safetensors", 0.8, "", 1.0, " https://example.com/c.safetensors ", 1.2)
    assert loras == [
        {"path": "https://example.com/a.safetensors", "scale": 0.8},
        {"path": "https://example.com/c.safetensors", "scale": 1.2},
    ]


def test_lora_stack_requires_at_least_one_path():
    with pytest.raises(ValueError):
        MinimaxH3LoraStackNode._build_loras("", 1.0, "", 1.0, "", 1.0)


def test_lora_stack_feeds_the_image_nodes():
    # The official video edition has no -lora twin; only the open-weights image
    # endpoints do, so only those nodes expose the socket.
    assert _schema(MinimaxH3TextToImageNode).inputs[-1].io_type == "MINIMAX_H3_LORAS"
    assert _schema(MinimaxH3ImageEditNode).inputs[-1].io_type == "MINIMAX_H3_LORAS"


def test_lora_stack_is_a_config_node():
    # No seed, so no fingerprint_inputs: an always-NaN fingerprint here would
    # cascade re-billing into every video node downstream.
    assert "fingerprint_inputs" not in MinimaxH3LoraStackNode.__dict__
    assert not _has_input(MinimaxH3LoraStackNode, "seed")
    assert [o.io_type for o in _schema(MinimaxH3LoraStackNode).outputs] == ["MINIMAX_H3_LORAS"]




# --- Image and video-chaining nodes ------------------------------------------

IMAGE_NODES = [MinimaxH3TextToImageNode, MinimaxH3ImageEditNode]
CHAIN_NODES = [MinimaxH3VideoEditNode, MinimaxH3VideoExtendNode]
NEW_API_NODES = IMAGE_NODES + CHAIN_NODES


@pytest.mark.parametrize("request_cls,path,extra", [
    (MinimaxH3TextToImage, f"{BASE}/text-to-image", {}),
    (MinimaxH3ImageEdit, f"{BASE}/image-edit", {"images": ["https://example.com/a.png"]}),
    (MinimaxH3VideoEdit, f"{BASE}/video-edit", {"video": "https://example.com/a.mp4"}),
    (MinimaxH3VideoExtend, f"{BASE}/video-extend", {"video": "https://example.com/a.mp4"}),
])
def test_new_requests_route_to_documented_endpoint(request_cls, path, extra):
    req = request_cls(prompt="x", seed=7, **extra)
    assert req.get_api_path() == path
    assert req.build_payload()["seed"] == 7


@pytest.mark.parametrize("request_cls,extra", [
    (MinimaxH3TextToImage, {}),
    (MinimaxH3ImageEdit, {"images": ["https://example.com/a.png"]}),
])
def test_image_requests_have_lora_twins(request_cls, extra):
    plain = request_cls(prompt="x", **extra)
    assert request_cls(prompt="x", loras=LORAS, **extra).get_api_path() == plain.get_api_path() + "-lora"


@pytest.mark.parametrize("request_cls", [MinimaxH3VideoEdit, MinimaxH3VideoExtend])
def test_chain_requests_have_no_lora_twin(request_cls):
    assert "loras" not in request_cls.model_fields


@pytest.mark.parametrize("node", NEW_API_NODES)
def test_new_nodes_follow_the_seed_contract(node):
    import math
    assert _schema(node).not_idempotent is True
    assert math.isnan(node.fingerprint_inputs(seed=-1))
    assert node.fingerprint_inputs(seed=3) == 3
    assert inspect.iscoroutinefunction(node.execute.__func__)


@pytest.mark.parametrize("node", IMAGE_NODES)
def test_image_nodes_output_an_image(node):
    assert [o.io_type for o in _schema(node).outputs] == ["IMAGE"]
    assert list(_input(node, "resolution").options) == ["1k", "2k"]
    assert _schema(node).inputs[-1].id == "loras"


def test_text_to_image_offers_all_fifteen_ratios():
    assert len(_input(MinimaxH3TextToImageNode, "aspect_ratio").options) == 15


def test_image_edit_follows_the_first_reference_by_default():
    # aspect_ratio is optional on the endpoint; "auto" means omit the field.
    for node in (MinimaxH3ImageEditNode, MinimaxH3VideoEditNode):
        spec = _input(node, "aspect_ratio")
        assert spec.options[0] == "auto" and spec.default == "auto"
    assert MinimaxH3ImageEdit(prompt="x", images=["u"], aspect_ratio=None).build_payload().get("aspect_ratio") is None


@pytest.mark.parametrize("node", CHAIN_NODES)
def test_chain_nodes_take_a_video_url_and_return_one(node):
    assert _has_input(node, "video_url")
    assert [o.id for o in _schema(node).outputs] == ["video_url"]
    assert list(_input(node, "resolution").options) == ["480p", "540p", "768p", "1080p"]


def test_video_edit_duration_zero_follows_the_input():
    # The endpoint has no default: unset means the output matches the input.
    assert MinimaxH3VideoEditNode._duration_or_none(0) is None
    assert MinimaxH3VideoEditNode._duration_or_none(2) is None
    assert MinimaxH3VideoEditNode._duration_or_none(3) == 3
    assert MinimaxH3VideoEditNode._duration_or_none(8) == 8
    assert "duration" not in MinimaxH3VideoEdit(prompt="x", video="u").build_payload()


def test_video_edit_can_keep_the_source_audio():
    assert MinimaxH3VideoEdit(prompt="x", video="u", generate_audio=False).build_payload()["generate_audio"] is False


def test_video_extend_accepts_a_target_last_frame():
    for name in ("last_frame", "last_frame_url"):
        assert _has_input(MinimaxH3VideoExtendNode, name)
