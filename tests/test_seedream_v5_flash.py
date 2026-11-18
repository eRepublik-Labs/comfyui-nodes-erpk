# ABOUTME: Tests for the Seedream V5.0 Flash text-to-image, edit and layer-decomposition nodes.
# ABOUTME: Payload shapes follow WaveSpeed's documented schemas; the API call itself is stubbed.

import asyncio
import importlib
import io
from unittest.mock import patch

import pytest
from PIL import Image

torch = pytest.importorskip("torch")


def _node(module, name):
    # Loaded under the erpk test package (see conftest) so the nodes' relative
    # imports resolve.
    return getattr(importlib.import_module(f"erpk.wavespeed.{module}"), name)


def _png(mode, size, color):
    buffer = io.BytesIO()
    Image.new(mode, size, color).save(buffer, "PNG")
    return buffer.getvalue()


FILES = {
    "https://example.com/out.jpeg": _png("RGB", (8, 6), (10, 20, 30)),
    "https://example.com/base.png": _png("RGB", (16, 16), (10, 20, 30)),
    "https://example.com/layer.png": _png("RGBA", (5, 9), (200, 40, 40, 255)),
}
LAYER_OUTPUTS = ["https://example.com/base.png", "https://example.com/layer.png"]


def _run(node, outputs, **kwargs):
    """Run a node with only the network stubbed; return (sent request, node output)."""
    sent = {}

    async def fake_send(self, request, *args):
        sent["request"] = request
        return {"outputs": outputs}

    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request", fake_send), \
         patch("erpk.utils.safe_fetch.fetch_remote_bytes", side_effect=lambda url, **_: FILES[url]):
        result = asyncio.run(node.execute(client={"api_key": "test-key"}, **kwargs))
    return sent["request"], result


def _inputs(node):
    return {i.id: i for i in node.define_schema().inputs}


def test_text_to_image_sends_only_the_documented_fields_and_no_seed():
    node = _node("seedream_v5_flash", "SeedreamV5FlashNode")
    request, result = _run(node, ["https://example.com/out.jpeg"], prompt="a red apple", seed=1234)
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.0-flash"
    assert request.build_payload() == {
        "prompt": "a red apple",
        "aspect_ratio": "1:1",
        "resolution": "1k",
        "output_format": "jpeg",
    }
    assert tuple(result.result[0].shape) == (1, 6, 8, 3)


def test_text_to_image_forwards_its_settings():
    node = _node("seedream_v5_flash", "SeedreamV5FlashNode")
    request, _ = _run(node, ["https://example.com/out.jpeg"], prompt="a red apple", aspect_ratio="16:9",
                      resolution="2k", output_format="png")
    assert request.build_payload() == {
        "prompt": "a red apple",
        "aspect_ratio": "16:9",
        "resolution": "2k",
        "output_format": "png",
    }


def test_text_to_image_offers_the_documented_defaults():
    inputs = _inputs(_node("seedream_v5_flash", "SeedreamV5FlashNode"))
    assert (inputs["aspect_ratio"].default, inputs["resolution"].default, inputs["output_format"].default) == (
        "1:1", "1k", "jpeg")
    assert "enable_sync_mode" not in inputs
    assert "enable_base64_output" not in inputs
    assert "prompt_optimization_mode" not in inputs


def test_edit_auto_aspect_is_omitted_so_the_api_follows_the_first_image():
    node = _node("seedream_v5_flash_edit", "SeedreamV5FlashEditNode")
    request, _ = _run(node, ["https://example.com/out.jpeg"], prompt="make it blue", seed=1234,
                      image_url="https://example.com/a.png\nhttps://example.com/b.png")
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.0-flash/edit"
    assert request.build_payload() == {
        "prompt": "make it blue",
        "images": ["https://example.com/a.png", "https://example.com/b.png"],
        "resolution": "1k",
        "output_format": "jpeg",
    }


def test_edit_sends_an_explicit_aspect_ratio():
    node = _node("seedream_v5_flash_edit", "SeedreamV5FlashEditNode")
    request, _ = _run(node, ["https://example.com/out.jpeg"], prompt="x",
                      image_url="https://example.com/a.png", aspect_ratio="4:5")
    assert request.build_payload()["aspect_ratio"] == "4:5"


def test_edit_aspect_defaults_to_auto():
    inputs = _inputs(_node("seedream_v5_flash_edit", "SeedreamV5FlashEditNode"))
    assert list(inputs["aspect_ratio"].options)[0] == "auto"
    assert inputs["aspect_ratio"].default == "auto"


def test_edit_rejects_more_than_ten_images_by_count():
    node = _node("seedream_v5_flash_edit", "SeedreamV5FlashEditNode")
    urls = "\n".join(f"https://example.com/{i}.png" for i in range(11))
    with pytest.raises(ValueError, match="^Seedream accepts at most 10 input images, got 11$"):
        _run(node, [], prompt="x", image_url=urls)


def test_layers_request_always_asks_for_png_and_sends_no_seed():
    node = _node("seedream_v5_flash_layers", "SeedreamV5FlashLayersNode")
    request, _ = _run(node, LAYER_OUTPUTS, image_url="https://example.com/in.png", seed=1234)
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.0-flash/layer-decomposition"
    assert request.build_payload() == {
        "image": "https://example.com/in.png",
        "resolution": "1k",
        "output_format": "png",
    }


def test_layers_forwards_prompt_and_resolution():
    node = _node("seedream_v5_flash_layers", "SeedreamV5FlashLayersNode")
    request, _ = _run(node, LAYER_OUTPUTS, image_url="https://example.com/in.png",
                      prompt="separate the car", resolution="1.5k")
    assert request.build_payload() == {
        "image": "https://example.com/in.png",
        "prompt": "separate the car",
        "resolution": "1.5k",
        "output_format": "png",
    }


def test_layers_returns_the_base_then_one_image_and_mask_per_layer():
    node = _node("seedream_v5_flash_layers", "SeedreamV5FlashLayersNode")
    _, result = _run(node, LAYER_OUTPUTS, image_url="https://example.com/in.png")
    base, layers, masks = result.result
    assert tuple(base.shape) == (1, 16, 16, 3)
    assert [tuple(t.shape) for t in layers] == [(1, 9, 5, 3)]
    assert [tuple(m.shape) for m in masks] == [(1, 9, 5)]
    assert masks[0].min().item() == 1.0


def test_layers_reports_a_result_without_layers():
    node = _node("seedream_v5_flash_layers", "SeedreamV5FlashLayersNode")
    with pytest.raises(ValueError, match="^Layer decomposition returned 0 images, so there are no layers to output$"):
        _run(node, [], image_url="https://example.com/in.png")
