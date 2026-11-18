# ABOUTME: Tests for the Seedream V5.5 text-to-image, edit and layer-decomposition nodes.
# ABOUTME: Payload shapes follow WaveSpeed's documented schemas; the API call itself is stubbed.

import asyncio
import importlib
import io
from unittest.mock import patch

import pytest
from PIL import Image

torch = pytest.importorskip("torch")

from erpk.wavespeed.wavespeed_api.utils import load_decomposed_layers


def _node(module, name):
    # Loaded under the erpk test package (see conftest) so the nodes' relative
    # imports resolve.
    return getattr(importlib.import_module(f"erpk.wavespeed.{module}"), name)


def _rgba_png(size, opaque_box):
    image = Image.new("RGB", size, (200, 40, 40))
    alpha = Image.new("L", size, 0)
    alpha.paste(255, opaque_box)
    image.putalpha(alpha)
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


LEFT_HALF_OPAQUE = _rgba_png((8, 6), (0, 0, 4, 6))
FILES = {
    "https://example.com/out.png": LEFT_HALF_OPAQUE,
    "https://example.com/base.png": _rgba_png((16, 16), (0, 0, 16, 16)),
    "https://example.com/layer.png": LEFT_HALF_OPAQUE,
}


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


def _refused(node, **kwargs):
    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request") as send:
        with pytest.raises(ValueError) as exc:
            asyncio.run(node.execute(client={"api_key": "test-key"}, **kwargs))
    assert not send.called
    return exc.value


def _inputs(node):
    return {i.id: i for i in node.define_schema().inputs}


def _assert_left_half_opaque(image, mask):
    assert tuple(image.shape) == (1, 6, 8, 3)
    assert tuple(mask.shape) == (1, 6, 8)
    assert mask[0, :, :4].min().item() == 1.0
    assert mask[0, :, 4:].max().item() == 0.0


# ---- text to image ---------------------------------------------------------

def test_text_to_image_sends_only_the_documented_fields_and_no_seed():
    node = _node("seedream_v5_5", "SeedreamV5_5Node")
    request, _ = _run(node, ["https://example.com/out.png"], prompt="a red apple", seed=1234)
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.5"
    assert request.build_payload() == {
        "prompt": "a red apple",
        "aspect_ratio": "1:1",
        "resolution": "1k",
        "output_format": "png",
        "background": "auto",
    }


def test_text_to_image_forwards_its_settings():
    node = _node("seedream_v5_5", "SeedreamV5_5Node")
    request, _ = _run(node, ["https://example.com/out.png"], prompt="a logo", aspect_ratio="21:9",
                      resolution="2k", output_format="png", background="transparent")
    assert request.build_payload() == {
        "prompt": "a logo",
        "aspect_ratio": "21:9",
        "resolution": "2k",
        "output_format": "png",
        "background": "transparent",
    }


def test_text_to_image_offers_the_documented_options():
    inputs = _inputs(_node("seedream_v5_5", "SeedreamV5_5Node"))
    assert list(inputs["background"].options) == ["auto", "transparent", "opaque"]
    assert inputs["background"].default == "auto"
    assert list(inputs["output_format"].options) == ["jpeg", "png"]
    assert inputs["output_format"].default == "png"
    assert list(inputs["resolution"].options) == ["1k", "1.5k", "2k"]
    assert "enable_sync_mode" not in inputs
    assert "enable_base64_output" not in inputs
    assert "prompt_optimization_mode" not in inputs


def test_text_to_image_outputs_the_alpha_of_an_rgba_result_as_its_mask():
    node = _node("seedream_v5_5", "SeedreamV5_5Node")
    _, result = _run(node, ["https://example.com/out.png"], prompt="a logo", background="transparent")
    image, mask = result.result
    _assert_left_half_opaque(image, mask)


def test_mask_uses_the_same_convention_as_the_layer_nodes():
    node = _node("seedream_v5_5", "SeedreamV5_5Node")
    _, result = _run(node, ["https://example.com/out.png"], prompt="a logo")
    with patch("erpk.utils.safe_fetch.fetch_remote_bytes", side_effect=lambda url, **_: FILES[url]):
        _, _, layer_masks = load_decomposed_layers(["https://example.com/base.png", "https://example.com/layer.png"])
    assert torch.equal(result.result[1], layer_masks[0])


def test_transparent_background_in_jpeg_is_refused_before_the_paid_call():
    error = _refused(_node("seedream_v5_5", "SeedreamV5_5Node"), prompt="a logo",
                     background="transparent", output_format="jpeg")
    assert error.errors()[0]["msg"] == 'Value error, background "transparent" needs output_format "png", got "jpeg"'


