# ABOUTME: Tests for the Seedream 5.0 Pro text-to-image, edit and layer-decomposition nodes.
# ABOUTME: Payload shapes follow WaveSpeed's llms.txt schemas; layer shapes were measured live 2026-09-22.

import pytest

from wavespeed.wavespeed_api.requests.seedream_v5_pro import SeedreamV5Pro


def test_text_to_image_payload_carries_the_pro_settings():
    request = SeedreamV5Pro(
        prompt="a red apple",
        aspect_ratio="16:9",
        resolution="1.5k",
        output_format="png",
        prompt_optimization_mode="fast",
    )
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.0-pro"
    assert request.build_payload() == {
        "prompt": "a red apple",
        "aspect_ratio": "16:9",
        "resolution": "1.5k",
        "output_format": "png",
        "prompt_optimization_mode": "fast",
        "enable_sync_mode": False,
        "enable_base64_output": False,
    }


from wavespeed.wavespeed_api.requests.seedream_v5_pro_edit import SeedreamV5ProEdit


def test_edit_without_an_aspect_ratio_follows_the_first_image():
    request = SeedreamV5ProEdit(prompt="make it blue", images=["https://example.com/a.png"])
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.0-pro/edit"
    assert "aspect_ratio" not in request.build_payload()
    assert request.build_payload()["images"] == ["https://example.com/a.png"]


def test_edit_sends_an_explicit_aspect_ratio():
    request = SeedreamV5ProEdit(prompt="x", images=["https://example.com/a.png"], aspect_ratio="9:16")
    assert request.build_payload()["aspect_ratio"] == "9:16"


def test_edit_rejects_more_than_ten_images():
    with pytest.raises(ValueError):
        SeedreamV5ProEdit(prompt="x", images=[f"https://example.com/{i}.png" for i in range(11)])


from wavespeed.wavespeed_api.requests.seedream_v5_pro_layers import SeedreamV5ProLayers


def test_layers_request_always_asks_for_png():
    # Measured 2026-09-22: output_format=jpeg returns jpeg layers, which drops the
    # transparency that makes them layers.
    request = SeedreamV5ProLayers(image="https://example.com/a.png", resolution="2k")
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.0-pro/layer-decomposition"
    assert request.build_payload() == {
        "image": "https://example.com/a.png",
        "resolution": "2k",
        "output_format": "png",
        "prompt_optimization_mode": "standard",
    }


def test_layers_request_sends_a_guiding_prompt():
    request = SeedreamV5ProLayers(image="https://example.com/a.png", prompt="separate the car")
    assert request.build_payload()["prompt"] == "separate the car"


# ---- nodes -----------------------------------------------------------------

import asyncio
import importlib
from unittest.mock import patch

torch = pytest.importorskip("torch")


def _node(module, name):
    # Loaded under the erpk test package (see conftest) so the nodes' relative
    # import of the shared inline preview resolves.
    return getattr(importlib.import_module(f"erpk.wavespeed.{module}"), name)


def _run(node, outputs, **kwargs):
    """Run a node against a stubbed WaveSpeed call; return (sent request, node output)."""
    sent = {}

    async def fake_send(self, request, *args):
        sent["request"] = request
        return {"outputs": outputs}

    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request", fake_send), \
         patch("erpk.wavespeed.wavespeed_api.utils.imageurl2tensor", return_value=torch.zeros(1, 8, 8, 3)), \
         patch("erpk.utils.inline_preview.inline_preview_image", return_value=None):
        result = asyncio.run(node.execute(client={"api_key": "test-key"}, **kwargs))
    return sent["request"], result


def test_text_to_image_node_forwards_its_settings():
    node = _node("seedream_v5_pro", "SeedreamV5ProNode")
    request, _ = _run(node, ["https://example.com/out.jpeg"], prompt="a red apple",
                      aspect_ratio="21:9", resolution="2k", output_format="png",
                      prompt_optimization_mode="fast")
    assert request.build_payload() == {
        "prompt": "a red apple",
        "aspect_ratio": "21:9",
        "resolution": "2k",
        "output_format": "png",
        "prompt_optimization_mode": "fast",
        "enable_sync_mode": False,
        "enable_base64_output": False,
    }


def test_text_to_image_node_offers_the_documented_options():
    inputs = {i.id: i for i in _node("seedream_v5_pro", "SeedreamV5ProNode").define_schema().inputs}
    assert list(inputs["aspect_ratio"].options) == [
        "1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3",
        "4:5", "5:4", "9:16", "16:9", "9:21", "21:9"]
    assert inputs["aspect_ratio"].default == "1:1"
    assert list(inputs["resolution"].options) == ["1k", "1.5k", "2k"]
    assert inputs["resolution"].default == "1k"
    assert list(inputs["output_format"].options) == ["jpeg", "png"]
    assert list(inputs["prompt_optimization_mode"].options) == ["standard", "fast"]


