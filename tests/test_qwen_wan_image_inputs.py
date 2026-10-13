# ABOUTME: Tests the IMAGE sockets on the Qwen edit nodes and WAN 2.7 image-to-video.
# ABOUTME: A connected IMAGE goes inline as a base64 data URI; otherwise the URL text is sent.

import asyncio
import importlib
from unittest.mock import patch

import pytest

torch = pytest.importorskip("torch")

from wavespeed.wavespeed_api.utils import input_image_list

DATA_URI = "data:image/jpeg;base64,"

# (module, class, max images)
MULTI_NODES = [
    ("qwen_image_multiple_angles", "QwenImageMultipleAnglesNode", 3),
    ("qwen_image_edit_plus", "QwenImageEditPlusNode", 3),
    ("qwen_image_edit_plus_lora", "QwenImageEditPlusLoraNode", 3),
    ("qwen_image_max_edit", "QwenImageMaxEditNode", 6),
    ("qwen_image_2_0_edit", "QwenImage20EditNode", 3),
]
SINGLE_NODES = [
    ("qwen_image_edit", "QwenImageEditNode"),
    ("qwen_image_edit_lora", "QwenImageEditLoraNode"),
    ("qwen_image_layered", "QwenImageLayeredNode"),
]

# Widget order as saved in workflows before the IMAGE sockets existed, captured
# from these nodes on main. ComfyUI lists required widgets before optional ones,
# so flipping a widget's optional flag would misplace saved values.
SAVED_WIDGET_ORDER = {
    "QwenImageMultipleAnglesNode": ["images", "prompt", "horizontal_angle", "vertical_angle", "distance",
                                    "width", "height", "seed", "output_format", "enable_sync_mode",
                                    "enable_base64_output"],
    "QwenImageEditPlusNode": ["model", "prompt", "images", "width", "height", "seed", "output_format",
                              "enable_sync_mode", "enable_base64_output"],
    "QwenImageEditPlusLoraNode": ["model", "prompt", "images", "lora_1_path", "lora_1_scale", "lora_2_path",
                                  "lora_2_scale", "lora_3_path", "lora_3_scale", "width", "height", "seed",
                                  "output_format", "enable_sync_mode", "enable_base64_output"],
    "QwenImageMaxEditNode": ["prompt", "images", "width", "height", "seed"],
    "QwenImage20EditNode": ["model", "prompt", "images", "width", "height", "seed", "output_format",
                            "enable_sync_mode", "enable_base64_output"],
    "QwenImageEditNode": ["prompt", "image", "width", "height", "seed", "output_format", "enable_sync_mode",
                          "enable_base64_output"],
    "QwenImageEditLoraNode": ["prompt", "image", "lora_1_path", "lora_1_scale", "lora_2_path", "lora_2_scale",
                              "lora_3_path", "lora_3_scale", "width", "height", "seed", "output_format",
                              "enable_sync_mode", "enable_base64_output"],
    "QwenImageLayeredNode": ["image", "seed", "prompt", "num_layers", "enable_sync_mode", "enable_base64_output"],
    "Wan27ImageToVideoNode": ["prompt", "image", "last_image", "negative_prompt", "audio", "duration",
                              "resolution", "enable_prompt_expansion", "seed"],
}

WIDGET_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")

ALL_NODES = ([(m, n) for m, n, _ in MULTI_NODES] + SINGLE_NODES
             + [("wan_2_7_image_to_video", "Wan27ImageToVideoNode")])


def _node(module, name):
    # Loaded under the erpk test package (see conftest) so the nodes' relative
    # import of the shared inline preview resolves.
    return getattr(importlib.import_module(f"erpk.wavespeed.{module}"), name)


# ---- helper ----------------------------------------------------------------

def test_url_list_from_upload_image_is_sent_as_is():
    urls = ["https://example.com/a.png", " https://example.com/b.png ", ""]
    assert input_image_list(None, urls, 3, "Qwen") == ["https://example.com/a.png", "https://example.com/b.png"]


def test_too_many_listed_urls_names_the_model():
    urls = [f"https://example.com/{i}.png" for i in range(4)]
    with pytest.raises(ValueError, match="^Qwen Edit Plus accepts at most 3 input images, got 4$"):
        input_image_list(None, urls, 3, "Qwen Edit Plus")


# ---- schema ----------------------------------------------------------------

@pytest.mark.parametrize("module,name", ALL_NODES)
def test_saved_widget_order_is_unchanged(module, name):
    inputs = _node(module, name).define_schema().inputs
    widgets = [i for i in inputs if i.io_type in WIDGET_TYPES]
    order = [i.id for i in widgets if not i.optional] + [i.id for i in widgets if i.optional]
    assert order == SAVED_WIDGET_ORDER[name]


@pytest.mark.parametrize("module,name,_max", MULTI_NODES)
def test_multi_image_node_offers_an_optional_image_socket(module, name, _max):
    inputs = {i.id: i for i in _node(module, name).define_schema().inputs}
    assert inputs["reference_images"].io_type == "IMAGE"
    assert inputs["reference_images"].optional is True
    assert inputs["images"].io_type == "STRING"
    assert inputs["images"].default == ""


