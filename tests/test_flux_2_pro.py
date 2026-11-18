# ABOUTME: Tests for the FLUX.2 Pro text-to-image and edit nodes.
# ABOUTME: Payload shapes follow WaveSpeed's documented schemas; the API call itself is stubbed.

import asyncio
import importlib
from unittest.mock import patch

import pytest

torch = pytest.importorskip("torch")


def _node(module, name):
    # Loaded under the erpk test package (see conftest) so the nodes' relative
    # imports resolve.
    return getattr(importlib.import_module(f"erpk.wavespeed.{module}"), name)


def _text_to_image():
    return _node("flux_2_pro", "Flux2ProNode")


def _edit():
    return _node("flux_2_pro_edit", "Flux2ProEditNode")


def _run(node, **kwargs):
    """Run a node against a stubbed WaveSpeed call; return (sent request, node output)."""
    sent = {}

    async def fake_send(self, request, *args):
        sent["request"] = request
        return {"outputs": ["https://example.com/out.jpeg"]}

    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request", fake_send), \
         patch("erpk.wavespeed.wavespeed_api.utils.imageurl2tensor", return_value=torch.zeros(1, 8, 8, 3)):
        result = asyncio.run(node.execute(client={"api_key": "test-key"}, **kwargs))
    return sent["request"], result


def _refused(node, **kwargs):
    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request") as send:
        with pytest.raises(ValueError) as exc:
            asyncio.run(node.execute(client={"api_key": "test-key"}, **kwargs))
    assert not send.called
    return str(exc.value)


def _inputs(node):
    return {i.id: i for i in node.define_schema().inputs}


def test_text_to_image_sends_prompt_size_and_seed():
    request, _ = _run(_text_to_image(), prompt="a red apple", width=1280, height=720, seed=1234)
    assert request.get_api_path() == "/api/v3/wavespeed-ai/flux-2-pro/text-to-image"
    assert request.build_payload() == {"prompt": "a red apple", "size": "1280*720", "seed": 1234}


def test_text_to_image_defaults_to_a_square_and_a_random_seed():
    request, _ = _run(_text_to_image(), prompt="a red apple")
    assert request.build_payload() == {"prompt": "a red apple", "size": "1024*1024", "seed": -1}


@pytest.mark.parametrize("widget", ["width", "height"])
def test_text_to_image_size_widgets_cover_the_documented_range(widget):
    size = _inputs(_text_to_image())[widget]
    assert (size.default, size.min, size.max, size.step) == (1024, 256, 2048, 16)


def test_edit_omits_size_when_width_and_height_are_zero():
    request, _ = _run(_edit(), prompt="make it blue", seed=1234,
                      image_url="https://example.com/a.png\nhttps://example.com/b.png")
    assert request.get_api_path() == "/api/v3/wavespeed-ai/flux-2-pro/edit"
    assert request.build_payload() == {
        "prompt": "make it blue",
        "images": ["https://example.com/a.png", "https://example.com/b.png"],
        "seed": 1234,
    }


def test_edit_sends_size_when_both_dimensions_are_set():
    request, _ = _run(_edit(), prompt="x", image_url="https://example.com/a.png", width=768, height=1344)
    assert request.build_payload() == {
        "prompt": "x",
        "images": ["https://example.com/a.png"],
        "size": "768*1344",
        "seed": -1,
    }


@pytest.mark.parametrize("width, height, expected", [
    (1024, 0, "Set width and height together, each 256-2048, or leave both at 0: got width=1024, height=0"),
    (0, 1024, "Set width and height together, each 256-2048, or leave both at 0: got width=0, height=1024"),
    (128, 1024, "Set width and height together, each 256-2048, or leave both at 0: got width=128, height=1024"),
    (1024, 2064, "Set width and height together, each 256-2048, or leave both at 0: got width=1024, height=2064"),
])
def test_edit_refuses_a_mixed_or_out_of_range_size_naming_the_values(width, height, expected):
    assert _refused(_edit(), prompt="x", image_url="https://example.com/a.png",
                    width=width, height=height) == expected


@pytest.mark.parametrize("widget", ["width", "height"])
def test_edit_size_widgets_default_to_following_the_input(widget):
    size = _inputs(_edit())[widget]
    assert (size.default, size.min, size.max, size.step) == (0, 0, 2048, 16)


def test_edit_rejects_more_than_three_images_by_count():
    urls = "\n".join(f"https://example.com/{i}.png" for i in range(4))
    assert _refused(_edit(), prompt="x", image_url=urls) == "FLUX.2 Pro accepts at most 3 input images, got 4"


def test_edit_without_images_is_an_error():
    assert _refused(_edit(), prompt="x") == (
        "Connect an image or add images to the grid, or enter at least one image URL")


@pytest.mark.parametrize("node", [_text_to_image, _edit])
def test_nodes_offer_no_sync_or_base64_switch(node):
    inputs = _inputs(node())
    assert "enable_sync_mode" not in inputs
    assert "enable_base64_output" not in inputs