def test_edit_node_auto_aspect_lets_the_api_follow_the_first_image():
    node = _node("seedream_v5_pro_edit", "SeedreamV5ProEditNode")
    request, _ = _run(node, ["https://example.com/out.jpeg"], prompt="make it blue",
                      image_url="https://example.com/a.png\nhttps://example.com/b.png",
                      aspect_ratio="auto")
    payload = request.build_payload()
    assert "aspect_ratio" not in payload
    assert payload["images"] == ["https://example.com/a.png", "https://example.com/b.png"]


def test_edit_node_sends_an_image_batch_inline():
    node = _node("seedream_v5_pro_edit", "SeedreamV5ProEditNode")
    request, _ = _run(node, ["https://example.com/out.jpeg"], prompt="x",
                      images=torch.rand(3, 8, 8, 3), aspect_ratio="4:5")
    payload = request.build_payload()
    assert payload["aspect_ratio"] == "4:5"
    assert len(payload["images"]) == 3
    assert all(u.startswith("data:image/jpeg;base64,") for u in payload["images"])


def test_edit_node_without_images_is_an_error():
    node = _node("seedream_v5_pro_edit", "SeedreamV5ProEditNode")
    with pytest.raises(ValueError, match="^Connect images or enter at least one image URL$"):
        _run(node, [], prompt="x")


def test_edit_node_aspect_defaults_to_auto():
    inputs = {i.id: i for i in _node("seedream_v5_pro_edit", "SeedreamV5ProEditNode").define_schema().inputs}
    assert list(inputs["aspect_ratio"].options)[0] == "auto"
    assert inputs["aspect_ratio"].default == "auto"
    assert inputs["images"].io_type == "IMAGE"


# Layer decomposition. Shapes mirror a live run on 2026-09-22: a palette-mode
# base, then one RGBA PNG per object, each cropped to its object at its own size.

import io as _io
from PIL import Image as _Image


def _png(mode, size, color, alpha_band=None):
    image = _Image.new(mode, size, color)
    if alpha_band is not None:
        alpha = _Image.new("L", size, 0)
        alpha.paste(255, alpha_band)
        image.putalpha(alpha)
    buffer = _io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


LAYER_FILES = {
    "https://example.com/base.png": _png("P", (16, 16), 3),
    "https://example.com/red.png": _png("RGB", (8, 6), (200, 40, 40), alpha_band=(0, 0, 4, 6)),
    "https://example.com/green.png": _png("RGB", (5, 9), (40, 160, 60), alpha_band=(0, 0, 5, 9)),
}


def _run_layers(outputs, **kwargs):
    node = _node("seedream_v5_pro_layers", "SeedreamV5ProLayersNode")
    with patch("erpk.utils.safe_fetch.fetch_remote_bytes", side_effect=lambda url, **_: LAYER_FILES[url]):
        return _run(node, outputs, **kwargs)


def test_layers_node_returns_base_then_one_image_and_mask_per_layer():
    request, result = _run_layers(list(LAYER_FILES), image_url="https://example.com/in.png")
    base, layers, masks = result.result
    assert tuple(base.shape) == (1, 16, 16, 3)
    assert [tuple(t.shape) for t in layers] == [(1, 6, 8, 3), (1, 9, 5, 3)]
    assert [tuple(m.shape) for m in masks] == [(1, 6, 8), (1, 9, 5)]
    # Mask is the layer's alpha: the red layer is opaque only in its left half.
    assert masks[0][0, :, :4].min().item() == 1.0
    assert masks[0][0, :, 4:].max().item() == 0.0
    assert masks[1].min().item() == 1.0
    assert request.build_payload()["image"] == "https://example.com/in.png"


def test_layers_node_outputs_layers_as_lists():
    outputs = _node("seedream_v5_pro_layers", "SeedreamV5ProLayersNode").define_schema().outputs
    assert [(o.id, o.io_type, o.is_output_list) for o in outputs] == [
        ("base", "IMAGE", False), ("layers", "IMAGE", True), ("masks", "MASK", True)]


def test_layers_node_sends_a_connected_image_inline():
    request, _ = _run_layers(list(LAYER_FILES), images=torch.rand(1, 8, 8, 3))
    assert request.build_payload()["image"].startswith("data:image/jpeg;base64,")


def test_layers_node_takes_exactly_one_image():
    with pytest.raises(ValueError, match="^Layer decomposition takes one image, got 2$"):
        _run_layers(list(LAYER_FILES), images=torch.rand(2, 8, 8, 3))
    with pytest.raises(ValueError, match="^Connect an image or enter an image URL$"):
        _run_layers(list(LAYER_FILES))


def test_layers_node_reports_a_result_without_layers():
    with pytest.raises(ValueError, match="^Layer decomposition returned 1 image, so there are no layers to output$"):
        _run_layers(["https://example.com/base.png"], image_url="https://example.com/in.png")