@pytest.mark.parametrize("module,name", SINGLE_NODES)
def test_single_image_node_offers_an_optional_image_socket(module, name):
    inputs = {i.id: i for i in _node(module, name).define_schema().inputs}
    assert inputs["input_image"].io_type == "IMAGE"
    assert inputs["input_image"].optional is True
    assert inputs["image"].io_type == "STRING"
    assert inputs["image"].default == ""


def test_wan_offers_first_and_last_frame_sockets():
    inputs = {i.id: i for i in _node("wan_2_7_image_to_video", "Wan27ImageToVideoNode").define_schema().inputs}
    for socket in ("first_frame", "last_frame"):
        assert inputs[socket].io_type == "IMAGE"
        assert inputs[socket].optional is True


# ---- execute wiring --------------------------------------------------------

def _run(node, **kwargs):
    sent = {}

    async def fake_send(self, request, *args, **kw):
        sent.update(request.model_dump())
        return {"outputs": ["https://example.com/out.png"]}

    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request", fake_send), \
         patch("erpk.wavespeed.wavespeed_api.utils.imageurl2tensor", return_value=torch.zeros(1, 8, 8, 3)), \
         patch("erpk.wavespeed.wavespeed_api.utils.imageurl2tensor_rgba",
               return_value=(torch.zeros(1, 8, 8, 3), torch.zeros(1, 8, 8))), \
         patch("erpk.utils.inline_preview.inline_preview_image", return_value=None):
        asyncio.run(node.execute(client={"api_key": "test-key"}, **kwargs))
    return sent


def _kwargs(name, **extra):
    base = {"prompt": "edit it"}
    if "Lora" in name:
        base["lora_1_path"] = "https://example.com/lora.safetensors"
    base.update(extra)
    return base


@pytest.mark.parametrize("module,name,_max", MULTI_NODES)
def test_multi_node_sends_every_url(module, name, _max):
    sent = _run(_node(module, name), **_kwargs(name, images="https://example.com/a.png\nhttps://example.com/b.png"))
    assert sent["images"] == ["https://example.com/a.png", "https://example.com/b.png"]


@pytest.mark.parametrize("module,name,_max", MULTI_NODES)
def test_multi_node_sends_the_image_batch_over_urls(module, name, _max):
    sent = _run(_node(module, name), **_kwargs(name, images="https://example.com/a.png",
                                               reference_images=torch.rand(2, 8, 8, 3)))
    assert len(sent["images"]) == 2
    assert all(u.startswith(DATA_URI) for u in sent["images"])


@pytest.mark.parametrize("module,name,max_images", MULTI_NODES)
def test_multi_node_rejects_a_batch_over_its_limit(module, name, max_images):
    batch = torch.rand(max_images + 1, 8, 8, 3)
    with pytest.raises(ValueError, match=f"accepts at most {max_images} input images, got {max_images + 1}$"):
        _run(_node(module, name), **_kwargs(name, reference_images=batch))


@pytest.mark.parametrize("module,name,_max", MULTI_NODES)
def test_multi_node_without_any_image_is_an_error(module, name, _max):
    with pytest.raises(ValueError, match="^Connect reference_images or enter at least one image URL$"):
        _run(_node(module, name), **_kwargs(name))


@pytest.mark.parametrize("module,name", SINGLE_NODES)
def test_single_node_sends_the_url(module, name):
    sent = _run(_node(module, name), **_kwargs(name, image="https://example.com/a.png"))
    assert sent["image"] == "https://example.com/a.png"


@pytest.mark.parametrize("module,name", SINGLE_NODES)
def test_single_node_sends_the_image_over_the_url(module, name):
    sent = _run(_node(module, name), **_kwargs(name, image="https://example.com/a.png",
                                               input_image=torch.rand(1, 8, 8, 3)))
    assert sent["image"].startswith(DATA_URI)


@pytest.mark.parametrize("module,name", SINGLE_NODES)
def test_single_node_without_an_image_is_an_error(module, name):
    with pytest.raises(ValueError, match="^Connect input_image or enter an image URL$"):
        _run(_node(module, name), **_kwargs(name))


def test_wan_sends_frames_inline():
    node = _node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
    sent = _run(node, prompt="move", first_frame=torch.rand(1, 8, 8, 3), last_frame=torch.rand(1, 8, 8, 3))
    assert sent["image"].startswith(DATA_URI)
    assert sent["last_image"].startswith(DATA_URI)


def test_wan_sends_urls_and_omits_an_empty_last_frame():
    node = _node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
    sent = _run(node, prompt="move", image="https://example.com/a.png")
    assert sent["image"] == "https://example.com/a.png"
    assert sent["last_image"] is None


def test_wan_without_a_first_frame_is_an_error():
    node = _node("wan_2_7_image_to_video", "Wan27ImageToVideoNode")
    with pytest.raises(ValueError, match="^Connect first_frame or enter an image URL$"):
        _run(node, prompt="move")
