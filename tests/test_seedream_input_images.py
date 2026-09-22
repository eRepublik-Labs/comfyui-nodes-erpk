# ABOUTME: Tests how Seedream edit nodes turn an IMAGE batch or URL text into the images list.
# ABOUTME: WaveSpeed accepts up to 10 input images on every Seedream edit endpoint.

import pytest

torch = pytest.importorskip("torch")

from wavespeed.wavespeed_api.utils import input_image_list


def test_single_url_becomes_one_item_list():
    assert input_image_list(None, "https://example.com/a.png", 10) == ["https://example.com/a.png"]


def test_several_urls_split_on_newlines_and_commas():
    text = "https://example.com/a.png\n https://example.com/b.png ,https://example.com/c.png\n\n"
    assert input_image_list(None, text, 10) == [
        "https://example.com/a.png",
        "https://example.com/b.png",
        "https://example.com/c.png",
    ]


def test_empty_inputs_give_none():
    assert input_image_list(None, "", 10) is None
    assert input_image_list(None, "  \n , ", 10) is None
    assert input_image_list(None, None, 10) is None


def test_too_many_urls_is_an_error_not_a_silent_cut():
    text = "\n".join(f"https://example.com/{i}.png" for i in range(11))
    with pytest.raises(ValueError, match="^Seedream accepts at most 10 input images, got 11$"):
        input_image_list(None, text, 10)


def _batch(n):
    return torch.rand(n, 8, 8, 3)


def test_image_batch_becomes_one_data_uri_per_slice():
    uris = input_image_list(_batch(3), "", 10)
    assert len(uris) == 3
    assert all(u.startswith("data:image/jpeg;base64,") for u in uris)


def test_connected_images_win_over_urls():
    uris = input_image_list(_batch(2), "https://example.com/a.png", 10)
    assert len(uris) == 2
    assert all(u.startswith("data:image/jpeg;base64,") for u in uris)


def test_too_large_batch_is_an_error():
    with pytest.raises(ValueError, match="^Seedream accepts at most 10 input images, got 12$"):
        input_image_list(_batch(12), "", 10)


# ---- node wiring -----------------------------------------------------------

import asyncio
import importlib
from unittest.mock import AsyncMock, patch

EDIT_NODES = [
    ("seedream_v4_edit", "SeedreamV4EditNode", False),
    ("seedream_v4_5_edit", "SeedreamV4_5EditNode", False),
    ("seedream_v5_lite_edit", "SeedreamV5LiteEditNode", False),
    ("seedream_v4_edit_sequential", "SeedreamV4EditSequentialNode", True),
    ("seedream_v4_5_edit_sequential", "SeedreamV4_5EditSequentialNode", True),
    ("seedream_v5_lite_edit_sequential", "SeedreamV5LiteEditSequentialNode", True),
]


def _node(module, name):
    # Loaded under the erpk test package (see conftest) so the nodes' relative
    # import of the shared inline preview resolves.
    return getattr(importlib.import_module(f"erpk.wavespeed.{module}"), name)


@pytest.mark.parametrize("module,name,_seq", EDIT_NODES)
def test_node_offers_an_image_socket_and_multiline_url_text(module, name, _seq):
    inputs = {i.id: i for i in _node(module, name).define_schema().inputs}
    assert inputs["images"].io_type == "IMAGE"
    assert inputs["images"].optional is True
    assert inputs["image_url"].io_type == "STRING"
    assert inputs["image_url"].default == ""
    assert inputs["image_url"].multiline is True


WIDGET_TYPES = ("STRING", "INT", "FLOAT", "BOOLEAN", "COMBO")

# Widget order as saved in workflows before the IMAGE socket existed (captured
# from the nodes on main). ComfyUI lists required widgets before optional ones,
# so flipping a widget's optional flag moves it and misplaces saved values.
PLAIN_ORDER = ["prompt", "image_url", "size_preset", "seed", "width", "height",
               "show_aspect_ratio", "enable_sync_mode", "enable_base64_output"]
SEQUENTIAL_ORDER = ["prompt", "max_images", "size_preset", "seed", "image_url", "width",
                    "height", "show_aspect_ratio", "enable_sync_mode", "enable_base64_output"]


@pytest.mark.parametrize("module,name,seq", EDIT_NODES)
def test_saved_widget_order_is_unchanged(module, name, seq):
    inputs = _node(module, name).define_schema().inputs
    widgets = [i for i in inputs if i.io_type in WIDGET_TYPES]
    order = [i.id for i in widgets if not i.optional] + [i.id for i in widgets if i.optional]
    assert order == (SEQUENTIAL_ORDER if seq else PLAIN_ORDER)


def _run(node, **kwargs):
    sent = {}

    async def fake_send(self, request, *args):
        sent["images"] = request.images
        return {"outputs": ["https://example.com/out.png"]}

    with patch("erpk.wavespeed.wavespeed_api.client.WaveSpeedClient.send_request", fake_send), \
         patch("erpk.wavespeed.wavespeed_api.utils.imageurl2tensor", return_value=torch.zeros(1, 8, 8, 3)), \
         patch("erpk.utils.inline_preview.inline_preview_image", return_value=None):
        asyncio.run(node.execute(client={"api_key": "test-key"}, **kwargs))
    return sent["images"]


def _kwargs(sequential, **extra):
    base = {"prompt": "edit it", "size_preset": "Custom"}
    if sequential:
        base["max_images"] = 2
    base.update(extra)
    return base


@pytest.mark.parametrize("module,name,seq", EDIT_NODES)
def test_node_sends_every_url(module, name, seq):
    images = _run(_node(module, name), **_kwargs(seq, image_url="https://example.com/a.png\nhttps://example.com/b.png"))
    assert images == ["https://example.com/a.png", "https://example.com/b.png"]


@pytest.mark.parametrize("module,name,seq", EDIT_NODES)
def test_node_sends_the_image_batch(module, name, seq):
    images = _run(_node(module, name), **_kwargs(seq, images=torch.rand(3, 8, 8, 3)))
    assert len(images) == 3
    assert all(u.startswith("data:image/jpeg;base64,") for u in images)


@pytest.mark.parametrize("module,name", [(m, n) for m, n, seq in EDIT_NODES if not seq])
def test_plain_edit_without_any_image_is_an_error(module, name):
    with pytest.raises(ValueError, match="^Connect images or enter at least one image URL$"):
        _run(_node(module, name), **_kwargs(False))


@pytest.mark.parametrize("module,name", [(m, n) for m, n, seq in EDIT_NODES if seq])
def test_sequential_edit_without_images_sends_none(module, name):
    assert _run(_node(module, name), **_kwargs(True)) is None