# ---- edit ------------------------------------------------------------------

def test_edit_auto_aspect_is_omitted_so_the_api_follows_the_first_image():
    node = _node("seedream_v5_5_edit", "SeedreamV5_5EditNode")
    request, result = _run(node, ["https://example.com/out.png"], prompt="make it blue", seed=1234,
                           image_url="https://example.com/a.png\nhttps://example.com/b.png")
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.5/edit"
    assert request.build_payload() == {
        "prompt": "make it blue",
        "images": ["https://example.com/a.png", "https://example.com/b.png"],
        "resolution": "1k",
        "output_format": "png",
        "background": "auto",
    }
    _assert_left_half_opaque(*result.result)


def test_edit_sends_an_explicit_aspect_ratio():
    node = _node("seedream_v5_5_edit", "SeedreamV5_5EditNode")
    request, _ = _run(node, ["https://example.com/out.png"], prompt="x",
                      image_url="https://example.com/a.png", aspect_ratio="9:16")
    assert request.build_payload()["aspect_ratio"] == "9:16"


def test_edit_aspect_defaults_to_auto():
    inputs = _inputs(_node("seedream_v5_5_edit", "SeedreamV5_5EditNode"))
    assert list(inputs["aspect_ratio"].options)[0] == "auto"
    assert inputs["aspect_ratio"].default == "auto"


def test_edit_rejects_more_than_ten_images_by_count():
    urls = "\n".join(f"https://example.com/{i}.png" for i in range(11))
    error = _refused(_node("seedream_v5_5_edit", "SeedreamV5_5EditNode"), prompt="x", image_url=urls)
    assert str(error) == "Seedream accepts at most 10 input images, got 11"


def test_edit_without_images_is_an_error():
    error = _refused(_node("seedream_v5_5_edit", "SeedreamV5_5EditNode"), prompt="x")
    assert str(error) == "Connect an image or add images to the grid, or enter at least one image URL"


# ---- layers ----------------------------------------------------------------

LAYER_OUTPUTS = ["https://example.com/base.png", "https://example.com/layer.png"]


def test_layers_request_sends_the_default_image_count_and_always_png():
    node = _node("seedream_v5_5_layers", "SeedreamV5_5LayersNode")
    request, _ = _run(node, LAYER_OUTPUTS, image_url="https://example.com/in.png", seed=1234)
    assert request.get_api_path() == "/api/v3/bytedance/seedream-v5.5/layer-decomposition"
    assert request.build_payload() == {
        "image": "https://example.com/in.png",
        "resolution": "1k",
        "max_images": 10,
        "output_format": "png",
    }


def test_layers_forwards_prompt_resolution_and_image_count():
    node = _node("seedream_v5_5_layers", "SeedreamV5_5LayersNode")
    request, _ = _run(node, LAYER_OUTPUTS, image_url="https://example.com/in.png",
                      prompt="separate the car", resolution="2k", max_images=2)
    assert request.build_payload() == {
        "image": "https://example.com/in.png",
        "prompt": "separate the car",
        "resolution": "2k",
        "max_images": 2,
        "output_format": "png",
    }


def test_layers_image_count_widget_covers_the_documented_range():
    max_images = _inputs(_node("seedream_v5_5_layers", "SeedreamV5_5LayersNode"))["max_images"]
    assert (max_images.default, max_images.min, max_images.max) == (10, 2, 100)


@pytest.mark.parametrize("count", [1, 101])
def test_layers_image_count_outside_the_range_is_refused(count):
    error = _refused(_node("seedream_v5_5_layers", "SeedreamV5_5LayersNode"),
                     image_url="https://example.com/in.png", max_images=count)
    assert error.errors()[0]["loc"] == ("max_images",)


def test_layers_returns_the_base_then_one_image_and_mask_per_layer():
    node = _node("seedream_v5_5_layers", "SeedreamV5_5LayersNode")
    _, result = _run(node, LAYER_OUTPUTS, image_url="https://example.com/in.png")
    base, layers, masks = result.result
    assert tuple(base.shape) == (1, 16, 16, 3)
    assert len(layers) == len(masks) == 1
    _assert_left_half_opaque(layers[0], masks[0])


def test_layers_reports_a_result_without_layers():
    node = _node("seedream_v5_5_layers", "SeedreamV5_5LayersNode")
    with pytest.raises(ValueError, match="^Layer decomposition returned 1 image, so there are no layers to output$"):
        _run(node, ["https://example.com/base.png"], image_url="https://example.com/in.png")
